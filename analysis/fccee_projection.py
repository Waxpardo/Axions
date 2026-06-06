"""FCC-ee Z-pole ALP projection and signature classification.

Signal yields use analytic production and decay probabilities. Production
contours must include a background-yield CSV unless `--allow-zero-background`
is explicitly requested for a smoke/prototype run.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.special import erf

try:
    from theory.predictions import predict_grid as theory
except ModuleNotFoundError:
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[1]))
    from theory.predictions import predict_grid as theory


DEFAULT_CONFIG = Path("analysis/configs/fccee_zpole_inputs.json")


class EfficiencyCorrections:
    """Branch-aware Delphes efficiency correction curves."""

    def __init__(self, path: Path, df: pd.DataFrame, column: str):
        self.path = path
        self.df = df.copy()
        self.column = column

    def factor(self, channel: str, m_a: float) -> float:
        curve = self.df[self.df["channel"] == channel].copy()
        if curve.empty:
            raise ValueError(
                f"Efficiency-correction map {self.path} has no rows for channel {channel!r}"
            )
        curve = curve.sort_values("m_a_GeV")
        masses = curve["m_a_GeV"].to_numpy(dtype=float)
        factors = curve[self.column].to_numpy(dtype=float)
        valid = np.isfinite(masses) & np.isfinite(factors) & (masses > 0.0) & (factors > 0.0)
        if not bool(np.any(valid)):
            raise ValueError(
                f"Efficiency-correction map {self.path} has no positive finite "
                f"{self.column!r} values for channel {channel!r}"
            )
        masses = masses[valid]
        factors = factors[valid]
        order = np.argsort(masses)
        masses = masses[order]
        factors = factors[order]
        log_factor = np.interp(
            math.log10(float(m_a)),
            np.log10(masses),
            np.log10(factors),
            left=np.log10(factors[0]),
            right=np.log10(factors[-1]),
        )
        return float(10.0**log_factor)

    def summary(self) -> dict[str, Any]:
        stats = (
            self.df.groupby("channel")[self.column]
            .agg(["count", "min", "max", "mean", "median"])
            .to_dict(orient="index")
        )
        return {
            "path": str(self.path),
            "column": self.column,
            "channels": sorted(self.df["channel"].unique().tolist()),
            "stats": stats,
        }


def load_config(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    card = Path(data["delphes_card"])
    data["delphes_card_exists"] = card.exists()
    data["theta_res_rad"] = math.radians(float(data["delta_theta_res_deg"]))
    data["luminosity_pb_inv"] = float(data["luminosity_ab_inv"]) * 1.0e6
    return data


def load_background_yields(
    config: dict[str, Any],
    background_path: Path | None,
    allow_zero_background: bool,
) -> pd.DataFrame | None:
    """Load the background-yield table required for production contours."""
    configured = Path(config["background_yields_csv"])
    path = background_path or configured
    if path.exists():
        df = pd.read_csv(path)
        required = {"channel", "m_a_GeV", "bkg_events"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
        return df

    if allow_zero_background or not bool(config.get("require_background_for_contours", True)):
        return None

    raise FileNotFoundError(
        "Background yields are required for production FCC-ee contours. "
        f"Expected {path}. Build it with analysis/fccee_background_yields.py "
        "from actual Delphes background samples, or pass --allow-zero-background "
        "only for a non-final smoke plot."
    )


def load_background_bins(
    config: dict[str, Any],
    background_bins_path: Path | None,
) -> pd.DataFrame | None:
    """Load binned background histograms if available."""
    configured = Path(config.get("background_bins_csv", ""))
    path = background_bins_path or configured
    if not path or not path.exists():
        return None
    df = pd.read_csv(path)
    required = {"channel", "observable", "bin_low_GeV", "bin_high_GeV", "bkg_events"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
    return df


def load_efficiency_corrections(
    config: dict[str, Any],
    correction_path: Path | None,
    use_corrections: bool,
    column: str,
) -> EfficiencyCorrections | None:
    """Load Delphes-derived branch-aware efficiency corrections."""
    if not use_corrections:
        return None

    configured_value = config.get("efficiency_corrections_csv", "")
    configured = Path(configured_value) if configured_value else None
    path = correction_path or configured
    if path is None:
        raise FileNotFoundError(
            "Efficiency corrections are enabled, but no correction map was provided. "
            "Set efficiency_corrections_csv in the config or pass --efficiency-corrections."
        )
    if not path.exists():
        raise FileNotFoundError(
            f"Efficiency corrections are enabled, but {path} does not exist. "
            "Build it with analysis/build_full_analysis_efficiency_map.py, or pass "
            "--no-efficiency-corrections for a flat-efficiency smoke plot."
        )

    df = pd.read_csv(path)
    required = {"channel", "m_a_GeV", column}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing required columns: {sorted(missing)}")
    df = df[["channel", "m_a_GeV", column]].copy()
    df = df[np.isfinite(df["m_a_GeV"]) & np.isfinite(df[column])]
    df = df[(df["m_a_GeV"] > 0.0) & (df[column] > 0.0)]
    if df.empty:
        raise ValueError(f"{path} has no positive finite efficiency-correction rows")
    return EfficiencyCorrections(path=path, df=df, column=column)


def log_grid(low: float, high: float, n: int) -> np.ndarray:
    if n < 2:
        return np.array([low], dtype=float)
    return np.logspace(math.log10(low), math.log10(high), n)


def angular_acceptance_from_eta_max(eta_max: float) -> float:
    """Acceptance for the recoil-photon 1+cos^2(theta) distribution."""
    c = math.tanh(eta_max)
    accepted = 2.0 * (c + c**3 / 3.0)
    full = 8.0 / 3.0
    return accepted / full


def photon_energy_pass(m_a: float, sqrt_s: float, photon_energy_min: float) -> bool:
    return float(theory.e_gamma_recoil(m_a, sqrt_s)) >= photon_energy_min


def expected_events(
    m_a: float,
    g_agg: float,
    config: dict[str, Any],
    channel: str,
    efficiency_scale: float = 1.0,
) -> float:
    sqrt_s = float(config["sqrt_s_GeV"])
    lumi = float(config["luminosity_pb_inv"])
    sigma = float(theory.sigma_prod_pb(m_a, g_agg, sqrt_s))
    ell = float(theory.ell_a(m_a, g_agg, sqrt_s))
    if ell <= 0.0:
        return 0.0

    acceptance = angular_acceptance_from_eta_max(float(config["eta_max"]))
    photon_eff = float(config["photon_efficiency"])
    if not photon_energy_pass(m_a, sqrt_s, float(config["photon_energy_min_GeV"])):
        return 0.0

    if channel == "invisible":
        probability = math.exp(-float(config["l_max_m"]) / ell)
        efficiency = acceptance * photon_eff
    elif channel == "resolved_prompt":
        if float(theory.delta_theta_min(m_a, sqrt_s)) < float(config["theta_res_rad"]):
            return 0.0
        probability = 1.0 - math.exp(-float(config["l_min_m"]) / ell)
        efficiency = acceptance * photon_eff**3
    else:
        raise ValueError(f"Unknown channel: {channel}")
    if not math.isfinite(efficiency_scale) or efficiency_scale <= 0.0:
        return 0.0
    return lumi * sigma * probability * efficiency * efficiency_scale


def interpolate_background_events(background: pd.DataFrame | None, channel: str, m_a: float) -> float:
    """Interpolate background yield at `m_a` for a channel."""
    if background is None:
        return 0.0
    curve = background[background["channel"] == channel].copy()
    if curve.empty:
        raise ValueError(f"Background table has no rows for channel {channel!r}")
    curve = curve.sort_values("m_a_GeV")
    masses = curve["m_a_GeV"].to_numpy(dtype=float)
    yields = curve["bkg_events"].to_numpy(dtype=float)
    if m_a < masses[0] or m_a > masses[-1]:
        return 0.0
    return float(np.interp(np.log10(m_a), np.log10(masses), yields))


def _normal_bin_fractions(bin_low: np.ndarray, bin_high: np.ndarray, mean: float, sigma: float) -> np.ndarray:
    sigma = max(float(sigma), 1.0e-12)
    z_low = (bin_low - mean) / (math.sqrt(2.0) * sigma)
    z_high = (bin_high - mean) / (math.sqrt(2.0) * sigma)
    fractions = 0.5 * (erf(z_high) - erf(z_low))
    total = float(np.sum(fractions))
    if total <= 0.0:
        return np.zeros_like(fractions)
    return fractions / total


def required_signal_events_binned(
    *,
    channel: str,
    m_a: float,
    config: dict[str, Any],
    background_bins: pd.DataFrame,
) -> tuple[float, float, str]:
    """Return required signal events using binned Asimov Delta chi2."""
    curve = background_bins[background_bins["channel"] == channel].copy()
    if curve.empty:
        raise ValueError(f"Binned background table has no rows for channel {channel!r}")
    curve = curve.sort_values("bin_low_GeV")

    if channel == "invisible":
        observable = float(theory.e_gamma_recoil(m_a, float(config["sqrt_s_GeV"])))
        sigma = max(
            float(config["invisible_recoil_resolution_relative"]) * observable,
            float(config["invisible_recoil_resolution_min_GeV"]),
        )
        floor_key = "n_target_invisible"
    elif channel == "resolved_prompt":
        observable = m_a
        sigma = max(
            float(config["resolved_mass_resolution_relative"]) * m_a,
            float(config["resolved_mass_resolution_min_GeV"]),
        )
        floor_key = "n_target_resolved"
    else:
        raise ValueError(f"Unknown channel: {channel}")

    low = curve["bin_low_GeV"].to_numpy(dtype=float)
    high = curve["bin_high_GeV"].to_numpy(dtype=float)
    bkg = curve["bkg_events"].to_numpy(dtype=float)
    fractions = _normal_bin_fractions(low, high, observable, sigma)

    bkg_floor = float(config.get("background_bin_floor_events", 1.0))
    denominator = float(np.sum((fractions * fractions) / np.maximum(bkg, bkg_floor)))
    floor = float(config[floor_key])
    if denominator <= 0.0:
        return floor, 0.0, "binned_delta_chi2_no_covered_bins_3_event_floor"

    target = math.sqrt(float(config.get("cl_delta_chi2", 2.71)) / denominator)
    target = max(floor, target)
    equivalent_bkg = target * target / float(config.get("cl_delta_chi2", 2.71))
    return target, equivalent_bkg, "binned_delta_chi2_with_3_event_floor"


def required_signal_events(
    *,
    channel: str,
    m_a: float,
    config: dict[str, Any],
    background: pd.DataFrame | None,
    background_bins: pd.DataFrame | None,
) -> tuple[float, float, str]:
    """Return required signal events, background events, and limit method."""
    if background_bins is not None:
        return required_signal_events_binned(
            channel=channel,
            m_a=m_a,
            config=config,
            background_bins=background_bins,
        )

    floor_key = "n_target_invisible" if channel == "invisible" else "n_target_resolved"
    floor = float(config[floor_key])
    bkg = interpolate_background_events(background, channel, m_a)
    if bkg <= 0.0:
        return floor, bkg, "zero_or_empty_background_3_event_floor"
    target = max(floor, math.sqrt(float(config.get("cl_delta_chi2", 2.71)) * bkg))
    return target, bkg, "single_bin_delta_chi2_with_3_event_floor"


def solve_roots(
    m_a: float,
    config: dict[str, Any],
    channel: str,
    target: float,
    g_min: float,
    g_max: float,
    n_scan: int,
    efficiency_scale: float = 1.0,
) -> list[float]:
    gs = log_grid(g_min, g_max, n_scan)
    vals = np.array(
        [expected_events(m_a, g, config, channel, efficiency_scale=efficiency_scale) - target for g in gs]
    )
    roots: list[float] = []
    for i in np.where(np.diff(np.signbit(vals)))[0]:
        lo, hi = float(gs[i]), float(gs[i + 1])
        try:
            roots.append(
                brentq(
                    lambda g: expected_events(m_a, g, config, channel, efficiency_scale=efficiency_scale)
                    - target,
                    lo,
                    hi,
                )
            )
        except ValueError:
            continue
    return roots


def classify_point(m_a: float, g_agg: float, config: dict[str, Any]) -> str:
    sqrt_s = float(config["sqrt_s_GeV"])
    ell = float(theory.ell_a(m_a, g_agg, sqrt_s))
    dtheta = float(theory.delta_theta_min(m_a, sqrt_s))
    resolved = dtheta >= float(config["theta_res_rad"])

    if ell >= float(config["l_max_m"]):
        return "invisible"
    if not resolved:
        return "merged"
    if ell <= float(config["l_min_m"]):
        return "prompt_resolved"
    return "displaced_resolved"


def build_classification(
    masses: Iterable[float],
    couplings: Iterable[float],
    config: dict[str, Any],
) -> pd.DataFrame:
    rows = []
    sqrt_s = float(config["sqrt_s_GeV"])
    for m_a in masses:
        if m_a >= sqrt_s:
            continue
        for g in couplings:
            ell = float(theory.ell_a(m_a, g, sqrt_s))
            dtheta = float(theory.delta_theta_min(m_a, sqrt_s))
            rows.append(
                {
                    "m_a_GeV": float(m_a),
                    "g_agg_GeV_inv": float(g),
                    "sqrt_s_GeV": sqrt_s,
                    "ell_a_m": ell,
                    "dtheta_min_rad": dtheta,
                    "dtheta_min_deg": math.degrees(dtheta),
                    "is_resolved": dtheta >= float(config["theta_res_rad"]),
                    "signature": classify_point(float(m_a), float(g), config),
                }
            )
    return pd.DataFrame(rows)


def build_projection(
    masses: Iterable[float],
    config: dict[str, Any],
    background: pd.DataFrame | None,
    background_bins: pd.DataFrame | None,
    efficiency_corrections: EfficiencyCorrections | None,
    g_min: float,
    g_max: float,
    n_scan: int,
) -> pd.DataFrame:
    rows = []
    sqrt_s = float(config["sqrt_s_GeV"])
    for m_a in masses:
        if m_a >= sqrt_s:
            continue
        invisible_target, invisible_bkg, invisible_method = required_signal_events(
            channel="invisible",
            m_a=float(m_a),
            config=config,
            background=background,
            background_bins=background_bins,
        )
        if efficiency_corrections is None:
            invisible_roots = solve_roots(float(m_a), config, "invisible", invisible_target, g_min, g_max, n_scan)
            invisible_solutions = [
                (side, root, 1.0, f"invisible_{side}") for side, root in zip(["lower", "upper"], invisible_roots)
            ]
        else:
            invisible_solutions = []
            for side, pick in (("lower", "first"), ("upper", "last")):
                correction_channel = f"invisible_{side}"
                correction = efficiency_corrections.factor(correction_channel, float(m_a))
                roots = solve_roots(
                    float(m_a),
                    config,
                    "invisible",
                    invisible_target,
                    g_min,
                    g_max,
                    n_scan,
                    efficiency_scale=correction,
                )
                if roots:
                    root = roots[0] if pick == "first" else roots[-1]
                    invisible_solutions.append((side, root, correction, correction_channel))

        for side, root, correction, correction_channel in invisible_solutions:
            rows.append(
                {
                    "m_a_GeV": float(m_a),
                    "g_agg_GeV_inv": float(root),
                    "channel": f"invisible_{side}",
                    "base_channel": "invisible",
                    "n_target": invisible_target,
                    "bkg_events": invisible_bkg,
                    "limit_method": invisible_method,
                    "efficiency_model": (
                        "delphes_corrected" if efficiency_corrections is not None else "flat_parametric"
                    ),
                    "efficiency_correction_channel": correction_channel,
                    "detector_correction_factor": correction,
                    "sqrt_s_GeV": sqrt_s,
                    "luminosity_ab_inv": float(config["luminosity_ab_inv"]),
                }
            )

        resolved_target, resolved_bkg, resolved_method = required_signal_events(
            channel="resolved_prompt",
            m_a=float(m_a),
            config=config,
            background=background,
            background_bins=background_bins,
        )
        resolved_correction = (
            efficiency_corrections.factor("resolved_prompt", float(m_a)) if efficiency_corrections is not None else 1.0
        )
        resolved_roots = solve_roots(
            float(m_a),
            config,
            "resolved_prompt",
            resolved_target,
            g_min,
            g_max,
            n_scan,
            efficiency_scale=resolved_correction,
        )
        if resolved_roots:
            rows.append(
                {
                    "m_a_GeV": float(m_a),
                    "g_agg_GeV_inv": float(resolved_roots[0]),
                    "channel": "resolved_prompt",
                    "base_channel": "resolved_prompt",
                    "n_target": resolved_target,
                    "bkg_events": resolved_bkg,
                    "limit_method": resolved_method,
                    "efficiency_model": (
                        "delphes_corrected" if efficiency_corrections is not None else "flat_parametric"
                    ),
                    "efficiency_correction_channel": "resolved_prompt",
                    "detector_correction_factor": resolved_correction,
                    "sqrt_s_GeV": sqrt_s,
                    "luminosity_ab_inv": float(config["luminosity_ab_inv"]),
                }
            )
    return pd.DataFrame(rows)


def plot_classification(df: pd.DataFrame, out: Path) -> None:
    codes = {
        "invisible": 0,
        "merged": 1,
        "displaced_resolved": 2,
        "prompt_resolved": 3,
    }
    colors = {
        0: "#4c78a8",
        1: "#f58518",
        2: "#54a24b",
        3: "#b279a2",
    }
    fig, ax = plt.subplots(figsize=(7.2, 5.2), constrained_layout=True)
    for signature, code in codes.items():
        group = df[df["signature"] == signature]
        if group.empty:
            continue
        ax.scatter(
            group["m_a_GeV"],
            group["g_agg_GeV_inv"],
            s=4,
            alpha=0.75,
            color=colors[code],
            label=signature.replace("_", " "),
            rasterized=True,
        )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$m_a$ [GeV]")
    ax.set_ylabel(r"$g_{a\gamma\gamma}$ [GeV$^{-1}$]")
    ax.set_title("FCC-ee Z-Pole ALP Signature Regions")
    ax.grid(True, which="both", alpha=0.16)
    ax.legend(frameon=False, fontsize=8)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=250)
    plt.close(fig)


def write_summary(
    config: dict[str, Any],
    projection: pd.DataFrame,
    classification: pd.DataFrame,
    background: pd.DataFrame | None,
    background_bins: pd.DataFrame | None,
    efficiency_corrections: EfficiencyCorrections | None,
    out: Path,
) -> None:
    resolved_threshold = float(config["sqrt_s_GeV"]) * float(config["theta_res_rad"]) / 4.0
    summary = {
        "config": config,
        "resolved_mass_threshold_GeV_light_alp_approx": resolved_threshold,
        "projection_rows": int(len(projection)),
        "classification_rows": int(len(classification)),
        "projection_channels": projection["channel"].value_counts().to_dict() if not projection.empty else {},
        "signature_counts": classification["signature"].value_counts().to_dict() if not classification.empty else {},
        "delphes_card_exists": bool(config.get("delphes_card_exists")),
        "background_included": background is not None,
        "background_channels": sorted(background["channel"].unique().tolist()) if background is not None else [],
        "binned_background_included": background_bins is not None,
        "binned_background_channels": (
            sorted(background_bins["channel"].unique().tolist()) if background_bins is not None else []
        ),
        "efficiency_corrections_included": efficiency_corrections is not None,
        "efficiency_corrections": efficiency_corrections.summary() if efficiency_corrections is not None else None,
        "limit_methods": projection["limit_method"].value_counts().to_dict() if "limit_method" in projection else {},
        "efficiency_models": (
            projection["efficiency_model"].value_counts().to_dict() if "efficiency_model" in projection else {}
        ),
    }
    out.write_text(json.dumps(summary, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate FCC-ee Z-pole ALP contours and signature regions.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out-dir", type=Path, default=Path("results/fccee"))
    parser.add_argument("--m-min", type=float, default=1.0e-2)
    parser.add_argument("--m-max", type=float, default=80.0)
    parser.add_argument("--n-mass", type=int, default=180)
    parser.add_argument("--g-min", type=float, default=1.0e-8)
    parser.add_argument("--g-max", type=float, default=1.0e-1)
    parser.add_argument("--n-g", type=int, default=180)
    parser.add_argument("--root-scan-points", type=int, default=3000)
    parser.add_argument("--background-yields", type=Path, default=None)
    parser.add_argument("--background-bins", type=Path, default=None)
    parser.add_argument("--efficiency-corrections", type=Path, default=None)
    parser.add_argument(
        "--efficiency-correction-column",
        default=None,
        help="Positive correction column to multiply the flat parametric yield.",
    )
    parser.add_argument(
        "--no-efficiency-corrections",
        action="store_true",
        help="Disable configured Delphes-derived efficiency corrections.",
    )
    parser.add_argument("--allow-zero-background", action="store_true")
    args = parser.parse_args()

    config = load_config(args.config)
    background = load_background_yields(config, args.background_yields, args.allow_zero_background)
    background_bins = load_background_bins(config, args.background_bins)
    use_efficiency_corrections = bool(config.get("use_efficiency_corrections", False)) and not args.no_efficiency_corrections
    if args.efficiency_corrections is not None:
        use_efficiency_corrections = True
    correction_column = args.efficiency_correction_column or str(
        config.get("efficiency_correction_column", "detector_correction_factor")
    )
    efficiency_corrections = load_efficiency_corrections(
        config,
        args.efficiency_corrections,
        use_efficiency_corrections,
        correction_column,
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    masses = log_grid(args.m_min, args.m_max, args.n_mass)
    couplings = log_grid(args.g_min, args.g_max, args.n_g)

    classification = build_classification(masses, couplings, config)
    projection = build_projection(
        masses,
        config,
        background,
        background_bins,
        efficiency_corrections,
        args.g_min,
        args.g_max,
        args.root_scan_points,
    )

    classification_path = args.out_dir / "fccee_zpole_signature_classification.csv"
    projection_path = args.out_dir / "fccee_projection.csv"
    summary_path = args.out_dir / "fccee_projection_summary.json"
    classification_plot = args.out_dir / "fccee_zpole_signature_classification.png"

    classification.to_csv(classification_path, index=False)
    projection.to_csv(projection_path, index=False)
    plot_classification(classification, classification_plot)
    write_summary(config, projection, classification, background, background_bins, efficiency_corrections, summary_path)

    print(f"Wrote {projection_path}")
    print(f"Wrote {classification_path}")
    print(f"Wrote {classification_plot}")
    print(f"Wrote {summary_path}")
    if not config.get("delphes_card_exists"):
        raise SystemExit(f"Configured Delphes card does not exist: {config['delphes_card']}")


if __name__ == "__main__":
    main()
