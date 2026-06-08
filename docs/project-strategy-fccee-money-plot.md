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

where the final FCC-ee labels are `invisible_lower`, `invisible_upper`, and
`resolved_prompt`.

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

For this project, the core deliverable implements invisible and resolved
contours. Merged and displaced are classified discussion regions unless the
analysis code is extended.

## Current Technical State

The FCC-ee limit calculator, full-stat backgrounds, 284-point detector-level
signal scan, branch-aware Delphes correction map, and final money plots are now
implemented. The paper-draft result uses:

1. Full-stat SM backgrounds for `gamma gamma gamma` and `gamma nu nu~`.
2. `results/fccee/fccee_background_bins.csv` as the binned background input.
3. A binned Asimov `Delta chi2 = 2.71` limit with a 3-event floor.
4. `results/fccee/alp_full_analysis_efficiency_map.csv` as the branch-aware
   detector-correction map.
5. `results/fccee/fccee_projection.csv` as the detector-corrected contour.

The current headline spans are:

```text
invisible_lower: 0.01--0.92 GeV at 5.5e-7--7.3e-7 GeV^-1
invisible_upper: 0.01--0.92 GeV at 1.3e-6--5.5e-2 GeV^-1
resolved_prompt: 0.61--80 GeV at 1.1e-5--2.9e-4 GeV^-1
```

Regenerate the final plotting artifacts with:

```bash
.venv/bin/python analysis/make_axionlimits_style_plot.py \
  --axionlimits-dir external/AxionLimits \
  --projection results/fccee/fccee_projection.csv \
  --constraint-set full \
  --output-stem results/fccee/money_plot_alp_full \
  --combined-output-stem results/fccee/money_plot_alp_full_combined

.venv/bin/python analysis/make_axionlimits_style_plot.py \
  --axionlimits-dir external/AxionLimits \
  --projection results/fccee/fccee_projection.csv \
  --constraint-set full \
  --output-stem results/fccee/money_plot_alp_full_closeup \
  --also-save-as results/fccee/money_plot \
  --m-min 1e7 --m-max 1e12 --g-min 1e-8 --g-max 1e-1
```

The invisible upper branch should be presented as a short-lifetime boundary
rather than a precision contour because its low-mass tail has very large
detector-correction factors.
