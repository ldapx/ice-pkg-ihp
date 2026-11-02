# IHP SG13G2 PDK package

This package definition installs the upstream IHP Open Source PDK:

<https://github.com/IHP-GmbH/IHP-Open-PDK>

This package contains the simulation subset of the upstream IHP PDK
(`libs.tech/ngspice/models` and the Verilog-A sources under `pdk/verilog-a`).
Simulation depends only on this ICE package, not on Volare, CIEL, `PDK_ROOT`,
or a global `~/.spiceinit`.

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

The package ships TOML sidecar definitions under `symbols/` for NMOS, PMOS, NPN
HBT, and MIM capacitor devices. Their `artwork` fields reference ICE's built-in
SchematicSymbolsSVG artwork with `generic:<file>.svg`, so the package does not
duplicate SVG files. See `symbols/ATTRIBUTION.md` and ICE's
`symbols/ATTRIBUTION.md` for source attribution.

## Procedural layout dummy fill

ICE procedural layouts can call the PDK-provided dummy metal fill implementation:

```python
layout.add_dummy_fill(layers=["Metal1", "Metal2"], density=50, deviation=10)
```

The implementation lives in `layout/dummy_fill.py`. ICE loads it only when a
script requests dummy fill and exposes it through the generic
`layout.add_dummy_fill(...)` API. The IHP implementation uses the square-fill
rules from the open-source `gdsfill` project for Metal1-5 and TopMetal1-2. It
uses KLayout's `pya` geometry engine, so the Python interpreter running the
procedural script must be able to import `pya`.

If the layout has no die boundary, the fill area defaults to the bounding box of
the generated geometry. Use `area=(x0, y0, x1, y1)` to fill a larger region.
Very small layouts may have room for only a few minimum-size squares; Metal1
can legitimately receive no fill when its keep-out leaves less than 1 µm of free
space.


## Layout device library and PCells

The package ships the complete IHP layout device library as
`layout/devices.json`, containing the flattened reference geometry and the
parametric PCell definitions used by the ICE Devices panel. The IHP PyCell
sources are vendored under `upstream/ihp`, so parametric regeneration no longer
requires an external IHP checkout or `ICE_IHP_ROOT`.

Layout devices are regenerated through `layout/device_generator.py`. The script
uses `icepy.pcells`, the PCell runtime shipped with ICE's optional Python
bindings, evaluates the vendored IHP PyCell implementation through ICE's CNI
compatibility layer, and transfers the resulting polygons into an `icepy` layout
cell.

Build and expose the Python bindings with:

```text
xmake build icepy
export PYTHONPATH=<ice>/build/linux/x86_64/release:<ice>/python
```

The GUI supplies this path automatically. A device generator can then be
exercised directly:

```text
python layout/device_generator.py --pdk-root . \
  --module nmos_code --class nmos --params-file params.json --output geometry.json
```

## Simulation

The package declares `[pdk.simulation]` and `[pdk.simulation.osdi]` in
`package.toml`. Build the OSDI cache once with:

```text
ice-pkg pdk-build ihp.sg13g2
```

Verify it with `ice-cli pdk-info ihp-sg13g2 --probe`.
