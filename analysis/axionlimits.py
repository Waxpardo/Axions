"""Utilities for using AxionLimits axion-photon constraint data.

AxionLimits stores axion-photon files with mass in eV in the first column and
g_agamma in GeV^-1 in the second column. This module keeps that convention at
the boundary and converts masses to GeV for this project's plots.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


AXIONLIMITS_GITHUB_URL = "https://github.com/cajohare/AxionLimits"
AXIONLIMITS_DOCS_URL = "https://cajohare.github.io/AxionLimits/docs/ap.html"
AXIONLIMITS_ZENODO_DOI = "10.5281/zenodo.3932430"

AXION_PHOTON_DIR = Path("limit_data") / "AxionPhoton"
DEFAULT_CONTEXT_FILES = {
    "Laboratory/Collider/LSW": "Combined_Laboratory.txt",
    "Astrophysical": "Combined_Astro.txt",
    "Astrophysical DM": "Combined_DarkMatterAstro.txt",
}
DEFAULT_COLLIDER_FILES = {
    "Belle II": "BelleII.txt",
    "BaBar": "BaBar.txt",
    "LEP": "LEP.txt",
    "BESIII": "BESIII.txt",
    "Beam dumps": "BeamDump.txt",
}


@dataclass(frozen=True)
class ConstraintCurve:
    """One AxionLimits curve in project units."""

    label: str
    source_path: Path
    data: pd.DataFrame


def candidate_roots() -> list[Path]:
    """Return plausible local AxionLimits clone locations."""
    roots: list[Path] = []
    env_root = os.environ.get("AXIONLIMITS_DIR")
    if env_root:
        roots.append(Path(env_root))
    roots.extend(
        [
            Path("external") / "AxionLimits",
            Path("third_party") / "AxionLimits",
            Path("AxionLimits"),
            Path("..") / "AxionLimits",
        ]
    )
    return roots


def resolve_axionlimits_root(axionlimits_dir: str | Path | None = None) -> Path:
    """Find a local AxionLimits checkout and return its root path."""
    roots = [Path(axionlimits_dir)] if axionlimits_dir else candidate_roots()
    for root in roots:
        if (root / AXION_PHOTON_DIR).is_dir():
            return root
    searched = "\n  ".join(str(root) for root in roots)
    raise FileNotFoundError(
        "Could not find a local AxionLimits checkout. Clone it with:\n"
        f"  git clone {AXIONLIMITS_GITHUB_URL} external/AxionLimits\n"
        "or set AXIONLIMITS_DIR to the clone path. Searched:\n"
        f"  {searched}"
    )


def load_curve(path: Path, label: str, mass_unit: str = "eV") -> ConstraintCurve:
    """Load a whitespace-delimited AxionLimits curve.

    The returned dataframe has columns `m_a_GeV` and `g_agg_GeV_inv`.
    """
    if mass_unit != "eV":
        raise ValueError(f"Unsupported mass unit: {mass_unit}")
    raw = np.loadtxt(path, comments="#", ndmin=2)
    if raw.shape[1] < 2:
        raise ValueError(f"Expected at least two columns in {path}")
    df = pd.DataFrame(
        {
            "m_a_GeV": raw[:, 0] * 1.0e-9,
            "g_agg_GeV_inv": raw[:, 1],
        }
    )
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    df = df[(df["m_a_GeV"] > 0.0) & (df["g_agg_GeV_inv"] > 0.0)]
    df = df.sort_values("m_a_GeV", kind="mergesort").reset_index(drop=True)
    return ConstraintCurve(label=label, source_path=path, data=df)


def load_axion_photon_curves(
    axionlimits_dir: str | Path | None = None,
    files: dict[str, str] | None = None,
) -> list[ConstraintCurve]:
    """Load selected axion-photon constraints from a local AxionLimits clone."""
    root = resolve_axionlimits_root(axionlimits_dir)
    selected = files or {**DEFAULT_CONTEXT_FILES, **DEFAULT_COLLIDER_FILES}
    curves: list[ConstraintCurve] = []
    missing: list[Path] = []
    for label, rel_name in selected.items():
        path = root / AXION_PHOTON_DIR / rel_name
        if not path.exists():
            missing.append(path)
            continue
        curves.append(load_curve(path, label))
    if missing:
        missing_text = "\n  ".join(str(path) for path in missing)
        raise FileNotFoundError(f"Missing AxionLimits files:\n  {missing_text}")
    return curves


def summarize_curves(curves: Iterable[ConstraintCurve]) -> pd.DataFrame:
    """Build a compact summary table for loaded curves."""
    rows = []
    for curve in curves:
        data = curve.data
        rows.append(
            {
                "label": curve.label,
                "points": int(len(data)),
                "m_min_GeV": float(data["m_a_GeV"].min()),
                "m_max_GeV": float(data["m_a_GeV"].max()),
                "g_min_GeV_inv": float(data["g_agg_GeV_inv"].min()),
                "g_max_GeV_inv": float(data["g_agg_GeV_inv"].max()),
                "source_path": str(curve.source_path),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check/load AxionLimits axion-photon data.")
    parser.add_argument("--axionlimits-dir", type=Path, default=None)
    parser.add_argument("--context-only", action="store_true")
    args = parser.parse_args()

    files = DEFAULT_CONTEXT_FILES if args.context_only else None
    curves = load_axion_photon_curves(args.axionlimits_dir, files=files)
    print(summarize_curves(curves).to_string(index=False))


if __name__ == "__main__":
    main()
