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
| `build_full_analysis_efficiency_map.py` | Builds the final branch-aware analysis-bin correction map. |
| `collect_alp_full_scan.py` | Collects Condor per-point detector-level signal summaries. |
| `plot_prompt_resolved_invariant_mass.py` | Makes a CMS-style $m_{\gamma\gamma}$ signal-plus-background example plot. |
| `make_axionlimits_style_plot.py` | Builds the final AxionLimits-style money plot with FCC-ee overlays. |

## How The FCC-ee Projection Works

`fccee_projection.py` is the central limit-setting script. It takes:

1. `analysis/configs/fccee_zpole_inputs.json`
2. `results/fccee/fccee_background_yields.csv`
3. `results/fccee/fccee_background_bins.csv`
4. `results/fccee/alp_full_analysis_efficiency_map.csv`

For each ALP mass, the script computes analytic signal yields:

$$
N_S=
\mathcal{L}\,\sigma(m_a,g_{a\gamma\gamma})\,
P_{\mathrm{region}}(m_a,g_{a\gamma\gamma})\,
\epsilon_{\mathrm{parametric}}\,
C_{\mathrm{Delphes}}.
$$

where:

| Factor | Source |
|---|---|
| $\sigma$ | `theory/predictions/predict_grid.py` |
| $P_{\mathrm{region}}$ | decay-length survival or prompt-decay probability |
| $\epsilon_{\mathrm{parametric}}$ | angular acceptance and photon efficiency from config |
| $C_{\mathrm{Delphes}}$ | Delphes-derived full-analysis map |

The two final channels are:

| Channel | Observable | Condition |
|---|---|---|
| `invisible` | recoil photon energy | ALP survives past `L_max` |
| `resolved_prompt` | diphoton invariant mass | ALP decays before `L_min` and photons resolve |

The invisible channel is non-monotonic in $g_{a\gamma\gamma}$. At small coupling
the production cross section is too small. At large coupling the ALP decays
before leaving the detector, so the invisible probability vanishes. The script
therefore writes two branches:

```text
invisible_lower
invisible_upper
```

The prompt-resolved channel is monotonic and writes:

```text
resolved_prompt
```

The checked-in paper-draft contour currently has:

| Branch | Rows | Mass span | Coupling span |
|---|---:|---:|---:|
| `invisible_lower` | 91 | `0.01--0.92 GeV` | `5.5e-7--7.3e-7 GeV^-1` |
| `invisible_upper` | 91 | `0.01--0.92 GeV` | `1.3e-6--5.5e-2 GeV^-1` |
| `resolved_prompt` | 98 | `0.61--80 GeV` | `1.1e-5--2.9e-4 GeV^-1` |

The invisible lower and prompt-resolved branches are the robust headline
results. The invisible upper branch is a rapidly varying lifetime ceiling and
is retained as a directional boundary rather than a precision contour.

## Signature Classification Map

`fccee_projection.py` also builds the full signature map. For every point in
the `180 x 180` grid it computes `ell_a`, `Delta theta_min`, and the resolved
flag, then assigns one of four labels:

| Label | Grid points | Fraction | Meaning |
|---|---:|---:|---|
| `prompt_resolved` | 14,171 | 43.7% | prompt decay, two resolved ALP photons |
| `invisible` | 10,452 | 32.3% | ALP survives past `L_max` |
| `merged` | 5,989 | 18.5% | decays inside detector but photons merge |
| `displaced_resolved` | 1,788 | 5.5% | resolved diphoton displaced between `L_min` and `L_max` |

The resolved threshold follows from
`m_a ~= sqrt(s) * Delta theta_res / 4 = 0.597 GeV`; below that value, prompt
ALP decays are classified as merged rather than prompt-resolved.

## Binned Background Method

`fccee_binned_background.py` reads Delphes ROOT files and normalizes the
selected background entries to FCC-ee luminosity:

$$
N_{B,\mathrm{bin}}=
\sigma_B\,\mathcal{L}\,
\frac{N_{\mathrm{raw,bin}}}{N_{\mathrm{generated}}}.
$$

The resolved background is $e^+e^-\to\gamma\gamma\gamma$; the binned observable
is all reconstructed diphoton masses in events with at least three photons.

The invisible background is $e^+e^-\to\gamma\nu\bar\nu$; the binned observable is
the reconstructed recoil photon energy in events with exactly one photon.

The current full-stat background inputs are:

| Channel | Cross section | Generated events | Histogram entries | Expected entries at `150 ab^-1` |
|---|---:|---:|---:|---:|
| `resolved_prompt` | `7.3063 pb` | 10,000 | 23,592 diphoton pairs | `2.58e9` |
| `invisible` | `134.885 pb` | 10,000 | 2,684 recoil photons | `5.43e9` |

`fccee_projection.py` smears the signal into these bins with a Gaussian whose
width is set by the locked resolution assumptions. It then solves the Asimov
condition:

