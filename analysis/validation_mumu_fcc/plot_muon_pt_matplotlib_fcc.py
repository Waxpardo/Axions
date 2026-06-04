#!/usr/bin/env python3
"""
analysis/validation_mumu_fcc/plot_muon_pt_matplotlib_fcc.py

Matplotlib muon pT validation plot for e+e- -> mu+mu- at FCC-ee, sqrt(s)=240 GeV.

Reads the Delphes ROOT file without loading libDelphes.so:
  - primary path : uproot (pure Python, zero shared-library dependency)
  - fallback path: ROOT TLeaf API (requires ROOT but NOT libDelphes)

Physics: at sqrt(s)=240 GeV each muon carries |p|~120 GeV. Within the IDEA
acceptance (|eta|<3.0, theta~5.7-174 deg) reconstructed pT spans roughly
12-120 GeV, peaking in the 40-80 GeV range (weighted by the QED 1+cos^2(theta)
angular distribution). This is ~23x the Belle II pT scale; the x-axis runs
0-130 GeV accordingly.

Usage (run from repo root after sourcing env/setup_lcg105.sh):
    python analysis/validation_mumu_fcc/plot_muon_pt_matplotlib_fcc.py
"""

import os
import sys
import numpy as np

INPUT   = "PROC_validation_mumu_fcc/Events/run_01/delphes_mumu_fcc.root"
OUTDIR  = "plots/validation_mumu_fcc"
OUT_PNG = os.path.join(OUTDIR, "muon_pt_matplotlib_fcc.png")
OUT_PDF = os.path.join(OUTDIR, "muon_pt_matplotlib_fcc.pdf")

if not os.path.isfile(INPUT):
    sys.exit(
        f"ERROR: Delphes output not found: {INPUT}\n"
        "       Run Stage 3 first:  bash mc/delphes_validation_mumu_fcc.sh"
    )

# ---------------------------------------------------------------------------
# Read muon pT — uproot preferred, ROOT TLeaf as fallback
# ---------------------------------------------------------------------------
def _read_uproot(path):
    import uproot
    with uproot.open(path) as f:
        tree = f["Delphes"]
        n_events = tree.num_entries
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
print(f"(expect ~40-80 GeV within |eta|<3.0 for e+e- -> mu+mu- at sqrt(s)=240 GeV)")
print()

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs(OUTDIR, exist_ok=True)

# 52 bins of 2.5 GeV each, 0-130 GeV — covers the full beam-energy range.
# Each muon carries |p|~120 GeV; pT_max = 120 GeV for central (theta=90 deg) muons.
# (Previously: 26 bins of 5.0 GeV, np.linspace(0.0, 130.0, 27))
BIN_EDGES = np.linspace(0.0, 130.0, 53)
print(f"Bins used: {len(BIN_EDGES)-1}  (width {(BIN_EDGES[1]-BIN_EDGES[0]):.1f} GeV, range 0-130 GeV)")
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
ax.set_title(
    r"$e^+e^- \to \mu^+\mu^-$ validation  (FCC-ee IDEA, $\sqrt{s}=240$ GeV)",
    fontsize=13,
)
ax.set_xlim(0.0, 130.0)
ax.set_ylim(0, ax.get_ylim()[1] * 1.30)
ax.tick_params(axis="both", which="major", labelsize=11)

# Stats box (upper-right)
stats_lines = "\n".join([
    f"Events:  {n_events}",
    f"Muons:  {n_muons}",
    f"Mean $p_T$:  {mean_pt:.1f} GeV",
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

# Watermark
ax.text(
    0.01, 0.99,
    "Software-chain validation only — NOT an FCC-ee physics result",
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
