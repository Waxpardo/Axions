# Environment Setup

This directory contains the lightweight setup files used by the local Python
analysis and the Nikhef/Stoomboot production scripts. MadGraph, Pythia,
Delphes, ROOT, and AxionLimits are not vendored here.

## Python

Create a local analysis environment from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r env/requirements.txt
```

`requirements.txt` includes the Python packages used by the analysis scripts:

```text
numpy
scipy
matplotlib
uproot
awkward
vector
pandas
pylhe
pyhepmc
```

ROOT itself is not installed through pip. ROOT is expected from the LCG view on
Nikhef or from a local system installation.

## Nikhef LCG Environment

Use:

```bash
source env/setup_nikhef_lcg.sh
```

before running the smoke or production scripts on Stoomboot. The script:

1. Clears compiler-related environment variables that often cause mismatches.
2. Sources a CERN LCG view.
3. Sets `MG5ROOT` if it is not already set.
4. Exposes Pythia8 and Delphes helper paths.
5. Prints command locations and compiler versions for debugging.

If your MadGraph location is not the default, set it first:

```bash
export MG5ROOT=/data/alice/<username>/MadGraph5_aMC/MG5_aMC_v3_7_1
source env/setup_nikhef_lcg.sh
```

After sourcing the environment, a good first cluster check is:

```bash
cd mc/hepmc_smoke_test
./run_mg5_to_delphes_smoke_test.sh work 1000 100.0 "$DELPHES_CARD"
cd ../..
python3 theory/predictions/validate.py mc/hepmc_smoke_test/work --pipeline-smoke
```

The full stage order and production commands are in the repository root
`README.md`.
