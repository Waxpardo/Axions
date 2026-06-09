"""Make a CMS-style prompt-resolved ALP invariant-mass plot.

The plot uses the FCC-ee prompt-resolved background histogram already produced
by the pipeline and overlays an arbitrary ALP signal hypothesis. The black
points are pseudo-data, not real data, and the red curves are the expected
background and signal-plus-background templates.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.special import erf

try:
    from analysis.fccee_projection import (
        expected_events,
        load_background_bins,
        load_config,
        load_efficiency_corrections,
        required_signal_events,
    )
except ModuleNotFoundError:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from analysis.fccee_projection import (  # type: ignore
        expected_events,
        load_background_bins,
        load_config,
        load_efficiency_corrections,
        required_signal_events,
    )


DEFAULT_CONFIG = Path("analysis/configs/fccee_zpole_inputs.json")
DEFAULT_OUT = Path("results/fccee/prompt_resolved_invariant_mass_example.png")


def normal_bin_fractions(bin_low: np.ndarray, bin_high: np.ndarray, mean: float, sigma: float) -> np.ndarray:
    """Gaussian fraction in each histogram bin."""
    sigma = max(float(sigma), 1.0e-12)
    z_low = (bin_low - mean) / (math.sqrt(2.0) * sigma)
    z_high = (bin_high - mean) / (math.sqrt(2.0) * sigma)
    fractions = 0.5 * (erf(z_high) - erf(z_low))
    total = float(np.sum(fractions))
    if total <= 0.0:
        return np.zeros_like(fractions)
    return fractions / total


def poisson_errors(counts: np.ndarray) -> np.ndarray:
    """Simple symmetric errors for plotting pseudo-data."""
    return np.sqrt(np.maximum(counts, 1.0))


def load_resolved_background(config: dict[str, Any], path: Path | None) -> pd.DataFrame:
    bins = load_background_bins(config, path)
    if bins is None:
        raise FileNotFoundError("Binned background CSV is required for this plot.")
    resolved = bins[bins["channel"] == "resolved_prompt"].copy()
    if resolved.empty:
        raise ValueError("Background CSV has no resolved_prompt rows.")
    return resolved.sort_values("bin_low_GeV").reset_index(drop=True)


def make_signal_template(
    *,
    m_a: float,
    g_agg: float,
    config: dict[str, Any],
    background: pd.DataFrame,
    use_efficiency_corrections: bool,
    correction_path: Path | None,
) -> dict[str, Any]:
    low = background["bin_low_GeV"].to_numpy(dtype=float)
    high = background["bin_high_GeV"].to_numpy(dtype=float)
    width = max(
        float(config["resolved_mass_resolution_relative"]) * m_a,
        float(config["resolved_mass_resolution_min_GeV"]),
    )
    fractions = normal_bin_fractions(low, high, m_a, width)

    corrections = load_efficiency_corrections(
        config,
        correction_path,
        use_corrections=use_efficiency_corrections,
        column=str(config.get("efficiency_correction_column", "detector_correction_factor")),
    )
    correction = corrections.factor("resolved_prompt", m_a) if corrections is not None else 1.0
    n_signal = expected_events(
        m_a,
        g_agg,
        config,
        "resolved_prompt",
        efficiency_scale=correction,
    )
    n_required, equivalent_background, limit_method = required_signal_events(
        channel="resolved_prompt",
        m_a=m_a,
        config=config,
        background=None,
        background_bins=pd.concat(
            [
                background.assign(channel="resolved_prompt"),
            ],
            ignore_index=True,
        ),
    )
    delta_chi2 = float(config["cl_delta_chi2"]) * (n_signal / n_required) ** 2 if n_required > 0 else math.nan
    return {
        "signal": n_signal * fractions,
        "template_width_GeV": width,
        "detector_correction_factor": correction,
        "expected_signal_events": n_signal,
        "required_signal_events": n_required,
        "equivalent_background_events": equivalent_background,
        "delta_chi2": delta_chi2,
        "excluded_90cl": bool(delta_chi2 >= float(config["cl_delta_chi2"])),
        "limit_method": limit_method,
    }


def select_window(
    background: pd.DataFrame,
    signal: np.ndarray,
    m_a: float,
    width: float,
    x_min: float | None,
    x_max: float | None,
) -> pd.DataFrame:
    out = background.copy()
    out["signal_events"] = signal
    if x_min is None:
        x_min = max(0.0, m_a - max(8.0 * width, 6.0))
    if x_max is None:
        x_max = m_a + max(8.0 * width, 6.0)
    return out[(out["bin_high_GeV"] >= x_min) & (out["bin_low_GeV"] <= x_max)].copy()


def make_plot(
    *,
    config_path: Path,
    background_bins_path: Path | None,
    efficiency_corrections_path: Path | None,
    m_a: float,
    g_agg: float,
    out_png: Path,
    out_pdf: Path | None,
    summary_csv: Path | None,
    x_min: float | None,
    x_max: float | None,
    data_mode: str,
    seed: int,
    use_efficiency_corrections: bool,
    top_scale: float,
) -> pd.DataFrame:
    config = load_config(config_path)
    background = load_resolved_background(config, background_bins_path)
    template = make_signal_template(
        m_a=m_a,
        g_agg=g_agg,
        config=config,
        background=background,
        use_efficiency_corrections=use_efficiency_corrections,
        correction_path=efficiency_corrections_path,
    )
    window = select_window(
        background,
        np.asarray(template["signal"], dtype=float),
        m_a,
        float(template["template_width_GeV"]),
        x_min,
        x_max,
    )

    x = 0.5 * (window["bin_low_GeV"].to_numpy(dtype=float) + window["bin_high_GeV"].to_numpy(dtype=float))
    xerr = 0.5 * (window["bin_high_GeV"].to_numpy(dtype=float) - window["bin_low_GeV"].to_numpy(dtype=float))
    bkg = window["bkg_events"].to_numpy(dtype=float)
    sig = window["signal_events"].to_numpy(dtype=float)
    s_plus_b = bkg + sig

    rng = np.random.default_rng(seed)
    if data_mode == "poisson-splusb":
        data = rng.poisson(np.maximum(s_plus_b, 0.0)).astype(float)
        data_label = "Pseudo-data"
    elif data_mode == "asimov-splusb":
        data = s_plus_b
        data_label = "Asimov S+B"
    elif data_mode == "asimov-background":
        data = bkg
        data_label = "Asimov background"
    else:
        raise ValueError(f"Unknown data mode {data_mode!r}")
    yerr = poisson_errors(data)

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "mathtext.fontset": "dejavusans",
            "axes.linewidth": 1.0,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": True,
            "ytick.right": True,
        }
    )

    fig, (ax, rax) = plt.subplots(
        2,
        1,
        figsize=(7.2, 7.0),
        sharex=True,
        gridspec_kw={"height_ratios": [3.0, 1.25], "hspace": 0.05},
    )

    if top_scale <= 0.0 or not math.isfinite(top_scale):
        raise ValueError("--top-scale must be positive and finite.")
    top_ylabel = "Events / bin" if top_scale == 1.0 else rf"Events / bin [$10^{{{int(round(math.log10(top_scale)))}}}$]"

    ax.errorbar(
        x,
        data / top_scale,
        yerr=yerr / top_scale,
        xerr=xerr,
        fmt="o",
        color="black",
        markersize=4.2,
        elinewidth=0.9,
        capsize=0,
        label=data_label,
        zorder=5,
    )
    ax.step(x, s_plus_b / top_scale, where="mid", color="#d7191c", linewidth=2.2, label="S+B fit", zorder=4)
    ax.step(x, bkg / top_scale, where="mid", color="#d7191c", linewidth=2.0, linestyle=":", label="B component", zorder=3)

    ax.text(0.00, 1.01, "FCC-ee", transform=ax.transAxes, fontsize=17, fontweight="bold", va="bottom")
    ax.text(0.18, 1.01, "Simulation", transform=ax.transAxes, fontsize=15, style="italic", va="bottom")
    ax.text(
        1.0,
        1.01,
        rf"{config['luminosity_ab_inv']:.0f} ab$^{{-1}}$ ($\sqrt{{s}}={config['sqrt_s_GeV']:.1f}$ GeV)",
        transform=ax.transAxes,
        fontsize=13,
        ha="right",
        va="bottom",
    )
    ax.text(
        0.03,
        0.30,
        r"$e^+e^-\to\gamma a,\ a\to\gamma\gamma$" "\n"
        rf"$m_a={m_a:g}$ GeV, $g_{{a\gamma\gamma}}={g_agg:.1e}$ GeV$^{{-1}}$",
        transform=ax.transAxes,
        fontsize=12,
        va="bottom",
    )
    ax.text(
        0.97,
        0.88,
        "Prompt-resolved\nIDEA-like Delphes",
        transform=ax.transAxes,
        fontsize=12,
        ha="right",
        va="top",
    )
    ax.set_ylabel(top_ylabel)
    ax.legend(frameon=False, fontsize=11, loc="center right", bbox_to_anchor=(0.98, 0.36))
    ax.set_ylim(0.0, max(np.max((data + yerr) / top_scale), np.max(s_plus_b / top_scale)) * 1.22)
    ax.minorticks_on()

    residual = data - bkg
    residual_err = yerr
    band1 = np.sqrt(np.maximum(bkg, 1.0))
    band2 = 2.0 * band1
    rax.fill_between(x, -band2, band2, step="mid", color="#ffe51f", alpha=0.95, label=r"$\pm2\sigma$")
    rax.fill_between(x, -band1, band1, step="mid", color="#24d824", alpha=0.95, label=r"$\pm1\sigma$")
    rax.axhline(0.0, color="#d7191c", linestyle=":", linewidth=1.7)
    rax.step(x, sig, where="mid", color="#d7191c", linewidth=2.1, label="S component")
    rax.errorbar(
        x,
        residual,
        yerr=residual_err,
        xerr=xerr,
        fmt="o",
        color="black",
        markersize=4.2,
        elinewidth=0.9,
        capsize=0,
        zorder=5,
    )
    rax.text(0.98, 0.92, "B component subtracted", transform=rax.transAxes, ha="right", va="top", fontsize=12)
    rax.set_ylabel("Events - B")
    rax.set_xlabel(r"$m_{\gamma\gamma}$ [GeV]")
    rax.legend(frameon=False, fontsize=10, loc="lower left", ncol=3)
    rax.minorticks_on()

    low_resid = np.min(residual - residual_err)
    high_resid = np.max(np.maximum(residual + residual_err, sig + band1))
    symmetric = max(abs(low_resid), abs(high_resid), float(np.max(band2)))
    rax.set_ylim(-1.2 * symmetric, 1.35 * symmetric)
    rax.set_xlim(float(window["bin_low_GeV"].min()), float(window["bin_high_GeV"].max()))

    fig.align_ylabels([ax, rax])
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=220, bbox_inches="tight")
    if out_pdf is not None:
        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)

    summary = pd.DataFrame(
        [
            {
                "m_a_GeV": m_a,
                "g_agg_GeV_inv": g_agg,
                "data_mode": data_mode,
                "seed": seed,
                "top_panel_scale": top_scale,
                "window_low_GeV": float(window["bin_low_GeV"].min()),
                "window_high_GeV": float(window["bin_high_GeV"].max()),
                "template_width_GeV": float(template["template_width_GeV"]),
                "detector_correction_factor": float(template["detector_correction_factor"]),
                "expected_signal_events_total": float(template["expected_signal_events"]),
                "expected_signal_events_window": float(np.sum(sig)),
                "expected_background_events_window": float(np.sum(bkg)),
                "required_signal_events": float(template["required_signal_events"]),
                "delta_chi2": float(template["delta_chi2"]),
                "excluded_90cl": bool(template["excluded_90cl"]),
                "limit_method": str(template["limit_method"]),
                "output_png": str(out_png),
                "output_pdf": str(out_pdf) if out_pdf is not None else "",
            }
        ]
    )
    if summary_csv is not None:
        summary_csv.parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(summary_csv, index=False)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--background-bins", type=Path, default=None)
    parser.add_argument("--efficiency-corrections", type=Path, default=None)
    parser.add_argument("--no-efficiency-corrections", action="store_true")
    parser.add_argument("--mass", type=float, default=10.21, help="ALP mass in GeV.")
    parser.add_argument("--coupling", type=float, default=8.0e-5, help="g_{a gamma gamma} in GeV^-1.")
    parser.add_argument("--x-min", type=float, default=None)
    parser.add_argument("--x-max", type=float, default=None)
    parser.add_argument(
        "--data-mode",
        choices=("poisson-splusb", "asimov-splusb", "asimov-background"),
        default="poisson-splusb",
    )
    parser.add_argument("--seed", type=int, default=1258)
    parser.add_argument(
        "--top-scale",
        type=float,
        default=1.0e6,
        help="Scale factor for top-panel event counts. Default shows millions of events.",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--out-pdf", type=Path, default=None)
    parser.add_argument("--summary", type=Path, default=Path("results/fccee/prompt_resolved_invariant_mass_example_summary.csv"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_pdf = args.out_pdf
    if out_pdf is None and args.out.suffix.lower() == ".png":
        out_pdf = args.out.with_suffix(".pdf")
    summary = make_plot(
        config_path=args.config,
        background_bins_path=args.background_bins,
        efficiency_corrections_path=args.efficiency_corrections,
        m_a=float(args.mass),
        g_agg=float(args.coupling),
        out_png=args.out,
        out_pdf=out_pdf,
        summary_csv=args.summary,
        x_min=args.x_min,
        x_max=args.x_max,
        data_mode=args.data_mode,
        seed=int(args.seed),
        use_efficiency_corrections=not bool(args.no_efficiency_corrections),
        top_scale=float(args.top_scale),
    )
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
