"""Plot FCC-ee background histograms with example ALP signal hypotheses.

The figure is intended for the paper methods/results discussion. It shows the
two binned observables used by the limit calculation:

* prompt-resolved: diphoton invariant mass, M_gg;
* invisible: recoil-photon energy.

For each observable we overlay one excluded and one non-excluded ALP signal
template using the same binned Asimov criterion as the contour solver.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
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
    from theory.predictions import predict_grid as theory
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
    from theory.predictions import predict_grid as theory  # type: ignore


@dataclass(frozen=True)
class SignalExample:
    label: str
    channel: str
    correction_channel: str
    m_a_gev: float
    g_agg_gev_inv: float
    color: str
    linestyle: str


DEFAULT_EXAMPLES = (
    SignalExample(
        label="Excluded example",
        channel="resolved_prompt",
        correction_channel="resolved_prompt",
        m_a_gev=10.21,
        g_agg_gev_inv=3.0e-5,
        color="#D55E00",
        linestyle="-",
    ),
    SignalExample(
        label="Not excluded example",
        channel="resolved_prompt",
        correction_channel="resolved_prompt",
        m_a_gev=10.21,
        g_agg_gev_inv=1.2e-5,
        color="#0072B2",
        linestyle="--",
    ),
    SignalExample(
        label="Excluded example",
        channel="invisible",
        correction_channel="invisible_lower",
        m_a_gev=0.10,
        g_agg_gev_inv=1.0e-6,
        color="#D55E00",
        linestyle="-",
    ),
    SignalExample(
        label="Not excluded example",
        channel="invisible",
        correction_channel="invisible_lower",
        m_a_gev=0.10,
        g_agg_gev_inv=2.0e-7,
        color="#0072B2",
        linestyle="--",
    ),
)


def normal_bin_fractions(bin_low: np.ndarray, bin_high: np.ndarray, mean: float, sigma: float) -> np.ndarray:
    """Fraction of a Gaussian signal template in each histogram bin."""
    sigma = max(float(sigma), 1.0e-12)
    z_low = (bin_low - mean) / (math.sqrt(2.0) * sigma)
    z_high = (bin_high - mean) / (math.sqrt(2.0) * sigma)
    fractions = 0.5 * (erf(z_high) - erf(z_low))
    total = float(np.sum(fractions))
    if total <= 0.0:
        return np.zeros_like(fractions)
    return fractions / total


def signal_template(
    example: SignalExample,
    config: dict[str, Any],
    background_bins: pd.DataFrame,
    corrections: Any,
) -> dict[str, Any]:
    """Return signal counts per bin and exclusion metrics for one example."""
    base = background_bins[background_bins["channel"] == example.channel].copy()
    if base.empty:
        raise ValueError(f"No background bins for {example.channel!r}")
    base = base.sort_values("bin_low_GeV")
    low = base["bin_low_GeV"].to_numpy(dtype=float)
    high = base["bin_high_GeV"].to_numpy(dtype=float)

    if example.channel == "resolved_prompt":
        observable = example.m_a_gev
        width = max(
            float(config["resolved_mass_resolution_relative"]) * example.m_a_gev,
            float(config["resolved_mass_resolution_min_GeV"]),
        )
        x_label = r"$M_{\gamma\gamma}$ [GeV]"
    elif example.channel == "invisible":
        observable = float(theory.e_gamma_recoil(example.m_a_gev, float(config["sqrt_s_GeV"])))
        width = max(
            float(config["invisible_recoil_resolution_relative"]) * observable,
            float(config["invisible_recoil_resolution_min_GeV"]),
        )
        x_label = r"$E_{\gamma,\mathrm{recoil}}$ [GeV]"
    else:
        raise ValueError(f"Unknown channel {example.channel!r}")

    correction = corrections.factor(example.correction_channel, example.m_a_gev) if corrections is not None else 1.0
    n_signal = expected_events(
        example.m_a_gev,
        example.g_agg_gev_inv,
        config,
        example.channel,
        efficiency_scale=correction,
    )
    n_required, equivalent_background, limit_method = required_signal_events(
        channel=example.channel,
        m_a=example.m_a_gev,
        config=config,
        background=None,
        background_bins=background_bins,
    )
    delta_chi2 = float(config["cl_delta_chi2"]) * (n_signal / n_required) ** 2 if n_required > 0.0 else math.nan
    fractions = normal_bin_fractions(low, high, observable, width)
    return {
        "example": example,
        "bin_low": low,
        "bin_high": high,
        "bin_center": 0.5 * (low + high),
        "signal_events_per_bin": n_signal * fractions,
        "observable": observable,
        "width": width,
        "x_label": x_label,
        "detector_correction_factor": correction,
        "expected_signal_events": n_signal,
        "required_signal_events": n_required,
        "equivalent_background_events": equivalent_background,
        "delta_chi2": delta_chi2,
        "excluded": bool(delta_chi2 >= float(config["cl_delta_chi2"])),
        "limit_method": limit_method,
    }


def _plot_channel(
    ax: plt.Axes,
    background_bins: pd.DataFrame,
    templates: list[dict[str, Any]],
    *,
    channel: str,
    title: str,
) -> None:
    bkg = background_bins[background_bins["channel"] == channel].copy().sort_values("bin_low_GeV")
    x = 0.5 * (bkg["bin_low_GeV"].to_numpy(dtype=float) + bkg["bin_high_GeV"].to_numpy(dtype=float))
    widths = bkg["bin_high_GeV"].to_numpy(dtype=float) - bkg["bin_low_GeV"].to_numpy(dtype=float)
    y = bkg["bkg_events"].to_numpy(dtype=float)
    y_positive = y[y > 0.0]

    ax.bar(
        x,
        y,
        width=widths,
        align="center",
        color="#7A8795",
        edgecolor="#44515F",
        linewidth=0.25,
        alpha=0.62,
        label="SM background",
        zorder=1,
    )

    signal_floor = 1.0 if channel == "resolved_prompt" else 1.0e-3
    max_signal = 0.0
    for template in templates:
        ex = template["example"]
        label = (
            f"{ex.label}: "
            rf"$m_a={ex.m_a_gev:g}$ GeV, "
            rf"$g={ex.g_agg_gev_inv:.1e}$"
            "\n"
            rf"$N_S={template['expected_signal_events']:.2g}$, "
            rf"$N_S^{{req}}={template['required_signal_events']:.2g}$, "
            rf"$\Delta\chi^2={template['delta_chi2']:.2g}$"
        )
        y_signal = np.asarray(template["signal_events_per_bin"], dtype=float)
        max_signal = max(max_signal, float(np.max(y_signal)) if y_signal.size else 0.0)
        y_signal = np.where(y_signal >= signal_floor, y_signal, np.nan)
        ax.step(
            template["bin_center"],
            y_signal,
            where="mid",
            color=ex.color,
            linestyle=ex.linestyle,
            linewidth=2.3,
            label=label,
            zorder=3,
        )
        ax.axvline(template["observable"], color=ex.color, linestyle=":", linewidth=1.2, alpha=0.75)

    ax.set_title(title)
    ax.set_xlabel(templates[0]["x_label"])
    ax.set_ylabel("Expected events per bin at 150 ab$^{-1}$")
    ax.set_yscale("log")
    ymin = signal_floor
    ymax = max(float(np.max(y_positive)) if y_positive.size else 1.0, max_signal) * 2.5
    ax.set_ylim(ymin, ymax)
    ax.grid(True, which="both", alpha=0.16)
    ax.legend(fontsize=7.8, frameon=True, loc="best")


def make_plot(
    *,
    config_path: Path,
    out_png: Path,
    out_pdf: Path,
    summary_csv: Path,
) -> pd.DataFrame:
    config = load_config(config_path)
    background_bins = load_background_bins(config, None)
    if background_bins is None:
        raise FileNotFoundError("Binned background inputs are required.")
    corrections = load_efficiency_corrections(
        config,
        None,
        bool(config.get("use_efficiency_corrections", True)),
        str(config["efficiency_correction_column"]),
    )

    templates = [
        signal_template(example, config, background_bins, corrections)
        for example in DEFAULT_EXAMPLES
    ]
    rows = []
    for template in templates:
        ex = template["example"]
        rows.append(
            {
                "channel": ex.channel,
                "example_label": ex.label,
                "m_a_GeV": ex.m_a_gev,
                "g_agg_GeV_inv": ex.g_agg_gev_inv,
                "observable_GeV": template["observable"],
                "template_width_GeV": template["width"],
                "detector_correction_factor": template["detector_correction_factor"],
                "expected_signal_events": template["expected_signal_events"],
                "required_signal_events": template["required_signal_events"],
                "equivalent_background_events": template["equivalent_background_events"],
                "delta_chi2": template["delta_chi2"],
                "excluded_90cl": template["excluded"],
                "limit_method": template["limit_method"],
            }
        )
    summary = pd.DataFrame(rows)
    summary_csv.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(summary_csv, index=False)

    fig, axes = plt.subplots(1, 2, figsize=(13.4, 5.6), constrained_layout=True)
    _plot_channel(
        axes[0],
        background_bins,
        [t for t in templates if t["example"].channel == "resolved_prompt"],
        channel="resolved_prompt",
        title=r"Prompt-resolved channel: $e^+e^-\to\gamma\gamma\gamma$ background",
    )
    _plot_channel(
        axes[1],
        background_bins,
        [t for t in templates if t["example"].channel == "invisible"],
        channel="invisible",
        title=r"Invisible channel: $e^+e^-\to\gamma\nu\bar{\nu}$ background",
    )
    fig.suptitle(
        r"FCC-ee Z-pole binned backgrounds with example ALP signal templates",
        fontsize=15,
    )
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=250)
    fig.savefig(out_pdf)
    plt.close(fig)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot FCC-ee background histograms with signal examples.")
    parser.add_argument("--config", type=Path, default=Path("analysis/configs/fccee_zpole_inputs.json"))
    parser.add_argument("--out-png", type=Path, default=Path("results/fccee/background_signal_examples.png"))
    parser.add_argument("--out-pdf", type=Path, default=Path("results/fccee/background_signal_examples.pdf"))
    parser.add_argument("--summary-csv", type=Path, default=Path("results/fccee/background_signal_examples_summary.csv"))
    args = parser.parse_args()

    summary = make_plot(
        config_path=args.config,
        out_png=args.out_png,
        out_pdf=args.out_pdf,
        summary_csv=args.summary_csv,
    )
    print(f"Wrote {args.out_png}")
    print(f"Wrote {args.out_pdf}")
    print(f"Wrote {args.summary_csv}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
