#!/usr/bin/env python3
"""Build per-publication manifests and root catalog files."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

from lib_publications import (
    CATALOG_DIR,
    ROOT,
    canonical_json,
    hash_file,
    iter_publication_dirs,
    load_manifest,
    utc_now,
    write_csv,
    write_json,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if generated files are stale.")
    parser.add_argument("--verify-ots", action="store_true", help="Attempt live OpenTimestamps verification.")
    args = parser.parse_args()

    changed: list[Path] = []
    rows: list[dict[str, Any]] = []
    for item_dir in iter_publication_dirs():
        manifest = build_manifest(item_dir, verify_ots=args.verify_ots)
        rows.append(flatten_manifest(manifest))
        manifest_path = item_dir / "manifest.json"
        changed.extend(write_or_check_json(manifest_path, manifest, args.check))

    rows.sort(key=lambda row: (row["publication_type"], row["date"], row["id"]))
    catalog = {
        "schema": "panta-rhei-publications-catalog-v1",
        "publication_count": len(rows),
        "generated_at": stable_catalog_generated_at(rows),
        "publications": rows,
    }
    changed.extend(write_or_check_json(CATALOG_DIR / "publications.json", catalog, args.check))
    changed.extend(write_or_check_csv(CATALOG_DIR / "publications.csv", rows, args.check))
    changed.extend(write_or_check_text(CATALOG_DIR / "checksums.sha256", render_checksums(rows, "sha256"), args.check))
    changed.extend(write_or_check_text(CATALOG_DIR / "checksums.sha512", render_checksums(rows, "sha512"), args.check))

    if args.check and changed:
        for path in changed:
            print(f"stale: {path.relative_to(ROOT)}")
        return 1
    print(f"Built manifests for {len(rows)} publication artifacts.")
    return 0


def build_manifest(item_dir: Path, verify_ots: bool = False) -> dict[str, Any]:
    readme = item_dir / "README.md"
    if not readme.exists():
        raise SystemExit(f"Missing README: {item_dir}")
    pdfs = sorted(item_dir.glob("*.pdf"))
    if len(pdfs) != 1:
        raise SystemExit(f"Expected exactly one PDF in {item_dir}, found {len(pdfs)}")
    pdf = pdfs[0]
    existing = load_manifest(item_dir / "manifest.json") if (item_dir / "manifest.json").exists() else {}
    metadata = parse_readme_metadata(readme)
    hashes = hash_file(pdf)
    existing_file = existing.get("file", {})
    generated_at = existing.get("generated_at")
    if not generated_at or existing_file.get("sha256") != hashes["sha256"] or existing_file.get("sha512") != hashes["sha512"]:
        generated_at = utc_now()
    ots = ots_status(pdf, existing.get("opentimestamps", {}), verify_ots=verify_ots)
    return {
        "schema": "panta-rhei-publication-manifest-v1",
        "id": item_dir.name,
        "generated_at": generated_at,
        "publication": {
            "title": metadata.get("title", ""),
            "publication_type": metadata.get("type", ""),
            "authors": metadata.get("authors", ""),
            "date": metadata.get("date", ""),
            "version": metadata.get("version", ""),
            "status": metadata.get("status", ""),
            "doi": "" if metadata.get("doi") == "Not assigned" else metadata.get("doi", ""),
            "website_url": metadata.get("website", ""),
            "source_website_page": metadata.get("source website page", "").strip("`"),
        },
        "file": {
            "path": pdf.name,
            "bytes": hashes["bytes"],
            "sha256": hashes["sha256"],
            "sha512": hashes["sha512"],
            "source_website_asset_path": source_asset_path(metadata.get("pdf", "").strip("`")),
        },
        "opentimestamps": ots,
        "integrity_note": "Hashes and timestamps attest to the PDF bytes only; they do not certify correctness, peer review, legal status, DOI registration, or content validity.",
    }


def parse_readme_metadata(path: Path) -> dict[str, str]:
    data: dict[str, str] = {"title": ""}
    lines = path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        if line.startswith("# ") and not data["title"]:
            data["title"] = line[2:].strip()
        if line.startswith("- ") and ":" in line:
            key, value = line[2:].split(":", 1)
            data[key.strip().lower()] = value.strip()
    return data


def source_asset_path(pdf_name: str) -> str:
    if pdf_name.startswith("research-paper-"):
        return f"site/assets/pdfs/research-papers/{pdf_name}"
    if pdf_name.startswith("research-note-"):
        return f"site/assets/pdfs/research-notes/{pdf_name}"
    if pdf_name.startswith("public-good-briefing-"):
        return f"site/assets/pdfs/research-briefings/public-good/{pdf_name}"
    if pdf_name.startswith("white-paper-"):
        return f"site/assets/pdfs/white-papers/{pdf_name}"
    return ""


def ots_status(pdf: Path, existing: dict[str, Any], verify_ots: bool = False) -> dict[str, str]:
    receipt = pdf.with_suffix(pdf.suffix + ".ots")
    if not receipt.exists():
        return {"status": "missing", "receipt_path": "", "verification": "not-stamped"}
    if not verify_ots:
        if existing.get("receipt_path") == receipt.name and existing.get("status") in {"pending", "complete"}:
            return {
                "status": str(existing.get("status")),
                "receipt_path": receipt.name,
                "verification": str(existing.get("verification", "receipt-present")),
            }
        return {"status": "pending", "receipt_path": receipt.name, "verification": "receipt-present"}
    status = "pending"
    verification = "receipt-present"
    try:
        result = subprocess.run(
            ["ots", "verify", str(pdf)],
            cwd=pdf.parent,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
        combined = result.stdout + result.stderr
        if result.returncode == 0 and ("Success" in combined or "attested" in combined.lower()):
            status = "complete"
            verification = "verified"
        else:
            verification = "pending-upgrade-or-network"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        verification = "ots-client-unavailable"
    return {"status": status, "receipt_path": receipt.name, "verification": verification}


def flatten_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    pub = manifest["publication"]
    file = manifest["file"]
    ots = manifest["opentimestamps"]
    return {
        "id": manifest["id"],
        "publication_type": pub["publication_type"],
        "title": pub["title"],
        "date": pub["date"],
        "version": pub["version"],
        "doi": pub["doi"],
        "website_url": pub["website_url"],
        "pdf": file["path"],
        "bytes": file["bytes"],
        "sha256": file["sha256"],
        "sha512": file["sha512"],
        "ots_status": ots["status"],
    }


def stable_catalog_generated_at(rows: list[dict[str, Any]]) -> str:
    manifests = [load_manifest(path / "manifest.json") for path in iter_publication_dirs() if (path / "manifest.json").exists()]
    if len(manifests) == len(rows):
        return max(str(manifest.get("generated_at", "")) for manifest in manifests)
    return utc_now()


def render_checksums(rows: list[dict[str, Any]], key: str) -> str:
    return "".join(f"{row[key]}  {row['publication_type']}/{row['id']}/{row['pdf']}\n" for row in rows)


def write_or_check_json(path: Path, data: Any, check: bool) -> list[Path]:
    rendered = canonical_json(data)
    return write_or_check_text(path, rendered, check)


def write_or_check_csv(path: Path, rows: list[dict[str, Any]], check: bool) -> list[Path]:
    if check:
        import io
        import csv

        fields = [
            "id",
            "publication_type",
            "title",
            "date",
            "version",
            "doi",
            "website_url",
            "pdf",
            "bytes",
            "sha256",
            "sha512",
            "ots_status",
        ]
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
        rendered = buffer.getvalue()
        return write_or_check_text(path, rendered, check)
    write_csv(path, rows)
    return []


def write_or_check_text(path: Path, rendered: str, check: bool) -> list[Path]:
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != rendered:
            return [path]
        return []
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return []


if __name__ == "__main__":
    raise SystemExit(main())
