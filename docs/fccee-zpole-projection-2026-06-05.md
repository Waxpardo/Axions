# FCC-ee Z-Pole Projection, 2026-06-05

This note records the FCC-ee Z-pole ALP projection machinery, the associated
IDEA-card smoke test, and the current detector-corrected paper-draft result.

## Inputs

The projection inputs live in:

```bash
analysis/configs/fccee_zpole_inputs.json
```

The current values are:

| Quantity | Value |
|---|---:|
| `sqrt_s_GeV` | `91.2` |
| `luminosity_ab_inv` | `150.0` |
| `l_min_m` | `0.02` |
| `l_max_m` | `2.5` |
| `eta_max` | `3.0` |
| `photon_energy_min_GeV` | `0.5` |
| `photon_efficiency` | `0.99` |
| `delta_theta_res_deg` | `1.5` |
| `n_target_invisible` | `3.0` event floor |
| `n_target_resolved` | `3.0` event floor |
| `background_yields_csv` | `results/fccee/fccee_background_yields.csv` |
| `background_bins_csv` | `results/fccee/fccee_background_bins.csv` |
| `use_efficiency_corrections` | `true` |
| `efficiency_corrections_csv` | `results/fccee/alp_full_analysis_efficiency_map.csv` |
| `efficiency_correction_column` | `detector_correction_factor` |
| `background_bin_floor_events` | `1.0` |
| `invisible_recoil_histogram_high_GeV` | `50.0` |
| `invisible_recoil_histogram_bins` | `264` |
| `resolved_mass_resolution_relative` | `0.05` |
| `resolved_mass_resolution_min_GeV` | `0.05` |
| `invisible_recoil_resolution_relative` | `0.05` |
| `invisible_recoil_resolution_min_GeV` | `0.5` |
| `cl_delta_chi2` | `2.71` |
| `delphes_card` | `mc/delphes_cards/delphes_card_IDEA.tcl` |

The angular-resolution value is a conservative calorimeter-cell scale from the
IDEA Delphes card phi segmentation, `pi/120`. With
`Delta theta_min ~= 4 m_a / sqrt(s)`, this gives a light-ALP resolved threshold
near:

```text
m_a ~= 0.597 GeV
```

## Current Paper-Draft Result

The checked-in projection is the result summarized in `paper_draft.tex`:

| Branch | Rows | Mass span | Coupling span | Interpretation |
|---|---:|---:|---:|---|
| `invisible_lower` | 91 | `0.01--0.92 GeV` | `5.5e-7--7.3e-7 GeV^-1` | robust production/survival floor |
| `invisible_upper` | 91 | `0.01--0.92 GeV` | `1.3e-6--5.5e-2 GeV^-1` | short-lifetime ceiling; numerically fragile at low mass |
| `resolved_prompt` | 98 | `0.61--80 GeV` | `1.1e-5--2.9e-4 GeV^-1` | robust prompt/resolved contour |

The invisible lower branch and the prompt-resolved branch are the robust
headline projections. The upper invisible branch is retained to show where the
ALP becomes too short-lived to escape, but it has very large detector-correction
factors in part of the low-mass tail and should be described qualitatively.

## Background Inputs

Production contours are background-aware. The contour script refuses to run
without a background-yield CSV unless the caller explicitly passes
`--allow-zero-background` for a non-final smoke plot. If a binned-background CSV
is available, the binned method is used for the limit. The yield CSV is retained
as a diagnostic and fallback.

The SM backgrounds are produced with:

```bash
mc/backgrounds/run_sm_background_full_pipeline.sh \
  results/backgrounds/fccee_z/resolved_3gamma \
  resolved_3gamma \
  10000 \
  91.2 \
  mc/delphes_cards/delphes_card_IDEA.tcl

mc/backgrounds/run_sm_background_full_pipeline.sh \
  results/backgrounds/fccee_z/invisible_gamma_nunu \
  invisible_gamma_nunu \
  10000 \
  91.2 \
  mc/delphes_cards/delphes_card_IDEA.tcl
```

where:

```text
resolved_3gamma      = e+ e- -> gamma gamma gamma
invisible_gamma_nunu = e+ e- -> gamma nu nu~
```

The Delphes outputs are converted into the contour input with:

```bash
python3 analysis/fccee_background_yields.py \
  --resolved-root results/backgrounds/fccee_z/resolved_3gamma/resolved_3gamma_delphes.root \
  --resolved-banner results/backgrounds/fccee_z/resolved_3gamma/resolved_3gamma_mg5/Events/run_01/run_01_tag_1_banner.txt \
  --invisible-root results/backgrounds/fccee_z/invisible_gamma_nunu/invisible_gamma_nunu_delphes.root \
  --invisible-banner results/backgrounds/fccee_z/invisible_gamma_nunu/invisible_gamma_nunu_mg5/Events/run_01/run_01_tag_1_banner.txt \
  --out results/fccee/fccee_background_yields.csv \
  --summary-json results/fccee/fccee_background_yields_summary.json
```

For the final-style binned limit, also run:

```bash
python3 analysis/fccee_binned_background.py \
  --resolved-root results/backgrounds/fccee_z/resolved_3gamma/resolved_3gamma_delphes.root \
  --resolved-banner results/backgrounds/fccee_z/resolved_3gamma/resolved_3gamma_mg5/Events/run_01/run_01_tag_1_banner.txt \
  --invisible-root results/backgrounds/fccee_z/invisible_gamma_nunu/invisible_gamma_nunu_delphes.root \
  --invisible-banner results/backgrounds/fccee_z/invisible_gamma_nunu/invisible_gamma_nunu_mg5/Events/run_01/run_01_tag_1_banner.txt \
  --out results/fccee/fccee_background_bins.csv \
  --summary-json results/fccee/fccee_background_bins_summary.json
```

