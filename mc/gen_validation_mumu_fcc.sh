#!/usr/bin/env bash
# ============================================================================
# Stage-1 FCC-ee validation:  MadGraph e+ e- -> mu+ mu- at sqrt(s)=240 GeV
# ============================================================================
#
# Purpose (physics): generates parton-level events for the known-answer process
# e+e- -> mu+mu- at FCC-ee Higgs-factory energy. Tree-level cross-section is
# ~1.7 pb (= 0.87 nb * (10.58/240)^2 via sigma ~ 4*pi*alpha^2/(3s)).
# Purpose (software): exercises the MG5 batch-mode entrypoint in the FCC
# namespace, identically to the Belle II validation but at 120 GeV beams.
#
# Usage (run on NIKHEF after review -- not executed automatically):
#   bash mc/gen_validation_mumu_fcc.sh
# ----------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

MG5_CARD="mc/cards/validation_mumu_fcc/mg5_mumu_fcc.dat"
PROC_DIR="PROC_validation_mumu_fcc"

echo ">>> Sourcing environment (env/setup_lcg105.sh)"
set +u
source env/setup_lcg105.sh
set -u

if ! command -v mg5_aMC >/dev/null 2>&1; then
  echo "ERROR: mg5_aMC not on PATH after sourcing env/setup_lcg105.sh" >&2
  exit 1
fi

echo ">>> Running MadGraph: $MG5_CARD"
mg5_aMC "$MG5_CARD"

BANNER="$PROC_DIR/Events/run_01/run_01_tag_1_banner.txt"
LHE="$PROC_DIR/Events/run_01/unweighted_events.lhe.gz"

echo
echo "==================== Stage-1 FCC-ee validation summary ===================="
if [[ -f "$BANNER" ]]; then
  echo "Cross-section (from run banner):"
  grep -i "Integrated weight" "$BANNER" || echo "  (could not find 'Integrated weight' line)"
else
  echo "Run banner not found at: $BANNER"
  echo "Check $PROC_DIR/crossx.html or the MadGraph terminal output above."
fi
echo
echo "Expected gate: sigma(e+e- -> mu+ mu-) ~ 1.7 pb  at sqrt(s)=240 GeV"
echo
if [[ -f "$LHE" ]]; then
  echo "Parton-level LHE: $LHE"
else
  echo "WARNING: expected LHE not found at $LHE"
fi
echo "==========================================================================="
