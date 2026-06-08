# Overleaf Paper Package

This directory is a self-contained Overleaf-ready copy of the paper draft.

Upload the contents of this directory to Overleaf and compile `main.tex`.
The bibliography is included directly in `main.tex`, so no separate `.bib` file is required.

`main.tex` mirrors the current local `paper_draft.tex` result narrative: FCC-ee
Z-pole at `sqrt(s)=91.2 GeV`, `L=150 ab^-1`, invisible reach over
`m_a=0.01--0.92 GeV`, prompt/resolved reach over `m_a=0.61--80 GeV`, and the
invisible upper branch treated as a short-lifetime boundary rather than a
precision contour.

Required figure files are stored in `figures/`:

- `axionlimits_alp_landscape_intro.png`
- `belle2_closure.png`
- `background_signal_examples.png`
- `fccee_zpole_signature_classification.png`
- `money_plot_alp_full_closeup.png`

The local build was checked with:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```
