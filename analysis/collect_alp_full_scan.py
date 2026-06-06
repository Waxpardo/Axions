"""Collect detector-level ALP full-scan summaries.

Each Condor point run by `condor/run_alp_full_point.sh` writes one
`full_point_summary.csv`. This helper concatenates those files, checks the
required validation flags, and writes a campaign-level CSV/JSON summary.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"1", "true", "t", "yes", "y", "passed"}


def collect_full_scan(input_dir: Path, out: Path, summary_json: Path) -> pd.DataFrame:
    files = sorted(input_dir.glob("**/full_point_summary.csv"))
    if not files:
        raise FileNotFoundError(f"No full_point_summary.csv files found below {input_dir}")

    frames: list[pd.DataFrame] = []
    for path in files:
        frame = pd.read_csv(path)
        frame["summary_csv"] = str(path)
        frames.append(frame)

    df = pd.concat(frames, ignore_index=True)
    if "signature_validation_passed" not in df.columns and "mass_validation_passed" in df.columns:
        df["signature_validation_passed"] = df["mass_validation_passed"]

    for column in ["gate1_passed", "signature_validation_passed", "mass_validation_passed"]:
        if column in df.columns:
            df[column] = df[column].map(_as_bool)

    sort_columns = [col for col in ["m_a_GeV", "g_agg_GeV_inv", "jobid"] if col in df.columns]
    if sort_columns:
        df = df.sort_values(sort_columns)

    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)

    summary: dict[str, Any] = {
        "input_dir": str(input_dir),
        "output": str(out),
        "n_summary_files": len(files),
        "n_rows": int(len(df)),
    }
    for column in ["gate1_passed", "signature_validation_passed", "mass_validation_passed"]:
        if column in df.columns:
            summary[column] = {
                "passed": int(df[column].sum()),
                "failed": int((~df[column]).sum()),
            }
    if "campaign" in df.columns:
        summary["campaigns"] = sorted(str(item) for item in df["campaign"].dropna().unique())
    if "detector" in df.columns:
        summary["detectors"] = sorted(str(item) for item in df["detector"].dropna().unique())

    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_json.write_text(json.dumps(summary, indent=2) + "\n")
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect detector-level ALP full-scan summaries.")
    parser.add_argument("input_dir", type=Path, help="Campaign directory below results/alp_full_production.")
    parser.add_argument("--out", type=Path, default=Path("results/fccee/alp_full_scan_summary.csv"))
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=Path("results/fccee/alp_full_scan_summary.json"),
    )
    args = parser.parse_args()

    df = collect_full_scan(args.input_dir, args.out, args.summary_json)
    print(f"Wrote {args.out}")
    if {"gate1_passed", "signature_validation_passed"} <= set(df.columns):
        print(
            df[["gate1_passed", "signature_validation_passed"]]
            .value_counts()
            .rename("count")
            .to_string()
        )
    else:
        print(f"Collected {len(df)} rows")


if __name__ == "__main__":
    main()
