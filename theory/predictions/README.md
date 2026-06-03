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
`m_a` and `sqrt_s`. If `--g` is omitted, it reports a UFO-based estimate from
`fa`, `KB`, and `KW`, but that mapping must be locked with Gate 1 and Gate 2
before it is treated as project convention.

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
this validator. The UFO-derived `g_agg_ufo_guess` is only a diagnostic until the
coupling convention is confirmed.

Example with the current Belle II smoke-test banner:

```bash
python theory/predictions/validate.py belleII_alp_testrun10k
```
