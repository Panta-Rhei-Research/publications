#!/usr/bin/env python3
"""Create or upgrade OpenTimestamps receipts for publication PDFs."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from lib_publications import ROOT, iter_publication_dirs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upgrade", action="store_true", help="Attempt to upgrade existing receipts.")
    parser.add_argument("--verify", action="store_true", help="Attempt verification after stamping/upgrading.")
    args = parser.parse_args()

    if shutil.which("ots") is None:
        raise SystemExit("OpenTimestamps client not found. Install with: python3 -m pip install opentimestamps-client")

    pdfs = [pdf for item_dir in iter_publication_dirs() for pdf in sorted(item_dir.glob("*.pdf"))]
    if not pdfs:
        raise SystemExit("No publication PDFs found.")

    for pdf in pdfs:
        receipt = pdf.with_suffix(pdf.suffix + ".ots")
        if receipt.exists():
            print(f"receipt exists: {receipt.relative_to(ROOT)}")
        else:
            run(["ots", "stamp", str(pdf)], cwd=pdf.parent)
        if args.upgrade and receipt.exists():
            run(["ots", "upgrade", str(receipt)], cwd=pdf.parent, allow_failure=True)
        if args.verify and receipt.exists():
            run(["ots", "verify", str(pdf)], cwd=pdf.parent, allow_failure=True)

    build_command = ["python3", "scripts/build_manifests.py"]
    if args.verify:
        build_command.append("--verify-ots")
    run(build_command, cwd=ROOT)
    return 0


def run(command: list[str], cwd: Path, allow_failure: bool = False) -> None:
    print("+", " ".join(command))
    result = subprocess.run(command, cwd=cwd, text=True, check=False)
    if result.returncode and not allow_failure:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
