#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./run_smoke_test.sh <lhe_path> [n_events] [hepmc_out] [analysis_root] [delphes_root] [delphes_card]

Inputs:
  lhe_path       MadGraph LHE or LHE.GZ file.
  n_events       Number of Pythia events to try. Default: 1000.
  hepmc_out      HepMC2 ASCII output from Pythia. Default: events.hepmc.
  analysis_root  Simple ROOT histogram output. Default: analysis.root.
  delphes_root   Delphes ROOT output. Default: delphes.root.
  delphes_card   Detector card. Default: $DELPHES_CARD.

Source ../../env/setup_nikhef_lcg.sh before running this script on Nikhef.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

lhe_path="${1:-ee_mumu_test/Events/run_01/unweighted_events.lhe.gz}"
n_events="${2:-1000}"
hepmc_out="${3:-events.hepmc}"
root_out="${4:-analysis.root}"
delphes_out="${5:-delphes.root}"
delphes_card="${6:-${DELPHES_CARD:-}}"

if [[ ! -f "${lhe_path}" ]]; then
  echo "LHE input not found: ${lhe_path}" >&2
  exit 1
fi

if [[ -z "${LCG_VIEW:-}" ]]; then
  echo "LCG_VIEW is unset. Source env/setup_nikhef_lcg.sh first." >&2
  exit 1
fi

if [[ -z "${delphes_card}" ]]; then
  echo "No Delphes card set. Pass one explicitly or set DELPHES_CARD." >&2
  exit 1
fi

if [[ ! -f "${delphes_card}" ]]; then
  echo "Delphes card not found: ${delphes_card}" >&2
  exit 1
fi

for exe in g++ pythia8-config root-config DelphesHepMC2; do
  if ! command -v "${exe}" >/dev/null 2>&1; then
    echo "Required command not found: ${exe}" >&2
    exit 1
  fi
done

g++ run_pythia.cc \
  $(pythia8-config --cflags --libs) \
  -L"${LCG_VIEW}/lib" \
  -lHepMC \
  -o run_pythia

./run_pythia "${lhe_path}" "${n_events}" "${hepmc_out}"

g++ read_hepmc.cc \
  -I"${LCG_VIEW}/include" \
  -L"${LCG_VIEW}/lib" \
  -lHepMC \
  -o read_hepmc

./read_hepmc "${hepmc_out}" 5 25

g++ analyse_hepmc.cc \
  -I"${LCG_VIEW}/include" \
  $(root-config --cflags --libs) \
  -L"${LCG_VIEW}/lib" \
  -lHepMC \
  -o analyse_hepmc

./analyse_hepmc "${hepmc_out}" "${root_out}"

DelphesHepMC2 "${delphes_card}" "${delphes_out}" "${hepmc_out}"

echo
echo "Smoke test complete:"
echo "  HepMC:        ${hepmc_out}"
echo "  ROOT histos:  ${root_out}"
echo "  Delphes ROOT: ${delphes_out}"
