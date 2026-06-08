"""Build an AxionLimits-style ALP-photon landscape with FCC-ee overlays.

The default plot uses the full AxionLimits axion-photon landscape, including
dark-matter, astrophysical, and cosmological regions. Plot labels are relabeled
to ALP language for this project, while QCD axion reference regions are kept
explicitly as QCD axion constraints.

The FCC-ee contours are this project's contribution and are read from the
projection CSV produced by ``analysis/fccee_projection.py``.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Iterator

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import patheffects as pe
from matplotlib.colors import to_rgba
from matplotlib.patches import ConnectionPatch

try:
    from analysis.axionlimits import resolve_axionlimits_root
except ModuleNotFoundError:
    from axionlimits import resolve_axionlimits_root  # type: ignore


DEFAULT_PROJECTION = Path("results") / "fccee" / "fccee_projection.csv"
DEFAULT_OUTPUT_STEM = Path("results") / "fccee" / "money_plot_alp_full"
DEFAULT_COMBINED_OUTPUT_STEM = Path("results") / "fccee" / "money_plot_alp_full_combined"
FULL_PARAMETER_SPACE_MARKER = "AxionPhoton_FullParameterSpace"
MASS_AXIS_LABEL = r"$m_a$ [eV]"
COUPLING_AXIS_LABEL = r"$g_{a\gamma\gamma}$ [GeV$^{-1}$]"
CLOSEUP_M_MIN = 1.0e7
CLOSEUP_M_MAX = 1.0e12
CLOSEUP_G_MIN = 1.0e-8
CLOSEUP_G_MAX = 1.0e-1
REFERENCE_FIGSETUP = (
    "fig,ax = FigSetup(xlab='Axion mass [eV]',ylab='Axion-photon coupling [GeV$^{-1}$]',"
    "m_min=1e-24,m_max=1e12,g_min=1e-20,g_max=1e-1,xtick_rotation=0)"
)
CONSTRAINT_SETS = ("generic", "full")

# FCC-ee projection accent palette. The existing AxionLimits regions are solid
# red/green/gray/blue blocks, so the project overlays use a colorblind-safe
# Okabe-Ito blue/orange pair with translucent fills and dashed contours.
FCCEE_INVISIBLE_FILL = "#56B4E9"
FCCEE_INVISIBLE_EDGE = "#0072B2"
FCCEE_PROMPT_FILL = "#E69F00"
FCCEE_PROMPT_EDGE = "#D55E00"
FCCEE_LABEL_COLOR = "white"
LABEL_OUTLINE = [pe.withStroke(linewidth=2.8, foreground="0.12", alpha=0.88)]
SMALL_LABEL_OUTLINE = [pe.withStroke(linewidth=2.1, foreground="0.12", alpha=0.85)]

# Existing-landscape palette. This deliberately avoids the bright FCC-ee blue
# and orange projection colors above.
LANDSCAPE_LAB = "#9E3A53"          # lab, collider, beam dumps
LANDSCAPE_ASTRO = "#3E8C6B"        # stellar, solar, supernova
LANDSCAPE_LOWMASS = "#6D5A7E"      # low-mass lab / haloscope-style bounds
LANDSCAPE_COSMO = "#B7B1A8"        # cosmology / dark-matter / decay regions
LANDSCAPE_QCD = "#E2B84B"          # QCD axion reference band label/legend


@contextmanager
def _temporary_axionlimits_imports(root: Path) -> Iterator[None]:
    """Temporarily import AxionLimits modules and resolve relative data paths."""
    old_cwd = Path.cwd()
    # Resolve to an absolute path *before* inserting into sys.path. We chdir
    # into `root` below, and Python re-resolves relative sys.path entries
    # against the *current* cwd at import time -- a relative entry such as
    # "external/AxionLimits" would then be looked up as
    # "external/AxionLimits/external/AxionLimits" (relative to the new cwd)
    # and `import PlotFuncs` would fail with ModuleNotFoundError even though
    # PlotFuncs.py sits right at the clone root.
    root_str = str(Path(root).resolve())
    inserted = False
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
        inserted = True
    try:
        os.chdir(root)
        yield
    finally:
        os.chdir(old_cwd)
        if inserted:
            try:
                sys.path.remove(root_str)
            except ValueError:
                pass
        for name, module in list(sys.modules.items()):
            if name in {"PlotFuncs", "PlotFuncs_ScalarVector"} and isinstance(module, ModuleType):
                sys.modules.pop(name, None)


def _full_parameter_space_cell(notebook_path: Path) -> str:
    """Return the AxionLimits code cell that makes the detailed full plot."""
    data = json.loads(notebook_path.read_text())
    for cell in data.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        if FULL_PARAMETER_SPACE_MARKER in source:
            lines = []
            for line in source.splitlines():
                if "MySaveFig(" in line:
                    continue
                lines.append(line)
            return "\n".join(lines)
    raise RuntimeError(f"Could not find {FULL_PARAMETER_SPACE_MARKER!r} in {notebook_path}")


def _format_sci(value: float) -> str:
    return f"{value:.12g}"


def build_axionlimits_base_plot(
    axionlimits_root: Path,
    *,
    m_min: float,
    m_max: float,
    g_min: float,
    g_max: float,
) -> tuple[plt.Figure, plt.Axes]:
    """Execute the AxionLimits reference cell and return its figure/axes."""
    notebook_path = axionlimits_root / "UltraSimplifiedPlots.ipynb"
    if not notebook_path.exists():
        raise FileNotFoundError(f"Missing AxionLimits notebook: {notebook_path}")

    source = _full_parameter_space_cell(notebook_path)
    replacement = (
        "fig,ax = FigSetup(xlab=r'$m_a$ [eV]',ylab=r'$g_{a\\gamma\\gamma}$ [GeV$^{-1}$]',"
        f"m_min={_format_sci(m_min)},m_max={_format_sci(m_max)},"
        f"g_min={_format_sci(g_min)},g_max={_format_sci(g_max)},xtick_rotation=0)"
    )
    source = source.replace(REFERENCE_FIGSETUP, replacement)
    prefix = "\n".join(
        [
            "from numpy import *",
            "import matplotlib.pyplot as plt",
            "",
        ]
    )
    namespace: dict[str, object] = {}
    with _temporary_axionlimits_imports(axionlimits_root):
        exec(compile(prefix + source, str(notebook_path), "exec"), namespace)

    fig = namespace.get("fig")
    ax = namespace.get("ax")
    if fig is None or ax is None:
        raise RuntimeError("AxionLimits plot cell did not define fig and ax")
    ax.set_xlim(m_min, m_max)  # type: ignore[attr-defined]
    ax.set_ylim(g_min, g_max)  # type: ignore[attr-defined]
    ax.set_xlabel(MASS_AXIS_LABEL)  # type: ignore[attr-defined]
    ax.set_ylabel(COUPLING_AXIS_LABEL)  # type: ignore[attr-defined]
    for text in list(ax.texts):  # type: ignore[attr-defined]
        if text.get_transform() != ax.transData:  # type: ignore[attr-defined]
            continue
        x, y = text.get_position()
        if not (m_min <= x <= m_max and g_min <= y <= g_max):
            text.set_visible(False)
    return fig, ax  # type: ignore[return-value]


def _hide_out_of_view_text(ax: plt.Axes) -> None:
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    for text in list(ax.texts):
        if text.get_transform() != ax.transData:
            continue
        x, y = text.get_position()
        if not (xmin <= x <= xmax and ymin <= y <= ymax):
            text.set_visible(False)


def _relabel_axion_text_as_alp(ax: plt.Axes) -> None:
    """Use ALP wording on plot labels while preserving QCD axion references."""
    ax.set_xlabel(MASS_AXIS_LABEL)
    ax.set_ylabel(COUPLING_AXIS_LABEL)
    for text in list(ax.texts):
        value = text.get_text()
        lower = value.lower()
        if "qcd axion" in lower:
            continue
        value = value.replace("Axion", "ALP")
        value = value.replace("axion", "ALP")
        text.set_text(value)


def _looks_like(color: np.ndarray, reference: tuple[float, float, float], tol: float = 0.12) -> bool:
    return bool(np.linalg.norm(color[:3] - np.asarray(reference)) < tol)


def _replace_facecolor_family(artist: object, old_rgb: tuple[float, float, float], new_color: str) -> None:
    if not hasattr(artist, "get_facecolor") or not hasattr(artist, "set_facecolor"):
        return
    face = np.asarray(artist.get_facecolor())  # type: ignore[attr-defined]
    if face.size == 0:
        return
    original_shape = face.shape
    rows = face.reshape(-1, 4).copy()
    new_rgb = np.asarray(to_rgba(new_color)[:3])
    changed = False
    for row in rows:
        if row[3] > 0.05 and _looks_like(row, old_rgb):
            row[:3] = new_rgb
            changed = True
    if changed:
        artist.set_facecolor(rows.reshape(original_shape))  # type: ignore[attr-defined]


def _apply_landscape_color_scheme(ax: plt.Axes) -> None:
    """Recolor AxionLimits' native regions to a muted project palette."""
    # These RGB anchors are the colors used by the AxionLimits notebook cell
    # before recoloring: seagreen, maroon, royalblue, and mid-gray.
    replacements = (
        ((0.180, 0.545, 0.341), LANDSCAPE_ASTRO),
        ((0.659, 0.196, 0.275), LANDSCAPE_LAB),
        ((0.255, 0.412, 0.882), LANDSCAPE_LOWMASS),
        ((0.700, 0.700, 0.700), LANDSCAPE_COSMO),
    )
    for artist in list(ax.collections) + list(ax.patches):
        for old_rgb, new_color in replacements:
            _replace_facecolor_family(artist, old_rgb, new_color)


