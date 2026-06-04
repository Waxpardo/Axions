#!/usr/bin/env python3
"""
analysis/validation_mumu/plot_muon_pt_matplotlib.py

Matplotlib muon pT validation plot for e+e- -> mu+mu-.

Reads the Delphes ROOT file without loading libDelphes.so:
  - primary path : uproot (pure Python, zero shared-library dependency)
  - fallback path: ROOT TLeaf API (requires ROOT but NOT libDelphes)

Physics: at sqrt(s)=10.58 GeV each muon carries |p|~5.29 GeV; within the
Belle-II-like acceptance (|eta|<1.13, theta~36-144 deg) reconstructed pT
peaks in the 3-5 GeV range.  This plot confirms the full MG5->Pythia->Delphes
chain ran correctly on a known-answer process before trusting ALP results.

Usage (run from repo root after sourcing env/setup_lcg105.sh):
    python analysis/validation_mumu/plot_muon_pt_matplotlib.py
"""

import os
import sys
import numpy as np

INPUT   = "PROC_validation_mumu/Events/run_01/delphes_mumu.root"
OUTDIR  = "plots/validation_mumu"
OUT_PNG = os.path.join(OUTDIR, "muon_pt_matplotlib.png")
OUT_PDF = os.path.join(OUTDIR, "muon_pt_matplotlib.pdf")

if not os.path.isfile(INPUT):
    sys.exit(
        f"ERROR: Delphes output not found: {INPUT}\n"
        "       Run Stage 3 first:  bash mc/delphes_validation_mumu.sh"
    )

# ---------------------------------------------------------------------------
# Read muon pT — uproot preferred, ROOT TLeaf as fallback
# ---------------------------------------------------------------------------
def _read_uproot(path):
    import uproot
    with uproot.open(path) as f:
        tree = f["Delphes"]
        n_events = tree.num_entries
        # "Muon/Muon.PT" is the uproot path into the TClonesArray sub-branch.
        # Returns a jagged array (one variable-length array of floats per event).
        jagged = tree["Muon/Muon.PT"].array(library="np")
    non_empty = [a for a in jagged if len(a) > 0]
    pt = np.concatenate(non_empty) if non_empty else np.array([], dtype=float)
    return n_events, pt


def _read_tleaf(path):
    import ROOT
    ROOT.gROOT.SetBatch(True)
    ROOT.gErrorIgnoreLevel = ROOT.kWarning
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        sys.exit(f"ERROR: cannot open {path}")
    tree = f.Get("Delphes")
    if not tree:
        sys.exit("ERROR: no 'Delphes' tree found")
    n_events = tree.GetEntries()
    leaf_size = tree.GetLeaf("Muon_size")
    leaf_pt   = tree.GetLeaf("Muon.PT")
    if not leaf_size or not leaf_pt:
        sys.exit("ERROR: Muon_size or Muon.PT leaf not found in tree")
    pt = []
    for i in range(n_events):
        tree.GetEntry(i)
        n = int(leaf_size.GetValue(0))
        for j in range(n):
            pt.append(leaf_pt.GetValue(j))
    f.Close()
    return n_events, np.array(pt, dtype=float)


try:
    import uproot  # noqa: F401
    n_events, pt_values = _read_uproot(INPUT)
    reader = "uproot"
except ImportError:
    print("uproot not found — falling back to ROOT TLeaf reading")
    n_events, pt_values = _read_tleaf(INPUT)
    reader = "ROOT TLeaf"

n_muons = len(pt_values)
mean_pt = float(pt_values.mean()) if n_muons > 0 else 0.0

print()
print(f"Reader              : {reader}")
print(f"Delphes events read : {n_events}")
print(f"Reconstructed muons : {n_muons}")
print(f"Mean muon pT        : {mean_pt:.3f} GeV")
print(f"(expect ~3-5 GeV within |eta|<1.13 for e+e- -> mu+mu- at sqrt(s)=10.58 GeV)")
print()

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")           # non-interactive; must be set before pyplot import
import matplotlib.pyplot as plt

os.makedirs(OUTDIR, exist_ok=True)

BIN_EDGES = np.linspace(0.0, 6.0, 31)   # 30 bins of 0.2 GeV each
counts, edges = np.histogram(pt_values, bins=BIN_EDGES)
centers = 0.5 * (edges[:-1] + edges[1:])
width   = edges[1] - edges[0]

fig, ax = plt.subplots(figsize=(8, 6))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

ax.bar(
    centers, counts, width=width,
    color="#1f77b4", alpha=0.75,
    edgecolor="#174e82", linewidth=0.8,
    label=r"Reconstructed $\mu$",
)

ax.set_xlabel(r"Reconstructed muon $p_T$ [GeV]", fontsize=13)
ax.set_ylabel("Muons / bin", fontsize=13)
ax.set_title(r"$e^+e^- \to \mu^+\mu^-$ validation", fontsize=14)
ax.set_xlim(0.0, 6.0)
ax.set_ylim(0, ax.get_ylim()[1] * 1.30)
ax.tick_params(axis="both", which="major", labelsize=11)

# Stats box (upper-right)
stats_lines = "\n".join([
    f"Events:  {n_events}",
    f"Muons:  {n_muons}",
    f"Mean $p_T$:  {mean_pt:.2f} GeV",
])
ax.text(
    0.97, 0.97, stats_lines,
    transform=ax.transAxes,
    fontsize=11,
    verticalalignment="top",
    horizontalalignment="right",
    bbox=dict(
        boxstyle="round,pad=0.45",
        facecolor="white",
        edgecolor="gray",
        alpha=0.85,
    ),
)

# Watermark — makes clear this is not a Belle II physics result
ax.text(
    0.01, 0.99,
    "Software-chain validation only — NOT a Belle II physics result",
    transform=ax.transAxes,
    fontsize=7.5,
    color="gray",
    verticalalignment="top",
)

fig.tight_layout()
fig.savefig(OUT_PNG, dpi=150, bbox_inches="tight", facecolor="white")
fig.savefig(OUT_PDF,           bbox_inches="tight", facecolor="white")

print(f"Saved: {OUT_PNG}")
print(f"Saved: {OUT_PDF}")
