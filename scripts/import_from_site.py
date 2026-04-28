#!/usr/bin/env python3
"""Seed publication artifacts from the sibling site repo."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

from lib_publications import (
    ROOT,
    SITE_ROOT,
    extract_first,
    extract_section,
    parse_frontmatter,
    read_text,
    slugify,
)


AUTHORS = "Thorsten Fuchs and Anna-Sophie Fuchs"
BASE_URL = "https://panta-rhei.site"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", type=Path, default=SITE_ROOT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    site_root = args.site_root.resolve()
    if not site_root.exists():
        raise SystemExit(f"Missing site root: {site_root}")

    items = collect_items(site_root)
    expected_counts = {"research-papers": 9, "research-notes": 6, "research-briefings/public-good": 1}
    counts: dict[str, int] = {}
    for item in items:
        counts[item["category_path"]] = counts.get(item["category_path"], 0) + 1
    if counts != expected_counts:
        raise SystemExit(f"Unexpected seed counts: {counts}, expected {expected_counts}")

    for item in sorted(items, key=lambda entry: (entry["publication_type"], entry["date"], entry["slug"])):
        target_dir = ROOT / item["category_path"] / f"{item['date']}-{item['slug']}"
        pdf_source = site_root / item["pdf_source"].lstrip("/")
        pdf_target = target_dir / pdf_source.name
        if not pdf_source.exists():
            raise SystemExit(f"Missing PDF source: {pdf_source}")
        print(f"{item['publication_type']}: {pdf_source} -> {pdf_target}")
        if args.dry_run:
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf_source, pdf_target)
        (target_dir / "README.md").write_text(render_readme(item, pdf_target.name), encoding="utf-8")
    return 0


def collect_items(site_root: Path) -> list[dict[str, str]]:
    return [
        *collect_research_papers(site_root),
        *collect_research_notes(site_root),
        *collect_public_good_briefings(site_root),
    ]


def collect_research_papers(site_root: Path) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for page in sorted((site_root / "publications" / "research-papers").glob("*/index.md")):
        data, body = parse_frontmatter(read_text(page))
        pdf = extract_first(r"\{\{\s*'([^']+\.pdf)'\s*\|\s*relative_url\s*\}\}", body)
        date = extract_first(r"^- Publication date:\s*([0-9-]+)\s*$", body)
        version = extract_first(r"^- Version:\s*([^·\n]+)", body) or "v1.0"
        doi = extract_first(r"https://doi\.org/([^\)]+)", body)
        summary = extract_section(body, "Summary")
        claim_boundary = extract_section(body, "Claim Boundary")
        citation = extract_section(body, "Citation Guidance")
        if not pdf or not date:
            continue
        items.append(
            {
                "publication_type": data.get("type", "Research Paper"),
                "category_path": "research-papers",
                "title": data.get("title", ""),
                "subtitle": data.get("subtitle", ""),
                "slug": page.parent.name,
                "date": date,
                "version": version.strip(),
                "doi": doi,
                "website_url": f"{BASE_URL}{data.get('permalink', '')}",
                "source_page": str(page.relative_to(site_root)),
                "pdf_source": pdf,
                "abstract": summary,
                "summary": data.get("summary_short", ""),
                "claim_boundary": claim_boundary,
                "citation": citation,
                "status": data.get("status", "Published"),
                "verification_note": "See the linked website page for current verification and routing context.",
            }
        )
    return items


def collect_research_notes(site_root: Path) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for page in sorted((site_root / "_research_notes").glob("*.md")):
        text = read_text(page)
        data, body = parse_frontmatter(text)
        pdf = str(data.get("pdf_url") or data.get("pdf") or "")
        date = str(data.get("date", ""))
        slug = str(data.get("slug", "")) or slugify(str(data.get("title", "")))
        if not pdf or not date:
            continue
        items.append(
            {
                "publication_type": "Research Note",
                "category_path": "research-notes",
                "title": str(data.get("title", "")),
                "subtitle": str(data.get("subtitle", "")),
                "slug": slug,
                "date": date,
                "version": "v1.0",
                "doi": "",
                "website_url": f"{BASE_URL}{data.get('permalink', '')}",
                "source_page": str(page.relative_to(site_root)),
                "pdf_source": pdf,
                "abstract": str(data.get("abstract", "")),
                "summary": str(data.get("summary", data.get("summary_short", ""))),
                "claim_boundary": extract_claims_block(text) or "See the publication page and PDF for claim boundaries and falsification surfaces.",
                "citation": extract_nested_scalar(text, "editorial", "citation_note") or "Cite the PDF as the stable artifact; cite the website page for current status and routing.",
                "status": str(data.get("status", "Published")),
                "verification_note": extract_nested_scalar(text, "verification", "status") or "See the linked website page for current verification routes.",
            }
        )
    return items


def collect_public_good_briefings(site_root: Path) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    root = site_root / "publications" / "research-briefings" / "public-good"
    for page in sorted(root.glob("*/index.md")):
        data, _ = parse_frontmatter(read_text(page))
        if data.get("pdf_status") != "available":
            continue
        pdf = str(data.get("pdf_path", ""))
        date = str(data.get("date", ""))
        slug = str(data.get("slug", page.parent.name))
        items.append(
            {
                "publication_type": "Public-Good Briefing",
                "category_path": "research-briefings/public-good",
                "title": str(data.get("title", "")),
                "subtitle": str(data.get("subtitle", "")),
                "slug": slug,
                "date": date,
                "version": "v1.0",
                "doi": "",
                "website_url": f"{BASE_URL}{data.get('permalink', '')}",
                "source_page": str(page.relative_to(site_root)),
                "pdf_source": pdf,
                "abstract": str(data.get("abstract", data.get("summary", ""))),
                "summary": str(data.get("summary", "")),
                "claim_boundary": "Conditional public-good scenario briefing. It does not validate the framework, claim policy adoption, or replace domain expertise and external review.",
                "citation": "Cite the PDF as the stable briefing artifact; cite the website page for current status and routing.",
                "status": str(data.get("status", "published")),
                "verification_note": "Conditional on upstream results, verification survival, domain review, translation, and uptake.",
            }
        )
    return items


def extract_claims_block(text: str) -> str:
    core = extract_nested_scalar(text, "claims", "core")
    non_claims = extract_nested_list(text, "does_not_claim")
    falsification = extract_nested_list(text, "falsification_surface")
    parts: list[str] = []
    if core:
        parts.append(f"Core claim: {core}")
    if non_claims:
        parts.append("Does not claim:\n" + "\n".join(f"- {item}" for item in non_claims))
    if falsification:
        parts.append("Falsification surface:\n" + "\n".join(f"- {item}" for item in falsification))
    return "\n\n".join(parts)


def extract_nested_scalar(text: str, parent: str, key: str) -> str:
    raw = raw_frontmatter(text)
    pattern = rf"^{re.escape(parent)}:\n(?:  .+\n)*?  {re.escape(key)}:\s*(.+)$"
    match = re.search(pattern, raw, flags=re.MULTILINE)
    if not match:
        return ""
    return str(match.group(1)).strip().strip('"')


def extract_nested_list(text: str, key: str) -> list[str]:
    raw = raw_frontmatter(text)
    match = re.search(rf"^  {re.escape(key)}:\n((?:    - .+\n)+)", raw, flags=re.MULTILINE)
    if not match:
        return []
    return [line.strip()[2:].strip().strip('"') for line in match.group(1).splitlines() if line.strip().startswith("- ")]


def raw_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---", 4)
    return text[4:end].strip("\n") if end != -1 else ""


def render_readme(item: dict[str, str], pdf_name: str) -> str:
    doi_line = item["doi"] if item["doi"] else "Not assigned"
    return f"""# {item['title']}

{item['subtitle']}

## Metadata

- Type: {item['publication_type']}
- Authors: {AUTHORS}
- Date: {item['date']}
- Version: {item['version']}
- Status: {item['status']}
- DOI: {doi_line}
- Website: {item['website_url']}
- Source website page: `{item['source_page']}`
- PDF: `{pdf_name}`

## Abstract

{item['abstract'] or item['summary']}

## Claim Boundary

{item['claim_boundary']}

## Verification And Status Notes

{item['verification_note']}

## Citation Guidance

{item['citation']}

## Integrity

Cryptographic hashes and OpenTimestamps receipt status are recorded in `manifest.json`. The timestamp receipt proves the existence of the exact PDF bytes at or before the attested time; it does not certify correctness, peer review, legal status, DOI registration, or content validity.
"""


if __name__ == "__main__":
    raise SystemExit(main())
