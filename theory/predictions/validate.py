"""Validation tools comparing MC outputs against analytic ALP predictions."""

from __future__ import annotations

import argparse
import gzip
import json
import math
import re
from pathlib import Path
from typing import Any

try:
    import numpy as np  # type: ignore
except ImportError as exc:  # Keep --pipeline-smoke usable on a fresh account.
    np = None  # type: ignore
    _NUMPY_IMPORT_ERROR: ImportError | None = exc
else:
    _NUMPY_IMPORT_ERROR = None

try:
    from predict_grid import (
        ALPHA,
        e_gamma_recoil,
        ell_a,
        gamma_a,
        sigma_prod_pb,
        delta_theta_min,
    )
except ImportError as exc:  # Keep --pipeline-smoke independent of ALP deps.
    ALPHA = 1.0 / 137.035999084
    e_gamma_recoil = None  # type: ignore
    ell_a = None  # type: ignore
    gamma_a = None  # type: ignore
    sigma_prod_pb = None  # type: ignore
    delta_theta_min = None  # type: ignore
    _PREDICT_GRID_IMPORT_ERROR: ImportError | None = exc
else:
    _PREDICT_GRID_IMPORT_ERROR = None


FLOAT_RE = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"


def _read_lines(path: Path):
    if path.suffix == ".gz":
        with gzip.open(path, "rt") as handle:
            yield from handle
    else:
        with path.open() as handle:
            yield from handle


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def _require_numpy():
    if np is None:
        raise RuntimeError("Install numpy for ALP physics validation: pip install -r env/requirements.txt") from _NUMPY_IMPORT_ERROR
    return np


def _require_prediction_tool(name: str, tool: Any):
    if tool is None:
        raise RuntimeError(
            f"Could not import {name} from predict_grid.py. "
            "Install the theory dependencies with: pip install -r env/requirements.txt"
        ) from _PREDICT_GRID_IMPORT_ERROR
    return tool


def find_banner(run_dir: Path) -> Path | None:
    candidates = [run_dir / "banner.txt"]
    candidates.extend(sorted(run_dir.glob("*_banner.txt")))
    candidates.extend(sorted(run_dir.glob("run_*_tag_*_banner.txt")))
    candidates.extend(sorted(run_dir.glob("Events/run_*/run_*_tag_*_banner.txt")))
    return _first_existing(candidates)


def find_lhe(run_dir: Path) -> Path | None:
    candidates = [
        run_dir / "unweighted_events.lhe.gz",
        run_dir / "unweighted_events.lhe",
    ]
    candidates.extend(sorted(run_dir.glob("Events/run_*/unweighted_events.lhe.gz")))
    candidates.extend(sorted(run_dir.glob("Events/run_*/unweighted_events.lhe")))
    candidates.extend(sorted(run_dir.glob("*/Events/run_*/unweighted_events.lhe.gz")))
    candidates.extend(sorted(run_dir.glob("*/Events/run_*/unweighted_events.lhe")))
    candidates.extend(sorted(run_dir.glob("**/unweighted_events.lhe.gz")))
    candidates.extend(sorted(run_dir.glob("**/unweighted_events.lhe")))
    return _first_existing(candidates)


def find_hepmc(run_dir: Path) -> Path | None:
    candidates = [run_dir / "events.hepmc"]
    candidates.extend(sorted(run_dir.glob("*.hepmc")))
    candidates.extend(sorted(run_dir.glob("**/*.hepmc")))
    return _first_existing(candidates)


def find_analysis_root(run_dir: Path) -> Path | None:
    candidates = [run_dir / "analysis.root"]
    candidates.extend(sorted(run_dir.glob("analysis*.root")))
    candidates.extend(sorted(run_dir.glob("**/analysis*.root")))
    return _first_existing(candidates)


def find_delphes_root(run_dir: Path) -> Path | None:
    candidates = [run_dir / "delphes.root"]
    candidates.extend(sorted(run_dir.glob("delphes*.root")))
    candidates.extend(sorted(run_dir.glob("**/delphes*.root")))
    return _first_existing(candidates)


