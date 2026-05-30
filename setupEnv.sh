#!/bin/bash

# 1. Clean the shell environment
unset CC CXX FC
unset LD_LIBRARY_PATH

# 2. Source the working compiler toolchain from CVMFS
source /cvmfs/sft.cern.ch/lcg/views/LCG_107/x86_64-el9-gcc14-opt/setup.sh

# 3. Pathing to your unzipped MadGraph folder
export MG5ROOT=/data/alice/cwydeman/MG5_aMC_v3_7_1
export PATH=$MG5ROOT/bin:/cvmfs/sft.cern.ch/lcg/views/LCG_107/x86_64-el9-gcc14-opt/bin:$PATH

# 4. Bind frameworks from the updated environment
export PYTHIA8_ROOT=$(pythia8-config --prefix)
export PYTHIA8DATA=$PYTHIA8_ROOT/share/Pythia8/xmldoc
export LCG_VIEW=/cvmfs/sft.cern.ch/lcg/views/LCG_107/x86_64-el9-gcc14-opt

echo "=== Environment Ready (GCC 14 / ROOT Active) ==="
