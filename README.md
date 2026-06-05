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
│   ├── delphes/                 # Local Delphes build (fetched + built; build_delphes.sh)
│   ├── pythia/                  # Standalone Pythia8 shower driver (built locally)
│   ├── gen_signal.sh            # Signal generation entrypoint
│   ├── gen_background.sh        # Background generation entrypoint
│   └── make_param_card.py       # Per-point param-card writer
├── analysis/                    # Delphes readers, selections, limits, plots
├── condor/                      # Batch scan scripts
└── results/
    ├── belle2_closure/
    └── fccee/
```

