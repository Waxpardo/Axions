# Analysis Configurations

This directory stores locked inputs for reproducible validation and projection
runs. These files are deliberately small JSON documents so that changes to
physics assumptions are visible in git diffs.

## Files

| File | Purpose |
|---|---|
| `belle2_closure_inputs.json` | Belle II public-contour closure inputs. |
| `fccee_zpole_inputs.json` | FCC-ee Z-pole projection inputs. |
| `axionlimits_source.json` | External AxionLimits provenance and citation metadata. |

## Belle II Closure Inputs

`belle2_closure_inputs.json` is used by:

```text
analysis/belle2_closure.py
theory/predictions/validate.py --belle2-closure
```

Key values:

The Belle II closure uses $\sqrt{s}=10.58\,\mathrm{GeV}$,
$\mathcal{L}=445\,\mathrm{pb}^{-1}$, $L_{\min}=0.14\,\mathrm{m}$,
$L_{\max}=1.55\,\mathrm{m}$, $\theta_{\min}=12.4^\circ$,
$\theta_{\max}=155.1^\circ$, $E_\gamma^{\min}=0.25\,\mathrm{GeV}$, and
$\Delta\theta_{\mathrm{res}}=0.8^\circ$. The public target curve is
`limit_data/AxionPhoton/BelleII.txt`.

Why these choices are used:

| Setting | Meaning |
|---|---|
| `sqrt_s_GeV` | Belle II center-of-mass energy. |
| `luminosity_pb_inv` | Belle II dataset used for the public limit curve. |
| `l_min_m` | Prompt-decay length scale for the closure logic. |
| `l_max_m` | Calorimeter scale, retained for invisible-probability diagnostics. |
| `theta_min_deg`, `theta_max_deg` | Belle II photon polar acceptance. |
| `delta_theta_res_deg` | Diphoton separation required for a resolved pair. |
| `published_curve` | Public target curve from AxionLimits. |

The closure tolerance is set by:

$$
\mathrm{closure\_tolerance}_{\log_{10}}=0.02 .
$$

That means the reconstructed contour must agree with the digitized published
curve to within about five percent in $g_{a\gamma\gamma}$.

## FCC-ee Z-Pole Inputs

`fccee_zpole_inputs.json` is used by:

```text
analysis/fccee_projection.py
analysis/build_full_analysis_efficiency_map.py
analysis/fccee_binned_background.py
```

Core machine and detector settings:

The FCC-ee Z-pole projection uses $\sqrt{s}=91.2\,\mathrm{GeV}$,
$\mathcal{L}=150\,\mathrm{ab}^{-1}$, $L_{\min}=0.02\,\mathrm{m}$,
$L_{\max}=2.5\,\mathrm{m}$, $|\eta|_{\max}=3.0$,
$E_\gamma^{\min}=0.5\,\mathrm{GeV}$, photon efficiency $0.99$, and
$\Delta\theta_{\mathrm{res}}=1.5^\circ$.

Why these choices are used:

| Setting | Why it matters |
|---|---|
| `sqrt_s_GeV` | Sets phase space, recoil energy, ALP boost, and opening angle. |
| `luminosity_ab_inv` | Converts cross sections to expected event counts. |
| `l_min_m` | Boundary between prompt and displaced decay. |
| `l_max_m` | Boundary between detector decay and invisible survival. |
| `eta_max` | Converts detector angular coverage into acceptance. |
| `photon_energy_min_GeV` | Vetoes kinematically visible photons below reconstruction threshold. |
| `photon_efficiency` | Parametric photon reconstruction efficiency. |
| `delta_theta_res_deg` | Determines whether the ALP diphoton pair is resolved or merged. |

Background inputs:

```text
background_yields_csv = results/fccee/fccee_background_yields.csv
background_bins_csv = results/fccee/fccee_background_bins.csv
require_background_for_contours = true
```

The final contour should use binned backgrounds. The single-window yield file is
kept as a diagnostic and fallback.

Signal smearing inputs:

The resolved mass smearing is
$\max(0.05\,M_{\gamma\gamma},0.05\,\mathrm{GeV})$. The invisible recoil smearing
is $\max(0.05\,E_\gamma,0.5\,\mathrm{GeV})$.

The relative term models detector resolution scaling with energy or mass. The
minimum term avoids unrealistically narrow bins at low mass.

Efficiency-correction inputs:

```text
use_efficiency_corrections = true
efficiency_corrections_csv = results/fccee/alp_full_analysis_efficiency_map.csv
efficiency_correction_column = detector_correction_factor
```

These values make the final contour detector-corrected. Use
`--no-efficiency-corrections` only for a flat-efficiency diagnostic comparison.

## AxionLimits Source

`axionlimits_source.json` records the external constraint source used for the
money plot. The AxionLimits clone itself is not committed. Keep this metadata
updated whenever the external clone changes.

Current pinned commit:

```text
7d375f4879b32406a239fe48d2615a4bfd9bc0bb
```

The money plot scripts use AxionLimits as context only. The FCC-ee curves are
read from this project's own `results/fccee/fccee_projection.csv`.
