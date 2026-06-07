# Belle II Closure Test

Overall status: **passed**

This is a published-contour closure test for the photophilic ALP
`e+ e- -> gamma a, a -> gamma gamma` analysis. The target contour
is the Belle II curve distributed in AxionLimits.

## Method

1. Load the digitized Belle II boundary from AxionLimits.
2. Convert masses from eV to GeV and keep the lower exclusion boundary.
3. Use the validated analytic ALP-strahlung cross section and lifetime model.
4. Infer the effective signal-event threshold implied by the published curve.
5. Solve the same analytic model for `g_agg` at that inferred threshold.

Because the Belle II private likelihood, background spectra, and reconstruction
efficiencies are not in this repository, those ingredients are absorbed into
the inferred effective signal-event threshold. This tests our units, cross
section, lifetime, prompt/resolved logic, and plotting conventions against
the published result.

## Inputs

- target curve: `external/AxionLimits/limit_data/AxionPhoton/BelleII.txt`
- source: `AxionLimits BelleII.txt, digitized from Belle II PRL 125, 161806`
- sqrt(s): `10.58 GeV`
- luminosity: `445.0 pb^-1`
- L_min: `0.14 m`
- L_max: `1.55 m`
- polar acceptance: `12.4--155.1 deg`
- angular acceptance factor: `0.91613`
- photon energy threshold: `0.25 GeV`
- diphoton angular resolution: `0.8 deg`

## Closure Metrics

- boundary points: `328`
- closure points: `300`
- max |log10(g_closure/g_published)|: `7.586e-03`
- RMS log10 residual: `8.137e-04`
- median effective signal events: `219`
- effective signal-event range: `48.7--802`

## Outputs

- `belle2_closure_contour.csv`
- `belle2_closure_target.csv`
- `belle2_closure_summary.json`
- `belle2_closure.png` / `belle2_closure.pdf`

