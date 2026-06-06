# ALP Production on Nikhef Condor

Stable production entrypoint:

```bash
condor_submit condor/submit_alp_scan.sub
```

The default submit file reads:

```text
condor/alp_mass_grid_fccee_z_50.txt
```

Do not add a header row to Condor point files; Stoomboot's
`queue ... from <file>` treats every non-empty row as a job.

That file queues 50 log-spaced ALP masses from `0.01` to `10 GeV` at
`sqrt(s) = 91.2 GeV`, with `10000` events per mass and a reference coupling
`g_ref = 1e-4 GeV^-1`.

Only one reference coupling is generated because the associated-production
matrix element has exactly:

```text
sigma(e+e- -> alp gamma) proportional to g_agg^2
```

Downstream scans should rescale the validated reference cross section to the
full coupling grid. Lifetime and survival probabilities are applied
analytically; the Condor production LHE keeps the ALP stable.

To regenerate or customize the point file:

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
source env/setup_nikhef_lcg.sh
condor/run_alp_point.sh 0 1.0 10.58 1e-4 100 validation_manual
```

Outputs are written below:

```text
results/alp_production/<campaign>/
logs/alp_production/<campaign>/
```

Each point writes a `point_summary.csv` and a validation JSON containing the
Gate 1 cross-section comparison.

## Final Detector-Level Signal Production

The production-only scan above is useful for cross-section validation and fast
analytic rescaling. It does not contain the detector-level `a -> gamma gamma`
mass reconstruction.

For final signal-production settings use either the example grid or the
projection-derived point list:

```bash
condor_submit condor/submit_alp_full_scan.sub
condor_submit condor/submit_alp_full_projection_scan.sub
```

The example full scan reads:

```text
condor/alp_full_points_fccee_z_example.txt
```

The projection-derived scan reads:

```text
condor/alp_full_points_fccee_z_projection.txt
```

Each full point runs MG5, Pythia with the ALP lifetime and decay, Delphes, and
`analysis/alp_pipeline_histograms.py --require-pass`. A point fails if the
channel-aware detector validation does not pass. Resolved channels validate the
ALP diphoton invariant mass; invisible channels validate the recoil photon
without requiring reconstructed ALP daughter photons.

After the full scan finishes, collect the per-point summaries with:

```bash
python3 analysis/collect_alp_full_scan.py \
  results/alp_full_production/fccee_z_full_projection_fullbg_channelaware \
  --out results/fccee/alp_full_scan_summary.csv \
  --summary-json results/fccee/alp_full_scan_summary.json
```

## SM Background Production

FCC-ee production contours must include backgrounds. The background submit file
is:

```bash
condor_submit condor/submit_background_scan.sub
```

with points in:

```text
condor/background_points_fccee_z.txt
```

The current required backgrounds are:

```text
resolved_3gamma       e+ e- -> gamma gamma gamma
invisible_gamma_nunu  e+ e- -> gamma nu nu~
```

After the Delphes ROOT files exist, build the window-yield diagnostic input
with:

```bash
python3 analysis/fccee_background_yields.py \
  --resolved-root <resolved_3gamma_delphes.root> \
  --resolved-banner <resolved_3gamma_banner.txt> \
  --invisible-root <invisible_gamma_nunu_delphes.root> \
  --invisible-banner <invisible_gamma_nunu_banner.txt> \
  --out results/fccee/fccee_background_yields.csv
```

Build the binned background input used by the final-style contours with:

```bash
python3 analysis/fccee_binned_background.py \
  --resolved-root <resolved_3gamma_delphes.root> \
  --resolved-banner <resolved_3gamma_banner.txt> \
  --invisible-root <invisible_gamma_nunu_delphes.root> \
  --invisible-banner <invisible_gamma_nunu_banner.txt> \
  --out results/fccee/fccee_background_bins.csv \
  --summary-json results/fccee/fccee_background_bins_summary.json
```

`analysis/fccee_projection.py` refuses to build production contours without a
background-yield CSV unless `--allow-zero-background` is explicitly passed for a
smoke-only plot. If `results/fccee/fccee_background_bins.csv` exists, the
projection uses the binned Asimov Delta chi2 method; otherwise it falls back to
the window-yield method.
