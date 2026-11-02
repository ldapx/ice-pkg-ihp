# Layout device library attribution

`devices.json` contains layout geometry derived from the IHP SG13G2
open-source PDK:

- Project: IHP-Open-PDK
- Source: https://github.com/IHP-GmbH/IHP-Open-PDK
- Revision: `7d92ceafebfc51abb3285570ca0380c39e7e1826` (`v2.0.0-44-g7d92cea`)
- License: Apache-2.0

The geometry was extracted from the GDS files under `ihp/gds/` and flattened
into ICE layout cell polygons. Cells with a PyCell generator store the default
geometry and parameter metadata produced by the matching implementation under
`ihp/refs/ihp_pycell/`.

The IHP PyCell runtime needed for parametric regeneration is vendored under
`upstream/ihp/` (`cni/` and `ihp/refs/ihp_pycell/`) from the same upstream
project and license.
