#!/usr/bin/env python3
"""
FCC-ee SM background -- diphoton invariant mass analysis

Primary ALP search observable: e+e- -> gamma a, a -> gamma gamma
would appear as a narrow bump in m(gamma gamma).

Reads all reconstructed photons from the Delphes ROOT file and computes
the Lorentz-invariant diphoton invariant mass for every unique photon pair
in each event. No pair is skipped on pT ordering -- all combinations are
formed, as required for model-independent bump hunting.

Outputs:
    analysis/background_sm_fcc/plots/diphoton_mass_sm_bkg.png
    analysis/background_sm_fcc/plots/diphoton_mass_sm_bkg_logy.png
    analysis/background_sm_fcc/plots/diphoton_mass_sm_bkg_summary.json

Usage:
    bash analysis/background_sm_fcc/run_diphoton.sh
    python analysis/background_sm_fcc/diphoton_mass.py [--root ...] [--meta ...] [--outdir ...]
"""

import argparse
import json
import math
import os
import sys

parser = argparse.ArgumentParser(description="FCC-ee SM background diphoton invariant mass")
parser.add_argument(
    "--root",
    default="PROC_background_sm_fcc/Events/run_01/delphes_sm_fcc.root",
    help="Path to Delphes ROOT output",
)
parser.add_argument(
    "--meta",
    default="PROC_background_sm_fcc/Events/run_01/metadata_sm_fcc.json",
    help="Path to production metadata JSON",
)
parser.add_argument(
    "--outdir",
    default="analysis/background_sm_fcc/plots",
    help="Output directory for plots and JSON summary",
)
args = parser.parse_args()


# ---------------------------------------------------------------------------
# Four-vector helpers (pure Python, no ROOT/numpy dependency at call time)
# ---------------------------------------------------------------------------

def _lv(pt, eta, phi, e):
    """Return (E, px, py, pz) from Delphes photon branches."""
    px = pt * math.cos(phi)
    py = pt * math.sin(phi)
    pz = pt * math.sinh(eta)
    return (e, px, py, pz)


def _mgg(lv1, lv2):
    """Lorentz-invariant diphoton mass from two (E,px,py,pz) tuples.

    m^2 = (E1+E2)^2 - (px1+px2)^2 - (py1+py2)^2 - (pz1+pz2)^2
    Equivalent to 2*E1*E2*(1 - cos(theta)) for massless photons.
    The max(m2, 0) guard handles floating-point rounding near collinear pairs.
    """
    m2 = (
        (lv1[0] + lv2[0]) ** 2
        - (lv1[1] + lv2[1]) ** 2
        - (lv1[2] + lv2[2]) ** 2
        - (lv1[3] + lv2[3]) ** 2
    )
    return math.sqrt(max(m2, 0.0))


# ---------------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------------

def _read_uproot(path):
    import uproot
    import numpy as np

    with uproot.open(path) as f:
        tree = f["Delphes"]
        n_events = tree.num_entries
        ph_n   = tree["Photon_size"].array(library="np").astype(int)
        ph_pt  = tree["Photon/Photon.PT"].array(library="np")
        ph_eta = tree["Photon/Photon.Eta"].array(library="np")
        ph_phi = tree["Photon/Photon.Phi"].array(library="np")
        ph_e   = tree["Photon/Photon.E"].array(library="np")

    mgg_vals = []
    n_ge2 = 0

    for i in range(n_events):
        nph = int(ph_n[i])
        if nph < 2:
            continue
        n_ge2 += 1
        lvs = [
            _lv(float(ph_pt[i][j]), float(ph_eta[i][j]),
                float(ph_phi[i][j]), float(ph_e[i][j]))
            for j in range(nph)
        ]
        for j in range(nph):
            for k in range(j + 1, nph):
                mgg_vals.append(_mgg(lvs[j], lvs[k]))

    return mgg_vals, n_events, n_ge2, ph_n


