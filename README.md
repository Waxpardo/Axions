# Photophilic ALP Search at $e^+e^-$ Colliders

This repository contains a complete simulation and analysis pipeline for a
photophilic axion-like particle (ALP) search at electron-positron colliders.
The signal process is

$$
e^+e^- \to \gamma a,\qquad a\to\gamma\gamma,
$$

with the effective interaction

$$
\mathcal{L}\supset
\frac{g_{a\gamma\gamma}}{4}\,aF_{\mu\nu}\tilde F^{\mu\nu}.
$$

The pipeline is set up to do three things:

1. Check the analytic formulas against MadGraph and the Belle II public limit.
2. Generate ALP signal and Standard Model background samples through
   MadGraph, Pythia, and Delphes.
3. Build FCC-ee Z-pole projected sensitivity contours and overlay them on the
   existing ALP-photon landscape.

The default FCC-ee setup is the Z pole,
$\sqrt{s}=91.2\,\mathrm{GeV}$ with
$\mathcal{L}=150\,\mathrm{ab}^{-1}$, using an IDEA-like Delphes detector card.

## Quick Start

From a fresh clone, set up the local Python environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r env/requirements.txt
```

Clone the external AxionLimits data if you want to rebuild the landscape plots
or rerun the Belle II closure:

```bash
git clone https://github.com/cajohare/AxionLimits.git external/AxionLimits
cd external/AxionLimits
git checkout 7d375f4879b32406a239fe48d2615a4bfd9bc0bb
cd ../..
```

Then the local, pure-Python chain is:

```bash
make theory-grid
make belle2-closure
make projection
make background-signal-examples
make money-plots
```

or, in one go:

```bash
make local-all
```

Run this if you just want to check that the Python scripts compile:

```bash
.venv/bin/python -m py_compile analysis/*.py theory/predictions/*.py mc/make_param_card.py
```

## Repository Architecture

```text
.
├── analysis/              Python background building, limits, plots, efficiency maps
│   └── configs/           Locked JSON inputs for Belle II, FCC-ee, AxionLimits
├── condor/                HTCondor point lists and submit files for Nikhef/Stoomboot
├── env/                   Python requirements and Nikhef LCG setup helper
├── external/              Local external checkouts, especially AxionLimits
├── literature/            Reference papers kept outside the runnable pipeline
├── mc/                    MadGraph, Pythia, Delphes cards and production wrappers
├── models/ALP_linear/     UFO model used by MadGraph
├── results/               Compact CSV, JSON, PNG, and PDF outputs
└── theory/predictions/    Analytic formulas and validation tools
```

The detailed READMEs are:

| README | What it covers |
|---|---|
| `env/README.md` | Python environment and Nikhef LCG setup. |
| `theory/predictions/README.md` | Analytic grid, cross-section checks, Belle II closure. |
| `mc/README.md` | MadGraph, Pythia, Delphes signal/background production. |
| `condor/README.md` | Batch production on the Nikhef Stoomboot cluster. |
| `analysis/README.md` | Background histograms, contours, efficiency maps, plotting. |
| `results/README.md` | Meaning of the checked-in result files. |
| `external/README.md` | How external data repositories are expected to live here. |

## Physics Conventions

The code uses:

- mostly-minus metric;
- $\epsilon^{0123}=+1$;
- $g_{a\gamma\gamma}$ in $\mathrm{GeV}^{-1}$;
- $\hbar c=1.973269804\times10^{-16}\,\mathrm{GeV\,m}$;
- $\Gamma(a\to\gamma\gamma)=g_{a\gamma\gamma}^2m_a^3/(64\pi)$.

The main analytic formulas are

$$
\sigma(e^+e^-\to\gamma a)=
\frac{\alpha g_{a\gamma\gamma}^2}{12}
\left(1-\frac{m_a^2}{s}\right)^3,
$$

$$
E_{\gamma,\mathrm{recoil}}=
\frac{s-m_a^2}{2\sqrt{s}},
$$

$$
\ell_a=
\frac{|\mathbf{p}_a|}{m_a}\,
\frac{\hbar c}{\Gamma_a},
$$

and

$$
\Delta\theta_{\gamma\gamma}^{\min}\simeq\frac{4m_a}{\sqrt{s}}.
$$

These are implemented in `theory/predictions/predict_grid.py` and used by the
validation and projection scripts.

## Pipeline Order

The full analysis runs in this order:

```text
1. Analytic prediction grid
2. Belle II public-contour closure
3. MadGraph ALP signal production
4. Pythia ALP decay/lifetime and HepMC writing
5. Delphes detector simulation
6. Detector-level signal validation
7. Standard Model background production
8. Binned background histograms
9. Detector efficiency/correction map
10. FCC-ee projected contours
11. Signature classification map
12. AxionLimits landscape and money plots
```

The dense contour is not made by running Delphes at every
$(m_a,g_{a\gamma\gamma})$ point. Instead, the code uses the analytic scaling of
the production rate and lifetime over a dense grid, then corrects that grid
with Delphes signal samples and binned Standard Model backgrounds.

## Stage 1: Analytic Prediction Grid

Build the theory grid:

```bash
.venv/bin/python theory/predictions/predict_grid.py \
  --out theory/predictions/theory_grid.csv
```

Useful variants:

```bash
.venv/bin/python theory/predictions/predict_grid.py \
  --sqrt-s 10.58 \
  --out theory/predictions/theory_grid_belle2.csv

.venv/bin/python theory/predictions/predict_grid.py \
  --sqrt-s 91.2 \
  --fccee-l-min 0.02 \
  --fccee-l-max 2.5 \
  --out theory/predictions/theory_grid_fccee.csv
```

Main script:

| Script | Role |
|---|---|
| `theory/predictions/predict_grid.py` | Computes $\sigma$, $\Gamma_a$, $c\tau$, boosted decay length, recoil energy, and photon opening angle. |

## Stage 2: Belle II Closure

Run the closure against the public Belle II curve in AxionLimits:

```bash
.venv/bin/python theory/predictions/validate.py \
  --belle2-closure \
  --axionlimits-dir external/AxionLimits
```

Outputs:

```text
results/belle2_closure/belle2_closure.png
results/belle2_closure/belle2_closure.pdf
results/belle2_closure/belle2_closure_summary.json
results/belle2_closure/belle2_closure_contour.csv
```

Main scripts:

| Script | Role |
|---|---|
| `analysis/belle2_closure.py` | Reconstructs the public Belle II boundary using the same production/lifetime logic used later for FCC-ee. |
| `theory/predictions/validate.py` | Runs the closure and writes pass/fail summaries. |

## Stage 3: Local FCC-ee Projection

The checked-in FCC-ee result can be rebuilt from the compact CSV/JSON files in
`results/fccee/`:

```bash
.venv/bin/python analysis/fccee_projection.py \
  --config analysis/configs/fccee_zpole_inputs.json \
  --out-dir results/fccee \
  --background-yields results/fccee/fccee_background_yields.csv \
  --background-bins results/fccee/fccee_background_bins.csv \
  --n-mass 180 \
  --n-g 180
```

Outputs:

```text
results/fccee/fccee_projection.csv
results/fccee/fccee_projection_summary.json
results/fccee/fccee_zpole_signature_classification.csv
results/fccee/fccee_zpole_signature_classification.png
```

Main scripts:

| Script | Role |
|---|---|
| `analysis/fccee_projection.py` | Solves invisible and prompt-resolved projected contours and writes the topology map. |
| `analysis/build_full_analysis_efficiency_map.py` | Converts detector-level signal samples into correction factors for the contour. |

## Stage 4: Example Signal/Background Figures

Build the background-plus-signal comparison plot:

```bash
.venv/bin/python analysis/plot_background_signal_examples.py \
  --config analysis/configs/fccee_zpole_inputs.json \
  --out-png results/fccee/background_signal_examples.png \
  --out-pdf results/fccee/background_signal_examples.pdf \
  --summary-csv results/fccee/background_signal_examples_summary.csv
```

Build a CMS-style prompt-resolved invariant-mass plot for one ALP point:

```bash
.venv/bin/python analysis/plot_prompt_resolved_invariant_mass.py \
  --mass 0.8 \
  --coupling 8e-5 \
  --x-min 0.0 \
  --x-max 2.5 \
  --out results/fccee/prompt_resolved_invariant_mass_example.png
```

Main scripts:

| Script | Role |
|---|---|
| `analysis/plot_background_signal_examples.py` | Shows binned backgrounds with example ALP templates. |
| `analysis/plot_prompt_resolved_invariant_mass.py` | Builds a two-panel $m_{\gamma\gamma}$ signal-plus-background plot. |

## Stage 5: AxionLimits Landscape And Money Plots

Build the ALP-photon landscape without FCC-ee overlays:

```bash
.venv/bin/python analysis/make_axionlimits_style_plot.py \
  --axionlimits-dir external/AxionLimits \
  --projection results/fccee/fccee_projection.csv \
  --constraint-set full \
  --no-fcc-ee \
  --output-stem results/fccee/axionlimits_alp_landscape_intro \
  --combined-output-stem results/fccee/axionlimits_alp_landscape_intro
```

Build the FCC-ee close-up money plot:

```bash
.venv/bin/python analysis/make_axionlimits_style_plot.py \
  --axionlimits-dir external/AxionLimits \
  --projection results/fccee/fccee_projection.csv \
  --constraint-set full \
  --output-stem results/fccee/money_plot_alp_full_closeup \
  --also-save-as results/fccee/money_plot \
  --m-min 1e7 \
  --m-max 1e12 \
  --g-min 1e-8 \
  --g-max 1e-1
```

The plotting code uses AxionLimits masses in eV internally, so the close-up
range above corresponds to $m_a=10^{-2}$--$10^3\,\mathrm{GeV}$.

Main script:

| Script | Role |
|---|---|
| `analysis/make_axionlimits_style_plot.py` | Loads AxionLimits and overlays FCC-ee projection contours. |

## Stage 6: Full MadGraph/Pythia/Delphes Signal Point

For a single detector-level ALP point:

```bash
source env/setup_nikhef_lcg.sh

mc/alp_signal/run_alp_full_pipeline.sh \
  results/alp_full_pipeline/example_fccee \
  1000 91.2 1.0 1e-5 \
  mc/delphes_cards/delphes_card_IDEA.tcl \
  resolved_prompt
```

That wrapper does:

```text
param_card -> MadGraph LHE -> Pythia HepMC -> Delphes ROOT
           -> theory validation -> detector histogram validation
```

Main files:

| File | Role |
|---|---|
| `mc/make_param_card.py` | Writes a point-specific ALP parameter card. |
| `mc/alp_signal/run_alp_full_pipeline.sh` | Runs one full ALP point end to end. |
| `mc/alp_signal/run_alp_pythia_delphes.cc` | Pythia8 ALP decay/lifetime and HepMC writer. |
| `analysis/alp_pipeline_histograms.py` | Validates detector-level photons, invariant masses, and recoil energies. |
| `theory/predictions/validate.py` | Checks cross section, width/lifetime convention, and file outputs. |

## Stage 7: Standard Model Background Production

For one background sample:

```bash
source env/setup_nikhef_lcg.sh

mc/backgrounds/run_sm_background_full_pipeline.sh \
  results/backgrounds/fccee_resolved_3gamma \
  resolved_3gamma \
  10000 \
  91.2 \
  mc/delphes_cards/delphes_card_IDEA.tcl
```

The two FCC-ee backgrounds used by the contour are:

| Label | Process | Observable |
|---|---|---|
| `resolved_3gamma` | $e^+e^-\to\gamma\gamma\gamma$ | diphoton invariant mass |
| `invisible_gamma_nunu` | $e^+e^-\to\gamma\nu\bar\nu$ | recoil-photon energy |

After the Delphes ROOT files exist, build the background inputs:

```bash
.venv/bin/python analysis/fccee_background_yields.py \
  --resolved-root <resolved_3gamma_delphes.root> \
  --resolved-banner <resolved_3gamma_banner.txt> \
  --invisible-root <invisible_gamma_nunu_delphes.root> \
  --invisible-banner <invisible_gamma_nunu_banner.txt> \
  --out results/fccee/fccee_background_yields.csv

.venv/bin/python analysis/fccee_binned_background.py \
  --resolved-root <resolved_3gamma_delphes.root> \
  --resolved-banner <resolved_3gamma_banner.txt> \
  --invisible-root <invisible_gamma_nunu_delphes.root> \
  --invisible-banner <invisible_gamma_nunu_banner.txt> \
  --out results/fccee/fccee_background_bins.csv \
  --summary-json results/fccee/fccee_background_bins_summary.json
```

Main scripts:

| Script | Role |
|---|---|
| `mc/backgrounds/run_sm_background_full_pipeline.sh` | Runs one SM background sample through MG5, Pythia, and Delphes. |
| `analysis/fccee_background_yields.py` | Builds single-window diagnostic background yields. |
| `analysis/fccee_binned_background.py` | Builds binned background histograms for the Asimov limit. |

## Stage 8: HTCondor Campaigns

On Nikhef/Stoomboot, the batch entrypoints are:

```bash
condor_submit condor/submit_background_scan.sub
condor_submit condor/submit_alp_full_projection_scan.sub
```

After the full ALP campaign finishes:

```bash
.venv/bin/python analysis/collect_alp_full_scan.py \
  results/alp_full_production/fccee_z_full_projection_fullbg_channelaware \
  --out results/fccee/alp_full_scan_summary.csv \
  --summary-json results/fccee/alp_full_scan_summary.json
```

Main files:

| File | Role |
|---|---|
| `condor/background_points_fccee_z.txt` | Two FCC-ee background jobs. |
| `condor/alp_full_points_fccee_z_projection.txt` | Detector-level ALP points around the projected contours. |
| `condor/submit_background_scan.sub` | Background submit file. |
| `condor/submit_alp_full_projection_scan.sub` | Full ALP signal submit file. |
| `analysis/collect_alp_full_scan.py` | Collects per-point summaries into `results/fccee/`. |

More details are in `condor/README.md`.

## Main Outputs

Belle II:

```text
results/belle2_closure/belle2_closure.png
results/belle2_closure/belle2_closure.pdf
results/belle2_closure/belle2_closure_summary.json
results/belle2_closure/belle2_closure_contour.csv
```

FCC-ee:

```text
results/fccee/fccee_projection.csv
results/fccee/fccee_projection_summary.json
results/fccee/fccee_zpole_signature_classification.csv
results/fccee/fccee_zpole_signature_classification.png
results/fccee/background_signal_examples.png
results/fccee/prompt_resolved_invariant_mass_example.png
results/fccee/money_plot.png
results/fccee/money_plot.pdf
```

## Current Numerical Summary

The checked-in FCC-ee Z-pole projection has:

| Branch | Mass span | Coupling span |
|---|---:|---:|
| Invisible lower | $0.01$--$0.92\,\mathrm{GeV}$ | $5.5$--$7.3\times10^{-7}\,\mathrm{GeV}^{-1}$ |
| Invisible upper | $0.01$--$0.92\,\mathrm{GeV}$ | $1.3\times10^{-6}$--$5.5\times10^{-2}\,\mathrm{GeV}^{-1}$ |
| Prompt-resolved | $0.61$--$80\,\mathrm{GeV}$ | $1.1\times10^{-5}$--$2.9\times10^{-4}\,\mathrm{GeV}^{-1}$ |

The invisible lower branch and prompt-resolved branch are the most stable
headline contours. The invisible upper branch is a short-lifetime boundary and
is more sensitive to detector and lifetime modeling.

The full signature grid has $180\times180=32{,}400$ points:

| Topology | Points |
|---|---:|
| prompt-resolved | 14,171 |
| invisible | 10,452 |
| merged | 5,989 |
| displaced-resolved | 1,788 |

## Caveats

The Belle II closure is a public-contour closure, not a reimplementation of the
private Belle II likelihood. The FCC-ee contours include leading SM
backgrounds and Delphes-derived correction factors, but they do not include
full detector systematics, beam-induced backgrounds, object misidentification,
or dedicated displaced/merged reconstruction.
