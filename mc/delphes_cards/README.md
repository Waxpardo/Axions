Project-specific detector cards can live here:

- `delphes_card_Belle2.tcl`
- `delphes_card_IDEA.tcl`

For the Nikhef smoke test, do not vendor a full Delphes installation into this
repository. Source `env/setup_nikhef_lcg.sh` and use the CVMFS IDEA card exposed
as `$DELPHES_CARD_IDEA`.
