#!/usr/bin/env python3
"""Create HTCondor queue files for ALP production mass scans."""

from __future__ import annotations

import argparse
import math
from pathlib import Path


def log_grid(low: float, high: float, n_points: int) -> list[float]:
    if n_points < 1:
        raise ValueError("n_points must be positive")
    if n_points == 1:
        return [low]
    log_low = math.log10(low)
    log_high = math.log10(high)
    return [10 ** (log_low + i * (log_high - log_low) / (n_points - 1)) for i in range(n_points)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--sqrt-s", type=float, required=True, help="Collider center-of-mass energy in GeV.")
    parser.add_argument("--m-min", type=float, default=1e-2)
    parser.add_argument("--m-max", type=float, default=10.0)
    parser.add_argument("--n-mass", type=int, default=50)
    parser.add_argument("--g-ref", type=float, default=1e-4)
    parser.add_argument("--nevents", type=int, default=10000)
    parser.add_argument("--campaign", default="fccee_z_50")
    parser.add_argument("--job-category", default="medium")
    args = parser.parse_args()

    if args.m_min <= 0 or args.m_max <= 0:
        raise ValueError("masses must be positive")
    if args.m_min >= args.m_max:
        raise ValueError("--m-min must be smaller than --m-max")
    if args.m_max >= args.sqrt_s:
        raise ValueError("--m-max must be below sqrt(s)")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    masses = log_grid(args.m_min, args.m_max, args.n_mass)
    with args.out.open("w") as handle:
        for jobid, mass in enumerate(masses):
            handle.write(
                f"{jobid} {mass:.10e} {args.sqrt_s:.10g} {args.g_ref:.10e} "
                f"{args.nevents} {args.campaign} {args.job_category}\n"
            )
    print(f"Wrote {args.out} with {len(masses)} points")


if __name__ == "__main__":
    main()