$$
\Delta\chi^2=2.71
$$

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

Current mean detector correction factors:

```text
invisible_lower: 0.998, range 0.969--1.003
invisible_upper: 7.8e6 mean, range 0.919--1.49e8
resolved_prompt: 1.02, range 0.900--2.62
```

## Locked Configurations

The small JSON files in `analysis/configs/` are the machine-readable source of
truth for detector and analysis assumptions:

| File | Purpose |
|---|---|
| `belle2_closure_inputs.json` | Belle II public-contour closure inputs. |
| `fccee_zpole_inputs.json` | FCC-ee Z-pole projection inputs. |
| `axionlimits_source.json` | External AxionLimits provenance and citation metadata. |

The Belle II closure uses $\sqrt{s}=10.58\,\mathrm{GeV}$,
$\mathcal{L}=445\,\mathrm{pb}^{-1}$, $L_{\min}=0.14\,\mathrm{m}$,
$L_{\max}=1.55\,\mathrm{m}$, $\theta_{\min}=12.4^\circ$,
$\theta_{\max}=155.1^\circ$, $E_\gamma^{\min}=0.25\,\mathrm{GeV}$, and
$\Delta\theta_{\mathrm{res}}=0.8^\circ$. The public target curve is
`limit_data/AxionPhoton/BelleII.txt` from AxionLimits.

The FCC-ee Z-pole projection uses $\sqrt{s}=91.2\,\mathrm{GeV}$,
$\mathcal{L}=150\,\mathrm{ab}^{-1}$, $L_{\min}=0.02\,\mathrm{m}$,
$L_{\max}=2.5\,\mathrm{m}$, $|\eta|_{\max}=3.0$,
$E_\gamma^{\min}=0.5\,\mathrm{GeV}$, photon efficiency $0.99$, and
$\Delta\theta_{\mathrm{res}}=1.5^\circ$.

The final projection requires binned backgrounds:

```text
background_yields_csv = results/fccee/fccee_background_yields.csv
background_bins_csv = results/fccee/fccee_background_bins.csv
require_background_for_contours = true
```

The resolved mass smearing is
$\max(0.05\,M_{\gamma\gamma},0.05\,\mathrm{GeV})$. The invisible recoil smearing
is $\max(0.05\,E_\gamma,0.5\,\mathrm{GeV})$.

## Prompt-Resolved Example Plot

`plot_prompt_resolved_invariant_mass.py` makes the report-style invariant-mass
figure for one chosen ALP point. It uses the same prompt-resolved
$e^+e^-\to\gamma\gamma\gamma$ background bins and Delphes-derived efficiency
corrections as the FCC-ee contour. The top panel shows pseudo-data, the
background model, and the signal-plus-background template. The bottom panel
subtracts the background and shows the ALP peak against the expected
$\pm1\sigma$ and $\pm2\sigma$ background fluctuations.

Default example:

```bash
.venv/bin/python analysis/plot_prompt_resolved_invariant_mass.py
```

Choose a different mass and coupling:

```bash
.venv/bin/python analysis/plot_prompt_resolved_invariant_mass.py \
  --mass 10.21 \
  --coupling 8e-5 \
  --out results/fccee/prompt_resolved_invariant_mass_example.png
```

Detector corrections are enabled by default:

```text
use_efficiency_corrections = true
efficiency_corrections_csv = results/fccee/alp_full_analysis_efficiency_map.csv
efficiency_correction_column = detector_correction_factor
```

Use `--no-efficiency-corrections` only for a flat-efficiency diagnostic
comparison.

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
6. Solves the same model back for $g_{a\gamma\gamma}$.

This verifies units, lifetime convention, production normalization, and
detector-region logic against Belle II. It is not a private-likelihood
reimplementation.

## Final Plot

Use `make_axionlimits_style_plot.py` for the paper intro landscape and the
project money plot:

```bash
.venv/bin/python analysis/make_axionlimits_style_plot.py \
  --axionlimits-dir external/AxionLimits \
  --projection results/fccee/fccee_projection.csv \
  --constraint-set full \
  --no-fcc-ee \
  --output-stem results/fccee/axionlimits_alp_landscape_intro \
  --combined-output-stem results/fccee/axionlimits_alp_landscape_intro

.venv/bin/python analysis/make_axionlimits_style_plot.py \
  --axionlimits-dir external/AxionLimits \
  --projection results/fccee/fccee_projection.csv \
  --constraint-set full \
  --output-stem results/fccee/money_plot_alp_full_closeup \
  --also-save-as results/fccee/money_plot \
  --m-min 1e7 --m-max 1e12 --g-min 1e-8 --g-max 1e-1
```

The `full` constraint set is the intended final choice. It includes the
dark-matter, astrophysical, cosmological, and QCD axion reference regions from
AxionLimits. The `generic` constraint set remains available as a diagnostic
view when those assumption-dependent regions need to be hidden.

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
