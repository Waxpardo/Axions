# Photophilic ALP Search at e+e- Colliders

This repository contains the simulation and analysis pipeline for a
photophilic Axion-Like Particle (ALP) search at electron-positron colliders.
The signal process is associated production,

```text
e+ e- -> gamma a,  a -> gamma gamma
```

with the effective interaction

```text
L contains (g_agg / 4) a F_{mu nu} Ftilde^{mu nu}.
```

The project has two roles:

1. Reproduce Belle II at the level available from public information.
2. Produce an FCC-ee Z-pole projected sensitivity contour and money plot.

The current stable branch is `Iñaki`.

## Current Deliverable Status

The core computational deliverable is in place:

| Item | Status | Output |
|---|---:|---|
| Belle II validation anchor | complete | `results/belle2_closure/` |
| ALP MG5 -> Pythia -> Delphes signal pipeline | complete | `mc/alp_signal/` |
| SM background MG5 -> Pythia -> Delphes pipeline | complete | `mc/backgrounds/` |
| FCC-ee Z-pole binned backgrounds | complete | `results/fccee/fccee_background_bins.csv` |
| FCC-ee detector-corrected projection | complete | `results/fccee/fccee_projection.csv` |
| Signature classification over the full grid | complete | `results/fccee/fccee_zpole_signature_classification.csv` |
| Money plots with AxionLimits context | complete | `results/fccee/money_plot*.png` and `.pdf` |
| Setup/run documentation | complete | `docs/`, plus directory READMEs |

The remaining limitations are physics limitations, not missing software pieces:
merged and displaced signatures are classified but not turned into exclusion
contours, and the FCC-ee projection does not include detector systematics,
machine backgrounds, or pileup-like effects.

## Physics Conventions

The project uses the following locked conventions:

```text
metric: mostly minus
epsilon^{0123}: +1
g_agg units: GeV^-1
hbar c: 1.973269804e-16 GeV m
Gamma(a -> gamma gamma): g_agg^2 m_a^3 / (64 pi)
```

The analytic validation formulas are:

```text
sigma(e+e- -> gamma a)
  = alpha g_agg^2 / 12 * (1 - m_a^2 / s)^3

E_gamma,recoil
  = (s - m_a^2) / (2 sqrt(s))

ell_a
  = (|p_a| / m_a) * hbar c / Gamma_a

Delta theta_min
  ~= 4 m_a / sqrt(s)
```

These formulas are implemented in `theory/predictions/predict_grid.py` and are
the source of truth for analysis-side production, lifetime, and kinematic
checks.

## Main Analysis Assumptions

The current FCC-ee result is a Z-pole projection:

```text
sqrt(s) = 91.2 GeV
luminosity = 150 ab^-1
detector model = IDEA-style Delphes card
```

The locked inputs are in:

```text
analysis/configs/fccee_zpole_inputs.json
```

Important values are:

```text
L_min = 0.02 m
L_max = 2.5 m
eta_max = 3.0
minimum photon energy = 0.5 GeV
photon efficiency = 0.99
diphoton angular resolution = 1.5 deg
resolved mass resolution = max(5 percent, 0.05 GeV)
invisible recoil resolution = max(5 percent, 0.5 GeV)
```

Why these matter:

| Input | Used for |
|---|---|
| `L_min_m` | prompt vs displaced decay boundary |
| `L_max_m` | invisible survival probability |
| `eta_max` | recoil-photon angular acceptance |
| `photon_energy_min_GeV` | basic reconstructed photon threshold |
| `delta_theta_res_deg` | resolved vs merged diphoton classification |
| mass/recoil resolutions | signal smearing into binned backgrounds |

## Pipeline Overview

The full detector-level chain for one ALP point is:

```text
param_card.dat
  -> MadGraph5_aMC LHE production
  -> Pythia8 ALP decay/lifetime and HepMC
  -> Delphes detector ROOT
  -> Python validation histograms
  -> efficiency maps and contour corrections
```

The final contour itself is not produced by brute-forcing every coupling with
Delphes. Instead, it combines:

1. Analytic production and lifetime as a function of `(m_a, g_agg)`.
2. Binned SM backgrounds from full-stat Delphes samples.
3. Delphes-derived detector corrections from a contour-point signal campaign.

This keeps the full scan tractable while still anchoring the final contour to
detector-level signal and background samples.

## Repository Layout

```text
.
├── analysis/              Python limit-setting, plotting, background builders
│   └── configs/           Locked analysis inputs and external-source provenance
├── condor/                Nikhef/Stoomboot batch submit files and point lists
├── docs/                  Human-facing setup, method, status, and runbook notes
├── env/                   Python and Nikhef environment setup
├── external/              Non-vendored external data clones, especially AxionLimits
├── literature/            Reference PDFs used by the project
├── mc/                    MadGraph, Pythia, Delphes, and detector cards
├── models/ALP_linear/     UFO model used by MadGraph
├── results/               Checked-in final CSV/JSON/plot deliverables
└── theory/predictions/    Analytic formulas and validation gates
```

Each major directory now has its own README explaining how that layer works.