def find_width_file(run_dir: Path) -> Path | None:
    candidates = [run_dir / "width.txt", run_dir / "compute_widths.txt"]
    candidates.extend(sorted(run_dir.glob("*width*.txt")))
    return _first_existing(candidates)


def find_param_card(run_dir: Path) -> Path | None:
    candidates = [run_dir / "param_card.dat"]
    candidates.extend(sorted(run_dir.glob("Cards/param_card.dat")))
    candidates.extend(sorted(run_dir.glob("Events/run_*/param_card.dat")))
    return _first_existing(candidates)


def find_run_card(run_dir: Path) -> Path | None:
    candidates = [run_dir / "run_card.dat"]
    candidates.extend(sorted(run_dir.glob("Cards/run_card.dat")))
    candidates.extend(sorted(run_dir.glob("Events/run_*/run_card.dat")))
    return _first_existing(candidates)


def parse_mg_cross_section(banner_path: Path) -> float:
    """Parse MadGraph integrated cross section in pb from a banner file"""
    pattern = re.compile(r"Integrated weight \(pb\)\s*:\s*(%s)" % FLOAT_RE)
    for line in _read_lines(banner_path):
        match = pattern.search(line)
        if match:
            return float(match.group(1))
    raise ValueError(f"Cross section not found in {banner_path}")


def parse_width_gev(width_path: Path, alp_pdg_id: int = 9999) -> float:
    """Parse ALP width in GeV from a compute_widths or param-card-like file"""
    decay_pattern = re.compile(r"^\s*DECAY\s+%d\s+(%s)\b" % (alp_pdg_id, FLOAT_RE), re.IGNORECASE)
    generic_pattern = re.compile(r"\b(?:width|gamma)\b[^\d+\-.]*(%s)" % FLOAT_RE, re.IGNORECASE)
    for line in _read_lines(width_path):
        match = decay_pattern.search(line)
        if match:
            return float(match.group(1))
        match = generic_pattern.search(line)
        if match:
            return float(match.group(1))
    raise ValueError(f"ALP width not found in {width_path}")


def parse_run_card(run_card: Path) -> dict[str, float]:
    """Parse enough run-card metadata to infer sqrt(s) for lepton runs"""
    values: dict[str, float] = {}
    pattern = re.compile(r"^\s*(%s)\s*=\s*([A-Za-z0-9_]+)" % FLOAT_RE)
    for line in _read_lines(run_card):
        match = pattern.search(line)
        if match:
            value = float(match.group(1))
            key = match.group(2).lower()
            values[key] = value
    if "ebeam1" in values and "ebeam2" in values:
        values["sqrt_s"] = values["ebeam1"] + values["ebeam2"]
    return values


def parse_param_card(param_card: Path, alp_pdg_id: int = 9999) -> dict[str, float]:
    """Parse ALP UFO parameters and masses from a MadGraph param card"""
    result: dict[str, float] = {}
    current_block: str | None = None
    line_pattern = re.compile(r"^\s*(\d+)\s+(%s)(?:\s*#\s*([A-Za-z0-9_]+))?" % FLOAT_RE)
    decay_pattern = re.compile(r"^\s*DECAY\s+(\d+)\s+(%s)" % FLOAT_RE, re.IGNORECASE)

    for raw_line in _read_lines(param_card):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        block_match = re.match(r"^BLOCK\s+(\S+)", line, re.IGNORECASE)
        if block_match:
            current_block = block_match.group(1).upper()
            continue
        decay_match = decay_pattern.match(line)
        if decay_match and int(decay_match.group(1)) == alp_pdg_id:
            result["Walp_GeV"] = float(decay_match.group(2))
            current_block = "DECAY"
            continue
        match = line_pattern.match(line)
        if not match or current_block is None:
            continue
        code = int(match.group(1))
        value = float(match.group(2))
        label = (match.group(3) or "").lower()
        if current_block == "ALP":
            if code == 1 or label == "fa":
                result["fa_GeV"] = value
            elif code == 11 or label == "kg":
                result["Kg"] = value
            elif code == 12 or label == "kb":
                result["KB"] = value
            elif code == 13 or label == "kw":
                result["KW"] = value
            elif label:
                result[label] = value
        elif current_block == "MASS" and code == alp_pdg_id:
            result["m_a_GeV"] = value

    if {"fa_GeV", "KB", "KW"} <= result.keys():
        result["g_agg_ufo_guess_GeV_inv"] = ALPHA * (result["KB"] + result["KW"]) / (2.0 * math.pi * result["fa_GeV"])
    return result


