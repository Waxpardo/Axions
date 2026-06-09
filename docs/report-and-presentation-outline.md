# Report And Presentation Outline

This note maps the completed repository artifacts into the final course
deliverables.

## Current Paper-Draft Anchors

`paper_draft.tex` is the current narrative source of truth. The Markdown docs
should preserve these result statements:

| Item | Current statement |
|---|---|
| FCC-ee setup | `sqrt(s)=91.2 GeV`, `L=150 ab^-1`, IDEA-style Delphes |
| Invisible reach | `m_a=0.01--0.92 GeV`, lower branch near `g_agg=5.5e-7 GeV^-1` |
| Invisible upper branch | short-lifetime boundary up to `g_agg ~= 5.5e-2 GeV^-1`; qualitatively useful but numerically fragile |
| Prompt/resolved reach | `m_a=0.61--80 GeV`, `g_agg=1.1e-5--2.9e-4 GeV^-1` |
| Signature grid | 32,400 points: 14,171 prompt/resolved, 10,452 invisible, 5,989 merged, 1,788 displaced/resolved |
| Backgrounds | full-stat `gamma gamma gamma` and `gamma nu nu~` samples, binned and normalized to `150 ab^-1` |

## Report Structure

Target length: 4000--7000 words excluding references.

### 1. Introduction

Use:

```text
README.md
docs/project-status.md
literature/
docs/references.bib
```

Content:

- Photophilic ALP motivation.
- Effective operator and free parameters `(m_a, g_agg)`.
- Why `e+ e- -> gamma a, a -> gamma gamma` is clean.
- Why FCC-ee Z pole is interesting: high luminosity and mono-energetic recoil photon.
- Existing ALP and QCD axion constraints, including dark-matter, astrophysical,
  and cosmological regions from AxionLimits.

### 2. Theory And Kinematics

Use:

```text
theory/predictions/README.md
theory/predictions/predict_grid.py
```

Content:

- `a gamma gamma` interaction convention.
- Decay width and lifetime.
- Associated-production cross section.
- Recoil photon energy.
- Diphoton opening angle and resolved/merged boundary.
- Decay-length regions: prompt, displaced, invisible.

### 3. Simulation Pipeline

Use:

```text
mc/README.md
condor/README.md
docs/nikhef-mg5-pythia-hepmc-smoke-test.md
```

Content:

- MG5 LHE production.
- UFO parameter mapping from `g_agg` to `fa`, `KB`, `KW`.
- Pythia ALP decay and physical lifetime.
- HepMC handoff.
- Delphes detector simulation.
- Background generation.
- Condor campaign layout.

### 4. Validation

Use:

```text
docs/belle2-closure-test.md
docs/alp-full-pipeline-verification-2026-06-05.md
results/belle2_closure/
```

Content:

- Gate 1: cross-section validation.
- Gate 2: width and lifetime convention.
- Gate 3: Belle II public-contour closure.
- Detector-level invariant-mass/recoil validation.
- Smoke-test result for the generic chain.

### 5. FCC-ee Projection Method

Use:

```text
analysis/README.md
docs/detector-assumptions-fccee-zpole.md
docs/final-analysis-rundown.md
```

Content:

- Locked FCC-ee Z-pole inputs.
- Invisible and prompt/resolved signal regions.
- Binned SM background model.
- Asimov `Delta chi2 = 2.71` limit with three-event floor.
- Delphes-derived efficiency corrections.
- Signature classification.

### 6. Results

Use:

```text
results/README.md
results/fccee/fccee_projection.csv
results/fccee/fccee_projection_summary.json
results/fccee/fccee_zpole_signature_classification.png
results/fccee/money_plot_alp_full.png
results/fccee/money_plot_alp_full_closeup.png
results/fccee/money_plot_alp_full_combined.png
```

Content:

- Belle II closure figure.
- Signature-region classification figure.
- Full-range ALP money plot with DM/astro/cosmology constraints.
- FCC-ee-relevant close-up plot.
- Discussion of invisible lower/upper branches.
- Discussion of prompt/resolved reach.
- State that the invisible lower branch and prompt/resolved branch are the
  robust headline results, while the invisible upper branch is a lifetime
  ceiling with large correction factors in the low-mass tail.

### 7. Limitations And Outlook

Use:

```text
docs/project-status.md
docs/final-analysis-rundown.md
```

Content:

- Belle II closure is public-contour level, not a private likelihood.
- No detector systematics or machine backgrounds yet.
- Merged/displaced signatures are classification-only.
- Invisible upper branch is numerically fragile in part of the low-mass tail.
- Future work: other FCC-ee energies, merged/displaced reconstruction, `Z -> gamma a`.

## Presentation Structure

Target: 15 minutes plus 5 minutes questions.

Suggested slide flow:

1. Title and physics question.
2. Photophilic ALP operator and final state.
3. Recoil photon and diphoton signatures.
4. Simulation pipeline diagram.
5. Validation gates.
6. Belle II closure result.
7. FCC-ee Z-pole detector assumptions.
8. Signal regions in `(m_a, g_agg)`.
9. Background and binned-limit method.
10. FCC-ee projection close-up.
11. Full money plot.
12. Limitations and next steps.

Recommended figures:

```text
results/belle2_closure/belle2_closure.png
results/fccee/fccee_zpole_signature_classification.png
results/fccee/money_plot_alp_full_closeup.png
results/fccee/money_plot_alp_full.png
```
