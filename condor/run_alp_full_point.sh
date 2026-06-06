#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  run_alp_full_point.sh CLUSTERID JOBID MASS_GEV G_GEV_INV SQRT_S_GEV NEVENTS CAMPAIGN DETECTOR [CHANNEL]
  run_alp_full_point.sh JOBID MASS_GEV G_GEV_INV SQRT_S_GEV NEVENTS CAMPAIGN DETECTOR [CHANNEL]

Runs one final full-detector ALP production point:
  MG5 e+e- -> alp gamma
  Pythia alp -> gamma gamma with lifetime
  Delphes
  validation plus channel-aware detector-level signature check

DETECTOR can be IDEA or Belle2.
CHANNEL can be resolved_prompt, invisible_lower, invisible_upper, or invisible.
EOF
}

is_nonnegative_integer() {
  case "${1:-}" in
    ''|*[!0-9]*) return 1 ;;
    *) return 0 ;;
  esac
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "$#" -eq 7 || "$#" -eq 8 && ! "${2:-}" =~ ^[0-9]+$ ]]; then
  CLUSTERID=""
  JOBID="$1"
  MASS_GEV="$2"
  G_GEV_INV="$3"
  SQRT_S_GEV="$4"
  NEVENTS="$5"
  CAMPAIGN="$6"
  DETECTOR="$7"
  CHANNEL="${8:-resolved_prompt}"
elif [[ "$#" -eq 8 || "$#" -eq 9 ]]; then
  CLUSTERID="$1"
  JOBID="$2"
  MASS_GEV="$3"
  G_GEV_INV="$4"
  SQRT_S_GEV="$5"
  NEVENTS="$6"
  CAMPAIGN="$7"
  DETECTOR="$8"
  CHANNEL="${9:-resolved_prompt}"
else
  usage
  exit 1
fi

if [[ -n "${CLUSTERID}" ]] && ! is_nonnegative_integer "${CLUSTERID}"; then
  echo "ERROR: CLUSTERID must be a non-negative integer." >&2
  exit 1
fi
if ! is_nonnegative_integer "${JOBID}"; then
  echo "ERROR: JOBID must be a non-negative integer." >&2
  exit 1
fi
if ! is_nonnegative_integer "${NEVENTS}" || [[ "${NEVENTS}" -eq 0 ]]; then
  echo "ERROR: NEVENTS must be a positive integer." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FALLBACK_BASEDIR="/data/alice/ipardoza/Axions"

if [[ -f "${SCRIPT_DIR}/../env/setup_nikhef_lcg.sh" ]]; then
  AXIONS_BASE="$(cd "${SCRIPT_DIR}/.." && pwd)"
else
  AXIONS_BASE="${AXIONS_BASE:-${FALLBACK_BASEDIR}}"
fi
AXIONS_BASE="${AXIONS_BASE%/}"
cd "${AXIONS_BASE}"

case "${DETECTOR}" in
  IDEA|idea|fccee|FCCEE)
    DELPHES_CARD="${AXIONS_BASE}/mc/delphes_cards/delphes_card_IDEA.tcl"
    DETECTOR_TAG="IDEA"
    ;;
  Belle2|belle2|BELLE2)
    DELPHES_CARD="${AXIONS_BASE}/mc/delphes_cards/delphes_card_Belle2.tcl"
    DETECTOR_TAG="Belle2"
    ;;
  *)
    echo "ERROR: unknown DETECTOR '${DETECTOR}'. Use IDEA or Belle2." >&2
    exit 1
    ;;
esac

export SETUPENV_QUIET=1
set +u
# shellcheck source=/dev/null
source "${AXIONS_BASE}/env/setup_nikhef_lcg.sh"
set -u

SAFE_CAMPAIGN="$(printf '%s' "${CAMPAIGN}" | tr ' ' '_' | tr -cd 'A-Za-z0-9_.-')"
POINT_TAG="$(python3 - "${JOBID}" "${MASS_GEV}" "${G_GEV_INV}" "${SQRT_S_GEV}" "${DETECTOR_TAG}" <<'PY'
import re
import sys

jobid, mass, coupling, sqrt_s, detector = sys.argv[1:]

