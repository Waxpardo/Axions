"""Build ALP end-of-pipeline histograms from Delphes ROOT output.

The validation target is the detector-level prompt/resolved topology:

    e+ e- -> gamma alp,  alp -> gamma gamma

For each event with at least two reconstructed photons, the script forms all
diphoton pairs and selects the pair with invariant mass closest to the requested
ALP mass. It writes ROOT histograms plus a compact JSON summary.

The required validation is channel-aware:

* resolved channels require a reconstructed diphoton mass near the ALP mass.
* invisible channels require a reconstructed recoil photon near the two-body
  recoil energy, but do not require ALP daughter photons in Delphes.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import awkward as ak
import numpy as np
import uproot


def _asarray(values: Any) -> np.ndarray:
    return np.asarray(ak.to_numpy(values), dtype=float)


def _safe_mean(values: np.ndarray) -> float | None:
    return float(np.mean(values)) if values.size else None


def _safe_std(values: np.ndarray) -> float | None:
    return float(np.std(values)) if values.size else None


def _hist(values: np.ndarray, bins: int, low: float, high: float) -> tuple[np.ndarray, np.ndarray]:
    return np.histogram(values, bins=bins, range=(low, high))


def _canonical_channel(channel: str) -> str:
    text = channel.strip().lower().replace("-", "_")
    if text in {"invisible", "invisible_lower", "invisible_upper"}:
        return "invisible"
    if text in {"resolved", "resolved_prompt", "prompt_resolved"}:
        return "resolved_prompt"
    if text in {"none", "production", "production_only", "no_mass_check"}:
        return "production_only"
    raise ValueError(f"Unknown validation channel: {channel}")


def _photon_arrays(delphes_root: Path, tree_name: str) -> dict[str, Any]:
    with uproot.open(delphes_root) as root_file:
        tree = root_file[tree_name]
        arrays = tree.arrays(
            ["Photon.PT", "Photon.Eta", "Photon.Phi", "Photon.E"],
            library="ak",
        )
    return {
        "pt": arrays["Photon.PT"],
        "eta": arrays["Photon.Eta"],
        "phi": arrays["Photon.Phi"],
        "energy": arrays["Photon.E"],
    }


def _four_vector_components(pt: Any, eta: Any, phi: Any, energy: Any) -> tuple[Any, Any, Any, Any]:
    px = pt * np.cos(phi)
    py = pt * np.sin(phi)
    pz = pt * np.sinh(eta)
    return px, py, pz, energy


def _invariant_mass(e: Any, px: Any, py: Any, pz: Any) -> Any:
    mass2 = e * e - px * px - py * py - pz * pz
    return np.sqrt(np.maximum(mass2, 0.0))


def build_histograms(
    *,
    delphes_root: Path,
    hist_root: Path,
    summary_json: Path,
    m_a_gev: float,
    sqrt_s_gev: float,
    validation_channel: str = "resolved_prompt",
    tree_name: str = "Delphes",
) -> dict[str, Any]:
    channel = _canonical_channel(validation_channel)
    ph = _photon_arrays(delphes_root, tree_name)
    n_photons = ak.num(ph["pt"])
    n_photons_np = np.asarray(ak.to_numpy(n_photons), dtype=int)

    pt = ph["pt"]
    eta = ph["eta"]
    phi = ph["phi"]
    energy = ph["energy"]
    px, py, pz, e = _four_vector_components(pt, eta, phi, energy)

    pairs = ak.combinations(
        ak.zip({"px": px, "py": py, "pz": pz, "e": e, "energy": energy}),
        2,
        fields=["p1", "p2"],
    )
    pair_px = pairs.p1.px + pairs.p2.px
    pair_py = pairs.p1.py + pairs.p2.py
    pair_pz = pairs.p1.pz + pairs.p2.pz
    pair_e = pairs.p1.e + pairs.p2.e
    pair_mass = _invariant_mass(pair_e, pair_px, pair_py, pair_pz)

    all_mgg = _asarray(ak.flatten(pair_mass, axis=None))
    pair_count = ak.num(pair_mass)
    has_pair = pair_count > 0

    best_mgg = np.asarray([], dtype=float)
    if ak.any(has_pair):
        best_index = ak.argmin(abs(pair_mass[has_pair] - m_a_gev), axis=1, keepdims=True)
        best_mgg = _asarray(ak.flatten(pair_mass[has_pair][best_index], axis=None))

    resolved_mask = n_photons >= 3
    resolved_best_mgg = np.asarray([], dtype=float)
    if ak.any(resolved_mask):
        resolved_pair_mass = pair_mass[resolved_mask]
        resolved_best_index = ak.argmin(abs(resolved_pair_mass - m_a_gev), axis=1, keepdims=True)
        resolved_best_mgg = _asarray(ak.flatten(resolved_pair_mass[resolved_best_index], axis=None))

    photon_energy = _asarray(ak.flatten(energy, axis=None))
    leading_energy = np.asarray([], dtype=float)
    if ak.any(n_photons > 0):
        leading_energy = _asarray(ak.max(energy[n_photons > 0], axis=1))

    recoil_energy_expected = (sqrt_s_gev * sqrt_s_gev - m_a_gev * m_a_gev) / (2.0 * sqrt_s_gev)

    mass_window_abs = max(0.05 * m_a_gev, 0.05)
    in_mass_window = (
        int(np.count_nonzero(np.abs(best_mgg - m_a_gev) < mass_window_abs))
        if best_mgg.size
        else 0
    )
    resolved_in_mass_window = (
        int(np.count_nonzero(np.abs(resolved_best_mgg - m_a_gev) < mass_window_abs))
        if resolved_best_mgg.size
        else 0
    )
    recoil_window_abs = max(0.05 * recoil_energy_expected, 0.5)
    leading_recoil_abs_error = (
        abs(float(np.mean(leading_energy)) - recoil_energy_expected) if leading_energy.size else None
    )
    leading_in_recoil_window = (
        int(np.count_nonzero(np.abs(leading_energy - recoil_energy_expected) < recoil_window_abs))
        if leading_energy.size
        else 0
    )

    max_mass_axis = max(2.5 * m_a_gev, sqrt_s_gev)
    max_energy_axis = max(sqrt_s_gev, recoil_energy_expected * 1.4)

    hist_root.parent.mkdir(parents=True, exist_ok=True)
    with uproot.recreate(hist_root) as out:
        out["h_n_photons"] = _hist(n_photons_np.astype(float), 8, -0.5, 7.5)
        out["h_photon_energy"] = _hist(photon_energy, 100, 0.0, max_energy_axis)
        out["h_leading_photon_energy"] = _hist(leading_energy, 100, 0.0, max_energy_axis)
        out["h_mgg_all_pairs"] = _hist(all_mgg, 120, 0.0, max_mass_axis)
        out["h_mgg_best_pair"] = _hist(best_mgg, 120, 0.0, max_mass_axis)
        out["h_mgg_best_pair_ge3_photons"] = _hist(resolved_best_mgg, 120, 0.0, max_mass_axis)

    summary = {
        "mode": "alp_delphes_histograms",
        "delphes_root": str(delphes_root),
        "hist_root": str(hist_root),
        "m_a_GeV": m_a_gev,
        "sqrt_s_GeV": sqrt_s_gev,
        "validation_channel": channel,
        "recoil_energy_expected_GeV": recoil_energy_expected,
        "events": int(n_photons_np.size),
        "events_ge_1_photon": int(np.count_nonzero(n_photons_np >= 1)),
        "events_ge_2_photons": int(np.count_nonzero(n_photons_np >= 2)),
        "events_ge_3_photons": int(np.count_nonzero(n_photons_np >= 3)),
        "mean_reco_photons": _safe_mean(n_photons_np.astype(float)),
        "all_pairs_entries": int(all_mgg.size),
        "best_pairs_entries": int(best_mgg.size),
        "best_mgg_mean_GeV": _safe_mean(best_mgg),
        "best_mgg_std_GeV": _safe_std(best_mgg),
        "best_mgg_abs_error_GeV": (
            abs(float(np.mean(best_mgg)) - m_a_gev) if best_mgg.size else None
        ),
        "mass_window_abs_GeV": mass_window_abs,
        "best_pairs_in_mass_window": in_mass_window,
        "best_pairs_in_mass_window_fraction": (
            in_mass_window / int(best_mgg.size) if best_mgg.size else None
        ),
        "resolved_best_pairs_entries": int(resolved_best_mgg.size),
        "resolved_best_mgg_mean_GeV": _safe_mean(resolved_best_mgg),
        "resolved_best_mgg_std_GeV": _safe_std(resolved_best_mgg),
        "resolved_best_mgg_abs_error_GeV": (
            abs(float(np.mean(resolved_best_mgg)) - m_a_gev) if resolved_best_mgg.size else None
        ),
        "resolved_best_pairs_in_mass_window": resolved_in_mass_window,
        "resolved_best_pairs_in_mass_window_fraction": (
            resolved_in_mass_window / int(resolved_best_mgg.size) if resolved_best_mgg.size else None
        ),
        "photon_energy_mean_GeV": _safe_mean(photon_energy),
        "leading_photon_energy_mean_GeV": _safe_mean(leading_energy),
        "recoil_window_abs_GeV": recoil_window_abs,
        "leading_recoil_abs_error_GeV": leading_recoil_abs_error,
        "leading_photons_in_recoil_window": leading_in_recoil_window,
        "leading_photons_in_recoil_window_fraction": (
            leading_in_recoil_window / int(leading_energy.size) if leading_energy.size else None
        ),
    }

    resolved_mass_ok = (
        summary["resolved_best_mgg_abs_error_GeV"] is not None
        and summary["resolved_best_mgg_abs_error_GeV"] < max(0.20 * m_a_gev, 0.20)
    )
    recoil_ok = (
        summary["leading_recoil_abs_error_GeV"] is not None
        and summary["leading_recoil_abs_error_GeV"] < max(0.20 * recoil_energy_expected, 1.0)
    )
    if channel == "resolved_prompt":
        summary["passed"] = bool(summary["events_ge_3_photons"] > 0 and resolved_mass_ok)
        summary["validation_reason"] = "resolved_prompt_requires_ge3_photons_and_mgg_near_ma"
    elif channel == "invisible":
        summary["passed"] = bool(summary["events_ge_1_photon"] > 0 and recoil_ok)
        summary["validation_reason"] = "invisible_requires_recoil_photon_near_two_body_energy"
    else:
        summary["passed"] = bool(summary["events"] > 0)
        summary["validation_reason"] = "production_only_requires_nonempty_delphes_tree"

    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Create ALP Delphes validation histograms.")
    parser.add_argument("delphes_root", type=Path)
    parser.add_argument("--hist-root", type=Path, required=True)
    parser.add_argument("--summary-json", type=Path, required=True)
    parser.add_argument("--m-a", type=float, required=True)
    parser.add_argument("--sqrt-s", type=float, required=True)
    parser.add_argument(
        "--validation-channel",
        default="resolved_prompt",
        help="resolved_prompt, invisible, invisible_lower, invisible_upper, or production_only.",
    )
    parser.add_argument("--tree", default="Delphes")
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    summary = build_histograms(
        delphes_root=args.delphes_root,
        hist_root=args.hist_root,
        summary_json=args.summary_json,
        m_a_gev=args.m_a,
        sqrt_s_gev=args.sqrt_s,
        validation_channel=args.validation_channel,
        tree_name=args.tree,
    )
    print(f"Wrote {args.hist_root}")
    print(f"Wrote {args.summary_json}")
    for key in [
        "passed",
        "validation_channel",
        "events",
        "events_ge_1_photon",
        "events_ge_2_photons",
        "events_ge_3_photons",
        "mean_reco_photons",
        "resolved_best_mgg_mean_GeV",
        "resolved_best_mgg_abs_error_GeV",
        "resolved_best_pairs_in_mass_window_fraction",
        "leading_photon_energy_mean_GeV",
        "leading_recoil_abs_error_GeV",
        "leading_photons_in_recoil_window_fraction",
    ]:
        print(f"{key}: {summary[key]}")
    if args.require_pass and not summary["passed"]:
        raise SystemExit("ALP invariant-mass validation failed.")


if __name__ == "__main__":
    main()
