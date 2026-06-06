# External Data

This directory is reserved for external data repositories that are not vendored
into this project.

For the axion-photon constraints landscape, clone AxionLimits here:

```bash
git clone https://github.com/cajohare/AxionLimits.git external/AxionLimits
```

The plotting code also accepts another location through:

```bash
export AXIONLIMITS_DIR=/path/to/AxionLimits
```

Do not commit the full AxionLimits clone unless the project explicitly decides
to vendor a fixed snapshot. The preferred workflow is to cite AxionLimits and
record the commit hash used for the final plot.
