# Final Analysis Rundown

This is the current runbook for the photophilic ALP project. It is written for
a collaborator who has cloned the repository and wants to understand what is
implemented, what assumptions are locked, and what still needs final production
statistics.

## Project Goal

The target result is a projected FCC-ee Z-pole exclusion contour in the
`(m_a, g_agg)` plane for:

```text
e+ e- -> gamma a,  a -> gamma gamma
sqrt(s) = 91.2 GeV
L = 150 ab^-1
```

The final plot overlays the FCC-ee projection on the current axion-photon
constraint landscape from AxionLimits. Belle II closure is implemented as a
published-contour closure test in `analysis/belle2_closure.py`. It reproduces
the public Belle II boundary by inferring the effective signal-yield threshold
implied by the digitized curve; it does not claim access to Belle II's private
likelihood, background spectra, or reconstruction-efficiency maps.

## Repository Map

| Path | Purpose |
|---|---|
| `models/ALP_linear/SM_alp_UFO/` | MadGraph UFO with the ALP model |
| `mc/alp_signal/` | ALP MG5, Pythia lifetime/decay, and Delphes pipeline |
| `mc/backgrounds/` | SM background MG5, Pythia, and Delphes pipeline |
| `mc/delphes_cards/` | Belle II-style and FCC-ee IDEA Delphes cards |
| `theory/predictions/` | Analytic cross sections, widths, lifetimes, grids, validation |
| `analysis/` | Background builders, FCC-ee projection, plots, AxionLimits loader |
| `analysis/configs/` | Locked analysis inputs and external-source provenance |
| `condor/` | Nikhef full-production submit files |
| `docs/` | Setup guides, assumptions, and analysis notes |
| `results/fccee/` | Projection CSVs, summaries, classification grids, money plot |

## Physics and Validation

The validated formulas are:

```text
Gamma(a -> gamma gamma) = g_agg^2 m_a^3 / (64 pi)
sigma(e+e- -> gamma a) = alpha g_agg^2 / 12 * (1 - m_a^2/s)^3
E_gamma = (s - m_a^2) / (2 sqrt(s))
ell_a = (p_a / m_a) * hbar c / Gamma_a
Delta theta_min ~= 4 m_a / sqrt(s)
```

The full signal pipeline checks:

| Gate | Check |
|---|---|
| Gate 1 | MG5 production cross section agrees with analytic `sigma` |
| Gate 2 | Width/lifetime uses the `64 pi` convention and Pythia lifetime is synced |
| Detector mass check | Delphes photon pairs reconstruct the requested ALP mass |

Every final detector-level ALP point is run through
`analysis/alp_pipeline_histograms.py --require-pass`.

## Signal Regions

The analysis classifies every grid point using the decay length and opening
angle assumptions in `docs/detector-assumptions-fccee-zpole.md`.

| Region | Detector signature | Current status |
|---|---|---|
| Invisible | one recoil photon plus missing energy | FCC-ee contour |
| Prompt resolved | recoil photon plus two resolved ALP photons | FCC-ee contour |
| Displaced resolved | recoil photon plus displaced diphoton | classification only |
| Merged | recoil photon plus merged ALP photon shower | classification only |

The current money plot therefore claims projected reach only for invisible and
prompt-resolved signatures. Displaced and merged regions are interpretation
bands until dedicated detector efficiencies and backgrounds are added.

## Backgrounds

The current background samples are:

| Channel | MG5 process | Observable |
|---|---|---|
| `resolved_prompt` | `e+ e- -> gamma gamma gamma` | all Delphes photon-pair masses `M_gg` |
| `invisible` | `e+ e- -> gamma nu nu~` | Delphes one-photon recoil energy |

Backgrounds are normalized with:

```text
N_B = sigma_pb * L_pb^-1 * N_bin / N_generated
```

The final-style limit uses the binned CSV:

```text
results/fccee/fccee_background_bins.csv
```

The window-yield CSV:

```text
results/fccee/fccee_background_yields.csv
```

is retained as a diagnostic and fallback. It is not the preferred final method.

## Binned Limit Method

For each mass and channel, the projection script smears the signal into the
analysis observable bins and computes the Asimov signal count required for
`Delta chi2 = 2.71`:

```text
N_signal_required = max(3, sqrt(2.71 / sum_i f_i^2 / max(B_i, 1)))
```

The contour solver then finds `g_agg` such that:

```text
L * sigma(m_a, g_agg) * P_region(m_a, g_agg) * efficiency_parametric * C_Delphes = N_signal_required
```

