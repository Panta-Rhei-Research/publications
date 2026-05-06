#!/usr/bin/env python3
"""Build per-publication manifests and root catalog files."""

from __future__ import annotations

import argparse
import csv
import io
import re
import subprocess
from pathlib import Path
from typing import Any

from lib_publications import (
    CATALOG_DIR,
    ROOT,
    canonical_json,
    display_label,
    hash_file,
    iter_publication_dirs,
    load_manifest,
    normalize_publication_type,
    normalize_status,
    registry_entry,
    to_simple_yaml,
    utc_now,
    write_csv,
    write_json,
)


README_TABLE_START = "<!-- BEGIN GENERATED PUBLICATIONS TABLE -->"
README_TABLE_END = "<!-- END GENERATED PUBLICATIONS TABLE -->"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if generated files are stale.")
    parser.add_argument("--verify-ots", action="store_true", help="Attempt live OpenTimestamps verification.")
    args = parser.parse_args()

    changed: list[Path] = []
    manifests: list[dict[str, Any]] = []
    for item_dir in iter_publication_dirs():
        manifest = build_manifest(item_dir, verify_ots=args.verify_ots)
        manifests.append(manifest)
        changed.extend(write_or_check_json(item_dir / "manifest.json", manifest, args.check))

    rows = [flatten_manifest(manifest) for manifest in manifests]
    rows.sort(key=lambda row: (row["status"] != "released", row["type"], row["date"], row["publication_id"]))
    released_rows = [row for row in rows if row["status"] == "released" and row["pdf"]]

    catalog = {
        "schema": "panta-rhei-publications-catalog-v2",
        "publication_count": len(rows),
        "released_publication_count": len(released_rows),
        "generated_at": stable_catalog_generated_at(manifests),
        "publications": rows,
    }
    changed.extend(write_or_check_json(CATALOG_DIR / "publications.json", catalog, args.check))
    changed.extend(write_or_check_yaml(CATALOG_DIR / "publications.yml", catalog, args.check))
    changed.extend(write_or_check_yaml(ROOT / "publications.yml", catalog, args.check))
    changed.extend(write_or_check_csv(CATALOG_DIR / "publications.csv", rows, args.check))
    changed.extend(write_or_check_text(CATALOG_DIR / "checksums.sha256", render_checksums(released_rows, "sha256"), args.check))
    changed.extend(write_or_check_text(CATALOG_DIR / "checksums.sha512", render_checksums(released_rows, "sha512"), args.check))
    changed.extend(update_readme_table(rows, args.check))

    if args.check and changed:
        for path in changed:
            print(f"stale: {path.relative_to(ROOT)}")
        return 1
    print(f"Built manifests for {len(rows)} publication artifacts ({len(released_rows)} released with PDFs).")
    return 0


