"""Build FCC-ee background-yield inputs from Delphes ROOT samples.

The output CSV is consumed by `analysis/fccee_projection.py` and has one row per
mass/channel:

    channel,m_a_GeV,bkg_events,bkg_selected_events,...

Background yields are normalized as

    N_B = sigma_pb * L_pb^-1 * N_selected / N_generated.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

import awkward as ak
import numpy as np
import pandas as pd
import uproot


FLOAT_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"


def parse_sigma_pb(path: Path | None, explicit_sigma: float | None) -> float:
    if explicit_sigma is not None:
        return explicit_sigma
    if path is None:
        raise ValueError("Provide --sigma-pb or --banner for each background sample.")
    text = path.read_text(errors="ignore")
    patterns = [
        rf"Integrated weight \(pb\)\s*:\s*({FLOAT_RE})",
        rf"Cross-section\s*:\s*({FLOAT_RE})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    raise ValueError(f"Could not parse cross section in pb from {path}")


def log_grid(low: float, high: float, n: int) -> np.ndarray:
    if n < 2:
        return np.array([low], dtype=float)
    return np.logspace(math.log10(low), math.log10(high), n)


def load_delphes(delphes_root: Path, tree_name: str) -> dict[str, Any]:
    with uproot.open(delphes_root) as root_file:
        tree = root_file[tree_name]
        names = set(tree.keys())
        branches = ["Photon.PT", "Photon.Eta", "Photon.Phi", "Photon.E"]
        if "MissingET.MET" in names:
            branches.append("MissingET.MET")
        arrays = tree.arrays(branches, library="ak")
    out = {
        "pt": arrays["Photon.PT"],
        "eta": arrays["Photon.Eta"],
        "phi": arrays["Photon.Phi"],
        "energy": arrays["Photon.E"],
    }
    if "MissingET.MET" in arrays.fields:
        out["met"] = arrays["MissingET.MET"]
    else:
        out["met"] = ak.zeros_like(ak.num(out["pt"]))
    return out


def invariant_masses(ph: dict[str, Any]) -> Any:
    pt = ph["pt"]
    eta = ph["eta"]
    phi = ph["phi"]
    energy = ph["energy"]
    px = pt * np.cos(phi)
    py = pt * np.sin(phi)
    pz = pt * np.sinh(eta)
    pairs = ak.combinations(
        ak.zip({"px": px, "py": py, "pz": pz, "e": energy}),
        2,
        fields=["p1", "p2"],
    )
    pair_px = pairs.p1.px + pairs.p2.px
    pair_py = pairs.p1.py + pairs.p2.py
    pair_pz = pairs.p1.pz + pairs.p2.pz
    pair_e = pairs.p1.e + pairs.p2.e
    mass2 = pair_e * pair_e - pair_px * pair_px - pair_py * pair_py - pair_pz * pair_pz
    return np.sqrt(np.maximum(mass2, 0.0))


def recoil_energy(m_a: float, sqrt_s: float) -> float:
    return (sqrt_s * sqrt_s - m_a * m_a) / (2.0 * sqrt_s)


def selected_resolved_counts(ph: dict[str, Any], m_a: float, rel_window: float, min_window: float) -> int:
    n_photons = ak.num(ph["pt"])
    pair_mass = invariant_masses(ph)
    width = max(rel_window * m_a, min_window)
    in_window = ak.any(abs(pair_mass - m_a) <= width, axis=1)
    selected = (n_photons >= 3) & in_window
    return int(ak.sum(selected))


def selected_invisible_counts(
    ph: dict[str, Any],
    m_a: float,
    sqrt_s: float,
    rel_window: float,
    min_window: float,
) -> int:
    n_photons = ak.num(ph["energy"])
    leading_energy = ak.max(ph["energy"][n_photons > 0], axis=1)
    met = ak.flatten(ph["met"][n_photons > 0], axis=None)
    expected = recoil_energy(m_a, sqrt_s)
    width = max(rel_window * expected, min_window)
    selected_nonempty = (n_photons[n_photons > 0] == 1) & (abs(leading_energy - expected) <= width) & (met > 0.0)
    return int(ak.sum(selected_nonempty))


def build_yields(
    *,
    resolved_root: Path | None,
    resolved_sigma_pb: float | None,
    resolved_banner: Path | None,
    invisible_root: Path | None,
    invisible_sigma_pb: float | None,
    invisible_banner: Path | None,
    out: Path,
    summary_json: Path,
    sqrt_s: float,
    luminosity_ab: float,
    masses: np.ndarray,
    mass_window_relative: float,
    mass_window_min: float,
    recoil_window_relative: float,
    recoil_window_min: float,
    tree_name: str,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    lumi_pb = luminosity_ab * 1.0e6

    for channel, root_path, sigma_arg, banner, rel_window, min_window in [
        ("resolved_prompt", resolved_root, resolved_sigma_pb, resolved_banner, mass_window_relative, mass_window_min),
        ("invisible", invisible_root, invisible_sigma_pb, invisible_banner, recoil_window_relative, recoil_window_min),
    ]:
        if root_path is None:
            continue
        sigma_pb = parse_sigma_pb(banner, sigma_arg)
        ph = load_delphes(root_path, tree_name)
        n_generated = int(len(ak.num(ph["pt"])))
        if n_generated <= 0:
            raise ValueError(f"No events found in {root_path}")

        for m_a in masses:
            if m_a >= sqrt_s:
                continue
            if channel == "resolved_prompt":
                selected = selected_resolved_counts(ph, float(m_a), rel_window, min_window)
            else:
                selected = selected_invisible_counts(ph, float(m_a), sqrt_s, rel_window, min_window)
            bkg_events = sigma_pb * lumi_pb * selected / n_generated
            rows.append(
                {
                    "channel": channel,
                    "m_a_GeV": float(m_a),
                    "bkg_events": float(bkg_events),
                    "bkg_selected_events": int(selected),
                    "n_generated": n_generated,
                    "sigma_pb": sigma_pb,
                    "luminosity_ab_inv": luminosity_ab,
                    "source_root": str(root_path),
                }
            )

    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("No background samples were provided.")
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)

    summary = {
        "output": str(out),
        "sqrt_s_GeV": sqrt_s,
        "luminosity_ab_inv": luminosity_ab,
        "channels": df["channel"].value_counts().to_dict(),
        "bkg_events_by_channel": df.groupby("channel")["bkg_events"].agg(["min", "max", "mean"]).to_dict(),
    }
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2) + "\n")
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FCC-ee background yield CSV from Delphes ROOT files.")
    parser.add_argument("--resolved-root", type=Path, default=None)
    parser.add_argument("--resolved-banner", type=Path, default=None)
    parser.add_argument("--resolved-sigma-pb", type=float, default=None)
    parser.add_argument("--invisible-root", type=Path, default=None)
    parser.add_argument("--invisible-banner", type=Path, default=None)
    parser.add_argument("--invisible-sigma-pb", type=float, default=None)
    parser.add_argument("--out", type=Path, default=Path("results/fccee/fccee_background_yields.csv"))
    parser.add_argument("--summary-json", type=Path, default=Path("results/fccee/fccee_background_yields_summary.json"))
    parser.add_argument("--sqrt-s", type=float, default=91.2)
    parser.add_argument("--luminosity-ab", type=float, default=150.0)
    parser.add_argument("--m-min", type=float, default=1.0e-2)
    parser.add_argument("--m-max", type=float, default=80.0)
    parser.add_argument("--n-mass", type=int, default=180)
    parser.add_argument("--mass-window-relative", type=float, default=0.05)
    parser.add_argument("--mass-window-min", type=float, default=0.05)
    parser.add_argument("--recoil-window-relative", type=float, default=0.05)
    parser.add_argument("--recoil-window-min", type=float, default=0.5)
    parser.add_argument("--tree", default="Delphes")
    args = parser.parse_args()

    masses = log_grid(args.m_min, args.m_max, args.n_mass)
    df = build_yields(
        resolved_root=args.resolved_root,
        resolved_sigma_pb=args.resolved_sigma_pb,
        resolved_banner=args.resolved_banner,
        invisible_root=args.invisible_root,
        invisible_sigma_pb=args.invisible_sigma_pb,
        invisible_banner=args.invisible_banner,
        out=args.out,
        summary_json=args.summary_json,
        sqrt_s=args.sqrt_s,
        luminosity_ab=args.luminosity_ab,
        masses=masses,
        mass_window_relative=args.mass_window_relative,
        mass_window_min=args.mass_window_min,
        recoil_window_relative=args.recoil_window_relative,
        recoil_window_min=args.recoil_window_min,
        tree_name=args.tree,
    )
    print(f"Wrote {args.out}")
    print(df.groupby("channel")["bkg_events"].agg(["count", "min", "max", "mean"]).to_string())


if __name__ == "__main__":
    main()
