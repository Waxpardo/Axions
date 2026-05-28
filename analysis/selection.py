"""Selection helpers for invisible and prompt-resolved ALP signatures."""

from __future__ import annotations

import numpy as np


EGAMMA_MIN_GEV = 0.25
THETA_MIN_DEG = 12.4
THETA_MAX_DEG = 155.1
DTHETA_RES_DEG = 0.8
SQRT_S_GEV = 10.58


def survival_prob(length_m: float, ell_a_m: float) -> float:
    """Return P(ALP reaches length_m without decaying)."""
    return float(np.exp(-length_m / ell_a_m))


def select_invisible(photons, met):
    """Select one-photon plus missing-energy events."""
    import awkward as ak

    n_photons = ak.num(photons)
    one_photon = n_photons == 1
    energy_pass = ak.firsts(photons.e) > EGAMMA_MIN_GEV
    return one_photon & energy_pass


def select_resolved(photons):
    """Select prompt-resolved three-photon candidates.

    Pairing and invariant-mass requirements are analysis-specific and will be
    filled after the Belle II closure inputs are locked.
    """
    import awkward as ak

    return ak.num(photons) == 3

