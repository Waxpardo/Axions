# Belle II Published-Contour Closure Test

This note documents the Belle II closure implemented in
`analysis/belle2_closure.py`.

## Purpose

The closure checks that the repository's analytic ALP-strahlung model,
lifetime convention, prompt/resolved detector-region logic, and units reproduce
the public Belle II exclusion boundary for:

```text
e+ e- -> gamma a,  a -> gamma gamma
sqrt(s) = 10.58 GeV
```

## Important Scope

This is a published-contour closure, not a Belle II private-likelihood
reimplementation. The public repository does not contain Belle II's full binned
likelihood, background spectra, or reconstruction-efficiency maps. Those
ingredients are absorbed into an inferred effective signal-yield threshold.

## Inputs

The locked assumptions live in:

```bash
analysis/configs/belle2_closure_inputs.json
```

Key values:

```text
sqrt_s_GeV = 10.58
luminosity_pb_inv = 445
L_min = 0.14 m
L_max = 1.55 m
photon_energy_min = 0.25 GeV
polar acceptance = 12.4--155.1 deg
delta_theta_res = 0.8 deg
```

The published Belle II target curve is loaded from AxionLimits:

```text
limit_data/AxionPhoton/BelleII.txt
```

## Run

Clone AxionLimits into `external/AxionLimits`, or pass the local checkout path:

```bash
python theory/predictions/validate.py \
  --belle2-closure \
  --axionlimits-dir external/AxionLimits
```

For the current local checkout used in development:

```bash
.venv/bin/python theory/predictions/validate.py \
  --belle2-closure \
  --axionlimits-dir /private/tmp/AxionLimits_verify
```

The standalone plotting script remains available for direct reruns:

```bash
python analysis/belle2_closure.py \
  --axionlimits-dir external/AxionLimits
```

## Outputs

The script writes:

```text
results/belle2_closure/belle2_closure_contour.csv
results/belle2_closure/belle2_closure_target.csv
results/belle2_closure/belle2_closure_summary.json
results/belle2_closure/belle2_closure.md
results/belle2_closure/belle2_closure.png
results/belle2_closure/belle2_closure.pdf
```

Current status:

```text
passed
max |log10(g_closure/g_published)| = 7.59e-3
median effective signal events = 219
effective signal-event range = 48.7--802
```

The gray three-event curve in the plot is intentionally included as a sanity
check: it does not reproduce Belle II, which confirms that the published
analysis is background/selection limited and cannot be represented as a
zero-background three-event search.
