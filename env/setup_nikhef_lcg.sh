#!/usr/bin/env bash
# Source this file on Nikhef/Stoomboot before running MG5/Pythia/HepMC tests.
#
# Usage:
#   export MG5ROOT=/data/alice/$USER/MadGraph5_aMC/MG5_aMC_v3_7_1
#   source env/setup_nikhef_lcg.sh


unset CC CXX FC
unset LD_LIBRARY_PATH

# Alternative views for debugging:
# source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc12-opt/setup.sh
# source /cvmfs/sft.cern.ch/lcg/views/LCG_107/x86_64-el9-gcc14-opt/setup.sh
source /cvmfs/sft.cern.ch/lcg/views/LCG_106_ATLAS_13/x86_64-el9-gcc13-opt/setup.sh

# Point this to your unzipped MadGraph installation.
if [[ -z "${MG5ROOT:-}" ]]; then
  export MG5ROOT="/data/alice/${USER}/MadGraph5_aMC/MG5_aMC_v3_7_1"
fi

export LCG_VIEW=/cvmfs/sft.cern.ch/lcg/views/LCG_106_ATLAS_13/x86_64-el9-gcc13-opt
export PATH="${MG5ROOT}/bin:/cvmfs/sft.cern.ch/lcg/releases/gcc/12.1.0/x86_64-el9/bin:${PATH}"
export PYTHIA8_ROOT="$(pythia8-config --prefix)"
export PYTHIA8DATA="${PYTHIA8_ROOT}/share/Pythia8/xmldoc"

# 4. Verify.
echo "=== Nikhef MG5/Pythia/HepMC Environment ==="
echo "MG5ROOT=${MG5ROOT}"
echo "LCG_VIEW=${LCG_VIEW}"
which g++
gcc --version | head -n 1
g++ --version | head -n 1
which python3
python3 --version
which mg5_aMC || true

