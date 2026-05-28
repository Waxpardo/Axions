"""Write per-point ALP param cards once the UFO parameter names are verified."""

from __future__ import annotations

import math


HBARC_GEV_M = 1.973269804e-16


def width_a(g_agammagamma: float, m_a: float) -> float:
    """Return Gamma(a -> gamma gamma) in GeV using the 64*pi convention."""
    return g_agammagamma**2 * m_a**3 / (64 * math.pi)


def write_param_card(template: str, out: str, m_a: float, g_agammagamma: float) -> None:
    """Write a model-specific param card.

    This is intentionally not implemented until ALP label, PDG id, and coupling
    parameter names are confirmed in models/ALP_linear.
    """
    raise NotImplementedError("Inspect the ALP_linear UFO before editing param cards.")

