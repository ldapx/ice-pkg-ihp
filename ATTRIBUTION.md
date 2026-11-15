# Attribution

This package bundles data from the IHP SG13G2 open-source PDK.

- IHP-Open-PDK: https://github.com/IHP-GmbH/IHP-Open-PDK (Apache-2.0)
- Revision: `7d92ceafebfc51abb3285570ca0380c39e7e1826`
  (`v2.0.0-44-g7d92cea`)
- Standard-cell release: SG13G2 rev0.1.4 (12 Jan 2026)

The package's `LICENSE` is Apache-2.0. Directory-level details are recorded in:

- `layout/ATTRIBUTION.md` — device index, fixed-device geometry, and PCells.
- `implementation/ATTRIBUTION.md` — standard-cell, stack, RCX, and script data.
- `symbols/ATTRIBUTION.md` — schematic symbol sidecars.

The vendored PyCell runtime under `vendor/ihp` retains its upstream license file.
The ngspice model tree under `simulation/ngspice` and the Verilog-A sources under
`simulation/verilog-a` retain their upstream copyright and license notices.
