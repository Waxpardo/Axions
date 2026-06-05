#!/usr/bin/env bash
# ============================================================================
# Stage-3 FCC-ee ALP validation:  Delphes IDEA detector simulation
# ============================================================================
#
# Purpose (physics): applies the FCC-ee IDEA parametric detector response to
# the showered 3-photon HepMC (Stage 2). Validation = Delphes runs and
# reconstructs photons with plausible multiplicity (~3/event).
# Purpose (software): reuses the IDEA minimal card from the FCC-ee mumu
# validation (jet finders already removed to avoid FastJetFinder segfault).
# For the 3-photon ALP final state, only the ECAL/photon modules are needed;
# the minimal card is appropriate.
#
# Fix: DelphesHepMC2 is built locally against ROOT 6.30 (mc/delphes/build_delphes.sh)
# to match the LCG_105 runtime. A clean exit 0 is expected.
#
# Usage (run on NIKHEF after review -- not executed automatically):
#   bash mc/delphes_validation_alp_fcc.sh
# Optional first arg: max events for a tiny-sample test, e.g.:
#   bash mc/delphes_validation_alp_fcc.sh 100
# ----------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

NEVENTS="${1:-}"

# Reuse the mumu minimal IDEA card -- jet finders removed, photon modules kept.
CARD="mc/delphes_cards/fcc_idea/card_IDEA_winter2023_mumu_minimal.tcl"
IN="PROC_validation_alp_fcc/Events/run_01/showered_alp_fcc.hepmc"
OUT="PROC_validation_alp_fcc/Events/run_01/delphes_alp_fcc.root"
CHECK="mc/delphes_alp_photon_check.C"

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
  echo "       Run 'bash mc/shower_validation_alp_fcc.sh' first." >&2
  exit 1
fi

RUNIN="$IN"
if [[ -n "$NEVENTS" ]]; then
  SMALL="PROC_validation_alp_fcc/Events/run_01/showered_alp_fcc_small.hepmc"
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

echo ">>> Checking reconstructed photons"
root -l -b -q "${CHECK}(\"${OUT}\")"

echo
echo "Stage-3 FCC-ee ALP status: CLEAN PASS"
