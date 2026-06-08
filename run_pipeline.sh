#!/bin/bash

RUN_NAME="${1}"
LHE_INPUT_PATH="${2}"

BASE_DIR="/data/alice/cwydeman/Axions"
if [ -z "$RUN_NAME" ] || [ -z "$LHE_INPUT_PATH" ]; then
    echo "Error: Missing arguments!"
    exit 1
fi

# 1. Define the absolute path to your base directory
BASE_DIR="/data/alice/cwydeman/Axions"
# Define absolute paths to your executables
RUN_PYTHIA="/data/alice/cwydeman/Axions/run_pythia"
ANALYSE_HEPMC="/data/alice/cwydeman/Axions/analyse_hepmc"

LHE_ABS_PATH=$(readlink -f "$LHE_INPUT_PATH")

echo "==> Starting pipeline for: $RUN_NAME"

source "$BASE_DIR/setupEnv.sh"

TARGET_DIR="$BASE_DIR/$RUN_NAME/Events/run_01"
mkdir -p "$TARGET_DIR"

ln -sf "$LHE_ABS_PATH" "$TARGET_DIR/unweighted_events.lhe"
if [ ! -f "$TARGET_DIR/unweighted_events.lhe" ]; then
    echo "CRITICAL ERROR: LHE file link failed at $TARGET_DIR/unweighted_events.lhe"
    exit 1
fi

cd "$TARGET_DIR" || exit 1

echo "==> Running Pythia..."
"$RUN_PYTHIA" 

echo "==> Running Analysis..."
"$ANALYSE_HEPMC"

echo "==> Pipeline complete. Files are in: $TARGET_DIR/"