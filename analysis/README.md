# Analysis

This directory contains the Python layer that turns analytic predictions and
Delphes outputs into backgrounds, efficiency maps, exclusion contours, and
plots.

The usual analysis flow is:

```text
Delphes background ROOT files
  -> binned SM background histograms
  -> FCC-ee projected contours

Delphes ALP signal ROOT files
  -> detector-level validation summaries
  -> efficiency/correction map
  -> corrected FCC-ee projected contours

AxionLimits checkout
  -> existing ALP-photon landscape
  -> FCC-ee projection overlays
```

## Scripts

| Script | What it does |
|---|---|
| `alp_pipeline_histograms.py` | Reads one Delphes ALP signal ROOT file, validates photon observables, and writes histogram summaries. |
| `axionlimits.py` | Loads selected AxionLimits curves and converts them into the project units. |
| `belle2_closure.py` | Reconstructs the public Belle II contour using the same production and lifetime model used elsewhere. |
| `fccee_background_yields.py` | Builds single-window background-yield diagnostics from Delphes ROOT files. |
| `fccee_binned_background.py` | Builds binned background histograms for the final Asimov limit. |
| `fccee_projection.py` | Solves the FCC-ee invisible and prompt-resolved contours and writes the signature map. |
| `build_full_analysis_efficiency_map.py` | Converts detector-level ALP signal scans into correction factors. |
| `collect_alp_full_scan.py` | Collects Condor per-point ALP summaries into one CSV/JSON pair. |
| `plot_background_signal_examples.py` | Plots background histograms with example ALP signals. |
| `plot_prompt_resolved_invariant_mass.py` | Makes a CMS-style $m_{\gamma\gamma}$ signal-plus-background example plot. |
| `make_axionlimits_style_plot.py` | Builds the AxionLimits landscape and FCC-ee money plots. |

## Configuration Files

The locked inputs live in `analysis/configs/`:

| File | Purpose |
|---|---|
| `belle2_closure_inputs.json` | Belle II public-contour closure inputs. |
| `fccee_zpole_inputs.json` | FCC-ee Z-pole detector, luminosity, smearing, and contour inputs. |
| `axionlimits_source.json` | AxionLimits source URL, pinned commit, and citation metadata. |

The FCC-ee config is the main input for the projection:

```text
sqrt_s_GeV = 91.2
luminosity_ab_inv = 150
L_min_m = 0.02
L_max_m = 2.5
eta_max = 3.0
photon_energy_min_GeV = 0.5
photon_efficiency = 0.99
delta_theta_res_deg = 1.5
```

## Background Histograms

The binned-background builder reads Delphes ROOT files and normalizes each bin
to the FCC-ee integrated luminosity:

$$
N_{B,i}=
\sigma_B\,\mathcal{L}\,
\frac{N_{\mathrm{raw},i}}{N_{\mathrm{generated}}}.
$$

The two background channels are:

| Channel | Process | Observable |
|---|---|---|
| `resolved_prompt` | $e^+e^-\to\gamma\gamma\gamma$ | all reconstructed $M_{\gamma\gamma}$ values in events with at least three photons |
| `invisible` | $e^+e^-\to\gamma\nu\bar\nu$ | recoil-photon energy in exactly-one-photon events |

Build the binned file from ROOT outputs:

```bash
.venv/bin/python analysis/fccee_binned_background.py \
  --resolved-root <resolved_3gamma_delphes.root> \
  --resolved-banner <resolved_3gamma_banner.txt> \
  --invisible-root <invisible_gamma_nunu_delphes.root> \
  --invisible-banner <invisible_gamma_nunu_banner.txt> \
  --out results/fccee/fccee_background_bins.csv \
  --summary-json results/fccee/fccee_background_bins_summary.json
```

The checked-in background inputs are:

| Channel | Cross section | Generated events | Histogram entries | Expected entries at $150\,\mathrm{ab}^{-1}$ |
|---|---:|---:|---:|---:|
| `resolved_prompt` | `7.3063 pb` | 10,000 | 23,592 diphoton pairs | `2.58e9` |
| `invisible` | `134.885 pb` | 10,000 | 2,684 recoil photons | `5.43e9` |

## Detector Corrections

The dense FCC-ee contour is mostly analytic, but it is corrected with
detector-level ALP signal points. The correction map contains one correction
factor per mass and branch:

```text
detector_correction_factor
```

