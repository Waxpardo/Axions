# Repository Build and Pipeline Report

This report explains how the Axions repository was built, why the current
layout and technical choices were made, where the files came from, how the
files work together, what was taken or adapted from other branches, and how to
run the full pipeline from a clean clone.

The canonical file-by-file provenance table is
`docs/file-provenance-report.md`. That file lists every tracked file returned by
`git ls-files`, classifies it as project-authored, generated, imported,
downloaded, adapted, or derived, and gives references for each file. This report
is the companion narrative: it explains the logic behind the repository and how
the pieces fit together.

## 1. Project Objective

The repository was built to simulate and analyze a photophilic Axion-Like
Particle (ALP) search at $e^+e^-$ colliders. The target signal is

$$
e^+e^- \to \gamma a,\qquad a\to\gamma\gamma,
$$

with the effective interaction

$$
\mathcal{L}\supset
\frac{g_{a\gamma\gamma}}{4}aF_{\mu\nu}\tilde F^{\mu\nu}.
$$

The two physical scan parameters are the invariant ALP mass $m_a$ and the
photon coupling $g_{a\gamma\gamma}$, measured in $\mathrm{GeV}$ and
$\mathrm{GeV}^{-1}$. The practical deliverable is a projected FCC-ee Z-pole
sensitivity contour in the $(m_a,g_{a\gamma\gamma})$ plane, overlaid on
existing ALP and QCD-axion constraints.

The repository also includes a Belle II public-contour closure test. That
closure is not a private Belle II likelihood reproduction. It is a validation
anchor that checks whether the public Belle II ALP contour can be reproduced
using the same production, width, lifetime, and detector-region logic as the
FCC-ee projection.

## 2. Design Philosophy

The repository was deliberately organized as a modular pipeline rather than as
one monolithic script. The project has several jobs that need different tools:

| Layer | Main job | Reason for separation |
|---|---|---|
| Theory | Compute analytic cross sections, widths, lifetimes, recoil energies, and opening angles. | These formulas are the validation ground truth and must be independent of MC implementation details. |
| MC production | Generate LHE, decay ALPs in Pythia, and run Delphes. | This is heavy, cluster-dependent work and should not be mixed with plotting or limit setting. |
| Analysis | Convert detector outputs into histograms, backgrounds, efficiency maps, and contours. | This is where the physics assumptions and statistical choices are applied. |
| Batch production | Run many points on Nikhef/Stoomboot with Condor. | Cluster execution needs small, restartable jobs and clean output contracts. |
| Documentation | Explain setup, assumptions, provenance, validation, and deliverables. | New collaborators should be able to understand and reproduce the project without reconstructing the conversation history. |
| Results | Store compact final CSV/JSON/plot deliverables. | Large raw files stay ignored; the report-facing products remain versioned. |

The most important design choice is that the final contour is not obtained by
running Delphes at every point in a dense two-dimensional grid. At tree level
the associated-production matrix element has

$$
\sigma(e^+e^-\to\gamma a)\propto g_{a\gamma\gamma}^2.
$$

This means the expensive detector simulation can be used to validate selected
signal points and build correction maps, while the full $(m_a,g)$ scan is done
with analytic production and lifetime formulas. That is why the repository has
both full-pipeline MC scripts and analytic projection scripts.

## 3. Repository Creation History

The repository began as a scaffold matching the project specification:

```text
analysis/
condor/
docs/
env/
external/
literature/
mc/
models/
results/
theory/
```

The first scaffold created the directory responsibilities and initial template
cards. The next development stages added, in order:

1. Theory validation scripts in `theory/predictions/`.
2. Nikhef setup documentation and a generic $e^+e^-\to\mu^+\mu^-$ smoke test.
3. The imported ALP UFO model under `models/ALP_linear/SM_alp_UFO/`.
4. ALP parameter-card writing through `mc/make_param_card.py`.
5. ALP production through MadGraph, Pythia, HepMC, and Delphes.
6. SM background production through the same MG5/Pythia/Delphes chain.
7. Binned FCC-ee background builders in `analysis/`.
8. Belle II public-contour closure.
9. FCC-ee projection and signature classification.
10. AxionLimits-style full and close-up money plots.
11. Final cleanup, consolidated READMEs, provenance documentation, and this report.

The final stable development branch is `Iñaki`. The remote branch
`origin/Iñaki` is the Nikhef-sync branch. The most recent synchronized baseline
before this report was commit `0507487`, which added the file provenance
report.

## 4. Why This Layout Was Chosen

The layout reflects the data flow:

```text
models/ + mc/cards/
  -> mc/make_param_card.py
  -> mc/alp_signal/ or mc/backgrounds/
  -> Delphes ROOT files
  -> analysis/*.py
  -> results/*.csv, *.json, *.png, *.pdf
  -> docs/ and final report
```

Each directory has a narrow responsibility:

