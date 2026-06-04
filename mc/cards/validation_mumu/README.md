# Validation sample: `e+ e- -> mu+ mu-`

This directory is the **toolchain smoke test** for the ALP analysis pipeline
(`MadGraph -> Pythia -> Delphes -> ROOT -> limits`). It uses a pure Standard-Model
process whose cross-section is analytically known, so we can confirm the generator
and our beam/run settings are correct *before* trusting any ALP signal numbers.
It is fully isolated from the ALP production cards in `mc/cards/belle2/` and `mc/cards/fccee/`.

## Physics: the known answer

At tree level the QED process `e+ e- -> gamma* -> mu+ mu-` has

```
sigma = 4*pi*alpha^2 / (3 s)
```

At Belle II energy **sqrt(s) = 10.58 GeV** (so `s = 111.9 GeV^2`) this gives
**sigma ~ 0.87 nb** (about 0.067 pb in the high-energy `86.8 nb*GeV^2 / s` form... i.e. ~0.8 nb).
Including the small photon/Z interference shifts it slightly, so the expected band is

> **Validation gate: sigma(e+e- -> mu+ mu-) ~ 0.8 - 0.9 nb**

If MadGraph reports a cross-section in this band, Stage 1 passes and the generator +
beam configuration are trustworthy.

## How to run (on NIKHEF, after review)

```bash
cd /data/alice/ojansons/Axions
source env/setup_lcg105.sh
mg5_aMC mc/cards/validation_mumu/mg5_mumu.dat
# or, equivalently, the wrapper:
bash mc/gen_validation_mumu.sh
```

Beams are symmetric 5.29 GeV (lpp=0, no PDF). The total cross-section depends only on
`s`, so symmetric beams are equivalent to Belle II's real 7x4 GeV asymmetric beams.

## Where to read the cross-section

After the run, MadGraph reports the cross-section in three places:

- terminal summary at the end of `launch`,
- `PROC_validation_mumu/crossx.html` (per-run table), and
- the run banner `PROC_validation_mumu/Events/run_01/run_01_tag_1_banner.txt`
  (line `#  Integrated weight (pb)`).

The parton-level events land at
`PROC_validation_mumu/Events/run_01/unweighted_events.lhe.gz`.

## Outputs are not committed

`PROC_validation_mumu/`, `*.lhe(.gz)`, `*.hepmc`, and `*.root` are already in
`.gitignore` — generated artifacts stay out of the repository by design.

## Stage 2: showering with Pythia8 (standalone, not MG5-driven)

### Why MadGraph cannot drive Pythia in this environment

When Stage 1 runs `launch`, the program-switch menu shows `shower = Not Avail.`
MadGraph here cannot hand events to Pythia8. This is an **LCG packaging limitation**,
not a fixable misconfiguration on our side:

- In the LCG MG5 config
  (`.../madgraph5amc/3.5.2.../input/mg5_configuration.txt`) both `pythia8_path`
  (line 70) and `mg5amc_py8_interface_path` (line 77) are **commented out** — MG5
  has no Pythia to call and no interface to steer it.
- The **MG5aMC_PY8_interface** (the small C++ bridge MG5 compiles to talk to
  Pythia8) is not bundled (no `HEPTools/` dir), and LCG ships **no prebuilt
  interface package** anywhere under `MCGenerators/` to point at.
- The MG5 install tree is owned by `cvmfs` (read-only), so MG5's own
  `install mg5amc_py8_interface` cannot write into it.

Restoring MG5-driven Pythia would require a user-level config plus
`install mg5amc_py8_interface`, which **downloads from the MG5 server** (outbound
internet — typically unavailable on Condor workers) and **compiles a version-pinned
interface** against Pythia 8.310 (compatibility not guaranteed). It would not
reproduce on the batch farm.

### What we do instead

Run Pythia8 **standalone**. Pythia 8.310 (libs, headers, examples) and HepMC2 are
already in LCG_105, so a small compiled program reads the LHE, runs the real parton
shower, and writes HepMC for `DelphesHepMC2` — with no network, reproducible on
Condor. This genuinely exercises the Pythia stage (it is not a bypass) and becomes
the permanent `Pythia/HepMC` node for the ALP production pipeline too.

```bash
cd /data/alice/ojansons/Axions
bash mc/shower_validation_mumu.sh    # builds the driver, then showers the Stage-1 LHE
```

Validation check: the program writes a valid HepMC2 file and each event still
contains ~2 muons (plus any radiated photons). Output (git-ignored):
`PROC_validation_mumu/Events/run_01/showered_mumu.hepmc`.

## Stage 3: detector simulation with Delphes

Feed the Stage-2 HepMC into Delphes and confirm muons are reconstructed:

```bash
cd /data/alice/ojansons/Axions
bash mc/delphes_validation_mumu.sh
```

