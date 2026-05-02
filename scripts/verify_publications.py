#!/usr/bin/env python3
"""Validate publication artifact folders, manifests, and catalogs."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from lib_publications import CATALOG_DIR, ROOT, hash_file, iter_publication_dirs, load_manifest


EXPECTED_COUNTS = {
    "research-papers": 9,
    "research-notes": 6,
    "research-briefings/public-good": 1,
    "white-papers": 1,
}


def main() -> int:
    errors: list[str] = []
    manifests: list[dict[str, Any]] = []
    for item_dir in iter_publication_dirs():
        errors.extend(validate_item_dir(item_dir))
        manifest_path = item_dir / "manifest.json"
        if manifest_path.exists():
            manifests.append(load_manifest(manifest_path))
    errors.extend(validate_counts(manifests))
    errors.extend(validate_catalogs(manifests))
    errors.extend(validate_site_byte_identity(manifests))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Validated {len(manifests)} publication artifacts.")
    return 0


def validate_item_dir(item_dir: Path) -> list[str]:
    errors: list[str] = []
    if not re.match(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+$", item_dir.name):
        errors.append(f"invalid item folder name: {item_dir.relative_to(ROOT)}")
    for required in ("README.md", "manifest.json"):
        if not (item_dir / required).exists():
            errors.append(f"missing {required}: {item_dir.relative_to(ROOT)}")
    pdfs = sorted(item_dir.glob("*.pdf"))
    if len(pdfs) != 1:
        errors.append(f"expected one PDF in {item_dir.relative_to(ROOT)}, found {len(pdfs)}")
        return errors
    manifest_path = item_dir / "manifest.json"
    if not manifest_path.exists():
        return errors
    manifest = load_manifest(manifest_path)
    file = manifest.get("file", {})
    pub = manifest.get("publication", {})
    hashes = hash_file(pdfs[0])
    for key in ("sha256", "sha512", "bytes"):
        if file.get(key) != hashes[key]:
            errors.append(f"{key} mismatch in {manifest_path.relative_to(ROOT)}")
    for key in ("title", "publication_type", "authors", "date", "version", "website_url"):
        if not pub.get(key):
            errors.append(f"missing publication.{key} in {manifest_path.relative_to(ROOT)}")
    doi = pub.get("doi", "")
    if doi and not re.match(r"^10\.\d{4,9}/\S+$", doi):
        errors.append(f"invalid DOI shape in {manifest_path.relative_to(ROOT)}: {doi}")
    if not str(pub.get("website_url", "")).startswith("https://panta-rhei.site/"):
        errors.append(f"invalid website URL in {manifest_path.relative_to(ROOT)}")
    ots = manifest.get("opentimestamps", {})
    if ots.get("status") not in {"missing", "pending", "complete"}:
        errors.append(f"invalid OpenTimestamps status in {manifest_path.relative_to(ROOT)}")
    receipt = ots.get("receipt_path", "")
    if receipt and not (item_dir / receipt).exists():
        errors.append(f"manifest references missing OTS receipt in {manifest_path.relative_to(ROOT)}")
    return errors


def validate_counts(manifests: list[dict[str, Any]]) -> list[str]:
    counts: dict[str, int] = {}
    for manifest in manifests:
        source = manifest.get("file", {}).get("source_website_asset_path", "")
        if "/research-papers/" in source:
            key = "research-papers"
        elif "/research-notes/" in source:
            key = "research-notes"
        elif "/research-briefings/public-good/" in source:
            key = "research-briefings/public-good"
        elif "/white-papers/" in source:
            key = "white-papers"
        else:
            key = "unknown"
        counts[key] = counts.get(key, 0) + 1
    if counts != EXPECTED_COUNTS:
        return [f"unexpected publication counts: {counts}, expected {EXPECTED_COUNTS}"]
    return []


def validate_catalogs(manifests: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    catalog_path = CATALOG_DIR / "publications.json"
    if not catalog_path.exists():
        return ["missing catalog/publications.json"]
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if catalog.get("publication_count") != len(manifests):
        errors.append("catalog publication_count mismatch")
    catalog_ids = sorted(item.get("id") for item in catalog.get("publications", []))
    manifest_ids = sorted(manifest.get("id") for manifest in manifests)
    if catalog_ids != manifest_ids:
        errors.append("catalog IDs do not match manifests")
    for checksum_file in ("checksums.sha256", "checksums.sha512", "publications.csv"):
        if not (CATALOG_DIR / checksum_file).exists():
            errors.append(f"missing catalog/{checksum_file}")
    check = subprocess.run(["python3", "scripts/build_manifests.py", "--check"], cwd=ROOT, text=True, check=False)
    if check.returncode:
        errors.append("generated manifests/catalogs are stale")
    return errors


def validate_site_byte_identity(manifests: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    site_root = ROOT.parent / "site"
    if not site_root.exists():
        print("Skipping source byte-identity check; sibling site repo is not present.")
        return errors
    for manifest in manifests:
        file = manifest.get("file", {})
        source = file.get("source_website_asset_path", "")
        if not source.startswith("site/"):
            errors.append(f"missing source website asset path for {manifest.get('id')}")
            continue
        source_path = site_root.parent / source
        target_path = find_pdf_for_manifest(manifest)
        if not source_path.exists():
            errors.append(f"missing source asset: {source}")
            continue
        if hash_file(source_path)["sha256"] != hash_file(target_path)["sha256"]:
            errors.append(f"source byte mismatch for {manifest.get('id')}")
    return errors


def find_pdf_for_manifest(manifest: dict[str, Any]) -> Path:
    for item_dir in iter_publication_dirs():
        if item_dir.name == manifest.get("id"):
            return item_dir / manifest["file"]["path"]
    raise SystemExit(f"Cannot find publication folder for {manifest.get('id')}")


if __name__ == "__main__":
    raise SystemExit(main())
