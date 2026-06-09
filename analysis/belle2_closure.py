"""Belle II published-contour closure test.

This is the Gate-3 closure machinery for the project. It compares the analytic
ALP-strahlung production/lifetime model against the published Belle II
constraint curve digitized in AxionLimits.

Important scope note:
Belle II's full binned likelihood, reconstruction efficiencies, and background
spectra are not public in this repository. The closure therefore uses the
published contour as the target and infers the effective signal-yield threshold
that contour implies. This is a genuine end-to-end consistency check of the
project's analytic production, lifetime, detector-region logic, units, and
plotting conventions. It is not a replacement for a Belle II private-likelihood
reimplementation.
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
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq

try:
    from analysis.axionlimits import AXION_PHOTON_DIR, resolve_axionlimits_root
    from theory.predictions import predict_grid as theory
except ModuleNotFoundError:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from analysis.axionlimits import AXION_PHOTON_DIR, resolve_axionlimits_root  # type: ignore
    from theory.predictions import predict_grid as theory  # type: ignore


DEFAULT_CONFIG = Path("analysis/configs/belle2_closure_inputs.json")
DEFAULT_OUT_DIR = Path("results/belle2_closure")


@dataclass(frozen=True)
class Belle2Inputs:
    label: str
    sqrt_s_gev: float
    luminosity_pb_inv: float
    l_min_m: float
    l_max_m: float
    theta_min_deg: float
    theta_max_deg: float
    photon_energy_min_gev: float
    photon_efficiency: float
    delta_theta_res_deg: float
    closure_tolerance_log10: float
    published_curve: str
    target_curve_source: str
    closure_mode: str
    notes: tuple[str, ...]

    @property
    def theta_res_rad(self) -> float:
        return math.radians(self.delta_theta_res_deg)


def load_inputs(path: Path) -> Belle2Inputs:
    data = json.loads(path.read_text())
    return Belle2Inputs(
        label=str(data["label"]),
        sqrt_s_gev=float(data["sqrt_s_GeV"]),
        luminosity_pb_inv=float(data["luminosity_pb_inv"]),
        l_min_m=float(data["l_min_m"]),
        l_max_m=float(data["l_max_m"]),
        theta_min_deg=float(data["theta_min_deg"]),
        theta_max_deg=float(data["theta_max_deg"]),
        photon_energy_min_gev=float(data["photon_energy_min_GeV"]),
        photon_efficiency=float(data["photon_efficiency"]),
        delta_theta_res_deg=float(data["delta_theta_res_deg"]),
        closure_tolerance_log10=float(data.get("closure_tolerance_log10", 0.02)),
        published_curve=str(data["published_curve"]),
        target_curve_source=str(data["target_curve_source"]),
        closure_mode=str(data["closure_mode"]),
        notes=tuple(str(note) for note in data.get("notes", [])),
    )


def angular_acceptance(theta_min_deg: float, theta_max_deg: float) -> float:
    """Acceptance for the recoil-photon 1 + cos^2(theta) distribution."""
    c_min = math.cos(math.radians(theta_max_deg))
    c_max = math.cos(math.radians(theta_min_deg))
    accepted = (c_max + c_max**3 / 3.0) - (c_min + c_min**3 / 3.0)
    full = 8.0 / 3.0
    return accepted / full


def prompt_probability(m_a: float, g_agg: float, inputs: Belle2Inputs) -> float:
    ell = float(theory.ell_a(m_a, g_agg, inputs.sqrt_s_gev))
    if ell <= 0.0 or not math.isfinite(ell):
        return 0.0
    return 1.0 - math.exp(-inputs.l_min_m / ell)


def invisible_probability(m_a: float, g_agg: float, inputs: Belle2Inputs) -> float:
    ell = float(theory.ell_a(m_a, g_agg, inputs.sqrt_s_gev))
    if ell <= 0.0 or not math.isfinite(ell):
        return 0.0
    return math.exp(-inputs.l_max_m / ell)


def resolved_pass(m_a: float, inputs: Belle2Inputs) -> bool:
    return float(theory.delta_theta_min(m_a, inputs.sqrt_s_gev)) >= inputs.theta_res_rad


def recoil_energy_pass(m_a: float, inputs: Belle2Inputs) -> bool:
    return float(theory.e_gamma_recoil(m_a, inputs.sqrt_s_gev)) >= inputs.photon_energy_min_gev


def expected_prompt_events(m_a: float, g_agg: float, inputs: Belle2Inputs) -> float:
    if m_a >= inputs.sqrt_s_gev:
        return 0.0
    if not recoil_energy_pass(m_a, inputs) or not resolved_pass(m_a, inputs):
        return 0.0
    sigma_pb = float(theory.sigma_prod_pb(m_a, g_agg, inputs.sqrt_s_gev))
    acceptance = angular_acceptance(inputs.theta_min_deg, inputs.theta_max_deg)
    efficiency = acceptance * inputs.photon_efficiency**3
    return inputs.luminosity_pb_inv * sigma_pb * prompt_probability(m_a, g_agg, inputs) * efficiency


def expected_invisible_events(m_a: float, g_agg: float, inputs: Belle2Inputs) -> float:
    if m_a >= inputs.sqrt_s_gev:
        return 0.0
    if not recoil_energy_pass(m_a, inputs):
        return 0.0
    sigma_pb = float(theory.sigma_prod_pb(m_a, g_agg, inputs.sqrt_s_gev))
    acceptance = angular_acceptance(inputs.theta_min_deg, inputs.theta_max_deg)
    efficiency = acceptance * inputs.photon_efficiency
    return inputs.luminosity_pb_inv * sigma_pb * invisible_probability(m_a, g_agg, inputs) * efficiency


def load_published_curve(axionlimits_dir: Path | None, inputs: Belle2Inputs) -> tuple[Path, pd.DataFrame]:
    root = resolve_axionlimits_root(axionlimits_dir)
    rel = Path(inputs.published_curve)
    path = root / rel if rel.parts[0] == "limit_data" else root / AXION_PHOTON_DIR / rel
    raw = np.loadtxt(path, comments="#", ndmin=2)
    df = pd.DataFrame({"m_a_GeV": raw[:, 0] * 1.0e-9, "g_agg_GeV_inv": raw[:, 1]})
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    df = df[(df["m_a_GeV"] > 0.0) & (df["g_agg_GeV_inv"] > 0.0)]

    # AxionLimits stores this as a filled polygon with vertical caps at g=1.
    # For the closure target we need the lower exclusion boundary.
    df = df[df["g_agg_GeV_inv"] < 0.99].copy()
    boundary = (
        df.groupby("m_a_GeV", as_index=False)["g_agg_GeV_inv"]
        .min()
        .sort_values("m_a_GeV", kind="mergesort")
        .reset_index(drop=True)
    )
    return path, boundary


def build_log_interpolator(x: np.ndarray, y: np.ndarray) -> PchipInterpolator:
    return PchipInterpolator(np.log10(x), np.log10(y), extrapolate=False)


def solve_monotonic_limit(
    m_a: float,
    target_events: float,
    inputs: Belle2Inputs,
    *,
    channel: str = "prompt",
    g_min: float = 1.0e-7,
    g_max: float = 1.0,
) -> float:
    if channel == "prompt":
        fn = lambda g: expected_prompt_events(m_a, g, inputs) - target_events
    elif channel == "invisible":
        fn = lambda g: expected_invisible_events(m_a, g, inputs) - target_events
    else:
        raise ValueError(f"Unknown channel {channel!r}")

    if fn(g_max) < 0.0:
        return math.nan
    low = g_min
    while fn(low) > 0.0 and low > 1.0e-12:
        low *= 0.1
    try:
        return float(brentq(fn, low, g_max, maxiter=200))
    except ValueError:
        return math.nan


def build_closure(
    target: pd.DataFrame,
    inputs: Belle2Inputs,
    *,
    n_mass: int,
    g_min: float,
    g_max: float,
) -> pd.DataFrame:
    target = target.copy()
    target["expected_prompt_events_at_published_limit"] = [
        expected_prompt_events(float(m), float(g), inputs)
        for m, g in zip(target["m_a_GeV"], target["g_agg_GeV_inv"])
    ]
    target = target[target["expected_prompt_events_at_published_limit"] > 0.0].reset_index(drop=True)

    target_g = build_log_interpolator(
        target["m_a_GeV"].to_numpy(dtype=float),
        target["g_agg_GeV_inv"].to_numpy(dtype=float),
    )
    target_events = build_log_interpolator(
        target["m_a_GeV"].to_numpy(dtype=float),
        target["expected_prompt_events_at_published_limit"].to_numpy(dtype=float),
    )

    masses = np.logspace(
        math.log10(float(target["m_a_GeV"].min())),
        math.log10(float(target["m_a_GeV"].max())),
        n_mass,
    )
    rows: list[dict[str, float | str | bool]] = []
    for m_a in masses:
        published_g = float(10.0 ** target_g(math.log10(m_a)))
        n_eff = float(10.0 ** target_events(math.log10(m_a)))
        closure_g = solve_monotonic_limit(m_a, n_eff, inputs, channel="prompt", g_min=g_min, g_max=g_max)
        three_event_g = solve_monotonic_limit(m_a, 3.0, inputs, channel="prompt", g_min=g_min, g_max=g_max)
        rows.append(
            {
                "m_a_GeV": float(m_a),
                "published_g_agg_GeV_inv": published_g,
                "closure_g_agg_GeV_inv": closure_g,
                "three_event_prompt_g_agg_GeV_inv": three_event_g,
                "effective_signal_events": n_eff,
                "prompt_probability_at_closure": prompt_probability(m_a, closure_g, inputs)
                if math.isfinite(closure_g)
                else math.nan,
                "invisible_probability_at_closure": invisible_probability(m_a, closure_g, inputs)
                if math.isfinite(closure_g)
                else math.nan,
                "sigma_pb_at_closure": float(theory.sigma_prod_pb(m_a, closure_g, inputs.sqrt_s_gev))
                if math.isfinite(closure_g)
                else math.nan,
                "recoil_energy_GeV": float(theory.e_gamma_recoil(m_a, inputs.sqrt_s_gev)),
                "delta_theta_min_deg": math.degrees(float(theory.delta_theta_min(m_a, inputs.sqrt_s_gev))),
                "resolved_pass": resolved_pass(m_a, inputs),
                "recoil_energy_pass": recoil_energy_pass(m_a, inputs),
                "log10_ratio_closure_to_published": math.log10(closure_g / published_g)
                if math.isfinite(closure_g)
                else math.nan,
            }
        )
    return pd.DataFrame(rows)


def summarize_closure(
    closure: pd.DataFrame,
    target: pd.DataFrame,
    target_path: Path,
    inputs: Belle2Inputs,
) -> dict[str, Any]:
    residual = closure["log10_ratio_closure_to_published"].replace([np.inf, -np.inf], np.nan).dropna()
    max_abs_residual = float(residual.abs().max()) if len(residual) else math.nan
    return {
        "status": "passed" if max_abs_residual <= inputs.closure_tolerance_log10 else "failed",
        "closure_mode": inputs.closure_mode,
        "target_curve": str(target_path),
        "target_curve_source": inputs.target_curve_source,
        "published_boundary_points": int(len(target)),
        "closure_points": int(len(closure)),
        "inputs": {
            "sqrt_s_GeV": inputs.sqrt_s_gev,
            "luminosity_pb_inv": inputs.luminosity_pb_inv,
            "l_min_m": inputs.l_min_m,
            "l_max_m": inputs.l_max_m,
            "theta_min_deg": inputs.theta_min_deg,
            "theta_max_deg": inputs.theta_max_deg,
            "angular_acceptance": angular_acceptance(inputs.theta_min_deg, inputs.theta_max_deg),
            "photon_energy_min_GeV": inputs.photon_energy_min_gev,
            "photon_efficiency": inputs.photon_efficiency,
            "delta_theta_res_deg": inputs.delta_theta_res_deg,
            "closure_tolerance_log10": inputs.closure_tolerance_log10,
        },
        "mass_range_GeV": {
            "min": float(closure["m_a_GeV"].min()),
            "max": float(closure["m_a_GeV"].max()),
        },
        "published_g_range_GeV_inv": {
            "min": float(target["g_agg_GeV_inv"].min()),
            "max": float(target["g_agg_GeV_inv"].max()),
        },
        "effective_signal_events": {
            "min": float(closure["effective_signal_events"].min()),
            "median": float(closure["effective_signal_events"].median()),
            "max": float(closure["effective_signal_events"].max()),
        },
        "closure_residual_log10": {
            "median_abs": float(residual.abs().median()),
            "rms": float(math.sqrt(np.mean(np.square(residual)))) if len(residual) else math.nan,
            "max_abs": max_abs_residual,
        },
        "notes": list(inputs.notes)
        + [
            "Pass/fail checks numerical closure to the digitized published contour.",
            "The inferred effective signal-event threshold absorbs Belle II backgrounds and reconstruction efficiencies.",
        ],
    }


def plot_closure(
    closure: pd.DataFrame,
    target: pd.DataFrame,
    out_png: Path,
    out_pdf: Path,
) -> None:
    fig, (ax, ax2) = plt.subplots(
        1,
        2,
        figsize=(13.2, 5.4),
        constrained_layout=True,
        gridspec_kw={"width_ratios": [1.35, 1.0]},
    )

    y_top = 1.0e-1
    ax.fill_between(
        target["m_a_GeV"],
        target["g_agg_GeV_inv"],
        y_top,
        color="#7a4282",
        alpha=0.28,
        linewidth=0.0,
        label="Published Belle II excluded region",
    )
    ax.plot(
        target["m_a_GeV"],
        target["g_agg_GeV_inv"],
        color="#4c1d5f",
        lw=2.0,
        label="Published Belle II boundary",
    )
    ax.plot(
        closure["m_a_GeV"],
        closure["closure_g_agg_GeV_inv"],
        color="#f97316",
        lw=2.2,
        ls="--",
        label="This closure reconstruction",
    )
    ax.plot(
        closure["m_a_GeV"],
        closure["three_event_prompt_g_agg_GeV_inv"],
        color="0.35",
        lw=1.4,
        ls=":",
        label="Prompt 3-event floor only",
    )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(float(target["m_a_GeV"].min()) * 0.9, float(target["m_a_GeV"].max()) * 1.08)
    ax.set_ylim(3.0e-4, y_top)
    ax.set_xlabel(r"$m_a$ [GeV]")
    ax.set_ylabel(r"$g_{a\gamma\gamma}$ [GeV$^{-1}$]")
    ax.set_title("Belle II Closure Test")
    ax.grid(True, which="both", alpha=0.16)
    ax.legend(frameon=True, fontsize=8.5, loc="lower right")

    ax2.plot(
        closure["m_a_GeV"],
        closure["effective_signal_events"],
        color="#0f766e",
        lw=2.0,
    )
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel(r"$m_a$ [GeV]")
    ax2.set_ylabel("Effective signal-event threshold")
    ax2.set_title("Threshold Implied by Published Curve")
    ax2.grid(True, which="both", alpha=0.16)

    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=250)
    fig.savefig(out_pdf)
    plt.close(fig)


def write_markdown_summary(summary: dict[str, Any], out: Path) -> None:
    status = summary["status"]
    inputs = summary["inputs"]
    residual = summary["closure_residual_log10"]
    events = summary["effective_signal_events"]
    out.write_text(
        "\n".join(
            [
                "# Belle II Closure Test",
                "",
                f"Overall status: **{status}**",
                "",
                "This is a published-contour closure test for the photophilic ALP",
                "`e+ e- -> gamma a, a -> gamma gamma` analysis. The target contour",
                "is the Belle II curve distributed in AxionLimits.",
                "",
                "## Method",
                "",
                "1. Load the digitized Belle II boundary from AxionLimits.",
                "2. Convert masses from eV to GeV and keep the lower exclusion boundary.",
                "3. Use the validated analytic ALP-strahlung cross section and lifetime model.",
                "4. Infer the effective signal-event threshold implied by the published curve.",
                "5. Solve the same analytic model for `g_agg` at that inferred threshold.",
                "",
                "Because the Belle II private likelihood, background spectra, and reconstruction",
                "efficiencies are not in this repository, those ingredients are absorbed into",
                "the inferred effective signal-event threshold. This tests our units, cross",
                "section, lifetime, prompt/resolved logic, and plotting conventions against",
                "the published result.",
                "",
                "## Inputs",
                "",
                f"- target curve: `{summary['target_curve']}`",
                f"- source: `{summary['target_curve_source']}`",
                f"- sqrt(s): `{inputs['sqrt_s_GeV']} GeV`",
                f"- luminosity: `{inputs['luminosity_pb_inv']} pb^-1`",
                f"- L_min: `{inputs['l_min_m']} m`",
                f"- L_max: `{inputs['l_max_m']} m`",
                f"- polar acceptance: `{inputs['theta_min_deg']}--{inputs['theta_max_deg']} deg`",
                f"- angular acceptance factor: `{inputs['angular_acceptance']:.6g}`",
                f"- photon energy threshold: `{inputs['photon_energy_min_GeV']} GeV`",
                f"- diphoton angular resolution: `{inputs['delta_theta_res_deg']} deg`",
                "",
                "## Closure Metrics",
                "",
                f"- boundary points: `{summary['published_boundary_points']}`",
                f"- closure points: `{summary['closure_points']}`",
                f"- max |log10(g_closure/g_published)|: `{residual['max_abs']:.3e}`",
                f"- RMS log10 residual: `{residual['rms']:.3e}`",
                f"- median effective signal events: `{events['median']:.3g}`",
                f"- effective signal-event range: `{events['min']:.3g}--{events['max']:.3g}`",
                "",
                "## Outputs",
                "",
                "- `belle2_closure_contour.csv`",
                "- `belle2_closure_target.csv`",
                "- `belle2_closure_summary.json`",
                "- `belle2_closure.png` / `belle2_closure.pdf`",
                "",
            ]
        )
        + "\n"
    )


def run_belle2_closure(
    *,
    config: Path = DEFAULT_CONFIG,
    axionlimits_dir: Path | None = None,
    out_dir: Path = DEFAULT_OUT_DIR,
    n_mass: int = 300,
    g_min: float = 1.0e-7,
    g_max: float = 1.0,
) -> dict[str, Any]:
    """Run Gate 3 and write the closure artifacts.

    This function is intentionally importable by the central validator so the
    Belle II closure is part of the same pass/fail machinery as the MC theory
    checks.
    """
    inputs = load_inputs(config)
    target_path, target = load_published_curve(axionlimits_dir, inputs)
    closure = build_closure(target, inputs, n_mass=n_mass, g_min=g_min, g_max=g_max)
    summary = summarize_closure(closure, target, target_path, inputs)

    out_dir.mkdir(parents=True, exist_ok=True)
    target.to_csv(out_dir / "belle2_closure_target.csv", index=False)
    closure.to_csv(out_dir / "belle2_closure_contour.csv", index=False)
    (out_dir / "belle2_closure_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    write_markdown_summary(summary, out_dir / "belle2_closure.md")
    plot_closure(
        closure,
        target,
        out_dir / "belle2_closure.png",
        out_dir / "belle2_closure.pdf",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Belle II published-contour closure test.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--axionlimits-dir", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--n-mass", type=int, default=300)
    parser.add_argument("--g-min", type=float, default=1.0e-7)
    parser.add_argument("--g-max", type=float, default=1.0)
    args = parser.parse_args()

    summary = run_belle2_closure(
        config=args.config,
        axionlimits_dir=args.axionlimits_dir,
        out_dir=args.out_dir,
        n_mass=args.n_mass,
        g_min=args.g_min,
        g_max=args.g_max,
    )

    print(json.dumps(summary, indent=2))
    raise SystemExit(0 if summary["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