For the checked-in FCC-ee contour, `C_Delphes` is the branch-aware
`detector_correction_factor` interpolated from
`results/fccee/alp_full_analysis_efficiency_map.csv`. The correction branches
are `invisible_lower`, `invisible_upper`, and `resolved_prompt`.

Because the invisible yield is non-monotonic in `g_agg`, the invisible region
can produce lower and upper roots. These are written as `invisible_lower` and
`invisible_upper`.

The FCC-ee contour branches have sharp-looking mass endpoints for three
different reasons. The prompt/resolved branch starts near `0.6 GeV` because the
analysis requires the ALP daughter photons to be separated by more than the
IDEA angular-resolution input, `Delta theta_res = 1.5 deg`; using
`Delta theta_min ~= 4 m_a / sqrt(s)` gives
`m_a ~= sqrt(s) Delta theta_res / 4 = 0.597 GeV`, and the log mass grid places
the first solved point at `0.614 GeV`. The invisible branches stop near
`0.92 GeV` because above that mass the binned-background target is not reached
by the invisible signal yield with the current assumptions. The prompt/resolved
branch currently stops at `80 GeV` because the validated projection grid was
built with `--m-max 80`; extending it closer to the kinematic endpoint would
require regenerating the projection and detector-correction campaign in that
mass range.

## Locked Inputs

Use this config for the FCC-ee Z-pole result:

```bash
analysis/configs/fccee_zpole_inputs.json
```

Key values:

```text
sqrt_s_GeV = 91.2
luminosity_ab_inv = 150
L_min = 0.02 m
L_max = 2.5 m
eta_max = 3.0
E_gamma_min = 0.5 GeV
Delta theta_res = 1.5 deg
resolved mass resolution = max(5 percent, 0.05 GeV)
invisible recoil resolution = max(5 percent, 0.5 GeV)
invisible recoil histogram = 264 bins over 0--50 GeV
efficiency correction map = results/fccee/alp_full_analysis_efficiency_map.csv
```

See `docs/detector-assumptions-fccee-zpole.md` for the full table and caveats.

## AxionLimits Provenance

The context landscape is pinned in:

```bash
analysis/configs/axionlimits_source.json
```

Current source:

```text
repository = https://github.com/cajohare/AxionLimits.git
docs = https://cajohare.github.io/AxionLimits/docs/ap.html
commit = 7d375f4879b32406a239fe48d2615a4bfd9bc0bb
commit date = 2026-01-27 10:38:52 +1100
Zenodo DOI = 10.5281/zenodo.3932430
```

Use AxionLimits as a context layer, not as a primary result. Its curves combine
many experiments and assumptions, so the FCC-ee result should be described
separately and overlaid transparently.

## Full-Production Commands

Submit the full-stat SM background jobs on Nikhef:

```bash
condor_submit condor/submit_background_scan.sub
```

Submit the detector-level signal points generated from the projected contour:

```bash
condor_submit condor/submit_alp_full_projection_scan.sub
```

The submitted campaign files are:

```text
condor/background_points_fccee_z.txt
condor/alp_full_points_fccee_z_projection.txt
```

The projection-derived signal file currently contains 284 points with 10000
events per point.

The first full-stat submissions were launched on 2026-06-05:

```text
SM backgrounds: Condor cluster 4796877, 2 jobs, completed
ALP full scan: Condor cluster 4796878, 284 jobs, superseded by channel-aware validation
```

The clean channel-aware detector-level ALP scan was launched and completed on
2026-06-06:

```text
ALP full scan: Condor cluster 4797476, 284 jobs, campaign fccee_z_full_projection_fullbg_channelaware
Gate 1 and channel-aware detector validation: 284 / 284 passed
```

Recheck the active signal scan on Nikhef with:

```bash
condor_q 4797476 -wide
```

The completed detector-level signal summaries are:

```text
results/fccee/alp_full_scan_summary.csv
results/fccee/alp_full_scan_summary.json
results/fccee/alp_signal_efficiency_map.csv
results/fccee/alp_signal_efficiency_summary.json
results/fccee/alp_full_analysis_efficiency_map.csv
results/fccee/alp_full_analysis_efficiency_summary.json
```

The full-analysis efficiency map is now used in the official FCC-ee contour as
a branch-aware multiplicative detector correction. It is still an interpolation
layer built from the completed contour-point signal scan, not a fresh Delphes
campaign at the corrected contour points.

The full-stat background files have already replaced the smoke-level inputs in
`results/fccee/`. Rebuild them from the completed background ROOT files with:

