#!/usr/bin/env python3
"""Sync public website publication artifacts into this repository."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from lib_publications import ROOT, SITE_ROOT, extract_first, extract_section, parse_frontmatter, read_text, slugify


AUTHORS = "Thorsten Fuchs and Anna-Sophie Fuchs"
BASE_URL = "https://panta-rhei.site"
REPORT = ROOT / "routes" / "site-sync-report.md"


@dataclass
class ImportItem:
    category_path: str
    folder_name: str
    title: str
    publication_type: str
    date: str
    version: str
    status: str
    website_url: str
    source_page: str
    artifact_availability: str
    pdf_source: str = ""
    subtitle: str = ""
    doi: str = ""
    abstract: str = ""
    claim_boundary: str = ""
    citation: str = ""
    verification_note: str = ""
    external_links: list[tuple[str, str]] = field(default_factory=list)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-root", type=Path, default=SITE_ROOT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    site_root = args.site_root.resolve()
    if not site_root.exists():
        raise SystemExit(f"Missing site root: {site_root}")

    items = collect_items(site_root)
    validate_expected_counts(items)
    for item in sorted(items, key=lambda entry: (entry.category_path, entry.folder_name)):
        target_dir = ROOT / item.category_path / item.folder_name
        pdf_source = site_root / item.pdf_source.lstrip("/") if item.pdf_source else None
        pdf_target = target_dir / pdf_source.name if pdf_source else None
        if pdf_source and not pdf_source.exists():
            raise SystemExit(f"Missing PDF source: {pdf_source}")
        print(f"{item.folder_name}: {item.pdf_source or 'external-link'} -> {target_dir.relative_to(ROOT)}")
        if args.dry_run:
            continue
        target_dir.mkdir(parents=True, exist_ok=True)
        if pdf_source and pdf_target:
            shutil.copy2(pdf_source, pdf_target)
        (target_dir / "README.md").write_text(render_readme(item, pdf_target.name if pdf_target else ""), encoding="utf-8")

    if not args.dry_run:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(render_sync_report(items), encoding="utf-8")
    return 0


def collect_items(site_root: Path) -> list[ImportItem]:
    return [
        *collect_research_papers(site_root),
        *collect_research_notes(site_root),
        *collect_public_good_dossiers(site_root),
        *collect_white_papers(site_root),
        *collect_monograph_supplements(site_root),
        *collect_synoptic_overviews(site_root),
        *collect_guided_tours(site_root),
        *collect_research_monographs(site_root),
    ]


def collect_research_papers(site_root: Path) -> list[ImportItem]:
    items: list[ImportItem] = []
    for page in sorted((site_root / "publications" / "research-papers").glob("*/index.md")):
        data, body = parse_frontmatter(read_text(page))
        pdf = first_pdf_link(body)
        date = extract_first(r"^- Publication date:\s*([0-9-]+)\s*$", body)
        version = extract_first(r"^- Version:\s*([^·\n]+)", body) or "v1.0"
        doi = extract_first(r"https://doi\.org/([^\)]+)", body)
        if not pdf or not date:
            continue
        slug = page.parent.name
        items.append(
            ImportItem(
                category_path="research-papers",
                folder_name=f"{date}-{slug}",
                title=str(data.get("title", "")),
                subtitle=str(data.get("subtitle", "")),
                publication_type=str(data.get("type", "Research Paper")),
                date=date,
                version=version.strip(),
                status=str(data.get("status", "Published")),
                website_url=f"{BASE_URL}{data.get('permalink', '')}",
                source_page=str(page.relative_to(site_root)),
                artifact_availability="local_pdf",
                pdf_source=pdf,
                doi=doi,
                abstract=extract_section(body, "Summary") or str(data.get("summary_short", "")),
                claim_boundary=extract_section(body, "Claim Boundary"),
                citation=extract_section(body, "Citation Guidance"),
                verification_note="See the linked website page for current verification and routing context.",
            )
        )
    return items


def collect_research_notes(site_root: Path) -> list[ImportItem]:
    items: list[ImportItem] = []
    for page in sorted((site_root / "_research_notes").glob("*.md")):
        text = read_text(page)
        data, _ = parse_frontmatter(text)
        pdf = str(data.get("pdf_url") or data.get("pdf") or "")
        date = str(data.get("date", ""))
        slug = str(data.get("slug", "")) or slugify(str(data.get("title", "")))
        if not pdf or not date:
            continue
        items.append(
            ImportItem(
                category_path="research-notes",
                folder_name=f"{date}-{slug}",
                title=str(data.get("title", "")),
                subtitle=str(data.get("subtitle", "")),
                publication_type="Research Note",
                date=date,
                version="v1.0",
                status=str(data.get("status", "Published")),
                website_url=f"{BASE_URL}{data.get('permalink', '')}",
                source_page=str(page.relative_to(site_root)),
                artifact_availability="local_pdf",
                pdf_source=pdf,
                abstract=str(data.get("abstract", data.get("summary", data.get("summary_short", "")))),
                claim_boundary=extract_claims_block(text) or "See the publication page and PDF for claim boundaries and falsification surfaces.",
                citation=extract_nested_scalar(text, "editorial", "citation_note") or "Cite the PDF as the stable artifact; cite the website page for current status and routing.",
                verification_note=extract_nested_scalar(text, "verification", "status") or "See the linked website page for current verification routes.",
            )
        )
    return items


def collect_public_good_dossiers(site_root: Path) -> list[ImportItem]:
    data_path = site_root / "_data" / "impact" / "public-good-briefings.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    items: list[ImportItem] = []
    for entry in sorted(data, key=lambda item: str(item.get("slug", ""))):
        pdf = str(entry.get("pdf_path", ""))
        if not pdf:
            continue
        slug = str(entry["slug"])
        date = str(entry.get("pdf_release_date", "2026-05-02"))
        items.append(
            ImportItem(
                category_path="research-briefings/public-good",
                folder_name=f"{date}-{slug}",
                title=str(entry.get("title", "")),
                subtitle=f"Public-Good Impact Dossier · {entry.get('portfolio_title', 'Public Good')}",
                publication_type="Public-Good Briefing",
                date=date,
                version=str(entry.get("source_version", "v1.0")),
                status="Published",
                website_url=f"{BASE_URL}{entry.get('landing_url', '')}",
                source_page=str(Path("site/_data/impact/public-good-briefings.json")),
                artifact_availability="local_pdf",
                pdf_source=pdf,
                abstract=str(entry.get("summary_short", "")),
                claim_boundary="Conditional public-good scenario briefing. It does not claim validation, policy adoption, deployment readiness, product performance, or independent domain acceptance.",
                citation="Cite the PDF as the stable dossier artifact; cite the website page for current status and routing.",
                verification_note="Conditional on upstream results, verification survival, domain review, translation, and uptake.",
            )
        )
    return items


def collect_white_papers(site_root: Path) -> list[ImportItem]:
    items: list[ImportItem] = []
    for page in sorted((site_root / "publications" / "white-papers").glob("*/index.md")):
        data, body = parse_frontmatter(read_text(page))
        pdf = first_pdf_link(body)
        if not pdf:
            continue
        date = extract_first(r"^- Publication date:\s*([0-9-]+)\s*$", body) or date_from_pdf(pdf)
        folder_slug = slug_from_pdf(pdf, "white-paper")
        version = extract_first(r"^- Version:\s*([^·\n]+)", body) or extract_first(r"Version:\s*\*\*([^*]+)\*\*", body) or "v1.0"
        items.append(
            ImportItem(
                category_path="white-papers",
                folder_name=f"{date}-{folder_slug}",
                title=str(data.get("title", "")),
                subtitle=str(data.get("subtitle", "")),
                publication_type="White Paper",
                date=date,
                version=version.strip(),
                status=str(data.get("status", "Published")),
                website_url=f"{BASE_URL}{data.get('permalink', '')}",
                source_page=str(page.relative_to(site_root)),
                artifact_availability="local_pdf",
                pdf_source=pdf,
                abstract=extract_section(body, "Abstract") or str(data.get("summary_short", "")),
                claim_boundary=extract_scope(body) or "White-paper orientation artifact. It routes readers to canonical Corpus, Results, Verify, and Publications surfaces and does not replace those surfaces.",
                citation=extract_section(body, "Citation") or "Cite the PDF as the stable artifact; cite the website page for current status and routing.",
                verification_note="See the linked website page and Release Manifest for current verification routes.",
            )
        )
    return items


def collect_monograph_supplements(site_root: Path) -> list[ImportItem]:
    specs = [
        ("ms001-numerical-physics-ledger", "numerical-physics-ledger.md", "Numerical Physics Ledger", "technical"),
        ("ms002-categorical-genesis", "categorical-genesis.md", "Categorical Genesis", "orientation"),
    ]
    items: list[ImportItem] = []
    for folder, filename, default_title, _role in specs:
        page = site_root / "publications" / "monograph-supplements" / filename
        data, body = parse_frontmatter(read_text(page))
        pdf = first_pdf_link(body)
        items.append(
            ImportItem(
                category_path="monograph-supplements",
                folder_name=folder,
                title=str(data.get("title", default_title)),
                subtitle=str(data.get("summary_short", "")),
                publication_type="Monograph Supplement",
                date="2026-04-30",
                version="Second Edition",
                status=str(data.get("status", "Canonical")),
                website_url=f"{BASE_URL}{data.get('permalink', '')}",
                source_page=str(page.relative_to(site_root)),
                artifact_availability="local_pdf",
                pdf_source=pdf,
                abstract=first_paragraph(body),
                claim_boundary=extract_section(body, "Status and scope") or "Monograph supplement artifact. It records program commitments or supplemental exposition without implying external acceptance.",
                citation="Cite the PDF as the stable monograph supplement artifact; cite the website page for current status and routing.",
                verification_note="See the linked Results and Verify surfaces for current status, falsification, and scope boundaries.",
            )
        )
    return items


def collect_synoptic_overviews(site_root: Path) -> list[ImportItem]:
    page = site_root / "publications" / "conspectus" / "index.md"
    data, body = parse_frontmatter(read_text(page))
    pdf = first_pdf_link(body)
    return [
        ImportItem(
            category_path="synoptic-overviews",
            folder_name="so001-panta-rhei-conspectus",
            title=str(data.get("title", "The Panta Rhei Conspectus")),
            subtitle=str(data.get("summary_short", "")),
            publication_type="Synoptic Overview",
            date="2026-04-21",
            version="v1.1",
            status="Published",
            website_url=f"{BASE_URL}{data.get('permalink', '')}",
            source_page=str(page.relative_to(site_root)),
            artifact_availability="local_pdf",
            pdf_source=pdf,
            abstract=first_paragraph(body),
            claim_boundary=extract_section(body, "Scope labels") or "Synoptic overview artifact. It summarizes the program and routes readers to canonical source surfaces.",
            citation=extract_section(body, "Citation"),
            verification_note="The Release Manifest is authoritative for current TauLib and release-state metrics.",
        )
    ]


def collect_guided_tours(site_root: Path) -> list[ImportItem]:
    page = site_root / "publications" / "guided-tours" / "index.md"
    _, body = parse_frontmatter(read_text(page))
    rows = [
        ("I", "gt001-guided-tour-book-i", "Book I Guided Tour", "guided-tour-book-I.pdf"),
        ("II", "gt002-guided-tour-book-ii", "Book II Guided Tour", "guided-tour-book-II.pdf"),
        ("III", "gt003-guided-tour-book-iii", "Book III Guided Tour", "guided-tour-book-III.pdf"),
        ("IV", "gt004-guided-tour-book-iv", "Book IV Guided Tour", "guided-tour-book-IV.pdf"),
        ("V", "gt005-guided-tour-book-v", "Book V Guided Tour", "guided-tour-book-V.pdf"),
        ("VI", "gt006-guided-tour-book-vi", "Book VI Guided Tour", "guided-tour-book-VI.pdf"),
        ("VII", "gt007-guided-tour-book-vii", "Book VII Guided Tour", "guided-tour-book-VII.pdf"),
    ]
    items = []
    for roman, folder, title, pdf in rows:
        items.append(
            ImportItem(
                category_path="guided-tours",
                folder_name=folder,
                title=title,
                subtitle=f"Structural falsification guide and Lean verification companion for Book {roman}.",
                publication_type="Guided Tour",
                date="2026-04-15",
                version="v1.0",
                status="Published",
                website_url=f"{BASE_URL}/publications/guided-tours/",
                source_page=str(page.relative_to(site_root)),
                artifact_availability="local_pdf",
                pdf_source=f"/assets/media/{pdf}",
                abstract="Guided Tours are controlled entry points into the load-bearing parts of the program, identifying hinges, attack vectors, and verification routes.",
                claim_boundary="Guided tour artifact. It helps readers inspect and challenge the books; it does not replace the monographs, Registry, TauLib, Results, or external review.",
                citation=f"Cite this guided-tour PDF as the Book {roman} inspection companion; cite the website page for current routing.",
                verification_note="Follow the linked TauLib modules and Verify lane for current formalization and inspection status.",
            )
        )
    return items


def collect_research_monographs(site_root: Path) -> list[ImportItem]:
    books = json.loads((site_root / "_data" / "publications" / "books.json").read_text(encoding="utf-8"))
    amazon = {item["slug"]: item for item in json.loads((site_root / "_data" / "publications" / "amazon.json").read_text(encoding="utf-8"))}
    items = []
    for book in books:
        slug = str(book["id"])
        amz = amazon.get(slug, {})
        links = []
        for label, key in [
            ("Amazon.com ebook", "ebook_url_amazon_com"),
            ("Amazon.com paperback", "paperback_url_amazon_com"),
            ("Amazon.com hardcover", "hardcover_url_amazon_com"),
            ("Amazon.de ebook", "ebook_url_amazon_de"),
            ("Amazon.de paperback", "paperback_url_amazon_de"),
            ("Amazon.de hardcover", "hardcover_url_amazon_de"),
        ]:
            if amz.get(key):
                links.append((label, str(amz[key])))
        items.append(
            ImportItem(
                category_path="research-monographs",
                folder_name=slug,
                title=f"Book {book['roman']}: {book['title']}",
                subtitle=str(book.get("subtitle", "")),
                publication_type="Research Monograph",
                date="2026-04-30",
                version="Second Edition",
                status="Published",
                website_url=f"{BASE_URL}{book.get('url', f'/publications/books/{slug}/')}",
                source_page=f"site/_data/publications/books.json + site/_data/publications/amazon.json",
                artifact_availability="external_link",
                abstract=f"{book['title']} is the Book {book['roman']} monograph of the Panta Rhei Second Edition series: {book.get('pages')} pages, {book.get('parts')} parts, {book.get('chapters')} chapters.",
                claim_boundary="Research monograph retail artifact. This repository records metadata and external availability links only; it does not redistribute the paid manuscript PDF or replace Amazon KDP publication terms.",
                citation="Cite the monograph by title, authors, edition, format, and Amazon ASIN/ISBN where applicable; cite the website page for current routing.",
                verification_note="Use the Corpus monograph projection, Registry, and Verify lane for inspectable source, formalization, and status surfaces.",
                external_links=links,
            )
        )
    return items


def validate_expected_counts(items: list[ImportItem]) -> None:
    pdf_count = sum(1 for item in items if item.artifact_availability == "local_pdf")
    external_count = sum(1 for item in items if item.artifact_availability == "external_link")
    if pdf_count != 74 or external_count != 7:
        raise SystemExit(f"Unexpected sync counts: {pdf_count} PDFs and {external_count} external records")


def render_readme(item: ImportItem, pdf_name: str) -> str:
    doi_line = item.doi if item.doi else "Not assigned"
    pdf_line = pdf_name if pdf_name else "Not included in this repository"
    source_asset = f"site/{item.pdf_source.lstrip('/')}" if item.pdf_source else "null"
    external_links = ""
    if item.external_links:
        external_links = "\n## External Links\n\n" + "\n".join(f"- [{label}]({url})" for label, url in item.external_links) + "\n"
    return f"""# {item.title}

