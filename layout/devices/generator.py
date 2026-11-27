#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""IHP SG13G2 device generator backed by the OpenVLSI ``openvlsipy`` PCell runtime.

The IHP PyCell sources are vendored under ``vendor/ihp`` so the package is
self-contained. OpenVLSI invokes this script with:

    generator.py --pdk-root <package> --module nmos_code --class nmos \
                        --params-file params.json --output geometry.json

The upstream PyCell implementation is evaluated by ``openvlsipy.pcells`` and the
resulting polygons are transferred through the OpenVLSI layout API.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _vendored_ihp_root(argv: list[str]) -> Path | None:
    for index, argument in enumerate(argv):
        if argument == "--pdk-root" and index + 1 < len(argv):
            package_root = Path(argv[index + 1]).resolve()
            candidate = package_root / "vendor" / "ihp"
            if (candidate / "cni").is_dir() and (
                candidate / "ihp" / "refs" / "ihp_pycell"
            ).is_dir():
                return candidate
        elif argument.startswith("--pdk-root="):
            package_root = Path(argument.split("=", 1)[1]).resolve()
            candidate = package_root / "vendor" / "ihp"
            if (candidate / "cni").is_dir() and (
                candidate / "ihp" / "refs" / "ihp_pycell"
            ).is_dir():
                return candidate
    return None


def main() -> int:
    try:
        import openvlsipy  # noqa: F401  (the runtime needs the bindings)
    except ImportError as error:
        print(
            "The IHP device generator requires the OpenVLSI openvlsipy Python module. "
            f"Set PYTHONPATH to the OpenVLSI python/ directory and build the openvlsipy target. ({error})",
            file=sys.stderr,
        )
        return 2

    sys.path.insert(0, str(Path(__file__).resolve().parent / "pcell"))
    from ihp_runtime import main_cli

    arguments = list(sys.argv[1:])
    vendored = _vendored_ihp_root(arguments)
    if vendored is not None and "--ihp-root" not in arguments:
        arguments.extend(["--ihp-root", str(vendored)])
    return main_cli(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