```bash
python3 analysis/fccee_binned_background.py \
  --resolved-root <resolved_3gamma_delphes.root> \
  --resolved-banner <resolved_3gamma_banner.txt> \
  --invisible-root <invisible_gamma_nunu_delphes.root> \
  --invisible-banner <invisible_gamma_nunu_banner.txt> \
  --out results/fccee/fccee_background_bins.csv \
  --summary-json results/fccee/fccee_background_bins_summary.json
```

After the signal jobs finish, collect validation summaries:

```bash
python3 analysis/collect_alp_full_scan.py \
  results/alp_full_production/fccee_z_full_projection_fullbg_channelaware \
  --out results/fccee/alp_full_scan_summary.csv \
  --summary-json results/fccee/alp_full_scan_summary.json
```

Then rebuild the projection:

```bash
python3 analysis/fccee_projection.py \
  --config analysis/configs/fccee_zpole_inputs.json \
  --out-dir results/fccee \
  --background-yields results/fccee/fccee_background_yields.csv \
  --background-bins results/fccee/fccee_background_bins.csv \
  --n-mass 180 \
  --n-g 180
```

And rebuild the full ALP money plot:

```bash
python3 analysis/make_axionlimits_style_plot.py \
  --axionlimits-dir external/AxionLimits \
  --projection results/fccee/fccee_projection.csv \
  --constraint-set full \
  --output-stem results/fccee/money_plot_alp_full \
  --also-save-as results/fccee/money_plot \
  --combined-output-stem results/fccee/money_plot_alp_full_combined
```

Use `--constraint-set generic` only for a diagnostic plot that hides
dark-matter and cosmology-assuming regions.

Build the FCC-ee close-up with:

```bash
python3 analysis/make_axionlimits_style_plot.py \
  --axionlimits-dir external/AxionLimits \
  --projection results/fccee/fccee_projection.csv \
  --constraint-set full \
  --output-stem results/fccee/money_plot_alp_full_closeup \
  --m-min 1e7 \
  --m-max 1e12 \
  --g-min 1e-8 \
  --g-max 1e-1
```

## Current Status

The MG5 to Pythia to Delphes ALP signal pipeline has passed both channel-aware
smoke tests:

```text
resolved_prompt: high-mass point reconstructs M_gg near m_a
invisible: recoil photon reconstructs near the two-body recoil energy
```

The SM background pipeline has produced full-stat 10000-event samples for both
required channels, and the checked-in FCC-ee projection/money plot now use those
full-stat binned background files. The channel-aware detector-level signal scan
also completed with all 284 points passing.

The detector-level selected fractions from the full ALP scan are:

```text
invisible_lower: mean 0.950, range 0.512--0.977
invisible_upper: mean 0.0179, range 0.0044--0.1935
resolved_prompt: mean 0.635, range 0.209--0.919
```

The full-analysis efficiency map additionally uses the actual binned analysis
observables and SM background bins. It shows:

```text
invisible_lower: observable/bin/full fraction mean 0.959, strength mean 1.157
invisible_upper: observable/bin/full fraction mean 0.0187
resolved_prompt: observable/in-bin fraction mean 0.886, strength mean 1.180
```

The invisible recoil-energy histogram now extends beyond the nominal endpoint:
`0--50 GeV` with 264 bins. This keeps the bin width close to the previous setup
while retaining Delphes/ISR-smeared endpoint signal above `sqrt(s)/2 = 45.6 GeV`.
The post-rerun full-analysis map has
`analysis_bin_acceptance_fraction = 1.0` for all three projected branches, so the
previous endpoint-loss diagnostic is resolved.

## Limitations to State in the Report

The checked-in contour uses the analytic/binned projection model corrected by
the Delphes-derived full-analysis efficiency map. The invisible upper branch
has very large correction factors in parts of the low-mass tail, so that branch
should be described as detector-corrected but still numerically fragile.

The invisible and resolved backgrounds are leading SM channels for the defined
regions, but systematic uncertainties, detector noise, beam backgrounds, and
pileup-like machine backgrounds are not yet included.

The merged and displaced signatures are classified but not used as exclusion
regions. They need separate reconstruction and background models.

Belle II closure is claimed at published-contour level. The closure output is in
`results/belle2_closure/` and is integrated as Gate 3 in
`theory/predictions/validate.py`:

```bash
python theory/predictions/validate.py \
  --belle2-closure \
  --axionlimits-dir external/AxionLimits
```

The current run passes with max
`|log10(g_closure/g_published)| = 7.59e-3`. A future private-likelihood closure
would still require Belle II-specific background and reconstruction-efficiency
inputs that are not public in this repository.
