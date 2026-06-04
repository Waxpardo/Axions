// delphes_validation_check.C
// ---------------------------------------------------------------------------
// Stage-3 verification for the e+ e- -> mu+ mu- toolchain validation.
// Opens a Delphes ROOT file, and reports how many events have reconstructed
// muons. For our mu+mu- sample we expect ~2 reconstructed muons per event
// (within the Belle-II-like acceptance of delphes_card_belle2_validation.tcl).
//
// Usage (from repo root, after sourcing env/setup_lcg105.sh):
//   root -l -b -q 'mc/delphes_validation_check.C("<path-to>.root")'
// ---------------------------------------------------------------------------
void delphes_validation_check(
    const char* fname = "PROC_validation_mumu/Events/run_01/delphes_mumu.root") {

  TFile f(fname);
  if (f.IsZombie()) { printf("ERROR: cannot open %s\n", fname); return; }

  TTree* t = (TTree*) f.Get("Delphes");
  if (!t) { printf("ERROR: no 'Delphes' tree found in %s\n", fname); return; }

  Long64_t n  = t->GetEntries();
  Long64_t n1 = t->GetEntries("Muon_size >= 1");
  Long64_t n2 = t->GetEntries("Muon_size >= 2");

  // Mean reconstructed-muon multiplicity.
  t->Draw("Muon_size", "", "goff");
  double mean = (t->GetSelectedRows() > 0)
                  ? TMath::Mean(t->GetSelectedRows(), t->GetV1()) : 0.0;

  printf("\n==================== Stage-3 validation summary ====================\n");
  printf("Delphes file        : %s\n", fname);
  printf("Events              : %lld\n", n);
  printf("Mean Muon_size      : %.3f   (expect ~2 for e+e- -> mu+ mu-)\n", mean);
  if (n > 0) {
    printf(">= 1 reco muon      : %lld  (%.1f%%)\n", n1, 100.0 * n1 / n);
    printf(">= 2 reco muons     : %lld  (%.1f%%)\n", n2, 100.0 * n2 / n);
  }
  printf("Functional pass if mean Muon_size >= 1.5 and most events have >=1 reco muon.\n");
  printf("(Geometric acceptance |eta|<=1.13 means ~79%% per muon; expect mean ~1.6, not 2.0)\n");
  printf("====================================================================\n");
}