def gate1_cross_section(banner_path: Path, m_a: float, g_agg: float, sqrt_s: float, tol: float = 0.05) -> dict[str, Any]:
    mc_pb = parse_mg_cross_section(banner_path)
    sigma_tool = _require_prediction_tool("sigma_prod_pb", sigma_prod_pb)
    theory_pb = float(sigma_tool(m_a, g_agg, sqrt_s))
    ratio = mc_pb / theory_pb if theory_pb else math.inf
    passed = abs(ratio - 1.0) < tol
    return {
        "gate": "cross_section",
        "passed": passed,
        "mc_sigma_pb": mc_pb,
        "theory_sigma_pb": theory_pb,
        "ratio": ratio,
        "tolerance": tol,
    }


def gate2_width(width_gev_from_mg: float, m_a: float, g_agg: float, tol: float = 0.05) -> dict[str, Any]:
    gamma_tool = _require_prediction_tool("gamma_a", gamma_a)
    theory_width = float(gamma_tool(m_a, g_agg))
    ratio = width_gev_from_mg / theory_width if theory_width else math.inf
    if abs(ratio - 1.0) < tol:
        convention = "64pi"
        passed = True
    elif abs(ratio - 0.5) < tol:
        convention = "128pi"
        passed = True
    else:
        convention = "anomalous"
        passed = False
    return {
        "gate": "width",
        "passed": passed,
        "convention": convention,
        "mc_width_GeV": width_gev_from_mg,
        "theory_width_64pi_GeV": theory_width,
        "ratio_to_64pi": ratio,
        "tolerance": tol,
    }


def _require_pylhe():
    try:
        import pylhe  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Install pylhe to validate LHE outputs: pip install pylhe") from exc
    return pylhe


def _require_pyhepmc():
    try:
        import pyhepmc  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Install pyhepmc to validate HepMC outputs: pip install pyhepmc") from exc
    return pyhepmc


def _require_pyplot():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # type: ignore

    return plt


def _file_check(label: str, path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "check": label,
            "passed": False,
            "path": None,
            "exists": False,
            "size_bytes": 0,
        }
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    return {
        "check": label,
        "passed": exists and size > 0,
        "path": str(path),
        "exists": exists,
        "size_bytes": size,
    }


def _root_keys(path: Path) -> tuple[list[str] | None, str | None, bool]:
    try:
        import uproot  # type: ignore
    except ImportError as exc:
        return None, f"uproot is not installed, so ROOT keys were not inspected: {exc}", False

    try:
        with uproot.open(path) as root_file:
            return sorted({key.split(";")[0] for key in root_file.keys()}), None, True
    except Exception as exc:  # pragma: no cover - depends on external ROOT files.
        return None, f"could not inspect ROOT file with uproot: {exc}", True


def _root_file_check(label: str, path: Path | None, expected_keys: list[str]) -> dict[str, Any]:
    check = _file_check(label, path)
    if not check["passed"] or path is None:
        return check

    keys, error, attempted = _root_keys(path)
    if keys is None:
        check["root_key_check"] = "failed" if attempted else "skipped"
        check["warning"] = error
        check["passed"] = not attempted
        return check

    missing = [key for key in expected_keys if key not in keys]
    check["root_key_check"] = "checked"
    check["keys"] = keys
    check["expected_keys"] = expected_keys
    check["missing_keys"] = missing
    check["passed"] = not missing
    return check


