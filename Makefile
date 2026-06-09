# Makefile for the Photophilic ALP Search pipeline (Belle II / FCC-ee Z-pole).
#
# This file ties together the stages documented in README.md so the main
# local workflow can be driven with `make <target>` instead of copying long
# commands by hand.
#
# IMPORTANT — two tiers of targets:
#
#   1. LOCAL targets need only the Python virtualenv (`make venv`) and the
#      checked-in intermediate CSVs under results/. They run anywhere:
#      theory-grid, belle2-closure, projection, money-plots, local-all.
#
#   2. MC / CLUSTER targets need the MadGraph5_aMC + Pythia8 + Delphes stack
#      (sourced via env/setup_nikhef_lcg.sh, normally only available on
#      Nikhef/Stoomboot) and, for full-statistics production, an HTCondor
#      submit node. These targets fail early with a pointer to the setup
#      README when the required tools are missing.
#
# Run `make help` (or just `make`) for an overview.

VENV        := .venv
VENV_BIN    := $(VENV)/bin
SYSTEM_PYTHON ?= python3
PYTHON      ?= $(VENV_BIN)/python
AXIONLIMITS_DIR    := external/AxionLimits
AXIONLIMITS_COMMIT := 7d375f4879b32406a239fe48d2615a4bfd9bc0bb
FCCEE_CONFIG    := analysis/configs/fccee_zpole_inputs.json
BELLE2_CONFIG   := analysis/configs/belle2_closure_inputs.json
RESULTS_FCCEE   := results/fccee
N_MASS          := 180
N_G             := 180

.DEFAULT_GOAL := help

.PHONY: help venv axionlimits \
        theory-grid belle2-closure projection-bootstrap efficiency-map projection background-signal-examples prompt-resolved-mass-example money-plots local-all \
        check-mc-tools smoke-test signal-point-belle2 signal-point-fccee background-points \
        condor-background-scan condor-signal-scan collect-scan \
        status clean-pyc

## ------------------------------------------------------------------------
## help
## ------------------------------------------------------------------------

help:
	@echo "Photophilic ALP Search -- pipeline entry points"
	@echo ""
	@echo "Setup:"
	@echo "  make venv                 Create .venv and install env/requirements.txt"
	@echo "  make axionlimits          Clone AxionLimits at the pinned commit into external/"
	@echo ""
	@echo "Local analysis chain (pure Python; needs only 'make venv' + checked-in CSVs):"
	@echo "  make theory-grid          Rebuild theory/predictions/theory_grid.csv"
	@echo "  make belle2-closure       Rerun the Belle II closure test (needs AxionLimits)"
	@echo "  make efficiency-map       Rebuild the Delphes-derived detector-correction map"
	@echo "  make projection           Rebuild the FCC-ee projection + signature classification"
	@echo "  make background-signal-examples  Rebuild SM-background + example-signal figure"
	@echo "  make prompt-resolved-mass-example  Rebuild the CMS-style m_gg example figure"
	@echo "  make money-plots          Rebuild the money plots (full + closeup, needs AxionLimits)"
	@echo "  make local-all            Run the full local Python chain in order"
	@echo ""
	@echo "MC production (needs MadGraph5_aMC/Pythia8/Delphes; source env/setup_nikhef_lcg.sh):"
	@echo "  make smoke-test           Generic MG5->Pythia->HepMC->Delphes smoke test"
	@echo "  make signal-point-belle2  One full ALP signal point at Belle II energy (example)"
	@echo "  make signal-point-fccee   One full ALP signal point at FCC-ee Z-pole energy (example)"
	@echo "  make background-points    Two manual SM background points (resolved + invisible)"
	@echo ""
	@echo "HTCondor batch submission (Nikhef/Stoomboot only):"
	@echo "  make condor-background-scan   Submit the full SM background production scan"
	@echo "  make condor-signal-scan       Submit the detector-level ALP signal point scan"
	@echo "  make collect-scan             Collect finished signal-scan summaries into a CSV"
	@echo ""
	@echo "Misc:"
	@echo "  make status               Show which checked-in results/configs exist"
	@echo "  make clean-pyc            Remove __pycache__ directories and *.pyc files"
	@echo ""
	@echo "See README.md for the full stage order and the directory READMEs"
	@echo "for details on each part of the pipeline."

## ------------------------------------------------------------------------
## Environment setup
## ------------------------------------------------------------------------

venv:
	$(SYSTEM_PYTHON) -m venv $(VENV)
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r env/requirements.txt
	@echo ""
	@echo "Done. Activate it with:  source $(VENV_BIN)/activate"

