// analyze_hepmc.cc
#include "HepMC/IO_GenEvent.h"
#include "HepMC/GenEvent.h"
#include "TH1F.h"
#include "TFile.h"
#include <iostream>
#include <cmath>
#include <vector>

int main() {
  // 1. Point to your correct path location
  HepMC::IO_GenEvent ascii_in("mc/events.hepmc", std::ios::in);
  HepMC::GenEvent* evt = nullptr;

  TFile outfile("analysis.root", "RECREATE");

  // 2. Define targeted histograms for your ALP analysis
  TH1F h_nparticles("h_nparticles", "Final-state multiplicity;N particles;Events", 100, 0, 50);
  TH1F h_muon_pt("h_muon_pt", "Muon p_{T};p_{T} [GeV];Entries", 100, 0, 6);
  TH1F h_muon_eta("h_muon_eta", "Muon #eta;#eta;Entries", 100, -4, 4);
  
  // This is the histogram that will show your magnificent 3 GeV Peak!
  TH1F h_m_mumu("h_m_mumu", "Dimuon Invariant Mass;M_{#mu#mu} [GeV];Events / 20 MeV", 100, 2.0, 4.0);

  int iev = 0;
  while ((evt = ascii_in.read_next_event())) {
    ++iev;
    int nFinal = 0;

    // Vectors to store the four-momenta of muons in the current event
    std::vector<double> mu_E, mu_px, mu_py, mu_pz;

    for (auto part = evt->particles_begin(); part != evt->particles_end(); ++part) {
      int status = (*part)->status();
      int pdgid  = (*part)->pdg_id();

      if (status != 1) continue; // Keep only stable final-state tracks
      ++nFinal;

      int apdg = std::abs(pdgid);

      // Focus strictly on Muons (PDG code 13)
      if (apdg == 13) {
        auto mom = (*part)->momentum();
        double px = mom.px();
        double py = mom.py();
        double pz = mom.pz();
        double e  = mom.e();

        double pt  = std::sqrt(px*px + py*py);
        double p   = std::sqrt(px*px + py*py + pz*pz);
        double eta = (p != std::abs(pz)) ? 0.5 * std::log((p + pz)/(p - pz)) : 0.0;

        // Fill single-muon kinematics
        h_muon_pt.Fill(pt);
        h_muon_eta.Fill(eta);

        // Store vectors to compute dimuon pairs
        mu_E.push_back(e);
        mu_px.push_back(px);
        mu_py.push_back(py);
        mu_pz.push_back(pz);
      }
    }
    h_nparticles.Fill(nFinal);

    // ----------------------------------------
    // Calculate Dimuon Invariant Mass M_mumu
    // ----------------------------------------
    if (mu_E.size() >= 2) {
      // Combine the two highest momentum muons in the event
      double total_E  = mu_E[0]  + mu_E[1];
      double total_px = mu_px[0] + mu_px[1];
      double total_py = mu_py[0] + mu_py[1];
      double total_pz = mu_pz[0] + mu_pz[1];

      // M^2 = E^2 - p^2
      double m2 = (total_E*total_E) - (total_px*total_px + total_py*total_py + total_pz*total_pz);
      if (m2 > 0) {
        double m_mumu = std::sqrt(m2);
        h_m_mumu.Fill(m_mumu); // Fill the mass histogram
      }
    }

    delete evt;
    if (iev % 1000 == 0)
      std::cout << "Processed " << iev << " events" << std::endl;
  }

  outfile.Write();
  outfile.Close();
  std::cout << "\nDone. Wrote analysis.root\n";
  return 0;
}
