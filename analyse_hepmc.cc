// analyze_hepmc.cc


#include "HepMC/IO_GenEvent.h"

#include "HepMC/GenEvent.h"


#include "TH1F.h"

#include "TFile.h"


#include <iostream>

#include <cmath>


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


  // --------------------------------------------

  // Event loop

  // --------------------------------------------


  int iev = 0;


  while ((evt = ascii_in.read_next_event())) {


    ++iev;


    int nFinal = 0;


    for (auto part = evt->particles_begin();

         part != evt->particles_end(); ++part) {


      int status = (*part)->status();

      int pdgid  = (*part)->pdg_id();


      // Keep only stable final-state particles

      if (status != 1) continue;


      ++nFinal;


      auto mom = (*part)->momentum();


      double px = mom.px();

      double py = mom.py();

      double pz = mom.pz();


      double pt  = std::sqrt(px*px + py*py);

      double phi = std::atan2(py, px);


      double p = std::sqrt(px*px + py*py + pz*pz);


      double eta = 0.0;


      if (p != std::abs(pz))

        eta = 0.5 * std::log((p + pz)/(p - pz));


      // Fill inclusive histograms

      h_pt.Fill(pt);

      h_eta.Fill(eta);

      h_phi.Fill(phi);


      // ----------------------------------------

      // Identify B hadrons

      // crude PDG selection

      // ----------------------------------------


      int apdg = std::abs(pdgid);


      bool isBHadron =

          (apdg/1000 == 5) ||

          (apdg/100  == 5);


      if (isBHadron)

        h_bhadron_pt.Fill(pt);

    }


    h_nparticles.Fill(nFinal);


    delete evt;


    if (iev % 1000 == 0)

      std::cout << "Processed "

                << iev

                << " events"

                << std::endl;

  }


  // --------------------------------------------

  // Write ROOT output

  // --------------------------------------------


  outfile.Write();

  outfile.Close();


  std::cout << "\nDone.\n"

            << "Wrote analysis.root\n";


  return 0;


}

