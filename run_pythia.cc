#include "Pythia8/Pythia.h"
#include "Pythia8Plugins/HepMC2.h"

using namespace Pythia8;

int main() {

  Pythia pythia;

// Force the initialization printout parameters to show Belle II values
  pythia.readString("Beams:idA = -11");
  pythia.readString("Beams:idB = 11");
  pythia.readString("Beams:eCM = 10.58");
  pythia.readString("Beams:frameType = 4");
  pythia.readString("Beams:LHEF = /data/alice/egrivas/Axions/belleII_alp/Events/run_01/unweighted_events.lhe.gz");

  // HepMC writer (correct Pythia interface wrapper)
  HepMC::Pythia8ToHepMC toHepMC;
  HepMC::IO_GenEvent file("mc/events.hepmc", std::ios::out);

  pythia.init();

  for (int i = 0; i < 10000; ++i) {
    if (!pythia.next()) continue;

    HepMC::GenEvent* hepmcEvent = new HepMC::GenEvent();
    toHepMC.fill_next_event(pythia, hepmcEvent);

    file.write_event(hepmcEvent);

    delete hepmcEvent;
  }

  pythia.stat();
  return 0;
}
