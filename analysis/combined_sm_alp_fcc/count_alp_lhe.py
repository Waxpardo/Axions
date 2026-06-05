#!/usr/bin/env python3
"""
Count ALP-tagged events (PDG 9999) in a (combined) LHE file.

In the combined sample the ALP signal line `e+ e- > alp a, alp > a a` writes
the ALP as an intermediate resonance (PDG 9999) in its events; the SM and
photon-background lines do not. So counting events that contain a 9999 entry
counts the ALP signal fraction of the unweighted sample.

  honest variant  -> expect ~0  (sigma_ALP/sigma_SM ~ 5e-8)
  boosted variant -> expect ~170 per 1000 (non-physical coupling)

Pure standard library (gzip only) so it runs without the LCG env.

CLI:
    python count_alp_lhe.py <events.lhe[.gz]>
        prints a human summary plus machine-readable lines:
            ALP_EVENTS=<n>
            TOTAL_EVENTS=<m>

Importable:
    from count_alp_lhe import count_alp
    n_alp, n_total = count_alp("events.lhe.gz")
"""

import gzip
import sys

ALP_PDG = 9999


def _open(path):
    """Open a .lhe or .lhe.gz transparently in text mode."""
    if path.endswith(".gz"):
        return gzip.open(path, "rt")
    return open(path, "r")


def count_alp(path):
    """Return (n_alp_events, n_total_events, n_alp_decay_photons) for an LHE file.

    n_alp_decay_photons counts photons (PDG 22) whose mother is an ALP
    (PDG 9999) -- i.e. the products of alp -> a a (2 per ALP event).
    """
    n_alp = 0
    n_tot = 0
    n_decay_photons = 0
    in_event = False
    header_pending = False
    particles = []          # (pdg, mother1) per particle line, 1-indexed by position

    with _open(path) as f:
        for line in f:
            s = line.strip()
            if s.startswith("<event"):
                in_event = True
                header_pending = True   # the next line is the event header
                particles = []
                continue
            if s.startswith("</event>"):
                if in_event:
                    n_tot += 1
                    alp_pos = {i + 1 for i, (pdg, _) in enumerate(particles)
                               if abs(pdg) == ALP_PDG}
                    if alp_pos:
                        n_alp += 1
                        n_decay_photons += sum(
                            1 for pdg, mo1 in particles
                            if pdg == 22 and mo1 in alp_pos
                        )
                in_event = False
                continue
            if in_event:
                if header_pending:
                    header_pending = False   # skip the nup/idprup/... header line
                    continue
                parts = s.split()
                if len(parts) >= 3:
                    try:
                        pdg = int(float(parts[0]))
                        mo1 = int(float(parts[2]))   # mother1 column
                    except ValueError:
                        continue          # <rwgt>/<wgt> or other non-particle line
                    particles.append((pdg, mo1))
    return n_alp, n_tot, n_decay_photons


def main(argv):
    if len(argv) != 2:
        print("usage: python count_alp_lhe.py <events.lhe[.gz]>", file=sys.stderr)
        return 2
    path = argv[1]
    try:
        n_alp, n_tot, n_dec = count_alp(path)
    except FileNotFoundError:
        print(f"ERROR: LHE not found: {path}", file=sys.stderr)
        return 1

    frac = (n_alp / n_tot) if n_tot else 0.0
    print("Truth-level ALP accounting")
    print(f"  Generated events:            {n_tot}")
    print(f"  Events containing ALP:       {n_alp}")
    print(f"  ALP decay photons found:     {n_dec}")
    print(f"  Fraction of events with ALP: {frac:.4f}")
    print(f"  LHE file:                    {path}")
    # Machine-readable lines (parsed by gen_combined_sm_alp_fcc.sh)
    print(f"ALP_EVENTS={n_alp}")
    print(f"TOTAL_EVENTS={n_tot}")
    print(f"ALP_DECAY_PHOTONS={n_dec}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
