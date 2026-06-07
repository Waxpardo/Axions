"""Build binned FCC-ee background histograms for limit setting.

Resolved background:
  observable = m_gg for all reconstructed photon pairs in events with >=3 photons.

Invisible background:
  observable = recoil photon energy for events with exactly one reconstructed
  photon. This is the variable mapped to m_a through
  E_gamma = (s - m_a^2)/(2 sqrt(s)).

The output CSV is consumed by `analysis/fccee_projection.py`.
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
    from analysis.fccee_background_yields import config_defaults, load_delphes, parse_sigma_pb, invariant_masses
except ModuleNotFoundError:
    from fccee_background_yields import config_defaults, load_delphes, parse_sigma_pb, invariant_masses  # type: ignore


def linear_bins(low: float, high: float, n_bins: int) -> np.ndarray:
    return np.linspace(low, high, n_bins + 1)


def normalized_histogram(values: np.ndarray, bins: np.ndarray, sigma_pb: float, luminosity_ab: float, n_generated: int) -> pd.DataFrame:
    counts, edges = np.histogram(values, bins=bins)
    scale = sigma_pb * luminosity_ab * 1.0e6 / n_generated
    return pd.DataFrame(
        {
            "bin_low_GeV": edges[:-1],
            "bin_high_GeV": edges[1:],
            "raw_entries": counts.astype(int),
            "bkg_events": counts.astype(float) * scale,
        }
    )


def resolved_pair_masses(delphes_root: Path, tree_name: str) -> tuple[np.ndarray, int]:
    ph = load_delphes(delphes_root, tree_name)
    n_photons = ak.num(ph["pt"])
    pair_mass = invariant_masses(ph)
    values = ak.flatten(pair_mass[n_photons >= 3], axis=None)
    return np.asarray(ak.to_numpy(values), dtype=float), int(len(n_photons))


def invisible_recoil_energies(delphes_root: Path, tree_name: str) -> tuple[np.ndarray, int]:
    ph = load_delphes(delphes_root, tree_name)
    n_photons = ak.num(ph["energy"])
    one_photon = n_photons == 1
    energies = ak.flatten(ph["energy"][one_photon], axis=None)
    return np.asarray(ak.to_numpy(energies), dtype=float), int(len(n_photons))


def build_binned_background(
    *,
    resolved_root: Path | None,
    resolved_sigma_pb: float | None,
    resolved_banner: Path | None,
    invisible_root: Path | None,
    invisible_sigma_pb: float | None,
    invisible_banner: Path | None,
    out: Path,
    summary_json: Path,
    luminosity_ab: float,
    resolved_bins: np.ndarray,
    invisible_bins: np.ndarray,
    tree_name: str,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    summaries: dict[str, Any] = {}

    if resolved_root is not None:
        sigma_pb = parse_sigma_pb(resolved_banner, resolved_sigma_pb)
        masses, n_generated = resolved_pair_masses(resolved_root, tree_name)
        df = normalized_histogram(masses, resolved_bins, sigma_pb, luminosity_ab, n_generated)
        df.insert(0, "observable", "mgg_GeV")
        df.insert(0, "channel", "resolved_prompt")
        df["source_root"] = str(resolved_root)
        frames.append(df)
        summaries["resolved_prompt"] = {
            "source_root": str(resolved_root),
            "n_generated": n_generated,
            "raw_entries": int(len(masses)),
            "sigma_pb": sigma_pb,
            "bkg_events_total": float(df["bkg_events"].sum()),
        }

    if invisible_root is not None:
        sigma_pb = parse_sigma_pb(invisible_banner, invisible_sigma_pb)
        energies, n_generated = invisible_recoil_energies(invisible_root, tree_name)
        df = normalized_histogram(energies, invisible_bins, sigma_pb, luminosity_ab, n_generated)
        df.insert(0, "observable", "recoil_energy_GeV")
        df.insert(0, "channel", "invisible")
        df["source_root"] = str(invisible_root)
        frames.append(df)
        summaries["invisible"] = {
            "source_root": str(invisible_root),
            "n_generated": n_generated,
            "raw_entries": int(len(energies)),
            "sigma_pb": sigma_pb,
            "bkg_events_total": float(df["bkg_events"].sum()),
        }

    if not frames:
        raise ValueError("At least one background ROOT file is required.")

    result = pd.concat(frames, ignore_index=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False)

    summary = {
        "output": str(out),
        "luminosity_ab_inv": luminosity_ab,
        "channels": summaries,
        "bins_by_channel": result.groupby("channel").size().to_dict(),
        "bkg_events_by_channel": result.groupby("channel")["bkg_events"].agg(["min", "max", "sum"]).to_dict(),
    }
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Build binned FCC-ee background histograms.")
    parser.add_argument("--resolved-root", type=Path, default=None)
    parser.add_argument("--resolved-banner", type=Path, default=None)
    parser.add_argument("--resolved-sigma-pb", type=float, default=None)
    parser.add_argument("--invisible-root", type=Path, default=None)
    parser.add_argument("--invisible-banner", type=Path, default=None)
    parser.add_argument("--invisible-sigma-pb", type=float, default=None)
    parser.add_argument("--out", type=Path, default=Path("results/fccee/fccee_background_bins.csv"))
    parser.add_argument("--summary-json", type=Path, default=Path("results/fccee/fccee_background_bins_summary.json"))
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help=(
            "Optional locked-inputs JSON, e.g. analysis/configs/fccee_zpole_inputs.json. "
            "When given, luminosity-ab and the invisible recoil-histogram range/binning "
            "default to the values it contains instead of this script's own hardcoded "
            "numbers. Explicit CLI flags always take precedence over the config."
        ),
    )
    parser.add_argument("--luminosity-ab", type=float, default=150.0)
    parser.add_argument("--resolved-low", type=float, default=0.0)
    parser.add_argument("--resolved-high", type=float, default=91.2)
    parser.add_argument("--resolved-bins", type=int, default=240)
    parser.add_argument("--invisible-low", type=float, default=0.0)
    parser.add_argument(
        "--invisible-high",
        type=float,
        default=50.0,
        help="Upper edge for recoil-energy bins. Default extends above sqrt(s)/2 to catch Delphes/ISR smearing.",
    )
    parser.add_argument("--invisible-bins", type=int, default=264)
    parser.add_argument("--tree", default="Delphes")

    # Two-pass parse: first just to discover --config, then overlay its values
    # as argparse defaults (still overridable by explicit CLI flags).
    pre_args, _ = parser.parse_known_args()
    parser.set_defaults(
        **config_defaults(
            pre_args.config,
            {
                "luminosity_ab_inv": "luminosity_ab",
                "invisible_recoil_histogram_high_GeV": "invisible_high",
                "invisible_recoil_histogram_bins": "invisible_bins",
            },
        )
    )
    args = parser.parse_args()

    df = build_binned_background(
        resolved_root=args.resolved_root,
        resolved_sigma_pb=args.resolved_sigma_pb,
        resolved_banner=args.resolved_banner,
        invisible_root=args.invisible_root,
        invisible_sigma_pb=args.invisible_sigma_pb,
        invisible_banner=args.invisible_banner,
        out=args.out,
        summary_json=args.summary_json,
        luminosity_ab=args.luminosity_ab,
        resolved_bins=linear_bins(args.resolved_low, args.resolved_high, args.resolved_bins),
        invisible_bins=linear_bins(args.invisible_low, args.invisible_high, args.invisible_bins),
        tree_name=args.tree,
    )
    print(f"Wrote {args.out}")
    print(df.groupby("channel")["bkg_events"].agg(["count", "min", "max", "sum"]).to_string())


if __name__ == "__main__":
    main()
