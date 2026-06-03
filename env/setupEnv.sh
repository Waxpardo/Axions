#!/bin/bash



# 1. clean shell

unset CC CXX FC

unset LD_LIBRARY_PATH



# 2. use stable toolchain

#source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc12-opt/setup.sh

source /cvmfs/sft.cern.ch/lcg/views/LCG_106_ATLAS_13/x86_64-el9-gcc13-opt/setup.sh

#source /cvmfs/sft.cern.ch/lcg/views/LCG_107/x86_64-el9-gcc14-opt/setup.sh



export MG5ROOT=/data/alice/pchrist/MadGraph5_aMC/MG5_aMC_v3_7_1

export PATH=$MG5ROOT/bin:$PATH

export PYTHIA8_ROOT=$(pythia8-config --prefix)

export PYTHIA8DATA=$PYTHIA8_ROOT/share/Pythia8/xmldoc

export LCG_VIEW=/cvmfs/sft.cern.ch/lcg/views/LCG_106_ATLAS_13/x86_64-el9-gcc13-opt



# 3. verify

which g++

gcc --version

g++ --version

which python3

python3 --version
