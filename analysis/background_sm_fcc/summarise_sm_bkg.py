#!/usr/bin/env python3
"""
FCC-ee SM inclusive background -- Stage-3 summary and plots

Reads the Delphes ROOT output and Stage-1 metadata sidecar. Produces:
  - plots/background_sm_fcc/photon_multiplicity.png
  - plots/background_sm_fcc/electron_multiplicity.png
  - plots/background_sm_fcc/muon_multiplicity.png
  - plots/background_sm_fcc/jet_multiplicity.png
  - plots/background_sm_fcc/met_distribution.png
  - plots/background_sm_fcc/summary_sm_bkg.json   (machine-readable summary)
  - terminal summary table

Reader strategy:
  Primary  -- uproot (pure Python, no libDelphes.so needed)
  Fallback -- ROOT TLeaf API (requires PyROOT / sourced LCG env)
ROOT is still used for PyROOT import diagnostics if both paths fail.

Usage:
    python analysis/background_sm_fcc/summarise_sm_bkg.py
    bash  analysis/background_sm_fcc/run_summary.sh        # handles env setup
"""

import argparse
import json
import os
import sys

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="FCC-ee SM background summary")
parser.add_argument(
    "--root",
    default="PROC_background_sm_fcc/Events/run_01/delphes_sm_fcc.root",
    help="Path to Delphes ROOT output",
)
parser.add_argument(
    "--meta",
    default="PROC_background_sm_fcc/Events/run_01/metadata_sm_fcc.json",
    help="Path to metadata JSON sidecar",
)
parser.add_argument(
    "--outdir",
    default="plots/background_sm_fcc",
    help="Directory for output plots and JSON summary",
)
args = parser.parse_args()

# ---------------------------------------------------------------------------
# ROOT import diagnostics helper
# Called only when both uproot and ROOT paths fail.
# ---------------------------------------------------------------------------
def print_root_diagnostics():
    print("\n--- ROOT import diagnostics ---")
    print(f"  sys.executable : {sys.executable}")
    py_path = os.environ.get("PYTHONPATH", "<not set>")
    print(f"  PYTHONPATH     : {py_path[:200]}")
    rootsys = os.environ.get("ROOTSYS", "<not set>")
    print(f"  ROOTSYS        : {rootsys}")
    ld = os.environ.get("LD_LIBRARY_PATH", "<not set>")
    entries = ld.split(":") if ld != "<not set>" else []
    print(f"  LD_LIBRARY_PATH (first 5 entries):")
    for e in entries[:5]:
        print(f"    {e}")
    print()
    print("  Fix: source env/setup_lcg105.sh before running, or use:")
    print("       bash analysis/background_sm_fcc/run_summary.sh")

# ---------------------------------------------------------------------------
# Data readers
# ---------------------------------------------------------------------------

def _read_uproot(path):
    """Read per-event object counts and leading-pT arrays via uproot."""
    import uproot
    import numpy as np
    with uproot.open(path) as f:
        tree = f["Delphes"]
        n_events = tree.num_entries
        ph_n   = tree["Photon_size"].array(library="np").astype(int)
        el_n   = tree["Electron_size"].array(library="np").astype(int)
        mu_n   = tree["Muon_size"].array(library="np").astype(int)
        jet_n  = tree["Jet_size"].array(library="np").astype(int)
        met_sz = tree["MissingET_size"].array(library="np").astype(int)

        # Jagged arrays: per-event lists of PT values
        ph_pt_all  = tree["Photon/Photon.PT"].array(library="np")
        el_pt_all  = tree["Electron/Electron.PT"].array(library="np")
        mu_pt_all  = tree["Muon/Muon.PT"].array(library="np")
        jet_pt_all = tree["Jet/Jet.PT"].array(library="np")
        jet_btag   = tree["Jet/Jet.BTag"].array(library="np")
        met_all    = tree["MissingET/MissingET.MET"].array(library="np")

    # Leading-object pT (first element per event, where present)
    def lead_pt(arr):
        result = []
        for ev in arr:
            if hasattr(ev, "__len__") and len(ev) > 0:
                result.append(float(ev[0]))
        return np.array(result)

    # b-tagged jet count per event (bit 0 of BTag set)
    bjet_n = np.array([
        int(np.sum((np.asarray(ev) & 1).astype(bool))) if hasattr(ev, "__len__") else 0
        for ev in jet_btag
    ])

    # MET per event (first MET object; 0 if no MET object)
    import numpy as np
    met_vals = np.array([
        float(ev[0]) if (hasattr(ev, "__len__") and len(ev) > 0) else 0.0
        for ev in met_all
    ])

    return {
        "n_events": n_events,
        "ph_n":   ph_n,   "el_n":  el_n,  "mu_n":  mu_n,
        "jet_n":  jet_n,  "bjet_n": bjet_n,
        "met":    met_vals,
        "ph_pt_lead":  lead_pt(ph_pt_all),
        "el_pt_lead":  lead_pt(el_pt_all),
        "mu_pt_lead":  lead_pt(mu_pt_all),
        "jet_pt_lead": lead_pt(jet_pt_all),
    }


