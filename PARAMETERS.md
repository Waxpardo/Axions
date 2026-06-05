# Pipeline parameters — where to change what

Ordered newest → oldest. Edit `set <name> <value>` lines in the MG5 `.dat`
card; for event counts also update the Pythia `.cmnd`. `ebeam1 = ebeam2 = √s/2`.

**Shared infrastructure**
- Environment: `env/setup_lcg105.sh` (source before any run)
- ALP model: `models/SM_alp_UFO` — defaults in `models/SM_alp_UFO/parameters.py`
  (`Malp`, `fa`, `KB`, `KW`, `Kg`, `Cta`, `Cb`, `Ct`); **override per-run in the card**, don't edit the model
- Delphes: built locally by `mc/delphes/build_delphes.sh` (ROOT-matched)
- Pythia events: `Main:numberOfEvents` must be matched and **`Main:numberOfSubruns = 1`** kept (0 ⇒ zero showered events)

---

## 1. Combined SM+ALP   *(newest)*
Cards dir: `mc/cards/combined_sm_alp_fcc/`

| Change | File | Key |
|---|---|---|
| √s / beams | `mg5_combined_sm_alp_fcc.dat` | `set ebeam1`, `set ebeam2` |
| # events | `mg5_…dat` + `pythia8_combined_sm_alp_fcc.cmnd` | `set nevents` / `Main:numberOfEvents` |
| Random seed | `mg5_…dat` | `set iseed` |
| Processes | `mg5_…dat` | `generate` / `add process` (`CK=0` on γ-bkg lines) |
| ALP mass | `mg5_…dat` | `set Malp` |
| ALP coupling | `mg5_…dat` | `set fa`, `set KB`, `set KW` (`Kg,Cta,Cb,Ct=0`) |
| Photon cuts | `mg5_…dat` | `set pta`, `set etaa`, `set draa` |
| Jet/lepton cuts | `mg5_…dat` | `set ptj ptb ptl etal drll drjl mmll` |
| Signal strength (boosted) | `mg5_combined_sm_alp_fcc_boosted.dat` | `set KB`, `set KW` (=2000, non-physical) |
| Detector / jet algo | `mc/delphes_cards/fcc_idea/card_IDEA_winter2023_sm_bkg.tcl` | `GenJetFinder`/`FastJetFinder`: `JetAlgorithm`, `ParameterR` |
| Lumi target | `mc/combined_sm_alp_fcc/gen_combined_sm_alp_fcc.sh` | `luminosity_target_ab` |
| ALP-window (analysis) | `analysis/combined_sm_alp_fcc/summarise_combined.py` | `M_ALP`, `BUMP_HALF_WIDTH` |

---

## 2. SM inclusive background
Cards dir: `mc/cards/background_sm_fcc/`

| Change | File | Key |
|---|---|---|
| √s / beams | `mg5_sm_fcc.dat` | `set ebeam1`, `set ebeam2` |
| # events | `mg5_sm_fcc.dat` + `pythia8_sm_fcc.cmnd` | `set nevents` / `Main:numberOfEvents` |
| Random seed | `mg5_sm_fcc.dat` | `set iseed` |
| Processes | `mg5_sm_fcc.dat` | `generate` / `add process` (8 SM channels) |
| Jet/lepton cuts | `mg5_sm_fcc.dat` | `set ptj ptb ptl etal drll drjl mmll` |
| Detector / jet algo | `mc/delphes_cards/fcc_idea/card_IDEA_winter2023_sm_bkg.tcl` | `GenJetFinder`/`FastJetFinder`: `JetAlgorithm`, `ParameterR` |

---

## 3. ALP validation (FCC-ee)
Card dir: `mc/cards/validation_alp_fcc/`  ·  process `e+ e- > alp a, alp > a a`

| Change | File | Key |
|---|---|---|
| √s / beams | `mg5_alp_fcc.dat` | `set ebeam1`, `set ebeam2` |
| # events | `mg5_alp_fcc.dat` + `pythia8_alp_fcc.cmnd` | `set nevents` / `Main:numberOfEvents` |
| ALP mass | `mg5_alp_fcc.dat` | `set Malp` |
| ALP coupling | `mg5_alp_fcc.dat` | `set fa`, `set KB`, `set KW`, `set Kg`, `set Cta`, `set Cb`, `set Ct` |
| Detector | `mc/delphes_cards/fcc_idea/card_IDEA_winter2023_mumu_minimal.tcl` | module blocks |
| ALP mass marker (plot) | `analysis/validation_alp_fcc/plot_alp_validation_fcc.py` | `M_ALP` |

---

## 4. μ⁺μ⁻ validation (FCC-ee, √s = 240 GeV)
Card dir: `mc/cards/validation_mumu_fcc/`  ·  process `e+ e- > mu+ mu-`

| Change | File | Key |
|---|---|---|
| √s / beams | `mg5_mumu_fcc.dat` | `set ebeam1`, `set ebeam2` |
| # events | `mg5_mumu_fcc.dat` + `pythia8_mumu_fcc.cmnd` | `set nevents` / `Main:numberOfEvents` |
| Detector | `mc/delphes_cards/fcc_idea/card_IDEA_winter2023_mumu_minimal.tcl` | module blocks |

---

## 5. μ⁺μ⁻ validation (Belle II, √s = 10.58 GeV)   *(oldest)*
Card dir: `mc/cards/validation_mumu/`  ·  process `e+ e- > mu+ mu-`, `ebeam = 5.29`

| Change | File | Key |
|---|---|---|
| √s / beams | `mg5_mumu.dat` | `set ebeam1`, `set ebeam2` |
| # events | `mg5_mumu.dat` + `pythia8_mumu.cmnd` | `set nevents` / `Main:numberOfEvents` |
| Detector | `mc/delphes_cards/delphes_card_belle2_validation_mumu_minimal.tcl` | module blocks |