def build_manifest(item_dir: Path, verify_ots: bool = False) -> dict[str, Any]:
    readme = item_dir / "README.md"
    if not readme.exists():
        raise SystemExit(f"Missing README: {item_dir}")
    pdfs = sorted(item_dir.glob("*.pdf"))
    existing = load_manifest(item_dir / "manifest.json") if (item_dir / "manifest.json").exists() else {}
    metadata = parse_readme_metadata(readme)
    route = registry_entry(item_dir.name)
    publication_type = str(route.get("type") or normalize_publication_type(metadata.get("type", "")))
    status = str(route.get("status") or normalize_status(metadata.get("status", "")))
    is_released = status == "released"

    if is_released and len(pdfs) != 1:
        raise SystemExit(f"Expected exactly one PDF in {item_dir}, found {len(pdfs)}")
    if not is_released and len(pdfs) > 1:
        raise SystemExit(f"Expected at most one PDF in planned item {item_dir}, found {len(pdfs)}")

    pdf = pdfs[0] if pdfs else None
    hashes = hash_file(pdf) if pdf else {"bytes": 0, "sha256": "", "sha512": ""}
    existing_file = existing.get("file", {})
    generated_at = existing.get("generated_at")
    if not generated_at or existing_file.get("sha256") != hashes["sha256"] or existing_file.get("sha512") != hashes["sha512"]:
        generated_at = utc_now()

    title = metadata.get("title", "")
    canonical_url = metadata.get("website", "")
    if canonical_url == "null":
        canonical_url = ""
    pdf_name = pdf.name if pdf else ""
    claim_boundary = claim_boundary_from_readme(readme, publication_type)

    return {
        "schema": "panta-rhei-publication-manifest-v2",
        "id": item_dir.name,
        "publication_id": route.get("publication_id", item_dir.name),
        "publication_key": route.get("publication_key", key_from_title(publication_type, title)),
        "type": publication_type,
        "publication_role": route.get("publication_role", default_role(publication_type)),
        "status": status,
        "generated_at": generated_at,
        "publication": {
            "title": title,
            "subtitle": metadata.get("subtitle", ""),
            "publication_type": metadata.get("type", display_label(publication_type)),
            "authors": metadata.get("authors", ""),
            "date": metadata.get("date", ""),
            "version": metadata.get("version", ""),
            "status": metadata.get("status", display_label(status)),
            "doi": normalize_doi(metadata.get("doi", "")),
            "doi_url": doi_url(normalize_doi(metadata.get("doi", ""))),
            "zenodo_url": doi_url(normalize_doi(metadata.get("doi", ""))),
            "website_url": canonical_url,
            "canonical_url": canonical_url,
            "short_url": route.get("short_url", ""),
            "route_status": route.get("route_status", "not_applicable"),
            "source_website_page": "" if metadata.get("source website page", "").strip("`") == "null" else metadata.get("source website page", "").strip("`"),
            "github_path": str(item_dir.relative_to(ROOT)),
            "pdf_filename": pdf_name,
            "abstract": extract_section(readme, "Abstract"),
            "claim_boundary": claim_boundary,
            "related_lanes": route.get("related_lanes", []),
            "related_routes": route.get("related_routes", []),
            "license": route.get("license", metadata.get("license", "CC-BY-4.0")),
        },
        "file": {
            "path": pdf_name,
            "bytes": hashes["bytes"],
            "sha256": hashes["sha256"],
            "sha512": hashes["sha512"],
            "source_website_asset_path": source_asset_path(pdf_name) if pdf_name else "",
        },
        "checksums": {
            "sha256": hashes["sha256"],
            "sha512": hashes["sha512"],
        },
        "opentimestamps": ots_status(pdf, existing.get("opentimestamps", {}), verify_ots=verify_ots) if pdf else {
            "status": "not_applicable",
            "receipt_path": "",
            "verification": "no-pdf-planned-item",
        },
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
            data[key.strip().lower()] = value.strip().strip("`")
    return data


def extract_section(path: Path, heading: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"^## {re.escape(heading)}\s*$", text, flags=re.MULTILINE | re.IGNORECASE)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r"^##\s+", text[start:], flags=re.MULTILINE)
    end = start + next_match.start() if next_match else len(text)
    return re.sub(r"\n{3,}", "\n\n", text[start:end].strip())


def claim_boundary_from_readme(path: Path, publication_type: str) -> dict[str, str]:
    section = extract_section(path, "Claim Boundary") or extract_section(path, "Claim boundary")
    if section:
        return {"claim": section, "non_claim": infer_non_claim(section)}
    return {
        "claim": f"This artifact is a {display_label(publication_type).lower()} publication record.",
        "non_claim": "It does not by itself certify correctness, peer review, external acceptance, empirical adequacy, legal ownership, or DOI registration.",
    }


