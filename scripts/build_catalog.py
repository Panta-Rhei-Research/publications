#!/usr/bin/env python3
"""Build or check aggregate publication catalog outputs."""

from __future__ import annotations

import argparse
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if catalog/generated files are stale.")
    args = parser.parse_args()
    command = ["python3", "scripts/build_manifests.py"]
    if args.check:
        command.append("--check")
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
