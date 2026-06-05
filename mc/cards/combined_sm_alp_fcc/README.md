# Combined FCC-ee SM + ALP generation

A single MadGraph process directory holding the full FCC-ee event environment
**and** the ALP signal, at √s = 240 GeV (symmetric 120 GeV beams, IDEA
detector downstream). This is the experimental "combined sample" namespace —
isolated from the validated standalone `background_sm_fcc` and
`validation_alp_fcc` pipelines, which are untouched.

## Process list (12 lines, one `output` directory)

```
generate    e+ e- > j j               # j = g u c d s u~ c~ d~ s~  (b separate)
add process e+ e- > b b~
add process e+ e- > mu+ mu-
add process e+ e- > ta+ ta-
add process e+ e- > vl vl~             # vl = ve vm vt
add process e+ e- > w+ w-
add process e+ e- > z z
add process e+ e- > z h
add process e+ e- > a a    CK=0        # γγ   (pure SM)
add process e+ e- > a a a  CK=0        # γγγ  (pure SM, key irreducible 3γ bkg)
add process e+ e- > z a    CK=0        # Zγ   (pure SM)
add process e+ e- > alp a, alp > a a   # ALP signal (the only CK≠0 line)
```

### Why `a` and `alp`
In `SM_alp_UFO` the **photon is `a`** (PDG 22) and the **ALP is `alp`**
(PDG 9999, spin 0). The a–a–alp vertex (`V_5`, coupling `GC_17 ∝ (KB+KW)/fa`)
carries coupling order **`CK`**.

### Why `CK=0` on the photon backgrounds
`e+ e- > a a a` in this model has *two* kinds of diagram: pure-QED 3γ (order
QED³) **and** an ALP-resonant one (`γ + (γ*→alp→γγ)`, order QED³·CK²) that is
the same physics as the explicit signal line and peaks at m(γγ)=10 GeV.
Without a constraint it would be counted **twice** (once here, once in the
signal line). `CK=0` forbids the ALP vertex, keeping these three lines pure
Standard Model so the only ALP resonance comes from the explicit signal line.

### Photon cuts (required)
`γγ / γγγ / Zγ` have soft (E_γ→0) and collinear (γ∥beam) singularities, so the
run card sets `pta=1.0`, `etaa=3.0`, `draa=0.1`. These are loose enough to
retain the hard ALP photons (≈120 GeV recoil + two tens-of-GeV decay photons).
Note: being global run-card cuts, they also apply to the ALP signal photons —
a mild, physically reasonable change versus the uncut standalone ALP run
(`draa=0.1` only removes very-collinear ALP→γγ that would not resolve as two
photons anyway).

## Two variants

| variant | coupling | σ(ALP) | ALP events / 1000 | purpose |
|---|---|---|---|---|
| **honest** | KB=KW=1 (physical) | ~3.7×10⁻⁶ pb | **~0** (≈5×10⁻⁵) | physically correct; documents the dilution |
| **boosted** | KB=KW=2000 (**non-physical**) | ~15 pb | **~170** | populate the pipeline to validate reco of the 10 GeV peak |

**The dilution is real and expected:** σ(ALP)/σ(SM) ≈ 5×10⁻⁸, so an honest
unweighted sample of any practical size contains essentially zero ALP events.
That is a statistical-mixture certainty, not a tooling failure — the gen step
counts ALP-tagged LHE events (PDG 9999) and reports it. The boosted variant
raises the coupling (fa kept at 1000 GeV, staying in the m_a≪fa EFT regime)
purely so the Pythia→Delphes→analysis chain can be exercised on a real signal.
**The boosted sample is not a physics result.**

## Run sequence (on NIKHEF, after review)

```bash
V=honest        # or: boosted
bash mc/combined_sm_alp_fcc/gen_combined_sm_alp_fcc.sh      $V   # Stage 1: MG5 + metadata
bash mc/combined_sm_alp_fcc/shower_combined_sm_alp_fcc.sh   $V   # Stage 2: Pythia8 -> HepMC
bash mc/combined_sm_alp_fcc/delphes_combined_sm_alp_fcc.sh  $V   # Stage 3: Delphes -> ROOT
bash analysis/combined_sm_alp_fcc/run_summary.sh            $V   # Stage 4: validation plots
```

Outputs land in `PROC_combined_sm_alp_fcc[_boosted]/` (gitignored). Metadata
sidecar `metadata_combined_sm_alp_fcc.json` records cross section + uncertainty,
per-process pointer (`crossx.html`), ALP-event count, seed, mass/coupling point,
beam energy, software versions, detector card, **git commit**, and copies of the
exact input cards (`Events/run_01/cards_used/`).

## Known caveats / deferred

- **Excluded by design:** the two-photon / t-channel-electron family
  (`e+e-→e+e-`, `e+e-→e+e- f f̄`, …) — divergent, handled by dedicated
  generators; extra ME-level QED/QCD radiation (`f f̄ γ`, `q q̄ g`) — left to
  the parton shower to avoid soft/collinear divergences and double-counting;
  `t t̄` and other channels above √s=240 GeV — kinematically closed.
- `W⁺W⁻` and `ZZ` use the **on-shell** approximation (decayed by Pythia); full
  4-fermion / single-resonant / interference contributions are not included.
- The SM sector uses `SM_alp_UFO`, not the built-in `sm` of the standalone
  background run; the summary cross-checks that SM-only σ stays near ~78 pb.
- `nevents=1000` initially. Production scaling and Condor submission are
  **out of scope** here.
