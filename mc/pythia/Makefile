# Makefile for the standalone Pythia8 shower driver (Stage 2 of the validation).
#
# Builds `shower_lhe` (reads an LHE file, runs the Pythia8 parton shower, writes
# HepMC2). Requires LCG_105 to be sourced (env/setup_lcg105.sh) so that
# `pythia8-config` is on PATH.
#
# HEPMC_PREFIX must point at the LCG view that provides HepMC2 (libHepMC +
# include/HepMC). mc/shower_validation_mumu.sh derives it automatically; if you
# run `make` by hand, pass e.g.:
#     make HEPMC_PREFIX=/cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc11-opt
#
# We link HepMC2 (not HepMC3) to match the DelphesHepMC2 reader used in Stage 3.

CXX          ?= g++
HEPMC_PREFIX ?=

PYTHIA_CXXFLAGS := $(shell pythia8-config --cxxflags)
PYTHIA_LIBS     := $(shell pythia8-config --libs)

ifneq ($(HEPMC_PREFIX),)
  HEPMC_CXXFLAGS := -DHEPMC2 -I$(HEPMC_PREFIX)/include
  HEPMC_LIBS     := -L$(HEPMC_PREFIX)/lib -Wl,-rpath,$(HEPMC_PREFIX)/lib -lHepMC
else
  # Fall back to whatever HepMC the compiler/linker already sees on its paths.
  HEPMC_CXXFLAGS := -DHEPMC2
  HEPMC_LIBS     := -lHepMC
endif

shower_lhe: shower_lhe.cc
	$(CXX) $< -o $@ $(PYTHIA_CXXFLAGS) $(HEPMC_CXXFLAGS) $(PYTHIA_LIBS) $(HEPMC_LIBS)

clean:
	rm -f shower_lhe *.o

.PHONY: clean