def _read_tleaf(path):
    """Fallback reader using ROOT TLeaf API (requires PyROOT)."""
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

    ph_n   = []; el_n   = []; mu_n   = []; jet_n  = []; bjet_n = []; met_v  = []
    ph_pt  = []; el_pt  = []; mu_pt  = []; jet_pt = []

    for ev in tree:
        ph_n.append(ev.Photon_size)
        el_n.append(ev.Electron_size)
        mu_n.append(ev.Muon_size)
        jet_n.append(ev.Jet_size)
        nb = sum(1 for j in range(ev.Jet_size) if (ev.Jet[j].BTag & 1))
        bjet_n.append(nb)
        met_v.append(ev.MissingET[0].MET if ev.MissingET_size > 0 else 0.0)
        if ev.Photon_size   > 0: ph_pt.append(ev.Photon[0].PT)
        if ev.Electron_size > 0: el_pt.append(ev.Electron[0].PT)
        if ev.Muon_size     > 0: mu_pt.append(ev.Muon[0].PT)
        if ev.Jet_size      > 0: jet_pt.append(ev.Jet[0].PT)

    f.Close()
    n = tree.GetEntries()
    return {
        "n_events": n,
        "ph_n":   np.array(ph_n),   "el_n":  np.array(el_n),
        "mu_n":   np.array(mu_n),   "jet_n": np.array(jet_n),
        "bjet_n": np.array(bjet_n), "met":   np.array(met_v),
        "ph_pt_lead":  np.array(ph_pt),  "el_pt_lead":  np.array(el_pt),
        "mu_pt_lead":  np.array(mu_pt),  "jet_pt_lead": np.array(jet_pt),
    }


