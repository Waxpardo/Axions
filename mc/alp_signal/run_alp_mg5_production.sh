#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./run_alp_mg5_production.sh [work_dir] [n_events] [sqrt_s_GeV] [m_a_GeV] [g_agg_GeV_inv]

Runs the ALP production-only MadGraph stage:
  e+ e- -> alp gamma

This is the production sample used by the analytic-weighting strategy. The ALP
mass is written to MASS 9999, and the physical g_agg is converted into the
UFO-native fa, KB, and KW parameters:

  g_agg = alpha_em * (KB + KW) / (sqrt(2) * pi * fa)

Optional environment variables:
  ALP_FA_GEV        Default: 1000
  ALP_AEWM1         Default: 137.035999084
  ALP_KB_FRACTION   Optional manual split of KB+KW assigned to KB
  ALP_WIDTH_MODE    physical or stable. Default: stable
  ALP_KG, ALP_CTA, ALP_CB, ALP_CT

Source env/setup_nikhef_lcg.sh before running this script on Nikhef.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"

work_dir="${1:-${script_dir}/work}"
n_events="${2:-1000}"
sqrt_s_gev="${3:-100.0}"
m_a_gev="${4:-1.0}"
g_agg="${5:-1e-4}"

fa_gev="${ALP_FA_GEV:-1000.0}"
aewm1="${ALP_AEWM1:-137.035999084}"
kb_fraction="${ALP_KB_FRACTION:-}"
width_mode="${ALP_WIDTH_MODE:-stable}"
kg="${ALP_KG:-0.0}"
cta="${ALP_CTA:-0.0}"
cb="${ALP_CB:-0.0}"
ct="${ALP_CT:-0.0}"

model_path="${repo_root}/models/ALP_linear/SM_alp_UFO"
process_dir="${work_dir}/alp_production"
proc_card="${work_dir}/proc_card_alp_production.dat"
run_card="${process_dir}/Cards/run_card.dat"
param_card="${process_dir}/Cards/param_card.dat"

if ! command -v mg5_aMC >/dev/null 2>&1; then
  echo "mg5_aMC not found. Set MG5ROOT and source env/setup_nikhef_lcg.sh." >&2
  exit 1
fi

if [[ ! -d "${model_path}" ]]; then
  echo "ALP UFO not found at ${model_path}" >&2
  exit 1
fi

mkdir -p "${work_dir}"

cat > "${proc_card}" <<EOF
import model ${model_path}
generate e+ e- > alp a
output ${process_dir} -f
EOF

echo ">>> Creating ALP process directory"
echo "    model      : ${model_path}"
echo "    process    : e+ e- > alp a"
echo "    output dir : ${process_dir}"
mg5_aMC "${proc_card}"

python3 - "${run_card}" "${n_events}" "${sqrt_s_gev}" <<'PY'
from pathlib import Path
import re
import sys

run_card = Path(sys.argv[1])
n_events = sys.argv[2]
sqrt_s = float(sys.argv[3])
beam_energy = sqrt_s / 2.0

required_updates = {
    "nevents": n_events,
    "lpp1": "0",
    "lpp2": "0",
    "ebeam1": f"{beam_energy:.12g}",
    "ebeam2": f"{beam_energy:.12g}",
}
optional_updates = {
    "pdlabel": "none",
    "pdlabel1": "none",
    "pdlabel2": "none",
    "dsqrt_shat": "0.0",
    "pta": "0.0",
    "ptj": "0.0",
    "ptl": "0.0",
    "etaa": "-1.0",
    "etaj": "-1.0",
    "etal": "-1.0",
    "etaamin": "0.0",
    "etajmin": "0.0",
    "etalmin": "0.0",
    "draa": "0.0",
    "draj": "0.0",
    "drjj": "0.0",
    "drll": "0.0",
    "mmll": "0.0",
    "use_syst": "False",
}
updates = {**required_updates, **optional_updates}

lines = run_card.read_text().splitlines()
updated = []
seen = set()
for line in lines:
    matched_key = None
    for key in updates:
        if re.search(rf"=\s*{re.escape(key)}\b", line):
            matched_key = key
            break
    if matched_key is None:
        updated.append(line)
        continue

    comment = ""
    if "!" in line:
        comment = " !" + line.split("!", 1)[1]
    updated.append(f"  {updates[matched_key]}\t= {matched_key}{comment}")
    seen.add(matched_key)

for key, value in required_updates.items():
    if key not in seen:
        updated.append(f"  {value}\t= {key}")

run_card.write_text("\n".join(updated) + "\n")
PY

param_args=(
  --out "${param_card}"
  --m-a "${m_a_gev}"
  --g-agg "${g_agg}"
  --fa "${fa_gev}"
  --aewm1 "${aewm1}"
  --kg "${kg}"
  --cta "${cta}"
  --cb "${cb}"
  --ct "${ct}"
  --width-mode "${width_mode}"
)

if [[ -n "${kb_fraction}" ]]; then
  param_args+=(--kb-fraction "${kb_fraction}")
fi

python3 "${repo_root}/mc/make_param_card.py" "${param_args[@]}"

echo ">>> Running MadGraph event generation"
"${process_dir}/bin/generate_events" -f

lhe_path="$(find "${process_dir}/Events" -path "*/unweighted_events.lhe.gz" | sort | tail -n 1)"
banner_path="$(find "${process_dir}/Events" -path "*/*banner.txt" | sort | tail -n 1)"

if [[ -z "${lhe_path}" ]]; then
  echo "No unweighted_events.lhe.gz found under ${process_dir}/Events" >&2
  exit 1
fi

echo
echo "==================== ALP production summary ===================="
echo "Process        : e+ e- -> alp gamma"
echo "sqrt_s_GeV     : ${sqrt_s_gev}"
echo "m_a_GeV        : ${m_a_gev}"
echo "g_agg_GeV_inv  : ${g_agg}"
echo "param_card     : ${param_card}"
echo "run_card       : ${run_card}"
echo "LHE            : ${lhe_path}"
if [[ -n "${banner_path}" ]]; then
  echo "banner         : ${banner_path}"
  grep -i "Integrated weight" "${banner_path}" || true
fi
echo "==============================================================="