| Directory | Role | Main dependencies | Main downstream users |
|---|---|---|---|
| `models/` | MadGraph UFO model. | Imported UFO from the ALP EFT model. | `mc/make_param_card.py`, MG5 process generation. |
| `mc/` | Event generation and detector simulation. | MG5, Pythia8, HepMC, Delphes, ROOT, UFO model. | `analysis/`, `results/`, `condor/`. |
| `theory/` | Analytic formulas and validation gates. | NumPy/SciPy, project conventions. | `analysis/fccee_projection.py`, MC validation scripts. |
| `analysis/` | Limit setting, backgrounds, efficiency maps, plots. | Python analysis stack, ROOT files through uproot, AxionLimits checkout. | `results/`, final figures. |
| `condor/` | Batch wrappers and submit files. | Nikhef/Stoomboot, `env/setup_nikhef_lcg.sh`, MC scripts. | Production outputs later summarized by `analysis/`. |
| `docs/` | Human-readable guides and project record. | Project files, references, run history. | New collaborators and final course deliverables. |
| `env/` | Environment setup. | LCG view, Python requirements. | Every MC/analysis command. |
| `external/` | Location for non-vendored external clones. | AxionLimits clone by user. | `analysis/axionlimits.py`, plotting. |
| `literature/` | Local reference PDFs. | Downloaded papers. | Report writing and citation checks. |
| `results/` | Compact checked-in outputs. | Analysis scripts. | Final report and presentation. |

The repository intentionally does not vendor full MadGraph, Pythia, ROOT, or
Delphes source trees. Those packages are large, platform-specific, and not
project code. On Nikhef they are supplied by the LCG environment and local MG5
installation. This choice keeps the repository reviewable and prevents the
"too many changes" warning from becoming worse.

## 5. Physics Choices and Why They Were Made

### 5.1 Associated Production as the Main Signal

The core signal is $e^+e^-\to\gamma a$. It was chosen because the recoil photon
is mono-energetic at fixed $(m_a,\sqrt{s})$:

$$
E_{\gamma,\mathrm{recoil}}=
\frac{s-m_a^2}{2\sqrt{s}}.
$$

This gives a clean observable in the invisible region and a simple kinematic
anchor for resolved events.

Photon fusion, $e^+e^-\to e^+e^-a$, was left out of the claimed signal reach.
It can be larger at high energy, but it relies on forward electrons and has a
different background problem. The project specification treated it as
background context rather than a primary deliverable.

### 5.2 FCC-ee Z Pole as the Baseline

The current FCC-ee baseline is the Z-pole run:

$$
\sqrt{s}=91.2\,\mathrm{GeV},\qquad
\mathcal{L}=150\,\mathrm{ab}^{-1}.
$$

This setting was chosen because the projected luminosity is enormous and the
project specification explicitly prioritizes it. Higher FCC-ee energies are
interesting future extensions, but each energy changes the production
kinematics, recoil-energy bins, angular-resolution boundary, backgrounds,
luminosity, and Delphes/selection assumptions. The Z-pole result was therefore
locked first to finish one controlled deliverable.

### 5.3 Width Convention

The project uses

$$
\Gamma(a\to\gamma\gamma)=
\frac{g_{a\gamma\gamma}^2m_a^3}{64\pi}.
$$

This convention is implemented in `theory/predictions/predict_grid.py` and
`mc/make_param_card.py`. It is also used to set the ALP width passed to Pythia.
The UFO's direct `decays.py` expression gives a width corresponding to a
coupling normalization larger by $\sqrt{2}$, which is why Gate 2 is explicitly
implemented. The production pipeline writes the physical $64\pi$ width into
`DECAY 9999` so that lifetime-dependent regions use the same convention as the
analysis.

### 5.4 UFO Coupling Mapping

The imported UFO does not expose a direct parameter named
$g_{a\gamma\gamma}$. It uses `fa`, `KB`, and `KW`. For the production
normalization validated against the analytic formula, the mapping is

$$
g_{a\gamma\gamma}=
\frac{\alpha_{\mathrm{em}}(K_B+K_W)}
{\sqrt{2}\pi f_a}.
$$

This mapping lives in `mc/make_param_card.py` and is mirrored in
`theory/predictions/validate.py`. The default card writer splits `KB` and `KW`
so that the tree-level $\gamma Za$ coupling cancels. That choice keeps the
default scan photophilic and avoids accidentally turning on the stretch-goal
resonant process $Z\to\gamma a$.

### 5.5 Signal Regions

The grid is classified using the boosted decay length

$$
\ell_a=
\frac{|\mathbf{p}_a|}{m_a}
\frac{\hbar c}{\Gamma_a}
$$

and the light-ALP opening-angle estimate

$$
\Delta\theta_{\min}\simeq \frac{4m_a}{\sqrt{s}}.
$$

The implemented contour regions are:

| Region | Condition | Included in contour? |
|---|---|---|
| Invisible | ALP survives past $L_{\max}$. | Yes. |
| Prompt/resolved | ALP decays before $L_{\min}$ and daughter photons resolve. | Yes. |
| Displaced/resolved | ALP decays between $L_{\min}$ and $L_{\max}$ and daughter photons resolve. | Classified only. |
| Merged | ALP decays inside detector but daughter photons do not resolve. | Classified only. |

