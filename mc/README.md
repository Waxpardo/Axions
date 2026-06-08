# Monte Carlo Pipeline

This directory contains the event-generation side of the project:

```text
MadGraph5_aMC -> LHE
Pythia8 -> HepMC
Delphes -> ROOT
Python validation -> JSON/ROOT summaries
```

There are three production modes:

| Mode | Directory | Purpose |
|---|---|---|
| Generic smoke test | `mc/hepmc_smoke_test/` | Proves MG5, Pythia, HepMC, ROOT, and Delphes work on the cluster. |
| ALP signal | `mc/alp_signal/` | Produces $e^+e^-\to\gamma a$, decays $a\to\gamma\gamma$, runs Delphes. |
| SM backgrounds | `mc/backgrounds/` | Produces background channels for FCC-ee binned limits. |

## ALP Parameter Cards
The physical scan parameters are $m_a$, the ALP mass in GeV, and
$g_{a\gamma\gamma}$, the photon coupling in $\mathrm{GeV}^{-1}$.

The UFO does not expose $g_{a\gamma\gamma}$ directly. Instead, it uses:

```text
fa, KB, KW
```

`mc/make_param_card.py` maps the physical coupling to the UFO-native
parameters using the Gate-1 production normalization:

$$
g_{a\gamma\gamma}=
\frac{\alpha_{\mathrm{em}}(K_B+K_W)}
{\sqrt{2}\,\pi f_a}.
$$

By default, it splits `KB + KW` so that the tree-level $\gamma Z a$ coupling
vanishes. That keeps the production aligned with the photophilic process we are
studying. The script writes:

```text
DECAY 9999 <Gamma_a>
```

with:

$$
\Gamma(a\to\gamma\gamma)=
\frac{g_{a\gamma\gamma}^2 m_a^3}{64\pi}.
$$

This is the convention used by the analysis and by Pythia.

## Full ALP Signal Pipeline

Stable entrypoint:

```bash
mc/alp_signal/run_alp_full_pipeline.sh \
  <work_dir> <n_events> <sqrt_s_GeV> <m_a_GeV> <g_agg_GeV_inv> \
  <delphes_card> <validation_channel>
```

The script performs:

1. Generate a param card from $(m_a,g_{a\gamma\gamma})$.
2. Run MadGraph for $e^+e^-\to a\gamma$.
3. Parse the physical ALP width from the param card.
4. Compile the Pythia/HepMC runner.
5. Run Pythia with ISR/FSR and $a\to\gamma\gamma$.
6. Write a Pythia lifetime summary JSON.
7. Run Delphes with the selected detector card.
8. Run `theory/predictions/validate.py` on the point.
9. Run `analysis/alp_pipeline_histograms.py --require-pass`.

The validation channel can be:

```text
resolved_prompt
invisible
production_only
```

For `resolved_prompt`, the histogram validation requires at least three
reconstructed photons and checks that the best diphoton pair reconstructs the
requested ALP mass. For `invisible`, it only requires a recoil photon near the
two-body recoil energy.

Signal helper files:

| File | Purpose |
|---|---|
| `alp_signal/run_alp_full_pipeline.sh` | Full MG5 -> Pythia -> Delphes -> validation chain for one point. |
| `alp_signal/run_alp_mg5_production.sh` | MadGraph production-only stage. |
| `alp_signal/run_alp_pythia_delphes.cc` | Pythia8 ALP decay/lifetime and HepMC writer. |
| `alp_signal/run_alp_gate2_width.sh` | Width-convention diagnostic using MG5 `compute_widths`. |
| `alp_signal/run_fccee_zpole_smoke.sh` | Small FCC-ee signal smoke helper. |

The production pipeline writes the project width explicitly into the param
card and passes the same value to Pythia. The diagnostic
`alp_signal/run_alp_gate2_width.sh` documents the known UFO width-normalization
difference and is the reproducible Gate-2 check.

The completed FCC-ee detector-level signal campaign used by the current paper
draft is `fccee_z_full_projection_fullbg_channelaware`: 284 projection-derived
points, all passing Gate 1 and channel-aware detector validation. Its compact
outputs live in `results/fccee/alp_full_scan_summary.*` and
`results/fccee/alp_full_analysis_efficiency_*`.

## Signal Output Files

For each full ALP point, the work directory contains:

```text
alp_production/                 MadGraph process directory
events.hepmc                    Pythia event record
pythia_lifetime_summary.json    width and decay-length diagnostics
delphes.root                    detector output
delphes.log                     Delphes log
validation_plots/               Gate 1/2 and file-validation summary
alp_histograms.root             photon and invariant-mass histograms
alp_histograms_summary.json     channel-aware validation result
```

These files are large for full campaigns and should normally live under ignored
production directories. The summarized CSV/JSON products in `results/fccee/`
are the report-facing outputs.

## Background Pipeline

Stable entrypoint:

```bash
mc/backgrounds/run_sm_background_full_pipeline.sh \
  <work_dir> <process_name> <n_events> <sqrt_s_GeV> <delphes_card>
```

The current FCC-ee backgrounds are:

| Label | Process | Used for | Paper-draft sample |
|---|---|---|---|
| `resolved_3gamma` | $e^+e^-\to\gamma\gamma\gamma$ | prompt/resolved diphoton mass background | 10,000 events, `sigma = 7.3063 pb`, 23,592 pair entries |
| `invisible_gamma_nunu` | $e^+e^-\to\gamma\nu\bar\nu$ | recoil-photon invisible background | 10,000 events, `sigma = 134.885 pb`, 2,684 recoil entries |

Background helper files:

| File | Purpose |
|---|---|
| `backgrounds/run_sm_background_full_pipeline.sh` | MG5 -> Pythia -> Delphes background chain. |
| `backgrounds/run_pythia_hepmc.cc` | Pythia8 shower and HepMC writer for background LHE files. |

After the ROOT files exist, the analysis layer builds:

```text
results/fccee/fccee_background_yields.csv
results/fccee/fccee_background_bins.csv
```

The binned file is the final contour input.

## Detector Cards

Detector cards live in:

```text
mc/delphes_cards/
```

Current cards:

| Card | Use |
|---|---|
| `delphes_card_Belle2.tcl` | Belle II-style local validation. |
| `delphes_card_IDEA.tcl` | FCC-ee IDEA baseline projection. |
| `delphes_card_belle2_validation.tcl` | Smaller validation/smoke card. |
| `fcc_idea/card_IDEA_winter2023.tcl` | Vendor/reference IDEA card. |

The final FCC-ee config points to:

```text
mc/delphes_cards/delphes_card_IDEA.tcl
```

## Smoke Test

Before ALP production on a new cluster account, run the generic
$e^+e^-\to\mu^+\mu^-$ smoke test:

```bash
cd mc/hepmc_smoke_test
./run_mg5_to_delphes_smoke_test.sh work 1000 100.0 "$DELPHES_CARD"
```

Then validate:

```bash
python3 theory/predictions/validate.py \
  mc/hepmc_smoke_test/work \
  --pipeline-smoke
```

This smoke test does not use Belle II or FCC-ee physics settings. It is only a
software-chain test.

## Environment

On Nikhef:

```bash
source env/setup_nikhef_lcg.sh
```

That script sets:

```text
MG5ROOT
LCG_VIEW
PYTHIA8_ROOT
PYTHIA8DATA
PATH
```

The production scripts assume `mg5_aMC`, `pythia8-config`, `root-config`,
`DelphesHepMC2`, `g++`, and `python3` are on `PATH`.
