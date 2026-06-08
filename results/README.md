# Results Directory

This directory contains the report-facing outputs that should be easy to inspect
without rerunning a full Condor campaign.

Large raw production directories are ignored by git. The CSV, JSON, PNG, and PDF
files here are the compact artifacts that describe the current deliverable.

## Belle II Closure

Directory:

```text
results/belle2_closure/
```

Important files:

| File | Meaning |
|---|---|
| `belle2_closure_summary.json` | Pass/fail metrics for the public-contour closure. |
| `belle2_closure.md` | Human-readable closure report. |
| `belle2_closure_contour.csv` | Reconstructed closure curve. |
| `belle2_closure_target.csv` | Published Belle II lower boundary loaded from AxionLimits. |
| `belle2_closure.png` / `.pdf` | Visual comparison to Belle II. |

Current status:

The closure currently passes with:

$$
\max\left|\log_{10}\left(\frac{g_{\mathrm{closure}}}{g_{\mathrm{published}}}\right)\right|
=7.59\times10^{-3}.
$$

## FCC-ee Projection

Directory:

```text
results/fccee/
```

Main files:

| File | Meaning |
|---|---|
| `fccee_projection.csv` | Final detector-corrected FCC-ee contour branches. |
| `fccee_projection_summary.json` | Config, counts, background inclusion, and correction-map summary. |
| `fccee_zpole_signature_classification.csv` | Classification of the full $(m_a,g_{a\gamma\gamma})$ plane. |
| `fccee_zpole_signature_classification.png` | Signature-region plot. |
| `money_plot_alp_full.png` / `.pdf` | Final full ALP landscape money plot, including DM/astro/cosmology and QCD axion reference regions. |
| `money_plot_alp_full_closeup.png` / `.pdf` | FCC-ee-relevant close-up of the full ALP money plot. |
| `money_plot_alp_full_combined.png` / `.pdf` | Presentation-style two-panel plot linking the full landscape to the FCC-ee close-up. |
| `money_plot.png` / `.pdf` | Convenience copy of the final money plot. |
| `axionlimits_alp_landscape_intro.png` / `.pdf` | Matching AxionLimits-only landscape for the paper introduction, without FCC-ee overlays. |
| `background_signal_examples.png` / `.pdf` | Paper figure showing binned SM backgrounds with excluded/non-excluded ALP signal templates. |
| `background_signal_examples_summary.csv` | Numerical values for the signal examples in the background-template figure. |

Input/intermediate files kept because they define the contour:

| File | Meaning |
|---|---|
| `fccee_background_bins.csv` | Binned SM background histograms used by the final limit. |
| `fccee_background_bins_summary.json` | Cross sections, event counts, and bin summary. |
| `fccee_background_yields.csv` | Single-window diagnostic yields. |
| `alp_full_scan_summary.csv` | Per-point detector-level signal scan summary. |
| `alp_full_analysis_efficiency_map.csv` | Branch-aware detector correction map used by the contour. |
| `alp_full_analysis_efficiency_summary.json` | Summary of correction-map statistics. |

## What Is Not Stored Here

Full raw production outputs are usually too large for the repository:

```text
results/alp_full_production/
results/alp_full_pipeline/
results/backgrounds/
*.root
*.hepmc
*.lhe.gz
```

Those are ignored by `.gitignore`. If a raw file is needed to reproduce a
specific table, its location is recorded in the corresponding summary JSON.

## Rebuild Order

If all raw ROOT files exist, rebuild in this order:

1. `analysis/fccee_background_yields.py`
2. `analysis/fccee_binned_background.py`
3. `analysis/collect_alp_full_scan.py`
4. `analysis/build_full_analysis_efficiency_map.py`
5. `analysis/fccee_projection.py`
6. `analysis/plot_background_signal_examples.py`
7. `analysis/make_axionlimits_style_plot.py`

The final plot should be rebuilt after the projection CSV changes.