axionlimits:
	@if [ -d "$(AXIONLIMITS_DIR)/.git" ]; then \
		echo "external/AxionLimits already present (skipping clone)."; \
	else \
		echo "Cloning AxionLimits at the pinned commit recorded in analysis/configs/axionlimits_source.json ..."; \
		mkdir -p external && \
		git clone https://github.com/cajohare/AxionLimits.git "$(AXIONLIMITS_DIR)" && \
		cd "$(AXIONLIMITS_DIR)" && git checkout $(AXIONLIMITS_COMMIT); \
	fi
	@cd "$(AXIONLIMITS_DIR)" && \
		actual=$$(git rev-parse HEAD) && \
		if [ "$$actual" != "$(AXIONLIMITS_COMMIT)" ]; then \
			echo "WARNING: external/AxionLimits is at $$actual, expected $(AXIONLIMITS_COMMIT)."; \
			echo "         Run: cd $(AXIONLIMITS_DIR) && git checkout $(AXIONLIMITS_COMMIT)"; \
		else \
			echo "external/AxionLimits is at the pinned commit $(AXIONLIMITS_COMMIT)."; \
		fi

## ------------------------------------------------------------------------
## Local analysis chain
##
## These targets only touch Python + the CSV/JSON outputs already
## checked into results/ and analysis/configs/ -- no MadGraph/Pythia/Delphes
## and no cluster access required.
## ------------------------------------------------------------------------

theory-grid:
	$(PYTHON) theory/predictions/predict_grid.py --out theory/predictions/theory_grid.csv

belle2-closure: axionlimits
	$(PYTHON) theory/predictions/validate.py \
		--belle2-closure \
		--belle2-config $(BELLE2_CONFIG) \
		--axionlimits-dir $(AXIONLIMITS_DIR)

# The detector-correction map (efficiency-map) and the final projection are
# mutually seeded: build_full_analysis_efficiency_map.py optionally reads an
# existing fccee_projection.csv (only to merge in diagnostic columns -- it
# degrades gracefully to flat-efficiency seed values if that file is absent),
# while fccee_projection.py reads the efficiency map named in
# analysis/configs/fccee_zpole_inputs.json ("efficiency_corrections_csv").
#
# A repo checkout already ships a final results/fccee/fccee_projection.csv, so
# in the normal case `make efficiency-map` / `make projection` simply refresh
# both files in place using each other's *previous* output -- exactly what the
# runbook's 9.11 -> 9.12 order does. If fccee_projection.csv is missing
# entirely (e.g. results/ was wiped for a from-scratch rebuild), this bootstrap
# step builds one flat-efficiency seed first with --no-efficiency-corrections
# so the chain has something to merge against.
projection-bootstrap:
	@if [ ! -f $(RESULTS_FCCEE)/fccee_projection.csv ]; then \
		echo "No existing $(RESULTS_FCCEE)/fccee_projection.csv -- creating a flat-efficiency bootstrap seed first."; \
		$(PYTHON) analysis/fccee_projection.py \
			--config $(FCCEE_CONFIG) \
			--out-dir $(RESULTS_FCCEE) \
			--background-yields $(RESULTS_FCCEE)/fccee_background_yields.csv \
			--background-bins $(RESULTS_FCCEE)/fccee_background_bins.csv \
			--no-efficiency-corrections \
			--n-mass $(N_MASS) --n-g $(N_G); \
	fi

efficiency-map: projection-bootstrap
	@if [ ! -f $(RESULTS_FCCEE)/alp_full_analysis_efficiency_map.csv ]; then \
		echo "No existing $(RESULTS_FCCEE)/alp_full_analysis_efficiency_map.csv -- rebuilding from the Delphes scan."; \
		echo "NOTE: this reads every delphes_root path in $(RESULTS_FCCEE)/alp_full_scan_summary.csv directly," ; \
		echo "      which point at cluster-resident files (e.g. /data/alice/<user>/Axions/...). This step"; \
		echo "      only succeeds on a node where those paths resolve (the Nikhef/Stoomboot cluster)."; \
		$(PYTHON) analysis/build_full_analysis_efficiency_map.py \
			--scan-summary $(RESULTS_FCCEE)/alp_full_scan_summary.csv \
			--config $(FCCEE_CONFIG) \
			--background-bins $(RESULTS_FCCEE)/fccee_background_bins.csv \
			--projection $(RESULTS_FCCEE)/fccee_projection.csv \
			--out $(RESULTS_FCCEE)/alp_full_analysis_efficiency_map.csv \
			--summary-json $(RESULTS_FCCEE)/alp_full_analysis_efficiency_summary.json; \
	else \
		echo "Using existing $(RESULTS_FCCEE)/alp_full_analysis_efficiency_map.csv (delete it to force a rebuild from Delphes output on the cluster)."; \
	fi

