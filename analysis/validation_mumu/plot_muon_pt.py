#!/usr/bin/env python3
"""
analysis/validation_mumu/plot_muon_pt.py

Stage-4 analysis: reconstructed muon pT from e+e- -> mu+mu- Delphes output.

Purpose (physics): plots the pT spectrum of Delphes-reconstructed muons from
the e+e- -> mu+mu- smoke test. At sqrt(s)=10.58 GeV each muon carries
|p| ~ 5.29 GeV; within the Belle-II-like acceptance (|eta|<1.13, i.e. theta
~36-144 deg), pT = p*sin(theta) peaks in the 3-5 GeV range.

Purpose (software): exercises the ROOT file -> PyROOT -> histogram -> PNG
node of the pipeline. This is a software-chain validation plot, NOT a Belle II
physics result.

Usage (run from repo root after sourcing env/setup_lcg105.sh):
    python analysis/validation_mumu/plot_muon_pt.py
"""

import os
import sys

import ROOT  # provided by LCG_105 / source env/setup_lcg105.sh

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kWarning

# ---------------------------------------------------------------------------
# Paths (run from repo root)
# ---------------------------------------------------------------------------
INPUT  = "PROC_validation_mumu/Events/run_01/delphes_mumu.root"
OUTDIR = "plots/validation_mumu"
OUTPUT = os.path.join(OUTDIR, "muon_pt.png")

# No Delphes shared library needed: Muon.PT and Muon_size are plain Float_t /
# Int_t leaves inside TClonesArray branches. TLeaf::GetValue() reads them
# directly from the ROOT file without requiring the Delphes class dictionary.

# ---------------------------------------------------------------------------
# Open input
# ---------------------------------------------------------------------------
if not os.path.isfile(INPUT):
    sys.exit(
        f"ERROR: Delphes output not found: {INPUT}\n"
        "       Run Stage 3 first:  bash mc/delphes_validation_mumu.sh"
    )

f = ROOT.TFile.Open(INPUT)
if not f or f.IsZombie():
    sys.exit(f"ERROR: cannot open ROOT file: {INPUT}")

tree = f.Get("Delphes")
if not tree:
    sys.exit(f"ERROR: no 'Delphes' tree found in {INPUT}")

n_events = tree.GetEntries()

# ---------------------------------------------------------------------------
# Fill histogram
# pT range 0-6 GeV covers the full mu+mu- spectrum at Belle II energy.
# Within |eta|<1.13, reconstructed muons peak in the 3-5 GeV band.
# ---------------------------------------------------------------------------
h = ROOT.TH1F(
    "muon_pt",
    "e^{+}e^{-} #rightarrow #mu^{+}#mu^{-} validation: reconstructed muon p_{T};"
    "Reconstructed muon p_{T} [GeV];"
    "Muons / bin",
    30, 0.0, 6.0,
)
h.SetLineColor(ROOT.kBlue + 1)
h.SetLineWidth(2)
h.SetFillColorAlpha(ROOT.kBlue + 1, 0.15)

leaf_size = tree.GetLeaf("Muon_size")
leaf_pt   = tree.GetLeaf("Muon.PT")
if not leaf_size or not leaf_pt:
    sys.exit("ERROR: expected leaves 'Muon_size' / 'Muon.PT' not found in Delphes tree")

n_muons = 0
sum_pt  = 0.0
for i in range(n_events):
    tree.GetEntry(i)
    n = int(leaf_size.GetValue(0))
    for j in range(n):
        pt = leaf_pt.GetValue(j)
        h.Fill(pt)
        sum_pt += pt
        n_muons += 1

mean_pt = sum_pt / n_muons if n_muons > 0 else 0.0

# ---------------------------------------------------------------------------
# Print summary
# ---------------------------------------------------------------------------
print()
print(f"Delphes events read : {n_events}")
print(f"Reconstructed muons : {n_muons}")
print(f"Mean muon pT        : {mean_pt:.3f} GeV")
print(f"(expect ~3-5 GeV within |eta|<1.13 for e+e- -> mu+mu- at sqrt(s)=10.58 GeV)")
print()

# ---------------------------------------------------------------------------
# Draw and save
# ---------------------------------------------------------------------------
os.makedirs(OUTDIR, exist_ok=True)

ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetFrameLineWidth(1)

c = ROOT.TCanvas("c", "", 800, 600)
c.SetLeftMargin(0.13)
c.SetBottomMargin(0.13)
c.SetTopMargin(0.10)

h.GetXaxis().SetTitleSize(0.05)
h.GetYaxis().SetTitleSize(0.05)
h.GetXaxis().SetTitleOffset(1.1)
h.Draw("HIST")

# Validation watermark — makes clear this is not a Belle II physics result
watermark = ROOT.TLatex()
watermark.SetNDC()
watermark.SetTextSize(0.030)
watermark.SetTextColor(ROOT.kGray + 1)
watermark.DrawLatex(0.14, 0.925, "Software-chain validation only — NOT a Belle II physics result")

# In-plot statistics box
stats = ROOT.TLatex()
stats.SetNDC()
stats.SetTextSize(0.033)
stats.DrawLatex(0.58, 0.82, f"Events: {n_events}")
stats.DrawLatex(0.58, 0.76, f"Muons: {n_muons}")
stats.DrawLatex(0.58, 0.70, f"Mean p_{{T}}: {mean_pt:.2f} GeV")

c.SaveAs(OUTPUT)
print(f"Plot saved: {OUTPUT}")

f.Close()
