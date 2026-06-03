# Nikhef MG5 -> Pythia -> HepMC Smoke Test

This guide records the supervisor-provided test pipeline for checking that
MadGraph, Pythia, HepMC, and ROOT work on Nikhef/Stoomboot before adapting the
same chain to the ALP signal.

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

The script uses the supervisor-recommended LCG view:

```text
/cvmfs/sft.cern.ch/lcg/views/LCG_106_ATLAS_13/x86_64-el9-gcc13-opt
```

It also sets:

```text
MG5ROOT
LCG_VIEW
PYTHIA8_ROOT
PYTHIA8DATA
```

If `MG5ROOT` is not set before sourcing the script, it defaults to:

```text
/data/alice/$USER/MadGraph5_aMC/MG5_aMC_v3_7_1
```

## 3. Run The MadGraph Tutorial Process

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

## 4. Compile And Run The Pythia/HepMC/ROOT Test

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
./run_smoke_test.sh ../../bbbar_test/Events/run_01/unweighted_events.lhe.gz 10000 events.hepmc analysis.root
```

If `bbbar_test` was generated inside `mc/hepmc_smoke_test`, run:

```bash
./run_smoke_test.sh bbbar_test/Events/run_01/unweighted_events.lhe.gz 10000 events.hepmc analysis.root
```

The helper script does three things:

```bash
g++ run_pythia.cc $(pythia8-config --cflags --libs) -L$LCG_VIEW/lib -lHepMC -o run_pythia
./run_pythia <lhe_path> <n_events> <hepmc_out>

g++ read_hepmc.cc -I$LCG_VIEW/include -L$LCG_VIEW/lib -lHepMC -o read_hepmc
./read_hepmc <hepmc_out>

g++ analyse_hepmc.cc -I$LCG_VIEW/include $(root-config --cflags --libs) -L$LCG_VIEW/lib -lHepMC -o analyse_hepmc
./analyse_hepmc <hepmc_out> <root_out>
```

## 5. Expected Outputs

The smoke test should create:

```text
events.hepmc
analysis.root
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

## 6. Common Issues

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

If Git starts warning about old libraries after loading ROOT or ALICE tools, use
a clean shell and source only `env/setup_nikhef_lcg.sh` for this smoke test.

