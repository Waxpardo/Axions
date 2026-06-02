#!/bin/bash

# Setup script for LCG 105 environment with CERN tools
# Sources the LCG 105 setup and configures the Axions environment

# Source LCG 105 environment
source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc11-opt/setup.sh

# Define AXIONS_ROOT as the repository root
export AXIONS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Print diagnostics
echo "======================================"
echo "Axions Environment Setup - LCG 105"
echo "======================================"
echo ""
echo "Repository Root: $AXIONS_ROOT"
echo ""
echo "--- Tool Diagnostics ---"
echo ""

# ROOT version
if command -v root-config &> /dev/null; then
    ROOT_VERSION=$(root-config --version)
    echo "✓ ROOT version: $ROOT_VERSION"
else
    echo "✗ ROOT not found in PATH"
fi

# MadGraph5_aMC path
if command -v mg5_aMC &> /dev/null; then
    MG5_PATH=$(which mg5_aMC)
    echo "✓ MadGraph5_aMC path: $MG5_PATH"
else
    echo "✗ MadGraph5_aMC not found in PATH"
fi

# PYTHIA8
if command -v pythia8-config &> /dev/null; then
    PYTHIA8_PATH=$(which pythia8-config)
    echo "✓ PYTHIA8 path: $PYTHIA8_PATH"
else
    echo "✗ PYTHIA8 not found in PATH"
fi

# LHAPDF version
if command -v lhapdf-config &> /dev/null; then
    LHAPDF_VERSION=$(lhapdf-config --version)
    echo "✓ LHAPDF version: $LHAPDF_VERSION"
else
    echo "✗ LHAPDF not found in PATH"
fi

# Delphes
if command -v DelphesHepMC &> /dev/null; then
    DELPHES_PATH=$(which DelphesHepMC)
    echo "✓ Delphes path: $DELPHES_PATH"
elif [ -n "${DELPHES_DIR:-}" ] && [ -d "$DELPHES_DIR" ]; then
    echo "✓ DELPHES_DIR set: $DELPHES_DIR"
else
    echo "✗ Delphes not available in PATH"
fi

echo ""
echo "======================================"
echo "Setup complete!"
echo "======================================"