## Setup

For a local Python analysis environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r env/requirements.txt
```

For Nikhef/Stoomboot production, follow:

```text
docs/nikhef-first-login-github-ssh.md
docs/nikhef-mg5-pythia-hepmc-smoke-test.md
docs/nikhef-vscode-remote-ssh-guide.md
```

Then source the LCG environment:

```bash
source env/setup_nikhef_lcg.sh
```

## AxionLimits Data

AxionLimits is used only as an external context layer for existing constraints.
It is not vendored into this repository. Clone it with:

```bash
git clone https://github.com/cajohare/AxionLimits.git external/AxionLimits
```

The final source metadata is locked in:

```text
analysis/configs/axionlimits_source.json
```

The current pinned commit is:

```text
7d375f4879b32406a239fe48d2615a4bfd9bc0bb
```

## Validation Gates

Run the Belle II public-contour closure:

```bash
python theory/predictions/validate.py \
  --belle2-closure \
  --axionlimits-dir external/AxionLimits
```

The current closure passes with:

```text
max |log10(g_closure / g_published)| = 7.59e-3
tolerance = 2.0e-2
```

For one detector-level ALP point, the full pipeline wrapper runs Gates 1 and 2,
Pythia lifetime synchronization, Delphes output validation, and channel-aware
histogram checks:

```bash
mc/alp_signal/run_alp_full_pipeline.sh \
  <work_dir> <n_events> <sqrt_s_GeV> <m_a_GeV> <g_agg_GeV_inv> \
  <delphes_card> <validation_channel>
```

Example:

```bash
mc/alp_signal/run_alp_full_pipeline.sh \
  results/alp_full_pipeline/example_belle2 \
  1000 10.58 1.0 1e-5 \
  mc/delphes_cards/delphes_card_Belle2.tcl \
  resolved_prompt
```

The generic software smoke test, independent of ALPs and detector assumptions,
is documented in `docs/nikhef-mg5-pythia-hepmc-smoke-test.md`.

## Rebuilding The FCC-ee Result

The final-style FCC-ee projection requires binned SM backgrounds and the
Delphes-derived efficiency map already present in `results/fccee/`.

Rebuild the projection:

```bash
python analysis/fccee_projection.py \
  --config analysis/configs/fccee_zpole_inputs.json \
  --out-dir results/fccee \
  --background-yields results/fccee/fccee_background_yields.csv \
  --background-bins results/fccee/fccee_background_bins.csv \
  --n-mass 180 \
  --n-g 180
```

Rebuild the generic-ALP money plot:

```bash
python analysis/make_axionlimits_style_plot.py \
  --axionlimits-dir external/AxionLimits \
  --projection results/fccee/fccee_projection.csv \
  --constraint-set generic \
  --output-stem results/fccee/money_plot_generic_alp \
  --also-save-as results/fccee/money_plot
```

The `generic` constraint set intentionally omits constraints that require the
ALP to be the cosmological dark matter. Use `--constraint-set full` only when
the report explicitly wants the full AxionLimits reference landscape.

Build the FCC-ee close-up:

```bash
python analysis/make_axionlimits_style_plot.py \
  --axionlimits-dir external/AxionLimits \
  --projection results/fccee/fccee_projection.csv \
  --constraint-set generic \
  --output-stem results/fccee/money_plot_generic_alp_closeup \
  --m-min 1e7 \
  --m-max 1e12 \
  --g-min 1e-8 \
  --g-max 1e-1
```

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
results/fccee/money_plot_generic_alp.png
results/fccee/money_plot_generic_alp.pdf
results/fccee/money_plot_generic_alp_closeup.png
results/fccee/money_plot_generic_alp_closeup.pdf
```

## What The Code Actually Does

The analysis code is split by responsibility:

| File | Role |
|---|---|
| `theory/predictions/predict_grid.py` | analytic formulas for sigma, width, lifetime, opening angle |
| `theory/predictions/validate.py` | central validation gates and MC-output checks |
| `mc/make_param_card.py` | maps physical `g_agg` to UFO-native `fa`, `KB`, `KW` |
| `analysis/fccee_binned_background.py` | turns Delphes background ROOT files into normalized histograms |
| `analysis/fccee_projection.py` | solves the binned FCC-ee exclusion contours |
| `analysis/build_full_analysis_efficiency_map.py` | converts detector-level signal scans into correction factors |
| `analysis/make_axionlimits_style_plot.py` | draws existing bounds and overlays FCC-ee projections |

More detail is in `analysis/README.md`, `mc/README.md`, and
`theory/predictions/README.md`.

## Limits And Caveats

Belle II closure is a public-contour closure, not a private Belle II likelihood
reimplementation. The code infers the effective signal-yield threshold implied
by the published curve because the private background spectra, reconstruction
efficiencies, and likelihood are not available here.

FCC-ee invisible and prompt-resolved contours use leading SM backgrounds and
detector-derived correction factors. They do not yet include systematic
uncertainties, beam-induced backgrounds, detector noise, or dedicated merged and
displaced reconstruction models.
