# SM Background Production

This directory contains the Standard Model background pipeline used by the
FCC-ee contour.

The current final channels are:

| Label | Process | Analysis region |
|---|---|---|
| `resolved_3gamma` | `e+ e- -> gamma gamma gamma` | prompt/resolved `M_gg` background |
| `invisible_gamma_nunu` | `e+ e- -> gamma nu nu~` | one-photon invisible recoil background |

## Main Entrypoints

| File | Purpose |
|---|---|
| `run_sm_background_full_pipeline.sh` | MG5 -> Pythia -> Delphes background chain. |
| `run_pythia_hepmc.cc` | Pythia8 shower and HepMC writer for background LHE files. |

## Output Handoff

This directory produces Delphes ROOT files and banners. The analysis layer then
turns them into contour inputs:

```bash
python3 analysis/fccee_background_yields.py \
  --resolved-root <resolved_3gamma_delphes.root> \
  --resolved-banner <resolved_3gamma_banner.txt> \
  --invisible-root <invisible_gamma_nunu_delphes.root> \
  --invisible-banner <invisible_gamma_nunu_banner.txt> \
  --out results/fccee/fccee_background_yields.csv

python3 analysis/fccee_binned_background.py \
  --resolved-root <resolved_3gamma_delphes.root> \
  --resolved-banner <resolved_3gamma_banner.txt> \
  --invisible-root <invisible_gamma_nunu_delphes.root> \
  --invisible-banner <invisible_gamma_nunu_banner.txt> \
  --out results/fccee/fccee_background_bins.csv \
  --summary-json results/fccee/fccee_background_bins_summary.json
```

`fccee_background_bins.csv` is the final projection input. The yield file is
kept as a diagnostic.

## Condor Use

Use:

```bash
condor_submit condor/submit_background_scan.sub
```

The point list is:

```text
condor/background_points_fccee_z.txt
```

The final completed full-stat campaign used 10000 events per background
channel.
