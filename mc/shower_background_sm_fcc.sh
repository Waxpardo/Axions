#!/usr/bin/env bash
# ============================================================================
# Stage-2 FCC-ee SM background:  Pythia8 parton shower + hadronization
# ============================================================================
#
# Purpose (physics): applies the full Pythia8 treatment to the multi-process
# LHE from Stage 1 -- parton shower (ISR off beams, FSR off final-state
# charged particles), hadronization (qq~ -> hadrons, W/Z/H decays), and
# tau decays. The output HepMC2 file contains stable final-state particles
# ready for Delphes detector simulation.
# Purpose (software): reuses the same standalone mc/pythia/shower_lhe
# driver as the mumu and ALP validations; only the .cmnd path changes.
# Hadronization is on by default in Pythia8; it is made explicit in the
# cmnd to document the difference from the mumu/ALP cards.
#
# Usage (run on NIKHEF after review -- not executed automatically):
#   bash mc/shower_background_sm_fcc.sh
# ----------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

CMND="mc/cards/background_sm_fcc/pythia8_sm_fcc.cmnd"
LHE="PROC_background_sm_fcc/Events/run_01/unweighted_events.lhe.gz"
OUT="PROC_background_sm_fcc/Events/run_01/showered_sm_fcc.hepmc"
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
  echo "       Run 'bash mc/gen_background_sm_fcc.sh' first." >&2
  exit 1
fi

echo ">>> Showering: $EXE $CMND $OUT"
"$EXE" "$CMND" "$OUT"

echo
echo "==================== Stage-2 FCC-ee SM background summary ===================="
if [[ -f "$OUT" ]]; then
  NEVT=$(grep -c '^E ' "$OUT" || true)
  # Quick object-type tally from stable particles (status 1) in the HepMC
  NPHOT=$(awk '$1=="P" && $3==22  && $9==1 {n++} END{print n+0}' "$OUT")
  NMUON=$(awk '$1=="P" && (($3==13 || $3==-13)) && $9==1 {n++} END{print n+0}' "$OUT")
  NELEC=$(awk '$1=="P" && (($3==11 || $3==-11)) && $9==1 {n++} END{print n+0}' "$OUT")
  echo "HepMC2 output      : $OUT"
  echo "Events written     : $NEVT"
  echo "Stable photons     : $NPHOT  (~0.5/event from FSR)"
  echo "Stable muons       : $NMUON  (~0.6/event from mu+mu-, WW->lnu, Z->ll)"
  echo "Stable electrons   : $NELEC  (~0.6/event from WW->lnu, Z->ll)"
  echo
  echo "Next: bash mc/delphes_background_sm_fcc.sh"
else
  echo "ERROR: expected HepMC output not found at $OUT" >&2
  exit 1
fi
echo "=============================================================================="
