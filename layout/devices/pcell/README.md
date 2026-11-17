# IHP PCell definitions

The IHP SG13G2 PCell implementations are vendored upstream Python sources. They
live under `vendor/ihp/ihp/refs/ihp_pycell/` so the package remains
self-contained.

`layout/devices/generator.py` evaluates a named module and class from that tree
through `ihp_runtime.py` and writes ICE layout geometry. `layout/devices/index.json`
binds each parameterized device to its module and class; no geometry snapshot is
stored in the index.