This runs `DelphesHepMC2` with `mc/delphes_cards/delphes_card_belle2_validation_mumu.tcl`
and then a ROOT check. Validation check: the `Delphes` tree has mean `Muon_size` ≈ 2
and most events carry ≥2 reconstructed muons. Output (git-ignored):
`PROC_validation_mumu/Events/run_01/delphes_mumu.root`.

Tiny-sample first (recommended): `bash mc/delphes_validation_mumu.sh 20` truncates
the HepMC to the first 20 events; no argument runs the full sample.

### Jet-clustering disabled for the μ⁺μ⁻ smoke test

`e+ e- -> mu+ mu-` has **no hadronic final state**, so the Durham *exclusive* jet
finders inherited from CircularEE (`ExclusiveFastJetFinder_N2/N4/N6`) were being
asked for N exclusive jets from 0 input particles → `fastjet::Error` → **segfault**.
We therefore use a **minimal** dedicated card,
`delphes_card_belle2_validation_mumu_minimal.tcl`, which defines **only** the
modules the muon-pair smoke test needs: particle propagation, tracking
efficiency, momentum smearing, `TrackMerger`, muon efficiency, and `TreeWriter`.
All jet-clustering, b/c/τ-tagging, jet-energy-scale, jet-flavor, calorimeter/EFlow,
isolation, MissingET and `UniqueObjectFinder` modules are **not defined at all**
(the channel has no hadronic final state). `TreeWriter` writes only `Particle`,
`Track`, and `Muon` (plus the automatic `Event` branch). The Belle II tunings
(Bz, acceptance, muon-ID) are carried over. Both broader cards
(`delphes_card_belle2_validation.tcl` and the partially-trimmed
`..._mumu.tcl`) are left untouched.

If Delphes still segfaults **at exit** (after 100%), it is a Delphes/ROOT
finalization issue, not reconstruction — the ROOT file is written before teardown.
Verify it is complete and readable:
```bash
root -l -b -q 'mc/delphes_validation_check.C("PROC_validation_mumu/Events/run_01/delphes_mumu.root")'
```
If the `Delphes` tree is present with mean `Muon_size` ≈ 2, Stage 3 passes and the
exit crash is cosmetic.

### Detector card: Belle-II-inspired, validation-only

There is **no official Belle II Delphes card** (in the repo, on CVMFS, or in the
Delphes distribution — Belle II uses full simulation, basf2). So
`delphes_card_belle2_validation.tcl` is **derived from the stock CircularEE card**
and retuned toward Belle II. It is a **software-chain validation card, NOT validated
Belle II detector performance** — a real Belle II card remains a deferred task.

Belle-II-aligned changes (vs CircularEE; see the card header for inline `BELLE2:` marks):

| Parameter | CircularEE | Belle II validation | Basis |
|-----------|-----------|---------------------|-------|
| Solenoid `Bz` | 3.5 T | 1.5 T | Belle II solenoid |
| `Radius`/`HalfLength` | 1.81/2.35 m | 1.13/1.40 m | CDC outer radius |
| Track acceptance | \|η\|≤3.0 | \|η\|≤1.32 | CDC polar 17–150° |
| Muon-ID threshold | energy>2.0 | energy>0.6 GeV | KLM muon-ID onset |
| Muon-ID acceptance | \|η\|≤1.5/3.0 | \|η\|≤1.13 | KLM polar ~25–145° |
| Muon-ID efficiency | 0.99 | 0.98 | Belle II muon-ID |

Inherited unchanged (not Belle-II-tuned, irrelevant to this μμ check): momentum
smearing, calorimeter, jets, b/τ-tagging. Known simplification: Belle II's real
acceptance is asymmetric (7×4 GeV boost); this validation used symmetric 5.29 GeV
beams, so a symmetric \|η\| acceptance is applied.

## Files here / used by this validation

| File | Stage | Role |
|------|-------|------|
| `mg5_mumu.dat`       | 1 | MG5 driver: define process, beams, generate parton-level LHE |
| `pythia8_mumu.cmnd`  | 2 | Pythia8 steering: read the LHE, shower, write HepMC2 |
| `../../pythia/shower_lhe.cc` | 2 | Standalone Pythia8 LHE→HepMC2 program (vendored Pythia `main44.cc`) |
| `../../pythia/Makefile`      | 2 | Builds `shower_lhe` against LCG Pythia8 + HepMC2 |
| `../../shower_validation_mumu.sh` | 2 | Stage-2 entrypoint: build + shower + report |
| `../../delphes_cards/delphes_card_belle2_validation.tcl` | 3 | Belle-II-inspired Delphes card (validation-only) |
| `../../delphes_validation_check.C` | 3 | ROOT macro: count reconstructed muons |
| `../../delphes_validation_mumu.sh` | 3 | Stage-3 entrypoint: Delphes + muon check |

Batch submission (Stage 4, HTCondor) lives in `condor/` and is added only after the
interactive Stage-3 test succeeds.
