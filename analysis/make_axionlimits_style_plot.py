"""Build an AxionLimits-style axion-photon landscape with FCC-ee overlays.

The default plot is for a generic photophilic ALP: it keeps direct
lab/collider/beam-dump constraints and stellar/helioscope/source constraints
that do not assume the ALP is the cosmological dark matter. Haloscope, CMB,
ionisation, freeze-in, and dark-matter-decay regions are intentionally omitted
from the default money plot because those answer a different physics question.

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
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from analysis.axionlimits import resolve_axionlimits_root
except ModuleNotFoundError:
    from axionlimits import resolve_axionlimits_root  # type: ignore


DEFAULT_PROJECTION = Path("results") / "fccee" / "fccee_projection.csv"
DEFAULT_OUTPUT_STEM = Path("results") / "fccee" / "money_plot"
FULL_PARAMETER_SPACE_MARKER = "AxionPhoton_FullParameterSpace"
REFERENCE_FIGSETUP = (
    "fig,ax = FigSetup(xlab='Axion mass [eV]',ylab='Axion-photon coupling [GeV$^{-1}$]',"
    "m_min=1e-24,m_max=1e12,g_min=1e-20,g_max=1e-1,xtick_rotation=0)"
)
CONSTRAINT_SETS = ("generic", "full")


@contextmanager
def _temporary_axionlimits_imports(root: Path) -> Iterator[None]:
    """Temporarily import AxionLimits modules and resolve relative data paths."""
    old_cwd = Path.cwd()
    root_str = str(root)
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
        "fig,ax = FigSetup(xlab='Axion mass [eV]',ylab='Axion-photon coupling [GeV$^{-1}$]',"
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


def _add_generic_legend(ax: plt.Axes) -> None:
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    handles = [
        Patch(facecolor="#a83246", edgecolor="black", label="Existing lab / collider / beam dumps"),
        Patch(facecolor="seagreen", edgecolor="black", label="Existing stellar / helioscope / source bounds"),
        Line2D([0], [0], color="#0284c7", lw=3.0, ls="--", label="FCC-ee invisible projection"),
        Line2D([0], [0], color="#16a34a", lw=3.0, ls="--", label="FCC-ee prompt/resolved projection"),
    ]
    ax.legend(
        handles=handles,
        loc="lower left",
        bbox_to_anchor=(0.02, 0.02),
        fontsize=15,
        frameon=True,
        framealpha=0.9,
        facecolor="white",
        edgecolor="0.25",
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
            xlab=r"Axion mass [eV]",
            ylab=r"Axion-photon coupling [GeV$^{-1}$]",
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
    _set_ev_unit_ticks(ax)
    _hide_out_of_view_text(ax)
    _add_generic_legend(ax)
    return fig, ax


def _text_outline(color: str = "white", linewidth: float = 4.5) -> list[pe.AbstractPathEffect]:
    return [pe.withStroke(linewidth=linewidth, foreground=color), pe.Normal()]


def _finite_channel(df: pd.DataFrame, channel: str) -> pd.DataFrame:
    out = df.loc[df["channel"] == channel, ["m_a_GeV", "g_agg_GeV_inv"]].copy()
    out = out.replace([np.inf, -np.inf], np.nan).dropna()
    out = out[(out["m_a_GeV"] > 0.0) & (out["g_agg_GeV_inv"] > 0.0)]
    out = out.sort_values("m_a_GeV", kind="mergesort")
    return out


def _plot_fcc_ee_projection(ax: plt.Axes, projection_path: Path) -> None:
    """Overlay this project's FCC-ee projected contours on an eV x-axis."""
    df = pd.read_csv(projection_path)
    required = {"m_a_GeV", "g_agg_GeV_inv", "channel"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{projection_path} is missing columns: {sorted(missing)}")

    ymin, ymax = ax.get_ylim()

    lower = _finite_channel(df, "invisible_lower")
    upper = _finite_channel(df, "invisible_upper")
    if not lower.empty and not upper.empty:
        band = lower.merge(upper, on="m_a_GeV", suffixes=("_lower", "_upper"))
        x_ev = band["m_a_GeV"].to_numpy(dtype=float) * 1.0e9
        y_low = np.clip(band["g_agg_GeV_inv_lower"].to_numpy(dtype=float), ymin, ymax)
        y_high = np.clip(band["g_agg_GeV_inv_upper"].to_numpy(dtype=float), ymin, ymax)
        ax.fill_between(
            x_ev,
            y_low,
            y_high,
            color="#38bdf8",
            alpha=0.26,
            linewidth=0.0,
            zorder=20,
        )
        ax.plot(x_ev, y_low, color="#0284c7", lw=3.2, ls="--", zorder=22)
        ax.plot(x_ev, y_high, color="#0284c7", lw=2.8, ls=(0, (7, 3)), zorder=22)
        ax.text(
            7.0e8,
            4.0e-6,
            r"{\bf FCC-ee}" + "\n" + r"{\bf invisible}",
            color="#075985",
            fontsize=15,
            ha="center",
            va="center",
            path_effects=_text_outline(),
            zorder=24,
        )

    resolved = _finite_channel(df, "resolved_prompt")
    if not resolved.empty:
        x_ev = resolved["m_a_GeV"].to_numpy(dtype=float) * 1.0e9
        y = np.clip(resolved["g_agg_GeV_inv"].to_numpy(dtype=float), ymin, ymax)
        ax.fill_between(
            x_ev,
            y,
            ymax,
            color="#22c55e",
            alpha=0.20,
            linewidth=0.0,
            zorder=19,
        )
        ax.plot(x_ev, y, color="#16a34a", lw=3.4, ls="--", zorder=23)
        ax.text(
            4.5e10,
            2.2e-4,
            r"{\bf FCC-ee}" + "\n" + r"{\bf prompt/resolved}",
            color="#166534",
            fontsize=14,
            ha="center",
            va="center",
            path_effects=_text_outline(),
            zorder=24,
        )

    ax.text(
        6.0e11,
        4.0e-2,
        r"$e^+e^-\to\gamma a,\ a\to\gamma\gamma$" + "\n" + r"Z pole, $150\,{\rm ab}^{-1}$",
        fontsize=12,
        color="black",
        ha="right",
        va="top",
        path_effects=_text_outline(linewidth=3.5),
        zorder=24,
    )


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
) -> list[Path]:
    root = resolve_axionlimits_root(axionlimits_dir)
    projection_path = projection_path.resolve()
    output_stem = output_stem.resolve()

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
    _plot_fcc_ee_projection(ax, projection_path)

    output_stem.parent.mkdir(parents=True, exist_ok=True)
    outputs = [output_stem.with_suffix(".png"), output_stem.with_suffix(".pdf")]
    fig.savefig(outputs[0], dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(outputs[1], bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Make an AxionLimits-style axion-photon landscape with FCC-ee contours."
    )
    parser.add_argument("--axionlimits-dir", type=Path, default=None)
    parser.add_argument("--projection", type=Path, default=DEFAULT_PROJECTION)
    parser.add_argument("--output-stem", type=Path, default=DEFAULT_OUTPUT_STEM)
    parser.add_argument(
        "--constraint-set",
        choices=CONSTRAINT_SETS,
        default="generic",
        help="Use generic ALP constraints by default; 'full' includes DM/cosmology-assuming regions.",
    )
    parser.add_argument(
        "--show-qcd-band",
        action="store_true",
        help="Show the QCD axion mass-coupling band as a reference, not a constraint.",
    )
    parser.add_argument("--m-min", type=float, default=1.0e-12, help="Minimum axion mass in eV.")
    parser.add_argument("--m-max", type=float, default=1.0e12, help="Maximum axion mass in eV.")
    parser.add_argument("--g-min", type=float, default=1.0e-19, help="Minimum photon coupling in GeV^-1.")
    parser.add_argument("--g-max", type=float, default=1.0e-1, help="Maximum photon coupling in GeV^-1.")
    parser.add_argument(
        "--also-save-as",
        type=Path,
        default=None,
        help="Optional second output stem for png/pdf copies.",
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
    )
    if args.also_save_as:
        extra_stem = args.also_save_as.resolve()
        extra_stem.parent.mkdir(parents=True, exist_ok=True)
        for output in list(outputs):
            target = extra_stem.with_suffix(output.suffix)
            shutil.copyfile(output, target)
            outputs.append(target)

    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
