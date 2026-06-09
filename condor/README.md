# HTCondor Production

This directory contains the point lists and submit files for running the
pipeline on the Nikhef/Stoomboot cluster.

Before submitting jobs:

```bash
source env/setup_nikhef_lcg.sh
```

Also create the log directories used by the submit files. HTCondor does not
create these automatically:

```bash
mkdir -p logs/alp_production/fccee_z_50 \
         logs/alp_full_production/fccee_z_full_projection_fullbg_channelaware \
         logs/backgrounds/fccee_z_backgrounds
```

Do not add header rows to point files. Stoomboot's
`queue ... from <file>` treats every non-empty row as a job.

## Production-Only ALP Scan

Submit:

```bash
condor_submit condor/submit_alp_scan.sub
```

Default point file:

```text
condor/alp_mass_grid_fccee_z_50.txt
```

That file queues 50 log-spaced masses from $0.01$ to $10\,\mathrm{GeV}$ at
$\sqrt{s}=91.2\,\mathrm{GeV}$, with `10000` events per mass and reference
coupling $g_{\mathrm{ref}}=10^{-4}\,\mathrm{GeV}^{-1}$.

Only one reference coupling is needed for production-only cross-section scans
because

$$
\sigma(e^+e^-\to\gamma a)\propto g_{a\gamma\gamma}^2.
$$

Generate a custom point file:

```bash
python3 condor/make_alp_mass_grid.py \
  --out condor/alp_mass_grid_fccee_z_50.txt \
  --sqrt-s 91.2 \
  --m-min 1e-2 \
  --m-max 10 \
  --n-mass 50 \
  --g-ref 1e-4 \
  --nevents 10000 \
  --campaign fccee_z_50 \
  --job-category medium
```

Manual one-point test:

```bash
condor/run_alp_point.sh 0 1.0 91.2 1e-4 100 validation_manual
```

Outputs:

```text
results/alp_production/<campaign>/
logs/alp_production/<campaign>/
```

## Detector-Level ALP Signal Scan

Submit the detector-level signal campaign:

```bash
condor_submit condor/submit_alp_full_projection_scan.sub
```

Default point file:

```text
condor/alp_full_points_fccee_z_projection.txt
```

Each job runs:

```text
MadGraph -> Pythia ALP decay/lifetime -> Delphes -> detector validation
```

The same runner can also be used with the smaller example list:

```bash
condor_submit condor/submit_alp_full_scan.sub
```

which reads:

```text
condor/alp_full_points_fccee_z_example.txt
```

After the campaign finishes, collect the summaries:

```bash
python3 analysis/collect_alp_full_scan.py \
  results/alp_full_production/fccee_z_full_projection_fullbg_channelaware \
  --out results/fccee/alp_full_scan_summary.csv \
  --summary-json results/fccee/alp_full_scan_summary.json
```

The collected summary feeds:

```text
analysis/build_full_analysis_efficiency_map.py
```

which writes:

```text
results/fccee/alp_full_analysis_efficiency_map.csv
results/fccee/alp_full_analysis_efficiency_summary.json
```

## SM Background Scan

Submit:

```bash
condor_submit condor/submit_background_scan.sub
```

Default point file:

```text
condor/background_points_fccee_z.txt
```

It contains:

| Label | Process |
|---|---|
| `resolved_3gamma` | $e^+e^-\to\gamma\gamma\gamma$ |
| `invisible_gamma_nunu` | $e^+e^-\to\gamma\nu\bar\nu$ |

After the jobs finish, build the background inputs:

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

## Files

| File | Role |
|---|---|
| `make_alp_mass_grid.py` | Writes a production-only mass scan point file. |
| `make_alp_full_points_from_projection.py` | Builds detector-level points from the projected contours. |
| `run_alp_point.sh` | Runs one production-only ALP job. |
| `run_alp_full_point.sh` | Runs one full detector-level ALP job. |
| `run_background_point.sh` | Runs one SM background job. |
| `submit_alp_scan.sub` | Production-only ALP submit file. |
| `submit_alp_full_projection_scan.sub` | Detector-level ALP submit file. |
| `submit_background_scan.sub` | SM background submit file. |

## Common Checks

Check queued jobs:

```bash
condor_q
```

Check held jobs:

```bash
condor_q -hold
```

Inspect one job output:

```bash
tail -n 80 logs/alp_full_production/<campaign>/job_<cluster>_<jobid>.err
tail -n 80 logs/alp_full_production/<campaign>/job_<cluster>_<jobid>.out
```

Most failures come from one of three things:

1. The LCG environment was not sourced.
2. The log directories were not created before `condor_submit`.
3. `MG5ROOT`, `DELPHES_DIR`, or `DELPHES_CARD` points to a missing install.
