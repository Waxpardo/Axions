# Nikhef MG5 -> Pythia -> HepMC -> Delphes Setup

This guide starts from a fresh Nikhef/Stoomboot login and ends with a verified
software pipeline:

```text
MadGraph -> LHE -> Pythia -> HepMC -> ROOT histograms -> Delphes ROOT
```

The test process is:

```text
e+ e- -> mu+ mu-
```

This is only a software smoke test. It proves that the cluster environment,
compiler, MadGraph, Pythia, HepMC, ROOT, and Delphes can talk to each other. It
does not validate the ALP physics process; ALP validation is done later with the
physics gates in `theory/predictions/validate.py`.

The smoke test is deliberately generic. It does not hard-code Belle II,
FCC-ee, or any analysis detector choice into the pipeline. The center-of-mass
energy and Delphes detector card are inputs to the smoke script; the defaults
are only convenient software-test values.

## 1. Prerequisites

You need:

- A Nikhef account that can log in to `login.nikhef.nl`.
- Access to the Stoomboot interactive nodes, for example `stbc-i1`.
- GitHub SSH access configured on Nikhef.

If GitHub SSH is not configured yet, first follow:

```text
docs/nikhef-first-login-github-ssh.md
```

The commands below use `username` as a placeholder. Replace it with your Nikhef
username.

## 2. Log In To Nikhef And Stoomboot

From your laptop:

```bash
ssh -X -Y username@login.nikhef.nl
```

From the Nikhef login machine:

```bash
ssh -X -Y username@stbc-i1
```

If `stbc-i1` is busy, another interactive node such as `stbc-i2` or `stbc-i3`
is also fine.

## 3. Create Your Personal Alice Work Directory

On the Stoomboot node:

```bash
cd /data/alice
mkdir -p username
cd username
```

The project files and any local MadGraph installation should live under this
directory, not in your small home directory.

## 4. Clone The Repository

Still inside `/data/alice/username`:

```bash
git clone git@github.com:Waxpardo/Axions.git
cd Axions
```

Check out the branch that contains the current pipeline files. At the time of
writing this is:

```bash
git checkout Iñaki
git pull --ff-only origin Iñaki
```

If this work has already been merged into `main`, use:

```bash
git checkout main
git pull --ff-only origin main
```

## 5. MadGraph Choice

For the smoke test, the default Nikhef setup script uses the CVMFS LCG software
view. On the tested Stoomboot setup, this provides a working `mg5_aMC`, so a
separate local MadGraph download is not required just to run the smoke test.

For production work, or if `mg5_aMC` is not available from the LCG view, install
MadGraph under `/data/alice/username`:

```bash
cd /data/alice/username
wget https://launchpad.net/mg5amcnlo/3.0/3.7.x/+download/MG5_aMC_v3.7.1.tar.gz
tar xzf MG5_aMC_v3.7.1.tar.gz
mkdir -p MadGraph5_aMC
mv MG5_aMC_v3_7_1 MadGraph5_aMC/
```

The expected local path is then:

```text
/data/alice/username/MadGraph5_aMC/MG5_aMC_v3_7_1
```

If you use a different version or directory name, set `MG5ROOT` to that path
before sourcing the environment.

## 6. Set Up The Cluster Environment

From the repository root:

```bash
cd /data/alice/username/Axions
source env/setup_nikhef_lcg.sh
```

If you installed your own MadGraph:

```bash
cd /data/alice/username/Axions
export MG5ROOT=/data/alice/username/MadGraph5_aMC/MG5_aMC_v3_7_1
source env/setup_nikhef_lcg.sh
```

The setup script defaults to:

```text
/cvmfs/sft.cern.ch/lcg/views/LCG_108/x86_64-el9-gcc15-opt
```

This default is intentional. Earlier checks with `LCG_106_ATLAS_13` worked for
MG5, Pythia, HepMC, and ROOT, but the available Delphes package on Nikhef failed
against that ROOT with a missing `TF1::GradientPar` symbol. The `LCG_108` setup
uses a matching compiler/ROOT/Delphes combination for the full chain.

The script sets or reports:

```text
MG5ROOT
LCG_VIEW
PYTHIA8_ROOT
PYTHIA8DATA
DELPHES_DIR
DELPHES_CARD
```

## 7. Verify The Tools

After sourcing `env/setup_nikhef_lcg.sh`, run:

```bash
which mg5_aMC
which pythia8-config
which root-config
which DelphesHepMC2
echo "$DELPHES_CARD"
```

The `which` commands should print paths. `DELPHES_CARD` should point to a real
Delphes card. On the current Nikhef CVMFS setup the default is the generic
Delphes validation card:

```text
.../validation_card.tcl
```

That default is only for the software smoke test. For ALP production, choose and
pass the relevant detector card explicitly when the analysis point is chosen.

## 8. Run The Full Smoke Pipeline

From the repository root:

```bash
cd mc/hepmc_smoke_test
./run_mg5_to_delphes_smoke_test.sh work 100 100.0 "$DELPHES_CARD"
```

The arguments are:

```text
work              output directory
100               number of events
100.0             generic e+e- sqrt(s) in GeV
"$DELPHES_CARD"   detector card to use for Delphes
```

Use `100` events for a quick setup check and `1000` for a slightly stronger
test. The `100.0 GeV` value is not a Belle II or FCC-ee setting; it is just a
generic high-energy lepton-collider smoke-test value chosen to avoid low-energy
MadGraph card edge cases.

