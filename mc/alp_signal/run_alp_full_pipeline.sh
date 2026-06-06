#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./run_alp_full_pipeline.sh [work_dir] [n_events] [sqrt_s_GeV] [m_a_GeV] [g_agg_GeV_inv] [delphes_card] [validation_channel]

Runs one full detector-level ALP point:
  MadGraph: e+ e- -> alp gamma
  Pythia8:  ISR/FSR plus alp -> gamma gamma with physical c*tau
  HepMC2:   event record for detector simulation
  Delphes:  ROOT output using the requested detector card
  validate: Gate 1 cross section, Pythia lifetime, Delphes ROOT file,
            channel-aware Delphes signature check

Source env/setup_nikhef_lcg.sh before running on Nikhef.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"

work_dir="${1:-${script_dir}/work_full_belle2}"
n_events="${2:-1000}"
sqrt_s_gev="${3:-10.58}"
m_a_gev="${4:-1.0}"
g_agg="${5:-1e-5}"
delphes_card="${6:-${repo_root}/mc/delphes_cards/delphes_card_Belle2.tcl}"
validation_channel="${7:-resolved_prompt}"

if [[ -z "${LCG_VIEW:-}" ]]; then
  echo "LCG_VIEW is unset. Source env/setup_nikhef_lcg.sh first." >&2
  exit 1
fi

for exe in mg5_aMC python3 g++ pythia8-config root-config DelphesHepMC2; do
  if ! command -v "${exe}" >/dev/null 2>&1; then
    echo "Required command not found: ${exe}" >&2
    exit 1
  fi
done

if [[ ! -f "${delphes_card}" ]]; then
  echo "Delphes card not found: ${delphes_card}" >&2
  exit 1
fi

mkdir -p "${work_dir}"

echo ">>> Running MG5 ALP production with physical width"
ALP_WIDTH_MODE=physical \
  "${script_dir}/run_alp_mg5_production.sh" \
  "${work_dir}" \
  "${n_events}" \
  "${sqrt_s_gev}" \
  "${m_a_gev}" \
  "${g_agg}"

process_dir="${work_dir}/alp_production"
lhe_path="$(find "${process_dir}/Events" -path "*/unweighted_events.lhe.gz" | sort | tail -n 1)"
param_card="${process_dir}/Cards/param_card.dat"
hepmc_out="${work_dir}/events.hepmc"
pythia_summary="${work_dir}/pythia_lifetime_summary.json"
delphes_out="${work_dir}/delphes.root"
delphes_log="${work_dir}/delphes.log"
validation_dir="${work_dir}/validation_plots"
hist_root="${work_dir}/alp_histograms.root"
hist_summary="${work_dir}/alp_histograms_summary.json"

if [[ -z "${lhe_path}" || ! -f "${lhe_path}" ]]; then
  echo "No LHE file found under ${process_dir}/Events" >&2
  exit 1
fi

width_gev="$(
  python3 - "${param_card}" <<'PY'
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text()
match = re.search(r"^\s*DECAY\s+9999\s+([-+0-9.eE]+)", text, re.MULTILINE)
if not match:
    raise SystemExit("Could not parse DECAY 9999 from param card")
print(match.group(1))
PY
)"

zlib_flags=()
if [[ -n "${ZLIB_ROOT:-}" ]]; then
  [[ -d "${ZLIB_ROOT}/include" ]] && zlib_flags+=("-I${ZLIB_ROOT}/include")
  [[ -d "${ZLIB_ROOT}/lib" ]] && zlib_flags+=("-L${ZLIB_ROOT}/lib")
fi

echo ">>> Building ALP Pythia lifetime runner"
g++ "${script_dir}/run_alp_pythia_delphes.cc" \
  -I"${LCG_VIEW}/include" \
  "${zlib_flags[@]}" \
  $(pythia8-config --cflags --libs) \
  -L"${LCG_VIEW}/lib" \
  -lHepMC \
  -lz \
  -o "${work_dir}/run_alp_pythia_delphes"

echo ">>> Running Pythia8 ALP decay/lifetime stage"
"${work_dir}/run_alp_pythia_delphes" \
  "${lhe_path}" \
  "${n_events}" \
  "${hepmc_out}" \
  "${pythia_summary}" \
  "${m_a_gev}" \
  "${g_agg}" \
  "${width_gev}"

echo ">>> Running Delphes"
rm -f "${delphes_out}"
if ! DelphesHepMC2 "${delphes_card}" "${delphes_out}" "${hepmc_out}" >"${delphes_log}" 2>&1; then
  echo "Delphes failed. Last log lines:" >&2
  tail -n 80 "${delphes_log}" >&2 || true
  exit 1
fi
echo "    Delphes log: ${delphes_log}"

echo ">>> Running validation"
python3 "${repo_root}/theory/predictions/validate.py" \
  "${process_dir}" \
  --m-a "${m_a_gev}" \
  --g "${g_agg}" \
  --sqrt-s "${sqrt_s_gev}" \
  --width-file "${param_card}" \
  --hepmc "${hepmc_out}" \
  --pythia-summary "${pythia_summary}" \
  --delphes "${delphes_out}" \
  --plots-dir "${validation_dir}"

echo ">>> Building ALP invariant-mass histograms"
python3 "${repo_root}/analysis/alp_pipeline_histograms.py" \
  "${delphes_out}" \
  --hist-root "${hist_root}" \
  --summary-json "${hist_summary}" \
  --m-a "${m_a_gev}" \
  --sqrt-s "${sqrt_s_gev}" \
  --validation-channel "${validation_channel}" \
  --require-pass

echo
echo "==================== ALP full-pipeline summary ===================="
echo "sqrt_s_GeV     : ${sqrt_s_gev}"
echo "m_a_GeV        : ${m_a_gev}"
echo "g_agg_GeV_inv  : ${g_agg}"
echo "LHE            : ${lhe_path}"
echo "HepMC          : ${hepmc_out}"
echo "Pythia summary : ${pythia_summary}"
echo "Delphes ROOT   : ${delphes_out}"
echo "Delphes log    : ${delphes_log}"
echo "Hist ROOT      : ${hist_root}"
echo "Hist summary   : ${hist_summary}"
echo "Delphes card   : ${delphes_card}"
echo "Channel check  : ${validation_channel}"
echo "Validation     : ${validation_dir}/validation_summary.json"
echo "==============================================================="
