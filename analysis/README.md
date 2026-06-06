# Analysis Code

This directory turns MC outputs and analytic ALP predictions into validation
tables, FCC-ee contours, signature classifications, and final plots.

The code is intentionally split into small scripts because the full project has
several distinct data products:

```text
Delphes ROOT backgrounds
  -> normalized background histograms
  -> binned FCC-ee projection
  -> money plot

Delphes ROOT signal points
  -> channel-aware validation histograms
  -> detector efficiency/correction maps
  -> corrected FCC-ee projection

AxionLimits checkout
  -> existing-constraint landscape
  -> FCC-ee overlay plot
```

## Important Files

| File | Purpose |
|---|---|
| `alp_pipeline_histograms.py` | Validates one detector-level ALP sample and writes ROOT histograms plus JSON. |
| `axionlimits.py` | Finds and loads AxionLimits data in project units. |
| `belle2_closure.py` | Reproduces the public Belle II contour at published-contour level. |
| `fccee_background_yields.py` | Builds single-window diagnostic background yields. |
| `fccee_binned_background.py` | Builds binned background histograms used by the final contour. |
| `fccee_projection.py` | Solves FCC-ee invisible and prompt-resolved projected contours. |
| `build_signal_efficiency_map.py` | Builds simple detector-selection efficiency maps from ALP signal scans. |
| `build_full_analysis_efficiency_map.py` | Builds the final branch-aware analysis-bin correction map. |
| `collect_alp_full_scan.py` | Collects Condor per-point detector-level signal summaries. |
| `make_axionlimits_style_plot.py` | Builds the final AxionLimits-style money plot with FCC-ee overlays. |
| `make_plots.py` | Older/simple plotting entrypoint retained for diagnostics. |

## How The FCC-ee Projection Works

`fccee_projection.py` is the central limit-setting script. It takes:

1. `analysis/configs/fccee_zpole_inputs.json`
2. `results/fccee/fccee_background_yields.csv`
3. `results/fccee/fccee_background_bins.csv`
4. `results/fccee/alp_full_analysis_efficiency_map.csv`

For each ALP mass, the script computes analytic signal yields:

```text
N_S = L * sigma(m_a, g_agg) * P_region(m_a, g_agg)
      * efficiency_parametric * detector_correction_factor
```

where:

| Factor | Source |
|---|---|
| `sigma` | `theory/predictions/predict_grid.py` |
| `P_region` | decay-length survival or prompt-decay probability |
| `efficiency_parametric` | angular acceptance and photon efficiency from config |
| `detector_correction_factor` | Delphes-derived full-analysis map |

The two final channels are:

| Channel | Observable | Condition |
|---|---|---|
| `invisible` | recoil photon energy | ALP survives past `L_max` |
| `resolved_prompt` | diphoton invariant mass | ALP decays before `L_min` and photons resolve |

The invisible channel is non-monotonic in `g_agg`. At small coupling the
production cross section is too small. At large coupling the ALP decays before
leaving the detector, so the invisible probability vanishes. The script
therefore writes two branches:

```text
invisible_lower
invisible_upper
```

The prompt-resolved channel is monotonic and writes:

```text
resolved_prompt
```

## Binned Background Method

`fccee_binned_background.py` reads Delphes ROOT files and normalizes the
selected background entries to FCC-ee luminosity:

```text
N_B,bin = sigma_pb * L_pb^-1 * raw_bin_entries / N_generated
```

The resolved background is `e+ e- -> gamma gamma gamma`; the binned observable
is all reconstructed diphoton masses in events with at least three photons.

The invisible background is `e+ e- -> gamma nu nu~`; the binned observable is
the reconstructed recoil photon energy in events with exactly one photon.

`fccee_projection.py` smears the signal into these bins with a Gaussian whose
width is set by the locked resolution assumptions. It then solves the Asimov
condition:

```text
Delta chi2 = 2.71
```

with a three-event floor to avoid claiming an unphysical sub-event limit.

## Detector Corrections

`build_full_analysis_efficiency_map.py` compares detector-level ALP signal
samples to the binned-analysis expectation. It writes one correction factor per
mass and branch:

```text
detector_correction_factor
```

This is used multiplicatively in `fccee_projection.py`. The current correction
map is branch-aware:

```text
invisible_lower
invisible_upper
resolved_prompt
```

The invisible upper branch has very large correction factors in a low-mass
tail. That branch is retained, but the report should describe it as
numerically fragile.

## Belle II Closure

`belle2_closure.py` is imported by the central validator:

```bash
python theory/predictions/validate.py \
  --belle2-closure \
  --axionlimits-dir external/AxionLimits
```

The closure:

1. Loads `limit_data/AxionPhoton/BelleII.txt` from AxionLimits.
2. Converts masses from eV to GeV.
3. Keeps the lower exclusion boundary.
4. Computes the expected prompt/resolved signal yield at the published curve.
5. Infers the effective Belle II signal-event threshold.
6. Solves the same model back for `g_agg`.

This verifies units, lifetime convention, production normalization, and
detector-region logic against Belle II. It is not a private-likelihood
reimplementation.

## Final Plot

Use `make_axionlimits_style_plot.py` for the project money plot:

```bash
python analysis/make_axionlimits_style_plot.py \
  --axionlimits-dir external/AxionLimits \
  --projection results/fccee/fccee_projection.csv \
  --constraint-set generic \
  --output-stem results/fccee/money_plot_generic_alp \
  --also-save-as results/fccee/money_plot
```

The `generic` constraint set is the intended final choice because it omits
regions that assume the ALP is the cosmological dark matter. The `full`
constraint set can be used as a reference landscape, but it answers a broader
question than this collider project.

## Development Checks

Compile all analysis scripts:

```bash
python -m py_compile analysis/*.py
```

Run Gate 3:

```bash
python theory/predictions/validate.py \
  --belle2-closure \
  --axionlimits-dir external/AxionLimits
```

Rebuild the projection:

```bash
python analysis/fccee_projection.py \
  --config analysis/configs/fccee_zpole_inputs.json \
  --out-dir results/fccee \
  --background-yields results/fccee/fccee_background_yields.csv \
  --background-bins results/fccee/fccee_background_bins.csv
```