Displaced and merged searches need dedicated reconstruction and background
models, so they are not claimed as exclusion contours in the current result.

## 6. External Sources and Imported Material

The exact file-by-file source information is in
`docs/file-provenance-report.md`. The important imported or downloaded sources
are:

| Material | Local path | Source and role |
|---|---|---|
| ALP UFO model | `models/ALP_linear/SM_alp_UFO/` | FeynRules-generated UFO associated with the ALP EFT model used by Bauer, Neubert, and Thamm. Used by MadGraph to generate ALP matrix elements. |
| FCC IDEA Delphes reference card | `mc/delphes_cards/fcc_idea/card_IDEA_winter2023.tcl` | Imported FCC-ee IDEA Winter 2023 Delphes card. Used as the reference card for the adapted IDEA card. |
| Literature PDFs | `literature/` | Downloaded project references: Tammaro-Zupan tutorial, Belle II ALP paper, Bauer/Neubert/Thamm papers, AxionLimits/QCD axion context. |
| AxionLimits data | external clone at `external/AxionLimits` | Not vendored. Used to load existing constraints and Belle II public contour data. Pinned in `analysis/configs/axionlimits_source.json`. |
| Belle II public curve | `results/belle2_closure/belle2_closure_target.csv` | Derived from AxionLimits `BelleII.txt` and used as the closure target. |

Everything else in `analysis/`, `condor/`, `docs/`, `env/`, `mc/`, `results/`,
and `theory/` is project-authored or project-generated unless the provenance
report explicitly labels it otherwise.

## 7. How the Main Files Work Together

### 7.1 Theory Files

`theory/predictions/predict_grid.py` is the analytic source of truth. It
computes:

- $\Gamma(a\to\gamma\gamma)$,
- $c\tau$,
- boosted decay length $\ell_a$,
- $\sigma(e^+e^-\to\gamma a)$,
- recoil photon energy,
- opening-angle estimates, and
- detector-region probabilities.

`theory/predictions/validate.py` is the validation gatekeeper. It checks MG5
cross sections against the analytic cross section, checks the width/lifetime
convention, verifies smoke-test outputs, and runs the Belle II closure through
`analysis/belle2_closure.py`.

`theory/predictions/theory_grid.csv` is generated from `predict_grid.py`. It is
not the final result; it is a compact analytic grid used for sanity checks and
plotting diagnostics.

`theory/Cross.nb` is a Mathematica notebook retained for theory derivation
work. The production code does not depend on it.

### 7.2 Model and Parameter Card Files

`models/ALP_linear/SM_alp_UFO/` is the imported UFO model. The key identifiers
inside it are:

```text
ALP name: alp
ALP PDG: 9999
photon name: a
mass parameter: Malp
width parameter: Walp
coupling block: ALP with fa, Kg, KB, KW, Cta, Cb, Ct
```

`mc/make_param_card.py` is the bridge between physical scan parameters and the
UFO. It takes $(m_a,g_{a\gamma\gamma})$, computes the required `KB + KW` at a
chosen `fa`, writes the ALP mass, writes the ALP width, and emits a MadGraph
`param_card.dat`.

The files under `mc/cards/belle2/` and `mc/cards/fccee/` are baseline cards.
They are useful templates and historical anchors, but the production scripts
mostly write point-specific cards dynamically so the scan can vary mass and
coupling cleanly.

### 7.3 Monte Carlo Signal Files

`mc/alp_signal/run_alp_mg5_production.sh` runs MadGraph for one
$e^+e^-\to\gamma a$ point. It creates a process directory, writes a point
parameter card with `mc/make_param_card.py`, sets the beam energy from
$\sqrt{s}/2$, and produces an LHE file.

`mc/alp_signal/run_alp_pythia_delphes.cc` is the C++ Pythia/HepMC runner for
ALP signal. It reads the LHE file, turns on QED ISR/FSR, forces or enables
$a\to\gamma\gamma$, synchronizes the lifetime using the width written by the
param card, and writes `events.hepmc`.

`mc/alp_signal/run_alp_full_pipeline.sh` is the stable one-point end-to-end
entrypoint. It calls the MG5 production script, compiles the C++ Pythia runner,
runs Pythia, runs Delphes, validates the output with
`theory/predictions/validate.py`, and checks detector-level histograms with
`analysis/alp_pipeline_histograms.py`.

`mc/alp_signal/run_alp_gate2_width.sh` exists specifically to reproduce the
width/lifetime convention check. It isolates the `64\pi` versus UFO-width
normalization issue so the convention is not hidden inside the full pipeline.

`mc/alp_signal/run_fccee_zpole_smoke.sh` is a convenience wrapper for a small
FCC-ee ALP smoke test.

### 7.4 Monte Carlo Background Files