def _recolor_constraint_labels_white(ax: plt.Axes) -> None:
    """Render AxionLimits' native constraint-region labels in white.

    The canonical AxionLimits landscape renders its constraint-region names
    (SHAFT, CAST, Beam dump, Belle-II, ...) in white with a thin dark outline
    so they read cleanly against the filled colored regions. This project's
    executed copy of the notebook cell currently leaves them in their default
    (mostly black) color; recolor them here to match the normal AxionLimits
    look. Must run *before* the FCC-ee overlay and close-up labels are added,
    since those manage their own colors.
    """
    for text in list(ax.texts):
        if text.get_transform() != ax.transData:
            continue
        text.set_color("white")
        text.set_path_effects(LABEL_OUTLINE)


def _add_qcd_axion_label(ax: plt.Axes) -> None:
    """Re-add a visible 'QCD axion' label on the diagonal QCD-axion band.

    AxionLimits' own label for this band sits at g_agg ~ 1.5e-20 GeV^-1
    (see UltraSimplifiedPlots.ipynb), below this project's g_min=1e-19 floor,
    so build_axionlimits_base_plot's out-of-view text filter clips it. Without
    it the gold diagonal band has no name. Re-place the label inside the
    visible portion of the band (full-landscape view only).
    """
    if _is_fcc_ee_closeup(ax):
        return
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    x, y = 2.5e-7, 7.0e-14
    if not (xmin <= x <= xmax and ymin <= y <= ymax):
        return
    ax.text(
        x, y,
        r"{\bf QCD axion}",
        # Kept distinct from the white constraint-region labels: this is a
        # reference band, not an excluded region, and the accent color signals
        # that at a glance. No outline, matching the plot's plain-text style.
        color=LANDSCAPE_QCD,
        fontsize=14,
        rotation=43,
        alpha=0.95,
        ha="center",
        va="center",
        clip_on=True,
        path_effects=SMALL_LABEL_OUTLINE,
        zorder=30,
    )


