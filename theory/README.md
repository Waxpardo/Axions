# Theory And Analytic Predictions

This directory contains the analytic physics layer used to validate and guide
the Monte Carlo analysis.

## Contents

| Path | Purpose |
|---|---|
| `Cross.nb` | Mathematica notebook used for derivations/checks. |
| `notes/` | LaTeX/report-oriented theory notes. |
| `predictions/` | Python formulas, grids, and validation gates. |

## Source Of Truth

The code source of truth is:

```text
theory/predictions/predict_grid.py
```

It implements:

```text
Gamma(a -> gamma gamma)
sigma(e+e- -> gamma a)
recoil photon energy
proper and boosted decay length
minimum diphoton opening angle
```

These functions are imported by the validation and analysis scripts, so changes
to conventions should be made there first and then propagated through the
validation gates.

## Validation

The central validation script is:

```text
theory/predictions/validate.py
```

It checks:

| Gate/check | Meaning |
|---|---|
| Gate 1 | MG5 production cross section vs analytic `sigma`. |
| Gate 2 | ALP width convention and Pythia lifetime synchronization. |
| Gate 3 | Belle II public-contour closure. |
| Pipeline smoke | Expected files and ROOT keys for the generic chain. |
| Recoil/angle/decay checks | Kinematic validation for detector-level ALP points. |

See `theory/predictions/README.md` for command examples.