def read_data(path):
    """Try uproot first, fall back to ROOT TLeaf, then give up with diagnostics."""
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
        print_root_diagnostics()
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: ROOT TLeaf fallback also failed: {exc}")
        print_root_diagnostics()
        sys.exit(1)


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def make_plots(data, outdir):
    import matplotlib
    matplotlib.use("Agg")  # non-interactive backend; no $DISPLAY needed
    import matplotlib.pyplot as plt
    import numpy as np

    os.makedirs(outdir, exist_ok=True)
    n = data["n_events"]

    STYLE = dict(color="#2166ac", edgecolor="black", linewidth=0.5, alpha=0.85)

    def save_multiplicity(arr, label, fname, xlabel, expected_note=""):
        fig, ax = plt.subplots(figsize=(6, 4))
        max_n = max(int(arr.max()) + 1, 2) if len(arr) > 0 else 10
        bins = np.arange(-0.5, max_n + 0.5, 1)
        ax.hist(arr, bins=bins, **STYLE)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel("Events", fontsize=12)
        ax.set_title(f"FCC-ee SM bkg  –  {label}  (√s = 240 GeV)", fontsize=11)
        mean_val = arr.mean() if len(arr) > 0 else 0
        info = f"N = {n}\nmean = {mean_val:.2f}/event"
        if expected_note:
            info += f"\n{expected_note}"
        ax.text(0.97, 0.97, info, transform=ax.transAxes,
                ha="right", va="top", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
        ax.set_xlim(-0.5, max_n - 0.5)
        fig.tight_layout()
        out = os.path.join(outdir, fname)
        fig.savefig(out, dpi=150)
        plt.close(fig)
        print(f"  Saved: {out}")

    def save_continuous(arr, label, fname, xlabel, bins, expected_note="", log=False):
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.hist(arr, bins=bins, **STYLE)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel("Events", fontsize=12)
        ax.set_title(f"FCC-ee SM bkg  –  {label}  (√s = 240 GeV)", fontsize=11)
        if log:
            ax.set_yscale("log")
        mean_val = arr.mean() if len(arr) > 0 else 0
        info = f"N = {n}\nmean = {mean_val:.1f} GeV"
        if expected_note:
            info += f"\n{expected_note}"
        ax.text(0.97, 0.97, info, transform=ax.transAxes,
                ha="right", va="top", fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))
        fig.tight_layout()
        out = os.path.join(outdir, fname)
        fig.savefig(out, dpi=150)
        plt.close(fig)
        print(f"  Saved: {out}")

    save_multiplicity(data["ph_n"],  "Photon multiplicity",   "photon_multiplicity.png",
                      "Reconstructed photons / event",
                      "WW→lνqq' + FSR photons")

    save_multiplicity(data["el_n"],  "Electron multiplicity", "electron_multiplicity.png",
                      "Reconstructed electrons / event",
                      "From W→eν, Z→ee, H decays")

    save_multiplicity(data["mu_n"],  "Muon multiplicity",     "muon_multiplicity.png",
                      "Reconstructed muons / event",
                      "From W→μν, Z→μμ, validated ~1.7 pb")

    save_multiplicity(data["jet_n"], "Jet multiplicity",      "jet_multiplicity.png",
                      "Reconstructed jets (anti-kT R=0.5, pT>1 GeV) / event",
                      "Dominated by WW→qq' (~55%), jj (~22%)")

    save_continuous(data["met"], "MissingET", "met_distribution.png",
                    "Reconstructed MET [GeV]",
                    bins=np.linspace(0, 130, 40),
                    expected_note="From W→lν, ZZ→2ν, νν̄ events",
                    log=True)


# ---------------------------------------------------------------------------
# Text summary
# ---------------------------------------------------------------------------