def _add_landscape_legend(ax: plt.Axes) -> None:
    """Legend for the intro landscape plot without FCC-ee overlays."""
    from matplotlib.patches import Patch

    handles = [
        Patch(facecolor=LANDSCAPE_LAB, edgecolor="0.15", label="Laboratory, collider, beam-dump bounds"),
        Patch(facecolor=LANDSCAPE_ASTRO, edgecolor="0.15", label="Stellar, solar, and supernova bounds"),
        Patch(facecolor=LANDSCAPE_LOWMASS, edgecolor="0.15", label="Low-mass laboratory searches"),
        Patch(facecolor=LANDSCAPE_COSMO, edgecolor="0.15", label="Cosmology / dark-matter / decay regions"),
        Patch(facecolor=LANDSCAPE_QCD, edgecolor="0.15", alpha=0.65, label="QCD axion reference band"),
    ]
    ax.legend(
        handles=handles,
        loc="lower left",
        bbox_to_anchor=(0.018, 0.018),
        fontsize=10,
        frameon=True,
        framealpha=0.94,
        facecolor="white",
        edgecolor="0.30",
        handlelength=1.7,
        borderpad=0.65,
        labelspacing=0.35,
    )


def _add_fcc_ee_legend(ax: plt.Axes) -> None:
    """Add a compact FCC-ee projection legend that works on all plot variants."""
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    handles = [
        Patch(facecolor=FCCEE_INVISIBLE_FILL, edgecolor=FCCEE_INVISIBLE_EDGE, alpha=0.65, lw=1.0,
              label=r"FCC-ee invisible ($e^+e^-\!\to\gamma a$, $a$ escapes)"),
        Line2D([0], [0], color=FCCEE_INVISIBLE_EDGE, lw=2.8, ls="--",
               label="  lower / upper contour"),
        Patch(facecolor=FCCEE_PROMPT_FILL, edgecolor=FCCEE_PROMPT_EDGE, alpha=0.65, lw=1.0,
              label=r"FCC-ee prompt/resolved ($a\!\to\gamma\gamma$ in tracker)"),
        Line2D([0], [0], color=FCCEE_PROMPT_EDGE, lw=3.0, ls="--",
               label="  sensitivity contour"),
    ]
    ax.legend(
        handles=handles,
        loc="lower left",
        bbox_to_anchor=(0.01, 0.01),
        fontsize=10,
        frameon=True,
        framealpha=0.92,
        facecolor="white",
        edgecolor="0.30",
        handlelength=2.2,
        borderpad=0.65,
        labelspacing=0.35,
    )


