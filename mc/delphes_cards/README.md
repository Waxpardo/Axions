Project-specific detector cards can live here:

- `delphes_card_Belle2.tcl`
- `delphes_card_IDEA.tcl`

`delphes_card_Belle2.tcl` loads a Belle-II-inspired fast-simulation card adapted
from a CircularEE-style Delphes card. It is useful for software-chain and
analysis-development tests, but Belle II's official detector simulation is
basf2/Geant4 rather than Delphes.

`delphes_card_IDEA.tcl` loads the IDEA Winter 2023 FCC-ee card kept under
`fcc_idea/`.

For the Nikhef smoke test, do not vendor a full Delphes installation into this
repository. Source `env/setup_nikhef_lcg.sh` and use the detector card exposed
as `$DELPHES_CARD`, or pass a card explicitly as the final argument to the smoke
test scripts.

The current Nikhef default points to the CVMFS Delphes validation card when it
is available. The pipeline itself does not require IDEA, Belle II, FCC-ee, or
any fixed center-of-mass energy; those choices belong to the production/analysis
configuration for a specific scan.
