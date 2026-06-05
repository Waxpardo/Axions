#!/usr/bin/env bash
# Wrapper: sources LCG_105 env (Python + uproot + matplotlib), then runs
# the diphoton invariant mass analysis script.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"
set +u
# shellcheck disable=SC1091
source env/setup_lcg105.sh
set -u
python analysis/background_sm_fcc/diphoton_mass.py "$@"