Build it from a collected full-scan summary:

```bash
.venv/bin/python analysis/build_full_analysis_efficiency_map.py \
  --scan-summary results/fccee/alp_full_scan_summary.csv \
  --config analysis/configs/fccee_zpole_inputs.json \
  --background-bins results/fccee/fccee_background_bins.csv \
  --projection results/fccee/fccee_projection.csv \
  --out results/fccee/alp_full_analysis_efficiency_map.csv \
  --summary-json results/fccee/alp_full_analysis_efficiency_summary.json
```

The current correction map has three branches:

```text
invisible_lower
invisible_upper
resolved_prompt
```

The lower invisible and prompt-resolved corrections are stable. The upper
invisible branch is a short-lifetime boundary and is more sensitive to small
changes in lifetime and detector acceptance.

## FCC-ee Projection

Run the contour solver:

```bash
.venv/bin/python analysis/fccee_projection.py \
  --config analysis/configs/fccee_zpole_inputs.json \
  --out-dir results/fccee \
  --background-yields results/fccee/fccee_background_yields.csv \
  --background-bins results/fccee/fccee_background_bins.csv \
  --n-mass 180 \
  --n-g 180
```

For each ALP point it computes

$$
N_S =
\mathcal{L}\,
\sigma(m_a,g_{a\gamma\gamma})\,
P_{\mathrm{region}}(m_a,g_{a\gamma\gamma})\,
\epsilon_{\mathrm{parametric}}\,
C_{\mathrm{Delphes}}.
$$

The resolved channel uses binned $M_{\gamma\gamma}$ and the invisible channel
uses binned recoil-photon energy. With background-only Asimov data, the
resolved-channel test statistic is solved at

$$
\Delta\chi^2 = 2.71
$$

with a three-event floor.

Outputs:

```text
results/fccee/fccee_projection.csv
results/fccee/fccee_projection_summary.json
results/fccee/fccee_zpole_signature_classification.csv
results/fccee/fccee_zpole_signature_classification.png
```

## Belle II Closure

Run:

```bash
.venv/bin/python theory/predictions/validate.py \
  --belle2-closure \
  --axionlimits-dir external/AxionLimits
```

The closure:

1. Loads `limit_data/AxionPhoton/BelleII.txt` from AxionLimits.
2. Converts masses from eV to GeV.
3. Extracts the lower boundary.
4. Computes the signal yield using the same prompt-resolved model.
5. Solves back for the coupling and compares to the public curve.

This checks units, cross-section normalization, lifetime convention, and the
prompt-resolved detector logic.

## Plots

Background and signal examples:

```bash
.venv/bin/python analysis/plot_background_signal_examples.py \
  --config analysis/configs/fccee_zpole_inputs.json \
  --out-png results/fccee/background_signal_examples.png \
  --out-pdf results/fccee/background_signal_examples.pdf \
  --summary-csv results/fccee/background_signal_examples_summary.csv
```

Prompt-resolved invariant-mass example:

```bash
.venv/bin/python analysis/plot_prompt_resolved_invariant_mass.py \
  --mass 20.0 \
  --coupling 5e-4 \
  --x-min 10.0 \
  --x-max 30.0 \
  --out results/fccee/prompt_resolved_invariant_mass_example.png
```

AxionLimits landscape without FCC-ee overlays:

```bash
.venv/bin/python analysis/make_axionlimits_style_plot.py \
  --axionlimits-dir external/AxionLimits \
  --projection results/fccee/fccee_projection.csv \
  --constraint-set full \
  --no-fcc-ee \
  --output-stem results/fccee/axionlimits_alp_landscape_intro \
  --combined-output-stem results/fccee/axionlimits_alp_landscape_intro
```

FCC-ee money plot:

```bash
.venv/bin/python analysis/make_axionlimits_style_plot.py \
  --axionlimits-dir external/AxionLimits \
  --projection results/fccee/fccee_projection.csv \
  --constraint-set full \
  --output-stem results/fccee/money_plot_alp_full_closeup \
  --also-save-as results/fccee/money_plot \
  --m-min 1e7 --m-max 1e12 --g-min 1e-8 --g-max 1e-1
```

## Development Checks

Compile the Python scripts:

```bash
.venv/bin/python -m py_compile analysis/*.py
```

The scripts are intended to run from the repository root so relative paths
match the config files and checked-in result locations.
