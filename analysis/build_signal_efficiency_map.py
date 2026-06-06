"""Build detector-level signal-efficiency diagnostics from full ALP scans.

The full Condor scan writes one `full_point_summary.csv` per contour point. This
script follows the Delphes ROOT paths in the collected scan summary and computes
simple channel selections:

* invisible: exactly one reconstructed photon with recoil energy in the analysis
  recoil window.
* resolved_prompt: at least three reconstructed photons with any photon pair in
  the analysis mass window.

The output is a diagnostics/efficiency map. The FCC-ee projection still owns the
statistical limit calculation; this file records the detector-level selection
fractions that should be used when replacing the flat placeholder efficiency.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import awkward as ak
import numpy as np
import pandas as pd

try:
    from analysis.fccee_background_yields import invariant_masses, load_delphes
    from theory.predictions import predict_grid as theory
    from analysis.fccee_projection import angular_acceptance_from_eta_max
except ModuleNotFoundError:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from analysis.fccee_background_yields import invariant_masses, load_delphes
    from theory.predictions import predict_grid as theory
    from analysis.fccee_projection import angular_acceptance_from_eta_max


def _base_channel(channel: str) -> str:
    if channel.startswith("invisible"):
        return "invisible"
    if channel in {"resolved", "resolved_prompt", "prompt_resolved"}:
        return "resolved_prompt"
    raise ValueError(f"Unknown channel: {channel}")


def _bool_value(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "t", "yes", "passed"}


def _invisible_count(ph: dict[str, Any], m_a: float, sqrt_s: float, rel: float, minimum: float) -> int:
    n_photons = ak.num(ph["energy"])
    one_photon = n_photons == 1
    if not bool(ak.any(one_photon)):
        return 0
    energies = ak.flatten(ph["energy"][one_photon], axis=None)
    expected = float(theory.e_gamma_recoil(m_a, sqrt_s))
    width = max(rel * expected, minimum)
    return int(ak.sum(abs(energies - expected) <= width))


def _resolved_count(ph: dict[str, Any], m_a: float, rel: float, minimum: float) -> int:
    n_photons = ak.num(ph["pt"])
    pair_mass = invariant_masses(ph)
    width = max(rel * m_a, minimum)
    selected = (n_photons >= 3) & ak.any(abs(pair_mass - m_a) <= width, axis=1)
    return int(ak.sum(selected))


def _analytic_region_probability(channel: str, m_a: float, g_agg: float, sqrt_s: float, config: dict[str, Any]) -> float:
    ell = float(theory.ell_a(m_a, g_agg, sqrt_s))
    if ell <= 0.0:
        return 0.0
    if channel == "invisible":
        return math.exp(-float(config["l_max_m"]) / ell)
    if channel == "resolved_prompt":
        return 1.0 - math.exp(-float(config["l_min_m"]) / ell)
    raise ValueError(f"Unknown channel: {channel}")


def _flat_efficiency(channel: str, config: dict[str, Any]) -> float:
    acceptance = angular_acceptance_from_eta_max(float(config["eta_max"]))
    photon_eff = float(config["photon_efficiency"])
    if channel == "invisible":
        return acceptance * photon_eff
    if channel == "resolved_prompt":
        return acceptance * photon_eff**3
    raise ValueError(f"Unknown channel: {channel}")


def build_efficiency_map(
    *,
    scan_summary: Path,
    config_path: Path,
    out: Path,
    summary_json: Path,
    tree_name: str,
) -> pd.DataFrame:
    config = json.loads(config_path.read_text())
    rows = pd.read_csv(scan_summary)
    output_rows: list[dict[str, Any]] = []

    for _, row in rows.iterrows():
        if not (_bool_value(row.get("gate1_passed")) and _bool_value(row.get("signature_validation_passed"))):
            continue
        channel_label = str(row["channel"])
        channel = _base_channel(channel_label)
        m_a = float(row["m_a_GeV"])
        g_agg = float(row["g_agg_GeV_inv"])
        sqrt_s = float(row["sqrt_s_GeV"])
        root_path = Path(str(row["delphes_root"]))
        ph = load_delphes(root_path, tree_name)
        n_generated = int(len(ak.num(ph["pt"])))
        if n_generated <= 0:
            selected = 0
        elif channel == "invisible":
            selected = _invisible_count(
                ph,
                m_a,
                sqrt_s,
                float(config["invisible_recoil_resolution_relative"]),
                float(config["invisible_recoil_resolution_min_GeV"]),
            )
        else:
            selected = _resolved_count(
                ph,
                m_a,
                float(config["resolved_mass_resolution_relative"]),
                float(config["resolved_mass_resolution_min_GeV"]),
            )

        selected_fraction = selected / n_generated if n_generated else 0.0
        p_region = _analytic_region_probability(channel, m_a, g_agg, sqrt_s, config)
        flat_eff = _flat_efficiency(channel, config)
        analytic_selected_fraction = p_region * flat_eff
        correction = (
            selected_fraction / analytic_selected_fraction
            if analytic_selected_fraction > 0.0
            else math.nan
        )
        output_rows.append(
            {
                "jobid": int(row["jobid"]),
                "channel": channel_label,
                "base_channel": channel,
                "m_a_GeV": m_a,
                "g_agg_GeV_inv": g_agg,
                "sqrt_s_GeV": sqrt_s,
                "n_generated": n_generated,
                "n_selected": selected,
                "selected_fraction": selected_fraction,
                "analytic_region_probability": p_region,
                "flat_detector_efficiency": flat_eff,
                "analytic_selected_fraction": analytic_selected_fraction,
                "detector_correction_factor": correction,
                "delphes_root": str(root_path),
            }
        )

    result = pd.DataFrame(output_rows).sort_values(["channel", "m_a_GeV", "g_agg_GeV_inv"])
    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False)

    summary = {
        "scan_summary": str(scan_summary),
        "config": str(config_path),
        "output": str(out),
        "n_rows": int(len(result)),
        "channels": result["channel"].value_counts().to_dict() if not result.empty else {},
        "selected_fraction_by_channel": (
            result.groupby("channel")["selected_fraction"].agg(["min", "max", "mean"]).to_dict()
            if not result.empty
            else {}
        ),
        "detector_correction_by_channel": (
            result.groupby("channel")["detector_correction_factor"].agg(["min", "max", "mean"]).to_dict()
            if not result.empty
            else {}
        ),
    }
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Build detector-level ALP signal-efficiency diagnostics.")
    parser.add_argument("--scan-summary", type=Path, default=Path("results/fccee/alp_full_scan_summary.csv"))
    parser.add_argument("--config", type=Path, default=Path("analysis/configs/fccee_zpole_inputs.json"))
    parser.add_argument("--out", type=Path, default=Path("results/fccee/alp_signal_efficiency_map.csv"))
    parser.add_argument("--summary-json", type=Path, default=Path("results/fccee/alp_signal_efficiency_summary.json"))
    parser.add_argument("--tree", default="Delphes")
    args = parser.parse_args()

    df = build_efficiency_map(
        scan_summary=args.scan_summary,
        config_path=args.config,
        out=args.out,
        summary_json=args.summary_json,
        tree_name=args.tree,
    )
    print(f"Wrote {args.out}")
    print(df.groupby("channel")["selected_fraction"].agg(["count", "min", "max", "mean"]).to_string())


if __name__ == "__main__":
    main()
