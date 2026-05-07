#!/usr/bin/env python3
"""Validate the Corpus publication metadata projection against local manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lib_publications import ROOT, iter_publication_dirs, load_manifest


PROJECTION = ROOT / "metadata" / "corpus" / "publications-metadata.json"
EXPECTED_COUNT = 84


def load_projection() -> list[dict[str, Any]]:
    if not PROJECTION.exists():
        raise SystemExit(f"Missing Corpus metadata projection: {PROJECTION.relative_to(ROOT)}")
    data = json.loads(PROJECTION.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("Corpus publication metadata projection must be a JSON list.")
    return data


def manifest_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item_dir in iter_publication_dirs():
        manifest_path = item_dir / "manifest.json"
        if manifest_path.exists():
            manifest = load_manifest(manifest_path)
            manifest["_manifest_path"] = str(manifest_path.relative_to(ROOT))
            records.append(manifest)
    return records


def main() -> int:
    errors: list[str] = []
    projection = load_projection()
    manifests = manifest_records()
    projected_by_id = {record.get("publication_id"): record for record in projection}
    manifest_by_id = {record.get("publication_id"): record for record in manifests}

    if len(projection) != EXPECTED_COUNT:
        errors.append(f"expected {EXPECTED_COUNT} Corpus publication metadata records, found {len(projection)}")
    if len(projected_by_id) != len(projection):
        errors.append("duplicate publication_id in Corpus metadata projection")
    if len(manifest_by_id) != len(manifests):
        errors.append("duplicate publication_id in local publication manifests")

    missing_projection = sorted(set(manifest_by_id) - set(projected_by_id))
    extra_projection = sorted(set(projected_by_id) - set(manifest_by_id))
    if missing_projection:
        errors.append(f"local manifests missing from Corpus projection: {', '.join(missing_projection)}")
    if extra_projection:
        expected_planned = {"c001", "c002"}
        unexpected = sorted(set(extra_projection) - expected_planned)
        if unexpected:
            errors.append(f"Corpus projection records without local manifest: {', '.join(unexpected)}")

    for publication_id, manifest in sorted(manifest_by_id.items()):
        projected = projected_by_id.get(publication_id)
        if not projected:
            continue
        manifest_path = manifest["_manifest_path"]
        if projected.get("github_path") and projected.get("github_path") not in manifest_path:
            errors.append(f"github_path does not match local manifest path for {publication_id}: {projected.get('github_path')}")
        for key in ("type", "status", "artifact_availability", "publication_key"):
            if projected.get(key) != manifest.get(key):
                errors.append(f"{key} mismatch for {publication_id}: corpus={projected.get(key)!r} manifest={manifest.get(key)!r}")
        publication = manifest.get("publication", {})
        if projected.get("title") != publication.get("title"):
            errors.append(f"title mismatch for {publication_id}")
        if projected.get("canonical_url") != publication.get("canonical_url"):
            errors.append(f"canonical_url mismatch for {publication_id}")
        if projected.get("short_url") != publication.get("short_url"):
            errors.append(f"short_url mismatch for {publication_id}")
        if manifest.get("artifact_availability") == "local_pdf":
            integrity = projected.get("integrity", {})
            file_info = manifest.get("file", {})
            for key in ("bytes", "sha256", "sha512"):
                if integrity.get(key) != file_info.get(key):
                    errors.append(f"{key} integrity mismatch for {publication_id}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"Validated Corpus metadata projection against {len(manifests)} local publication manifests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
