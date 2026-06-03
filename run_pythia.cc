#include "Pythia8/Pythia.h"
#include "Pythia8Plugins/HepMC2.h"
#include <iostream>

using namespace Pythia8;

int main(int argc, char* argv[]) {
    // Check if the user passed an LHE file path from the command line
    if (argc < 2) {
        std::cerr << "Error: Missing input LHE file path!" << std::endl;
        std::cerr << "Usage: ./run_pythia <path_to_lhe_file>" << std::endl;
        return 1;
    }

    std::string lheFilePath = argv[1];

    Pythia pythia;

    // 1. Configure input stream
    pythia.readString("Beams:frameType = 4");
    pythia.readString("Beams:LHEF = " + lheFilePath); // Dynamic path input!

    // 2. CRITICAL SHOWERING SWITCHES (Turns on Hadronization!)
    pythia.readString("PartonLevel:ISR = on");
    pythia.readString("PartonLevel:FSR = on");
    pythia.readString("HadronLevel:Hadronize = on");

    // HepMC writer interface wrapper
    HepMC::Pythia8ToHepMC toHepMC;
    HepMC::IO_GenEvent file("events.hepmc", std::ios::out);

    // Initialize Pythia
    if (!pythia.init()) {
        std::cerr << "Pythia initialization failed!" << std::endl;
        return 1;
    }

    // 3. Loop dynamically through events until the LHE file runs out
    int iEvent = 0;
    while (true) {
        if (!pythia.next()) {
            // If it fails because it hit the end of the file, break smoothly
            if (pythia.info.atEndOfFile()) break;
            continue; 
        }

        HepMC::GenEvent* hepmcEvent = new HepMC::GenEvent();
        toHepMC.fill_next_event(pythia, hepmcEvent);
        file.write_event(hepmcEvent);
        delete hepmcEvent;

        iEvent++;
        if (iEvent % 1000 == 0) {
            std::cout << "Successfully showered " << iEvent << " events..." << std::endl;
        }
    }

    pythia.stat();
    std::cout << "Showering completed successfully. Total processed events: " << iEvent << std::endl;
    return 0;
}
