#!/usr/bin/env python3
"""
analysis/validation_alp_fcc/plot_alp_validation_fcc.py

Matplotlib validation plots for e+e- -> gamma alp (alp -> gamma gamma) at
FCC-ee, sqrt(s)=240 GeV. Benchmark: m_a=10 GeV, fa=1000 GeV, KB=KW=1 (pure
photon coupling), BR(alp->gamma gamma)=100%.

Three output plots:
  1. Photon multiplicity per event
     Expected: most events have 3 reconstructed photons
     (1 prompt from production vertex + 2 from alp decay)
  2. Leading reconstructed photon pT
     Expected: peak near (s - m_a^2)/(2*sqrt(s)) ~ 120 GeV (prompt photon)
     with a shoulder at lower pT from ALP decay photons
  3. All diphoton invariant masses m_gg (all pairs within each event)
     Expected: peak at m_gg = m_a = 10 GeV from the ALP decay pair

Reads the Delphes ROOT file without loading libDelphes.so:
  - primary path : uproot (pure Python)
  - fallback path: ROOT TLeaf API

Usage (run from repo root after sourcing env/setup_lcg105.sh):
    python analysis/validation_alp_fcc/plot_alp_validation_fcc.py
"""

import os
import sys
import numpy as np

INPUT   = "PROC_validation_alp_fcc/Events/run_01/delphes_alp_fcc.root"
OUTDIR  = "plots/validation_alp_fcc"
M_ALP   = 10.0   # GeV -- benchmark ALP mass, used for annotation

if not os.path.isfile(INPUT):
    sys.exit(
        f"ERROR: Delphes output not found: {INPUT}\n"
        "       Run Stage 3 first:  bash mc/delphes_validation_alp_fcc.sh"
    )

# ---------------------------------------------------------------------------
# Read photon kinematics -- uproot preferred, ROOT TLeaf as fallback
# Each returns (n_events, list-of-arrays) where each inner array holds the
# PT / Eta / Phi values for all photons in that event (may be empty).
# ---------------------------------------------------------------------------
def _read_uproot(path):
    import uproot
    with uproot.open(path) as f:
        tree = f["Delphes"]
        n_events = tree.num_entries
        pt_j  = tree["Photon/Photon.PT"].array(library="np")
        eta_j = tree["Photon/Photon.Eta"].array(library="np")
        phi_j = tree["Photon/Photon.Phi"].array(library="np")
    return n_events, list(pt_j), list(eta_j), list(phi_j)


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
    lsize = tree.GetLeaf("Photon_size")
    lpt   = tree.GetLeaf("Photon.PT")
    leta  = tree.GetLeaf("Photon.Eta")
    lphi  = tree.GetLeaf("Photon.Phi")
    if not all([lsize, lpt, leta, lphi]):
        sys.exit("ERROR: one or more Photon leaves not found in Delphes tree")
    pt_j, eta_j, phi_j = [], [], []
    for i in range(n_events):
        tree.GetEntry(i)
        n = int(lsize.GetValue(0))
        pt_j.append( np.array([lpt.GetValue(j)  for j in range(n)]))
        eta_j.append(np.array([leta.GetValue(j) for j in range(n)]))
        phi_j.append(np.array([lphi.GetValue(j) for j in range(n)]))
    f.Close()
    return n_events, pt_j, eta_j, phi_j


try:
    import uproot  # noqa: F401
    n_events, pt_jagged, eta_jagged, phi_jagged = _read_uproot(INPUT)
    reader = "uproot"
except ImportError:
    print("uproot not found — falling back to ROOT TLeaf reading")
    n_events, pt_jagged, eta_jagged, phi_jagged = _read_tleaf(INPUT)
    reader = "ROOT TLeaf"

# ---------------------------------------------------------------------------
# Derived observables
# ---------------------------------------------------------------------------
n_photons_per_event = np.array([len(pt) for pt in pt_jagged], dtype=int)
n_total_photons     = int(n_photons_per_event.sum())

# Leading photon pT (events with >=1 photon)
leading_pt = np.array(
    [float(np.max(pt)) for pt in pt_jagged if len(pt) > 0], dtype=float
)

# All diphoton invariant masses (all pairs within each event).
# Uses massless 4-momentum: E = pT*cosh(eta), etc.
m_gg_all = []
for pt, eta, phi in zip(pt_jagged, eta_jagged, phi_jagged):
    n = len(pt)
    for i in range(n):
        Ei  = pt[i] * np.cosh(eta[i])
        pxi = pt[i] * np.cos(phi[i])
        pyi = pt[i] * np.sin(phi[i])
        pzi = pt[i] * np.sinh(eta[i])
        for j in range(i + 1, n):
            Ej  = pt[j] * np.cosh(eta[j])
            pxj = pt[j] * np.cos(phi[j])
            pyj = pt[j] * np.sin(phi[j])
            pzj = pt[j] * np.sinh(eta[j])
            m2  = (Ei+Ej)**2 - (pxi+pxj)**2 - (pyi+pyj)**2 - (pzi+pzj)**2
            m_gg_all.append(float(np.sqrt(max(m2, 0.0))))
m_gg_all = np.array(m_gg_all, dtype=float)

print()
print(f"Reader                      : {reader}")
print(f"Delphes events read         : {n_events}")

if n_events == 0:
    sys.exit(
        "ERROR: Delphes ROOT file exists but contains 0 events.\n"
        "       Run the pipeline stages first:\n"
        "         bash mc/gen_validation_alp_fcc.sh\n"
        "         bash mc/shower_validation_alp_fcc.sh\n"
        "         bash mc/delphes_validation_alp_fcc.sh"
    )

