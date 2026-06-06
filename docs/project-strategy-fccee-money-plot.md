# Project Strategy: FCC-ee Money Plot

## Recommendation

Belle II is now available as a published-contour closure test. The repository
does not contain Belle II's private background and reconstruction-efficiency
inputs, so the closure infers the effective signal-yield threshold implied by
the digitized public Belle II curve and reruns the analytic production/lifetime
model against it. Keep this as the validation anchor while the main project
deliverable remains the FCC-ee projection.

The strongest structure for the project is:

1. Validate the simulation/theory machinery with Belle II-like kinematics.
2. Use the verified machinery to produce FCC-ee Z-pole projections.
3. Put the FCC-ee contours on the existing axion-photon landscape.
4. Explain which detector signature drives each part of the contour.

This preserves scientific discipline without letting a missing public background
table derail the actual deliverable.

## Role of AxionLimits

AxionLimits is suitable as the context layer for the final plot, not as a
primary result. It provides public data files and notebooks for axion,
axion-like-particle, and dark-photon constraints, has a Zenodo DOI, and links
curves to references. Its own README also warns that the included constraints
come from many subfields with differing assumptions and statistical conventions.

Use it for the background landscape and cite:

```bibtex
@misc{AxionLimits,
  author       = {Ciaran O'Hare},
  title        = {cajohare/AxionLimits: AxionLimits},
  month        = jul,
  year         = 2020,
  publisher    = {Zenodo},
  version      = {v1.0},
  doi          = {10.5281/zenodo.3932430},
  howpublished = {\url{https://cajohare.github.io/AxionLimits/}}
}
```

## Money Plot Definition

The final plot should have:

- x-axis: `m_a` in GeV
- y-axis: `g_{a gamma gamma}` in `GeV^-1`
- background: current axion-photon constraints from AxionLimits
- foreground: FCC-ee Z-pole projection at `sqrt(s) = 91.2 GeV`,
  `L = 150 ab^-1`
- separate FCC-ee curves or regions for invisible and resolved signatures

The plotting interface now expects projection CSVs with:

```text
m_a_GeV,g_agg_GeV_inv,channel
```

where `channel` can be `invisible`, `resolved`, or another analysis label.

## Signature Regions

Use three physics quantities to organize the FCC-ee discussion:

- production rate:
  `sigma(e+e- -> gamma a) proportional to g_{a gamma gamma}^2
   (1 - m_a^2/s)^3`
- decay length:
  `ell_a = (p_a / m_a) c tau_a`
- resolved diphoton opening angle:
  `Delta theta_min approximately 4 m_a / sqrt(s)` for light ALPs

The detector-level categories are:

- invisible: `ell_a > L_max`
- prompt/resolved: `ell_a < L_min` and
  `Delta theta_gamma_gamma > Delta theta_res`
- displaced/resolved: `L_min < ell_a < L_max` and
  `Delta theta_gamma_gamma > Delta theta_res`
- merged: `ell_a < L_max` and
  `Delta theta_gamma_gamma < Delta theta_res`

For this project, the core deliverable should implement invisible and resolved
first. Merged and displaced are useful discussion regions unless the analysis
code is extended.

## Current Technical Plan

The FCC-ee limit calculator is now implemented. The active production plan is:

1. Produce full-stat SM backgrounds for `gamma gamma gamma` and `gamma nu nu~`.
2. Build `results/fccee/fccee_background_bins.csv`.
3. Run the binned FCC-ee projection with `Delta chi2 = 2.71` and a 3-event
   floor.
4. Run the detector-level ALP scan points generated from the projection.
5. Collect full-scan summaries and use them to replace flat photon efficiencies
   with Delphes-derived efficiencies.
6. Regenerate `results/fccee/fccee_projection.csv` and the money plot:

```bash
python analysis/make_axionlimits_style_plot.py \
  --axionlimits-dir external/AxionLimits \
  --projection results/fccee/fccee_projection.csv \
  --constraint-set generic \
  --output-stem results/fccee/money_plot_generic_alp \
  --also-save-as results/fccee/money_plot
```

The checked-in projection is a working analysis product, but the numerical
limits should be updated after the full-stat Condor outputs replace the current
smoke-level background files.