The script performs these steps:

```text
1. Create a MadGraph process card for e+ e- -> mu+ mu-
2. Set a lepton-collider run card with lpp1 = lpp2 = 0
3. Set ebeam1 = ebeam2 = sqrt(s)/2
4. Generate LHE events with MadGraph
5. Run Pythia on the LHE file
6. Write HepMC2 ASCII output
7. Read the HepMC file with a small C++ checker
8. Write simple ROOT histograms from the HepMC file
9. Run DelphesHepMC2 with the selected detector card
```

Expected files:

```text
mc/hepmc_smoke_test/work/ee_mumu_test/Events/run_01/unweighted_events.lhe.gz
mc/hepmc_smoke_test/work/events.hepmc
mc/hepmc_smoke_test/work/analysis.root
mc/hepmc_smoke_test/work/delphes.root
```

## 9. Validate The Smoke Output

From the repository root:

```bash
python3 theory/predictions/validate.py \
  mc/hepmc_smoke_test/work \
  --pipeline-smoke
```

This mode checks that the expected pipeline files exist and are non-empty. If
`uproot` is available, it also checks:

```text
analysis.root contains h_nparticles, h_pt, h_eta, h_phi, h_charged_lepton_pt
delphes.root contains the Delphes tree
```

The command writes:

```text
mc/hepmc_smoke_test/work/validation_plots/pipeline_validation_summary.json
```

The setup is good when the command prints:

```text
Overall passed: True
```

## 10. Inspect Outputs Manually

Useful manual checks:

```bash
ls -lh work/events.hepmc work/analysis.root work/delphes.root
rootls -t work/analysis.root
rootls -t work/delphes.root
```

`analysis.root` should contain:

```text
h_nparticles
h_pt
h_eta
h_phi
h_charged_lepton_pt
```

`delphes.root` should contain:

```text
Delphes
```

If `rootls -t work/delphes.root | head` prints a Python `BrokenPipeError`, ignore
it. That comes from closing the pipe early with `head`; it is not a Delphes
failure.

## 11. Re-Running The Test

Delphes does not like overwriting an existing ROOT output file. The cleanest way
to rerun is to use a new work directory:

```bash
./run_mg5_to_delphes_smoke_test.sh work_002 100 100.0 "$DELPHES_CARD"
python3 ../../theory/predictions/validate.py work_002 --pipeline-smoke
```

## 12. Run Only Pythia/HepMC/ROOT/Delphes On An Existing LHE File

If you already have an LHE file:

```bash
cd mc/hepmc_smoke_test
./run_smoke_test.sh \
  path/to/unweighted_events.lhe.gz \
  100 \
  events.hepmc \
  analysis.root \
  delphes.root \
  "$DELPHES_CARD"
```

The helper script compiles and runs:

```text
run_pythia.cc
read_hepmc.cc
analyse_hepmc.cc
DelphesHepMC2
```

## 13. Common Failures

If `mg5_aMC` is not found:

```bash
echo "$MG5ROOT"
echo "$PATH"
which mg5_aMC
```

Either source `env/setup_nikhef_lcg.sh` again or install local MadGraph and set
`MG5ROOT` before sourcing the script.

If `pythia8-config`, `root-config`, or `DelphesHepMC2` is missing:

```bash
source env/setup_nikhef_lcg.sh
which pythia8-config
which root-config
which DelphesHepMC2
```

If `DELPHES_CARD` is unset or points to a missing file:

```bash
echo "$DELPHES_CARD"
ls "$DELPHES_CARD"
```

Either source `env/setup_nikhef_lcg.sh` again or pass a detector card explicitly
as the fourth argument to `run_mg5_to_delphes_smoke_test.sh`.

If C++ compilation cannot find HepMC:

```bash
echo "$LCG_VIEW"
ls "$LCG_VIEW/include/HepMC"
ls "$LCG_VIEW/lib" | grep HepMC
```

If Delphes fails with `TF1::GradientPar` or another ROOT symbol error, you are
probably using a mismatched ROOT/Delphes/compiler combination. Start from a clean
shell and use the default setup:

```bash
cd /data/alice/username/Axions
source env/setup_nikhef_lcg.sh
```

If ROOT reports a missing `GLIBCXX_*` symbol, an older compiler or library is
probably still first in your environment. Start a clean Stoomboot shell and
source only `env/setup_nikhef_lcg.sh` for this test.

If Git prints warnings involving old ALICE ROOT v5 or AliEn libraries, use a
clean shell. Do not load the ALICE ROOT v5 environment for this pipeline.

If Delphes says it cannot create the output file, run with a new work directory
such as `work_003`.

MadGraph can print Python-version deprecation warnings. Those warnings are not a
pipeline failure if the LHE file is generated and the validation command passes.

## 14. What Comes Next

After this smoke test passes, the software chain is usable. The next project
step is to replace the generic `e+ e- -> mu+ mu-` process with the ALP production
cards:

```text
e+ e- -> a gamma
a -> gamma gamma
```

At that point, choose the analysis-specific center-of-mass energy and detector
card explicitly. Then run the ALP-specific validation gates:

```text
Gate 1: production cross section
Gate 2: ALP width and lifetime convention
Gate 3: Belle II closure
Gate 4: FCC-ee sanity check
```