`mc/backgrounds/run_sm_background_full_pipeline.sh` is the stable background
entrypoint. It generates one SM background process with MG5, showers it with
Pythia using `mc/backgrounds/run_pythia_hepmc.cc`, runs Delphes, and leaves a
ROOT file plus banner for analysis.

The current FCC-ee backgrounds are:

$$
e^+e^-\to\gamma\gamma\gamma
$$

for prompt/resolved diphoton mass backgrounds, and

$$
e^+e^-\to\gamma\nu\bar{\nu}
$$

for invisible recoil-photon backgrounds.

### 7.5 Detector Cards

`mc/delphes_cards/delphes_card_IDEA.tcl` is the project FCC-ee card used by the
final config. It is adapted from the imported IDEA Winter 2023 reference card.

`mc/delphes_cards/fcc_idea/card_IDEA_winter2023.tcl` is kept as the imported
reference. Keeping the original reference separate makes later detector-card
changes auditable.

`mc/delphes_cards/delphes_card_Belle2.tcl` and
`mc/delphes_cards/delphes_card_belle2_validation.tcl` are project-authored
Belle II-style cards. Belle II does not provide an official Delphes card for
this analysis, so these cards are validation approximations, not official Belle
II detector simulations.

### 7.6 Analysis Files

`analysis/alp_pipeline_histograms.py` validates a detector-level signal point.
For prompt/resolved points it checks reconstructed photon multiplicity and the
best diphoton invariant mass. For invisible points it checks the recoil photon.
It writes a ROOT histogram file and a JSON summary used by later collection
scripts.

`analysis/fccee_binned_background.py` reads full-stat Delphes background ROOT
files and builds the binned background table used by the final contour:

$$
N_{B,\mathrm{bin}}=
\sigma_B\mathcal{L}
\frac{N_{\mathrm{raw,bin}}}{N_{\mathrm{generated}}}.
$$

`analysis/fccee_background_yields.py` builds older window-yield diagnostic
background tables. These are retained for checks, but the binned method is the
final method.

`analysis/fccee_projection.py` solves the FCC-ee contour. It reads
`analysis/configs/fccee_zpole_inputs.json`, binned backgrounds, and the
Delphes-derived correction map. For each mass and channel it solves for the
coupling satisfying the 90 percent CL Asimov requirement

$$
\Delta\chi^2=2.71
$$

with a three-event floor.

`analysis/build_full_analysis_efficiency_map.py` turns detector-level ALP scan
summaries into the final analysis-bin correction map. The final contour uses
the branch-aware `detector_correction_factor` from
`results/fccee/alp_full_analysis_efficiency_map.csv`.

`analysis/collect_alp_full_scan.py` collects many Condor point summaries into
compact CSV/JSON files under `results/fccee/`.

`analysis/axionlimits.py` locates and loads the external AxionLimits checkout.
It also handles unit conversion so the project can overlay FCC-ee results on
AxionLimits curves.

`analysis/make_axionlimits_style_plot.py` is the final plotting entrypoint. It
executes the relevant AxionLimits plotting code in a controlled way, relabels
axes and text to ALP language where appropriate, keeps QCD axion reference
regions, and overlays FCC-ee contours as translucent/dashed projections.

`analysis/belle2_closure.py` reconstructs the Belle II public contour logic at
published-contour level. It loads AxionLimits' Belle II curve, converts units,
infers an effective Belle II event threshold, and solves back for the contour
using the project formulas.

### 7.7 Config Files

`analysis/configs/fccee_zpole_inputs.json` is the locked FCC-ee input file. It
contains $\sqrt{s}$, luminosity, detector lengths, photon thresholds,
resolution assumptions, background paths, and efficiency-correction settings.
The projection reads this file rather than hardcoding detector assumptions in
the script.

`analysis/configs/belle2_closure_inputs.json` is the locked Belle II closure
config. It records the Belle II energy, public luminosity, geometry and
threshold assumptions, angular resolution, and closure tolerance.

`analysis/configs/axionlimits_source.json` pins the external AxionLimits source
and commit used for context curves.

### 7.8 Condor Files

`condor/make_alp_mass_grid.py` creates one-dimensional mass grids for the
production-only scan. That scan uses one reference coupling because
$\sigma\propto g^2$.

`condor/make_alp_full_points_from_projection.py` turns the analytic projection
branches into detector-level signal points to be checked by Delphes.

`condor/run_alp_point.sh` runs one production-only ALP point.

`condor/run_alp_full_point.sh` runs one full detector-level ALP point.

`condor/run_background_point.sh` runs one full detector-level SM background
point.

`condor/submit_alp_scan.sub`, `condor/submit_alp_full_scan.sub`,
`condor/submit_alp_full_projection_scan.sub`, and
`condor/submit_background_scan.sub` are the corresponding Stoomboot submit
files.

The text files in `condor/*.txt` are generated or locked point lists. They have
no header row because Condor's `queue ... from <file>` treats every non-empty
row as a job.

### 7.9 Environment and Setup Files

`env/requirements.txt` pins the Python analysis packages: NumPy, SciPy,
matplotlib, uproot, awkward, vector, pandas, and related tools.

