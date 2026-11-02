#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""IHP SG13G2 device generator backed by the ICE ``icepy`` PCell runtime.

ICE invokes this script with:

    device_generator.py --ihp-root ... --module nmos_code --class nmos \
                        --params-file params.json --output geometry.json

The upstream IHP PyCell implementation stays in the IHP checkout. This package
hook supplies the ICE side of the adapter and routes generated geometry through
``icepy``.
"""

from __future__ import annotations

import sys


def main() -> int:
    try:
        from icepy import pcells
    except ImportError as error:
        print(
            "The IHP device generator requires the ICE icepy Python module. "
            f"Set PYTHONPATH to the ICE python/ directory and build the icepy target. ({error})",
            file=sys.stderr,
        )
        return 2
    return pcells.main_cli()


if __name__ == "__main__":
    raise SystemExit(main())
