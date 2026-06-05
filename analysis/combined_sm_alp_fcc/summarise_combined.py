#!/usr/bin/env python3
"""
FCC-ee COMBINED SM+ALP -- Stage-4 validation summary and plots.

Reads the combined Delphes ROOT output, the Stage-1 metadata sidecar, and the
parton-level LHE (for the ALP truth count). Produces validation plots only --
no final physics interpretation:

  * photon multiplicity
  * diphoton invariant mass, full range 0-240 GeV (log y)
  * diphoton invariant mass, zoom 0-30 GeV with the m_a=10 GeV marker
    (where a populated ALP sample shows its resonance)
  * truth ALP-event count (from the LHE)
  * reconstructed ALP-candidate bump check (diphoton pairs in a 10 GeV window)

Diphoton mass uses the same massless four-vector formula as the validated ALP
plot (E = pT*cosh(eta)); all unique photon pairs per event are used.

Reader: uproot primary, ROOT TLeaf fallback.

Usage:
    bash analysis/combined_sm_alp_fcc/run_summary.sh [honest|boosted]
    python analysis/combined_sm_alp_fcc/summarise_combined.py --variant honest
"""

import argparse
import json
import os
import sys

import numpy as np

# Local import (same directory) for the ALP truth counter.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from count_alp_lhe import count_alp
except Exception:                       # pragma: no cover
    count_alp = None

M_ALP = 10.0          # GeV -- benchmark ALP mass (annotation + bump window)
BUMP_HALF_WIDTH = 2.0  # GeV -- +/- window around m_a for the candidate count

# ---------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="FCC-ee combined SM+ALP validation summary")
parser.add_argument("variant", nargs="?", choices=["honest", "boosted"], default="honest",
                    help="which variant to summarise (positional, matches the gen/shower/delphes scripts)")
parser.add_argument("--root", default=None, help="Delphes ROOT (overrides --variant default)")
parser.add_argument("--meta", default=None, help="metadata JSON (overrides --variant default)")
parser.add_argument("--lhe",  default=None, help="parton-level LHE (overrides --variant default)")
parser.add_argument("--outdir", default=None, help="output dir (default analysis/combined_sm_alp_fcc/plots/<variant>)")
args = parser.parse_args()

PROC = "PROC_combined_sm_alp_fcc" if args.variant == "honest" else "PROC_combined_sm_alp_fcc_boosted"
RUN  = f"{PROC}/Events/run_01"
ROOT_PATH = args.root or f"{RUN}/delphes_combined_sm_alp_fcc.root"
META_PATH = args.meta or f"{RUN}/metadata_combined_sm_alp_fcc.json"
LHE_PATH  = args.lhe  or f"{RUN}/unweighted_events.lhe.gz"
OUTDIR    = args.outdir or f"analysis/combined_sm_alp_fcc/plots/{args.variant}"


# ---------------------------------------------------------------------------
# Readers (uproot primary, ROOT TLeaf fallback) -- photon kinematics only
# ---------------------------------------------------------------------------
def _read_uproot(path):
    import uproot
    with uproot.open(path) as f:
        tree = f["Delphes"]
        n = tree.num_entries
        pt  = tree["Photon/Photon.PT"].array(library="np")
        eta = tree["Photon/Photon.Eta"].array(library="np")
        phi = tree["Photon/Photon.Phi"].array(library="np")
    return n, list(pt), list(eta), list(phi)


def _read_tleaf(path):
    import ROOT
    ROOT.gROOT.SetBatch(True)
    ROOT.gErrorIgnoreLevel = ROOT.kError
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        raise RuntimeError(f"cannot open {path}")
    tree = f.Get("Delphes")
    if not tree:
        raise RuntimeError("Delphes tree not found")
    n = tree.GetEntries()
    lsize = tree.GetLeaf("Photon_size")
    lpt, leta, lphi = tree.GetLeaf("Photon.PT"), tree.GetLeaf("Photon.Eta"), tree.GetLeaf("Photon.Phi")
    pt, eta, phi = [], [], []
    for i in range(n):
        tree.GetEntry(i)
        m = int(lsize.GetValue(0))
        pt.append(np.array([lpt.GetValue(j)  for j in range(m)]))
        eta.append(np.array([leta.GetValue(j) for j in range(m)]))
        phi.append(np.array([lphi.GetValue(j) for j in range(m)]))
    f.Close()
    return n, pt, eta, phi