`env/setup_nikhef_lcg.sh` configures the Nikhef/Stoomboot software environment.
It resets compiler-related variables, loads the LCG view, sets `MG5ROOT`,
`LCG_VIEW`, `PYTHIA8_ROOT`, `PYTHIA8DATA`, and updates `PATH`.

The `docs/nikhef-*.md` files explain first login, GitHub SSH setup, VS Code
Remote SSH, and the MG5/Pythia/HepMC/Delphes smoke-test procedure.

### 7.10 Results Files

The files under `results/belle2_closure/` are generated closure outputs:
plots, contour CSV, JSON summary, and a markdown report.

The files under `results/fccee/` are generated FCC-ee outputs:
background tables, efficiency maps, scan summaries, projection contours,
signature classification grids, and money plots.

These are checked in because they are compact deliverables. Large raw ROOT,
HepMC, LHE, MG5 process directories, and Condor scratch outputs are ignored.

## 8. Branch Integration Report

The final stable branch is `Iñaki`. Other branches were reviewed and used
selectively. Direct broad merges were avoided because several branches carried
generated event files, full process directories, source trees, binaries, or
older hardcoded assumptions.

### 8.1 `origin/main`

Useful content:

- Confirmed the ALP UFO content.
- Contained earlier Belle II ALP validation artifacts.

What was used:

- The UFO model content was kept in stable form under
  `models/ALP_linear/SM_alp_UFO/`.
- The UFO model was the useful part retained for the final pipeline. Earlier
  compact Belle II validation artifacts were removed during the final cleanup
  because the integrated Belle II closure now lives under `results/belle2_closure/`.

Modifications:

- The UFO was kept inside `models/ALP_linear/SM_alp_UFO/` rather than a flat
  `models/SM_alp_UFO/` path, matching the project specification.
- Full MG5 generated directories and raw event files were not retained.

### 8.2 `origin/Oliver`

Useful content:

- FCC-ee ALP process syntax and validation direction.
- Recognition that the ALP name in the UFO is `alp` and the photon is `a`.
- Early combined SM+ALP and truth-level accounting ideas.

What was used:

- The ALP process syntax became the basis for
  `mc/alp_signal/run_alp_mg5_production.sh`.
- The idea of channel-aware validation fed into
  `analysis/alp_pipeline_histograms.py` and the full-scan collection logic.
- FCC-ee background thinking was folded into `mc/backgrounds/` and
  `analysis/fccee_binned_background.py`.

Modifications:

- The final scripts were rewritten to be configurable by work directory,
  event count, $\sqrt{s}$, mass, coupling, Delphes card, and validation
  channel.
- Hardcoded FCC-ee-only assumptions were moved into
  `analysis/configs/fccee_zpole_inputs.json`.
- The final branch kept stable results and docs that Oliver's branch did not
  contain.

### 8.3 `origin/briac`

Useful content:

- Belle II and muon-validation ideas.
- Nikhef LCG setup direction.

What was used:

- The concept of an $e^+e^-\to\mu^+\mu^-$ smoke test was kept.
- The final version lives in `mc/hepmc_smoke_test/` and is detector/energy
  configurable.

Modifications:

- The smoke test was rewritten to avoid hardcoding Belle II or FCC-ee as a
  software-chain check.
- The final smoke test validates invariant mass and software handoff rather
  than acting as a physics result.

### 8.4 `origin/Camille`

Useful content:

- Simple setup scripts.
- C++ Pythia/HepMC reader examples.

What was used:

- The C++ pattern of reading LHE in Pythia and writing HepMC was adapted into
  `mc/hepmc_smoke_test/run_pythia.cc`,
  `mc/backgrounds/run_pythia_hepmc.cc`, and
  `mc/alp_signal/run_alp_pythia_delphes.cc`.

Modifications:

- The final scripts compile against the LCG environment and include zlib/HepMC
  handling needed on Nikhef.
- The setup was consolidated into `env/setup_nikhef_lcg.sh` rather than several
  branch-specific scripts.

### 8.5 `origin/Serge`

Useful content:

- A broad pipeline prototype.
- Evidence about Delphes/Pythia setup issues.

What was used:

- The branch helped diagnose that Delphes must be run with a consistent ROOT,
  HepMC, and compiler environment.
- This reinforced the choice to use the LCG view and not a random mixture of
  local binaries.

Modifications:

- Full `Delphes-3.5.1/`, `pythia8313/`, compiled objects, and large generated
  artifacts were intentionally not merged.
- The stable branch keeps only project-level scripts and cards, not software
  source trees.

### 8.6 `origin/effy`

Useful content:

- Early analysis files and ALP parameter-card examples.

What was used:

- Param-card block structure and early analysis ideas were used as references.

Modifications:

- Generated MG5 directories were not imported.
- The final analysis was rewritten around explicit configs, binned
  backgrounds, branch-aware efficiency corrections, and AxionLimits provenance.

## 9. Full Pipeline From Scratch

This section assumes a new collaborator starts from no local clone.

