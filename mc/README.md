# Monte Carlo Pipeline

This directory contains the event-generation side of the repository:

```text
MadGraph5_aMC -> LHE
Pythia8       -> HepMC
Delphes       -> ROOT
Python checks -> JSON and histogram summaries
```

There are three main modes:

| Mode | Directory | Purpose |
|---|---|---|
| Generic smoke test | `mc/hepmc_smoke_test/` | Checks that MG5, Pythia, HepMC, ROOT, and Delphes work together. |
| ALP signal | `mc/alp_signal/` | Produces $e^+e^-\to\gamma a$, decays $a\to\gamma\gamma$, and runs Delphes. |
| SM backgrounds | `mc/backgrounds/` | Produces the FCC-ee background samples used in the binned limits. |

## Environment

On Nikhef/Stoomboot, source the LCG setup before running production scripts:

```bash
source env/setup_nikhef_lcg.sh
```

The scripts expect these commands on `PATH`:

```text
mg5_aMC
pythia8-config
root-config
DelphesHepMC2
g++
python3
```

If your MadGraph install is not in the default location, set `MG5ROOT` first:

```bash
export MG5ROOT=/data/alice/<username>/MadGraph5_aMC/MG5_aMC_v3_7_1
source env/setup_nikhef_lcg.sh
```

## ALP Parameter Cards

The physical scan parameters are:

```text
m_a                 ALP mass in GeV
g_aγγ               ALP-photon coupling in GeV^-1
```

The UFO model uses `fa`, `KB`, and `KW` rather than exposing
$g_{a\gamma\gamma}$ directly. The helper script maps the physical coupling to
the UFO parameters:

$$
g_{a\gamma\gamma}=
\frac{\alpha_{\mathrm{em}}(K_B+K_W)}
{\sqrt{2}\,\pi f_a}.
$$

By default, `mc/make_param_card.py` splits `KB + KW` so the tree-level
$a\gamma Z$ coupling vanishes. That keeps the generated process aligned with
the photophilic benchmark:

$$
e^+e^-\to\gamma^\ast\to\gamma a.
$$

The same script writes the ALP width:

$$
\Gamma(a\to\gamma\gamma)=
\frac{g_{a\gamma\gamma}^2m_a^3}{64\pi}.
$$

Generate a standalone parameter card:

```bash
python3 mc/make_param_card.py \
  --m-a 1.0 \
  --g-agg 1e-5 \
  --out mc/cards/fccee/param_card.dat
```

## Generic Smoke Test

Use this when setting up a new machine or cluster account:

```bash
cd mc/hepmc_smoke_test
./run_mg5_to_delphes_smoke_test.sh work 1000 100.0 "$DELPHES_CARD"
cd ../..
```

Then validate it:

```bash
python3 theory/predictions/validate.py \
  mc/hepmc_smoke_test/work \
  --pipeline-smoke
```

This test uses $e^+e^-\to\mu^+\mu^-$ and is independent of Belle II or FCC-ee
physics settings. It only checks that the software chain works.

## Full ALP Signal Point

Run one detector-level ALP point:

```bash
mc/alp_signal/run_alp_full_pipeline.sh \
  <work_dir> <n_events> <sqrt_s_GeV> <m_a_GeV> <g_agg_GeV_inv> \
  <delphes_card> <validation_channel>
```

Example:

```bash
mc/alp_signal/run_alp_full_pipeline.sh \
  results/alp_full_pipeline/example_fccee \
  1000 91.2 1.0 1e-5 \
  mc/delphes_cards/delphes_card_IDEA.tcl \
  resolved_prompt
```

The wrapper runs:

1. `mc/make_param_card.py`
2. MadGraph production, $e^+e^-\to\gamma a$
3. Pythia ALP decay/lifetime and HepMC writing
4. Delphes detector simulation
5. `theory/predictions/validate.py`
6. `analysis/alp_pipeline_histograms.py --require-pass`

Allowed validation channels:

```text
resolved_prompt
invisible
production_only
```

For `resolved_prompt`, the validation requires at least three reconstructed
photons and checks that the best diphoton pair reconstructs $m_a$. For
`invisible`, it checks the recoil photon and does not require reconstructed
ALP daughter photons.

## ALP Signal Files

| File | Purpose |
|---|---|
| `alp_signal/run_alp_full_pipeline.sh` | Full MG5 -> Pythia -> Delphes -> validation chain for one point. |
| `alp_signal/run_alp_mg5_production.sh` | MadGraph production-only stage. |
| `alp_signal/run_alp_pythia_delphes.cc` | Pythia8 ALP decay/lifetime and HepMC writer. |
| `alp_signal/run_alp_gate2_width.sh` | Width-convention diagnostic using MG5 `compute_widths`. |
| `alp_signal/run_fccee_zpole_smoke.sh` | Small FCC-ee signal smoke helper. |

For each full ALP point, the work directory contains:

```text
alp_production/
events.hepmc
pythia_lifetime_summary.json
delphes.root
delphes.log
validation_plots/
alp_histograms.root
alp_histograms_summary.json
full_point_summary.csv
```

Full production directories are large and are ignored by git. The compact
summaries used by the analysis live in `results/fccee/`.

## Background Production

Run one Standard Model background point:

```bash
mc/backgrounds/run_sm_background_full_pipeline.sh \
  <work_dir> <process_name> <n_events> <sqrt_s_GeV> <delphes_card>
```

Example:

```bash
mc/backgrounds/run_sm_background_full_pipeline.sh \
  results/backgrounds/fccee_resolved_3gamma \
  resolved_3gamma \
  10000 \
  91.2 \
  mc/delphes_cards/delphes_card_IDEA.tcl
```

The FCC-ee background labels are:

| Label | Process | Used for |
|---|---|---|
| `resolved_3gamma` | $e^+e^-\to\gamma\gamma\gamma$ | prompt-resolved $M_{\gamma\gamma}$ background |
| `invisible_gamma_nunu` | $e^+e^-\to\gamma\nu\bar\nu$ | invisible recoil-photon background |

Background helper files:

| File | Purpose |
|---|---|
| `backgrounds/run_sm_background_full_pipeline.sh` | MG5 -> Pythia -> Delphes background chain. |
| `backgrounds/run_pythia_hepmc.cc` | Pythia8 shower and HepMC writer for background LHE files. |

After the ROOT files exist, use the analysis scripts to build:

```text
results/fccee/fccee_background_yields.csv
results/fccee/fccee_background_bins.csv
```

## Detector Cards

Detector cards live in `mc/delphes_cards/`:

| Card | Use |
|---|---|
| `delphes_card_Belle2.tcl` | Belle II-style validation. |
| `delphes_card_IDEA.tcl` | FCC-ee IDEA baseline projection. |
| `delphes_card_belle2_validation.tcl` | Small Belle II-style smoke card. |
| `fcc_idea/card_IDEA_winter2023.tcl` | Reference IDEA card copied into the repo. |

The FCC-ee config points to:

```text
mc/delphes_cards/delphes_card_IDEA.tcl
```