def read_photons(path):
    try:
        import uproot  # noqa: F401
        out = _read_uproot(path); print("Reader: uproot"); return out
    except ImportError:
        pass
    except Exception as exc:
        print(f"WARNING: uproot failed ({exc}); trying ROOT TLeaf")
    try:
        import ROOT  # noqa: F401
        out = _read_tleaf(path); print("Reader: ROOT TLeaf"); return out
    except Exception as exc:
        sys.exit(f"ERROR: could not read {path}: {exc}\n"
                 "       Run via: bash analysis/combined_sm_alp_fcc/run_summary.sh")


# ---------------------------------------------------------------------------
# Diphoton invariant mass -- all unique pairs, massless four-vectors
# ---------------------------------------------------------------------------
def compute_mgg(pt_j, eta_j, phi_j):
    mgg = []
    nph = np.array([len(p) for p in pt_j], dtype=int)
    for pt, eta, phi in zip(pt_j, eta_j, phi_j):
        m = len(pt)
        if m < 2:
            continue
        E  = pt * np.cosh(eta)
        px = pt * np.cos(phi)
        py = pt * np.sin(phi)
        pz = pt * np.sinh(eta)
        for i in range(m):
            for j in range(i + 1, m):
                m2 = ((E[i]+E[j])**2 - (px[i]+px[j])**2
                      - (py[i]+py[j])**2 - (pz[i]+pz[j])**2)
                mgg.append(float(np.sqrt(max(m2, 0.0))))
    return np.array(mgg, dtype=float), nph


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------
def make_plots(nph, mgg, variant, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(outdir, exist_ok=True)
    BLUE, EDGE = "#1f77b4", "#174e82"
    tag = f"FCC-ee combined SM+ALP ({variant})  √s=240 GeV"

    # 1. photon multiplicity
    fig, ax = plt.subplots(figsize=(7, 5))
    max_n = max(int(nph.max()) if len(nph) else 4, 4)
    ax.hist(nph, bins=np.arange(-0.5, max_n + 1.5, 1.0),
            color=BLUE, alpha=0.8, edgecolor=EDGE)
    ax.set_xlabel("Reconstructed photons / event")
    ax.set_ylabel("Events")
    ax.set_title(tag)
    ax.text(0.97, 0.97, f"events: {len(nph)}\nmean: {nph.mean():.2f}/evt",
            transform=ax.transAxes, ha="right", va="top",
            bbox=dict(boxstyle="round", fc="white", alpha=0.8))
    fig.tight_layout(); fig.savefig(os.path.join(outdir, "photon_multiplicity.png"), dpi=150)
    plt.close(fig); print(f"  Saved: {outdir}/photon_multiplicity.png")

    # 2. diphoton mass, full range (log y)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(mgg, bins=100, range=(0, 240), color=BLUE, alpha=0.8, edgecolor=EDGE, linewidth=0.4)
    ax.axvline(M_ALP, color="crimson", ls="--", lw=1.2, label=f"$m_a$={M_ALP:.0f} GeV")
    ax.set_yscale("log"); ax.set_ylim(bottom=0.5)
    ax.set_xlabel(r"$m(\gamma\gamma)$ [GeV]"); ax.set_ylabel("Photon pairs / 2.4 GeV")
    ax.set_title(tag + "  -- all pairs"); ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(outdir, "diphoton_mass_full.png"), dpi=150)
    plt.close(fig); print(f"  Saved: {outdir}/diphoton_mass_full.png")

    # 3. diphoton mass, zoom on the ALP region
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(mgg, bins=60, range=(0, 30), color=BLUE, alpha=0.8, edgecolor=EDGE, linewidth=0.5)
    ax.axvline(M_ALP, color="crimson", ls="--", lw=1.5, label=f"$m_a$={M_ALP:.0f} GeV")
    ax.set_xlabel(r"$m(\gamma\gamma)$ [GeV]"); ax.set_ylabel("Photon pairs / 0.5 GeV")
    ax.set_title(tag + "  -- ALP search window"); ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(outdir, "diphoton_mass_zoom.png"), dpi=150)
    plt.close(fig); print(f"  Saved: {outdir}/diphoton_mass_zoom.png")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if not os.path.exists(ROOT_PATH):
    sys.exit(f"ERROR: Delphes ROOT not found: {ROOT_PATH}\n"
             f"       Run Stage 3 first: bash mc/combined_sm_alp_fcc/delphes_combined_sm_alp_fcc.sh {args.variant}")

