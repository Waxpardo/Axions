#!/usr/bin/env bash
set -euo pipefail

lhe_path="${1:-bbbar_test/Events/run_01/unweighted_events.lhe.gz}"
n_events="${2:-10000}"
hepmc_out="${3:-events.hepmc}"
root_out="${4:-analysis.root}"

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

./read_hepmc "${hepmc_out}"

g++ analyse_hepmc.cc \
  -I"${LCG_VIEW}/include" \
  $(root-config --cflags --libs) \
  -L"${LCG_VIEW}/lib" \
  -lHepMC \
  -o analyse_hepmc

./analyse_hepmc "${hepmc_out}" "${root_out}"

