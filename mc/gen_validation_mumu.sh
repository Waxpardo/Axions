#!/usr/bin/env bash
# ============================================================================
# Stage-1 validation entrypoint:  e+ e- -> mu+ mu-
# ============================================================================
#
# Purpose (software): one command that runs the MadGraph driver and then reports
# the cross-section and LHE path, so the validation gate can be checked at a glance.
# This is the interactive entrypoint every later stage (Pythia, Delphes, Condor)
# is built on -- the same pattern as the ALP `mc/gen_signal.sh`, kept separate.
#
# Purpose (physics): produces the parton-level e+e- -> mu+ mu- sample and surfaces
# its cross-section, which must land in ~0.8-0.9 nb to validate the generator setup.
#
# Usage (run on NIKHEF after review -- not executed automatically):
#   bash mc/gen_validation_mumu.sh
# ----------------------------------------------------------------------------
set -euo pipefail

# Resolve the repository root from this script's location, so the script works
# regardless of the directory it is invoked from.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

MG5_CARD="mc/cards/validation_mumu/mg5_mumu.dat"
PROC_DIR="PROC_validation_mumu"

# Set up the LCG_105 toolchain (sourced directly -- never piped, or PATH is lost).
# Relax 'set -u' while sourcing: the CVMFS LCG setup.sh reads an unbound
# variable (COMPILER), which under 'set -u' aborts this script the moment we
# source it. We restore strict mode immediately after.
echo ">>> Sourcing environment (env/setup_lcg105.sh)"
set +u
# shellcheck disable=SC1091
source env/setup_lcg105.sh
set -u

if ! command -v mg5_aMC >/dev/null 2>&1; then
  echo "ERROR: mg5_aMC not on PATH after sourcing env/setup_lcg105.sh" >&2
  exit 1
fi

echo ">>> Running MadGraph: $MG5_CARD"
mg5_aMC "$MG5_CARD"

# --- Report the validation gate -----------------------------------------------
BANNER="$PROC_DIR/Events/run_01/run_01_tag_1_banner.txt"
LHE="$PROC_DIR/Events/run_01/unweighted_events.lhe.gz"

echo
echo "==================== Stage-1 validation summary ===================="
if [[ -f "$BANNER" ]]; then
  echo "Cross-section (from run banner):"
  grep -i "Integrated weight" "$BANNER" || echo "  (could not find 'Integrated weight' line)"
else
  echo "Run banner not found at: $BANNER"
  echo "Check $PROC_DIR/crossx.html or the MadGraph terminal output above."
fi
echo
echo "Expected gate: sigma(e+e- -> mu+ mu-) ~ 0.8 - 0.9 nb  (= 8e2 - 9e2 pb)"
echo
if [[ -f "$LHE" ]]; then
  echo "Parton-level LHE: $LHE"
else
  echo "WARNING: expected LHE not found at $LHE"
fi
echo "===================================================================="
