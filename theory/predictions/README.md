# Analytic Predictions And Validation

This directory contains the analytic prediction grid and the validation checks
used by the pipeline.

The formulas here define the common convention for:

- $e^+e^-\to\gamma a$ production;
- $a\to\gamma\gamma$ width and lifetime;
- recoil-photon energy;
- boosted ALP decay length;
- diphoton opening angle;
- Belle II public-contour closure;
- checks against MadGraph, Pythia, HepMC, and Delphes outputs.

## Prediction Grid

Build the default grid:

```bash
.venv/bin/python theory/predictions/predict_grid.py \
  --out theory/predictions/theory_grid.csv
```

Belle II-like grid:

```bash
.venv/bin/python theory/predictions/predict_grid.py \
  --sqrt-s 10.58 \
  --belle2-l-min 0.14 \
  --belle2-l-max 1.55 \
  --out theory/predictions/theory_grid_belle2.csv
```

FCC-ee Z-pole grid:

```bash
.venv/bin/python theory/predictions/predict_grid.py \
  --sqrt-s 91.2 \
  --fccee-l-min 0.02 \
  --fccee-l-max 2.5 \
  --out theory/predictions/theory_grid_fccee.csv
```

Useful output columns:

```text
m_a_GeV
g_agg_GeV_inv
sigma_pb
width_GeV
ctau_m
ell_a_m
recoil_E_GeV
delta_theta_min_deg
P_survive_Lmax
P_decay_det
```

## Validate One MC Point

The validator looks for common pipeline outputs:

```text
banner.txt
*_banner.txt
unweighted_events.lhe.gz
events.hepmc
width.txt
param_card.dat
run_card.dat
delphes.root
```

Run it explicitly:

```bash
.venv/bin/python theory/predictions/validate.py <run_dir> \
  --m-a <mass_GeV> \
  --g <g_agg_GeV_inv> \
  --sqrt-s <sqrt_s_GeV> \
  --alp-pdg-id 9999
```

If `<run_dir>` contains `param_card.dat` and `run_card.dat`, the script can
infer $m_a$, $\sqrt{s}$, and the UFO-derived coupling from `fa`, `KB`, and
`KW`. Passing the physical `--g` value is still the clearest option for ALP
production checks.

## Gate 1: Production Cross Section

MadGraph is checked against

$$
\sigma(e^+e^-\to\gamma a)=
\frac{\alpha g_{a\gamma\gamma}^2}{12}
\left(1-\frac{m_a^2}{s}\right)^3.
$$

This catches wrong beam settings, wrong UFO parameters, and unit mistakes in
the coupling mapping.

## Gate 2: Width And Lifetime

The project convention is

$$
\Gamma(a\to\gamma\gamma)=
\frac{g_{a\gamma\gamma}^2m_a^3}{64\pi}.
$$

The ALP production wrappers write this width into `DECAY 9999` and pass the
same value to Pythia. To rerun the width diagnostic:

```bash
mc/alp_signal/run_alp_gate2_width.sh \
  <work_dir> <m_a_GeV> <g_agg_GeV_inv> <param_card>
```

The validator also checks the boosted decay length,

$$
\ell_a=
\frac{|\mathbf{p}_a|}{m_a}\frac{\hbar c}{\Gamma_a},
$$

against the Pythia/HepMC event record when those files are present.

## Gate 3: Belle II Closure

Run:

```bash
.venv/bin/python theory/predictions/validate.py \
  --belle2-closure \
  --axionlimits-dir external/AxionLimits
```

The closure uses the public Belle II curve from AxionLimits and checks whether
the same production, lifetime, and prompt-resolved logic reconstructs it within
the tolerance in `analysis/configs/belle2_closure_inputs.json`.

Outputs:

```text
results/belle2_closure/belle2_closure.png
results/belle2_closure/belle2_closure.pdf
results/belle2_closure/belle2_closure_summary.json
results/belle2_closure/belle2_closure_contour.csv
```

## Pipeline Smoke Test

For the generic $e^+e^-\to\mu^+\mu^-$ smoke-test output:

```bash
.venv/bin/python theory/predictions/validate.py \
  mc/hepmc_smoke_test/work \
  --pipeline-smoke
```

That check is useful on a fresh cluster setup because it verifies that
MadGraph, Pythia, HepMC, Delphes, ROOT, and the Python reader are all connected.