def validate_pipeline_outputs(run_dir: Path, plots_dir: Path | None = None) -> dict[str, Any]:
    """Validate the non-ALP MG5 -> Pythia -> HepMC -> ROOT -> Delphes smoke outputs."""
    run_dir = run_dir.resolve()
    plots_dir = plots_dir or run_dir / "validation_plots"
    checks = [
        _file_check("madgraph_lhe", find_lhe(run_dir)),
        _file_check("pythia_hepmc", find_hepmc(run_dir)),
        _root_file_check(
            "hepmc_analysis_root",
            find_analysis_root(run_dir),
            ["h_nparticles", "h_pt", "h_eta", "h_phi", "h_bhadron_pt"],
        ),
        _root_file_check("delphes_root", find_delphes_root(run_dir), ["Delphes"]),
    ]
    results: dict[str, Any] = {
        "mode": "pipeline_smoke",
        "run_dir": str(run_dir),
        "passed": all(check.get("passed", False) for check in checks),
        "checks": checks,
    }

    summary_path = plots_dir / "pipeline_validation_summary.json"
    plots_dir.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(results, indent=2))
    results["summary_path"] = str(summary_path)
    return results


def _particle_energy(particle: Any) -> float:
    return float(getattr(particle, "e", getattr(particle, "E", 0.0)))


def _select_recoil_photon(event: Any, expected_energy: float) -> Any | None:
    photons = [
        p
        for p in event.particles
        if int(getattr(p, "id", getattr(p, "pid", 0))) == 22 and int(getattr(p, "status", 0)) == 1
    ]
    if not photons:
        return None
    return min(photons, key=lambda p: abs(_particle_energy(p) - expected_energy))


def validate_recoil_photon(lhe_path: Path, m_a: float, sqrt_s: float, plot_path: Path | None = None) -> dict[str, Any]:
    pylhe = _require_pylhe()
    npx = _require_numpy()
    recoil_tool = _require_prediction_tool("e_gamma_recoil", e_gamma_recoil)
    expected = float(recoil_tool(m_a, sqrt_s))
    energies: list[float] = []
    for event in pylhe.read_lhe(str(lhe_path)):
        photon = _select_recoil_photon(event, expected)
        if photon is not None:
            energies.append(_particle_energy(photon))
    if not energies:
        raise ValueError(f"No final-state photons found in {lhe_path}")

    values = npx.asarray(energies)
    mc_mean = float(values.mean())
    rel_diff = abs(mc_mean - expected) / expected if expected else math.inf

    if plot_path:
        plt = _require_pyplot()
        plt.figure()
        plt.hist(values, bins=50, alpha=0.75, label="MC")
        plt.axvline(expected, color="red", linestyle="--", linewidth=2, label=f"Theory {expected:.4g} GeV")
        plt.xlabel("Recoil photon energy [GeV]")
        plt.ylabel("Events")
        plt.legend()
        plot_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(plot_path, dpi=150, bbox_inches="tight")
        plt.close()

    return {
        "observable": "recoil_photon_energy",
        "mc_mean_GeV": mc_mean,
        "theory_GeV": expected,
        "relative_difference": rel_diff,
        "n_photons": int(values.size),
    }


