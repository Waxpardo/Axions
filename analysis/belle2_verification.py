"""Belle II-style pipeline verification report.

This is not the published Belle II closure limit. It verifies that the local
Belle II-like smoke point satisfies the validated pipeline checks that precede
limit setting: production cross section, width convention, Pythia lifetime,
Delphes ROOT production, and reconstructed ALP diphoton mass.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_RUN_DIR = Path("results/alp_full_pipeline/belle2_hist_m1_g1em5_s10p58_n500")


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required verification artifact: {path}")
    return json.loads(path.read_text())


def _find_check(validation: dict[str, Any], name: str) -> dict[str, Any] | None:
    for check in validation.get("checks", []):
        check_name = check.get("gate") or check.get("observable") or check.get("check")
        if check_name == name:
            return check
    return None


def build_report(run_dir: Path, output_dir: Path, m_a: float, mass_tolerance_gev: float) -> dict[str, Any]:
    validation_path = run_dir / "validation_summary.json"
    hist_path = run_dir / "alp_histograms_summary.json"
    pythia_path = run_dir / "pythia_lifetime_summary.json"
    delphes_root = run_dir / "delphes.root"
    hist_root = run_dir / "alp_histograms.root"

    validation = _load_json(validation_path)
    hist = _load_json(hist_path)
    pythia = _load_json(pythia_path)

    cross_section = _find_check(validation, "cross_section")
    width = _find_check(validation, "width")
    lifetime = _find_check(validation, "pythia_alp_lifetime")
    delphes = _find_check(validation, "delphes_root")

    resolved_mean = hist.get("resolved_best_mgg_mean_GeV")
    resolved_abs_error = None if resolved_mean is None else abs(float(resolved_mean) - m_a)
    mass_passed = resolved_abs_error is not None and resolved_abs_error <= mass_tolerance_gev

    checks = {
        "cross_section": bool(cross_section and cross_section.get("passed")),
        "width": bool(width and width.get("passed")),
        "pythia_lifetime": bool(lifetime and lifetime.get("passed")),
        "delphes_root": bool(delphes and delphes.get("passed")),
        "alp_mass_histogram": bool(hist.get("passed") and mass_passed and hist_root.exists()),
    }

    report = {
        "run_dir": str(run_dir),
        "validation_summary": str(validation_path),
        "histogram_summary": str(hist_path),
        "pythia_summary": str(pythia_path),
        "delphes_root": str(delphes_root),
        "delphes_root_local_exists": delphes_root.exists(),
        "histogram_root": str(hist_root),
        "target_m_a_GeV": m_a,
        "mass_tolerance_GeV": mass_tolerance_gev,
        "resolved_best_mgg_mean_GeV": resolved_mean,
        "resolved_best_mgg_abs_error_GeV": resolved_abs_error,
        "events": hist.get("events"),
        "events_ge_3_photons": hist.get("events_ge_3_photons"),
        "mean_reco_photons": hist.get("mean_reco_photons"),
        "ctau_input_mm": pythia.get("ctau_input_mm"),
        "mean_lab_decay_length_mm": pythia.get("mean_lab_decay_length_mm"),
        "checks": checks,
        "passed": all(checks.values()),
        "note": (
            "This verifies the Belle II-like simulation chain. It is not the "
            "published Belle II exclusion-contour closure test."
        ),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "belle2_pipeline_verification.json").write_text(json.dumps(report, indent=2) + "\n")
    write_markdown_report(report, output_dir / "belle2_pipeline_verification.md")
    return report


def write_markdown_report(report: dict[str, Any], out: Path) -> None:
    status = "passed" if report["passed"] else "failed"
    rows = "\n".join(
        f"| {name} | {'passed' if passed else 'failed'} |" for name, passed in report["checks"].items()
    )
    out.write_text(
        "\n".join(
            [
                "# Belle II-Style Pipeline Verification",
                "",
                f"Overall status: **{status}**",
                "",
                "This report verifies the Belle II-like simulation pipeline before limit setting.",
                "It does not claim reproduction of the published Belle II exclusion contour.",
                "",
                "## Inputs",
                "",
                f"- run directory: `{report['run_dir']}`",
                f"- target ALP mass: `{report['target_m_a_GeV']} GeV`",
                f"- mass tolerance: `{report['mass_tolerance_GeV']} GeV`",
                "",
                "## Checks",
                "",
                "| Check | Status |",
                "|---|---|",
                rows,
                "",
                "## Key Observables",
                "",
                f"- events: `{report['events']}`",
                f"- events with >=3 photons: `{report['events_ge_3_photons']}`",
                f"- mean reconstructed photons/event: `{report['mean_reco_photons']}`",
                f"- resolved best-pair mean mass: `{report['resolved_best_mgg_mean_GeV']} GeV`",
                f"- resolved mass absolute error: `{report['resolved_best_mgg_abs_error_GeV']} GeV`",
                f"- Pythia input c*tau: `{report['ctau_input_mm']} mm`",
                f"- mean lab decay length: `{report['mean_lab_decay_length_mm']} mm`",
                "",
            ]
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify Belle II-like ALP pipeline artifacts.")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--out-dir", type=Path, default=Path("results/belle2_closure"))
    parser.add_argument("--m-a", type=float, default=1.0)
    parser.add_argument("--mass-tolerance-gev", type=float, default=0.20)
    args = parser.parse_args()

    report = build_report(args.run_dir, args.out_dir, args.m_a, args.mass_tolerance_gev)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
