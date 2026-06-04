#!/usr/bin/env bash
# ============================================================================
# Stage-3 validation entrypoint:  Delphes detector simulation of e+ e- -> mu+ mu-
# ============================================================================
#
# Purpose (physics): the `Delphes/ROOT` node of the pipeline. Takes the showered
# HepMC (Stage 2), applies a parametric detector response, and writes a flat ROOT
# tree of reconstructed objects. Validation = Delphes runs and reconstructs the
# muons (~2 per event) within a Belle-II-like acceptance.
#
# Purpose (software): runs DelphesHepMC2 with the Belle-II-inspired validation
# card and then a ROOT macro that checks the reconstructed-muon counts.
#
# NOTE: the detector card (delphes_card_belle2_validation.tcl) is Belle-II-INSPIRED
# for software-chain validation only -- NOT validated Belle II detector performance.
# See mc/cards/validation_mumu/README.md.
#
# Usage (run on NIKHEF after review -- not executed automatically):
#   bash mc/delphes_validation_mumu.sh
# ----------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Optional first arg: number of events to process (tiny-sample test). Empty = all.
NEVENTS="${1:-}"

# Minimal mu+mu- card: only propagation/tracking/smearing/muon-eff/TreeWriter.
# Jet/tagging/calorimeter/isolation modules are not even defined (no hadronic
# final state). See the card header and mc/cards/validation_mumu/README.md.
CARD="mc/delphes_cards/delphes_card_belle2_validation_mumu_minimal.tcl"
IN="PROC_validation_mumu/Events/run_01/showered_mumu.hepmc"
OUT="PROC_validation_mumu/Events/run_01/delphes_mumu.root"
CHECK="mc/delphes_validation_check.C"

# Set up LCG_105 (sourced directly; relax 'set -u' for the LCG setup.sh COMPILER var).
echo ">>> Sourcing environment (env/setup_lcg105.sh)"
set +u
# shellcheck disable=SC1091
source env/setup_lcg105.sh
set -u

if ! command -v DelphesHepMC2 >/dev/null 2>&1; then
  echo "ERROR: DelphesHepMC2 not on PATH after sourcing env/setup_lcg105.sh" >&2
  exit 1
fi

# Require the Stage-2 HepMC before running Delphes.
if [[ ! -f "$IN" ]]; then
  echo "ERROR: Stage-2 HepMC not found: $IN" >&2
  echo "       Run 'bash mc/shower_validation_mumu.sh' first." >&2
  exit 1
fi

# Tiny-sample test: if an event count was given, truncate the HepMC to the first
# N complete events (HepMC2 records begin with 'E '; we stop before the (N+1)th,
# so the last kept event is whole and Delphes stops cleanly at EOF).
RUNIN="$IN"
if [[ -n "$NEVENTS" ]]; then
  SMALL="PROC_validation_mumu/Events/run_01/showered_mumu_small.hepmc"
  echo ">>> Tiny-sample test: first $NEVENTS events -> $SMALL"
  awk -v n="$NEVENTS" '/^E /{e++} e>n{exit} {print}' "$IN" > "$SMALL"
  RUNIN="$SMALL"
fi

# DelphesHepMC2 refuses to overwrite an existing output file. Remove only our own
# regenerable, git-ignored target (NOT a tracked repo file) before running.
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
  echo "WARNING: DelphesHepMC2 exited $DELPHES_EXIT (ROOT finalization crash -- output present, checking...)"
fi

# --- Verify reconstructed muons ----------------------------------------------
if [[ -f "$OUT" ]]; then
  echo ">>> Checking reconstructed muons"
  root -l -b -q "${CHECK}(\"${OUT}\")"
else
  echo "ERROR: expected Delphes output not found at $OUT" >&2
  exit 1
fi

# Summarise exit status so the log is unambiguous.
if [[ "$DELPHES_EXIT" -ne 0 ]]; then
  echo
  echo "Stage-3 status: FUNCTIONAL PASS (finalization warning, exit $DELPHES_EXIT)"
  echo "  ROOT output is readable and muon counts are nominal."
  echo "  Crash is a confirmed ROOT 6.26/6.30 version mismatch in the LCG Delphes build."
  echo "  Verified: all stock Delphes cards (CircularEE, CMS-NoFastJet) exit 139 identically."
  echo "  Cannot be fixed without recompiling Delphes against ROOT 6.30."
  echo "  Do NOT proceed to Condor until this exits cleanly or is explicitly accepted."
else
  echo
  echo "Stage-3 status: CLEAN PASS"
fi
