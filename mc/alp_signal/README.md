# ALP Signal Production

This directory contains the stable signal pipeline for:

$$
e^+e^-\to\gamma a,\qquad a\to\gamma\gamma .
$$

## Main Entrypoints

| File | Purpose |
|---|---|
| `run_alp_full_pipeline.sh` | Full MG5 -> Pythia -> Delphes -> validation chain for one point. |
| `run_alp_mg5_production.sh` | MadGraph production-only stage. |
| `run_alp_pythia_delphes.cc` | Pythia8 ALP decay/lifetime and HepMC writer. |
| `run_alp_gate2_width.sh` | Width-convention diagnostic using MG5 `compute_widths`. |
| `run_fccee_zpole_smoke.sh` | Small FCC-ee signal smoke helper. |

## Full Pipeline

Run:

```bash
mc/alp_signal/run_alp_full_pipeline.sh \
  <work_dir> <n_events> <sqrt_s_GeV> <m_a_GeV> <g_agg_GeV_inv> \
  <delphes_card> <validation_channel>
```

The script:

1. Writes a UFO param card with `mc/make_param_card.py`.
2. Generates $e^+e^-\to a\gamma$ in MadGraph.
3. Reads the project `64 pi` width from `DECAY 9999`.
4. Runs Pythia8 with ALP decay and physical lifetime.
5. Writes `events.hepmc` and `pythia_lifetime_summary.json`.
6. Runs Delphes.
7. Runs theory validation and channel-aware histogram validation.

## Validation Channels

Use:

```text
resolved_prompt
invisible
production_only
```

$\texttt{resolved\_prompt}$ validates reconstructed $M_{\gamma\gamma}$ near
$m_a$. $\texttt{invisible}$
validates the recoil photon energy and does not require reconstructed ALP decay
photons.

## Width Convention

The pipeline uses:

$$
\Gamma(a\to\gamma\gamma)=
\frac{g_{a\gamma\gamma}^2m_a^3}{64\pi}.
$$

The UFO-native width expression differs in normalization, so `run_alp_gate2_width.sh`
is kept as the diagnostic that documents the convention choice. The production
pipeline writes the project width explicitly into the param card and passes the
same value to Pythia.

## Condor Use

For many points, use the wrappers in `condor/`:

```text
condor/run_alp_full_point.sh
condor/submit_alp_full_projection_scan.sub
```

Do not submit raw loops directly from this folder unless you are debugging one
point interactively.
