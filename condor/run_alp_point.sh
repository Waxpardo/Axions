#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  run_alp_point.sh CLUSTERID JOBID MASS_GEV SQRT_S_GEV G_REF_GEV_INV NEVENTS CAMPAIGN
  run_alp_point.sh JOBID MASS_GEV SQRT_S_GEV G_REF_GEV_INV NEVENTS CAMPAIGN

Runs one production-only ALP point:
  e+ e- -> alp gamma

The generated ALP is stable in the LHE. Lifetime/decay probabilities are applied
analytically downstream, so the Condor production grid only needs one reference
coupling per mass and collider energy. Other couplings are obtained by g^2
rescaling after Gate 1 validation.
EOF
}

is_nonnegative_integer() {
  case "${1:-}" in
    ''|*[!0-9]*)
      return 1
      ;;
    *)
      return 0
      ;;
  esac
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "$#" -eq 6 ]]; then
  CLUSTERID=""
  JOBID="$1"
  MASS_GEV="$2"
  SQRT_S_GEV="$3"
  G_REF_GEV_INV="$4"
  NEVENTS="$5"
  CAMPAIGN="$6"
elif [[ "$#" -eq 7 ]]; then
  CLUSTERID="$1"
  JOBID="$2"
  MASS_GEV="$3"
  SQRT_S_GEV="$4"
  G_REF_GEV_INV="$5"
  NEVENTS="$6"
  CAMPAIGN="$7"
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
BASE_FILE="${SCRIPT_DIR}/base_path.txt"

is_valid_axions_base() {
  local candidate="${1:-}"
  [[ -n "${candidate}" ]] || return 1
  candidate="${candidate%/}"
  [[ -f "${candidate}/env/setup_nikhef_lcg.sh" ]] || return 1
  [[ -f "${candidate}/mc/alp_signal/run_alp_mg5_production.sh" ]] || return 1
  [[ -d "${candidate}/models/ALP_linear/SM_alp_UFO" ]] || return 1
  return 0
}

if is_valid_axions_base "${SCRIPT_DIR}/.."; then
  RESOLVED_BASEDIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
elif [[ -f "${BASE_FILE}" ]] && is_valid_axions_base "$(cat "${BASE_FILE}")"; then
  RESOLVED_BASEDIR="$(cat "${BASE_FILE}")"
elif is_valid_axions_base "${AXIONS_BASE:-}"; then
  RESOLVED_BASEDIR="${AXIONS_BASE}"
else
  RESOLVED_BASEDIR="${FALLBACK_BASEDIR}"
fi

RESOLVED_BASEDIR="${RESOLVED_BASEDIR%/}"
if ! is_valid_axions_base "${RESOLVED_BASEDIR}"; then
  echo "ERROR: could not resolve a valid Axions base directory." >&2
  echo "Tried script dir, ${BASE_FILE}, AXIONS_BASE, and ${FALLBACK_BASEDIR}." >&2
  exit 1
fi

export AXIONS_BASE="${RESOLVED_BASEDIR}"
cd "${AXIONS_BASE}"

export SETUPENV_QUIET=1
set +u
# shellcheck source=/dev/null
source "${AXIONS_BASE}/env/setup_nikhef_lcg.sh"
set -u

SAFE_CAMPAIGN="$(printf '%s' "${CAMPAIGN}" | tr ' ' '_' | tr -cd 'A-Za-z0-9_.-')"
if [[ -z "${SAFE_CAMPAIGN}" ]]; then
  echo "ERROR: CAMPAIGN sanitized to an empty string." >&2
  exit 1
fi

POINT_TAG="$(python3 - "${JOBID}" "${MASS_GEV}" "${SQRT_S_GEV}" "${G_REF_GEV_INV}" <<'PY'
import re
import sys

jobid, mass, sqrt_s, g_ref = sys.argv[1:]

def clean(value: str) -> str:
    value = value.replace("-", "m").replace("+", "")
    value = value.replace(".", "p")
    value = re.sub(r"[^A-Za-z0-9_.-]", "_", value)
    return value

print(f"job{jobid}_m{clean(mass)}_s{clean(sqrt_s)}_g{clean(g_ref)}")
PY
)"

if [[ -n "${CLUSTERID}" ]]; then
  WORK_ROOT="${AXIONS_BASE}/results/alp_production/${SAFE_CAMPAIGN}/cluster_${CLUSTERID}/${POINT_TAG}"
else
  WORK_ROOT="${AXIONS_BASE}/results/alp_production/${SAFE_CAMPAIGN}/local/${POINT_TAG}"
fi

mkdir -p "${WORK_ROOT}"

echo "==================== ALP Condor point ===================="
echo "AXIONS_BASE      : ${AXIONS_BASE}"
echo "cluster/job      : ${CLUSTERID:-local}/${JOBID}"
echo "campaign         : ${SAFE_CAMPAIGN}"
echo "m_a_GeV          : ${MASS_GEV}"
echo "sqrt_s_GeV       : ${SQRT_S_GEV}"
echo "g_ref_GeV_inv    : ${G_REF_GEV_INV}"
echo "nevents          : ${NEVENTS}"
echo "work root        : ${WORK_ROOT}"
echo "==========================================================="

ALP_WIDTH_MODE="${ALP_WIDTH_MODE:-stable}" \
  "${AXIONS_BASE}/mc/alp_signal/run_alp_mg5_production.sh" \
  "${WORK_ROOT}" \
  "${NEVENTS}" \
  "${SQRT_S_GEV}" \
  "${MASS_GEV}" \
  "${G_REF_GEV_INV}"

python3 "${AXIONS_BASE}/theory/predictions/validate.py" \
  "${WORK_ROOT}/alp_production" \
  --plots-dir "${WORK_ROOT}/validation_plots"

python3 - "${WORK_ROOT}" "${CLUSTERID:-local}" "${JOBID}" "${MASS_GEV}" "${SQRT_S_GEV}" "${G_REF_GEV_INV}" "${NEVENTS}" "${SAFE_CAMPAIGN}" <<'PY'
import csv
import json
import sys
from pathlib import Path

work_root = Path(sys.argv[1])
summary_path = work_root / "validation_plots" / "validation_summary.json"
summary = json.loads(summary_path.read_text())
cross = next((item for item in summary["checks"] if item.get("gate") == "cross_section"), {})
row = {
    "cluster": sys.argv[2],
    "jobid": sys.argv[3],
    "m_a_GeV": sys.argv[4],
    "sqrt_s_GeV": sys.argv[5],
    "g_ref_GeV_inv": sys.argv[6],
    "nevents": sys.argv[7],
    "campaign": sys.argv[8],
    "mc_sigma_pb": cross.get("mc_sigma_pb", ""),
    "theory_sigma_pb": cross.get("theory_sigma_pb", ""),
    "ratio": cross.get("ratio", ""),
    "gate1_passed": cross.get("passed", ""),
    "summary_json": str(summary_path),
    "lhe": str(work_root / "alp_production" / "Events" / "run_01" / "unweighted_events.lhe.gz"),
    "banner": str(work_root / "alp_production" / "Events" / "run_01" / "run_01_tag_1_banner.txt"),
}
out = work_root / "point_summary.csv"
with out.open("w", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(row))
    writer.writeheader()
    writer.writerow(row)
print(f"Wrote {out}")
PY