def _read_tleaf(path):
    """Fallback: ROOT TLeaf API (requires PyROOT in LCG env)."""
    import ROOT
    import numpy as np
    ROOT.gROOT.SetBatch(True)
    ROOT.gErrorIgnoreLevel = ROOT.kError

    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        raise RuntimeError(f"Cannot open ROOT file: {path}")
    tree = f.Get("Delphes")
    if not tree:
        raise RuntimeError("Delphes tree not found")

    mgg_vals = []
    n_events = 0
    n_ge2 = 0
    ph_n_list = []

    for ev in tree:
        n_events += 1
        nph = ev.Photon_size
        ph_n_list.append(nph)
        if nph < 2:
            continue
        n_ge2 += 1
        lvs = [
            _lv(ev.Photon[j].PT, ev.Photon[j].Eta,
                ev.Photon[j].Phi, ev.Photon[j].E)
            for j in range(nph)
        ]
        for j in range(nph):
            for k in range(j + 1, nph):
                mgg_vals.append(_mgg(lvs[j], lvs[k]))

    f.Close()
    return mgg_vals, n_events, n_ge2, np.array(ph_n_list)


def read_diphoton(path):
    """Try uproot first, fall back to ROOT TLeaf."""
    try:
        import uproot  # noqa: F401
        return _read_uproot(path)
    except ImportError:
        pass
    except Exception as exc:
        print(f"WARNING: uproot read failed ({exc}); trying ROOT TLeaf fallback")

    try:
        import ROOT  # noqa: F401
        return _read_tleaf(path)
    except ImportError:
        print("ERROR: neither uproot nor PyROOT is available.")
        print("       Run via: bash analysis/background_sm_fcc/run_diphoton.sh")
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: ROOT TLeaf fallback failed: {exc}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Terminal summary
# ---------------------------------------------------------------------------

def print_terminal_summary(mgg_vals, n_events, n_ge2, ph_n):
    import numpy as np

    mgg = np.array(mgg_vals)
    n_pairs = len(mgg)
    mean_ph = float(ph_n.mean()) if len(ph_n) > 0 else 0.0

    SEP = "=" * 70
    print()
    print(SEP)
    print("  FCC-ee SM BACKGROUND  --  DIPHOTON INVARIANT MASS")
    print(SEP)
    print(f"  Total events processed          : {n_events}")
    pct_str = f"  ({100*n_ge2/n_events:.1f}%)" if n_events > 0 else ""
    print(f"  Events with >= 2 photons        : {n_ge2}{pct_str}")
    print(f"  Total diphoton pairs            : {n_pairs}")
    print(f"  Mean photons / event            : {mean_ph:.3f}")
    if n_pairs > 0:
        print(f"  Mean m(gg)                      : {mgg.mean():.2f} GeV")
        print(f"  Maximum m(gg) observed          : {mgg.max():.2f} GeV")
    print()
    print("PHYSICS INTERPRETATION")
    print("-" * 40)
    print("  SM diphoton background sources:")
    print("    - Final-state radiation (FSR) off charged leptons and quarks")
    print("      -> collinear photons, peaked at low m(gg)")
    print("    - Isolated pi0->gg from hadron fragmentation passing photon ID")
    print("    - Direct qq~->gg and Wgamma/Zgamma diagrams")
    print("  Expected shape: steeply falling from low m(gg), smooth without")
    print("  any resonance structure. A bump would indicate an ALP signal")
    print("  (e+e- -> gamma a, a -> gg) or detector artefact.")
    print("  Maximum kinematically allowed for a single hard photon: ~120 GeV")
    print("  (= sqrt(s)/2). Pairs can reach 240 GeV only when both photons")
    print("  are back-to-back and each carries half the beam energy.")
    print(SEP)


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def make_plots(mgg_vals, n_events, n_ge2, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    os.makedirs(outdir, exist_ok=True)

    mgg = np.array(mgg_vals)
    n_pairs = len(mgg)
    RANGE = (0, 240)
    NBINS = 100
    BIN_W = (RANGE[1] - RANGE[0]) / NBINS   # 2.4 GeV / bin

    STYLE = dict(color="#2166ac", edgecolor="black", linewidth=0.4, alpha=0.85)

    info = (
        f"Events: {n_events}\n"
        f"Events ≥2γ: {n_ge2}\n"
        f"Total pairs: {n_pairs}\n"
        + (f"⟨m(γγ)⟩ = {mgg.mean():.1f} GeV" if n_pairs > 0 else "")
    )

    plots = [
        ("diphoton_mass_sm_bkg.png",      False),
        ("diphoton_mass_sm_bkg_logy.png", True),
    ]

    for fname, log_y in plots:
        fig, ax = plt.subplots(figsize=(7, 5))

        ax.hist(mgg, bins=NBINS, range=RANGE, **STYLE)

        ax.set_xlabel(r"$m(\gamma\gamma)$  [GeV]", fontsize=13)
        ax.set_ylabel(f"Photon pairs / {BIN_W:.1f} GeV", fontsize=12)
        ax.set_title(
            r"FCC-ee SM background  –  Diphoton invariant mass"
            "\n"
            r"$\sqrt{s}$ = 240 GeV,  IDEA detector,  anti-k$_{\rm T}$  $R$=0.5",
            fontsize=10,
        )
        ax.set_xlim(*RANGE)

        if log_y:
            ax.set_yscale("log")
            ax.set_ylim(bottom=0.5)

        # Stats box (top-right)
        ax.text(
            0.97, 0.97, info,
            transform=ax.transAxes, ha="right", va="top", fontsize=9,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
        )

        # Physics note (top-left)
        ax.text(
            0.03, 0.97,
            "ALP signal region:\nbump in this spectrum\n"
            r"($e^+e^- \to \gamma a,\; a \to \gamma\gamma$)",
            transform=ax.transAxes, ha="left", va="top", fontsize=8,
            color="#d62728",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7),
        )

        fig.tight_layout()
        out = os.path.join(outdir, fname)
        fig.savefig(out, dpi=150)
        plt.close(fig)
        print(f"  Saved: {out}")

    return RANGE, NBINS