meta = {}
if os.path.exists(META_PATH):
    with open(META_PATH) as f:
        meta = json.load(f)
else:
    print(f"WARNING: metadata not found at {META_PATH}")

print(f"Reading: {ROOT_PATH}")
n_events, pt_j, eta_j, phi_j = read_photons(ROOT_PATH)
mgg, nph = compute_mgg(pt_j, eta_j, phi_j)

# ALP truth count from the LHE (independent of the reconstructed sample)
n_alp_truth, n_lhe_tot, n_alp_dec = (None, None, None)
if count_alp is not None and os.path.exists(LHE_PATH):
    try:
        n_alp_truth, n_lhe_tot, n_alp_dec = count_alp(LHE_PATH)
    except Exception as exc:
        print(f"WARNING: ALP truth count failed: {exc}")

# Reconstructed ALP-candidate bump: pairs within +/- BUMP_HALF_WIDTH of m_a
in_window = int(np.sum((mgg > M_ALP - BUMP_HALF_WIDTH) & (mgg < M_ALP + BUMP_HALF_WIDTH)))

# ---- terminal summary ----
SEP = "=" * 70
print(); print(SEP)
print(f"  FCC-ee COMBINED SM+ALP -- VALIDATION SUMMARY ({args.variant})")
print(SEP)
if meta:
    print(f"  Total xsec      : {meta.get('total_xsec_pb','?')} +- {meta.get('xsec_uncertainty_pb','?')} pb")
    print(f"  Coupling point  : {meta.get('coupling_point','?')}")
    print(f"  git commit      : {meta.get('git_commit','?')}")
print(f"  Events in ROOT  : {n_events}")
print(f"  Mean photons/evt: {nph.mean():.3f}" if len(nph) else "  (no photons)")
print(f"  Diphoton pairs  : {len(mgg)}")
if len(mgg):
    print(f"  Mean m(gg)      : {mgg.mean():.2f} GeV   Max m(gg): {mgg.max():.2f} GeV")
print()
print("  Truth-level ALP accounting (from LHE)")
if n_alp_truth is not None:
    truth_frac = (n_alp_truth / n_lhe_tot) if n_lhe_tot else 0.0
    print(f"    Generated events:            {n_lhe_tot}")
    print(f"    Events containing ALP:       {n_alp_truth}")
    print(f"    ALP decay photons found:     {n_alp_dec}")
    print(f"    Fraction of events with ALP: {truth_frac:.4f}")
else:
    print("    (LHE unavailable)")
print(f"  Reco pairs in [{M_ALP-BUMP_HALF_WIDTH:.0f},{M_ALP+BUMP_HALF_WIDTH:.0f}] GeV : {in_window}")
if args.variant == "honest" and (n_alp_truth == 0 or n_alp_truth is None):
    print("  -> honest variant: ~0 ALP signal as expected; the m_a window count")
    print("     is pure SM combinatoric/π0 background (no resonance).")
elif args.variant == "boosted":
    print("  -> boosted variant: a peak at 10 GeV in the zoom plot validates the")
    print("     ALP signal propagating through the full reco chain (NON-PHYSICAL σ).")
print(SEP)

print("\nGenerating plots...")
make_plots(nph, mgg, args.variant, OUTDIR)

# ---- JSON summary ----
summary = {
    "variant": args.variant,
    "input_root": ROOT_PATH,
    "n_events": int(n_events),
    "mean_photons_per_event": round(float(nph.mean()), 4) if len(nph) else 0.0,
    "n_diphoton_pairs": int(len(mgg)),
    "mean_mgg_gev": round(float(mgg.mean()), 3) if len(mgg) else None,
    "max_mgg_gev": round(float(mgg.max()), 3) if len(mgg) else None,
    "alp_truth_events_lhe": n_alp_truth,
    "alp_decay_photons_lhe": n_alp_dec,
    "lhe_total_events": n_lhe_tot,
    "reco_pairs_in_alp_window": in_window,
    "alp_window_gev": [M_ALP - BUMP_HALF_WIDTH, M_ALP + BUMP_HALF_WIDTH],
    "production_metadata": meta,
}
os.makedirs(OUTDIR, exist_ok=True)
out = os.path.join(OUTDIR, "summary_combined.json")
with open(out, "w") as f:
    json.dump(summary, f, indent=2)
print(f"\nWriting JSON summary...\n  Saved: {out}")
print(f"\nAll outputs in: {OUTDIR}/")
