#include "HepMC/IO_GenEvent.h"
#include "HepMC/GenEvent.h"

#include <iostream>

int main() {

  HepMC::IO_GenEvent ascii_in("mc/events.hepmc", std::ios::in);

  HepMC::GenEvent* evt;

  int iev = 0;

  while ((evt = ascii_in.read_next_event())) {

    std::cout << "Event " << iev++
              << " particles = "
              << evt->particles_size()
              << std::endl;

    for (auto p = evt->particles_begin();
         p != evt->particles_end(); ++p) {

      if ((*p)->status() != 1) continue;

      std::cout
        << " PDG = " << (*p)->pdg_id()
        << " pT = " << (*p)->momentum().perp()
        << std::endl;
    }

    delete evt;
  }
}
