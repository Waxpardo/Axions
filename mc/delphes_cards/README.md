Project-specific detector cards can live here:

- `delphes_card_Belle2.tcl`
- `delphes_card_IDEA.tcl`

For the Nikhef smoke test, do not vendor a full Delphes installation into this
repository. Source `env/setup_nikhef_lcg.sh` and use the detector card exposed
as `$DELPHES_CARD`, or pass a card explicitly as the final argument to the smoke
test scripts.

The current Nikhef default points to the CVMFS Delphes validation card when it
is available. The pipeline itself does not require IDEA, Belle II, FCC-ee, or
any fixed center-of-mass energy; those choices belong to the production/analysis
configuration for a specific scan.