print(f"Total reconstructed photons : {n_total_photons}")
print(f"Mean photons / event        : {n_total_photons/n_events:.2f}  (expect ~3)")
print(f"Events with >=3 photons     : {int((n_photons_per_event >= 3).sum())}")
print(f"Diphoton pairs computed     : {len(m_gg_all)}")
if len(leading_pt):
    print(f"Mean leading photon pT      : {leading_pt.mean():.1f} GeV  (expect ~120 GeV)")
print()

# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs(OUTDIR, exist_ok=True)

TITLE_BASE = (
    r"$e^+e^- \to \gamma\, \mathrm{ALP}\ (\mathrm{ALP} \to \gamma\gamma)$"
    r"  (FCC-ee IDEA, $\sqrt{s}=240$ GeV)"
)
WATERMARK = r"Software-chain validation only — NOT an FCC-ee physics result"
BLUE      = "#1f77b4"
EDGE      = "#174e82"


def _save(fig, stem):
    fig.savefig(os.path.join(OUTDIR, stem + ".png"), dpi=150,
                bbox_inches="tight", facecolor="white")
    fig.savefig(os.path.join(OUTDIR, stem + ".pdf"),
                bbox_inches="tight", facecolor="white")
    print(f"Saved: {OUTDIR}/{stem}.png")
    print(f"Saved: {OUTDIR}/{stem}.pdf")
    plt.close(fig)


# ── Plot 1: photon multiplicity ─────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 5))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

max_n = max(int(n_photons_per_event.max()) if len(n_photons_per_event) else 5, 5)
bins = np.arange(-0.5, max_n + 1.5, 1.0)
ax.hist(n_photons_per_event, bins=bins,
        color=BLUE, alpha=0.75, edgecolor=EDGE, linewidth=0.8)
ax.set_xlabel("Reconstructed photon multiplicity", fontsize=13)
ax.set_ylabel("Events / bin", fontsize=13)
ax.set_title(TITLE_BASE, fontsize=12)
ax.set_xlim(-0.5, max_n + 0.5)
ax.tick_params(axis="both", which="major", labelsize=11)
ax.text(0.01, 0.99, WATERMARK, transform=ax.transAxes,
        fontsize=7.5, color="gray", verticalalignment="top")
ax.text(0.97, 0.97,
        f"Events: {n_events}\nExpect 3 photons/event",
        transform=ax.transAxes, fontsize=11,
        va="top", ha="right",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                  edgecolor="gray", alpha=0.85))
fig.tight_layout()
_save(fig, "photon_multiplicity_fcc")


# ── Plot 2: leading photon pT ────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 6))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

# 52 bins of 2.5 GeV each, 0-130 GeV (same scale as FCC-ee mumu plot)
edges_pt = np.linspace(0.0, 130.0, 53)
ax.hist(leading_pt, bins=edges_pt,
        color=BLUE, alpha=0.75, edgecolor=EDGE, linewidth=0.8,
        label=r"Leading reco $\gamma$")
ax.set_xlabel(r"Leading reconstructed photon $p_T$ [GeV]", fontsize=13)
ax.set_ylabel("Events / bin", fontsize=13)
ax.set_title(TITLE_BASE, fontsize=12)
ax.set_xlim(0.0, 130.0)
ax.set_ylim(0, ax.get_ylim()[1] * 1.30)
ax.tick_params(axis="both", which="major", labelsize=11)
ax.text(0.01, 0.99, WATERMARK, transform=ax.transAxes,
        fontsize=7.5, color="gray", verticalalignment="top")
mean_lpt = float(leading_pt.mean()) if len(leading_pt) else 0.0
ax.text(0.97, 0.97,
        f"Events: {n_events}\nMean lead $p_T$: {mean_lpt:.1f} GeV",
        transform=ax.transAxes, fontsize=11,
        va="top", ha="right",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                  edgecolor="gray", alpha=0.85))
fig.tight_layout()
_save(fig, "leading_photon_pt_fcc")


# ── Plot 3: diphoton invariant mass ─────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 6))
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

# 60 bins of 0.5 GeV each, 0-30 GeV -- shows the m_a=10 GeV peak clearly.
edges_mgg = np.linspace(0.0, 30.0, 61)
ax.hist(m_gg_all, bins=edges_mgg,
        color=BLUE, alpha=0.75, edgecolor=EDGE, linewidth=0.8,
        label=r"All $\gamma\gamma$ pairs")

# Vertical line at m_a = 10 GeV
ax.axvline(x=M_ALP, color="crimson", linewidth=1.5, linestyle="--",
           label=rf"$m_a = {M_ALP:.0f}$ GeV")

ax.set_xlabel(r"Diphoton invariant mass $m_{\gamma\gamma}$ [GeV]", fontsize=13)
ax.set_ylabel(r"Pairs / 0.5 GeV", fontsize=13)
ax.set_title(TITLE_BASE, fontsize=12)
ax.set_xlim(0.0, 30.0)
ax.set_ylim(0, ax.get_ylim()[1] * 1.35)
ax.tick_params(axis="both", which="major", labelsize=11)
ax.legend(fontsize=11, framealpha=0.85)
ax.text(0.01, 0.99, WATERMARK, transform=ax.transAxes,
        fontsize=7.5, color="gray", verticalalignment="top")
peak_note = (
    f"Events: {n_events}\n"
    f"All $\\gamma\\gamma$ pairs\n"
    r"Peak $\to$ $m_a$"
)
ax.text(0.97, 0.97, peak_note, transform=ax.transAxes, fontsize=11,
        va="top", ha="right",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                  edgecolor="gray", alpha=0.85))
fig.tight_layout()
_save(fig, "diphoton_mass_fcc")
