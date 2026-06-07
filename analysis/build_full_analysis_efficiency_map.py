"""Build a full-analysis ALP efficiency/sensitivity map.

This is the second-pass efficiency map. It uses the completed detector-level
ALP scan and the same binned observables used by the FCC-ee projection:

* invisible: exactly one reconstructed photon, binned in recoil photon energy.
* resolved_prompt: at least three reconstructed photons, binned in the best
  diphoton mass closest to the generated ALP mass.

For each scan point the script computes:

* the Delphes-selected fraction, including lifetime and detector effects;
* the actual signal-bin fractions from Delphes, not a Gaussian approximation;
* the binned Asimov signal count required against the SM background bins;
* the expected selected signal count at 150 ab^-1 for the generated coupling.

The resulting CSV is the right object for deciding how to replace or correct
the flat detector-efficiency approximation in the projection.
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
    from analysis.fccee_projection import angular_acceptance_from_eta_max
    from theory.predictions import predict_grid as theory
except ModuleNotFoundError:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from analysis.fccee_background_yields import invariant_masses, load_delphes
    from analysis.fccee_projection import angular_acceptance_from_eta_max
    from theory.predictions import predict_grid as theory


def _truth(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "t", "yes", "passed"}


def _base_channel(channel: str) -> str:
    if channel.startswith("invisible"):
        return "invisible"
    if channel in {"resolved", "resolved_prompt", "prompt_resolved"}:
        return "resolved_prompt"
    raise ValueError(f"Unknown channel: {channel}")


def _flat_efficiency(channel: str, config: dict[str, Any]) -> float:
    acceptance = angular_acceptance_from_eta_max(float(config["eta_max"]))
    photon_eff = float(config["photon_efficiency"])
    if channel == "invisible":
        return acceptance * photon_eff
    if channel == "resolved_prompt":
        return acceptance * photon_eff**3
    raise ValueError(f"Unknown channel: {channel}")


def _analytic_region_probability(channel: str, m_a: float, g_agg: float, sqrt_s: float, config: dict[str, Any]) -> float:
    ell = float(theory.ell_a(m_a, g_agg, sqrt_s))
    if ell <= 0.0:
        return 0.0
    if channel == "invisible":
        return math.exp(-float(config["l_max_m"]) / ell)
    if channel == "resolved_prompt":
        return 1.0 - math.exp(-float(config["l_min_m"]) / ell)
    raise ValueError(f"Unknown channel: {channel}")


def _best_pair_masses(ph: dict[str, Any], m_a: float) -> tuple[np.ndarray, int]:
    n_photons = ak.num(ph["pt"])
    mask = n_photons >= 3
    if not bool(ak.any(mask)):
        return np.asarray([], dtype=float), int(len(n_photons))
    pair_mass = invariant_masses(ph)[mask]
    best_index = ak.argmin(abs(pair_mass - m_a), axis=1, keepdims=True)
    best = ak.flatten(pair_mass[best_index], axis=None)
    return np.asarray(ak.to_numpy(best), dtype=float), int(len(n_photons))


def _one_photon_recoil_energies(ph: dict[str, Any]) -> tuple[np.ndarray, int]:
    n_photons = ak.num(ph["energy"])
    mask = n_photons == 1
    if not bool(ak.any(mask)):
        return np.asarray([], dtype=float), int(len(n_photons))
    values = ak.flatten(ph["energy"][mask], axis=None)
    return np.asarray(ak.to_numpy(values), dtype=float), int(len(n_photons))


def _signal_values(ph: dict[str, Any], channel: str, m_a: float) -> tuple[np.ndarray, int, str]:
    if channel == "invisible":
        values, n_generated = _one_photon_recoil_energies(ph)
        return values, n_generated, "recoil_energy_GeV"
    if channel == "resolved_prompt":
        values, n_generated = _best_pair_masses(ph, m_a)
        return values, n_generated, "best_mgg_GeV"
    raise ValueError(f"Unknown channel: {channel}")


def _background_curve(background_bins: pd.DataFrame, channel: str) -> pd.DataFrame:
    curve = background_bins[background_bins["channel"] == channel].copy()
    if curve.empty:
        raise ValueError(f"No background bins for channel {channel!r}")
    return curve.sort_values("bin_low_GeV")


def _binned_requirement_from_signal_values(
    values: np.ndarray,
    background_curve: pd.DataFrame,
    config: dict[str, Any],
    floor_key: str,
) -> tuple[float, float, float, int]:
    low = background_curve["bin_low_GeV"].to_numpy(dtype=float)
    high = background_curve["bin_high_GeV"].to_numpy(dtype=float)
    bkg = background_curve["bkg_events"].to_numpy(dtype=float)
    bins = np.concatenate([low[:1], high])
    counts, _ = np.histogram(values, bins=bins)
    n_in_bins = int(np.sum(counts))
    floor = float(config[floor_key])
    if n_in_bins <= 0:
        return floor, 0.0, 0.0, 0

    fractions = counts.astype(float) / n_in_bins
    bkg_floor = float(config.get("background_bin_floor_events", 1.0))
    denominator = float(np.sum((fractions * fractions) / np.maximum(bkg, bkg_floor)))
    if denominator <= 0.0:
        return floor, 0.0, 0.0, n_in_bins

    target = math.sqrt(float(config.get("cl_delta_chi2", 2.71)) / denominator)
    target = max(floor, target)
    equivalent_bkg = target * target / float(config.get("cl_delta_chi2", 2.71))
    return target, equivalent_bkg, denominator, n_in_bins


def _projection_rows(path: Path | None) -> pd.DataFrame | None:
    if path is None or not path.exists():
        return None
    df = pd.read_csv(path).copy()
    df["jobid"] = np.arange(len(df), dtype=int)
    return df


def build_full_analysis_efficiency_map(
    *,
    scan_summary: Path,
    config_path: Path,
    background_bins_path: Path,
    projection_path: Path | None,
    out: Path,
    summary_json: Path,
    tree_name: str,
) -> pd.DataFrame:
    config = json.loads(config_path.read_text())
    scan = pd.read_csv(scan_summary)
    background_bins = pd.read_csv(background_bins_path)
    projection = _projection_rows(projection_path)

    if projection is not None:
        keep = ["jobid", "n_target", "bkg_events", "limit_method"]
        scan = scan.merge(projection[keep], on="jobid", how="left", suffixes=("", "_projection"))

    rows: list[dict[str, Any]] = []
    luminosity_pb = float(config["luminosity_ab_inv"]) * 1.0e6

    for _, point in scan.iterrows():
        if not (_truth(point.get("gate1_passed")) and _truth(point.get("signature_validation_passed"))):
            continue

        channel_label = str(point["channel"])
        channel = _base_channel(channel_label)
        m_a = float(point["m_a_GeV"])
        g_agg = float(point["g_agg_GeV_inv"])
        sqrt_s = float(point["sqrt_s_GeV"])
        ph = load_delphes(Path(str(point["delphes_root"])), tree_name)
        values, n_generated, observable = _signal_values(ph, channel, m_a)
        curve = _background_curve(background_bins, channel)
        floor_key = "n_target_invisible" if channel == "invisible" else "n_target_resolved"
        target, equivalent_bkg, denominator, n_in_bins = _binned_requirement_from_signal_values(
            values,
            curve,
            config,
            floor_key,
        )

        n_observable_values = int(values.size)
        observable_fraction = n_observable_values / n_generated if n_generated else 0.0
        bin_acceptance = n_in_bins / n_observable_values if n_observable_values else 0.0
        selected_fraction = n_in_bins / n_generated if n_generated else 0.0
        sigma_pb = float(theory.sigma_prod_pb(m_a, g_agg, sqrt_s))
        expected_selected = luminosity_pb * sigma_pb * selected_fraction
        analysis_strength = expected_selected / target if target > 0.0 else math.nan
        p_region = _analytic_region_probability(channel, m_a, g_agg, sqrt_s, config)
        flat_eff = _flat_efficiency(channel, config)
        flat_selected_fraction = p_region * flat_eff
        flat_expected = luminosity_pb * sigma_pb * flat_selected_fraction
        projection_target = float(point["n_target"]) if "n_target" in point and pd.notna(point["n_target"]) else math.nan
        flat_strength = flat_expected / projection_target if projection_target and projection_target > 0 else math.nan
        conditional_efficiency = selected_fraction / p_region if p_region > 0.0 else math.nan
        detector_correction = conditional_efficiency / flat_eff if flat_eff > 0.0 else math.nan

        rows.append(
            {
                "jobid": int(point["jobid"]),
                "channel": channel_label,
                "base_channel": channel,
                "m_a_GeV": m_a,
                "g_agg_GeV_inv": g_agg,
                "sqrt_s_GeV": sqrt_s,
                "observable": observable,
                "n_generated": n_generated,
                "n_observable_values": n_observable_values,
                "observable_selected_fraction": observable_fraction,
                "n_analysis_selected": n_in_bins,
                "analysis_bin_acceptance_fraction": bin_acceptance,
                "full_analysis_selected_fraction": selected_fraction,
                "analytic_region_probability": p_region,
                "conditional_detector_efficiency": conditional_efficiency,
                "flat_detector_efficiency": flat_eff,
                "detector_correction_factor": detector_correction,
                "sigma_pb": sigma_pb,
                "luminosity_pb_inv": luminosity_pb,
                "expected_selected_events_full_analysis": expected_selected,
                "required_selected_events_full_shape": target,
                "equivalent_background_events_full_shape": equivalent_bkg,
                "binned_sensitivity_denominator": denominator,
                "full_analysis_strength_ratio": analysis_strength,
                "projection_required_events_gaussian": projection_target,
                "expected_selected_events_flat_model": flat_expected,
                "flat_model_strength_ratio": flat_strength,
                "projection_limit_method": point.get("limit_method", ""),
                "delphes_root": str(point["delphes_root"]),
            }
        )

    result = pd.DataFrame(rows).sort_values(["channel", "m_a_GeV", "g_agg_GeV_inv"])
    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False)

    summary = {
        "scan_summary": str(scan_summary),
        "config": str(config_path),
        "background_bins": str(background_bins_path),
        "projection": str(projection_path) if projection_path else None,
        "output": str(out),
        "n_rows": int(len(result)),
        "channels": result["channel"].value_counts().to_dict() if not result.empty else {},
        "selected_fraction_by_channel": (
            result.groupby("channel")["full_analysis_selected_fraction"].agg(["min", "max", "mean"]).to_dict()
            if not result.empty
            else {}
        ),
        "strength_ratio_by_channel": (
            result.groupby("channel")["full_analysis_strength_ratio"].agg(["min", "max", "mean"]).to_dict()
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
    parser = argparse.ArgumentParser(description="Build full-analysis ALP efficiency/sensitivity map.")
    parser.add_argument("--scan-summary", type=Path, default=Path("results/fccee/alp_full_scan_summary.csv"))
    parser.add_argument("--config", type=Path, default=Path("analysis/configs/fccee_zpole_inputs.json"))
    parser.add_argument("--background-bins", type=Path, default=Path("results/fccee/fccee_background_bins.csv"))
    parser.add_argument("--projection", type=Path, default=Path("results/fccee/fccee_projection.csv"))
    parser.add_argument("--out", type=Path, default=Path("results/fccee/alp_full_analysis_efficiency_map.csv"))
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=Path("results/fccee/alp_full_analysis_efficiency_summary.json"),
    )
    parser.add_argument("--tree", default="Delphes")
    args = parser.parse_args()

    df = build_full_analysis_efficiency_map(
        scan_summary=args.scan_summary,
        config_path=args.config,
        background_bins_path=args.background_bins,
        projection_path=args.projection,
        out=args.out,
        summary_json=args.summary_json,
        tree_name=args.tree,
    )
    print(f"Wrote {args.out}")
    print(
        df.groupby("channel")[["full_analysis_selected_fraction", "full_analysis_strength_ratio"]]
        .agg(["count", "min", "max", "mean"])
        .to_string()
    )


if __name__ == "__main__":
    main()