> **Shortcut:** every command in 9.2 and 9.6-9.13 (the locally-runnable parts
> of this narrative -- venv setup, AxionLimits clone, theory grid, Belle II
> closure, FCC-ee projection, money plots) is also wired up in the top-level
> `Makefile`. Run `make help`, `make status`, or `make local-all` to drive and
> inspect the local stages. The narrative below remains the authoritative
> reference for what each command does and why -- the Makefile is a convenience
> wrapper around exactly these steps, including the bootstrap/efficiency-map/
> projection ordering described in 9.11-9.12. Section 9.3, 9.5, and 9.9 (MC production
> and HTCondor submission) still require following the manual steps below on
> a Nikhef/Stoomboot node with the LCG stack sourced; the corresponding `make`
> targets exist mainly to fail fast with a pointer back here when run
> elsewhere.

### 9.1 Clone the Repository

On a normal machine:

```bash
git clone git@github.com:Waxpardo/Axions.git
cd Axions
git checkout Iñaki
```

On Nikhef, first log in and make a personal directory:

```bash
ssh -X -Y username@login.nikhef.nl
ssh -X -Y username@stbc-i1
cd /data/alice
mkdir -p username
cd username
git clone git@github.com:Waxpardo/Axions.git
cd Axions
git checkout Iñaki
```

If GitHub SSH is not set up yet, follow
`docs/nikhef-first-login-github-ssh.md`.

### 9.2 Set Up Python

For local analysis:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r env/requirements.txt
```

The Python environment is enough to rebuild theory grids, validate compact
outputs, rebuild projection CSVs from existing backgrounds, and make plots.

### 9.3 Install or Locate the MC Stack

On Nikhef, install or locate MadGraph under your `/data/alice/<username>`
directory, then edit `env/setup_nikhef_lcg.sh` if your `MG5ROOT` path differs.

Then source:

```bash
source env/setup_nikhef_lcg.sh
```

Check the tools:

```bash
which mg5_aMC
which g++
which pythia8-config
which root-config
which DelphesHepMC2
python3 --version
```

The project expects these commands to be available before running MC scripts.

### 9.4 Clone AxionLimits

AxionLimits is not vendored into this repo. Clone it only when you need the
Belle II closure or the money plot:

```bash
mkdir -p external
git clone https://github.com/cajohare/AxionLimits.git external/AxionLimits
cd external/AxionLimits
git checkout 7d375f4879b32406a239fe48d2615a4bfd9bc0bb
cd ../..
```

The pinned source is recorded in
`analysis/configs/axionlimits_source.json`.

### 9.5 Run the Generic Software Smoke Test

Before ALP production, test the software chain with a simple SM process:

```bash
cd mc/hepmc_smoke_test
./run_mg5_to_delphes_smoke_test.sh work 1000 100.0 ../../mc/delphes_cards/delphes_card_belle2_validation.tcl
cd ../..
```

Validate it:

```bash
python3 theory/predictions/validate.py mc/hepmc_smoke_test/work --pipeline-smoke
```

This proves that MG5, Pythia, HepMC, Delphes, ROOT, and Python can talk to one
another. It is not a Belle II or FCC-ee physics result.

### 9.6 Build the Analytic Theory Grid

```bash
python theory/predictions/predict_grid.py \
  --out theory/predictions/theory_grid.csv
```

This creates a grid of cross sections, widths, lifetimes, decay lengths, and
opening angles. It is useful for sanity checks and for understanding which
parts of the $(m_a,g)$ plane are invisible, prompt, displaced, or merged.

### 9.7 Run the Belle II Closure

With AxionLimits available:

```bash
python theory/predictions/validate.py \
  --belle2-closure \
  --axionlimits-dir external/AxionLimits
```

Expected outputs:

```text
results/belle2_closure/belle2_closure.png
results/belle2_closure/belle2_closure.pdf
results/belle2_closure/belle2_closure_contour.csv
results/belle2_closure/belle2_closure_summary.json
```

The current closure passes with

$$
\max\left|\log_{10}
\left(\frac{g_{\mathrm{closure}}}{g_{\mathrm{published}}}\right)\right|
\simeq 7.59\times10^{-3}.
$$

### 9.8 Run One Full ALP Signal Point

Example Belle II-style validation point:

```bash
source env/setup_nikhef_lcg.sh
mc/alp_signal/run_alp_full_pipeline.sh \
  results/alp_full_pipeline/example_belle2 \
  1000 10.58 1.0 1e-5 \
  mc/delphes_cards/delphes_card_Belle2.tcl \
  resolved_prompt
```

Example FCC-ee Z-pole point:

```bash
source env/setup_nikhef_lcg.sh
mc/alp_signal/run_alp_full_pipeline.sh \
  results/alp_full_pipeline/example_fccee \
  1000 91.2 1.0 1e-5 \
  mc/delphes_cards/delphes_card_IDEA.tcl \
  resolved_prompt
