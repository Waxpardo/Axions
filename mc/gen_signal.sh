#!/usr/bin/env bash
set -euo pipefail
echo "STARTING AUTOMATED MUON SIGNAL GENERATION"

# 1. Clean the old run folder out completely to ensure a fresh sample
rm -rf /data/alice/egrivas/Axions/belleII_alp/Events/run_01/

# 2. Run MadGraph in silent batch mode using our command script
mg5_aMC /data/alice/egrivas/Axions/mc/mg5_commands.txt

echo "SIGNAL GENERATION COMPLETE! run_01 IN PLACE"

