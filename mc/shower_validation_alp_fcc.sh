#!/usr/bin/env bash
# ============================================================================
# Stage-2 FCC-ee ALP validation:  Pythia8 shower of e+ e- -> gamma alp (alp -> gamma gamma)
# ============================================================================
#
# Purpose (physics): applies ISR off the initial-state e+e- beams to the
# Stage-1 LHE. The ALP decay (alp -> gamma gamma) is already included in the
# MG5 matrix element via cascade syntax -- Pythia8 does NOT re-decay the ALP.
# Final state after showering: three photons + ISR photons.
# Purpose (software): reuses the compiled shower_lhe binary from the Belle II /
# FCC-ee mumu validations -- no recompilation needed; only the .cmnd path changes.
#
# Usage (run on NIKHEF after review -- not executed automatically):
#   bash mc/shower_validation_alp_fcc.sh
# ----------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

CMND="mc/cards/validation_alp_fcc/pythia8_alp_fcc.cmnd"
LHE="PROC_validation_alp_fcc/Events/run_01/unweighted_events.lhe.gz"
OUT="PROC_validation_alp_fcc/Events/run_01/showered_alp_fcc.hepmc"
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
  echo "       Run 'bash mc/gen_validation_alp_fcc.sh' first." >&2
  exit 1
fi

echo ">>> Showering: $EXE $CMND $OUT"
"$EXE" "$CMND" "$OUT"

echo
echo "==================== Stage-2 FCC-ee ALP validation summary ===================="
if [[ -f "$OUT" ]]; then
  NEVT=$(grep -c '^E ' "$OUT" || true)
  # Count final-state photons (pid=22, status=1)
  NPHOTON=$(awk '$1=="P" && $3==22 && $9==1 {n++} END{print n+0}' "$OUT")
  echo "HepMC2 output : $OUT"
  echo "Events written: $NEVT"
  echo "Final-state photons (pid 22, status 1): $NPHOTON"
  echo "Mean photons/event: $(awk "BEGIN{printf \"%.1f\", $NPHOTON/$NEVT}")"
  echo "(expect ~3 photons/event: 1 prompt + 2 from alp->gamma gamma)"
  echo
  echo "Next: feed this HepMC into Delphes with the IDEA minimal card (Stage 3)."
else
  echo "ERROR: expected HepMC output not found at $OUT" >&2
  exit 1
fi
echo "=============================================================================="
