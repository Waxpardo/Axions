"""Limit-setting helpers for invisible and resolved ALP signatures."""

from __future__ import annotations

import numpy as np
from scipy.optimize import brentq


def delta_chi2(n_meas, n_background, n_signal, sigma):
    """Return the TZ binned Delta chi2 statistic."""
    term_signal = ((n_meas - (n_background + n_signal)) / sigma) ** 2
    term_background = ((n_meas - n_background) / sigma) ** 2
    return np.sum(term_signal - term_background)


def g_limit_invisible(
    m_a,
    sqrt_s,
    luminosity_pb,
    lmax_m,
    sigma_of_g,
    ell_of_g,
    n_target=3.0,
):
    """Solve L*sigma(g)*exp(-Lmax/ell(g)) = n_target at fixed mass."""

    def n_events(g_agammagamma):
        return luminosity_pb * sigma_of_g(g_agammagamma, m_a, sqrt_s) * np.exp(
            -lmax_m / ell_of_g(g_agammagamma, m_a, sqrt_s)
        )

    couplings = np.logspace(-7, -1, 4000)
    yields = np.array([n_events(g) for g in couplings])
    crossings = np.where(np.diff(np.sign(yields - n_target)))[0]
    return [
        brentq(lambda g: n_events(g) - n_target, couplings[i], couplings[i + 1])
        for i in crossings
    ]

