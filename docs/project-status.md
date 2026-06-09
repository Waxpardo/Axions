# Project Status

Last updated: 2026-06-09.

This file is a short checklist for collaborators. The detailed methods are in
`docs/final-analysis-rundown.md`.

## Completed Core Deliverables

| Deliverable | Status | Evidence |
|---|---:|---|
| Public Belle II validation anchor | complete | `results/belle2_closure/belle2_closure_summary.json` |
| ALP signal full pipeline | complete | `mc/alp_signal/run_alp_full_pipeline.sh` |
| SM background full pipeline | complete | `mc/backgrounds/run_sm_background_full_pipeline.sh` |
| Gate 1 cross-section validation | complete | `theory/predictions/validate.py` |
| Gate 2 width/lifetime synchronization | complete | `mc/alp_signal/run_alp_gate2_width.sh` and pipeline summaries |
| Gate 3 Belle II closure | complete | `python theory/predictions/validate.py --belle2-closure` |
| FCC-ee binned background inputs | complete | `results/fccee/fccee_background_bins.csv` |
| FCC-ee detector-corrected contours | complete | `results/fccee/fccee_projection.csv` |
| FCC-ee signature classification | complete | `results/fccee/fccee_zpole_signature_classification.csv` |
| Existing constraints overlay | complete | `analysis/make_axionlimits_style_plot.py` |
| Final money plots | complete | `results/fccee/money_plot_alp_full*.png` and `.pdf` |

## Current Final Result

The headline output is the FCC-ee Z-pole projection:

```text
sqrt(s) = 91.2 GeV
L = 150 ab^-1
detector = IDEA-style Delphes
channels = invisible and prompt/resolved
```

The final contour uses:

```text
binned SM backgrounds
Delphes-derived branch-aware efficiency corrections
analytic production and lifetime scan
```

Paper-draft numerical summary:

```text
invisible_lower: m_a = 0.01--0.92 GeV, g_agg = 5.5e-7--7.3e-7 GeV^-1
invisible_upper: m_a = 0.01--0.92 GeV, g_agg = 1.3e-6--5.5e-2 GeV^-1
resolved_prompt: m_a = 0.61--80 GeV, g_agg = 1.1e-5--2.9e-4 GeV^-1
resolved threshold: m_a ~= 0.597 GeV
```

## Validation Summary

Belle II closure:

```text
status = passed
max |log10(g_closure / g_published)| = 7.59e-3
tolerance = 2.0e-2
```

FCC-ee projection summary:

```text
projection rows = 280
resolved_prompt rows = 98
invisible_lower rows = 91
invisible_upper rows = 91
binned backgrounds included = true
efficiency corrections included = true
signature grid = 32400 rows
signature counts = prompt_resolved 14171, invisible 10452, merged 5989, displaced_resolved 1788
```

Detector-level signal campaign:

```text
points = 284
Gate 1 passed = 284
channel-aware signature validation passed = 284
```

## Limitations To State Clearly

The Belle II result is a public-contour closure. It does not use the private
Belle II likelihood, private background spectra, or private reconstruction
efficiencies.

The FCC-ee projection includes leading SM backgrounds for the implemented
regions, but not full detector systematics, beam-induced backgrounds, or
machine-noise effects.

Merged and displaced ALP signatures are classified in the `(m_a, g_agg)` plane
but do not yet have exclusion contours. They need dedicated reconstruction and
background studies.

The invisible upper branch is detector-corrected but numerically fragile in
parts of the low-mass tail because the selected detector fraction is very small.

## Recommended Next Physics Improvements

1. Add systematic uncertainties to the binned limit model.
2. Add a merged-photon region with a realistic shower-shape efficiency.
3. Add a displaced-photon region with an explicit vertexing/non-pointing model.
4. Repeat the FCC-ee projection at other run energies if time allows.
5. Convert the method notes into the final 4000--7000 word report.
