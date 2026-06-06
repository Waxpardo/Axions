#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  run_sm_background_full_pipeline.sh WORK_DIR SAMPLE N_EVENTS SQRT_S_GEV DELPHES_CARD

SAMPLE:
  resolved_3gamma       e+ e- > gamma gamma gamma
  invisible_gamma_nunu  e+ e- > gamma nu nu~

Runs:
  MG5 SM background -> Pythia/HepMC -> Delphes ROOT

Source env/setup_nikhef_lcg.sh before running on Nikhef.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"

work_dir="${1:-${repo_root}/results/backgrounds/fccee_z/resolved_3gamma_test}"
sample="${2:-resolved_3gamma}"
n_events="${3:-1000}"
sqrt_s_gev="${4:-91.2}"
delphes_card="${5:-${repo_root}/mc/delphes_cards/delphes_card_IDEA.tcl}"

if [[ -z "${LCG_VIEW:-}" ]]; then
  echo "LCG_VIEW is unset. Source env/setup_nikhef_lcg.sh first." >&2
  exit 1
fi

for exe in mg5_aMC python3 g++ pythia8-config DelphesHepMC2; do
  if ! command -v "${exe}" >/dev/null 2>&1; then
    echo "Required command not found: ${exe}" >&2
    exit 1
  fi
done

case "${sample}" in
  resolved_3gamma)
    process_line="generate e+ e- > a a a"
    cut_pta="0.5"
    cut_etaa="3.0"
    cut_draa="0.01"
    ;;
  invisible_gamma_nunu)
    process_line="generate e+ e- > a vl vl~"
    cut_pta="0.5"
    cut_etaa="3.0"
    cut_draa="0.0"
    ;;
  *)
    echo "Unknown background sample '${sample}'." >&2
    usage
    exit 1
    ;;
esac

process_dir="${work_dir}/${sample}_mg5"
proc_card="${work_dir}/proc_card_${sample}.dat"
run_card="${process_dir}/Cards/run_card.dat"
hepmc_out="${work_dir}/${sample}.hepmc"
delphes_out="${work_dir}/${sample}_delphes.root"
delphes_log="${work_dir}/${sample}_delphes.log"
metadata_json="${work_dir}/${sample}_metadata.json"

mkdir -p "${work_dir}"

cat > "${proc_card}" <<EOF
import model sm
define vl = ve vm vt
define vl~ = ve~ vm~ vt~
${process_line}
output ${process_dir} -f
EOF

echo ">>> Creating MG5 background process"
echo "sample      : ${sample}"
echo "process     : ${process_line}"
echo "output dir  : ${process_dir}"
mg5_aMC "${proc_card}"

python3 - "${run_card}" "${n_events}" "${sqrt_s_gev}" "${cut_pta}" "${cut_etaa}" "${cut_draa}" <<'PY'
from pathlib import Path
import re
import sys

run_card = Path(sys.argv[1])
n_events = sys.argv[2]
sqrt_s = float(sys.argv[3])
pta, etaa, draa = sys.argv[4:7]
beam_energy = sqrt_s / 2.0

updates = {
    "nevents": n_events,
    "lpp1": "0",
    "lpp2": "0",
    "ebeam1": f"{beam_energy:.12g}",
    "ebeam2": f"{beam_energy:.12g}",
    "pdlabel": "none",
    "pdlabel1": "none",
    "pdlabel2": "none",
    "dsqrt_shat": "0.0",
    "pta": pta,
    "ptgmin": pta,
    "etaa": etaa,
    "etaamin": "0.0",
    "draa": draa,
    "drll": "0.0",
    "mmll": "0.0",
    "use_syst": "False",
}

lines = run_card.read_text().splitlines()
updated = []
seen = set()
for line in lines:
    matched = None
    for key in updates:
        if re.search(rf"=\s*{re.escape(key)}\b", line):
            matched = key
            break
    if matched is None:
        updated.append(line)
        continue
    comment = ""
    if "!" in line:
        comment = " !" + line.split("!", 1)[1]
    updated.append(f"  {updates[matched]}\t= {matched}{comment}")
    seen.add(matched)

