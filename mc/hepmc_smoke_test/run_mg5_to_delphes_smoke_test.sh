#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./run_mg5_to_delphes_smoke_test.sh [work_dir] [n_events]

Runs a non-ALP software smoke test:
  MadGraph p p > b b~ -> LHE
  Pythia -> HepMC2
  HepMC reader + simple ROOT histograms
  DelphesHepMC2 -> Delphes ROOT

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
process_dir="${work_dir}/bbbar_test"
proc_card="${work_dir}/proc_card_smoke_test.dat"
run_card="${process_dir}/Cards/run_card.dat"

if ! command -v mg5_aMC >/dev/null 2>&1; then
  echo "mg5_aMC not found. Set MG5ROOT and source env/setup_nikhef_lcg.sh." >&2
  exit 1
fi

mkdir -p "${work_dir}"

cat > "${proc_card}" <<EOF
import model sm
generate p p > b b~
output ${process_dir} -f
EOF

mg5_aMC "${proc_card}"

python3 - "${run_card}" "${n_events}" <<'PY'
from pathlib import Path
import sys

run_card = Path(sys.argv[1])
n_events = sys.argv[2]

lines = run_card.read_text().splitlines()
updated = []
seen = False
for line in lines:
    if "= nevents" in line:
        updated.append(f"  {n_events} = nevents ! Number of unweighted events requested")
        seen = True
    else:
        updated.append(line)
if not seen:
    updated.append(f"  {n_events} = nevents ! Number of unweighted events requested")
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
  "${work_dir}/delphes.root"
