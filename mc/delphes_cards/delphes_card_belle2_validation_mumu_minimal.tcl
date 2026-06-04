################################################################################
# delphes_card_belle2_validation_mumu_minimal.tcl
#
# *** MINIMAL Belle-II-inspired SOFTWARE-CHAIN VALIDATION card for e+e- -> mu+mu- ***
# *** NOT an official Belle II card, NOT validated detector performance.         ***
#
# Truly minimal muon-pair smoke test: contains ONLY the modules needed to
# propagate stable particles, track them, reconstruct muons, and write a ROOT
# tree. Jet clustering (FastJet / Durham exclusive jets), b/c/tau-tagging,
# jet-energy-scale, jet-flavor, calorimeter/EFlow, isolation, MissingET and
# UniqueObjectFinder are NOT DEFINED here at all (not merely disabled) -- the
# mu+mu- channel has no hadronic final state and needs none of them.
#
# Belle II tunings carried over from delphes_card_belle2_validation.tcl:
#   Bz = 1.5 T; CDC track acceptance |eta| <= 1.32; KLM muon-ID energy > 0.6 GeV,
#   |eta| <= 1.13, eff 0.98. See mc/cards/validation_mumu/README.md.
#
# The broader Belle-II-validation cards are left untouched.
################################################################################

#######################################
# Order of execution of various modules
#######################################

set ExecutionPath {
  ParticlePropagator

  ChargedHadronTrackingEfficiency
  ElectronTrackingEfficiency
  MuonTrackingEfficiency

  ChargedHadronMomentumSmearing
  ElectronMomentumSmearing
  MuonMomentumSmearing

  TrackMerger

  MuonEfficiency

  TreeWriter
}

#################################
# Propagate particles in cylinder
#################################

module ParticlePropagator ParticlePropagator {
  set InputArray Delphes/stableParticles

  set OutputArray stableParticles
  set ChargedHadronOutputArray chargedHadrons
  set ElectronOutputArray electrons
  set MuonOutputArray muons

  # radius of the magnetic field coverage, in m
  set Radius 1.13   ;# BELLE2: 1.81 -> 1.13 (Belle II CDC outer radius)
  # half-length of the magnetic field coverage, in m
  set HalfLength 1.40   ;# BELLE2: 2.35 -> 1.40 (Belle II CDC/ECL z extent)

  # magnetic field
  set Bz 1.5   ;# BELLE2: 3.5 -> 1.5 T (Belle II solenoid)
}

####################################
# Charged hadron tracking efficiency
####################################

module Efficiency ChargedHadronTrackingEfficiency {
  set InputArray ParticlePropagator/chargedHadrons
  set OutputArray chargedHadrons

  # tracking efficiency formula for charged hadrons
  # BELLE2: |eta| 3.0 -> 1.32 (CDC tracking acceptance, polar 17-150 deg; symmetric core)
  set EfficiencyFormula {                                                    (pt <= 0.1)   * (0.00) +
                                           (abs(eta) <= 1.32)              * (pt > 0.1)    * (1.00) +
                                           (abs(eta) >  1.32)                              * (0.00)}
}

##############################
# Electron tracking efficiency
##############################

module Efficiency ElectronTrackingEfficiency {
  set InputArray ParticlePropagator/electrons
  set OutputArray electrons

  # tracking efficiency formula for electrons
  # BELLE2: |eta| 3.0 -> 1.32 (CDC tracking acceptance, polar 17-150 deg; symmetric core)
  set EfficiencyFormula {                                                    (pt <= 0.1)   * (0.00) +
                                           (abs(eta) <= 1.32)              * (pt > 0.1)    * (1.00) +
                                           (abs(eta) >  1.32)                              * (0.00)}
}

##########################
# Muon tracking efficiency
##########################

module Efficiency MuonTrackingEfficiency {
  set InputArray ParticlePropagator/muons
  set OutputArray muons

  # tracking efficiency formula for muons
  # BELLE2: |eta| 3.0 -> 1.32 (CDC tracking acceptance, polar 17-150 deg; symmetric core)
  set EfficiencyFormula {                                                    (pt <= 0.1)   * (0.00) +
                                           (abs(eta) <= 1.32)              * (pt > 0.1)    * (1.00) +
                                           (abs(eta) >  1.32)                              * (0.00)}
}

########################################
# Momentum resolution for charged tracks
########################################

module MomentumSmearing ChargedHadronMomentumSmearing {
  set InputArray ChargedHadronTrackingEfficiency/chargedHadrons
  set OutputArray chargedHadrons

  # resolution formula for charged hadrons (inherited from CircularEE; not Belle-II-tuned)
  set ResolutionFormula {    (abs(eta) <= 3.0)                   * sqrt(0.001^2 + pt^2*1.e-5^2) +
                             (abs(eta) > 1.0 && abs(eta) <= 3.0) * sqrt(0.01^2 + pt^2*1.e-4^2)}
}

###################################
# Momentum resolution for electrons
###################################

module MomentumSmearing ElectronMomentumSmearing {
  set InputArray ElectronTrackingEfficiency/electrons
  set OutputArray electrons

  # resolution formula (inherited from CircularEE; not Belle-II-tuned)
  set ResolutionFormula {    (abs(eta) <= 1.0)                   * sqrt(0.001^2 + pt^2*1.e-5^2) +
                             (abs(eta) > 1.0 && abs(eta) <= 3.0) * sqrt(0.01^2 + pt^2*1.e-4^2)}
}

###############################
# Momentum resolution for muons
###############################

module MomentumSmearing MuonMomentumSmearing {
  set InputArray MuonTrackingEfficiency/muons
  set OutputArray muons

  # resolution formula (inherited from CircularEE; not Belle-II-tuned)
  set ResolutionFormula {    (abs(eta) <= 1.0)                   * sqrt(0.001^2 + pt^2*1.e-5^2) +
                             (abs(eta) > 1.0 && abs(eta) <= 3.0) * sqrt(0.01^2 + pt^2*1.e-4^2)}
}

##############
# Track merger
##############

module Merger TrackMerger {
# add InputArray InputArray
  add InputArray ChargedHadronMomentumSmearing/chargedHadrons
  add InputArray ElectronMomentumSmearing/electrons
  add InputArray MuonMomentumSmearing/muons
  set OutputArray tracks
}

##################
# Muon efficiency
##################

module Efficiency MuonEfficiency {
  set InputArray MuonMomentumSmearing/muons
  set OutputArray muons

  # BELLE2: KLM muon-ID -- threshold energy>2.0->0.6 GeV, |eta|<=1.13 (~25-145 deg), eff 0.99->0.98
  set EfficiencyFormula {                                      (energy <= 0.6)  * (0.00) +
                                          (abs(eta) <= 1.13) * (energy > 0.6)   * (0.98) +
                                          (abs(eta) > 1.13)                      * (0.00)}
}

##################
# ROOT tree writer
##################

module TreeWriter TreeWriter {
# add Branch InputArray BranchName BranchClass
# (the event-level "Event" branch is written automatically)
  add Branch Delphes/allParticles Particle GenParticle
  add Branch TrackMerger/tracks   Track    Track
  add Branch MuonEfficiency/muons Muon     Muon
}
