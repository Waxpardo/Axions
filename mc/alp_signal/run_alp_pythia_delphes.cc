#include "Pythia8/Pythia.h"
#include "Pythia8Plugins/HepMC2.h"

#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>

namespace {

constexpr int kAlpPdgId = 9999;
constexpr double kPi = 3.14159265358979323846;
constexpr double kHbarCGeVMm = 1.973269804e-13;

std::string format_double(double value) {
  std::ostringstream os;
  os << std::setprecision(12) << std::scientific << value;
  return os.str();
}

double theory_width_64pi(double mass_gev, double g_agg_gev_inv) {
  return g_agg_gev_inv * g_agg_gev_inv * mass_gev * mass_gev * mass_gev / (64.0 * kPi);
}

void write_json_string(std::ofstream& out, const std::string& key, const std::string& value, bool comma = true) {
  out << "  \"" << key << "\": \"" << value << "\"";
  if (comma) out << ",";
  out << "\n";
}

void write_json_number(std::ofstream& out, const std::string& key, double value, bool comma = true) {
  out << "  \"" << key << "\": " << format_double(value);
  if (comma) out << ",";
  out << "\n";
}

void write_json_int(std::ofstream& out, const std::string& key, long long value, bool comma = true) {
  out << "  \"" << key << "\": " << value;
  if (comma) out << ",";
  out << "\n";
}

}  // namespace

