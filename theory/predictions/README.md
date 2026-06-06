# Analytic predictions and MC validation

This directory holds analytic grids for cross sections, lifetimes, decay
lengths, recoil photon energies, and photon opening angles.

## Build the theory grid

From the repository root:

```bash
python theory/predictions/predict_grid.py \
  --out theory/predictions/theory_grid.csv
```

Useful single-run examples:

```bash
python theory/predictions/predict_grid.py \
  --sqrt-s 10.58 \
  --out theory/predictions/theory_grid_belle2.csv

python theory/predictions/predict_grid.py \
  --sqrt-s 91.2 \
  --out theory/predictions/theory_grid_fccee.csv
```

Belle II and FCC-ee detector lengths are independent CLI parameters. The FCC-ee
defaults are currently set equal to the Belle II values until IDEA values are
locked:

```bash
python theory/predictions/predict_grid.py \
  --belle2-l-min 0.14 \
  --belle2-l-max 1.55 \
  --fccee-l-min 0.14 \
  --fccee-l-max 1.55 \
  --out theory/predictions/theory_grid.csv
```

The analysis-facing columns are:

```text
sigma_pb
ell_a_m
P_survive_Lmax
P_decay_det
L_min_m
L_max_m
```

The grid also includes a `detector` label. For the default Belle II and FCC-ee
Z-pole grid this is `BelleII` and `FCCee_Z`. The FCC-ee detector lengths are
currently set equal to Belle II values until IDEA values are locked, but they
can already be changed independently with `--fccee-l-min` and `--fccee-l-max`.

## Validate one MC point

The validator understands the MC common output names:

```text
banner.txt
*_banner.txt
unweighted_events.lhe.gz
events.hepmc
width.txt
param_card.dat
run_card.dat
```

Run:

```bash
python theory/predictions/validate.py <run_dir> \
  --m-a <mass_GeV> \
  --g <g_agg_GeV_inv> \
  --sqrt-s <sqrt_s_GeV> \
  --alp-pdg-id 9999
```

If `<run_dir>` contains `param_card.dat` and `run_card.dat`, the script can infer
`m_a`, `sqrt_s`, and the UFO-derived `g_agg` from `fa`, `KB`, and `KW`.

For the ALP production pipeline, prefer passing the physical coupling used to
write the point:

```bash
python theory/predictions/validate.py <run_dir> \
  --m-a <mass_GeV> \
  --g <g_agg_GeV_inv> \
  --sqrt-s <sqrt_s_GeV> \
  --alp-pdg-id 9999
```

This is the handoff expected once `mc/make_param_card.py` writes each production
point: the same physical `(m_a, g_agg)` values should be sent to MadGraph and to
this validator. For `SM_alp_UFO`, Gate 1 fixes the production-normalized mapping
to:

```text
g_agg = alpha_em * (KB + KW) / (sqrt(2) * pi * fa)
```

When `mc/make_param_card.py --g-agg` is used, the default `KB/KW` split cancels
the tree-level `gamma Z alp` coupling so the production point is aligned with
the photophilic associated-production validation formula.

The direct UFO decay-width normalization is also reported as
`g_agg_ufo_width_GeV_inv` and is reserved for Gate 2 width/lifetime diagnostics.

Current Gate 2 result for `SM_alp_UFO`: with the Gate-1 production-normalized
mapping, MG5 `compute_widths alp` returns a two-body ALP width that is `2x` the
project `64pi` width. The production pipeline therefore writes the project
`64pi` width into `DECAY 9999` and passes that same width to Pythia. Run:

```bash
mc/alp_signal/run_alp_gate2_width.sh <work_dir> <m_a_GeV> <g_agg_GeV_inv> <param_card>
```

to reproduce the convention check.

## Gate 3: Belle II closure

The published-contour Belle II closure is integrated into the central validator:

```bash
python theory/predictions/validate.py \
  --belle2-closure \
  --axionlimits-dir external/AxionLimits
```

The command writes the closure plot, contour CSV, report, and JSON summary to:

```text
results/belle2_closure/
```

It passes when the reconstructed contour agrees with the digitized Belle II
boundary within the tolerance in
`analysis/configs/belle2_closure_inputs.json`.

Example with the current Belle II smoke-test banner:

```bash
python theory/predictions/validate.py belleII_alp_testrun10k
```
