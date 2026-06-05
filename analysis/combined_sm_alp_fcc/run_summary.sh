#!/usr/bin/env bash
# Wrapper: sources LCG_105 env (Python + uproot + matplotlib), then runs the
# combined SM+ALP validation summary. Pass the variant through, e.g.:
#   bash analysis/combined_sm_alp_fcc/run_summary.sh honest
#   bash analysis/combined_sm_alp_fcc/run_summary.sh boosted
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"
set +u
# shellcheck disable=SC1091
source env/setup_lcg105.sh
set -u
python analysis/combined_sm_alp_fcc/summarise_combined.py "$@"
