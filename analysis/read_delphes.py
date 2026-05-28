"""Helpers for reading Delphes ROOT output."""

from __future__ import annotations


def load_photons(path: str, tree: str = "Delphes"):
    """Return photon and MET arrays from a Delphes file.

    Import uproot/awkward lazily so the scaffold can be imported before the
    analysis environment is installed.
    """
    import awkward as ak
    import uproot

    root_file = uproot.open(path)
    delphes_tree = root_file[tree]
    photons = ak.zip(
        {
            "pt": delphes_tree["Photon.PT"].array(),
            "eta": delphes_tree["Photon.Eta"].array(),
            "phi": delphes_tree["Photon.Phi"].array(),
            "e": delphes_tree["Photon.E"].array(),
        }
    )
    met = delphes_tree["MissingET.MET"].array()
    return photons, met

