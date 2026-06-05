#!/usr/bin/env bash
# ============================================================================
# Stage-3 FCC-ee SM background:  Delphes IDEA detector simulation
# ============================================================================
#
# Purpose (physics): applies the FCC-ee IDEA parametric detector response to
# the showered multi-process HepMC (Stage 2). Output is a flat ROOT tree
# containing reconstructed photons, electrons, muons, jets (anti-kT R=0.5),
# b-tagged jets, and MissingET. This is the final reconstructed sample used
# to assess the SM background composition at the detector level.
# Purpose (software): first Delphes run with the full IDEA card (including
# jets, b-tagging, MissingET) in this repo. Uses card_IDEA_winter2023_sm_bkg.tcl
# which switches GenJetFinder and FastJetFinder from Durham kt (JetAlgorithm 10)
# to anti-kT (JetAlgorithm 6, R=0.5) to avoid SIGSEGV on invisible nu nu~ events.
#
# Usage (run on NIKHEF after review -- not executed automatically):
#   bash mc/delphes_background_sm_fcc.sh
# Optional first arg: max events for a quick smoke test, e.g.:
#   bash mc/delphes_background_sm_fcc.sh 50
# ----------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

NEVENTS="${1:-}"

CARD="mc/delphes_cards/fcc_idea/card_IDEA_winter2023_sm_bkg.tcl"
IN="PROC_background_sm_fcc/Events/run_01/showered_sm_fcc.hepmc"
OUT="PROC_background_sm_fcc/Events/run_01/delphes_sm_fcc.root"
META="PROC_background_sm_fcc/Events/run_01/metadata_sm_fcc.json"

echo ">>> Sourcing environment (env/setup_lcg105.sh)"
set +u
# shellcheck disable=SC1091
source env/setup_lcg105.sh
set -u

if ! command -v DelphesHepMC2 >/dev/null 2>&1; then
  echo "ERROR: DelphesHepMC2 not on PATH after sourcing env/setup_lcg105.sh" >&2
  exit 1
fi

if [[ ! -f "$IN" ]]; then
  echo "ERROR: Stage-2 HepMC not found: $IN" >&2
  echo "       Run 'bash mc/shower_background_sm_fcc.sh' first." >&2
  exit 1
fi

RUNIN="$IN"
if [[ -n "$NEVENTS" ]]; then
  SMALL="PROC_background_sm_fcc/Events/run_01/showered_sm_fcc_small.hepmc"
  echo ">>> Tiny-sample test: first $NEVENTS events -> $SMALL"
  awk -v n="$NEVENTS" '/^E /{e++} e>n{exit} {print}' "$IN" > "$SMALL"
  RUNIN="$SMALL"
fi

if [[ -f "$OUT" ]]; then
  echo ">>> Removing stale output $OUT"
  rm -f "$OUT"
fi

echo ">>> Running Delphes: DelphesHepMC2 $CARD $OUT $RUNIN"
DELPHES_EXIT=0
DelphesHepMC2 "$CARD" "$OUT" "$RUNIN" || DELPHES_EXIT=$?
if [[ ! -f "$OUT" ]]; then
  echo "ERROR: DelphesHepMC2 exited $DELPHES_EXIT and output not found: $OUT" >&2
  exit 1
fi
if [[ "$DELPHES_EXIT" -ne 0 ]]; then
  echo "ERROR: DelphesHepMC2 exited $DELPHES_EXIT" >&2
  exit 1
fi

# Quick sanity check: print branch list and mean object counts per event
echo ">>> ROOT file check"
root -l -b -q <<'ROOTEOF'
  TFile *f = TFile::Open("PROC_background_sm_fcc/Events/run_01/delphes_sm_fcc.root");
  if (!f || f->IsZombie()) { printf("ERROR: cannot open ROOT file\n"); exit(1); }
  TTree *t = (TTree*)f->Get("Delphes");
  if (!t) { printf("ERROR: Delphes tree not found\n"); exit(1); }
  Long64_t n = t->GetEntries();
  printf("\nDelphes tree: %lld events\n", n);
  printf("Branches present:\n");
  TIter next(t->GetListOfBranches());
  TBranch *b;
  while ((b = (TBranch*)next())) printf("  %s\n", b->GetName());
  // Mean object counts per event
  printf("\nMean object counts per event (all %lld events):\n", n);
  double njet=0, nmu=0, nel=0, nph=0, nmet=0, nbjet=0;
  for (Long64_t i=0; i<n; i++) {
    t->GetEntry(i);
    njet += t->GetLeaf("Jet_size") ? t->GetLeaf("Jet_size")->GetValue() : 0;
    nmu  += t->GetLeaf("Muon_size") ? t->GetLeaf("Muon_size")->GetValue() : 0;
    nel  += t->GetLeaf("Electron_size") ? t->GetLeaf("Electron_size")->GetValue() : 0;
    nph  += t->GetLeaf("Photon_size") ? t->GetLeaf("Photon_size")->GetValue() : 0;
  }
  printf("  Jets (anti-kT R=0.5, pT>1 GeV) : %.2f/event\n", njet/n);
  printf("  Muons                           : %.2f/event\n", nmu/n);
  printf("  Electrons                       : %.2f/event\n", nel/n);
  printf("  Photons (isolated)              : %.2f/event\n", nph/n);
  f->Close();
ROOTEOF

echo
echo "Stage-3 FCC-ee SM background status: CLEAN PASS"
echo "  ROOT output  : $OUT"
echo "  Metadata     : $META"
echo
echo "Next: python analysis/background_sm_fcc/summarise_sm_bkg.py"
