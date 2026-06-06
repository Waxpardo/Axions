#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./run_alp_gate2_width.sh [work_dir] [m_a_GeV] [g_agg_GeV_inv] [param_card]

Runs Gate 2 for the ALP UFO with MG5/MadWidth:
  compute_widths alp --body_decay=2 --path=<param_card> --output=<computed_card>

If param_card is omitted, one is generated with mc/make_param_card.py using the
project's production-normalized g_agg -> fa/KB/KW mapping and physical 64pi
width. The JSON summary compares:
  - input DECAY 9999 width
  - MG5 compute_widths DECAY 9999 width
  - theory Gamma = g_agg^2 m_a^3 / (64 pi)
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/../.." && pwd)"

work_dir="${1:-${script_dir}/gate2_width}"
m_a_gev="${2:-1.0}"
g_agg="${3:-1e-5}"
input_param_card="${4:-}"

if ! command -v mg5_aMC >/dev/null 2>&1; then
  echo "mg5_aMC not found. Source env/setup_nikhef_lcg.sh first." >&2
  exit 1
fi

mkdir -p "${work_dir}"

if [[ -z "${input_param_card}" ]]; then
  input_param_card="${work_dir}/param_card_input.dat"
  python3 "${repo_root}/mc/make_param_card.py" \
    --out "${input_param_card}" \
    --m-a "${m_a_gev}" \
    --g-agg "${g_agg}" \
    --width-mode physical
fi

if [[ ! -f "${input_param_card}" ]]; then
  echo "Param card not found: ${input_param_card}" >&2
  exit 1
fi

model_path="${repo_root}/models/ALP_linear/SM_alp_UFO"
command_card="${work_dir}/compute_widths.mg5"
computed_card="${work_dir}/param_card_mg5_compute_widths.dat"
log_path="${work_dir}/compute_widths.log"
summary_path="${work_dir}/gate2_width_summary.json"

cat > "${command_card}" <<EOF
import model ${model_path}
set automatic_html_opening False
compute_widths alp --body_decay=2 --path=${input_param_card} --output=${computed_card}
quit
EOF

mg5_aMC "${command_card}" | tee "${log_path}"

python3 - "${input_param_card}" "${computed_card}" "${summary_path}" "${m_a_gev}" "${g_agg}" <<'PY'
import json
import math
import re
import sys
from pathlib import Path

input_card = Path(sys.argv[1])
computed_card = Path(sys.argv[2])
summary_path = Path(sys.argv[3])
m_a = float(sys.argv[4])
g_agg = float(sys.argv[5])

decay_re = re.compile(r"^\s*DECAY\s+9999\s+([-+0-9.eE]+)", re.MULTILINE)

def parse_width(path: Path) -> float:
    text = path.read_text()
    match = decay_re.search(text)
    if not match:
        raise SystemExit(f"Could not parse DECAY 9999 from {path}")
    return float(match.group(1))

theory_width = g_agg * g_agg * m_a**3 / (64.0 * math.pi)
input_width = parse_width(input_card)
mg5_width = parse_width(computed_card)

summary = {
    "mode": "gate2_mg5_compute_widths",
    "m_a_GeV": m_a,
    "g_agg_GeV_inv": g_agg,
    "input_param_card": str(input_card),
    "computed_param_card": str(computed_card),
    "input_width_GeV": input_width,
    "mg5_compute_width_GeV": mg5_width,
    "theory_width_64pi_GeV": theory_width,
    "input_ratio_to_64pi": input_width / theory_width if theory_width else math.inf,
    "mg5_ratio_to_64pi": mg5_width / theory_width if theory_width else math.inf,
    "input_passed_64pi": abs(input_width / theory_width - 1.0) < 0.05 if theory_width else False,
    "mg5_passed_64pi": abs(mg5_width / theory_width - 1.0) < 0.05 if theory_width else False,
    "mg5_passed_128pi": abs(mg5_width / theory_width - 0.5) < 0.05 if theory_width else False,
}
mg5_ratio = summary["mg5_ratio_to_64pi"]
if abs(mg5_ratio - 1.0) < 0.05:
    summary["mg5_convention"] = "64pi"
elif abs(mg5_ratio - 0.5) < 0.05:
    summary["mg5_convention"] = "128pi"
elif abs(mg5_ratio - 2.0) < 0.05:
    summary["mg5_convention"] = "ufo_direct_width_2x_64pi"
else:
    summary["mg5_convention"] = "unresolved"

summary["gate2_resolved"] = (
    summary["input_passed_64pi"]
    and summary["mg5_convention"] in {"64pi", "128pi", "ufo_direct_width_2x_64pi"}
)
summary_path.write_text(json.dumps(summary, indent=2) + "\n")

print(f"Wrote {summary_path}")
for key, value in summary.items():
    print(f"{key}: {value}")
PY

echo
echo "==================== Gate 2 width summary ===================="
echo "input card    : ${input_param_card}"
echo "computed card : ${computed_card}"
echo "summary       : ${summary_path}"
echo "log           : ${log_path}"
echo "==============================================================="
