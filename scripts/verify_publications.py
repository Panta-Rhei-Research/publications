#!/usr/bin/env python3
"""Validate publication artifact folders, manifests, and catalogs."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from lib_publications import (
    ALLOWED_ARTIFACT_AVAILABILITY,
    ALLOWED_ROLES,
    ALLOWED_ROUTE_STATUS,
    ALLOWED_STATUS,
    ALLOWED_TYPES,
    CATALOG_DIR,
    ROOT,
    hash_file,
    iter_publication_dirs,
    load_manifest,
    registry_entry,
)


EXPECTED_RELEASED_COUNTS = {
    "research_paper": 9,
    "research_note": 6,
    "public_good_briefing": 44,
    "white_paper": 5,
    "research_monograph": 7,
    "monograph_supplement": 2,
    "synoptic_overview": 1,
    "guided_tour": 7,
}
EXPECTED_SUPERSEDED_COUNTS = {"public_good_briefing": 1}
EXPECTED_PLANNED_COUNTS = {"charter_essay": 2}
EXPECTED_PDF_COUNT = 75
EXPECTED_EXTERNAL_COUNT = 7


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
    released = sum(1 for manifest in manifests if manifest.get("status") == "released")
    print(f"Validated {len(manifests)} publication records ({released} released artifacts).")
    return 0


def validate_item_dir(item_dir: Path) -> list[str]:
    errors: list[str] = []
    if (
        not re.match(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+$", item_dir.name)
        and not re.match(r"^[a-z]{1,4}[0-9]{3}-[a-z0-9-]+$", item_dir.name)
        and not re.match(r"^book-[ivx]+$", item_dir.name)
    ):
        errors.append(f"invalid item folder name: {item_dir.relative_to(ROOT)}")
    for required in ("README.md", "manifest.json"):
        if not (item_dir / required).exists():
            errors.append(f"missing {required}: {item_dir.relative_to(ROOT)}")
    manifest_path = item_dir / "manifest.json"
    if not manifest_path.exists():
        return errors
    manifest = load_manifest(manifest_path)
    errors.extend(validate_manifest_contract(manifest, manifest_path))
    status = manifest.get("status")
    availability = manifest.get("artifact_availability", manifest.get("publication", {}).get("artifact_availability"))
    pdfs = sorted(item_dir.glob("*.pdf"))
    if availability == "local_pdf":
        if len(pdfs) != 1:
            errors.append(f"expected one PDF in {item_dir.relative_to(ROOT)}, found {len(pdfs)}")
            return errors
        errors.extend(validate_released_file(item_dir, pdfs[0], manifest))
    elif availability == "external_link":
        if pdfs:
            errors.append(f"external-link item unexpectedly contains PDF: {item_dir.relative_to(ROOT)}")
        if status != "released":
            errors.append(f"external-link item should be released: {manifest_path.relative_to(ROOT)}")
        if not manifest.get("publication", {}).get("external_links"):
            errors.append(f"external-link item has no external links: {manifest_path.relative_to(ROOT)}")
    else:
        if pdfs:
            errors.append(f"planned/non-released item unexpectedly contains PDF: {item_dir.relative_to(ROOT)}")
        ots = manifest.get("opentimestamps", {})
        if ots.get("status") != "not_applicable":
            errors.append(f"planned item should have OpenTimestamps status not_applicable: {manifest_path.relative_to(ROOT)}")
    return errors


def validate_manifest_contract(manifest: dict[str, Any], path: Path) -> list[str]:
    errors: list[str] = []
    for key in ("publication_id", "publication_key", "type", "publication_role", "status"):
        if not manifest.get(key):
            errors.append(f"missing {key} in {path.relative_to(ROOT)}")
    if manifest.get("type") not in ALLOWED_TYPES:
        errors.append(f"invalid type in {path.relative_to(ROOT)}: {manifest.get('type')}")
    if manifest.get("publication_role") not in ALLOWED_ROLES:
        errors.append(f"invalid publication_role in {path.relative_to(ROOT)}: {manifest.get('publication_role')}")
    if manifest.get("status") not in ALLOWED_STATUS:
        errors.append(f"invalid status in {path.relative_to(ROOT)}: {manifest.get('status')}")
    availability = manifest.get("artifact_availability")
    if availability not in ALLOWED_ARTIFACT_AVAILABILITY:
        errors.append(f"invalid artifact_availability in {path.relative_to(ROOT)}: {availability}")
    pub = manifest.get("publication", {})
    route_status = pub.get("route_status")
    if route_status not in ALLOWED_ROUTE_STATUS:
        errors.append(f"invalid route_status in {path.relative_to(ROOT)}: {route_status}")
    if pub.get("short_url") and not str(pub["short_url"]).startswith("https://prrp.site/"):
        errors.append(f"invalid short_url in {path.relative_to(ROOT)}")
    if manifest.get("status") == "released" and not str(pub.get("canonical_url", "")).startswith("https://panta-rhei.site/"):
        errors.append(f"released item missing canonical website URL in {path.relative_to(ROOT)}")
    claim = pub.get("claim_boundary", {})
    if not isinstance(claim, dict) or not claim.get("claim") or not claim.get("non_claim"):
        errors.append(f"missing claim_boundary claim/non_claim in {path.relative_to(ROOT)}")
    route = registry_entry(str(manifest.get("id", "")))
    if route and route.get("publication_id") != manifest.get("publication_id"):
        errors.append(f"publication_id does not match registry in {path.relative_to(ROOT)}")
    return errors


def validate_released_file(item_dir: Path, pdf: Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    manifest_path = item_dir / "manifest.json"
    file = manifest.get("file", {})
    pub = manifest.get("publication", {})
    hashes = hash_file(pdf)
    for key in ("sha256", "sha512", "bytes"):
        if file.get(key) != hashes[key]:
            errors.append(f"{key} mismatch in {manifest_path.relative_to(ROOT)}")
    if pub.get("pdf_filename") != pdf.name or file.get("path") != pdf.name:
        errors.append(f"PDF filename mismatch in {manifest_path.relative_to(ROOT)}")
    doi = pub.get("doi", "")
    if doi and doi != "forthcoming" and not re.match(r"^10\.\d{4,9}/\S+$", doi):
        errors.append(f"invalid DOI shape in {manifest_path.relative_to(ROOT)}: {doi}")
    ots = manifest.get("opentimestamps", {})
    if ots.get("status") not in {"missing", "pending", "complete"}:
        errors.append(f"invalid OpenTimestamps status in {manifest_path.relative_to(ROOT)}")
    receipt = ots.get("receipt_path", "")
    if receipt and not (item_dir / receipt).exists():
        errors.append(f"manifest references missing OTS receipt in {manifest_path.relative_to(ROOT)}")
    return errors


def validate_counts(manifests: list[dict[str, Any]]) -> list[str]:
    released: dict[str, int] = {}
    superseded: dict[str, int] = {}
    planned: dict[str, int] = {}
    ids: set[str] = set()
    errors: list[str] = []
    pdf_count = 0
    external_count = 0
    for manifest in manifests:
        publication_id = manifest.get("publication_id")
        if publication_id in ids:
            errors.append(f"duplicate publication_id: {publication_id}")
        ids.add(publication_id)
        availability = manifest.get("artifact_availability")
        if availability == "local_pdf":
            pdf_count += 1
        if availability == "external_link":
            external_count += 1
        if manifest.get("status") == "released":
            target = released
        elif manifest.get("status") == "superseded":
            target = superseded
        else:
            target = planned
        target[manifest.get("type", "unknown")] = target.get(manifest.get("type", "unknown"), 0) + 1
    if released != EXPECTED_RELEASED_COUNTS:
        errors.append(f"unexpected released counts: {released}, expected {EXPECTED_RELEASED_COUNTS}")
    if superseded != EXPECTED_SUPERSEDED_COUNTS:
        errors.append(f"unexpected superseded counts: {superseded}, expected {EXPECTED_SUPERSEDED_COUNTS}")
    if planned != EXPECTED_PLANNED_COUNTS:
        errors.append(f"unexpected planned counts: {planned}, expected {EXPECTED_PLANNED_COUNTS}")
    if pdf_count != EXPECTED_PDF_COUNT:
        errors.append(f"unexpected PDF-bearing count: {pdf_count}, expected {EXPECTED_PDF_COUNT}")
    if external_count != EXPECTED_EXTERNAL_COUNT:
        errors.append(f"unexpected external-link count: {external_count}, expected {EXPECTED_EXTERNAL_COUNT}")
    return errors


def validate_catalogs(manifests: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    catalog_path = CATALOG_DIR / "publications.json"
    if not catalog_path.exists():
        return ["missing catalog/publications.json"]
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if catalog.get("publication_count") != len(manifests):
        errors.append("catalog publication_count mismatch")
    if catalog.get("released_publication_count") != sum(1 for manifest in manifests if manifest.get("status") == "released"):
        errors.append("catalog released_publication_count mismatch")
    if catalog.get("pdf_publication_count") != sum(1 for manifest in manifests if manifest.get("artifact_availability") == "local_pdf"):
        errors.append("catalog pdf_publication_count mismatch")
    catalog_ids = sorted(item.get("id") for item in catalog.get("publications", []))
    manifest_ids = sorted(manifest.get("id") for manifest in manifests)
    if catalog_ids != manifest_ids:
        errors.append("catalog IDs do not match manifests")
    for checksum_file in ("checksums.sha256", "checksums.sha512", "publications.csv", "publications.yml"):
        if not (CATALOG_DIR / checksum_file).exists():
            errors.append(f"missing catalog/{checksum_file}")
    check = subprocess.run(["python3", "scripts/build_manifests.py", "--check"], cwd=ROOT, text=True, check=False)
    if check.returncode:
        errors.append("generated manifests/catalogs are stale")
    return errors


def validate_site_byte_identity(manifests: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    site_root = Path(os.environ.get("PANTA_RHEI_SITE_ROOT", ROOT.parent / "site"))
    if not site_root.exists():
        print(f"Skipping source byte-identity check; site repo is not present: {site_root}")
        return errors
    for manifest in manifests:
        if manifest.get("artifact_availability") != "local_pdf":
            continue
        file = manifest.get("file", {})
        source = file.get("source_website_asset_path", "")
        if not source.startswith("site/"):
            errors.append(f"missing source website asset path for {manifest.get('id')}")
            continue
        source_path = site_root / source.removeprefix("site/")
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
