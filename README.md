# IHP SG13G2 PDK package

This package definition installs the upstream IHP Open Source PDK:

<https://github.com/IHP-GmbH/IHP-Open-PDK>

The upstream repository is treated as an external package source. ICE does
not copy or redistribute its contents. The PDK is marked untrusted by
default, and its upstream installation prerequisites and preview status must
be reviewed before use.

Install it into a local package repository with:

```text
ice-pkg install <repository> ihp.sg13g2 0.1.0 \
  https://github.com/IHP-GmbH/IHP-Open-PDK.git main
```

Then resolve it from a project:

```text
ice-pkg resolve <repository> 0.1.0 ihp.sg13g2=0.1.0
```

## Schematic symbols

The package ships SVG schematic symbols under `symbols/` for NMOS, PMOS, NPN
HBT, and MIM capacitor devices. They use the same SchematicSymbolsSVG artwork
collection as the built-in ICE symbol library; see `symbols/ATTRIBUTION.md`.
