This directory contains the ALP UFO used by the project:

```text
models/ALP_linear/SM_alp_UFO
```

MadGraph particle names from this UFO:

```text
photon: a
ALP:    alp
PDG:    9999
```

The UFO does not expose the physical `g_agg` coupling as a direct external
parameter. Use `mc/make_param_card.py` to vary the physical scan point
`(m_a, g_agg)`. The writer converts `g_agg` into the UFO-native `fa`, `KB`, and
`KW` inputs with the Gate-1 production normalization:

```text
g_agg = alpha_em * (KB + KW) / (sqrt(2) * pi * fa)
```

When `--g-agg` is used, the writer defaults to the electroweak-basis split that
cancels the tree-level `gamma Z alp` coupling. A manual `KB/KW` split can still
be requested with `--kb-fraction`.

The direct UFO decay-width normalization is larger by `sqrt(2)` at the coupling
level. For the production-normalized mapping above, MG5/MadWidth therefore
computes a two-body `alp -> gamma gamma` width that is `2x` the project
`g_agg^2 m_a^3/(64 pi)` width. This is now the Gate 2 convention result:

```text
input/Pythia lifetime width:  g_agg^2 m_a^3 / (64 pi)
MG5 compute_widths width:     2 * g_agg^2 m_a^3 / (64 pi)
```

The full-pipeline runner deliberately feeds Pythia the input-card `64pi` width
so that decay lengths follow the convention used in the analytic predictions.
The validator reports the direct UFO width coupling separately as
`g_agg_ufo_width_GeV_inv` for diagnostics.
