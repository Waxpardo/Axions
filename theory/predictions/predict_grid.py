"""Analytic predictions for photophilic ALP associated production."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


ALPHA_EM = 1 / 137.035999084
GEV2_TO_PB = 3.894e8
HBARC_GEV_M = 1.973269804e-16


def width_agg(g_agammagamma: float, m_a: float) -> float:
    """Return Gamma(a -> gamma gamma) in GeV using the 64*pi convention."""
    return g_agammagamma**2 * m_a**3 / (64 * math.pi)


def sigma_associated_pb(g_agammagamma: float, m_a: float, sqrt_s: float) -> float:
    """Return sigma(e+e- -> gamma a) in pb over the full angular range."""
    s = sqrt_s**2
    if m_a >= sqrt_s:
        return 0.0
    sigma_gev2 = ALPHA_EM * g_agammagamma**2 / 12 * (1 - m_a**2 / s) ** 3
    return sigma_gev2 * GEV2_TO_PB


def recoil_energy(m_a: float, sqrt_s: float) -> float:
    """Return the mono-energetic recoil photon energy in GeV."""
    return (sqrt_s**2 - m_a**2) / (2 * sqrt_s)


def alp_momentum(m_a: float, sqrt_s: float) -> float:
    """Return the ALP three-momentum magnitude in the CM frame in GeV."""
    return recoil_energy(m_a, sqrt_s)


def proper_decay_length_m(g_agammagamma: float, m_a: float) -> float:
    """Return c*tau in meters."""
    gamma = width_agg(g_agammagamma, m_a)
    if gamma == 0:
        return math.inf
    return HBARC_GEV_M / gamma


def lab_decay_length_m(g_agammagamma: float, m_a: float, sqrt_s: float) -> float:
    """Return boosted decay length in meters."""
    if m_a == 0:
        return math.inf
    return alp_momentum(m_a, sqrt_s) / m_a * proper_decay_length_m(g_agammagamma, m_a)


def min_opening_angle_rad(m_a: float, sqrt_s: float) -> float:
    """Return the light-ALP estimate Delta theta_min ~= 4 m_a / sqrt(s)."""
    return 4 * m_a / sqrt_s


def log_grid(low: float, high: float, n: int) -> list[float]:
    if n < 2:
        return [low]
    step = (math.log10(high) - math.log10(low)) / (n - 1)
    return [10 ** (math.log10(low) + i * step) for i in range(n)]


def write_grid(path: Path, sqrt_s: float, n_mass: int, g_ref: float) -> None:
    masses = log_grid(1e-2, min(10.0, 0.999 * sqrt_s), n_mass)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "m_a_gev",
                "g_ref_gev_inv",
                "sqrt_s_gev",
                "sigma_pb",
                "width_gev",
                "ctau_m",
                "ell_lab_m",
                "e_recoil_gev",
                "delta_theta_min_rad",
            ],
        )
        writer.writeheader()
        for m_a in masses:
            writer.writerow(
                {
                    "m_a_gev": m_a,
                    "g_ref_gev_inv": g_ref,
                    "sqrt_s_gev": sqrt_s,
                    "sigma_pb": sigma_associated_pb(g_ref, m_a, sqrt_s),
                    "width_gev": width_agg(g_ref, m_a),
                    "ctau_m": proper_decay_length_m(g_ref, m_a),
                    "ell_lab_m": lab_decay_length_m(g_ref, m_a, sqrt_s),
                    "e_recoil_gev": recoil_energy(m_a, sqrt_s),
                    "delta_theta_min_rad": min_opening_angle_rad(m_a, sqrt_s),
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sqrt-s", type=float, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-mass", type=int, default=50)
    parser.add_argument("--g-ref", type=float, default=1e-3)
    args = parser.parse_args()
    write_grid(args.out, args.sqrt_s, args.n_mass, args.g_ref)


if __name__ == "__main__":
    main()

