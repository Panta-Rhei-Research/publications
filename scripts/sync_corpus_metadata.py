#!/usr/bin/env python3
"""Sync public-safe Corpus publication metadata into this artifact mirror."""

from __future__ import annotations

import argparse
import filecmp
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPORTS = ROOT.parent / "corpus" / "exports" / "public"
CORPUS_EXPORTS = Path(os.environ.get("CORPUS_EXPORTS_DIR", DEFAULT_EXPORTS))
SOURCE_DIR = CORPUS_EXPORTS / "publications-repo"
TARGET_DIR = ROOT / "metadata" / "corpus"
FILES = ("publications-metadata.json", "publications-metadata.yml")


def sync_file(source: Path, target: Path, check: bool) -> bool:
    if not source.exists():
        raise SystemExit(f"Missing Corpus export: {source}")
    if check:
        if not target.exists() or not filecmp.cmp(source, target, shallow=False):
            print(f"stale: {target.relative_to(ROOT)}")
            return False
        print(f"ok: {target.relative_to(ROOT)}")
        return True
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    print(f"synced {target.relative_to(ROOT)}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if generated metadata is stale.")
    args = parser.parse_args()

    if not SOURCE_DIR.exists():
        raise SystemExit(f"Missing Corpus publications-repo export directory: {SOURCE_DIR}")

    ok = True
    for name in FILES:
        ok = sync_file(SOURCE_DIR / name, TARGET_DIR / name, args.check) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
