# Nikhef MG5 -> Pythia -> HepMC -> Delphes Smoke Test

This guide records the supervisor-provided test pipeline for checking that
MadGraph, Pythia, HepMC, ROOT, and Delphes work on Nikhef/Stoomboot before
adapting the same chain to the ALP signal.

The tutorial process is:

```text
p p -> b b~
```

This is only a software smoke test. It is not the ALP physics process.

## 1. Install MadGraph Under `/data/alice`

Log in to Nikhef/Stoomboot and go to your personal Alice directory:

```bash
ssh -X -Y username@login.nikhef.nl
ssh -X -Y username@stbc-i1
cd /data/alice/username
```

Download MadGraph from:

```text
https://launchpad.net/mg5amcnlo
```

Unpack it under `/data/alice/username`. One possible layout is:

```text
/data/alice/username/MadGraph5_aMC/MG5_aMC_v3_7_1
```

## 2. Set Up The Environment

From the repository root on Nikhef, point `MG5ROOT` to your own MadGraph
installation and source the setup script:

```bash
export MG5ROOT=/data/alice/username/MadGraph5_aMC/MG5_aMC_v3_7_1
source env/setup_nikhef_lcg.sh
```

The script uses an LCG view that is internally compatible with the CVMFS Delphes
package:

```text
/cvmfs/sft.cern.ch/lcg/views/LCG_108/x86_64-el9-gcc15-opt
```

Earlier `LCG_106_ATLAS_13` checks worked for MG5, Pythia, HepMC, and ROOT, but
the available Delphes packages on Nikhef failed against that ROOT with a missing
`TF1::GradientPar` symbol. The default is therefore `LCG_108` for the full
Delphes smoke test.

It also sets:

```text
MG5ROOT
LCG_VIEW
PYTHIA8_ROOT
PYTHIA8DATA
DELPHES_DIR
DELPHES_CARD_IDEA
```

If `MG5ROOT` is not set before sourcing the script, it defaults to:

```text
/data/alice/$USER/MadGraph5_aMC/MG5_aMC_v3_7_1
```

## 3. One-Command Full Smoke Test

From the repository root on Nikhef:

```bash
export MG5ROOT=/data/alice/username/MadGraph5_aMC/MG5_aMC_v3_7_1
source env/setup_nikhef_lcg.sh
cd mc/hepmc_smoke_test
./run_mg5_to_delphes_smoke_test.sh work 1000
```

This creates the MadGraph process, generates LHE events, converts them through
Pythia to HepMC, reads the HepMC file, writes a small ROOT histogram file, and
runs Delphes with the CVMFS IDEA card.

Expected outputs:

```text
mc/hepmc_smoke_test/work/events.hepmc
mc/hepmc_smoke_test/work/analysis.root
mc/hepmc_smoke_test/work/delphes.root
```

## 4. Manual MadGraph Tutorial Process

Start MadGraph:

```bash
mg5_aMC
```

At the `MG5_aMC>` prompt:

```text
generate p p > b b~
output bbbar_test
launch
```

Accept the default cards for the smoke test unless you are deliberately testing
something else.

The expected LHE output path is:

```text
bbbar_test/Events/run_01/unweighted_events.lhe.gz
```

## 5. Manual Pythia/HepMC/ROOT/Delphes Test

The C++ examples live in:

```text
mc/hepmc_smoke_test
```

From the repository root:

```bash
cd mc/hepmc_smoke_test
```

If `bbbar_test` was generated in the repository root, run:

```bash
./run_smoke_test.sh ../../bbbar_test/Events/run_01/unweighted_events.lhe.gz 1000 events.hepmc analysis.root delphes.root
```

If `bbbar_test` was generated inside `mc/hepmc_smoke_test`, run:

```bash
./run_smoke_test.sh bbbar_test/Events/run_01/unweighted_events.lhe.gz 1000 events.hepmc analysis.root delphes.root
```

The helper script does three things:

```bash
g++ run_pythia.cc $(pythia8-config --cflags --libs) -L$LCG_VIEW/lib -lHepMC -o run_pythia
./run_pythia <lhe_path> <n_events> <hepmc_out>

g++ read_hepmc.cc -I$LCG_VIEW/include -L$LCG_VIEW/lib -lHepMC -o read_hepmc
./read_hepmc <hepmc_out>

g++ analyse_hepmc.cc -I$LCG_VIEW/include $(root-config --cflags --libs) -L$LCG_VIEW/lib -lHepMC -o analyse_hepmc
./analyse_hepmc <hepmc_out> <root_out>

DelphesHepMC2 <delphes_card> <delphes_root> <hepmc_out>
```

## 6. Expected Outputs

The smoke test should create:

```text
events.hepmc
analysis.root
delphes.root
```

`read_hepmc` prints final-state PDG IDs and transverse momenta. `analyse_hepmc`
writes histograms into `analysis.root`, including:

```text
h_nparticles
h_pt
h_eta
h_phi
h_bhadron_pt
```

The Delphes output should contain a `Delphes` tree.

## 7. Common Issues

If `mg5_aMC` is not found, check:

```bash
echo $MG5ROOT
echo $PATH
ls $MG5ROOT/bin/mg5_aMC
```

If `pythia8-config` is not found, the LCG view was probably not sourced:

```bash
source env/setup_nikhef_lcg.sh
which pythia8-config
```

If the compile step cannot find HepMC headers or libraries, check:

```bash
echo $LCG_VIEW
ls $LCG_VIEW/include/HepMC
ls $LCG_VIEW/lib | grep HepMC
```

If `DelphesHepMC2` or the IDEA card is not found, check:

```bash
echo $DELPHES_DIR
echo $DELPHES_CARD_IDEA
which DelphesHepMC2
ls $DELPHES_CARD_IDEA
```

If Git starts warning about old libraries after loading ROOT or ALICE tools, use
a clean shell and source only `env/setup_nikhef_lcg.sh` for this smoke test.