def _add_generic_legend(ax: plt.Axes) -> None:
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    handles = [
        Patch(facecolor=LANDSCAPE_LAB, edgecolor="black", label="Existing lab / collider / beam dumps"),
        Patch(facecolor=LANDSCAPE_ASTRO, edgecolor="black", label="Existing stellar / helioscope / source bounds"),
        Line2D([0], [0], color=FCCEE_INVISIBLE_EDGE, lw=3.0, ls="--", label="FCC-ee invisible projection"),
        Line2D([0], [0], color=FCCEE_PROMPT_EDGE, lw=3.0, ls="--", label="FCC-ee prompt/resolved projection"),
    ]
    ax.legend(
        handles=handles,
        loc="lower left",
        bbox_to_anchor=(0.02, 0.02),
        fontsize=12,
        frameon=True,
        framealpha=0.92,
        facecolor="white",
        edgecolor="0.25",
        handlelength=2.4,
        borderpad=0.8,
    )


def _set_ev_unit_ticks(ax: plt.Axes) -> None:
    ticks = 10.0 ** np.arange(-12, 13, 3)
    labels = ["peV", "neV", r"$\mu$eV", "meV", "eV", "keV", "MeV", "GeV", "TeV"]
    visible_ticks: list[float] = []
    visible_labels: list[str] = []
    xmin, xmax = ax.get_xlim()
    for tick, label in zip(ticks, labels):
        if xmin <= tick <= xmax:
            visible_ticks.append(float(tick))
            visible_labels.append(label)
    ax.set_xticks(visible_ticks)
    ax.set_xticklabels(visible_labels, rotation=0)


def build_generic_alp_plot(
    axionlimits_root: Path,
    *,
    m_min: float,
    m_max: float,
    g_min: float,
    g_max: float,
    show_qcd_band: bool,
) -> tuple[plt.Figure, plt.Axes]:
    """Build the generic-ALP plot without DM-abundance/cosmology assumptions."""
    with _temporary_axionlimits_imports(axionlimits_root):
        from PlotFuncs import AxionPhoton, FigSetup, line_background

        fig, ax = FigSetup(
            xlab=MASS_AXIS_LABEL,
            ylab=COUPLING_AXIS_LABEL,
            m_min=m_min,
            m_max=m_max,
            g_min=g_min,
            g_max=g_max,
            xtick_rotation=0,
        )

        lab_col = "#a83246"
        stellar_col = "seagreen"

        if show_qcd_band:
            AxionPhoton.QCDAxion(
                ax,
                C_center=abs(5 / 3 - 1.92) * (44 / 3 - 1.92) / 2,
                C_width=0.7,
                vmax=1.1,
                KSVZ_on=False,
                DFSZ_on=False,
            )
            plt.text(
                1.2e-8,
                4.0e-18,
                r"{\bf QCD axion reference}",
                fontsize=17,
                color="goldenrod",
                rotation=43,
                alpha=0.9,
                path_effects=line_background(0.75, "k"),
            )

        # Direct searches and collider bounds. These are the most relevant
        # comparison class for a projected FCC-ee collider sensitivity.
        AxionPhoton.LSW(ax, text_on=True)
        AxionPhoton.ColliderBounds(ax, text_on=True)

        # Constraints on generic ALP production in stars/Sun/SN/source
        # environments. These do not require the ALP to be the dark matter.
        AxionPhoton.Helioscopes(ax, text_on=True, col=stellar_col)
        AxionPhoton.StellarBounds(ax, text_on=True)
        AxionPhoton.LowMassAstroBounds(ax, text_on=False, edgealpha=0.9, lw=0.75)

    ax.text(
            2.0e5,
            1.5e-17,
            "DM-abundance and cosmology-assuming regions omitted",
            color="0.25",
            fontsize=13,
            ha="center",
        )

    ax.set_xlim(m_min, m_max)
    ax.set_ylim(g_min, g_max)
    _relabel_axion_text_as_alp(ax)
    _set_ev_unit_ticks(ax)
    _hide_out_of_view_text(ax)
    _add_generic_legend(ax)
    return fig, ax


def _is_fcc_ee_closeup(ax: plt.Axes) -> bool:
    xmin, xmax = ax.get_xlim()
    return xmin >= 1.0e6 and xmax <= 1.0e13


def _add_manual_label(
    ax: plt.Axes,
    text: str,
    x: float,
    y: float,
    *,
    rotation: float = 0.0,
    fontsize: float = 12.0,
    color: str = "white",
    ha: str = "center",
    va: str = "center",
) -> None:
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    if not (xmin <= x <= xmax and ymin <= y <= ymax):
        return
    ax.text(
        x,
        y,
        text,
        color=color,
        fontsize=fontsize,
        rotation=rotation,
        ha=ha,
        va=va,
        clip_on=True,
        path_effects=SMALL_LABEL_OUTLINE,
        zorder=36,
    )