```

The work directory will contain LHE, HepMC, Delphes ROOT, validation summaries,
and histograms.

### 9.9 Run SM Background Production

For a manual background point:

```bash
source env/setup_nikhef_lcg.sh
mc/backgrounds/run_sm_background_full_pipeline.sh \
  results/background_production/resolved_3gamma \
  resolved_3gamma 10000 91.2 \
  mc/delphes_cards/delphes_card_IDEA.tcl
```

and

```bash
source env/setup_nikhef_lcg.sh
mc/backgrounds/run_sm_background_full_pipeline.sh \
  results/background_production/invisible_gamma_nunu \
  invisible_gamma_nunu 10000 91.2 \
  mc/delphes_cards/delphes_card_IDEA.tcl
```

For full production on Nikhef use Condor:

```bash
condor_submit condor/submit_background_scan.sub
```

### 9.10 Build Binned Backgrounds

After background ROOT files exist:

```bash
python3 analysis/fccee_binned_background.py \
  --resolved-root <resolved_3gamma_delphes.root> \
  --resolved-banner <resolved_3gamma_banner.txt> \
  --invisible-root <invisible_gamma_nunu_delphes.root> \
  --invisible-banner <invisible_gamma_nunu_banner.txt> \
  --out results/fccee/fccee_background_bins.csv \
  --summary-json results/fccee/fccee_background_bins_summary.json
```

The binned output is the final contour input. The older diagnostic window
background can be built with `analysis/fccee_background_yields.py`.

### 9.11 Submit Detector-Level ALP Signal Points

The projection-derived signal scan is submitted with:

```bash
condor_submit condor/submit_alp_full_projection_scan.sub
```

Each job calls `condor/run_alp_full_point.sh`, which calls
`mc/alp_signal/run_alp_full_pipeline.sh`.

After completion, collect the summaries:

```bash
python3 analysis/collect_alp_full_scan.py \
  results/alp_full_production/fccee_z_full_projection_fullbg_channelaware \
  --out results/fccee/alp_full_scan_summary.csv \
  --summary-json results/fccee/alp_full_scan_summary.json
```

Then build the final detector-correction map:

```bash
python3 analysis/build_full_analysis_efficiency_map.py \
  --scan-summary results/fccee/alp_full_scan_summary.csv \
  --projection results/fccee/fccee_projection.csv \
  --out results/fccee/alp_full_analysis_efficiency_map.csv \
  --summary-json results/fccee/alp_full_analysis_efficiency_summary.json
```

### 9.12 Rebuild the FCC-ee Projection

```bash
python analysis/fccee_projection.py \
  --config analysis/configs/fccee_zpole_inputs.json \
  --out-dir results/fccee \
  --background-yields results/fccee/fccee_background_yields.csv \
  --background-bins results/fccee/fccee_background_bins.csv \
  --n-mass 180 \
  --n-g 180
```

This writes:

```text
results/fccee/fccee_projection.csv
results/fccee/fccee_projection_summary.json
results/fccee/fccee_zpole_signature_classification.csv
results/fccee/fccee_zpole_signature_classification.png
```

### 9.13 Rebuild the Money Plots

Full landscape with astrophysical, cosmological, dark-matter, lab, collider,
and QCD axion reference regions:

```bash
python analysis/make_axionlimits_style_plot.py \
  --axionlimits-dir external/AxionLimits \
  --projection results/fccee/fccee_projection.csv \
  --constraint-set full \
  --output-stem results/fccee/money_plot_alp_full \
  --also-save-as results/fccee/money_plot \
  --combined-output-stem results/fccee/money_plot_alp_full_combined
```

FCC-ee close-up:

```bash
python analysis/make_axionlimits_style_plot.py \
  --axionlimits-dir external/AxionLimits \
  --projection results/fccee/fccee_projection.csv \
  --constraint-set full \
  --output-stem results/fccee/money_plot_alp_full_closeup \
  --m-min 1e7 \
  --m-max 1e12 \
  --g-min 1e-8 \
  --g-max 1e-1