int main(int argc, char* argv[]) {
  if (argc < 7 || argc > 9) {
    std::cerr
        << "Usage:\n"
        << "  run_alp_pythia_delphes <lhe> <n_events> <hepmc_out> <summary_json> "
        << "<m_a_GeV> <g_agg_GeV_inv> [width_GeV] [seed]\n";
    return 1;
  }

  const std::string lhe_path = argv[1];
  const int n_events = std::atoi(argv[2]);
  const std::string hepmc_out = argv[3];
  const std::string summary_json = argv[4];
  const double m_a_gev = std::atof(argv[5]);
  const double g_agg = std::atof(argv[6]);
  const double width_theory_gev = theory_width_64pi(m_a_gev, g_agg);
  const double width_input_gev = argc > 7 ? std::atof(argv[7]) : width_theory_gev;
  const int seed = argc > 8 ? std::atoi(argv[8]) : 12345;

  if (n_events <= 0 || m_a_gev <= 0.0 || g_agg <= 0.0 || width_input_gev <= 0.0) {
    std::cerr << "Invalid input: require n_events, m_a, g_agg, and width > 0.\n";
    return 1;
  }

  const double ctau_input_mm = kHbarCGeVMm / width_input_gev;
  const double ctau_theory_mm = kHbarCGeVMm / width_theory_gev;

  Pythia8::Pythia pythia;
  pythia.readString("Beams:frameType = 4");
  pythia.readString("Beams:LHEF = " + lhe_path);
  pythia.readString("Print:quiet = on");
  pythia.readString("Next:numberShowInfo = 0");
  pythia.readString("Next:numberShowProcess = 0");
  pythia.readString("Next:numberShowEvent = 0");
  pythia.readString("Random:setSeed = on");
  pythia.readString("Random:seed = " + std::to_string(seed));
  pythia.readString("PartonLevel:MPI = off");
  pythia.readString("PartonLevel:ISR = on");
  pythia.readString("PartonLevel:FSR = on");
  pythia.readString("HadronLevel:Hadronize = off");
  pythia.readString("HadronLevel:Decay = on");
  pythia.readString("ParticleDecays:limitTau0 = off");

  pythia.readString(
      std::to_string(kAlpPdgId) + ":new = alp alp 1 0 0 " +
      format_double(m_a_gev) + " " + format_double(width_input_gev) + " 0.0 0.0 " +
      format_double(ctau_input_mm));
  pythia.readString(std::to_string(kAlpPdgId) + ":m0 = " + format_double(m_a_gev));
  pythia.readString(std::to_string(kAlpPdgId) + ":mWidth = " + format_double(width_input_gev));
  pythia.readString(std::to_string(kAlpPdgId) + ":tau0 = " + format_double(ctau_input_mm));
  pythia.readString(std::to_string(kAlpPdgId) + ":mayDecay = on");
  // Generic resonances need meMode >= 100; meMode 100 keeps the stored
  // branching ratio and width without requiring a hardcoded partial width.
  pythia.readString(std::to_string(kAlpPdgId) + ":oneChannel = 1 1.0 100 22 22");

  HepMC::Pythia8ToHepMC to_hepmc;
  HepMC::IO_GenEvent hepmc_file(hepmc_out, std::ios::out);

  pythia.init();

  long long events_written = 0;
  long long alp_decays = 0;
  long long final_state_photons = 0;
  double sum_lab_decay_mm = 0.0;
  double sum_expected_lab_decay_mm = 0.0;
  double sum_beta_gamma = 0.0;

  for (int i_event = 0; i_event < n_events; ++i_event) {
    if (!pythia.next()) {
      if (pythia.info.atEndOfFile()) break;
      continue;
    }

    for (int i = 0; i < pythia.event.size(); ++i) {
      const Pythia8::Particle& particle = pythia.event[i];
      if (particle.isFinal() && particle.id() == 22) {
        ++final_state_photons;
      }

      if (particle.idAbs() != kAlpPdgId || particle.daughter1() <= 0) {
        continue;
      }

      int photon_daughters = 0;
      int first_photon_daughter = -1;
      for (int daughter = particle.daughter1(); daughter <= particle.daughter2(); ++daughter) {
        if (daughter <= 0 || daughter >= pythia.event.size()) continue;
        if (pythia.event[daughter].id() == 22) {
          ++photon_daughters;
          if (first_photon_daughter < 0) {
            first_photon_daughter = daughter;
          }
        }
      }

      if (photon_daughters < 2 || first_photon_daughter < 0) {
        continue;
      }

      const Pythia8::Particle& daughter = pythia.event[first_photon_daughter];
      const double dx = daughter.xProd() - particle.xProd();
      const double dy = daughter.yProd() - particle.yProd();
      const double dz = daughter.zProd() - particle.zProd();
      const double lab_decay_mm = std::sqrt(dx * dx + dy * dy + dz * dz);
      const double beta_gamma = particle.pAbs() / particle.m();

      ++alp_decays;
      sum_lab_decay_mm += lab_decay_mm;
      sum_beta_gamma += beta_gamma;
      sum_expected_lab_decay_mm += beta_gamma * ctau_input_mm;
    }

    HepMC::GenEvent* hepmc_event = new HepMC::GenEvent();
    to_hepmc.fill_next_event(pythia, hepmc_event);
    hepmc_file.write_event(hepmc_event);
    delete hepmc_event;
    ++events_written;
  }

  pythia.stat();

  const double mean_lab_decay_mm = alp_decays > 0 ? sum_lab_decay_mm / alp_decays : 0.0;
  const double mean_expected_lab_decay_mm = alp_decays > 0 ? sum_expected_lab_decay_mm / alp_decays : 0.0;
  const double mean_beta_gamma = alp_decays > 0 ? sum_beta_gamma / alp_decays : 0.0;
  const double mean_photons_per_event = events_written > 0 ? static_cast<double>(final_state_photons) / events_written : 0.0;

  std::ofstream out(summary_json);
  out << "{\n";
  write_json_string(out, "mode", "alp_pythia_lifetime");
  write_json_string(out, "lhe_path", lhe_path);
  write_json_string(out, "hepmc_path", hepmc_out);
  write_json_int(out, "alp_pdg_id", kAlpPdgId);
  write_json_int(out, "events_requested", n_events);
  write_json_int(out, "events_written", events_written);
  write_json_int(out, "alp_decays", alp_decays);
  write_json_int(out, "final_state_photons", final_state_photons);
  write_json_number(out, "mean_final_state_photons_per_event", mean_photons_per_event);
  write_json_number(out, "m_a_GeV", m_a_gev);
  write_json_number(out, "g_agg_GeV_inv", g_agg);
  write_json_number(out, "width_input_GeV", width_input_gev);
  write_json_number(out, "width_theory_64pi_GeV", width_theory_gev);
  write_json_number(out, "ctau_input_mm", ctau_input_mm);
  write_json_number(out, "ctau_theory_64pi_mm", ctau_theory_mm);
  write_json_number(out, "mean_beta_gamma", mean_beta_gamma);
  write_json_number(out, "mean_lab_decay_length_mm", mean_lab_decay_mm);
  write_json_number(out, "mean_expected_lab_decay_length_mm", mean_expected_lab_decay_mm, false);
  out << "}\n";

  std::cout << "Wrote " << hepmc_out << "\n";
  std::cout << "Wrote " << summary_json << "\n";
  return 0;
}
