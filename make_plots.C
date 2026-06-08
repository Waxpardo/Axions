void make_plots() {
    // 1. Open the file
    TFile *f = TFile::Open("/data/alice/cwydeman/Axions/my_process_folder_run01/Events/run_01/analysis.root");
    if (!f || f->IsZombie()) {
        std::cout << "Could not open analysis.root!" << std::endl;
        return;
    }

    // 2. Extract the histograms (Matching the types used in analyse_hepmc.cc)
    // You created these as TH1F in your analyse_hepmc.cc
    TH1F *h_bhadron_pt = (TH1F*)f->Get("h_bhadron_pt");
    TH1F *h_nparticles  = (TH1F*)f->Get("h_nparticles");
    TH1F *h_invMass    = (TH1F*)f->Get("h_invMass");

    // 3. Set up a virtual canvas
    TCanvas *c1 = new TCanvas("c1", "Canvas", 800, 600);

    // 4. Draw and save
    if (h_bhadron_pt) {
        h_bhadron_pt->SetLineColor(kBlue);
        h_bhadron_pt->Draw("HIST");
        c1->SaveAs("plot_bhadron_pt.png");
    }

    if (h_nparticles) {
        h_nparticles->SetLineColor(kRed);
        h_nparticles->Draw("HIST");
        c1->SaveAs("plot_multiplicity.png");
    }

    if (h_invMass) {
        h_invMass->SetLineColor(kBlack);
        h_invMass->SetLineWidth(2);
        h_invMass->Draw("HIST"); // "HIST" prevents drawing error bars
        c1->SaveAs("plot_invariant_mass.png");
    }

    // 5. Clean up
    f->Close();
    delete c1;
}