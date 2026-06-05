// mc/delphes_alp_photon_check.C
//
// Quick ROOT macro to verify that Delphes reconstructed photons are present
// in the ALP validation output. Called by mc/delphes_validation_alp_fcc.sh.
// Uses TLeaf direct reading -- does NOT require libDelphes.so.
//
// Expected result for e+ e- -> gamma alp, alp -> gamma gamma at sqrt(s)=240 GeV:
//   Most events should have 3 reconstructed photons. Some may have 2 if one
//   photon falls outside the IDEA acceptance (|eta|<3.0) or below threshold.
//   Events with 0-1 photons indicate a configuration problem.
//
// Usage:  root -l -b -q 'mc/delphes_alp_photon_check.C("path/to/delphes.root")'
void delphes_alp_photon_check(const char* path) {
    TFile* f = TFile::Open(path);
    if (!f || f->IsZombie()) {
        printf("ERROR: cannot open %s\n", path);
        return;
    }
    TTree* tree = (TTree*)f->Get("Delphes");
    if (!tree) {
        printf("ERROR: no 'Delphes' tree in %s\n", path);
        f->Close();
        return;
    }

    Long64_t nev = tree->GetEntries();
    TLeaf* lsize = tree->GetLeaf("Photon_size");
    if (!lsize) {
        printf("ERROR: Photon_size leaf not found -- is this a Delphes file?\n");
        f->Close();
        return;
    }

    int counts[8] = {0};   // events with exactly 0,1,...,6,7+ photons
    long long ntotal = 0;
    for (Long64_t i = 0; i < nev; i++) {
        tree->GetEntry(i);
        int n = (int)lsize->GetValue(0);
        ntotal += n;
        int bucket = (n < 7) ? n : 7;
        counts[bucket]++;
    }

    printf("\n");
    printf("======= Delphes ALP photon check (%s) =======\n", path);
    printf("Events in tree          : %lld\n", nev);
    printf("Total reco photons      : %lld\n", ntotal);
    printf("Mean photons / event    : %.2f\n", nev > 0 ? (double)ntotal / nev : 0.0);
    printf("\nPhoton multiplicity breakdown:\n");
    for (int k = 0; k < 7; k++)
        printf("  n_photon = %d : %d events\n", k, counts[k]);
    if (counts[7])
        printf("  n_photon >= 7 : %d events\n", counts[7]);
    int n2plus = 0, n3plus = 0;
    for (int k = 0; k < 8; k++) {
        if (k >= 2) n2plus += counts[k];
        if (k >= 3) n3plus += counts[k];
    }
    printf("\nEvents with >=2 photons : %d (%.1f%%)\n",
           n2plus, nev > 0 ? 100.0*n2plus/nev : 0.0);
    printf("Events with >=3 photons : %d (%.1f%%)\n",
           n3plus, nev > 0 ? 100.0*n3plus/nev : 0.0);
    printf("(expect most events with 3 photons: 1 prompt + 2 from alp->gamma gamma)\n");
    printf("=======================================================\n\n");

    f->Close();
}