def validate_angular(lhe_path: Path, m_a: float, sqrt_s: float, plot_path: Path | None = None) -> dict[str, Any]:
    pylhe = _require_pylhe()
    npx = _require_numpy()
    recoil_tool = _require_prediction_tool("e_gamma_recoil", e_gamma_recoil)
    expected_energy = float(recoil_tool(m_a, sqrt_s))
    cos_theta: list[float] = []
    for event in pylhe.read_lhe(str(lhe_path)):
        photon = _select_recoil_photon(event, expected_energy)
        if photon is None:
            continue
        px = float(photon.px)
        py = float(photon.py)
        pz = float(photon.pz)
        pmag = math.sqrt(px * px + py * py + pz * pz)
        if pmag > 0:
            cos_theta.append(pz / pmag)
    if not cos_theta:
        raise ValueError(f"No recoil photon angles found in {lhe_path}")

    values = npx.asarray(cos_theta)
    counts, edges = npx.histogram(values, bins=40)
    centers = 0.5 * (edges[1:] + edges[:-1])
    bin_width = edges[1] - edges[0]
    expected_counts = values.size * bin_width * (3.0 / 8.0) * (1.0 + centers**2)
    chi2 = float(npx.sum((counts - expected_counts) ** 2 / npx.maximum(expected_counts, 1.0)))
    ndof = max(len(counts) - 1, 1)

    if plot_path:
        plt = _require_pyplot()
        grid = npx.linspace(-1, 1, 200)
        theory_pdf = (3.0 / 8.0) * (1.0 + grid**2)
        plt.figure()
        plt.hist(values, bins=40, density=True, alpha=0.75, label="MC")
        plt.plot(grid, theory_pdf, "r--", linewidth=2, label="Theory")
        plt.xlabel("cos(theta_CM)")
        plt.ylabel("Probability density")
        plt.legend()
        plot_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(plot_path, dpi=150, bbox_inches="tight")
        plt.close()

    return {
        "observable": "angular_distribution",
        "chi2": chi2,
        "ndof": ndof,
        "chi2_per_ndof": chi2 / ndof,
        "n_photons": int(values.size),
    }


def validate_decay_length(
    hepmc_path: Path,
    m_a: float,
    g_agg: float,
    sqrt_s: float,
    alp_pdg_id: int,
    plot_path: Path | None = None,
    position_unit_to_m: float = 1e-3,
) -> dict[str, Any]:
    pyhepmc = _require_pyhepmc()
    npx = _require_numpy()
    distances: list[float] = []
    with pyhepmc.open(str(hepmc_path)) as handle:
        for event in handle:
            for particle in event.particles:
                if abs(int(particle.pid)) != alp_pdg_id or particle.end_vertex is None:
                    continue
                pos = particle.end_vertex.position
                distances.append(math.sqrt(pos.x**2 + pos.y**2 + pos.z**2) * position_unit_to_m)
    if not distances:
        raise ValueError(f"No ALP decay vertices with PDG {alp_pdg_id} found in {hepmc_path}")

    values = npx.asarray(distances)
    ell_tool = _require_prediction_tool("ell_a", ell_a)
    theory = float(ell_tool(m_a, g_agg, sqrt_s))
    mc_mean = float(values.mean())
    rel_diff = abs(mc_mean - theory) / theory if theory else math.inf

    if plot_path:
        plt = _require_pyplot()
        plt.figure()
        plt.hist(values, bins=50, alpha=0.75, label="MC")
        plt.axvline(theory, color="red", linestyle="--", linewidth=2, label=f"Theory {theory:.3e} m")
        plt.xlabel("Decay distance [m]")
        plt.ylabel("ALPs")
        plt.yscale("log")
        plt.legend()
        plot_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(plot_path, dpi=150, bbox_inches="tight")
        plt.close()

    return {
        "observable": "decay_length",
        "mc_mean_m": mc_mean,
        "theory_m": theory,
        "relative_difference": rel_diff,
        "n_decays": int(values.size),
    }