projection: efficiency-map
	$(PYTHON) analysis/fccee_projection.py \
		--config $(FCCEE_CONFIG) \
		--out-dir $(RESULTS_FCCEE) \
		--background-yields $(RESULTS_FCCEE)/fccee_background_yields.csv \
		--background-bins $(RESULTS_FCCEE)/fccee_background_bins.csv \
		--n-mass $(N_MASS) --n-g $(N_G)

background-signal-examples: projection
	$(PYTHON) analysis/plot_background_signal_examples.py \
		--config $(FCCEE_CONFIG) \
		--out-png $(RESULTS_FCCEE)/background_signal_examples.png \
		--out-pdf $(RESULTS_FCCEE)/background_signal_examples.pdf \
		--summary-csv $(RESULTS_FCCEE)/background_signal_examples_summary.csv

prompt-resolved-mass-example: projection
	$(PYTHON) analysis/plot_prompt_resolved_invariant_mass.py \
		--config $(FCCEE_CONFIG) \
		--mass 0.8 \
		--coupling 8.0e-5 \
		--x-min 0.0 \
		--x-max 2.5 \
		--out $(RESULTS_FCCEE)/prompt_resolved_invariant_mass_example.png \
		--summary $(RESULTS_FCCEE)/prompt_resolved_invariant_mass_example_summary.csv

money-plots: axionlimits projection
	$(PYTHON) analysis/make_axionlimits_style_plot.py \
		--axionlimits-dir $(AXIONLIMITS_DIR) \
		--projection $(RESULTS_FCCEE)/fccee_projection.csv \
		--constraint-set full \
		--output-stem $(RESULTS_FCCEE)/money_plot_alp_full \
		--combined-output-stem $(RESULTS_FCCEE)/money_plot_alp_full_combined
	$(PYTHON) analysis/make_axionlimits_style_plot.py \
		--axionlimits-dir $(AXIONLIMITS_DIR) \
		--projection $(RESULTS_FCCEE)/fccee_projection.csv \
		--constraint-set full \
		--output-stem $(RESULTS_FCCEE)/money_plot_alp_full_closeup \
		--also-save-as $(RESULTS_FCCEE)/money_plot \
		--m-min 1e7 --m-max 1e12 --g-min 1e-8 --g-max 1e-1
	$(PYTHON) analysis/make_axionlimits_style_plot.py \
		--axionlimits-dir $(AXIONLIMITS_DIR) \
		--projection $(RESULTS_FCCEE)/fccee_projection.csv \
		--constraint-set full \
		--no-fcc-ee \
		--output-stem $(RESULTS_FCCEE)/axionlimits_alp_landscape_intro \
		--combined-output-stem $(RESULTS_FCCEE)/axionlimits_alp_landscape_intro

local-all: theory-grid belle2-closure projection background-signal-examples prompt-resolved-mass-example money-plots
	@echo ""
	@echo "Local analysis chain complete: theory grid, Belle II closure,"
	@echo "FCC-ee projection, example figures, and money plots have been rebuilt."

## ------------------------------------------------------------------------
## MC production
##
## These need the MadGraph5_aMC + Pythia8 + Delphes stack. On Nikhef that
## means `source env/setup_nikhef_lcg.sh` first; see env/README.md for
## how to point it at your own MG5ROOT. We check for the key binaries up front
## so a missing stack fails with a clear pointer instead of a raw
## "command not found" three directories deep.
## ------------------------------------------------------------------------

check-mc-tools:
	@missing=0; \
	for tool in mg5_aMC pythia8-config DelphesHepMC2 root-config; do \
		if ! command -v $$tool >/dev/null 2>&1; then \
			echo "  missing: $$tool"; missing=1; \
		fi; \
	done; \
	if [ $$missing -ne 0 ]; then \
		echo ""; \
		echo "The MC stack (MadGraph5_aMC, Pythia8, Delphes, ROOT) is not on PATH."; \
		echo "On Nikhef:   source env/setup_nikhef_lcg.sh"; \
		echo "Details:     env/README.md and mc/README.md"; \
		exit 1; \
	fi

smoke-test: check-mc-tools
	cd mc/hepmc_smoke_test && \
		./run_mg5_to_delphes_smoke_test.sh work 1000 100.0 \
			../../mc/delphes_cards/delphes_card_belle2_validation.tcl
	$(PYTHON) theory/predictions/validate.py mc/hepmc_smoke_test/work --pipeline-smoke

signal-point-belle2: check-mc-tools
	mc/alp_signal/run_alp_full_pipeline.sh \
		results/alp_full_pipeline/example_belle2 \
		1000 10.58 1.0 1e-5 \
		mc/delphes_cards/delphes_card_Belle2.tcl \
		resolved_prompt