def infer_non_claim(section: str) -> str:
    lowered = section.lower()
    marker = "does not claim"
    if marker in lowered:
        index = lowered.find(marker)
        return section[index:].strip()
    return "This boundary does not certify correctness, peer review, external acceptance, empirical adequacy, legal ownership, or DOI registration."


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
        "publication_id": manifest["publication_id"],
        "publication_key": manifest["publication_key"],
        "publication_type": pub["publication_type"],
        "type": manifest["type"],
        "publication_role": manifest["publication_role"],
        "status": manifest["status"],
        "title": pub["title"],
        "date": pub["date"],
        "version": pub["version"],
        "doi": pub["doi"],
        "doi_url": pub["doi_url"],
        "website_url": pub["website_url"],
        "canonical_url": pub["canonical_url"],
        "short_url": pub["short_url"],
        "route_status": pub["route_status"],
        "github_path": pub["github_path"],
        "pdf": file["path"],
        "bytes": file["bytes"],
        "sha256": file["sha256"],
        "sha512": file["sha512"],
        "ots_status": ots["status"],
    }


def stable_catalog_generated_at(manifests: list[dict[str, Any]]) -> str:
    if manifests:
        return max(str(manifest.get("generated_at", "")) for manifest in manifests)
    return utc_now()


def render_checksums(rows: list[dict[str, Any]], key: str) -> str:
    return "".join(f"{row[key]}  {row['type']}/{row['id']}/{row['pdf']}\n" for row in rows if row.get(key) and row.get("pdf"))


def default_role(publication_type: str) -> str:
    return {
        "charter_essay": "orientation",
        "research_note": "dialogue",
        "research_paper": "technical",
        "verification_manifest": "verification",
        "public_good_briefing": "translation",
        "release_record": "governance",
        "erratum": "correction",
        "white_paper": "orientation",
    }.get(publication_type, "technical")


def key_from_title(publication_type: str, title: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return f"{publication_type}s.{key}" if key else publication_type


def normalize_doi(value: str) -> str:
    clean = value.strip()
    if clean.lower() in {"", "not assigned", "forthcoming", "null"}:
        return "" if clean.lower() != "forthcoming" else "forthcoming"
    return clean.removeprefix("https://doi.org/")


def doi_url(value: str) -> str:
    if value and value != "forthcoming":
        return f"https://doi.org/{value}"
    return ""


def write_or_check_json(path: Path, data: Any, check: bool) -> list[Path]:
    return write_or_check_text(path, canonical_json(data), check)


def write_or_check_yaml(path: Path, data: Any, check: bool) -> list[Path]:
    return write_or_check_text(path, to_simple_yaml(data) + "\n", check)


def write_or_check_csv(path: Path, rows: list[dict[str, Any]], check: bool) -> list[Path]:
    if check:
        fields = [
            "id",
            "publication_id",
            "publication_key",
            "publication_type",
            "type",
            "publication_role",
            "status",
            "title",
            "date",
            "version",
            "doi",
            "website_url",
            "canonical_url",
            "short_url",
            "route_status",
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
        return write_or_check_text(path, buffer.getvalue(), check)
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


def update_readme_table(rows: list[dict[str, Any]], check: bool) -> list[Path]:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    if README_TABLE_START not in text or README_TABLE_END not in text:
        return []
    table = render_readme_table(rows)
    start = text.index(README_TABLE_START) + len(README_TABLE_START)
    end = text.index(README_TABLE_END)
    rendered = text[:start] + "\n" + table + "\n" + text[end:]
    return write_or_check_text(path, rendered, check)


def render_readme_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| ID | Type | Role | Status | Title | Date | Canonical | Short |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        if row.get("status") != "released":
            continue
        canonical = f"[Website]({row['canonical_url']})" if row.get("canonical_url") else "planned"
        if row.get("short_url") and row.get("route_status") == "active":
            short = f"[{row['short_url'].removeprefix('https://')}]({row['short_url']})"
        elif row.get("short_url"):
            short = f"`{row['short_url'].removeprefix('https://')}`"
        else:
            short = ""
        lines.append(
            f"| `{row['publication_id']}` | {display_label(row['type'])} | {display_label(row['publication_role'])} | "
            f"{display_label(row['status'])} | {row['title']} | {row['date'] or 'planned'} | {canonical} | {short} |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
