#!/usr/bin/env python3
"""Shared helpers for publication artifact scripts."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = ROOT.parent / "site"
PUBLICATION_ROOTS = (
    ROOT / "research-papers",
    ROOT / "research-notes",
    ROOT / "research-briefings" / "public-good",
    ROOT / "white-papers",
)
CATALOG_DIR = ROOT / "catalog"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip("\n")
    body = text[end + 4 :].lstrip("\n")
    data: dict[str, Any] = {}
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#") or line.startswith(" "):
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            items: list[str] = []
            j = i + 1
            while j < len(lines) and lines[j].startswith("  - "):
                items.append(clean_scalar(lines[j][4:].strip()))
                j += 1
            if items:
                data[key] = items
                i = j
                continue
            data[key] = ""
        else:
            data[key] = clean_scalar(value)
        i += 1
    return data, body


def clean_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    if value in {"true", "false"}:
        return value == "true"
    return value


def slugify(value: str) -> str:
    value = value.lower()
    value = value.replace("τ", "tau").replace("ι", "iota")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def extract_section(body: str, heading: str) -> str:
    pattern = rf"^## {re.escape(heading)}\s*$"
    match = re.search(pattern, body, flags=re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r"^##\s+", body[start:], flags=re.MULTILINE)
    end = start + next_match.start() if next_match else len(body)
    section = body[start:end].strip()
    return re.sub(r"\n{3,}", "\n\n", section)


def extract_first(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def hash_file(path: Path) -> dict[str, str | int]:
    sha256 = hashlib.sha256()
    sha512 = hashlib.sha512()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(chunk)
            sha256.update(chunk)
            sha512.update(chunk)
    return {
        "bytes": size,
        "sha256": sha256.hexdigest(),
        "sha512": sha512.hexdigest(),
    }


def iter_publication_dirs() -> list[Path]:
    dirs: list[Path] = []
    for root in PUBLICATION_ROOTS:
        if not root.exists():
            continue
        for child in sorted(root.iterdir()):
            if child.is_dir() and re.match(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+$", child.name):
                dirs.append(child)
    return dirs


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(data), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
