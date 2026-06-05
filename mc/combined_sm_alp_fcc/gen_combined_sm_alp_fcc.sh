#!/usr/bin/env bash
# ============================================================================
# Stage-1 COMBINED FCC-ee SM+ALP:  MadGraph multi-process generation
# ============================================================================
#
# Generates the combined sample (8 SM channels + gamma gamma / gamma gamma gamma
# / Z gamma photon backgrounds + ALP signal) in a single MG5 process directory
# at sqrt(s)=240 GeV. Two variants:
#
#   honest   (default) -- physical couplings (KB=KW=1). sigma(ALP)/sigma(SM)
#                         ~5e-8, so expect ~0 ALP events in the unweighted LHE.
#   boosted            -- KB=KW=2000 (NON-PHYSICAL, validation only) so the
#                         sample contains ~170 ALP events for pipeline testing.
#
# After MG5 this script: parses the total cross section + uncertainty, counts
# ALP-tagged events (PDG 9999) in the LHE, copies the exact input cards into
# the run directory, records the git commit, and writes a full metadata JSON.
#
# Usage (run on NIKHEF after review -- not executed automatically):
#   bash mc/combined_sm_alp_fcc/gen_combined_sm_alp_fcc.sh [honest|boosted]
# ----------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

VARIANT="${1:-honest}"
case "$VARIANT" in
  honest)
    CARD_TEMPLATE="mc/cards/combined_sm_alp_fcc/mg5_combined_sm_alp_fcc.dat"
    PROC_DIR="PROC_combined_sm_alp_fcc" ;;
  boosted)
    CARD_TEMPLATE="mc/cards/combined_sm_alp_fcc/mg5_combined_sm_alp_fcc_boosted.dat"
    PROC_DIR="PROC_combined_sm_alp_fcc_boosted" ;;
  *)
    echo "ERROR: unknown variant '$VARIANT' (use 'honest' or 'boosted')" >&2
    exit 1 ;;
esac

RUN_DIR="${PROC_DIR}/Events/run_01"
PYTHIA_CMND="mc/cards/combined_sm_alp_fcc/pythia8_combined_sm_alp_fcc.cmnd"
DELPHES_CARD="mc/delphes_cards/fcc_idea/card_IDEA_winter2023_sm_bkg.tcl"
COUNT_ALP="analysis/combined_sm_alp_fcc/count_alp_lhe.py"

echo ">>> Variant : $VARIANT"
echo ">>> Card    : $CARD_TEMPLATE"
echo ">>> Output  : $PROC_DIR"

echo ">>> Sourcing environment (env/setup_lcg105.sh)"
set +u
# shellcheck disable=SC1091
source env/setup_lcg105.sh
set -u

if ! command -v mg5_aMC >/dev/null 2>&1; then
  echo "ERROR: mg5_aMC not on PATH after sourcing env/setup_lcg105.sh" >&2
  exit 1
fi

# --- Resolve the SM_alp_UFO model path at runtime (token __MODEL_PATH__) ----
MODEL_PATH="${REPO_ROOT}/models/SM_alp_UFO"
if [[ ! -d "$MODEL_PATH" ]]; then
  echo "ERROR: ALP UFO model not found at $MODEL_PATH" >&2
  exit 1
fi
TMPCARD=$(mktemp /tmp/mg5_combined_XXXXXX.dat)
trap 'rm -f "$TMPCARD"' EXIT
sed "s|__MODEL_PATH__|${MODEL_PATH}|g" "$CARD_TEMPLATE" > "$TMPCARD"