```

## 10. How the Final Contour Is Computed

For each point and channel, the signal expectation is

$$
N_S =
\mathcal{L}\,
\sigma(m_a,g_{a\gamma\gamma})\,
P_{\mathrm{region}}(m_a,g_{a\gamma\gamma})\,
\epsilon_{\mathrm{parametric}}\,
C_{\mathrm{Delphes}}.
$$

The factors come from different files:

| Factor | File/source |
|---|---|
| $\mathcal{L}$ | `analysis/configs/fccee_zpole_inputs.json` |
| $\sigma$ | `theory/predictions/predict_grid.py` |
| $P_{\mathrm{region}}$ | `analysis/fccee_projection.py`, using theory decay length formulas |
| $\epsilon_{\mathrm{parametric}}$ | `analysis/configs/fccee_zpole_inputs.json` |
| $C_{\mathrm{Delphes}}$ | `results/fccee/alp_full_analysis_efficiency_map.csv` |
| $N_B$ | `results/fccee/fccee_background_bins.csv` |

The binned background model gives the required signal count. For a normalized
signal shape $f_i$ and expected background $B_i$, the code uses

$$
N_{\mathrm{signal,req}} =
\max\left(
3,\,
\sqrt{\frac{2.71}{\sum_i f_i^2/\max(B_i,1)}}
\right).
$$

The contour is the coupling where

$$
N_S(m_a,g_{a\gamma\gamma})=
N_{\mathrm{signal,req}}(m_a).
$$

The invisible branch can have two roots because production grows like $g^2$,
but the probability to survive the detector decreases at large $g$. Therefore
the output has `invisible_lower` and `invisible_upper`. The prompt/resolved
branch is monotonic and appears as `resolved_prompt`.

## 11. Why Some Choices May Look Unusual

### Why not generate every $(m_a,g)$ point with Delphes?

That would be expensive and unnecessary because the cross section scales
exactly as $g^2$ at tree level for the single-vertex associated-production
signal. The detector simulation is used where it matters: validating the
pipeline, estimating channel-aware detector corrections, and building
backgrounds.

### Why keep generated results in `results/`?

The checked-in results are compact deliverables: CSVs, JSON summaries, and
plots. They let a collaborator inspect the final state without rerunning a
large Condor campaign. Large raw files stay ignored.

### Why keep the imported UFO in the repo?

MadGraph needs the UFO locally and exactly. The model is small enough to vendor
cleanly, unlike full Pythia or Delphes source trees.

### Why pin AxionLimits but not vendor it?

AxionLimits is large and external. The project only needs it for context
curves, so the repo records the exact commit and asks collaborators to clone it
into `external/AxionLimits`.

### Why use an IDEA card but explicit $L_{\min}$ and $L_{\max}$?

Delphes handles reconstructed objects, not all analysis-level lifetime-region
boundaries. The prompt/invisible classification uses explicit detector-length
assumptions in `analysis/configs/fccee_zpole_inputs.json`, while the IDEA card
models object reconstruction and resolutions.

### Why include QCD axion and DM/astro/cosmo constraints on an ALP plot?

They are part of the existing axion-photon landscape and are important context.
The plot labels and report must explain that some regions have additional
model assumptions. The FCC-ee projection is overlaid separately and should be
described as a collider sensitivity, not as a replacement for every
assumption-dependent bound.

## 12. File Provenance Contract

Use these rules when deciding whether a file belongs in the repository:

1. Project-authored code, configs, cards, docs, and compact results belong in
   git.
2. Imported small model/card files belong in git only when they are required to
   reproduce the project and their source is documented.
3. External clones such as AxionLimits belong under `external/` but are not
   vendored.
4. Large raw outputs, ROOT files, HepMC files, LHE files, MG5 process
   directories, Condor scratch directories, compiled binaries, and software
   source trees should stay ignored.
5. Every tracked file should have an entry in `docs/file-provenance-report.md`.

This is why the final branch did not merge full generated directories from
other branches even when those branches contained useful ideas.

## 13. Final Deliverable State

The repository currently contains the pieces needed for the project deliverable:

| Deliverable | Evidence |
|---|---|
| Belle II public-contour closure | `results/belle2_closure/` |
| Full ALP MG5/Pythia/Delphes point pipeline | `mc/alp_signal/run_alp_full_pipeline.sh` |
| SM background MG5/Pythia/Delphes pipeline | `mc/backgrounds/run_sm_background_full_pipeline.sh` |
| FCC-ee binned backgrounds | `results/fccee/fccee_background_bins.csv` |
| FCC-ee detector-corrected contours | `results/fccee/fccee_projection.csv` |
| Signature classification | `results/fccee/fccee_zpole_signature_classification.csv` |
| Money plots | `results/fccee/money_plot_alp_full*.png` and `.pdf` |
| Setup and run documentation | `README.md`, `docs/`, selected directory READMEs, and `Makefile` |
| File provenance | `docs/file-provenance-report.md` |

The main limitations are physics limitations, not missing infrastructure:

- Belle II closure is based on the public curve, not the private likelihood.
- FCC-ee detector systematics and beam-induced backgrounds are not included.
- Merged and displaced signatures are classified but not converted into final
  contours.
- The invisible upper branch is detector-corrected but numerically fragile in
  part of the low-mass tail.
- Additional FCC-ee energies would require new configs, backgrounds, and
  detector-correction campaigns.

## 14. Recommended Maintenance Procedure

When a collaborator changes the project:

1. Add or modify the code in the appropriate layer.
2. Put detector or analysis assumptions in `analysis/configs/`, not hidden in a
   script.
3. Update the local directory README if the workflow changes.
4. Run `python -m compileall -q analysis theory mc condor`.
5. Run the relevant validation gate:
   - smoke test for environment changes,
   - Gate 1/Gate 2 for signal-production changes,
   - Belle II closure for theory/lifetime changes,
   - projection rebuild for background/limit changes.
6. Update `docs/file-provenance-report.md` if new tracked files are added.
7. Keep large raw outputs out of git.

This keeps the repository usable for both local development and Nikhef
production.