{item.subtitle}

## Metadata

- Type: {item.publication_type}
- Authors: {AUTHORS}
- Date: {item.date}
- Version: {item.version}
- Status: {item.status}
- Artifact availability: {item.artifact_availability}
- DOI: {doi_line}
- Website: {item.website_url}
- Source website page: `{item.source_page}`
- Source website asset path: `{source_asset}`
- PDF: `{pdf_line}`

## Abstract

{item.abstract}

## Claim Boundary

{item.claim_boundary}

## Verification And Status Notes

{item.verification_note}

## Citation Guidance

{item.citation}
{external_links}
## Integrity

Cryptographic hashes and OpenTimestamps receipt status are recorded in `manifest.json` for local PDFs. For external-link records, `manifest.json` records route and availability metadata only. Timestamp receipts prove existence of exact PDF bytes at or before the attested time; they do not certify correctness, peer review, legal status, DOI registration, or content validity.
"""


def render_sync_report(items: list[ImportItem]) -> str:
    by_category: dict[str, list[ImportItem]] = {}
    for item in items:
        by_category.setdefault(item.category_path, []).append(item)
    lines = [
        "# Website Publication Sync Report",
        "",
        "Generated from the public website publication surfaces in the sibling `site` repository.",
        "",
        f"- Website-linked PDFs represented by this sync: {sum(1 for item in items if item.artifact_availability == 'local_pdf')}",
        f"- External-link monograph records represented by this sync: {sum(1 for item in items if item.artifact_availability == 'external_link')}",
        "- Existing historical/superseded repository records are preserved outside this sync count.",
        "",
        "| Category | Records | Local PDFs | External links |",
        "|---|---:|---:|---:|",
    ]
    for category in sorted(by_category):
        records = by_category[category]
        lines.append(
            f"| `{category}` | {len(records)} | {sum(1 for item in records if item.artifact_availability == 'local_pdf')} | {sum(1 for item in records if item.artifact_availability == 'external_link')} |"
        )
    lines.append("")
    lines.append("Archived First Edition book records and full part/chapter route stubs are intentionally deferred.")
    lines.append("")
    return "\n".join(lines)


def first_pdf_link(body: str) -> str:
    return extract_first(r"\{\{\s*'([^']+\.pdf)'\s*\|\s*relative_url\s*\}\}", body) or extract_first(r"(\/assets\/[^\s\)'\"]+\.pdf)", body)


def date_from_pdf(path: str) -> str:
    match = re.search(r"(20\d{2}-\d{2}-\d{2})", path)
    return match.group(1) if match else "2026-04-30"


def slug_from_pdf(path: str, prefix: str) -> str:
    name = Path(path).name.removesuffix(".pdf")
    match = re.match(rf"{re.escape(prefix)}-(20\d{{2}}-\d{{2}}-\d{{2}})-(.+)$", name)
    if match:
        return match.group(2)
    return slugify(name)


def first_paragraph(body: str) -> str:
    stripped = re.sub(r"<[^>]+>", "", body)
    for paragraph in re.split(r"\n\s*\n", stripped):
        clean = paragraph.strip()
        if clean and not clean.startswith("{%") and not clean.startswith("##") and not clean.startswith("|"):
            return clean
    return ""


def extract_scope(body: str) -> str:
    return extract_section(body, "Scope and disclosure") or extract_section(body, "Status")


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


if __name__ == "__main__":
    raise SystemExit(main())
