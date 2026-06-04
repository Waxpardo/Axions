#!/usr/bin/env bash
# ============================================================================
# Stage-2 validation entrypoint:  Pythia8 parton shower of e+ e- -> mu+ mu-
# ============================================================================
#
# Purpose (physics): applies the QED parton shower (FSR off the muons, ISR off
# the beams) to the Stage-1 parton-level LHE and writes HepMC -- the `Pythia/HepMC`
# node of the MadGraph -> Pythia -> Delphes -> ROOT pipeline.
#
# Purpose (software): builds the standalone Pythia8 driver (no MG5-Pythia
# interface exists in this LCG build; see mc/cards/validation_mumu/README.md)
# and runs it on the Stage-1 LHE. Compiles once; the binary then runs anywhere,
# including Condor workers, with no network.
#
# Usage (run on NIKHEF after review -- not executed automatically):
#   bash mc/shower_validation_mumu.sh
# ----------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

CMND="mc/cards/validation_mumu/pythia8_mumu.cmnd"
LHE="PROC_validation_mumu/Events/run_01/unweighted_events.lhe.gz"
OUT="PROC_validation_mumu/Events/run_01/showered_mumu.hepmc"
EXE="mc/pythia/shower_lhe"

# Set up LCG_105 (sourced directly; relax 'set -u' -- LCG setup.sh reads an
# unbound COMPILER variable that would otherwise abort this script).
echo ">>> Sourcing environment (env/setup_lcg105.sh)"
set +u
# shellcheck disable=SC1091
source env/setup_lcg105.sh
set -u

if ! command -v pythia8-config >/dev/null 2>&1; then
  echo "ERROR: pythia8-config not on PATH after sourcing env/setup_lcg105.sh" >&2
  exit 1
fi

# Derive the LCG view prefix (root lives in <view>/bin) -> HepMC2 include/lib.
VIEW="$(cd "$(dirname "$(command -v root)")/.." && pwd)"
echo ">>> LCG view: $VIEW"

# Build the shower driver (idempotent; recompiles only if the source changed).
echo ">>> Building $EXE"
make -C mc/pythia HEPMC_PREFIX="$VIEW"

# Require the Stage-1 output before showering.
if [[ ! -f "$LHE" ]]; then
  echo "ERROR: Stage-1 LHE not found: $LHE" >&2
  echo "       Run 'bash mc/gen_validation_mumu.sh' first." >&2
  exit 1
fi

echo ">>> Showering: $EXE $CMND $OUT"
"$EXE" "$CMND" "$OUT"

# --- Report -------------------------------------------------------------------
echo
echo "==================== Stage-2 validation summary ===================="
if [[ -f "$OUT" ]]; then
  # HepMC2 ASCII layout: event records begin with 'E '; particle records begin
  # with 'P ' as:  P barcode pdg_id px py pz e m status ...
  # -> PDG id is column 3, status is column 9 (status==1 = final-state).
  NEVT=$(grep -c '^E ' "$OUT" || true)
  NMU=$(awk '$1=="P" && ($3==13 || $3==-13) && $9==1 {n++} END{print n+0}' "$OUT")
  echo "HepMC2 output : $OUT"
  echo "Events written: $NEVT"
  echo "Final-state muons (pid +-13, status 1): $NMU  (expect ~2 per event)"
  echo
  echo "Next: feed this HepMC into Delphes (Stage 3) once the counts look sane."
else
  echo "ERROR: expected HepMC output not found at $OUT" >&2
  exit 1
fi
echo "===================================================================="
