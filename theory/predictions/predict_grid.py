"""Theory predictions for photophilic ALP validation.

The formulas use the convention

    L = (g_agg / 4) a F_{mu nu} Ftilde^{mu nu}

with g_agg in GeV^-1. Outputs are designed to be consumed by both the
MadGraph/Pythia validation scripts and the analysis limit-setting code.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ALPHA = 1 / 137.035999084
HBAR_C_GEV_M = 1.97326980e-16
HBAR_GEV_S = 6.582119569e-25
GEV2_TO_PB = 3.8937937e8

BELLE2_SQRT_S_GEV = 10.58
FCCEE_Z_SQRT_S_GEV = 91.2
BELLE2_L_MIN_M = 0.14
BELLE2_L_MAX_M = 1.55
FCCEE_L_MIN_M = BELLE2_L_MIN_M
FCCEE_L_MAX_M = BELLE2_L_MAX_M


def gamma_a(m_a: float | np.ndarray, g_agg: float | np.ndarray) -> float | np.ndarray:
    """Gamma(a -> gamma gamma) in GeV"""
    return np.asarray(g_agg) ** 2 * np.asarray(m_a) ** 3 / (64.0 * math.pi)


def tau_a_seconds(m_a: float | np.ndarray, g_agg: float | np.ndarray) -> float | np.ndarray:
    """Proper lifetime in seconds"""
    return HBAR_GEV_S / gamma_a(m_a, g_agg)


def c_tau_a(m_a: float | np.ndarray, g_agg: float | np.ndarray) -> float | np.ndarray:
    """Proper decay length in meters"""
    return HBAR_C_GEV_M / gamma_a(m_a, g_agg)


def e_alp(m_a: float | np.ndarray, sqrt_s: float | np.ndarray) -> float | np.ndarray:
    """ALP energy in the CM frame in GeV"""
    return (np.asarray(sqrt_s) ** 2 + np.asarray(m_a) ** 2) / (2.0 * np.asarray(sqrt_s))


def p_alp(m_a: float | np.ndarray, sqrt_s: float | np.ndarray) -> float | np.ndarray:
    """ALP momentum magnitude in the CM frame in GeV"""
    return (np.asarray(sqrt_s) ** 2 - np.asarray(m_a) ** 2) / (2.0 * np.asarray(sqrt_s))


def e_gamma_recoil(m_a: float | np.ndarray, sqrt_s: float | np.ndarray) -> float | np.ndarray:
    """Recoil photon energy in GeV"""
    return p_alp(m_a, sqrt_s)


def gamma_lorentz(m_a: float | np.ndarray, sqrt_s: float | np.ndarray) -> float | np.ndarray:
    """ALP Lorentz boost factor"""
    return e_alp(m_a, sqrt_s) / np.asarray(m_a)


def ell_a(m_a: float | np.ndarray, g_agg: float | np.ndarray, sqrt_s: float | np.ndarray) -> float | np.ndarray:
    """Boosted lab decay length in meters"""
    return (p_alp(m_a, sqrt_s) / np.asarray(m_a)) * c_tau_a(m_a, g_agg)


def delta_theta_min(m_a: float | np.ndarray, sqrt_s: float | np.ndarray) -> float | np.ndarray:
    """Approximate minimum diphoton opening angle in radians"""
    return 2.0 / gamma_lorentz(m_a, sqrt_s)


def phase_space_factor(m_a: float | np.ndarray, sqrt_s: float | np.ndarray) -> float | np.ndarray:
    """(1 - m_a^2 / s)^3, clipped to zero above threshold"""
    m_arr = np.asarray(m_a)
    s_arr = np.asarray(sqrt_s) ** 2
    phase = (1.0 - m_arr**2 / s_arr) ** 3
    return np.where(m_arr < np.asarray(sqrt_s), phase, 0.0)


def dsigma_dcostheta(
    m_a: float | np.ndarray,
    g_agg: float | np.ndarray,
    sqrt_s: float | np.ndarray,
    cos_theta: float | np.ndarray,
) -> float | np.ndarray:
    """d sigma / d cos(theta_CM) in GeV^-2"""
    return ALPHA * np.asarray(g_agg) ** 2 / 32.0 * (1.0 + np.asarray(cos_theta) ** 2) * phase_space_factor(m_a, sqrt_s)


def sigma_prod(m_a: float | np.ndarray, g_agg: float | np.ndarray, sqrt_s: float | np.ndarray) -> float | np.ndarray:
    """Total e+e- -> gamma a cross section in GeV^-2"""
    return ALPHA * np.asarray(g_agg) ** 2 / 12.0 * phase_space_factor(m_a, sqrt_s)


def sigma_prod_pb(m_a: float | np.ndarray, g_agg: float | np.ndarray, sqrt_s: float | np.ndarray) -> float | np.ndarray:
    """Total e+e- -> gamma a cross section in pb."""
    return sigma_prod(m_a, g_agg, sqrt_s) * GEV2_TO_PB


def p_survive(length_m: float, m_a: float, g_agg: float, sqrt_s: float) -> float:
    """Probability that the ALP reaches length_m before decaying"""
    decay_length = float(ell_a(m_a, g_agg, sqrt_s))
    if decay_length <= 0:
        return 0.0
    return float(np.exp(-length_m / decay_length))


def p_decay_in_detector(l_min_m: float, l_max_m: float, m_a: float, g_agg: float, sqrt_s: float) -> float:
    """Probability to decay between l_min_m and l_max_m."""
    return p_survive(l_min_m, m_a, g_agg, sqrt_s) - p_survive(l_max_m, m_a, g_agg, sqrt_s)


def detector_lengths_for_sqrt_s(
    sqrt_s: float,
    belle2_l_min_m: float = BELLE2_L_MIN_M,
    belle2_l_max_m: float = BELLE2_L_MAX_M,
    fccee_l_min_m: float = FCCEE_L_MIN_M,
    fccee_l_max_m: float = FCCEE_L_MAX_M,
    default_l_min_m: float = BELLE2_L_MIN_M,
    default_l_max_m: float = BELLE2_L_MAX_M,
) -> tuple[str, float, float]:
    """Return detector label and lengths for a collider energy."""
    if math.isclose(sqrt_s, BELLE2_SQRT_S_GEV, rel_tol=0.0, abs_tol=1e-6):
        return "BelleII", belle2_l_min_m, belle2_l_max_m
    if math.isclose(sqrt_s, FCCEE_Z_SQRT_S_GEV, rel_tol=0.0, abs_tol=1e-6):
        return "FCCee_Z", fccee_l_min_m, fccee_l_max_m
    return "custom", default_l_min_m, default_l_max_m


def build_grid(
    m_a_grid: Iterable[float],
    g_grid: Iterable[float],
    sqrt_s_list: Iterable[float],
    belle2_l_min_m: float = BELLE2_L_MIN_M,
    belle2_l_max_m: float = BELLE2_L_MAX_M,
    fccee_l_min_m: float = FCCEE_L_MIN_M,
    fccee_l_max_m: float = FCCEE_L_MAX_M,
    default_l_min_m: float = BELLE2_L_MIN_M,
    default_l_max_m: float = BELLE2_L_MAX_M,
    l_min_m: float | None = None,
    l_max_m: float | None = None,
) -> pd.DataFrame:
    """Build the prediction grid as a pandas DataFrame"""
    if l_min_m is not None:
        belle2_l_min_m = fccee_l_min_m = default_l_min_m = l_min_m
    if l_max_m is not None:
        belle2_l_max_m = fccee_l_max_m = default_l_max_m = l_max_m

    rows: list[dict[str, float | str]] = []
    for sqrt_s in sqrt_s_list:
        detector, l_min_current_m, l_max_current_m = detector_lengths_for_sqrt_s(
            sqrt_s,
            belle2_l_min_m=belle2_l_min_m,
            belle2_l_max_m=belle2_l_max_m,
            fccee_l_min_m=fccee_l_min_m,
            fccee_l_max_m=fccee_l_max_m,
            default_l_min_m=default_l_min_m,
            default_l_max_m=default_l_max_m,
        )
        for m_a in m_a_grid:
            if m_a >= sqrt_s:
                continue
            for g_agg in g_grid:
                width = float(gamma_a(m_a, g_agg))
                dtheta = float(delta_theta_min(m_a, sqrt_s))
                rows.append(
                    {
                        "m_a_GeV": float(m_a),
                        "g_agg_GeV_inv": float(g_agg),
                        "sqrt_s_GeV": float(sqrt_s),
                        "detector": detector,
                        "sigma_pb": float(sigma_prod_pb(m_a, g_agg, sqrt_s)),
                        "sigma_GeV_neg2": float(sigma_prod(m_a, g_agg, sqrt_s)),
                        "E_a_GeV": float(e_alp(m_a, sqrt_s)),
                        "p_a_GeV": float(p_alp(m_a, sqrt_s)),
                        "E_gamma_recoil_GeV": float(e_gamma_recoil(m_a, sqrt_s)),
                        "gamma_lorentz": float(gamma_lorentz(m_a, sqrt_s)),
                        "Gamma_GeV": width,
                        "tau_s": float(tau_a_seconds(m_a, g_agg)),
                        "ctau_m": float(c_tau_a(m_a, g_agg)),
                        "ell_a_m": float(ell_a(m_a, g_agg, sqrt_s)),
                        "dtheta_min_rad": dtheta,
                        "dtheta_min_deg": float(np.degrees(dtheta)),
                        "P_survive_Lmax": p_survive(l_max_current_m, m_a, g_agg, sqrt_s),
                        "P_decay_det": p_decay_in_detector(l_min_current_m, l_max_current_m, m_a, g_agg, sqrt_s),
                        "L_min_m": float(l_min_current_m),
                        "L_max_m": float(l_max_current_m),
                    }
                )
    return pd.DataFrame(rows)


# Aliases
width_agg = gamma_a
recoil_energy = e_gamma_recoil
alp_momentum = p_alp
proper_decay_length_m = c_tau_a
lab_decay_length_m = ell_a
min_opening_angle_rad = delta_theta_min
sigma_associated_pb = lambda g_agg, m_a, sqrt_s: sigma_prod_pb(m_a, g_agg, sqrt_s)


def _log_grid(low: float, high: float, n_points: int) -> np.ndarray:
    if n_points < 2:
        return np.array([low], dtype=float)
    return np.logspace(math.log10(low), math.log10(high), n_points)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build analytic ALP prediction grids.")
    parser.add_argument("--out", type=Path, default=Path("theory/predictions/theory_grid.csv"))
    parser.add_argument("--sqrt-s", type=float, nargs="+", default=[BELLE2_SQRT_S_GEV, FCCEE_Z_SQRT_S_GEV])
    parser.add_argument("--m-min", type=float, default=1e-2)
    parser.add_argument("--m-max", type=float, default=10.0)
    parser.add_argument("--n-mass", type=int, default=50)
    parser.add_argument("--g-min", type=float, default=1e-6)
    parser.add_argument("--g-max", type=float, default=1e-2)
    parser.add_argument("--n-g", type=int, default=50)
    parser.add_argument("--belle2-l-min", type=float, default=BELLE2_L_MIN_M)
    parser.add_argument("--belle2-l-max", type=float, default=BELLE2_L_MAX_M)
    parser.add_argument("--fccee-l-min", type=float, default=FCCEE_L_MIN_M)
    parser.add_argument("--fccee-l-max", type=float, default=FCCEE_L_MAX_M)
    parser.add_argument("--default-l-min", type=float, default=BELLE2_L_MIN_M)
    parser.add_argument("--default-l-max", type=float, default=BELLE2_L_MAX_M)
    parser.add_argument("--l-min", type=float, default=None, help="Legacy override applied to every sqrt(s).")
    parser.add_argument("--l-max", type=float, default=None, help="Legacy override applied to every sqrt(s).")
    args = parser.parse_args()

    masses = _log_grid(args.m_min, args.m_max, args.n_mass)
    couplings = _log_grid(args.g_min, args.g_max, args.n_g)
    df = build_grid(
        masses,
        couplings,
        args.sqrt_s,
        belle2_l_min_m=args.belle2_l_min,
        belle2_l_max_m=args.belle2_l_max,
        fccee_l_min_m=args.fccee_l_min,
        fccee_l_max_m=args.fccee_l_max,
        default_l_min_m=args.default_l_min,
        default_l_max_m=args.default_l_max,
        l_min_m=args.l_min,
        l_max_m=args.l_max,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"Generated {len(df)} grid points -> {args.out}")
    print(df.head().to_string(index=False))


if __name__ == "__main__":
    main()
