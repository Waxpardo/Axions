#include "HepMC/IO_GenEvent.h"
#include "HepMC/GenEvent.h"
#include "TH1F.h"
#include "TFile.h"
#include <iostream>
#include <cmath>
#include <vector>
#include "TLorentzVector.h"

int main() {

  // --------------------------------------------
  // Input HepMC file
  // --------------------------------------------
  HepMC::IO_GenEvent ascii_in("events.hepmc", std::ios::in);
  HepMC::GenEvent* evt = nullptr;

  // --------------------------------------------
  // ROOT output
  // --------------------------------------------
  TFile outfile("analysis.root", "RECREATE");

  // --------------------------------------------
  // Histograms
  // --------------------------------------------
  TH1F h_nparticles("h_nparticles", "Final-state multiplicity;N particles;Events", 100, 0, 200);
  TH1F h_pt("h_pt", "Final-state particle p_{T};p_{T} [GeV];Entries", 100, 0, 100);
  TH1F h_eta("h_eta", "Final-state particle #eta;#eta;Entries", 100, -8, 8);
  TH1F h_phi("h_phi", "Final-state particle #phi;#phi;Entries", 64, -3.2, 3.2);
  TH1F h_invMass("h_invMass", "Invariant Mass of photon pairs;M_{\\gamma\\gamma} [GeV];Events", 100, 0, 10);
  TH1F h_bhadron_pt("h_bhadron_pt", "B-hadron p_{T};p_{T} [GeV];Entries", 100, 0, 100);
  h_invMass.SetDirectory(&outfile);

  // --------------------------------------------
  // Event loop
  // --------------------------------------------
  int iev = 0;
  while ((evt = ascii_in.read_next_event())) {
    ++iev;

    int nFinal = 0;
    std::vector<TLorentzVector> photons;

    // Loop through particles in the event
    for (auto part = evt->particles_begin(); part != evt->particles_end(); ++part) {
      
      int status = (*part)->status();
      if (status != 1) continue; // Only stable final-state particles
      
      ++nFinal;
      int pdgid = (*part)->pdg_id();
      auto mom = (*part)->momentum();

      // Calculate kinematics
      double px = mom.px();
      double py = mom.py();
      double pz = mom.pz();
      double pt = std::sqrt(px*px + py*py);
      double phi = std::atan2(py, px);
      double p = std::sqrt(px*px + py*py + pz*pz);
      double eta = (p != std::abs(pz)) ? 0.5 * std::log((p + pz)/(p - pz)) : 0.0;

      // Fill inclusive histograms
      h_pt.Fill(pt);
      h_eta.Fill(eta);
      h_phi.Fill(phi);

      // Store photons for invariant mass calculation
      if (std::abs(pdgid) == 22) {
          TLorentzVector photon;
          photon.SetPxPyPzE(px, py, pz, mom.e());
          photons.push_back(photon);
          std::cout << "DEBUG: Found a photon! Event: " << iev << " Photon Count: " << photons.size() << std::endl;
      }

      // Identify B hadrons
      int apdg = std::abs(pdgid);
      if ((apdg/1000 == 5) || (apdg/100 == 5)) {
        h_bhadron_pt.Fill(pt);
      }
    }

    // Calculate invariant mass of photon pairs for THIS event
    if (photons.size() >= 2) {
        for (size_t i = 0; i < photons.size(); ++i) {
            for (size_t j = i + 1; j < photons.size(); ++j) {
                h_invMass.Fill((photons[i] + photons[j]).M());
            }
        }
    }

    h_nparticles.Fill(nFinal);
    delete evt; // Safe to delete here

    if (iev % 1000 == 0) std::cout << "Processed " << iev << " events" << std::endl;
  }

  // --------------------------------------------
  // Write and Close
  // --------------------------------------------
  std::cout << "--- Analysis Summary ---" << std::endl;
  std::cout << "Entries in h_invMass: " << h_invMass.GetEntries() << std::endl;
  std::cout << "Entries in h_pt:      " << h_pt.GetEntries() << std::endl;
  
  outfile.Write();
  outfile.Close();

  std::cout << "\nDone. Wrote analysis.root" << std::endl;
  return 0;
}