def _add_closeup_constraint_labels(ax: plt.Axes) -> None:
    """Replace out-of-frame AxionLimits labels with close-up-specific labels."""
    if not _is_fcc_ee_closeup(ax):
        return

    duplicate_keys = (
        "primex",
        "beam",
        "opal",
        "lep",
        "belle",
        "besiii",
        "babar",
        "atlas",
        "cms",
        "lhc",
    )
    for text in list(ax.texts):
        value = text.get_text().lower()
        if any(key in value for key in duplicate_keys):
            text.set_visible(False)

    label_color = "white"
    _add_manual_label(ax, "PrimEx", 2.0e7, 2.0e-4, rotation=-63, fontsize=10.5, color=label_color)
    _add_manual_label(ax, "Beam dumps", 7.5e7, 3.5e-5, rotation=-56, fontsize=12.0, color=label_color)
    _add_manual_label(ax, "OPAL", 1.2e8, 3.0e-2, fontsize=12.0, color=label_color)
    _add_manual_label(ax, "LEP", 4.2e8, 1.5e-2, fontsize=14.0, color=label_color)
    _add_manual_label(ax, "Belle II", 7.5e8, 1.5e-3, rotation=12, fontsize=11.5, color=label_color)
    _add_manual_label(ax, "BESIII", 6.5e8, 1.4e-4, fontsize=11.0, color=label_color)
    _add_manual_label(ax, "BaBar", 3.5e10, 7.0e-3, fontsize=14.0, color=label_color)
    _add_manual_label(ax, "ATLAS", 6.0e9, 3.2e-5, fontsize=11.0, color=label_color)
    _add_manual_label(ax, "CMS", 8.0e10, 5.0e-4, fontsize=11.0, color=label_color)
    _add_manual_label(ax, "LHC", 1.4e11, 2.5e-5, fontsize=11.0, color=label_color)


def _simplify_full_landscape_labels(ax: plt.Axes) -> None:
    """Reduce clutter inside the full-panel collider corner.

    The combined money plot already gives this region its own zoom panel. In
    the full panel we keep a category-level label and hide the individual
    collider/beam-dump labels that become unreadable at full-landscape scale.
    """
    if _is_fcc_ee_closeup(ax):
        return

    crowded_keys = (
        "primex",
        "beam",
        "opal",
        "lep",
        "belle",
        "besiii",
        "babar",
        "atlas",
        "cms",
        "lhc",
        "miniboone",
    )
    for text in list(ax.texts):
        value = text.get_text().lower()
        if any(key in value for key in crowded_keys):
            text.set_visible(False)

    _add_manual_label(
        ax,
        "Collider and\nbeam-dump bounds",
        2.5e8,
        2.8e-2,
        fontsize=8.6,
        color="white",
    )


def _finite_channel(df: pd.DataFrame, channel: str) -> pd.DataFrame:
    out = df.loc[df["channel"] == channel, ["m_a_GeV", "g_agg_GeV_inv"]].copy()
    out = out.replace([np.inf, -np.inf], np.nan).dropna()
    out = out[(out["m_a_GeV"] > 0.0) & (out["g_agg_GeV_inv"] > 0.0)]
    out = out.sort_values("m_a_GeV", kind="mergesort")
    return out


def _bold(text: str) -> str:
    """Return *text* wrapped for bold rendering in matplotlib's mathtext."""
    # Works without text.usetex; safe to use inside ax.text(...) calls.
    return r"$\mathbf{" + text + r"}$"


