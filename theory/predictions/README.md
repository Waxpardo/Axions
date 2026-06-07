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

Belle II and FCC-ee detector lengths are independent CLI parameters. The IDEA
values are now locked (matching `analysis/configs/fccee_zpole_inputs.json`:
`l_min_m: 0.02`, `l_max_m: 2.5`), and the FCC-ee defaults in `predict_grid.py`
match them:

```bash
python theory/predictions/predict_grid.py \
  --belle2-l-min 0.14 \
  --belle2-l-max 1.55 \
  --fccee-l-min 0.02 \
  --fccee-l-max 2.5 \
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
the locked IDEA values (`0.02`/`2.5` m), independent of the Belle II values
(`0.14`/`1.55` m), and can still be overridden with `--fccee-l-min` and
`--fccee-l-max` if needed.

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
$m_a$, $\sqrt{s}$, and the UFO-derived $g_{a\gamma\gamma}$ from `fa`, `KB`, and
`KW`.

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
point: the same physical $(m_a,g_{a\gamma\gamma})$ values should be sent to
MadGraph and to this validator. For `SM_alp_UFO`, Gate 1 fixes the
production-normalized mapping to:

$$
g_{a\gamma\gamma}=
\frac{\alpha_{\mathrm{em}}(K_B+K_W)}
{\sqrt{2}\,\pi f_a}.
$$

When `mc/make_param_card.py --g-agg` is used, the default `KB/KW` split cancels
the tree-level $\gamma Z a$ coupling so the production point is aligned with
the photophilic associated-production validation formula.

The direct UFO decay-width normalization is also reported as
`g_agg_ufo_width_GeV_inv` and is reserved for Gate 2 width/lifetime diagnostics.

Current Gate 2 result for `SM_alp_UFO`: with the Gate-1 production-normalized
mapping, MG5 `compute_widths alp` returns a two-body ALP width that is
$2\times$ the project `64pi` width. The production pipeline therefore writes the project
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

Example with a full ALP pipeline output directory:

```bash
python theory/predictions/validate.py results/alp_full_pipeline/example_belle2
```

Raw full-pipeline output directories are ignored by git; regenerate them with
`make signal-point-belle2` or the explicit `mc/alp_signal/run_alp_full_pipeline.sh`
command when you need this detector-level validation locally.
