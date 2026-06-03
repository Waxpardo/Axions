#!/usr/bin/env bash
# Source this file on Nikhef/Stoomboot before running the smoke pipeline.
#
# Usage:
#   export MG5ROOT=/data/alice/$USER/MadGraph5_aMC/MG5_aMC_v3_7_1
#   source env/setup_nikhef_lcg.sh

unset CC CXX FC
unset LD_LIBRARY_PATH

export LCG_VIEW="${LCG_VIEW:-/cvmfs/sft.cern.ch/lcg/views/LCG_106_ATLAS_13/x86_64-el9-gcc13-opt}"
if [[ ! -f "${LCG_VIEW}/setup.sh" ]]; then
  echo "LCG view not found: ${LCG_VIEW}" >&2
  return 1 2>/dev/null || exit 1
fi

source "${LCG_VIEW}/setup.sh"

# Point this to your unzipped MadGraph installation.
if [[ -z "${MG5ROOT:-}" ]]; then
  export MG5ROOT="/data/alice/${USER}/MadGraph5_aMC/MG5_aMC_v3_7_1"
fi

# Keep the compiler from the LCG view. ROOT/Delphes in this view are built with
# GCC13, so prepending an older GCC causes libstdc++ symbol mismatches.
export PATH="${MG5ROOT}/bin:${PATH}"

if command -v pythia8-config >/dev/null 2>&1; then
  export PYTHIA8_ROOT="$(pythia8-config --prefix)"
  export PYTHIA8DATA="${PYTHIA8_ROOT}/share/Pythia8/xmldoc"
fi

# Delphes is not vendored in this repository. Use the CVMFS build matching the
# LCG106/GCC13 stack unless the user explicitly points DELPHES_DIR elsewhere.
export DELPHES_DIR="${DELPHES_DIR:-/cvmfs/sft.cern.ch/lcg/releases/delphes/3.5.1pre14-d549e/x86_64-el9-gcc13-opt}"
if [[ -d "${DELPHES_DIR}" ]]; then
  export PATH="${DELPHES_DIR}/bin:${PATH}"
  export LD_LIBRARY_PATH="${DELPHES_DIR}/lib:${LD_LIBRARY_PATH:-}"
  export DELPHES_CARD_IDEA="${DELPHES_CARD_IDEA:-${DELPHES_DIR}/cards/delphes_card_IDEA.tcl}"
else
  echo "Warning: DELPHES_DIR not found: ${DELPHES_DIR}" >&2
fi

echo "=== Nikhef MG5/Pythia/HepMC/Delphes Environment ==="
echo "MG5ROOT=${MG5ROOT}"
echo "LCG_VIEW=${LCG_VIEW}"
echo "DELPHES_DIR=${DELPHES_DIR:-unset}"
echo "DELPHES_CARD_IDEA=${DELPHES_CARD_IDEA:-unset}"
command -v g++ || true
gcc --version | head -n 1
g++ --version | head -n 1
command -v python3 || true
python3 --version
command -v mg5_aMC || true
command -v pythia8-config || true
command -v root-config || true
command -v DelphesHepMC2 || true