def clean(value: str) -> str:
    value = value.replace("-", "m").replace("+", "")
    value = value.replace(".", "p")
    return re.sub(r"[^A-Za-z0-9_.-]", "_", value)

print(f"job{jobid}_m{clean(mass)}_g{clean(coupling)}_s{clean(sqrt_s)}_{clean(detector)}")
PY
)"

if [[ -n "${CLUSTERID}" ]]; then
  WORK_ROOT="${AXIONS_BASE}/results/alp_full_production/${SAFE_CAMPAIGN}/cluster_${CLUSTERID}/${POINT_TAG}"
else
  WORK_ROOT="${AXIONS_BASE}/results/alp_full_production/${SAFE_CAMPAIGN}/local/${POINT_TAG}"
fi

mkdir -p "${WORK_ROOT}"

echo "================ ALP full-detector Condor point ================"
echo "AXIONS_BASE      : ${AXIONS_BASE}"
echo "cluster/job      : ${CLUSTERID:-local}/${JOBID}"
echo "campaign         : ${SAFE_CAMPAIGN}"
echo "detector         : ${DETECTOR_TAG}"
echo "m_a_GeV          : ${MASS_GEV}"
echo "g_agg_GeV_inv    : ${G_GEV_INV}"
echo "sqrt_s_GeV       : ${SQRT_S_GEV}"
echo "nevents          : ${NEVENTS}"
echo "channel          : ${CHANNEL}"
echo "work root        : ${WORK_ROOT}"
echo "Delphes card     : ${DELPHES_CARD}"
echo "==============================================================="

"${AXIONS_BASE}/mc/alp_signal/run_alp_full_pipeline.sh" \
  "${WORK_ROOT}" \
  "${NEVENTS}" \
  "${SQRT_S_GEV}" \
  "${MASS_GEV}" \
  "${G_GEV_INV}" \
  "${DELPHES_CARD}" \
  "${CHANNEL}"

python3 - "${WORK_ROOT}" "${CLUSTERID:-local}" "${JOBID}" "${MASS_GEV}" "${G_GEV_INV}" "${SQRT_S_GEV}" "${NEVENTS}" "${SAFE_CAMPAIGN}" "${DETECTOR_TAG}" "${CHANNEL}" <<'PY'
import csv
import json
import sys
from pathlib import Path

work_root = Path(sys.argv[1])
validation = json.loads((work_root / "validation_plots" / "validation_summary.json").read_text())
hist = json.loads((work_root / "alp_histograms_summary.json").read_text())
cross = next((item for item in validation["checks"] if item.get("gate") == "cross_section"), {})
row = {
    "cluster": sys.argv[2],
    "jobid": sys.argv[3],
    "m_a_GeV": sys.argv[4],
    "g_agg_GeV_inv": sys.argv[5],
    "sqrt_s_GeV": sys.argv[6],
    "nevents": sys.argv[7],
    "campaign": sys.argv[8],
    "detector": sys.argv[9],
    "channel": sys.argv[10],
    "mc_sigma_pb": cross.get("mc_sigma_pb", ""),
    "theory_sigma_pb": cross.get("theory_sigma_pb", ""),
    "gate1_passed": cross.get("passed", ""),
    "signature_validation_passed": hist.get("passed", ""),
    "validation_channel": hist.get("validation_channel", ""),
    "resolved_best_mgg_mean_GeV": hist.get("resolved_best_mgg_mean_GeV", ""),
    "resolved_best_mgg_abs_error_GeV": hist.get("resolved_best_mgg_abs_error_GeV", ""),
    "leading_photon_energy_mean_GeV": hist.get("leading_photon_energy_mean_GeV", ""),
    "leading_recoil_abs_error_GeV": hist.get("leading_recoil_abs_error_GeV", ""),
    "validation_json": str(work_root / "validation_plots" / "validation_summary.json"),
    "hist_summary_json": str(work_root / "alp_histograms_summary.json"),
    "delphes_root": str(work_root / "delphes.root"),
}
out = work_root / "full_point_summary.csv"
with out.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(row))
    writer.writeheader()
    writer.writerow(row)
print(f"Wrote {out}")
PY
