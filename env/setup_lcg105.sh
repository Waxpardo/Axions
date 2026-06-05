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

# Delphes: locally built against the active ROOT (see mc/delphes/build_delphes.sh).
# Built locally to match ROOT 6.30 -- the CVMFS Delphes 3.5.0 was compiled against
# ROOT 6.26 and crashes (exit 139) in the ROOT TFile finalizer. Upstream `make`
# puts the executables and libDelphes.so in the source root, so DELPHES_DIR points
# there (the bin/ and lib/ entries below are harmless robustness for either layout).
export DELPHES_DIR="$AXIONS_ROOT/mc/delphes/Delphes-3.5.0"
export PATH="$DELPHES_DIR:$DELPHES_DIR/bin:$PATH"
export LD_LIBRARY_PATH="$DELPHES_DIR:$DELPHES_DIR/lib:${LD_LIBRARY_PATH:-}"

# Delphes diagnostic (the pipeline uses DelphesHepMC2, not the legacy DelphesHepMC).
# NOTE: the LCG_105 view itself ships a DelphesHepMC2 (delphes 3.5.1pre09, built
# against ROOT 6.30), so 'command -v DelphesHepMC2' always succeeds. We therefore
# probe the LOCAL pinned 3.5.0 build explicitly and warn on fallback, so we never
# silently revert to the view's pre-release binary.
if [ -x "$DELPHES_DIR/DelphesHepMC2" ]; then
    echo "✓ Delphes (local 3.5.0, ROOT-matched): $DELPHES_DIR/DelphesHepMC2"
elif command -v DelphesHepMC2 &> /dev/null; then
    echo "⚠ Local Delphes not built -- falling back to $(which DelphesHepMC2)"
    echo "  Run 'bash mc/delphes/build_delphes.sh' for the pinned ROOT-6.30 build."
else
    echo "✗ Delphes not built -- run: bash mc/delphes/build_delphes.sh"
fi

echo ""
echo "======================================"
echo "Setup complete!"
echo "======================================"
