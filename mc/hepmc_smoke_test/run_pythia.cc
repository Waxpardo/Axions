#include "Pythia8/Pythia.h"
#include "Pythia8Plugins/HepMC2.h"

#include <cstdlib>
#include <iostream>
#include <string>

using namespace Pythia8;

int main(int argc, char* argv[]) {
  const std::string lhe_path =
      argc > 1 ? argv[1] : "ee_mumu_test/Events/run_01/unweighted_events.lhe.gz";
  const int n_events = argc > 2 ? std::atoi(argv[2]) : 10000;
  const std::string hepmc_out = argc > 3 ? argv[3] : "events.hepmc";

  Pythia pythia;

  pythia.readString("Beams:frameType = 4");
  pythia.readString("Beams:LHEF = " + lhe_path);
  pythia.readString("Print:quiet = on");
  pythia.readString("Next:numberShowInfo = 0");
  pythia.readString("Next:numberShowProcess = 0");
  pythia.readString("Next:numberShowEvent = 0");

  HepMC::Pythia8ToHepMC to_hepmc;
  HepMC::IO_GenEvent file(hepmc_out, std::ios::out);

  pythia.init();

  for (int i = 0; i < n_events; ++i) {
    if (!pythia.next()) continue;

    HepMC::GenEvent* hepmc_event = new HepMC::GenEvent();
    to_hepmc.fill_next_event(pythia, hepmc_event);
    file.write_event(hepmc_event);
    delete hepmc_event;
  }

  pythia.stat();
  std::cout << "Wrote " << hepmc_out << std::endl;
  return 0;
}
