# Branch Audit: 2026-06-05

Stable integration branch for now: `Iñaki`.

The remote branch state was refreshed with `git fetch --all --prune --tags`.
No broad branch merge was performed because several branches contain generated
event files, MadGraph process directories, or vendored software trees that
should not enter the stable branch.

## Branch Summary

| Branch | State | Useful content | Action |
|---|---|---|---|
| `origin/Iñaki` | Stable branch. Generic `e+e- -> mu+mu-` smoke pipeline works through MG5, Pythia, HepMC, ROOT histograms, and Delphes. | Current setup and validation docs. Already contains `models/ALP_linear/SM_alp_UFO`. | Kept as base. |
| `origin/main` | Contains the same ALP UFO at `models/SM_alp_UFO`; also has a tracked raw `mc/events.hepmc`. | Confirms the project UFO. | Did not merge. UFO content is byte-for-byte identical to `Iñaki`'s nested copy. |
| `origin/Oliver` | Advanced FCC-ee validation/background scripts and Delphes cards. Some scripts hardcode FCC-ee/IDEA and older environment assumptions. | Good ALP process syntax: `generate e+ e- > alp a`; useful note that photon is `a` and ALP is `alp`. | Adapted concept into generic `mc/alp_signal/run_alp_mg5_production.sh`; no direct merge. |
| `origin/briac` | Belle II muon validation scripts, Delphes cards, and the same flat-path UFO. | Some validation ideas overlap with current smoke test. | No import; current generic smoke test supersedes it. |
| `origin/Serge` | Large pipeline prototype with vendored `Delphes-3.5.1`, `pythia8313`, binaries, and generated files. | Confirms setup direction, but too much generated/vendor content. | No import. |
| `origin/Camille` | Simple setup script and C++ HepMC readers. | Early version of tools now covered by `mc/hepmc_smoke_test`. | No import. |
| `origin/effy` | Analysis files plus full generated MG5 directories. | Provides a generated ALP param-card example. | Used as reference for the param-card structure; no generated directories imported. |

## UFO Findings

The UFO already present in `Iñaki` is:

```text
models/ALP_linear/SM_alp_UFO
```

Important identifiers:

```text
photon name: a
ALP name:    alp
ALP PDG:     9999
mass:        MASS 9999 / Malp
width:       DECAY 9999 / Walp
couplings:   ALP block fa, Kg, KB, KW, Cta, Cb, Ct
```

The photonic vertex is controlled by `KB`, `KW`, and `fa`, not by a direct
external `g_agg`. Gate 1 fixes the production-normalized scan coupling to:

```text
g_agg = alpha_em * (KB + KW) / (sqrt(2) * pi * fa)
```

This is now the convention used by `mc/make_param_card.py` and parsed by
`theory/predictions/validate.py`.

The direct UFO decay-width normalization from `decays.py` is larger by
`sqrt(2)` and is exposed separately as `g_agg_ufo_width_GeV_inv` for Gate 2.

When writing a card from `--g-agg`, `mc/make_param_card.py` defaults to the
`KB/KW` split that cancels the tree-level `gamma Z alp` coupling. That keeps the
default production point aligned with the core photophilic associated-production
formula instead of accidentally turning on the resonant `Z -> gamma alp`
stretch channel.

## Imported Into Stable Setup

- Corrected ALP process cards to use `alp`, not the old placeholder `ax`.
- Added `mc/make_param_card.py` for per-point `(m_a, g_agg)` to UFO-parameter
  conversion.
- Added `mc/alp_signal/run_alp_mg5_production.sh`, a generic production-only
  MadGraph runner with configurable `sqrt(s)`, `m_a`, and `g_agg`.
- Updated validation parsing to infer `g_agg` from `fa`, `KB`, `KW`, and
  `aEWM1`.

Generated event files, full MG5 process directories, Delphes source trees,
Pythia source trees, and local binaries were intentionally left out.