def validate_opening_angle(
    hepmc_path: Path,
    m_a: float,
    sqrt_s: float,
    alp_pdg_id: int,
    plot_path: Path | None = None,
) -> dict[str, Any]:
    pyhepmc = _require_pyhepmc()
    npx = _require_numpy()
    delta_theta_tool = _require_prediction_tool("delta_theta_min", delta_theta_min)
    opening_angles: list[float] = []
    with pyhepmc.open(str(hepmc_path)) as handle:
        for event in handle:
            for particle in event.particles:
                if abs(int(particle.pid)) != alp_pdg_id or particle.end_vertex is None:
                    continue
                children = [child for child in particle.end_vertex.particles_out if int(child.pid) == 22]
                if len(children) != 2:
                    continue
                p1 = children[0].momentum
                p2 = children[1].momentum
                v1 = npx.array([p1.px, p1.py, p1.pz], dtype=float)
                v2 = npx.array([p2.px, p2.py, p2.pz], dtype=float)
                denom = npx.linalg.norm(v1) * npx.linalg.norm(v2)
                if denom == 0:
                    continue
                cos_angle = float(npx.dot(v1, v2) / denom)
                opening_angles.append(float(npx.arccos(npx.clip(cos_angle, -1.0, 1.0))))
    if not opening_angles:
        raise ValueError(f"No gamma gamma ALP decays with PDG {alp_pdg_id} found in {hepmc_path}")

    values = npx.asarray(opening_angles)
    theory = float(delta_theta_tool(m_a, sqrt_s))
    mc_min = float(values.min())

    if plot_path:
        plt = _require_pyplot()
        plt.figure()
        plt.hist(npx.degrees(values), bins=50, alpha=0.75, label="MC")
        plt.axvline(npx.degrees(theory), color="red", linestyle="--", linewidth=2, label=f"Theory {npx.degrees(theory):.3g} deg")
        plt.xlabel("Opening angle [deg]")
        plt.ylabel("ALPs")
        plt.legend()
        plot_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(plot_path, dpi=150, bbox_inches="tight")
        plt.close()

    return {
        "observable": "opening_angle",
        "mc_min_rad": mc_min,
        "theory_min_rad": theory,
        "mc_min_deg": float(npx.degrees(mc_min)),
        "theory_min_deg": float(npx.degrees(theory)),
        "n_decays": int(values.size),
    }


def validate_point(
    run_dir: Path,
    m_a: float,
    g_agg: float,
    sqrt_s: float,
    alp_pdg_id: int = 9999,
    banner_path: Path | None = None,
    width_path: Path | None = None,
    lhe_path: Path | None = None,
    hepmc_path: Path | None = None,
    plots_dir: Path | None = None,
) -> dict[str, Any]:
    """Run all available validation checks for one MC production point."""
    run_dir = run_dir.resolve()
    plots_dir = plots_dir or run_dir / "validation_plots"
    results: dict[str, Any] = {
        "run_dir": str(run_dir),
        "m_a_GeV": m_a,
        "g_agg_GeV_inv": g_agg,
        "sqrt_s_GeV": sqrt_s,
        "alp_pdg_id": alp_pdg_id,
        "checks": [],
    }

    banner_path = banner_path or find_banner(run_dir)
    if banner_path:
        results["checks"].append(gate1_cross_section(banner_path, m_a, g_agg, sqrt_s))
        results["banner_path"] = str(banner_path)

    width_path = width_path or find_width_file(run_dir)
    if width_path:
        width = parse_width_gev(width_path, alp_pdg_id)
        results["checks"].append(gate2_width(width, m_a, g_agg))
        results["width_path"] = str(width_path)

    lhe_path = lhe_path or find_lhe(run_dir)
    if lhe_path:
        results["checks"].append(validate_recoil_photon(lhe_path, m_a, sqrt_s, plots_dir / "val_Egamma.png"))
        results["checks"].append(validate_angular(lhe_path, m_a, sqrt_s, plots_dir / "val_angular.png"))
        results["lhe_path"] = str(lhe_path)

    hepmc_path = hepmc_path or find_hepmc(run_dir)
    if hepmc_path:
        results["checks"].append(validate_decay_length(hepmc_path, m_a, g_agg, sqrt_s, alp_pdg_id, plots_dir / "val_decaylen.png"))
        results["checks"].append(validate_opening_angle(hepmc_path, m_a, sqrt_s, alp_pdg_id, plots_dir / "val_opening.png"))
        results["hepmc_path"] = str(hepmc_path)

    summary_path = plots_dir / "validation_summary.json"
    plots_dir.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(results, indent=2))
    results["summary_path"] = str(summary_path)
    return results


