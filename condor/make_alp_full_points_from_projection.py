"""Create final detector-level ALP Condor points from a projection CSV."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Build full ALP scan points from projection contours.")
    parser.add_argument("--projection", type=Path, default=Path("results/fccee/fccee_projection.csv"))
    parser.add_argument("--out", type=Path, default=Path("condor/alp_full_points_fccee_z_projection.txt"))
    parser.add_argument("--channels", nargs="+", default=["resolved_prompt", "invisible_lower", "invisible_upper"])
    parser.add_argument("--sqrt-s", type=float, default=91.2)
    parser.add_argument("--nevents", type=int, default=10000)
    parser.add_argument("--campaign", default="fccee_z_full_projection_fullbg_channelaware")
    parser.add_argument("--detector", default="IDEA")
    parser.add_argument("--job-category", default="medium")
    parser.add_argument("--max-points", type=int, default=None)
    args = parser.parse_args()

    df = pd.read_csv(args.projection)
    df = df[df["channel"].isin(args.channels)].copy()
    df = df.sort_values(["channel", "m_a_GeV"], kind="mergesort").reset_index(drop=True)
    if args.max_points is not None:
        df = df.head(args.max_points).copy()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as handle:
        for jobid, row in df.iterrows():
            handle.write(
                f"{jobid} {row['m_a_GeV']:.12g} {row['g_agg_GeV_inv']:.12g} "
                f"{args.sqrt_s:.12g} {args.nevents} {args.campaign} {args.detector} "
                f"{row['channel']} {args.job_category}\n"
            )
    print(f"Wrote {len(df)} full-production points -> {args.out}")


if __name__ == "__main__":
    main()
