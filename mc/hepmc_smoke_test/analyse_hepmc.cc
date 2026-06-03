#include "HepMC/GenEvent.h"
#include "HepMC/IO_GenEvent.h"

#include "TFile.h"
#include "TH1F.h"

#include <cmath>
#include <iostream>
#include <string>

int main(int argc, char* argv[]) {
  const std::string hepmc_in = argc > 1 ? argv[1] : "events.hepmc";
  const std::string root_out = argc > 2 ? argv[2] : "analysis.root";

  HepMC::IO_GenEvent ascii_in(hepmc_in, std::ios::in);
  HepMC::GenEvent* evt = nullptr;

  TFile outfile(root_out.c_str(), "RECREATE");

  TH1F h_nparticles(
      "h_nparticles",
      "Final-state multiplicity;N particles;Events",
      100, 0, 200);

  TH1F h_pt(
      "h_pt",
      "Final-state particle p_{T};p_{T} [GeV];Entries",
      100, 0, 100);

  TH1F h_eta(
      "h_eta",
      "Final-state particle #eta;#eta;Entries",
      100, -8, 8);

  TH1F h_phi(
      "h_phi",
      "Final-state particle #phi;#phi;Entries",
      64, -3.2, 3.2);

  TH1F h_bhadron_pt(
      "h_bhadron_pt",
      "B-hadron p_{T};p_{T} [GeV];Entries",
      100, 0, 100);

  int iev = 0;

  while ((evt = ascii_in.read_next_event())) {
    ++iev;

    int n_final = 0;

    for (auto part = evt->particles_begin();
         part != evt->particles_end(); ++part) {
      const int status = (*part)->status();
      const int pdgid = (*part)->pdg_id();

      if (status != 1) continue;

      ++n_final;

      const auto mom = (*part)->momentum();
      const double px = mom.px();
      const double py = mom.py();
      const double pz = mom.pz();

      const double pt = std::sqrt(px * px + py * py);
      const double phi = std::atan2(py, px);
      const double p = std::sqrt(px * px + py * py + pz * pz);

      double eta = 0.0;
      if (p != std::abs(pz)) {
        eta = 0.5 * std::log((p + pz) / (p - pz));
      }

      h_pt.Fill(pt);
      h_eta.Fill(eta);
      h_phi.Fill(phi);

      const int apdg = std::abs(pdgid);
      const bool is_b_hadron = (apdg / 1000 == 5) || (apdg / 100 == 5);

      if (is_b_hadron) {
        h_bhadron_pt.Fill(pt);
      }
    }

    h_nparticles.Fill(n_final);

    delete evt;

    if (iev % 1000 == 0) {
      std::cout << "Processed " << iev << " events" << std::endl;
    }
  }

  outfile.Write();
  outfile.Close();

  std::cout << "\nDone.\nWrote " << root_out << "\n";
  return 0;
}

