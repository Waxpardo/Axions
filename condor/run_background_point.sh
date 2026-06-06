#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  run_background_point.sh CLUSTERID JOBID SAMPLE SQRT_S_GEV NEVENTS CAMPAIGN DETECTOR

SAMPLE:
  resolved_3gamma
  invisible_gamma_nunu
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "$#" -ne 7 ]]; then
  usage
  exit 1
fi

CLUSTERID="$1"
JOBID="$2"
SAMPLE="$3"
SQRT_S_GEV="$4"
NEVENTS="$5"
CAMPAIGN="$6"
DETECTOR="$7"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AXIONS_BASE="${AXIONS_BASE:-/data/alice/ipardoza/Axions}"
cd "${AXIONS_BASE}"

case "${DETECTOR}" in
  IDEA|idea|fccee|FCCEE)
    DELPHES_CARD="${AXIONS_BASE}/mc/delphes_cards/delphes_card_IDEA.tcl"
    ;;
  Belle2|belle2|BELLE2)
    DELPHES_CARD="${AXIONS_BASE}/mc/delphes_cards/delphes_card_Belle2.tcl"
    ;;
  *)
    echo "ERROR: unknown DETECTOR '${DETECTOR}'." >&2
    exit 1
    ;;
esac

export SETUPENV_QUIET=1
set +u
# shellcheck source=/dev/null
source "${AXIONS_BASE}/env/setup_nikhef_lcg.sh"
set -u

SAFE_CAMPAIGN="$(printf '%s' "${CAMPAIGN}" | tr ' ' '_' | tr -cd 'A-Za-z0-9_.-')"
WORK_ROOT="${AXIONS_BASE}/results/backgrounds/${SAFE_CAMPAIGN}/cluster_${CLUSTERID}/job${JOBID}_${SAMPLE}"

"${SCRIPT_DIR}/../mc/backgrounds/run_sm_background_full_pipeline.sh" \
  "${WORK_ROOT}" \
  "${SAMPLE}" \
  "${NEVENTS}" \
  "${SQRT_S_GEV}" \
  "${DELPHES_CARD}"
