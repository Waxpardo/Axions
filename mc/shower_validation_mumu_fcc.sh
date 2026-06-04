#!/usr/bin/env bash
# ============================================================================
# Stage-2 FCC-ee validation:  Pythia8 parton shower of e+ e- -> mu+ mu-
# ============================================================================
#
# Purpose (physics): applies the QED parton shower (FSR off the muons, ISR off
# the beams) to the Stage-1 parton-level LHE and writes HepMC2 for Delphes.
# At sqrt(s)=240 GeV the muons carry ~120 GeV each; ISR reduces this by O(alpha/pi).
# Purpose (software): runs the same standalone Pythia8 driver (mc/pythia/shower_lhe)
# built for the Belle II validation -- no recompilation needed; only the .cmnd
# path changes.
#
# Usage (run on NIKHEF after review -- not executed automatically):
#   bash mc/shower_validation_mumu_fcc.sh
# ----------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

CMND="mc/cards/validation_mumu_fcc/pythia8_mumu_fcc.cmnd"
LHE="PROC_validation_mumu_fcc/Events/run_01/unweighted_events.lhe.gz"
OUT="PROC_validation_mumu_fcc/Events/run_01/showered_mumu_fcc.hepmc"
EXE="mc/pythia/shower_lhe"

echo ">>> Sourcing environment (env/setup_lcg105.sh)"
set +u
# shellcheck disable=SC1091
source env/setup_lcg105.sh
set -u

if ! command -v pythia8-config >/dev/null 2>&1; then
  echo "ERROR: pythia8-config not on PATH after sourcing env/setup_lcg105.sh" >&2
  exit 1
fi

VIEW="$(cd "$(dirname "$(command -v root)")/.." && pwd)"
echo ">>> LCG view: $VIEW"

echo ">>> Building $EXE (idempotent)"
make -C mc/pythia HEPMC_PREFIX="$VIEW"

if [[ ! -f "$LHE" ]]; then
  echo "ERROR: Stage-1 LHE not found: $LHE" >&2
  echo "       Run 'bash mc/gen_validation_mumu_fcc.sh' first." >&2
  exit 1
fi

echo ">>> Showering: $EXE $CMND $OUT"
"$EXE" "$CMND" "$OUT"

echo
echo "==================== Stage-2 FCC-ee validation summary ===================="
if [[ -f "$OUT" ]]; then
  NEVT=$(grep -c '^E ' "$OUT" || true)
  NMU=$(awk '$1=="P" && ($3==13 || $3==-13) && $9==1 {n++} END{print n+0}' "$OUT")
  echo "HepMC2 output : $OUT"
  echo "Events written: $NEVT"
  echo "Final-state muons (pid +-13, status 1): $NMU  (expect ~2 per event)"
  echo
  echo "Next: feed this HepMC into Delphes with the IDEA card (Stage 3)."
else
  echo "ERROR: expected HepMC output not found at $OUT" >&2
  exit 1
fi
echo "==========================================================================="
