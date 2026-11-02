#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""IHP SG13G2 device generator backed by the ICE ``icepy`` PCell runtime.

The IHP PyCell sources are vendored under ``upstream/ihp`` so the package is
self-contained. ICE invokes this script with:

    device_generator.py --pdk-root <package> --module nmos_code --class nmos \
                        --params-file params.json --output geometry.json

The upstream PyCell implementation is evaluated by ``icepy.pcells`` and the
resulting polygons are transferred through the ICE layout API.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _vendored_ihp_root(argv: list[str]) -> Path | None:
    for index, argument in enumerate(argv):
        if argument == "--pdk-root" and index + 1 < len(argv):
            package_root = Path(argv[index + 1]).resolve()
            candidate = package_root / "upstream" / "ihp"
            if (candidate / "cni").is_dir() and (
                candidate / "ihp" / "refs" / "ihp_pycell"
            ).is_dir():
                return candidate
        elif argument.startswith("--pdk-root="):
            package_root = Path(argument.split("=", 1)[1]).resolve()
            candidate = package_root / "upstream" / "ihp"
            if (candidate / "cni").is_dir() and (
                candidate / "ihp" / "refs" / "ihp_pycell"
            ).is_dir():
                return candidate
    return None


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

    arguments = list(sys.argv[1:])
    vendored = _vendored_ihp_root(arguments)
    if vendored is not None and "--ihp-root" not in arguments:
        arguments.extend(["--ihp-root", str(vendored)])
    return pcells.main_cli(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