The checked-in background files now use the completed 10000-event full-stat
background campaign:

```text
Condor cluster: 4796877
resolved_3gamma: 10000 generated events, sigma = 7.3063 pb
invisible_gamma_nunu: 10000 generated events, sigma = 134.88513286 pb
resolved_3gamma selected entries: 23592 diphoton pairs
invisible_gamma_nunu selected entries: 2684 recoil photons
```

The binned background totals at `150 ab^-1` are:

```text
resolved_prompt: 2.581827231e9 expected entries across M_gg bins
invisible: 5.4304754489436e9 expected entries across recoil-energy bins
```

The invisible recoil histogram uses 264 bins over `0--50 GeV`, extending above
the nominal `sqrt(s)/2 = 45.6 GeV` endpoint so Delphes/ISR-smeared endpoint
photons are retained in the analysis shape.

## Projection Method

The contour uses the analytic associated-production cross section:

```text
sigma(e+e- -> gamma a) = alpha g_agg^2 / 12 * (1 - m_a^2/s)^3
```

and analytic decay probabilities:

```text
P_invisible = exp(-L_max / ell_a)
P_prompt = 1 - exp(-L_min / ell_a)
```

The invisible and prompt-resolved contours use a 3-event floor plus a binned
Asimov Delta chi2 criterion:

```text
N_signal_required = max(3, sqrt(2.71 / sum_i f_i^2 / max(B_i, 1)))
```

where `f_i` is the normalized Gaussian signal fraction in bin `i`, and `B_i` is
the expected SM background in that bin at `150 ab^-1`.

For each `(m_a, channel)`, the code solves:

```text
L_int * sigma * probability * efficiency_parametric * C_Delphes = N_signal_required
```

Here `efficiency_parametric` is the IDEA-card acceptance/photon-efficiency
baseline, and `C_Delphes` is interpolated from the completed full-analysis
efficiency map. The map is branch-aware: `invisible_lower`,
`invisible_upper`, and `resolved_prompt` are corrected separately.

The resolved contour is only drawn where:

```text
Delta theta_min >= Delta theta_res
```

The checked-in projection is therefore Delphes-corrected, not the old flat-only
projection. It still uses the analytic lifetime probabilities and Gaussian
signal shapes for the contour solve; the Delphes map is applied as an
interpolated efficiency correction layer.

The detector-correction map currently gives:

```text
invisible_lower: mean C_Delphes = 0.998, range 0.969--1.003
invisible_upper: mean C_Delphes = 7.8e6, range 0.919--1.49e8
resolved_prompt: mean C_Delphes = 1.02, range 0.900--2.62
```

## Generated Files

The generated FCC-ee outputs are:

```bash
results/fccee/fccee_projection.csv
results/fccee/fccee_projection_summary.json
results/fccee/fccee_background_yields.csv
results/fccee/fccee_background_yields_summary.json
results/fccee/fccee_background_bins.csv
results/fccee/fccee_background_bins_summary.json
results/fccee/alp_full_analysis_efficiency_map.csv
results/fccee/alp_full_analysis_efficiency_summary.json
results/fccee/fccee_zpole_signature_classification.csv
results/fccee/fccee_zpole_signature_classification.png
results/fccee/money_plot.png
```

The projection channels are:

```text
invisible_lower
invisible_upper
resolved_prompt
```

The full `(m_a, g_agg)` classification labels are:

```text
invisible
merged
displaced_resolved
prompt_resolved
```

The checked-in signature counts are:

```text
prompt_resolved: 14171
invisible: 10452
merged: 5989
displaced_resolved: 1788
total: 32400
```

## IDEA Delphes Smoke Test

The IDEA Delphes card is integrated through:

```bash
mc/delphes_cards/delphes_card_IDEA.tcl
```

which sources:

```bash
mc/delphes_cards/fcc_idea/card_IDEA_winter2023.tcl
```

On Nikhef, the first run failed in Delphes because the IDEA card's timing module
expected a missing `MuonMomentumSmearing/muons` input in the LCG Delphes build.
For this photon-only ALP study, track timing is not used, so this project copy
of the IDEA card skips `TimeSmearing` and `TimeOfFlight`, feeding
`ClusterCounting/tracks` directly into `TrackMerger`.

After that patch, the FCC-ee smoke test passed:

```text
sqrt_s_GeV = 91.2
m_a_GeV = 1.0
g_agg_GeV_inv = 1e-5
events = 200
MG5/theory cross-section ratio = 0.9987
width convention = 64pi, passed
Pythia lifetime = passed
Delphes ROOT = passed
resolved_best_mgg_mean_GeV = 1.0297
resolved_best_mgg_abs_error_GeV = 0.0297
```

The compact returned summaries are under:

```bash
results/alp_full_pipeline/fccee_zpole_idea_m1_g1em5_n200_rerun
```

## Final Signal Production Rule

Final detector-level signal points should use:

```bash
condor/run_alp_full_point.sh
condor/submit_alp_full_scan.sub
```

not the production-only stable-LHE scan. The full-point wrapper runs
`mc/alp_signal/run_alp_full_pipeline.sh`, which now calls:

```bash
analysis/alp_pipeline_histograms.py --require-pass
```

so every final signal point must pass the detector-level ALP invariant-mass
validation before it is accepted.