# --- Software versions (after env is sourced) ------------------------------
MG5_VERSION="$(readlink -f "$(which mg5_aMC 2>/dev/null)" 2>/dev/null | grep -oP 'madgraph5amc/\K[^/]+' || echo 'unknown')"
PYTHIA8_VERSION="$(grep 'versionNumber' "$(pythia8-config --xmldoc 2>/dev/null)/Version.xml" 2>/dev/null | grep -oP 'default="\K[^"]+' | head -1 || echo 'unknown')"
ROOT_VERSION="$(root-config --version 2>/dev/null || echo 'unknown')"
DELPHES_VERSION="3.5.0-local-root${ROOT_VERSION}"
GIT_COMMIT="$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo 'unknown')"

echo ">>> MadGraph version : $MG5_VERSION"
echo ">>> Pythia8 version  : $PYTHIA8_VERSION"
echo ">>> ROOT version     : $ROOT_VERSION"
echo ">>> git commit       : $GIT_COMMIT"

# --- Run MadGraph (tee to a log so we can parse the cross-section summary) --
MG5_LOG="${PROC_DIR}_mg5_run.log"
echo ">>> Running MadGraph (log: $MG5_LOG)"
mg5_aMC "$TMPCARD" 2>&1 | tee "$MG5_LOG"

BANNER="${RUN_DIR}/run_01_tag_1_banner.txt"
LHE="${RUN_DIR}/unweighted_events.lhe.gz"
CROSSX="${PROC_DIR}/crossx.html"

# --- Helper: read a 'set NAME VALUE' value straight from the card ----------
card_val() { grep -E "^[[:space:]]*set[[:space:]]+$1[[:space:]]" "$CARD_TEMPLATE" | head -1 | awk '{print $3}'; }

NEVENTS=$(card_val nevents); SEED=$(card_val iseed)
MALP=$(card_val Malp);       FA=$(card_val fa)
KB=$(card_val KB);           KW=$(card_val KW)
KG=$(card_val Kg);           CTA=$(card_val Cta)
CB=$(card_val Cb);           CT=$(card_val Ct)
PTA=$(card_val pta);         ETAA=$(card_val etaa);   DRAA=$(card_val draa)

# --- Cross section + uncertainty -------------------------------------------
# MG5 prints "Cross-section :   <val> +- <err> pb" in the run summary; fall
# back to the banner's "Integrated weight (pb)" central value.
TOTAL_XSEC="$(grep -iE 'Cross-section\s*:' "$MG5_LOG" | tail -1 | grep -oP ':\s*\K[0-9.eE+-]+' || echo '')"
XSEC_ERR="$(grep -iE 'Cross-section\s*:' "$MG5_LOG" | tail -1 | grep -oP '\+-\s*\K[0-9.eE+-]+' || echo '')"
if [[ -z "$TOTAL_XSEC" && -f "$BANNER" ]]; then
  TOTAL_XSEC="$(grep -i 'Integrated weight' "$BANNER" | tail -1 | awk '{print $NF}' || echo 'unknown')"
fi
[[ -z "$TOTAL_XSEC" ]] && TOTAL_XSEC="unknown"
[[ -z "$XSEC_ERR"   ]] && XSEC_ERR="unknown"

# --- Count ALP-tagged events (PDG 9999) in the LHE -------------------------
N_ALP="unknown"; N_TOT="unknown"; N_DEC="unknown"; FRAC="n/a"
if [[ -f "$LHE" ]]; then
  ALP_OUT="$(python "$COUNT_ALP" "$LHE" 2>/dev/null || true)"
  N_ALP="$(echo "$ALP_OUT" | grep '^ALP_EVENTS='        | cut -d= -f2 || echo 'unknown')"
  N_TOT="$(echo "$ALP_OUT" | grep '^TOTAL_EVENTS='      | cut -d= -f2 || echo 'unknown')"
  N_DEC="$(echo "$ALP_OUT" | grep '^ALP_DECAY_PHOTONS=' | cut -d= -f2 || echo 'unknown')"
  [[ -z "$N_ALP" ]] && N_ALP="unknown"
  [[ -z "$N_TOT" ]] && N_TOT="unknown"
  [[ -z "$N_DEC" ]] && N_DEC="unknown"
  FRAC="$(awk -v a="$N_ALP" -v t="$N_TOT" 'BEGIN{ if (t+0>0) printf "%.4f", a/t; else print "n/a" }' 2>/dev/null || echo 'n/a')"
fi

# --- Copy the exact input cards into the run dir for provenance ------------
CARDS_USED="${RUN_DIR}/cards_used"
mkdir -p "$CARDS_USED"
cp "$TMPCARD"      "${CARDS_USED}/mg5_card_resolved.dat" 2>/dev/null || true
cp "$CARD_TEMPLATE" "${CARDS_USED}/$(basename "$CARD_TEMPLATE")" 2>/dev/null || true
cp "$PYTHIA_CMND"  "${CARDS_USED}/$(basename "$PYTHIA_CMND")" 2>/dev/null || true
cp "$DELPHES_CARD" "${CARDS_USED}/$(basename "$DELPHES_CARD")" 2>/dev/null || true

# --- Write metadata sidecar -------------------------------------------------
META="${RUN_DIR}/metadata_combined_sm_alp_fcc.json"
mkdir -p "$RUN_DIR"
cat > "$META" <<METAEOF
{
  "description": "FCC-ee COMBINED SM background + ALP signal -- Stage-1 parton-level LHE",
  "variant": "${VARIANT}",
  "variant_note": "honest = physical couplings (expect ~0 ALP events); boosted = KB=KW raised, NON-PHYSICAL, validation only",
  "processes": [
    "e+e- > j j  (light quarks u d s c + gluon)",
    "e+e- > b b~",
    "e+e- > mu+ mu-",
    "e+e- > ta+ ta-",
    "e+e- > vl vl~ (all three nu flavours)",
    "e+e- > w+ w-",
    "e+e- > z z",
    "e+e- > z h",
    "e+e- > a a    CK=0  (pure-SM gamma gamma)",
    "e+e- > a a a  CK=0  (pure-SM gamma gamma gamma)",
    "e+e- > z a    CK=0  (pure-SM Z gamma)",
    "e+e- > alp a, alp > a a  (ALP signal, the only CK!=0 line)"
  ],
  "process_definition_card": "${CARD_TEMPLATE}",
  "model": "SM_alp_UFO",
  "model_path": "${MODEL_PATH}",
  "ebeam1_GeV": 120,
  "ebeam2_GeV": 120,
  "sqrts_GeV": 240,
  "nevents_requested": ${NEVENTS:-null},
  "random_seed": ${SEED:-null},
  "filter_cuts": "jets/leptons uncut (ptj=ptb=ptl=0, etal=-1); photons pta=${PTA}, etaa=${ETAA}, draa=${DRAA}",
  "luminosity_target_ab": 5.0,
  "mass_point_GeV": ${MALP:-null},
  "coupling_point": {
    "fa_GeV": ${FA:-null},
    "KB": ${KB:-null},
    "KW": ${KW:-null},
    "Kg": ${KG:-null},
    "Cta": ${CTA:-null},
    "Cb": ${CB:-null},
    "Ct": ${CT:-null}
  },
  "total_xsec_pb": "${TOTAL_XSEC}",
  "xsec_uncertainty_pb": "${XSEC_ERR}",
  "xsec_per_process": "authoritative per-subprocess values in ${CROSSX}",
  "n_alp_events_in_lhe": "${N_ALP}",
  "n_total_events_in_lhe": "${N_TOT}",
  "n_alp_decay_photons_in_lhe": "${N_DEC}",
  "fraction_events_with_alp": "${FRAC}",
  "mg5_version": "${MG5_VERSION}",
  "pythia8_version": "${PYTHIA8_VERSION}",
  "root_version": "${ROOT_VERSION}",
  "delphes_version": "${DELPHES_VERSION}",
  "detector_card": "${DELPHES_CARD}",
  "git_commit": "${GIT_COMMIT}",
  "lhe_file": "${LHE}",
  "banner_file": "${BANNER}",
  "crossx_html": "${CROSSX}",
  "mg5_log": "${MG5_LOG}",
  "cards_used_dir": "${CARDS_USED}"
}
METAEOF

# --- Report -----------------------------------------------------------------
echo
echo "================ Stage-1 COMBINED SM+ALP summary ($VARIANT) ================"
echo "Total cross section : ${TOTAL_XSEC} +- ${XSEC_ERR} pb"
if [[ -f "$LHE" ]]; then
  echo "Parton-level LHE    : $LHE  ($(du -sh "$LHE" 2>/dev/null | cut -f1))"
else
  echo "WARNING: expected LHE not found at $LHE"
fi
echo
echo "Truth-level ALP accounting"
echo "  Generated events:            ${N_TOT}"
echo "  Events containing ALP:       ${N_ALP}"
echo "  ALP decay photons found:     ${N_DEC}"
echo "  Fraction of events with ALP: ${FRAC}"
echo
if [[ "$VARIANT" == "honest" ]]; then
  echo "  -> honest variant: ~0 ALP events expected (sigma ratio ~5e-8). This is"
  echo "     a statistical-mixture certainty, NOT a failure. Use 'boosted' to"
  echo "     populate the pipeline with ALP events for end-to-end validation."
else
  echo "  -> boosted variant: expect ~170 ALP events (NON-PHYSICAL coupling)."
fi
echo "Metadata sidecar    : $META"
echo "Cards archived in    : $CARDS_USED"
echo "Per-process xsec     : $CROSSX"
echo
echo "Next: bash mc/combined_sm_alp_fcc/shower_combined_sm_alp_fcc.sh $VARIANT"
echo "============================================================================"