def _plot_fcc_ee_projection(ax: plt.Axes, projection_path: Path) -> None:
    """Overlay this project's FCC-ee projected contours on an eV x-axis."""
    df = pd.read_csv(projection_path)
    required = {"m_a_GeV", "g_agg_GeV_inv", "channel"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{projection_path} is missing columns: {sorted(missing)}")

    ymin, ymax = ax.get_ylim()
    xmin, xmax = ax.get_xlim()
    is_closeup = _is_fcc_ee_closeup(ax)

    def _label_anchor(x_ev: np.ndarray, frac: float) -> int:
        """Index of the visible-range data point closest to the given fraction.

        Picks an anchor relative to the portion of the curve that's actually
        inside the current axes view, so the same call produces a sensible
        position whether `ax` is the full landscape or the FCC-ee close-up --
        fixing labels that used to land well in one view and collide with
        AxionLimits' own collider-bound labels (LEP, Belle-II, CMS, ...) in
        the other.
        """
        visible = np.where((x_ev >= xmin) & (x_ev <= xmax))[0]
        pool = visible if visible.size else np.arange(x_ev.size)
        return int(pool[int(np.clip(frac, 0.0, 1.0) * (pool.size - 1))])

    lower = _finite_channel(df, "invisible_lower")
    upper = _finite_channel(df, "invisible_upper")
    if not lower.empty and not upper.empty:
        band = lower.merge(upper, on="m_a_GeV", suffixes=("_lower", "_upper"))
        x_ev = band["m_a_GeV"].to_numpy(dtype=float) * 1.0e9
        y_low = np.clip(band["g_agg_GeV_inv_lower"].to_numpy(dtype=float), ymin, ymax)
        y_high = np.clip(band["g_agg_GeV_inv_upper"].to_numpy(dtype=float), ymin, ymax)
        # Shaded exclusion band
        ax.fill_between(
            x_ev, y_low, y_high,
            color=FCCEE_INVISIBLE_FILL, alpha=0.55, linewidth=0.0, zorder=20,
        )
        # Lower (sensitivity) contour: solid dashed
        ax.plot(x_ev, y_low, color=FCCEE_INVISIBLE_EDGE, lw=3.2, ls="--", solid_capstyle="round", zorder=22)
        # Upper (short-lifetime) contour: lighter dash-dot
        ax.plot(x_ev, y_high, color=FCCEE_INVISIBLE_EDGE, lw=2.2, ls=(0, (6, 2)), solid_capstyle="round", zorder=22)

        i = _label_anchor(x_ev, 0.32 if is_closeup else 0.55)
        lo, hi = max(y_low[i], ymin), max(y_high[i], ymin)
        if hi > lo:
            label_x = x_ev[i]
            label_y = float(np.sqrt(lo * hi))
            if is_closeup:
                label_x = 2.4e7
                label_y = 2.0e-6
                ax.text(
                    label_x, label_y,
                    "FCC-ee\ninvisible",
                    color=FCCEE_LABEL_COLOR,
                    fontsize=14,
                    fontweight="bold",
                    ha="center", va="center",
                    path_effects=LABEL_OUTLINE,
                    zorder=25,
                )

    resolved = _finite_channel(df, "resolved_prompt")
    if not resolved.empty:
        x_ev = resolved["m_a_GeV"].to_numpy(dtype=float) * 1.0e9
        y = np.clip(resolved["g_agg_GeV_inv"].to_numpy(dtype=float), ymin, ymax)
        # Shaded region: everything above the contour is excluded
        ax.fill_between(
            x_ev, y, ymax,
            color=FCCEE_PROMPT_FILL, alpha=0.55, linewidth=0.0, zorder=19,
        )
        ax.plot(x_ev, y, color=FCCEE_PROMPT_EDGE, lw=3.6, ls="--", solid_capstyle="round", zorder=23)

        i = _label_anchor(x_ev, 0.74 if is_closeup else 0.86)
        contour_y = max(y[i], ymin)
        if is_closeup:
            label_x = x_ev[i]
            label_y = float(np.clip(contour_y * 5.0, contour_y * 3.0, ymax * 0.25))
            ax.text(
                label_x, label_y,
                "FCC-ee\nprompt/resolved",
                color=FCCEE_LABEL_COLOR,
                fontsize=13,
                fontweight="bold",
                ha="center", va="center",
                path_effects=LABEL_OUTLINE,
                zorder=25,
            )


def _build_project_plot(
    root: Path,
    projection_path: Path,
    *,
    constraint_set: str,
    m_min: float,
    m_max: float,
    g_min: float,
    g_max: float,
    show_qcd_band: bool,
    include_fcc_ee: bool = True,
) -> tuple[plt.Figure, plt.Axes]:
    if constraint_set == "generic":
        fig, ax = build_generic_alp_plot(
            root,
            m_min=m_min,
            m_max=m_max,
            g_min=g_min,
            g_max=g_max,
            show_qcd_band=show_qcd_band,
        )
    elif constraint_set == "full":
        fig, ax = build_axionlimits_base_plot(
            root,
            m_min=m_min,
            m_max=m_max,
            g_min=g_min,
            g_max=g_max,
        )
    else:
        raise ValueError(f"Unknown constraint set {constraint_set!r}; expected one of {CONSTRAINT_SETS}")
    # Recolor AxionLimits' native constraint labels to white (matching the
    # canonical AxionLimits look) before adding any of this project's own
    # overlay text, which manages its own colors.
    _apply_landscape_color_scheme(ax)
    _recolor_constraint_labels_white(ax)
    if include_fcc_ee:
        _simplify_full_landscape_labels(ax)
    _add_qcd_axion_label(ax)
    if include_fcc_ee:
        _plot_fcc_ee_projection(ax, projection_path)
    _relabel_axion_text_as_alp(ax)
    _add_closeup_constraint_labels(ax)
    # Add a dedicated FCC-ee legend only for the full AxionLimits landscape
    # (generic mode has a combined legend already included in build_generic_alp_plot).
    if include_fcc_ee and constraint_set == "full":
        _add_fcc_ee_legend(ax)
    if not include_fcc_ee and constraint_set == "full":
        _add_landscape_legend(ax)
    return fig, ax


def make_plot(
    axionlimits_dir: Path | None,
    projection_path: Path,
    output_stem: Path,
    *,
    constraint_set: str,
    m_min: float,
    m_max: float,
    g_min: float,
    g_max: float,
    show_qcd_band: bool,
    include_fcc_ee: bool = True,
) -> list[Path]:
    root = resolve_axionlimits_root(axionlimits_dir)
    projection_path = projection_path.resolve()
    output_stem = output_stem.resolve()

    fig, _ = _build_project_plot(
        root,
        projection_path,
        constraint_set=constraint_set,
        m_min=m_min,
        m_max=m_max,
        g_min=g_min,
        g_max=g_max,
        show_qcd_band=show_qcd_band,
        include_fcc_ee=include_fcc_ee,
    )

    output_stem.parent.mkdir(parents=True, exist_ok=True)
    outputs = [output_stem.with_suffix(".png"), output_stem.with_suffix(".pdf")]
    fig.savefig(outputs[0], dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(outputs[1], bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return outputs


def _data_to_image_point(fig: plt.Figure, ax: plt.Axes, x: float, y: float) -> tuple[float, float]:
    fig.canvas.draw()
    _, height = fig.canvas.get_width_height()
    x_pix, y_pix = ax.transData.transform((x, y))
    return float(x_pix), float(height - y_pix)


def _figure_to_rgba(fig: plt.Figure) -> np.ndarray:
    fig.canvas.draw()
    width, height = fig.canvas.get_width_height()
    data = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
    return data.reshape((height, width, 4)).copy()


def _draw_zoom_box(
    ax: plt.Axes,
    *,
    m_min: float,
    m_max: float,
    g_min: float,
    g_max: float,
) -> None:
    x = [m_min, m_max, m_max, m_min, m_min]
    y = [g_min, g_min, g_max, g_max, g_min]
    ax.plot(x, y, color="0.12", lw=2.0, zorder=35)


def make_combined_plot(
    axionlimits_dir: Path | None,
    projection_path: Path,
    output_stem: Path,
    *,
    constraint_set: str,
    m_min: float,
    m_max: float,
    g_min: float,
    g_max: float,
    closeup_m_min: float,
    closeup_m_max: float,
    closeup_g_min: float,
    closeup_g_max: float,
    show_qcd_band: bool,
    include_fcc_ee: bool = True,
) -> list[Path]:
    root = resolve_axionlimits_root(axionlimits_dir)
    projection_path = projection_path.resolve()
    output_stem = output_stem.resolve()

    full_fig, full_ax = _build_project_plot(
        root,
        projection_path,
        constraint_set=constraint_set,
        m_min=m_min,
        m_max=m_max,
        g_min=g_min,
        g_max=g_max,
        show_qcd_band=show_qcd_band,
        include_fcc_ee=include_fcc_ee,
    )
    full_fig.set_size_inches(10.5, 7.5, forward=True)
    full_fig.subplots_adjust(left=0.17, right=0.985, bottom=0.18, top=0.92)
    _draw_zoom_box(
        full_ax,
        m_min=closeup_m_min,
        m_max=closeup_m_max,
        g_min=closeup_g_min,
        g_max=closeup_g_max,
    )
    full_right_top = _data_to_image_point(full_fig, full_ax, closeup_m_max, closeup_g_max)
    full_right_bottom = _data_to_image_point(full_fig, full_ax, closeup_m_max, closeup_g_min)
    full_image = _figure_to_rgba(full_fig)

    zoom_fig, zoom_ax = _build_project_plot(
        root,
        projection_path,
        constraint_set=constraint_set,
        m_min=closeup_m_min,
        m_max=closeup_m_max,
        g_min=closeup_g_min,
        g_max=closeup_g_max,
        show_qcd_band=show_qcd_band,
        include_fcc_ee=include_fcc_ee,
    )
    zoom_fig.set_size_inches(8.6, 7.5, forward=True)
    zoom_fig.subplots_adjust(left=0.18, right=0.985, bottom=0.18, top=0.92)
    zoom_left_top = _data_to_image_point(zoom_fig, zoom_ax, closeup_m_min, closeup_g_max)
    zoom_left_bottom = _data_to_image_point(zoom_fig, zoom_ax, closeup_m_min, closeup_g_min)
    zoom_image = _figure_to_rgba(zoom_fig)

    plt.close(full_fig)
    plt.close(zoom_fig)

    combined_fig = plt.figure(figsize=(18.0, 7.8), facecolor="white")
    grid = combined_fig.add_gridspec(
        1,
        2,
        width_ratios=(1.05, 1.0),
        left=0.02,
        right=0.985,
        bottom=0.03,
        top=0.90,
        wspace=0.045,
    )
    full_panel = combined_fig.add_subplot(grid[0, 0])
    zoom_panel = combined_fig.add_subplot(grid[0, 1])

    full_panel.imshow(full_image, origin="upper")
    zoom_panel.imshow(zoom_image, origin="upper")
    for panel, image, title in (
        (full_panel, full_image, "Full ALP-photon landscape"),
        (zoom_panel, zoom_image, "FCC-ee close-up"),
    ):
        height, width = image.shape[:2]
        panel.set_xlim(0, width)
        panel.set_ylim(height, 0)
        panel.set_aspect("equal")
        panel.axis("off")
        panel.set_title(title, fontsize=15, pad=10)

    for source, target in ((full_right_top, zoom_left_top), (full_right_bottom, zoom_left_bottom)):
        connector = ConnectionPatch(
            xyA=source,
            coordsA=full_panel.transData,
            xyB=target,
            coordsB=zoom_panel.transData,
            color="0.18",
            lw=1.7,
            alpha=0.85,
            clip_on=False,
            zorder=100,
        )
        combined_fig.add_artist(connector)

    combined_fig.suptitle(
        "ALP-photon constraints with FCC-ee Z-pole projections"
        if include_fcc_ee
        else "ALP-photon constraint landscape",
        fontsize=18,
        y=0.985,
    )

    output_stem.parent.mkdir(parents=True, exist_ok=True)
    outputs = [output_stem.with_suffix(".png"), output_stem.with_suffix(".pdf")]
    combined_fig.savefig(outputs[0], dpi=300, bbox_inches="tight", facecolor="white")
    combined_fig.savefig(outputs[1], bbox_inches="tight", facecolor="white")
    plt.close(combined_fig)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Make an AxionLimits-style ALP-photon landscape with FCC-ee contours."
    )
    parser.add_argument("--axionlimits-dir", type=Path, default=None)
    parser.add_argument("--projection", type=Path, default=DEFAULT_PROJECTION)
    parser.add_argument("--output-stem", type=Path, default=DEFAULT_OUTPUT_STEM)
    parser.add_argument(
        "--constraint-set",
        choices=CONSTRAINT_SETS,
        default="full",
        help="Use the full landscape by default, including DM, astro, and cosmology regions.",
    )
    parser.add_argument(
        "--show-qcd-band",
        action="store_true",
        help="Show the QCD axion mass-coupling band as a reference, not a constraint.",
    )
    parser.add_argument(
        "--no-fcc-ee",
        action="store_true",
        help="Draw only the AxionLimits constraint landscape, without FCC-ee projections or legend.",
    )
    parser.add_argument("--m-min", type=float, default=1.0e-12, help="Minimum ALP mass in eV.")
    parser.add_argument("--m-max", type=float, default=1.0e12, help="Maximum ALP mass in eV.")
    parser.add_argument("--g-min", type=float, default=1.0e-19, help="Minimum photon coupling in GeV^-1.")
    parser.add_argument("--g-max", type=float, default=1.0e-1, help="Maximum photon coupling in GeV^-1.")
    parser.add_argument("--closeup-m-min", type=float, default=CLOSEUP_M_MIN)
    parser.add_argument("--closeup-m-max", type=float, default=CLOSEUP_M_MAX)
    parser.add_argument("--closeup-g-min", type=float, default=CLOSEUP_G_MIN)
    parser.add_argument("--closeup-g-max", type=float, default=CLOSEUP_G_MAX)
    parser.add_argument(
        "--also-save-as",
        type=Path,
        default=None,
        help="Optional second output stem for png/pdf copies.",
    )
    parser.add_argument(
        "--combined-output-stem",
        type=Path,
        default=None,
        help="Optional output stem for a two-panel full-plus-close-up money plot.",
    )
    args = parser.parse_args()

    outputs = make_plot(
        args.axionlimits_dir,
        args.projection,
        args.output_stem,
        constraint_set=args.constraint_set,
        m_min=args.m_min,
        m_max=args.m_max,
        g_min=args.g_min,
        g_max=args.g_max,
        show_qcd_band=args.show_qcd_band,
        include_fcc_ee=not args.no_fcc_ee,
    )
    if args.also_save_as:
        extra_stem = args.also_save_as.resolve()
        extra_stem.parent.mkdir(parents=True, exist_ok=True)
        for output in list(outputs):
            target = extra_stem.with_suffix(output.suffix)
            shutil.copyfile(output, target)
            outputs.append(target)

    if args.combined_output_stem:
        outputs.extend(
            make_combined_plot(
                args.axionlimits_dir,
                args.projection,
                args.combined_output_stem,
                constraint_set=args.constraint_set,
                m_min=args.m_min,
                m_max=args.m_max,
                g_min=args.g_min,
                g_max=args.g_max,
                closeup_m_min=args.closeup_m_min,
                closeup_m_max=args.closeup_m_max,
                closeup_g_min=args.closeup_g_min,
                closeup_g_max=args.closeup_g_max,
                show_qcd_band=args.show_qcd_band,
                include_fcc_ee=not args.no_fcc_ee,
            )
        )

    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
