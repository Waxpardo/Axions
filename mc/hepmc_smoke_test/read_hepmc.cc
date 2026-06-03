#include "HepMC/GenEvent.h"
#include "HepMC/IO_GenEvent.h"

#include <cstdlib>
#include <iostream>
#include <string>

int main(int argc, char* argv[]) {
  const std::string hepmc_in = argc > 1 ? argv[1] : "events.hepmc";
  const int max_print_events = argc > 2 ? std::atoi(argv[2]) : 5;
  HepMC::IO_GenEvent ascii_in(hepmc_in, std::ios::in);

  HepMC::GenEvent* evt = nullptr;
  int iev = 0;

  while ((evt = ascii_in.read_next_event())) {
    if (iev < max_print_events) {
      std::cout << "Event " << iev
                << " particles = " << evt->particles_size()
                << std::endl;

      for (auto p = evt->particles_begin(); p != evt->particles_end(); ++p) {
        if ((*p)->status() != 1) continue;

        std::cout << " PDG = " << (*p)->pdg_id()
                  << " pT = " << (*p)->momentum().perp()
                  << std::endl;
      }
    }

    ++iev;
    delete evt;
  }

  std::cout << "Read " << iev << " HepMC events from " << hepmc_in << std::endl;
  return 0;
}
