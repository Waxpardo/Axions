# Photophilic ALP Search at e+e- Colliders

This repository is organized for the Belle II closure test and FCC-ee projection
for a photophilic ALP produced through associated production:

```text
e+ e- -> gamma a,  a -> gamma gamma
```

The operational pipeline is:

```text
param_card -> MadGraph/LHE -> Pythia/HepMC -> Delphes/ROOT -> Python limits
```

The first milestone is the Belle II closure test. Do not advance FCC-ee
production limits until the analytic cross section, width/lifetime convention,
and Belle II contour validation gates pass.

## Layout

```text
.
├── env/                         # Python requirements
├── literature/                  # Reference papers
├── models/
│   └── ALP_linear/              # UFO model goes here
├── theory/
│   ├── Cross.nb                 # Mathematica notebook
│   ├── notes/                   # LaTeX derivations and report theory notes
│   └── predictions/             # Analytic grids and validation helpers
├── mc/
│   ├── cards/
│   │   ├── belle2/              # Belle II MG5/Pythia cards
│   │   └── fccee/               # FCC-ee MG5/Pythia cards
│   ├── delphes_cards/           # Detector cards
│   ├── gen_signal.sh            # Signal generation entrypoint
│   ├── gen_background.sh        # Background generation entrypoint
│   └── make_param_card.py       # Per-point param-card writer
├── analysis/                    # Delphes readers, selections, limits, plots
├── condor/                      # Batch scan scripts
└── results/
    ├── belle2_closure/
    └── fccee/
```
### Pipeline setup
Download UFO model (SM_alp_UFO)

In MG5_aMC_vX_X_X $ wget https://cms-project-generators.web.cern.ch/cms-project-generators/SM_alp_UFO.tar.gz

untar in mg5 under /data/alice/user/Axions/models

tar xzvf SM_alp_UFO.tar.gz

load madgraph and then run the commands:

MG5_aMC>import model ./path/SM_alp_UFO/

MG5_aMC>generate e+ e- > all all

MG5_aMC>add process e+ e- > alp a

the generate e+ e- > all all command goes through all pairs of particles that could be generated and filters out the ones that are physically impossible

(optional) run the following display command to see which collisions madgraph generated:

MG5_aMC>display processes

this should be the output:

Process: e+ e- > g g WEIGHTED<=4 @1

Process: e+ e- > a a WEIGHTED<=4 @1

Process: e+ e- > a z WEIGHTED<=4 @1

Process: e+ e- > a h WEIGHTED<=4 @1

Process: e+ e- > ve ve~ WEIGHTED<=4 @1

Process: e+ e- > vm vm~ WEIGHTED<=4 @1

Process: e+ e- > vt vt~ WEIGHTED<=4 @1

Process: e+ e- > u u~ WEIGHTED<=4 @1

Process: e+ e- > c c~ WEIGHTED<=4 @1

Process: e+ e- > t t~ WEIGHTED<=4 @1

Process: e+ e- > d d~ WEIGHTED<=4 @1

Process: e+ e- > s s~ WEIGHTED<=4 @1

Process: e+ e- > b b~ WEIGHTED<=4 @1

Process: e+ e- > z z WEIGHTED<=4 @1

Process: e+ e- > z h WEIGHTED<=4 @1

Process: e+ e- > w+ w- WEIGHTED<=4 @1

Process: e+ e- > h h WEIGHTED<=4 @1

Process: e+ e- > e- e+ WEIGHTED<=4 @1

Process: e+ e- > mu- mu+ WEIGHTED<=4 @1

Process: e+ e- > ta- ta+ WEIGHTED<=4 @1

Process: e+ e- > alp a WEIGHTED<=8 @2

MG5_aMC>output file_name

then edit the parameter and run cards to adjust the variables:

MG5_aMC>!nano file_name/Cards/param_card.dat

parameter card adjust:

ALP mass # Malp >> loop runs here (for now ive put 3GeV)
ALP decay particles (alp decays into 2 photons): under DECAY 9999 # Walp paste:
BR NDA ID1 ID2
 1.000000e+00      2    22   22

ALP photon coupling constant: under “information for alp” >> change # fa and/or # KB >> loop runs here (for now dont change anything)

MG5_aMC>!nano file_name/Cards/run_card.dat

run card adjust:

beam energies (ebeam1 & ebeam2)
minimum pt for the photons (pta): set to 0.0
minimum pt for the charged leptons (ptl): set to 0.0
minimum pt for the jets (ptj): set to 0.0

MG5_aMC>launch

madgraph generates the first launch menu, at the bottom: “[0, exit, run, direct, any string]”

MG5_aMC>0

second launch menu (here you can use the set command to adjust parameter of the cards as well, or you can press 1 for adjusting/checking the param_card and 2 for the run_card)

MG5_aMC>0

the run is saved, check run number, change the path on panos’s run_pythia.cc script and run it

compile and run:

g++ run_pythia.cc $(pythia8-config --cflags --libs) -L$LCG_VIEW/lib -lHepMC -o run_pythia

./run_pythia

read hepmc files and compile:

g++ read_hepmc.cc -I$LCG_VIEW/include -L$LCG_VIEW/lib -lHepMC -o read_hepmc

./read_hepmc

analysis compile and run:

g++ analyse_hepmc.cc -I$LCG_VIEW/include $(root-config --cflags --libs) -L$LCG_VIEW/lib -lHepMC -o analyse_hepmc

./analyse_hepmc