# ---------------------------------------------------------------------------
# JSON summary
# ---------------------------------------------------------------------------

def write_json_summary(mgg_vals, n_events, n_ge2, ph_n, hist_range, nbins,
                       meta, outdir, root_path):
    import numpy as np

    mgg = np.array(mgg_vals)
    n_pairs = len(mgg)

    summary = {
        "description": "FCC-ee SM background -- diphoton invariant mass",
        "input_root": root_path,
        "n_events_processed": n_events,
        "n_events_ge2_photons": n_ge2,
        "n_diphoton_pairs": n_pairs,
        "mean_photons_per_event": round(float(ph_n.mean()), 4) if len(ph_n) > 0 else 0,
        "mean_mgg_gev": round(float(mgg.mean()), 3) if n_pairs > 0 else None,
        "max_mgg_gev": round(float(mgg.max()), 3)  if n_pairs > 0 else None,
        "histogram": {
            "range_gev": list(hist_range),
            "n_bins": nbins,
            "bin_width_gev": round((hist_range[1] - hist_range[0]) / nbins, 3),
        },
        "production_metadata": meta,
    }

    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "diphoton_mass_sm_bkg_summary.json")
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Saved: {out}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if not os.path.exists(args.root):
    sys.exit(
        f"ERROR: Delphes ROOT file not found: {args.root}\n"
        "       Run Stage 3 first:  bash mc/delphes_background_sm_fcc.sh"
    )

meta = {}
if os.path.exists(args.meta):
    with open(args.meta) as f:
        meta = json.load(f)
else:
    print(f"WARNING: metadata sidecar not found at {args.meta} -- proceeding without it")

print(f"Reading: {args.root}")
mgg_vals, n_events, n_ge2, ph_n = read_diphoton(args.root)

print_terminal_summary(mgg_vals, n_events, n_ge2, ph_n)

print("\nGenerating plots...")
hist_range, nbins = make_plots(mgg_vals, n_events, n_ge2, args.outdir)

print("\nWriting JSON summary...")
write_json_summary(mgg_vals, n_events, n_ge2, ph_n, hist_range, nbins,
                   meta, args.outdir, args.root)

print(f"\nAll outputs in: {args.outdir}/")
