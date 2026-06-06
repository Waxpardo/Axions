#include "Pythia8/Pythia.h"
#include "Pythia8Plugins/HepMC2.h"

#include <cstdlib>
#include <iostream>
#include <string>

using namespace Pythia8;

int main(int argc, char* argv[]) {
  if (argc < 4) {
    std::cerr << "Usage: run_pythia_hepmc LHE_GZ N_EVENTS OUT_HEPMC\n";
    return 1;
  }

  const std::string lhe_path = argv[1];
  const int n_events = std::atoi(argv[2]);
  const std::string out_path = argv[3];

  Pythia pythia;
  pythia.readString("Beams:frameType = 4");
  pythia.readString("Beams:LHEF = " + lhe_path);
  pythia.readString("PartonLevel:MPI = off");
  pythia.readString("PartonLevel:ISR = on");
  pythia.readString("PartonLevel:FSR = on");
  pythia.readString("HadronLevel:all = off");

  HepMC::Pythia8ToHepMC toHepMC;
  HepMC::IO_GenEvent file(out_path, std::ios::out);

  pythia.init();

  int accepted = 0;
  for (int i = 0; i < n_events; ++i) {
    if (!pythia.next()) continue;
    HepMC::GenEvent* hepmc_event = new HepMC::GenEvent();
    toHepMC.fill_next_event(pythia, hepmc_event);
    file.write_event(hepmc_event);
    delete hepmc_event;
    ++accepted;
  }

  pythia.stat();
  std::cout << "Accepted events: " << accepted << "\n";
  return accepted > 0 ? 0 : 2;
}