def _infer_inputs(args: argparse.Namespace) -> tuple[float, float, float, dict[str, float]]:
    run_dir = Path(args.run_dir)
    param_data: dict[str, float] = {}
    param_card = Path(args.param_card) if args.param_card else find_param_card(run_dir)
    if param_card:
        param_data = parse_param_card(param_card, args.alp_pdg_id)

    run_card = Path(args.run_card) if args.run_card else find_run_card(run_dir)
    run_data = parse_run_card(run_card) if run_card else {}

    m_a = args.m_a if args.m_a is not None else param_data.get("m_a_GeV")
    g_agg = args.g if args.g is not None else param_data.get("g_agg_ufo_guess_GeV_inv")
    sqrt_s = args.sqrt_s if args.sqrt_s is not None else run_data.get("sqrt_s")

    missing = []
    if m_a is None:
        missing.append("--m-a or param_card MASS 9999")
    if g_agg is None:
        missing.append("--g or parseable ALP fa/KB/KW")
    if sqrt_s is None:
        missing.append("--sqrt-s or run_card ebeam1/ebeam2")
    if missing:
        raise ValueError("Missing required inputs: " + ", ".join(missing))

    return float(m_a), float(g_agg), float(sqrt_s), param_data


def _print_summary(results: dict[str, Any], param_data: dict[str, float]) -> None:
    if param_data:
        print("Parsed param-card metadata:")
        for key in sorted(param_data):
            print(f"  {key}: {param_data[key]:.8g}")
        if "g_agg_ufo_guess_GeV_inv" in param_data:
            print("  Note: g_agg_ufo_guess uses alpha*(KB+KW)/(2*pi*fa); lock this mapping with Gate 1/2.")
    print(f"Validation summary: {results['summary_path']}")
    for check in results["checks"]:
        name = check.get("gate") or check.get("observable")
        print(f"- {name}:")
        for key, value in check.items():
            if key in {"gate", "observable"}:
                continue
            print(f"    {key}: {value}")


def _print_pipeline_summary(results: dict[str, Any]) -> None:
    print(f"Pipeline validation summary: {results['summary_path']}")
    print(f"Overall passed: {results['passed']}")
    for check in results["checks"]:
        print(f"- {check['check']}:")
        for key, value in check.items():
            if key == "check":
                continue
            print(f"    {key}: {value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate one MC point against theory predictions.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument(
        "--pipeline-smoke",
        action="store_true",
        help="Validate the non-ALP MG5/Pythia/HepMC/ROOT/Delphes smoke-test outputs.",
    )
    parser.add_argument("--m-a", type=float, default=None)
    parser.add_argument("--g", type=float, default=None, help="Physical g_agg in GeV^-1.")
    parser.add_argument("--sqrt-s", type=float, default=None)
    parser.add_argument("--alp-pdg-id", type=int, default=9999)
    parser.add_argument("--banner", type=Path, default=None)
    parser.add_argument("--width-file", type=Path, default=None)
    parser.add_argument("--lhe", type=Path, default=None)
    parser.add_argument("--hepmc", type=Path, default=None)
    parser.add_argument("--param-card", type=Path, default=None)
    parser.add_argument("--run-card", type=Path, default=None)
    parser.add_argument("--plots-dir", type=Path, default=None)
    args = parser.parse_args()

    if args.pipeline_smoke:
        results = validate_pipeline_outputs(args.run_dir, args.plots_dir)
        _print_pipeline_summary(results)
        raise SystemExit(0 if results["passed"] else 1)

    m_a, g_agg, sqrt_s, param_data = _infer_inputs(args)
    results = validate_point(
        run_dir=args.run_dir,
        m_a=m_a,
        g_agg=g_agg,
        sqrt_s=sqrt_s,
        alp_pdg_id=args.alp_pdg_id,
        banner_path=args.banner,
        width_path=args.width_file,
        lhe_path=args.lhe,
        hepmc_path=args.hepmc,
        plots_dir=args.plots_dir,
    )
    _print_summary(results, param_data)


if __name__ == "__main__":
    main()
