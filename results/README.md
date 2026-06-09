# Results

This directory stores compact outputs that are useful to inspect or reuse
without rerunning the full Monte Carlo production. Large raw files such as
ROOT, HepMC, and LHE outputs are ignored by git unless they are intentionally
kept as tiny examples.

## Belle II Closure

Directory:

```text
results/belle2_closure/
```

| File | Meaning |
|---|---|
| `belle2_closure_summary.json` | Pass/fail metrics for the public-contour closure. |
| `belle2_closure.md` | Short machine-written closure summary. |
| `belle2_closure_contour.csv` | Reconstructed closure curve. |
| `belle2_closure_target.csv` | Public Belle II lower boundary loaded from AxionLimits. |
| `belle2_closure.png` / `.pdf` | Visual comparison to the Belle II public curve. |

The checked-in closure passes with

$$
\max\left|\log_{10}
\left(\frac{g_{\mathrm{closure}}}{g_{\mathrm{published}}}\right)
\right|
=7.59\times10^{-3}.
$$

## FCC-ee Projection

Directory:

```text
results/fccee/
```

Main contour outputs:

| File | Meaning |
|---|---|
| `fccee_projection.csv` | Detector-corrected FCC-ee contour branches. |
| `fccee_projection_summary.json` | Config, branch counts, background inclusion, and correction-map summary. |
| `fccee_zpole_signature_classification.csv` | Full $(m_a,g_{a\gamma\gamma})$ topology classification. |
| `fccee_zpole_signature_classification.png` | Signature-region plot. |

Main plot outputs:

| File | Meaning |
|---|---|
| `money_plot.png` / `.pdf` | Convenience copy of the FCC-ee close-up money plot. |
| `money_plot_alp_full_closeup.png` / `.pdf` | FCC-ee-relevant close-up with projected contours. |
| `money_plot_alp_full.png` / `.pdf` | Wider ALP landscape with FCC-ee overlays. |
| `money_plot_alp_full_combined.png` / `.pdf` | Full landscape plus close-up view. |
| `axionlimits_alp_landscape_intro.png` / `.pdf` | AxionLimits landscape without FCC-ee overlays. |
| `background_signal_examples.png` / `.pdf` | Binned SM backgrounds with example ALP signal templates. |
| `prompt_resolved_invariant_mass_example.png` / `.pdf` | CMS-style prompt-resolved $m_{\gamma\gamma}$ signal-plus-background example. |

Main inputs and intermediate summaries:

| File | Meaning |
|---|---|
| `fccee_background_bins.csv` | Binned SM background histograms used by the contour. |
| `fccee_background_bins_summary.json` | Cross sections, event counts, and bin summaries. |
| `fccee_background_yields.csv` | Single-window diagnostic yields. |
| `fccee_background_yields_summary.json` | Summary of the yield input. |
| `alp_full_scan_summary.csv` | Collected detector-level ALP signal scan summary. |
| `alp_full_scan_summary.json` | Pass/fail summary for the detector-level signal scan. |
| `alp_full_analysis_efficiency_map.csv` | Branch-aware detector correction map. |
| `alp_full_analysis_efficiency_summary.json` | Correction-map statistics. |
| `background_signal_examples_summary.csv` | Numerical values used in the background/signal example figure. |
| `prompt_resolved_invariant_mass_example_summary.csv` | Numerical values used in the invariant-mass example plot. |

## Current FCC-ee Numbers

The checked-in projection uses
$\sqrt{s}=91.2\,\mathrm{GeV}$ and
$\mathcal{L}=150\,\mathrm{ab}^{-1}$.

| Branch | Mass span | Coupling span |
|---|---:|---:|
| Invisible lower | $0.01$--$0.92\,\mathrm{GeV}$ | $5.5$--$7.3\times10^{-7}\,\mathrm{GeV}^{-1}$ |
| Invisible upper | $0.01$--$0.92\,\mathrm{GeV}$ | $1.3\times10^{-6}$--$5.5\times10^{-2}\,\mathrm{GeV}^{-1}$ |
| Prompt-resolved | $0.61$--$80\,\mathrm{GeV}$ | $1.1\times10^{-5}$--$2.9\times10^{-4}\,\mathrm{GeV}^{-1}$ |

The invisible upper branch is a short-lifetime boundary and is less stable than
the lower invisible and prompt-resolved branches.

The binned backgrounds are:

| Channel | Process | Cross section | Histogram entries | Expected entries at $150\,\mathrm{ab}^{-1}$ |
|---|---|---:|---:|---:|
| `resolved_prompt` | $e^+e^-\to\gamma\gamma\gamma$ | `7.3063 pb` | 23,592 | `2.58e9` |
| `invisible` | $e^+e^-\to\gamma\nu\bar\nu$ | `134.885 pb` | 2,684 | `5.43e9` |

## Rebuild Order

If the raw ROOT files are available, rebuild the FCC-ee outputs in this order:

1. `analysis/fccee_background_yields.py`
2. `analysis/fccee_binned_background.py`
3. `analysis/collect_alp_full_scan.py`
4. `analysis/build_full_analysis_efficiency_map.py`
5. `analysis/fccee_projection.py`
6. `analysis/plot_background_signal_examples.py`
7. `analysis/plot_prompt_resolved_invariant_mass.py`
8. `analysis/make_axionlimits_style_plot.py`

The root `README.md` has the exact commands for each stage.
