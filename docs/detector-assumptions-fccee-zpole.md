# FCC-ee Z-Pole Detector and Analysis Assumptions

This file locks the detector and analysis inputs used by the current FCC-ee
projection. The machine-independent physics formulas live in
`theory/predictions/predict_grid.py`; the numerical analysis inputs live in
`analysis/configs/fccee_zpole_inputs.json`.

## Baseline

| Quantity | Current value | Use in analysis |
|---|---:|---|
| Center-of-mass energy | `91.2 GeV` | Z-pole production kinematics |
| Integrated luminosity | `150 ab^-1` | Event-yield normalization |
| Detector card | `mc/delphes_cards/delphes_card_IDEA.tcl` | FCC-ee IDEA fast simulation |
| `L_min` | `0.02 m` | Prompt/displaced boundary |
| `L_max` | `2.5 m` | Invisible/inside-detector boundary |
| Photon acceptance | `abs(eta) < 3.0` | Recoil-photon geometric acceptance |
| Photon energy threshold | `0.5 GeV` | Signal yield veto for soft recoil photons |
| Photon efficiency | `0.99` | Baseline parametric efficiency before Delphes correction |
| Diphoton angular resolution | `1.5 deg` | Resolved/merged boundary |
| CL threshold | `Delta chi2 = 2.71` | One-sided 90 percent CL contour |
| Signal-event floor | `3` events | Conservative floor in each signal region |
| Background bin floor | `1` event | Stabilizes empty finite-MC bins |
| Invisible recoil histogram | `264` bins over `0--50 GeV` | Keeps smeared endpoint photons above `sqrt(s)/2` |
| Delphes efficiency correction | `detector_correction_factor` | Branch-aware correction from full-analysis signal map |

The paper-draft scan domain is:

```text
m_a = 0.01--80 GeV
g_agg = 1e-8--1e-1 GeV^-1
physics benchmark = photophilic ALP with tree-level C_gammaZ = 0
```

## Origin of the Numbers

The luminosity and Z-pole energy are the project baseline. The IDEA detector
card is included under `mc/delphes_cards/fcc_idea/` and sourced through the
project wrapper card. The photon `eta` range, photon threshold, and baseline
photon efficiency are taken from that card. The angular-resolution number is a
conservative calorimeter-cell scale from the IDEA phi segmentation, `pi/120`.

The `L_min` and `L_max` values are explicit analysis assumptions. They are not
parsed from Delphes. They should be updated in
`analysis/configs/fccee_zpole_inputs.json` if an official detector geometry
choice is adopted for the final report.

## Signal-Region Definitions

For each point in `(m_a, g_agg)`, the code computes the boosted decay length
`ell_a` and the light-ALP opening-angle estimate
`Delta theta_min ~= 4 m_a / sqrt(s)`.

The classification labels are:

| Label | Condition | Analysis status |
|---|---|---|
| `invisible` | `ell_a > L_max` | Used in limit contour |
| `prompt_resolved` | `ell_a < L_min` and `Delta theta_min >= Delta theta_res` | Used in limit contour |
| `displaced_resolved` | `L_min <= ell_a <= L_max` and resolved | Classified, not yet a limit region |
| `merged` | `ell_a <= L_max` and not resolved | Classified, not yet a limit region |

The current deliverable therefore has two projected FCC-ee contours:
`invisible` and `resolved_prompt`. The displaced and merged regions are shown
as physics interpretation regions, not claimed as final searches.

For the checked-in `180 x 180` grid, the signature map contains:

| Label | Grid points | Fraction |
|---|---:|---:|
| `prompt_resolved` | 14,171 | 43.7% |
| `invisible` | 10,452 | 32.3% |
| `merged` | 5,989 | 18.5% |
| `displaced_resolved` | 1,788 | 5.5% |

The resolved/merged boundary is at
`m_a ~= sqrt(s) * Delta theta_res / 4 = 0.597 GeV`.

## Binned Limit Settings

The production contour uses binned background inputs when
`results/fccee/fccee_background_bins.csv` exists.

Resolved prompt region:

```text
observable = M_gg
signal shape = Gaussian centered at m_a
resolution = max(0.05 * m_a, 0.05 GeV)
background = e+ e- -> gamma gamma gamma after Delphes
current input = sigma 7.3063 pb, 10000 generated events,
                23592 diphoton-pair entries, 2.58e9 expected entries
```

Invisible region:

```text
observable = recoil photon energy
E_gamma = (s - m_a^2) / (2 sqrt(s))
signal shape = Gaussian centered at E_gamma
resolution = max(0.05 * E_gamma, 0.5 GeV)
background = e+ e- -> gamma nu nu~ after Delphes
histogram = 264 bins over 0--50 GeV
current input = sigma 134.885 pb, 10000 generated events,
                2684 recoil entries, 5.43e9 expected entries
```

The binned Asimov requirement is:

```text
N_signal_required = max(3, sqrt(2.71 / sum_i f_i^2 / max(B_i, 1)))
```

where `f_i` is the normalized signal fraction in bin `i` and `B_i` is the
expected SM background in that bin at `150 ab^-1`.

The yield side of the contour uses:

```text
efficiency = parametric acceptance/photon efficiency * C_Delphes
```

where `C_Delphes` is interpolated from
`results/fccee/alp_full_analysis_efficiency_map.csv` using the
`detector_correction_factor` column. The correction is branch-aware for
`invisible_lower`, `invisible_upper`, and `resolved_prompt`.

The current contour endpoints implied by these settings are:

| Branch | Mass span | Coupling span | Interpretation |
|---|---:|---:|---|
| `invisible_lower` | `0.01--0.92 GeV` | `5.5e-7--7.3e-7 GeV^-1` | robust production/survival floor |
| `invisible_upper` | `0.01--0.92 GeV` | `1.3e-6--5.5e-2 GeV^-1` | short-lifetime ceiling; fragile in low-mass tail |
| `resolved_prompt` | `0.61--80 GeV` | `1.1e-5--2.9e-4 GeV^-1` | robust prompt/resolved contour |

## Limitations

The Delphes correction is interpolated from the completed contour-point scan. A
second full-signal scan at the corrected contour points would be needed for a
fully iterated detector-corrected result.

The current mean detector correction factors are approximately:

```text
invisible_lower: 0.998, range 0.969--1.003
invisible_upper: 7.8e6 mean, range 0.919--1.49e8
resolved_prompt: 1.02, range 0.900--2.62
```

The invisible upper branch is therefore useful as the expected lifetime ceiling,
but it should not be quoted as a precision contour.

The present angular-resolution boundary uses a simple minimum opening-angle
estimate. A final detector note should replace it with a cluster-level study if
merged photons become part of the claimed reach.