for key in ["nevents", "lpp1", "lpp2", "ebeam1", "ebeam2"]:
    if key not in seen:
        updated.append(f"  {updates[key]}\t= {key}")
run_card.write_text("\n".join(updated) + "\n")
PY

echo ">>> Running MG5 background generation"
"${process_dir}/bin/generate_events" -f

lhe_path="$(find "${process_dir}/Events" -path "*/unweighted_events.lhe.gz" | sort | tail -n 1)"
banner_path="$(find "${process_dir}/Events" -path "*/*banner.txt" | sort | tail -n 1)"
if [[ -z "${lhe_path}" || ! -f "${lhe_path}" ]]; then
  echo "No LHE file found under ${process_dir}/Events" >&2
  exit 1
fi

zlib_flags=()
if [[ -n "${ZLIB_ROOT:-}" ]]; then
  [[ -d "${ZLIB_ROOT}/include" ]] && zlib_flags+=("-I${ZLIB_ROOT}/include")
  [[ -d "${ZLIB_ROOT}/lib" ]] && zlib_flags+=("-L${ZLIB_ROOT}/lib")
fi

echo ">>> Building generic Pythia/HepMC runner"
g++ "${script_dir}/run_pythia_hepmc.cc" \
  -I"${LCG_VIEW}/include" \
  "${zlib_flags[@]}" \
  $(pythia8-config --cflags --libs) \
  -L"${LCG_VIEW}/lib" \
  -lHepMC \
  -lz \
  -o "${work_dir}/run_pythia_hepmc"

echo ">>> Running Pythia/HepMC"
"${work_dir}/run_pythia_hepmc" "${lhe_path}" "${n_events}" "${hepmc_out}"

echo ">>> Running Delphes"
rm -f "${delphes_out}"
if ! DelphesHepMC2 "${delphes_card}" "${delphes_out}" "${hepmc_out}" >"${delphes_log}" 2>&1; then
  echo "Delphes failed. Last log lines:" >&2
  tail -n 80 "${delphes_log}" >&2 || true
  exit 1
fi

python3 - "${metadata_json}" "${sample}" "${sqrt_s_gev}" "${n_events}" "${process_line}" "${banner_path}" "${lhe_path}" "${hepmc_out}" "${delphes_out}" "${delphes_log}" <<'PY'
import json
import re
import sys
from pathlib import Path

out = Path(sys.argv[1])
banner = Path(sys.argv[6])
sigma = None
if banner.exists():
    text = banner.read_text(errors="ignore")
    match = re.search(r"Integrated weight \(pb\)\s*:\s*([-+0-9.eE]+)", text)
    if match:
        sigma = float(match.group(1))
out.write_text(json.dumps({
    "sample": sys.argv[2],
    "sqrt_s_GeV": float(sys.argv[3]),
    "n_events": int(sys.argv[4]),
    "process": sys.argv[5],
    "sigma_pb": sigma,
    "banner": sys.argv[6],
    "lhe": sys.argv[7],
    "hepmc": sys.argv[8],
    "delphes_root": sys.argv[9],
    "delphes_log": sys.argv[10],
}, indent=2) + "\n")
PY

echo
echo "==================== SM background summary ===================="
echo "sample       : ${sample}"
echo "sqrt_s_GeV  : ${sqrt_s_gev}"
echo "LHE         : ${lhe_path}"
echo "HepMC       : ${hepmc_out}"
echo "Delphes ROOT: ${delphes_out}"
echo "Metadata    : ${metadata_json}"
echo "Delphes log : ${delphes_log}"
[[ -n "${banner_path}" ]] && grep -i "Integrated weight" "${banner_path}" || true
echo "==============================================================="
