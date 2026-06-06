# Belle II-Style Pipeline Verification

Overall status: **passed**

This report verifies the Belle II-like simulation pipeline before limit setting.
It does not claim reproduction of the published Belle II exclusion contour.

## Inputs

- run directory: `results/alp_full_pipeline/belle2_hist_m1_g1em5_s10p58_n500`
- target ALP mass: `1.0 GeV`
- mass tolerance: `0.2 GeV`

## Checks

| Check | Status |
|---|---|
| cross_section | passed |
| width | passed |
| pythia_lifetime | passed |
| delphes_root | passed |
| alp_mass_histogram | passed |

## Key Observables

- events: `500`
- events with >=3 photons: `46`
- mean reconstructed photons/event: `1.792`
- resolved best-pair mean mass: `1.0375553576842598 GeV`
- resolved mass absolute error: `0.03755535768425977 GeV`
- Pythia input c*tau: `0.396749434867 mm`
- mean lab decay length: `2.275433802278 mm`
