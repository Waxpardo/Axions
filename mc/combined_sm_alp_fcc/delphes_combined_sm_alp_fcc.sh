#!/usr/bin/env bash
# ============================================================================
# Stage-3 COMBINED FCC-ee SM+ALP:  Delphes IDEA detector simulation
# ============================================================================
#
# Applies the FCC-ee IDEA parametric detector response to the combined showered
# HepMC (Stage 2). Reuses card_IDEA_winter2023_sm_bkg.tcl (anti-kT R=0.5, which
# is safe on the invisible nu nu~ events present in the SM mixture). Output is a
# flat ROOT tree (photons, electrons, muons, jets, b-jets, MissingET) -- the
# reconstructed sample for the combined-pipeline validation.
#
# Usage (run on NIKHEF after review -- not executed automatically):
#   bash mc/combined_sm_alp_fcc/delphes_combined_sm_alp_fcc.sh [honest|boosted] [maxevents]
# ----------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

VARIANT="${1:-honest}"
case "$VARIANT" in
  honest)  PROC_DIR="PROC_combined_sm_alp_fcc" ;;
  boosted) PROC_DIR="PROC_combined_sm_alp_fcc_boosted" ;;
  *) echo "ERROR: unknown variant '$VARIANT' (use 'honest' or 'boosted')" >&2; exit 1 ;;
esac
NEVENTS="${2:-}"

CARD="mc/delphes_cards/fcc_idea/card_IDEA_winter2023_sm_bkg.tcl"
IN="${PROC_DIR}/Events/run_01/showered_combined_sm_alp_fcc.hepmc"
OUT="${PROC_DIR}/Events/run_01/delphes_combined_sm_alp_fcc.root"

echo ">>> Variant : $VARIANT"
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
  echo "       Run 'bash mc/combined_sm_alp_fcc/shower_combined_sm_alp_fcc.sh $VARIANT' first." >&2
  exit 1
fi

RUNIN="$IN"
if [[ -n "$NEVENTS" ]]; then
  SMALL="${PROC_DIR}/Events/run_01/showered_combined_sm_alp_fcc_small.hepmc"
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

echo ">>> ROOT file check"
root -l -b -q <<ROOTEOF
  TFile *f = TFile::Open("${OUT}");
  if (!f || f->IsZombie()) { printf("ERROR: cannot open ROOT file\n"); gSystem->Exit(1); }
  TTree *t = (TTree*)f->Get("Delphes");
  if (!t) { printf("ERROR: Delphes tree not found\n"); gSystem->Exit(1); }
  Long64_t n = t->GetEntries();
  printf("\nDelphes tree: %lld events\n", n);
  if (n==0) { printf("ERROR: Delphes tree has 0 events (empty input HepMC?)\n"); gSystem->Exit(2); }
  double njet=0, nph=0;
  for (Long64_t i=0; i<n; i++) {
    t->GetEntry(i);
    njet += t->GetLeaf("Jet_size")    ? t->GetLeaf("Jet_size")->GetValue()    : 0;
    nph  += t->GetLeaf("Photon_size") ? t->GetLeaf("Photon_size")->GetValue() : 0;
  }
  printf("  Jets    : %.2f/event\n", njet/n);
  printf("  Photons : %.2f/event\n", nph/n);
  f->Close();
ROOTEOF

echo
echo "================ Stage-3 COMBINED SM+ALP status ($VARIANT): CLEAN PASS ======"
echo "  ROOT output : $OUT"
echo
echo "Next: bash analysis/combined_sm_alp_fcc/run_summary.sh $VARIANT"
echo "============================================================================"