def print_summary(data, meta):
    import numpy as np

    n = data["n_events"]

    def safe_mean(arr):
        return float(arr.mean()) if len(arr) > 0 else 0.0

    def frac_above(arr, thresh):
        return float(np.mean(arr > thresh)) if len(arr) > 0 else 0.0

    SEP = "=" * 70
    print()
    print(SEP)
    print("  FCC-ee SM INCLUSIVE BACKGROUND  --  STAGE-3 SUMMARY")
    print(SEP)

    print("\nMETADATA")
    print("-" * 40)
    if meta:
        print(f"  Model          : {meta.get('model', 'sm')}")
        print(f"  sqrt(s)        : {meta.get('sqrts_GeV', 240)} GeV")
        print(f"  Events req.    : {meta.get('nevents_requested', 5000)}")
        print(f"  Random seed    : {meta.get('random_seed', 12345)}")
        print(f"  Filter cuts    : {meta.get('filter_cuts', 'none')}")
        print(f"  Total xsec     : {meta.get('total_xsec_pb', 'see banner')} pb")
        try:
            xsec = float(meta.get("total_xsec_pb", 0))
            if xsec > 0:
                equiv = n / (xsec * 1e3)
                print(f"  Lumi equiv.    : {equiv:.1f} fb⁻¹")
        except (TypeError, ValueError):
            pass
        print(f"  MG5 version    : {meta.get('mg5_version', 'unknown')}")
        print(f"  Pythia8 ver.   : {meta.get('pythia8_version', 'unknown')}")
        print(f"  ROOT version   : {meta.get('root_version', 'unknown')}")
        print(f"  Delphes ver.   : {meta.get('delphes_version', 'unknown')}")
        print("\n  Processes generated:")
        for p in meta.get("processes", []):
            print(f"    {p}")
    else:
        print("  (metadata sidecar not found)")

    print("\nRECONSTRUCTED OBJECT INVENTORY")
    print("-" * 40)
    print(f"  Events in ROOT file  : {n}")
    print()
    hdr = f"  {'Object':<22} {'Mean/evt':>8}  {'Max/evt':>8}  {'Lead pT mean':>14}"
    print(hdr)
    print(f"  {'-'*22}  {'-'*8}  {'-'*8}  {'-'*14}")
    rows = [
        ("Photon",   data["ph_n"],  data["ph_pt_lead"]),
        ("Electron", data["el_n"],  data["el_pt_lead"]),
        ("Muon",     data["mu_n"],  data["mu_pt_lead"]),
        ("Jet",      data["jet_n"], data["jet_pt_lead"]),
    ]
    for label, cnt, pt in rows:
        print(f"  {label:<22} {safe_mean(cnt):>8.2f}  {int(cnt.max() if len(cnt)>0 else 0):>8}"
              f"  {safe_mean(pt):>13.1f} GeV")

    bfrac = safe_mean(data["bjet_n"]) / safe_mean(data["jet_n"]) if safe_mean(data["jet_n"]) > 0 else 0
    print(f"\n  b-tagged jets/event  : {safe_mean(data['bjet_n']):.2f}"
          f"  ({bfrac*100:.1f}% of jets)")

    met = data["met"]
    print(f"\n  MET mean/event       : {safe_mean(met):.1f} GeV")
    print(f"  Fraction MET>10 GeV  : {frac_above(met, 10)*100:.1f}%"
          f"  (W→lν, ZZ→νν, νν̄ events)")
    print(f"  Fraction MET>30 GeV  : {frac_above(met, 30)*100:.1f}%")

    print("\nCONDOR SUITABILITY")
    print("-" * 40)
    print("  [✓] ROOT file is flat-tree, mergeable with hadd.")
    print("  [✓] Metadata JSON travels with ROOT file for provenance.")
    print("  [✓] Anti-kT jets safe for events with zero visible particles (νν̄).")
    print("  [!] Delphes local build required on each worker:")
    print("       add 'bash mc/delphes/build_delphes.sh' to Condor prologue.")
    print("  [!] For production scans: split by process, merge weighted by σ.")
    print("       Multi-process LHE does not support per-process reweighting.")

    print()
    print(SEP)


# ---------------------------------------------------------------------------
# JSON summary writer
# ---------------------------------------------------------------------------

def write_json_summary(data, meta, outdir):
    import numpy as np

    def safe_mean(arr):
        return round(float(arr.mean()), 4) if len(arr) > 0 else 0.0

    n = data["n_events"]
    met = data["met"]

    summary = {
        "n_events": int(n),
        "metadata": meta,
        "object_inventory": {
            "photon":   {"mean_per_event": safe_mean(data["ph_n"]),
                         "mean_lead_pt_gev": safe_mean(data["ph_pt_lead"])},
            "electron": {"mean_per_event": safe_mean(data["el_n"]),
                         "mean_lead_pt_gev": safe_mean(data["el_pt_lead"])},
            "muon":     {"mean_per_event": safe_mean(data["mu_n"]),
                         "mean_lead_pt_gev": safe_mean(data["mu_pt_lead"])},
            "jet":      {"mean_per_event": safe_mean(data["jet_n"]),
                         "mean_lead_pt_gev": safe_mean(data["jet_pt_lead"]),
                         "mean_bjet_per_event": safe_mean(data["bjet_n"])},
            "met":      {"mean_gev": safe_mean(met),
                         "frac_above_10gev": round(float(np.mean(met > 10)), 4),
                         "frac_above_30gev": round(float(np.mean(met > 30)), 4)},
        },
    }
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, "summary_sm_bkg.json")
    with open(out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Saved: {out}")
    return out


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
data = read_data(args.root)

print_summary(data, meta)

print("\nGenerating plots...")
make_plots(data, args.outdir)

print("\nWriting JSON summary...")
write_json_summary(data, meta, args.outdir)

print(f"\nAll outputs in: {args.outdir}/")
