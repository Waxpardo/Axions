# ALP Full-Pipeline Verification, 2026-06-05

This note records the current end-to-end status of the ALP signal pipeline on
the stable working branch.

## Scope

The verified signal point is:

- process: `e+ e- > alp a`, followed by `alp -> gamma gamma` in Pythia
- `sqrt_s = 10.58 GeV`
- `m_a = 1.0 GeV`
- `g_agg = 1e-5 GeV^-1`
- events: `500`
- Delphes card: `mc/delphes_cards/delphes_card_Belle2.tcl`

The run directory on Nikhef was:

```bash
/data/alice/ipardoza/Axions/results/alp_full_pipeline/belle2_hist_m1_g1em5_s10p58_n500
```

The same artifacts were copied back locally under:

```bash
results/alp_full_pipeline/belle2_hist_m1_g1em5_s10p58_n500
```

## Verified Checks

The full chain now runs as:

```text
MG5 param card -> LHE -> Pythia ALP decay/lifetime -> HepMC -> Delphes ROOT -> Python validation/histograms
```

The main validation results were:

| Check | Result |
|---|---:|
| MG5 cross section | passed |
| MG5/theory cross-section ratio | `1.0000999143182028` |
| Width convention used by pipeline | 64 pi theory convention |
| Pythia lifetime validation | passed |
| Mean lab decay length ratio | `1.0939` |
| Delphes ROOT existence/tree check | passed |
| Resolved Delphes diphoton invariant mass | passed |

The reconstructed ALP mass check uses events with at least three reconstructed
photons and chooses the photon pair closest to the generated ALP mass. This is
the correct resolved-topology check for `e+e- -> gamma alp, alp -> gamma gamma`;
using all events with only two reconstructed photons can incorrectly pair a
recoil photon with one ALP daughter.

The Delphes histogram summary gave:

```text
events = 500
events_ge_2_photons = 350
events_ge_3_photons = 46
mean_reco_photons = 1.792
resolved_best_mgg_mean_GeV = 1.0375553576842598
resolved_best_mgg_abs_error_GeV = 0.03755535768425977
resolved_best_pairs_in_mass_window_fraction = 0.41304347826086957
```

The ROOT histograms written by `analysis/alp_pipeline_histograms.py` are:

```text
h_n_photons
h_photon_energy
h_leading_photon_energy
h_mgg_all_pairs
h_mgg_best_pair
h_mgg_best_pair_ge3_photons
```

The histogram to use for the resolved ALP mass validation is
`h_mgg_best_pair_ge3_photons`. For the verified point it had 46 entries and a
peak near `1.014 GeV`, consistent with `m_a = 1 GeV` after Delphes acceptance
and reconstruction.

## FCC-ee IDEA Full-Signal Status

The FCC-ee IDEA path has also passed the same full chain:

```text
MG5 e+e- -> alp gamma
Pythia alp -> gamma gamma with lifetime
Delphes IDEA card
Python invariant-mass histograms
```

The validated FCC-ee smoke point used:

```text
sqrt_s_GeV = 91.2
m_a_GeV = 1.0
g_agg_GeV_inv = 1e-5
events = 200
```

The important checks passed:

```text
MG5/theory cross-section ratio ~= 0.999
width convention = 64 pi
Pythia lifetime = passed
Delphes ROOT = passed
resolved_best_mgg_mean_GeV ~= 1.03
```

This verifies that the FCC-ee signal pipeline is operational. The full
projection scan is reproduced with:

```bash
condor/submit_alp_full_projection_scan.sub
condor/alp_full_points_fccee_z_projection.txt
```

The channel-aware scan used by the current paper draft has also completed:

```text
campaign = fccee_z_full_projection_fullbg_channelaware
points = 284
Gate 1 passed = 284
channel-aware detector validation passed = 284
```

Those results feed the branch-aware full-analysis correction map in
`results/fccee/alp_full_analysis_efficiency_map.csv`.

## Delphes Verbosity

`mc/alp_signal/run_alp_full_pipeline.sh` now redirects Delphes stdout/stderr to:

```bash
${work_dir}/delphes.log
```

This keeps pipeline output readable while preserving the full Delphes log for
debugging.

## Local Versus Nikhef Status

The full generator chain is operational on Nikhef, where MG5, Pythia8, HepMC,
ROOT, and Delphes are provided by the configured LCG environment.

The local macOS checkout can validate Python-side outputs with the project
virtual environment, but it does not currently have the full generator stack:

```text
mg5_aMC: missing locally
pythia8-config: missing locally
DelphesHepMC2: missing locally
root-config: available locally
```

So local validation is currently for already-produced ROOT/JSON artifacts, while
full production is performed on Nikhef.

## Belle II Closure-Test Status

The Belle II-style full pipeline is verified at smoke-test level, and the
published Belle II contour closure is now implemented in
`analysis/belle2_closure.py`.

The closure uses the digitized Belle II curve from AxionLimits as the public
target. Since the Belle II private likelihood, background spectrum, and
reconstruction-efficiency map are not available in this repository, the script
infers the effective signal-yield threshold implied by the published curve and
then reruns the analytic production/lifetime model. The current output in
`results/belle2_closure/` passes with max
`|log10(g_closure/g_published)| = 7.59e-3`.

A future private-likelihood closure would still need Belle II-specific
background and reconstruction-efficiency inputs.
