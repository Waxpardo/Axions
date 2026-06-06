#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"

work_dir="${1:-${repo_root}/results/alp_full_pipeline/fccee_zpole_m1_g1em5_n500}"
n_events="${2:-500}"
m_a_gev="${3:-1.0}"
g_agg="${4:-1e-5}"

"${script_dir}/run_alp_full_pipeline.sh" \
  "${work_dir}" \
  "${n_events}" \
  91.2 \
  "${m_a_gev}" \
  "${g_agg}" \
  "${repo_root}/mc/delphes_cards/delphes_card_IDEA.tcl"