signal-point-fccee: check-mc-tools
	mc/alp_signal/run_alp_full_pipeline.sh \
		results/alp_full_pipeline/example_fccee \
		1000 91.2 1.0 1e-5 \
		mc/delphes_cards/delphes_card_IDEA.tcl \
		resolved_prompt

background-points: check-mc-tools
	mc/backgrounds/run_sm_background_full_pipeline.sh \
		results/backgrounds/resolved_3gamma \
		resolved_3gamma 10000 91.2 \
		mc/delphes_cards/delphes_card_IDEA.tcl
	mc/backgrounds/run_sm_background_full_pipeline.sh \
		results/backgrounds/invisible_gamma_nunu \
		invisible_gamma_nunu 10000 91.2 \
		mc/delphes_cards/delphes_card_IDEA.tcl

## ------------------------------------------------------------------------
## HTCondor batch submission  (Nikhef/Stoomboot only)
##
## condor_submit schedules jobs and returns immediately -- it does not block
## until they finish, so these targets cannot be chained into "make
## local-all". Collect the results with `make collect-scan` once Condor
## shows the campaign as done (`condor_q`), then continue with
## `make efficiency-map` / `make projection`.
##
## NOTE: HTCondor requires the log/output/error directories named in each
## .sub file to exist *before* submission -- it will not create them. The
## shipped submit files default to the campaigns documented in
## condor/README.md (their log dirs are pre-created); for any other
## --campaign name, `mkdir -p logs/<category>/<campaign>` first.
## ------------------------------------------------------------------------

condor-background-scan:
	@command -v condor_submit >/dev/null 2>&1 || { \
		echo "condor_submit not found -- this target only runs on a Nikhef/Stoomboot submit node."; \
		echo "See condor/README.md."; \
		exit 1; }
	condor_submit condor/submit_background_scan.sub

condor-signal-scan:
	@command -v condor_submit >/dev/null 2>&1 || { \
		echo "condor_submit not found -- this target only runs on a Nikhef/Stoomboot submit node."; \
		echo "See condor/README.md."; \
		exit 1; }
	condor_submit condor/submit_alp_full_projection_scan.sub

# CAMPAIGN must match the campaign directory under results/alp_full_production/
# that Condor wrote into, e.g.:
#   make collect-scan CAMPAIGN=fccee_z_full_projection_fullbg_channelaware
CAMPAIGN ?= fccee_z_full_projection_fullbg_channelaware
collect-scan:
	$(PYTHON) analysis/collect_alp_full_scan.py \
		results/alp_full_production/$(CAMPAIGN) \
		--out $(RESULTS_FCCEE)/alp_full_scan_summary.csv \
		--summary-json $(RESULTS_FCCEE)/alp_full_scan_summary.json

## ------------------------------------------------------------------------
## Misc
## ------------------------------------------------------------------------

status:
	@echo "Locked configs:"
	@for f in $(FCCEE_CONFIG) $(BELLE2_CONFIG) analysis/configs/axionlimits_source.json; do \
		[ -f $$f ] && echo "  [present] $$f" || echo "  [MISSING] $$f"; \
	done
	@echo ""
	@echo "Key checked-in outputs:"
	@for f in theory/predictions/theory_grid.csv \
	          results/belle2_closure/belle2_closure_summary.json \
	          $(RESULTS_FCCEE)/fccee_background_yields.csv \
	          $(RESULTS_FCCEE)/fccee_background_bins.csv \
	          $(RESULTS_FCCEE)/alp_full_scan_summary.csv \
	          $(RESULTS_FCCEE)/alp_full_analysis_efficiency_map.csv \
	          $(RESULTS_FCCEE)/fccee_projection.csv \
	          $(RESULTS_FCCEE)/fccee_zpole_signature_classification.csv \
	          $(RESULTS_FCCEE)/money_plot.png \
	          $(RESULTS_FCCEE)/axionlimits_alp_landscape_intro.png; do \
		[ -f $$f ] && echo "  [present] $$f" || echo "  [MISSING] $$f"; \
	done
	@echo ""
	@if [ -d "$(AXIONLIMITS_DIR)/.git" ]; then echo "external/AxionLimits: present"; \
	else echo "external/AxionLimits: not cloned (run 'make axionlimits')"; fi
	@if [ -d "$(VENV)" ]; then echo "$(VENV): present"; \
	else echo "$(VENV): not created (run 'make venv')"; fi

clean-pyc:
	find . -path ./.venv -prune -o -path ./external -prune -o \
		\( -name '__pycache__' -type d -print -exec rm -rf {} + \) 2>/dev/null || true
	find . -path ./.venv -prune -o -path ./external -prune -o \
		\( -name '*.py[co]' -type f -print -delete \) 2>/dev/null || true
