"""Plotting entrypoint for ALP collider projections and constraints."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd
from matplotlib.patches import ConnectionPatch
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import LogLocator

try:
    from analysis.axionlimits import (
        AXIONLIMITS_DOCS_URL,
        AXIONLIMITS_GITHUB_URL,
        DEFAULT_COLLIDER_FILES,
        DEFAULT_CONTEXT_FILES,
        load_axion_photon_curves,
    )
except ModuleNotFoundError:
    from axionlimits import (  # type: ignore
        AXIONLIMITS_DOCS_URL,
        AXIONLIMITS_GITHUB_URL,
        DEFAULT_COLLIDER_FILES,
        DEFAULT_CONTEXT_FILES,
        load_axion_photon_curves,
    )


CONTEXT_STYLES = {
    "Laboratory/Collider/LSW": {
        "color": "#b91c1c",
        "alpha": 0.82,
        "lw": 1.8,
    },
    "Astrophysical": {
        "color": "#15803d",
        "alpha": 0.84,
        "lw": 1.8,
    },
    "Astrophysical DM": {
        "color": "#334155",
        "alpha": 0.78,
        "lw": 1.5,
    },
}

COLLIDER_STYLES = {
    "Belle II": {"color": "#2563eb"},
    "BaBar": {"color": "#7c2d12"},
    "LEP": {"color": "#7e22ce"},
    "BESIII": {"color": "#0891b2"},
    "Beam dumps": {"color": "#ea580c"},
}

PROJECTION_STYLES = {
    "invisible_lower": {"color": "#0f5fb3", "lw": 2.7, "label": "FCC-ee invisible lower"},
    "invisible_upper": {"color": "#f97316", "lw": 2.7, "label": "FCC-ee invisible upper"},
    "resolved_prompt": {"color": "#16a34a", "lw": 3.2, "label": "FCC-ee prompt resolved"},
}

CONTEXT_LABELS = {
    "full": {
        "Laboratory/Collider/LSW": {
            "text": "Laboratory / collider / LSW",
            "xy": (2.0e-5, 3.0e-2),
            "fontsize": 10.5,
        },
        "Astrophysical": {
            "text": "Astrophysical",
            "xy": (3.0e-12, 1.5e-4),
            "fontsize": 10.5,
        },
        "Astrophysical DM": {
            "text": "Astro / cosmology",
            "xy": (5.0e-7, 3.0e-14),
            "fontsize": 10.5,
        },
    },
    "zoom": {},
}

COLLIDER_LABELS = {
    "full": {},
    "zoom": {
        "Belle II": {"text": "Belle II", "xy": (0.95, 1.2e-3), "fontsize": 8.8},
        "BaBar": {"text": "BaBar", "xy": (1.7e-2, 7.0e-3), "fontsize": 8.2},
        "LEP": {"text": "LEP", "xy": (25.0, 3.2e-3), "fontsize": 8.8},
        "BESIII": {"text": "BESIII", "xy": (0.42, 3.0e-4), "fontsize": 8.6},
        "Beam dumps": {"text": "Beam dumps", "xy": (4.0e-2, 1.6e-6), "fontsize": 8.2, "rotation": -33},
    },
}


def _label_with_outline(
    ax,
    x: float,
    y: float,
    text: str,
    *,
    color: str,
    fontsize: float = 9.0,
    rotation: float = 0.0,
    ha: str = "center",
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
        ha=ha,
        va="center",
        rotation=rotation,
        weight="semibold",
        path_effects=[pe.withStroke(linewidth=3.0, foreground="white", alpha=0.9)],
        zorder=12,
    )


def _visible_curve(data: pd.DataFrame, xlim: tuple[float, float], ylim: tuple[float, float]) -> pd.DataFrame:
    """Return finite curve points useful for line/fill plotting in the visible mass window."""
    df = data[["m_a_GeV", "g_agg_GeV_inv"]].replace([np.inf, -np.inf], np.nan).dropna()
    df = df[(df["m_a_GeV"] > 0.0) & (df["g_agg_GeV_inv"] > 0.0)]
    df = df[(df["m_a_GeV"] >= xlim[0] * 0.8) & (df["m_a_GeV"] <= xlim[1] * 1.2)]
    df = df.sort_values("m_a_GeV", kind="mergesort")
    if df.empty:
        return df
    return df.groupby("m_a_GeV", as_index=False)["g_agg_GeV_inv"].median()


def _plot_existing_region(
    ax,
    data: pd.DataFrame,
    *,
    color: str,
    alpha: float,
    lw: float,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
    zorder: int,
) -> None:
    curve = _visible_curve(data, xlim, ylim)
    if curve.empty:
        return
    x = curve["m_a_GeV"].to_numpy(dtype=float)
    y = np.clip(curve["g_agg_GeV_inv"].to_numpy(dtype=float), ylim[0], ylim[1])
    ax.fill_between(x, y, ylim[1], color=color, alpha=alpha, linewidth=0.0, zorder=zorder)
    ax.plot(x, y, color=color, lw=lw, alpha=1.0, zorder=zorder + 1)


def _plot_axionlimits(
    ax,
    axionlimits_dir: Path | None,
    show_individual: bool,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
    label_layout: str,
) -> None:
    if label_layout == "full":
        context_curves = load_axion_photon_curves(axionlimits_dir, DEFAULT_CONTEXT_FILES)
        for curve in context_curves:
            style = CONTEXT_STYLES.get(curve.label, {})
            color = style.get("color", "0.55")
            _plot_existing_region(
                ax,
                curve.data,
                color=color,
                alpha=float(style.get("alpha", 0.12)),
                lw=float(style.get("lw", 1.4)),
                xlim=xlim,
                ylim=ylim,
                zorder=2,
            )
            label = CONTEXT_LABELS.get(label_layout, {}).get(curve.label)
            if label:
                _label_with_outline(
                    ax,
                    *label["xy"],
                    str(label["text"]),
                    color=color,
                    rotation=float(label.get("rotation", 0.0)),
                    fontsize=float(label.get("fontsize", 9.0)),
                )

    if show_individual:
        collider_curves = load_axion_photon_curves(axionlimits_dir, DEFAULT_COLLIDER_FILES)
        for curve in collider_curves:
            style = COLLIDER_STYLES.get(curve.label, {})
            color = style.get("color", "0.35")
            _plot_existing_region(
                ax,
                curve.data,
                color=color,
                alpha=0.88,
                lw=2.0,
                xlim=xlim,
                ylim=ylim,
                zorder=5,
            )
            label = COLLIDER_LABELS.get(label_layout, {}).get(curve.label)
            if label:
                _label_with_outline(
                    ax,
                    *label["xy"],
                    str(label["text"]),
                    color=color,
                    rotation=float(label.get("rotation", 0.0)),
                    fontsize=float(label.get("fontsize", 9.0)),
                )


def _plot_projection(
    ax,
    projection_path: Path,
    label: str,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
    annotate: bool = True,
) -> None:
    df = pd.read_csv(projection_path)
    required = {"m_a_GeV", "g_agg_GeV_inv"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{projection_path} is missing required columns: {sorted(missing)}")

    if "channel" in df.columns:
        groups = {channel: group.sort_values("m_a_GeV") for channel, group in df.groupby("channel", sort=False)}

        if {"invisible_lower", "invisible_upper"} <= set(groups):
            lower = groups["invisible_lower"][["m_a_GeV", "g_agg_GeV_inv"]]
            upper = groups["invisible_upper"][["m_a_GeV", "g_agg_GeV_inv"]]
            band = lower.merge(upper, on="m_a_GeV", suffixes=("_lower", "_upper"))
            if not band.empty:
                ax.fill_between(
                    band["m_a_GeV"],
                    np.clip(band["g_agg_GeV_inv_lower"], ylim[0], ylim[1]),
                    np.clip(band["g_agg_GeV_inv_upper"], ylim[0], ylim[1]),
                    color="#38bdf8",
                    alpha=0.18,
                    zorder=8,
                )
                if annotate:
                    _label_with_outline(
                        ax,
                        5.5e-2,
                        2.2e-5,
                        "FCC-ee\ninvisible",
                        color="#075985",
                        fontsize=9.5,
                    )

        if "resolved_prompt" in groups:
            resolved = groups["resolved_prompt"].copy()
            ax.fill_between(
                resolved["m_a_GeV"],
                np.clip(resolved["g_agg_GeV_inv"], ylim[0], ylim[1]),
                ylim[1],
                color="#22c55e",
                alpha=0.16,
                zorder=7,
            )
            if annotate:
                _label_with_outline(
                    ax,
                    9.0,
                    2.9e-5,
                    "FCC-ee prompt\nresolved",
                    color="#166534",
                    fontsize=9.5,
                )

        for channel, group in groups.items():
            style = PROJECTION_STYLES.get(channel, {"color": "#111827", "lw": 2.8})
            ax.plot(
                group["m_a_GeV"],
                group["g_agg_GeV_inv"],
                lw=float(style.get("lw", 2.8)),
                color=str(style.get("color", "#111827")),
                ls="--",
                solid_capstyle="round",
                zorder=10,
                label=f"{label}: {channel}",
            )
    else:
        df = df.sort_values("m_a_GeV")
        ax.plot(df["m_a_GeV"], df["g_agg_GeV_inv"], lw=3.0, color="#111827", label=label, zorder=10)


def _finish_axes(
    ax,
    *,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
    title: str,
    legend: bool = False,
    source_note: bool = False,
) -> None:
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_xlabel(r"$m_a$ [GeV]", fontsize=14)
    ax.set_ylabel(r"$g_{a\gamma\gamma}$ [GeV$^{-1}$]", fontsize=14)
    ax.set_title(title, fontsize=13, pad=8)
    ax.tick_params(which="both", direction="in", top=True, right=True, length=5, width=1.0)
    ax.tick_params(which="major", length=7, width=1.2)
    ax.xaxis.set_major_locator(LogLocator(base=10.0))
    ax.yaxis.set_major_locator(LogLocator(base=10.0))
    ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1))
    ax.yaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1))
    ax.grid(True, which="major", alpha=0.10, lw=0.8)
    ax.grid(True, which="minor", alpha=0.05, lw=0.5)
    for spine in ax.spines.values():
        spine.set_linewidth(1.4)

    if legend:
        handles = [
            Patch(facecolor="0.45", alpha=0.88, edgecolor="0.25", label="Current bounds: solid fills"),
            Patch(facecolor="#38bdf8", alpha=0.18, edgecolor="#0f5fb3", label="FCC-ee invisible projection"),
            Patch(facecolor="#22c55e", alpha=0.16, edgecolor="#16a34a", label="FCC-ee prompt-resolved projection"),
            Line2D([0], [0], color="#0f5fb3", lw=2.7, ls="--", label="Projection contours: dashed"),
        ]
        ax.legend(handles=handles, loc="lower right", fontsize=7.2, frameon=True, framealpha=0.94)
    if source_note:
        ax.text(
            0.018,
            0.025,
            f"Existing constraints: AxionLimits ({AXIONLIMITS_DOCS_URL})",
            transform=ax.transAxes,
            fontsize=7.3,
            color="0.28",
            path_effects=[pe.withStroke(linewidth=2.5, foreground="white", alpha=0.8)],
            zorder=20,
        )


def _draw_zoom_guides(
    fig,
    ax_full,
    ax_zoom,
    zoom_xlim: tuple[float, float],
    zoom_ylim: tuple[float, float],
) -> None:
    rect = Rectangle(
        (zoom_xlim[0], zoom_ylim[0]),
        zoom_xlim[1] - zoom_xlim[0],
        zoom_ylim[1] - zoom_ylim[0],
        fill=False,
        ec="0.15",
        lw=1.3,
        zorder=30,
    )
    ax_full.add_patch(rect)
    for y in (zoom_ylim[0], zoom_ylim[1]):
        con = ConnectionPatch(
            xyA=(zoom_xlim[1], y),
            coordsA=ax_full.transData,
            xyB=(zoom_xlim[0], y),
            coordsB=ax_zoom.transData,
            color="0.2",
            lw=1.0,
            alpha=0.75,
            zorder=40,
            clip_on=False,
        )
        fig.add_artist(con)


def make_money_plot(
    out: Path,
    axionlimits_dir: Path | None = None,
    projection: Path | None = None,
    projection_label: str = "FCC-ee projection",
    show_individual_constraints: bool = True,
    xlim: tuple[float, float] = (1.0e-2, 1.0e2),
    ylim: tuple[float, float] = (1.0e-8, 1.0e-1),
    full_xlim: tuple[float, float] = (1.0e-15, 1.0e3),
    full_ylim: tuple[float, float] = (1.0e-19, 1.0),
) -> None:
    """Create the main ALP mass/coupling landscape plot."""
    with plt.rc_context(
        {
            "font.family": "serif",
            "mathtext.fontset": "dejavuserif",
            "axes.facecolor": "white",
            "figure.facecolor": "white",
        }
    ):
        fig = plt.figure(figsize=(13.6, 6.6), constrained_layout=True)
        gs = fig.add_gridspec(1, 2, width_ratios=[1.14, 1.0], wspace=0.08)
        ax_full = fig.add_subplot(gs[0, 0])
        ax_zoom = fig.add_subplot(gs[0, 1])

        _finish_axes(
            ax_full,
            xlim=full_xlim,
            ylim=full_ylim,
            title="Full ALP Landscape",
            source_note=True,
        )
        _finish_axes(
            ax_zoom,
            xlim=xlim,
            ylim=ylim,
            title="FCC-ee Z-Pole Zoom",
            legend=True,
        )

        _plot_axionlimits(ax_full, axionlimits_dir, show_individual_constraints, full_xlim, full_ylim, "full")
        _plot_axionlimits(ax_zoom, axionlimits_dir, show_individual_constraints, xlim, ylim, "zoom")
        if projection:
            _plot_projection(ax_full, projection, projection_label, full_xlim, full_ylim, annotate=False)
            _plot_projection(ax_zoom, projection, projection_label, xlim, ylim, annotate=True)
        _draw_zoom_guides(fig, ax_full, ax_zoom, xlim, ylim)
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=300)
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Make ALP constraints/projection plots.")
    parser.add_argument("--out", type=Path, default=Path("results/fccee/money_plot.png"))
    parser.add_argument("--axionlimits-dir", type=Path, default=None)
    parser.add_argument("--projection", type=Path, default=None)
    parser.add_argument("--projection-label", default="FCC-ee projection")
    parser.add_argument("--context-only", action="store_true", help="Hide individual collider curves.")
    parser.add_argument("--xlim", type=float, nargs=2, default=(1.0e-2, 1.0e2), help="Zoom-panel x limits.")
    parser.add_argument("--ylim", type=float, nargs=2, default=(1.0e-8, 1.0e-1))
    parser.add_argument("--full-xlim", type=float, nargs=2, default=(1.0e-15, 1.0e3))
    parser.add_argument("--full-ylim", type=float, nargs=2, default=(1.0e-19, 1.0))
    args = parser.parse_args()

    try:
        make_money_plot(
            out=args.out,
            axionlimits_dir=args.axionlimits_dir,
            projection=args.projection,
            projection_label=args.projection_label,
            show_individual_constraints=not args.context_only,
            xlim=tuple(args.xlim),
            ylim=tuple(args.ylim),
            full_xlim=tuple(args.full_xlim),
            full_ylim=tuple(args.full_ylim),
        )
    except FileNotFoundError as exc:
        print(exc)
        print(f"AxionLimits source: {AXIONLIMITS_GITHUB_URL}")
        raise SystemExit(2) from exc
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
