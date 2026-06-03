#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./run_mg5_to_delphes_smoke_test.sh [work_dir] [n_events] [sqrt_s_GeV] [delphes_card]

Runs a non-ALP software smoke test:
  MadGraph e+ e- > mu+ mu- -> LHE
  Pythia -> HepMC2
  HepMC reader + simple ROOT histograms
  DelphesHepMC2 -> Delphes ROOT

The center-of-mass energy and detector card are configurable. The default
sqrt(s) is a generic 10 GeV software-test value, not a Belle II or FCC-ee
analysis setting.

Source ../../env/setup_nikhef_lcg.sh before running this script on Nikhef.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work_dir="${1:-${script_dir}/work}"
n_events="${2:-1000}"
sqrt_s_gev="${3:-${SMOKE_SQRT_S_GEV:-10.0}}"
delphes_card="${4:-${DELPHES_CARD:-}}"
process_dir="${work_dir}/ee_mumu_test"
proc_card="${work_dir}/proc_card_smoke_test.dat"
run_card="${process_dir}/Cards/run_card.dat"

if ! command -v mg5_aMC >/dev/null 2>&1; then
  echo "mg5_aMC not found. Set MG5ROOT and source env/setup_nikhef_lcg.sh." >&2
  exit 1
fi

mkdir -p "${work_dir}"

cat > "${proc_card}" <<EOF
import model sm
generate e+ e- > mu+ mu-
output ${process_dir} -f
EOF

mg5_aMC "${proc_card}"

python3 - "${run_card}" "${n_events}" "${sqrt_s_gev}" <<'PY'
from pathlib import Path
import re
import sys

run_card = Path(sys.argv[1])
n_events = sys.argv[2]
sqrt_s = float(sys.argv[3])
beam_energy = sqrt_s / 2.0

updates = {
    "nevents": n_events,
    "lpp1": "0",
    "lpp2": "0",
    "ebeam1": f"{beam_energy:.12g}",
    "ebeam2": f"{beam_energy:.12g}",
    "pdlabel1": "none",
    "pdlabel2": "none",
    "use_syst": "False",
}

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

for key, value in updates.items():
    if key not in seen:
        updated.append(f"  {value}\t= {key}")
run_card.write_text("\n".join(updated) + "\n")
PY

"${process_dir}/bin/generate_events" -f

lhe_path="$(find "${process_dir}/Events" -path "*/unweighted_events.lhe.gz" | sort | tail -n 1)"
if [[ -z "${lhe_path}" ]]; then
  echo "No unweighted_events.lhe.gz found under ${process_dir}/Events" >&2
  exit 1
fi

"${script_dir}/run_smoke_test.sh" \
  "${lhe_path}" \
  "${n_events}" \
  "${work_dir}/events.hepmc" \
  "${work_dir}/analysis.root" \
  "${work_dir}/delphes.root" \
  "${delphes_card}"
