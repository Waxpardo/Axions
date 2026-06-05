#!/usr/bin/env bash
# ============================================================================
# Stage-1 FCC-ee SM background:  MadGraph multi-process generation
# ============================================================================
#
# Purpose (physics): generates 5000 parton-level events across eight SM
# processes at sqrt(s)=240 GeV with a fixed random seed (12345), weighted
# by their cross sections. The mixture approximates the FCC-ee collision
# environment: WW pairs dominate (~55%), followed by light quark pairs
# (~23%), lepton pairs (~12%), neutrino pairs (~5%), and diboson/ZH (~5%).
# Purpose (software): first multi-process MG5 run in this repo; the output
# LHE contains events from all processes, each labelled by process ID so
# Pythia and downstream analyses can separate them.
#
# Metadata: after MG5 completes, this script writes a JSON sidecar
# (metadata_sm_fcc.json) capturing per-process cross sections, beam
# settings, software versions, seed, and luminosity equivalent.
#
# Usage (run on NIKHEF after review -- not executed automatically):
#   bash mc/gen_background_sm_fcc.sh
# ----------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

CARD="mc/cards/background_sm_fcc/mg5_sm_fcc.dat"
PROC_DIR="PROC_background_sm_fcc"
RUN_DIR="${PROC_DIR}/Events/run_01"

echo ">>> Sourcing environment (env/setup_lcg105.sh)"
set +u
# shellcheck disable=SC1091
source env/setup_lcg105.sh
set -u

if ! command -v mg5_aMC >/dev/null 2>&1; then
  echo "ERROR: mg5_aMC not on PATH after sourcing env/setup_lcg105.sh" >&2
  exit 1
fi

MG5_VERSION="$(readlink -f "$(which mg5_aMC 2>/dev/null)" 2>/dev/null | grep -oP 'madgraph5amc/\K[^/]+' || echo 'unknown')"
PYTHIA8_VERSION="$(grep 'versionNumber' "$(pythia8-config --xmldoc 2>/dev/null)/Version.xml" 2>/dev/null | grep -oP 'default="\K[^"]+' | head -1 || echo 'unknown')"
ROOT_VERSION="$(root-config --version 2>/dev/null || echo 'unknown')"
DELPHES_VERSION="3.5.0-local-root${ROOT_VERSION}"

echo ">>> MadGraph version : $MG5_VERSION"
echo ">>> Pythia8 version  : $PYTHIA8_VERSION"
echo ">>> ROOT version     : $ROOT_VERSION"
echo ">>> Card             : $CARD"
echo ">>> Output dir       : $PROC_DIR"

echo ">>> Running MadGraph"
mg5_aMC "$CARD"

# -----------------------------------------------------------------------
# Parse per-process cross sections from MG5 banner
# MG5 writes lines like:
#   #  Process: e+ e- > j j  WEIGHTED=...
#   #  Integrated weight (pb)  : 6.234e+00
# The banner also contains a summary table. We extract the total and per-
# process cross sections from the run_01_tag_1_banner.txt file.
# -----------------------------------------------------------------------
BANNER="${RUN_DIR}/run_01_tag_1_banner.txt"
LHE="${RUN_DIR}/unweighted_events.lhe.gz"

echo
echo "==================== Stage-1 FCC-ee SM background summary ===================="

TOTAL_XSEC="unknown"
if [[ -f "$BANNER" ]]; then
  echo "Banner: $BANNER"
  echo
  echo "Cross-sections from run banner:"
  # Print the integrated weight line(s)
  grep -i "Integrated weight\|cross.section\|#  Process" "$BANNER" | head -40 || true
  TOTAL_XSEC="$(grep -i 'Integrated weight' "$BANNER" | tail -1 | awk '{print $NF}' || echo 'unknown')"
else
  echo "WARNING: banner not found at $BANNER"
  echo "  Check ${PROC_DIR}/crossx.html or the MadGraph terminal output above."
fi

echo
if [[ -f "$LHE" ]]; then
  echo "Parton-level LHE: $LHE  ($(du -sh "$LHE" | cut -f1))"
else
  echo "WARNING: expected LHE not found at $LHE"
fi

# -----------------------------------------------------------------------
# Write metadata sidecar (filled with runtime values)
# -----------------------------------------------------------------------
META="${RUN_DIR}/metadata_sm_fcc.json"
mkdir -p "$RUN_DIR"
cat > "$META" <<METAEOF
{
  "description": "FCC-ee SM inclusive background -- Stage-1 parton-level LHE",
  "processes": [
    "e+e- -> j j  (light quarks: u d s c)",
    "e+e- -> b b~",
    "e+e- -> mu+ mu-",
    "e+e- -> ta+ ta-",
    "e+e- -> vl vl~ (all three nu flavours)",
    "e+e- -> w+ w-",
    "e+e- -> z z",
    "e+e- -> z h"
  ],
  "model": "sm (MG5 built-in, no UFO)",
  "ebeam1_GeV": 120,
  "ebeam2_GeV": 120,
  "sqrts_GeV": 240,
  "nevents_requested": 5000,
  "random_seed": 12345,
  "filter_cuts": "none (ptj=ptb=ptl=0, etal=-1, drll=drjl=mmll=0)",
  "luminosity_target_ab": 5.0,
  "mass_point_GeV": null,
  "coupling_point": null,
  "total_xsec_pb": "${TOTAL_XSEC}",
  "xsec_per_process_pb": "see banner at ${BANNER}",
  "mg5_version": "${MG5_VERSION}",
  "pythia8_version": "${PYTHIA8_VERSION}",
  "root_version": "${ROOT_VERSION}",
  "delphes_version": "${DELPHES_VERSION}",
  "lhe_file": "${LHE}",
  "banner_file": "${BANNER}"
}
METAEOF

echo
echo "Metadata sidecar : $META"
echo
echo "Process mix (approximate, proportional to cross section):"
echo "  WW        ~15 pb  -> ~55% of events"
echo "  jj        ~6  pb  -> ~22%"
echo "  mu+mu-    ~1.7 pb -> ~6%"
echo "  ta+ta-    ~1.7 pb -> ~6%"
echo "  vl vl~    ~1.5 pb -> ~5%"
echo "  bb~       ~1  pb  -> ~4%"
echo "  ZZ        ~1  pb  -> ~4%"
echo "  ZH        ~0.22 pb -> ~0.8%  (H decays via Pythia8)"
echo
echo "Next: bash mc/shower_background_sm_fcc.sh"
echo "=============================================================================="
