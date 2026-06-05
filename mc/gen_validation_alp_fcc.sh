#!/usr/bin/env bash
# ============================================================================
# Stage-1 FCC-ee ALP validation:  MadGraph e+ e- -> gamma alp, alp -> gamma gamma
# ============================================================================
#
# Purpose (physics): generates parton-level + decay events for the photophilic
# ALP benchmark at FCC-ee energy. Benchmark point:
#   m_a   = 10 GeV          ALP mass
#   fa    = 1000 GeV        PQ decay constant
#   KB=KW = 1               EW Wilson coefficients (pure-photon coupling)
#   Kg=Cta=Cb=Ct = 0        all fermion/gluon couplings zeroed
# => BR(alp -> gamma gamma) = 100%, ctau ~ 5 fm (prompt), 3-photon final state.
# Purpose (software): first exercise of SM_alp_UFO model import and cascade
# decay syntax in the FCC namespace.
#
# Cross-section note: there is no analytic gate for this BSM process. Confirm
# only that MG5 completes, reports a non-zero cross-section, and produces the
# LHE file. The typical order of magnitude at fa=1000 GeV is O(few ab).
#
# Usage (run on NIKHEF after review -- not executed automatically):
#   bash mc/gen_validation_alp_fcc.sh
# ----------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

CARD_TEMPLATE="mc/cards/validation_alp_fcc/mg5_alp_fcc.dat"
PROC_DIR="PROC_validation_alp_fcc"

echo ">>> Sourcing environment (env/setup_lcg105.sh)"
set +u
# shellcheck disable=SC1091
source env/setup_lcg105.sh
set -u

if ! command -v mg5_aMC >/dev/null 2>&1; then
  echo "ERROR: mg5_aMC not on PATH after sourcing env/setup_lcg105.sh" >&2
  exit 1
fi

# Resolve the SM_alp_UFO model path at runtime.
# The card template contains the literal token __MODEL_PATH__ which we replace
# with the actual path so the card works regardless of where the repo lives.
MODEL_PATH="${REPO_ROOT}/models/SM_alp_UFO"
if [[ ! -d "$MODEL_PATH" ]]; then
  echo "ERROR: ALP UFO model not found at $MODEL_PATH" >&2
  exit 1
fi

TMPCARD=$(mktemp /tmp/mg5_alp_fcc_XXXXXX.dat)
trap 'rm -f "$TMPCARD"' EXIT
sed "s|__MODEL_PATH__|${MODEL_PATH}|g" "$CARD_TEMPLATE" > "$TMPCARD"

echo ">>> Model path  : $MODEL_PATH"
echo ">>> Temp card   : $TMPCARD"
echo ">>> Running MadGraph: $CARD_TEMPLATE (resolved)"
mg5_aMC "$TMPCARD"

BANNER="${PROC_DIR}/Events/run_01/run_01_tag_1_banner.txt"
LHE="${PROC_DIR}/Events/run_01/unweighted_events.lhe.gz"

echo
echo "==================== Stage-1 FCC-ee ALP validation summary ===================="
if [[ -f "$BANNER" ]]; then
  echo "Cross-section (from run banner):"
  grep -i "Integrated weight" "$BANNER" || echo "  (could not find 'Integrated weight' line)"
else
  echo "Run banner not found at: $BANNER"
  echo "Check $PROC_DIR/crossx.html or the MadGraph terminal output above."
fi
echo
echo "Process : e+ e- -> gamma alp (alp -> gamma gamma)  [SM_alp_UFO cascade]"
echo "Benchmark: m_a=10 GeV, fa=1000 GeV, KB=KW=1, Kg=Cta=Cb=Ct=0"
echo "Expected: cross-section O(few ab) -- no analytic gate, confirm non-zero."
echo
if [[ -f "$LHE" ]]; then
  echo "Parton-level LHE: $LHE"
else
  echo "WARNING: expected LHE not found at $LHE"
fi
echo "=============================================================================="
