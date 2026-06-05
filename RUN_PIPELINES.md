# How to run each pipeline

Ordered newest → oldest. Run from the repo root on NIKHEF. The `gen`/`shower`/
`delphes` drivers and the `run_*.sh` analysis wrappers source
`env/setup_lcg105.sh` themselves; bare `python` analysis scripts need it sourced
first. Outputs land in `PROC_*/` (gitignored); plots in `*/plots/` (gitignored).

---

## 1. Combined SM+ALP   *(newest)*
Single MG5 dir: 8 SM channels + γγ/γγγ/Zγ + ALP signal. Variant = `honest`
(physical, ~0 ALP events) or `boosted` (non-physical coupling, ~170 ALP events).

```bash
V=honest                                                            # or: boosted
bash mc/combined_sm_alp_fcc/gen_combined_sm_alp_fcc.sh      $V      # MG5 + metadata + truth-ALP count
bash mc/combined_sm_alp_fcc/shower_combined_sm_alp_fcc.sh   $V      # Pythia8 → HepMC
bash mc/combined_sm_alp_fcc/delphes_combined_sm_alp_fcc.sh  $V      # Delphes → ROOT
bash analysis/combined_sm_alp_fcc/run_summary.sh           $V      # plots + summary
```
Truth-ALP count alone: `python analysis/combined_sm_alp_fcc/count_alp_lhe.py PROC_combined_sm_alp_fcc/Events/run_01/unweighted_events.lhe.gz`
Delphes quick test: append a max-event count, e.g. `… delphes_combined_sm_alp_fcc.sh $V 50`.

---

## 2. SM inclusive background
8 SM channels at √s = 240 GeV.

```bash
bash mc/gen_background_sm_fcc.sh                  # MG5 + metadata
bash mc/shower_background_sm_fcc.sh               # Pythia8 → HepMC
bash mc/delphes_background_sm_fcc.sh              # Delphes → ROOT
bash analysis/background_sm_fcc/run_summary.sh    # object-inventory plots + summary
bash analysis/background_sm_fcc/run_diphoton.sh   # diphoton m(γγ) spectrum
```

---

## 3. ALP validation (FCC-ee)
`e+ e- > alp a, alp > a a`, m_a = 10 GeV.

```bash
bash mc/gen_validation_alp_fcc.sh                 # MG5 (SM_alp_UFO)
bash mc/shower_validation_alp_fcc.sh              # Pythia8 → HepMC
bash mc/delphes_validation_alp_fcc.sh             # Delphes → ROOT
source env/setup_lcg105.sh
python analysis/validation_alp_fcc/plot_alp_validation_fcc.py
```

---

## 4. μ⁺μ⁻ validation (FCC-ee, √s = 240 GeV)
`e+ e- > mu+ mu-`.

```bash
bash mc/gen_validation_mumu_fcc.sh
bash mc/shower_validation_mumu_fcc.sh
bash mc/delphes_validation_mumu_fcc.sh
source env/setup_lcg105.sh
python analysis/validation_mumu_fcc/plot_muon_pt_matplotlib_fcc.py
```

---

## 5. μ⁺μ⁻ validation (Belle II, √s = 10.58 GeV)   *(oldest)*
`e+ e- > mu+ mu-`, cross-section gate ≈ 0.8–0.9 nb.

```bash
bash mc/gen_validation_mumu.sh
bash mc/shower_validation_mumu.sh
bash mc/delphes_validation_mumu.sh
source env/setup_lcg105.sh
python analysis/validation_mumu/plot_muon_pt_matplotlib.py
```
