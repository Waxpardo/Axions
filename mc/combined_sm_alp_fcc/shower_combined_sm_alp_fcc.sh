#!/usr/bin/env bash
# ============================================================================
# Stage-2 COMBINED FCC-ee SM+ALP:  Pythia8 parton shower + hadronization
# ============================================================================
#
# Showers the combined Stage-1 LHE into a HepMC2 file for Delphes. Reuses the
# standalone mc/pythia/shower_lhe driver. The Pythia card's LHEF path (token
# __LHE_PATH__) is injected at runtime so one card serves both variants.
#
# Usage (run on NIKHEF after review -- not executed automatically):
#   bash mc/combined_sm_alp_fcc/shower_combined_sm_alp_fcc.sh [honest|boosted]
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

CMND_TEMPLATE="mc/cards/combined_sm_alp_fcc/pythia8_combined_sm_alp_fcc.cmnd"
LHE="${PROC_DIR}/Events/run_01/unweighted_events.lhe.gz"
OUT="${PROC_DIR}/Events/run_01/showered_combined_sm_alp_fcc.hepmc"
EXE="mc/pythia/shower_lhe"

echo ">>> Variant : $VARIANT"
echo ">>> Sourcing environment (env/setup_lcg105.sh)"
set +u
# shellcheck disable=SC1091
source env/setup_lcg105.sh
set -u

if ! command -v pythia8-config >/dev/null 2>&1; then
  echo "ERROR: pythia8-config not on PATH after sourcing env/setup_lcg105.sh" >&2
  exit 1
fi

if [[ ! -f "$LHE" ]]; then
  echo "ERROR: Stage-1 LHE not found: $LHE" >&2
  echo "       Run 'bash mc/combined_sm_alp_fcc/gen_combined_sm_alp_fcc.sh $VARIANT' first." >&2
  exit 1
fi

VIEW="$(cd "$(dirname "$(command -v root)")/.." && pwd)"
echo ">>> LCG view: $VIEW"

echo ">>> Building $EXE (idempotent)"
make -C mc/pythia HEPMC_PREFIX="$VIEW"

# Inject the variant's LHE path into the Pythia card (token __LHE_PATH__).
TMPCMND=$(mktemp /tmp/pythia8_combined_XXXXXX.cmnd)
trap 'rm -f "$TMPCMND"' EXIT
sed "s|__LHE_PATH__|${LHE}|g" "$CMND_TEMPLATE" > "$TMPCMND"

echo ">>> Showering: $EXE $TMPCMND $OUT"
"$EXE" "$TMPCMND" "$OUT"

echo
echo "================ Stage-2 COMBINED SM+ALP summary ($VARIANT) ================"
if [[ ! -f "$OUT" ]]; then
  echo "ERROR: expected HepMC output not found at $OUT" >&2
  exit 1
fi
NEVT=$(grep -c '^E ' "$OUT" || true)
if [[ "${NEVT:-0}" -eq 0 ]]; then
  echo "ERROR: HepMC written but contains 0 events ($OUT)." >&2
  echo "       Check Beams:LHEF resolved correctly and Main:numberOfSubruns>=1" >&2
  echo "       in the Pythia card." >&2
  exit 1
fi
NPHOT=$(awk '$1=="P" && $3==22 && $9==1 {n++} END{print n+0}' "$OUT")
echo "HepMC2 output    : $OUT"
echo "Events written   : $NEVT"
echo "Stable photons   : $NPHOT"
echo
echo "Next: bash mc/combined_sm_alp_fcc/delphes_combined_sm_alp_fcc.sh $VARIANT"
echo "============================================================================"
