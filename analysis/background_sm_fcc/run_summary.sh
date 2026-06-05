#!/usr/bin/env bash
# Wrapper: sources LCG_105 env (Python + PyROOT + uproot + matplotlib)
# then runs the SM background summary and plot script.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"
set +u
# shellcheck disable=SC1091
source env/setup_lcg105.sh
set -u
python analysis/background_sm_fcc/summarise_sm_bkg.py "$@"
