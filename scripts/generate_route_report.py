#!/usr/bin/env python3
"""Generate and validate the public PRRP route manifest/report."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from lib_publications import ROOT, ROUTES_DIR, iter_publication_dirs, load_manifest, to_simple_yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if route outputs are stale.")
    args = parser.parse_args()

    manifests = [load_manifest(path / "manifest.json") for path in iter_publication_dirs()]
    routes = build_routes(manifests)
    route_manifest = {
        "schema": "panta-rhei-prrp-routes-public-v1",
        "route_count": len(routes),
        "routes": routes,
    }
    report = render_report(routes)

    changed = []
    changed.extend(write_or_check(ROUTES_DIR / "prrp-routes.public.yml", to_simple_yaml(route_manifest) + "\n", args.check))
    changed.extend(write_or_check(ROUTES_DIR / "route-report.md", report, args.check))
    if args.check and changed:
        for path in changed:
            print(f"stale: {path.relative_to(ROOT)}")
        return 1
    print(f"Generated route report for {len(routes)} routes.")
    return 0


def build_routes(manifests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    routes = []
    seen: set[str] = set()
    for manifest in sorted(manifests, key=lambda item: str(item.get("publication_id", ""))):
        publication = manifest.get("publication", {})
        short_url = publication.get("short_url", "")
        if not short_url:
            continue
        route_id = manifest.get("publication_id")
        if route_id in seen:
            raise SystemExit(f"Duplicate route ID: {route_id}")
        seen.add(str(route_id))
        routes.append(
            {
                "route_id": route_id,
                "short_url": short_url,
                "route_status": publication.get("route_status", "not_applicable"),
                "publication_key": manifest.get("publication_key"),
                "type": manifest.get("type"),
                "publication_role": manifest.get("publication_role"),
                "publication_status": manifest.get("status"),
                "title": publication.get("title"),
                "canonical_url": publication.get("canonical_url", ""),
                "github_path": publication.get("github_path", ""),
            }
        )
    return routes


def render_report(routes: list[dict[str, Any]]) -> str:
    active = sum(1 for route in routes if route["route_status"] == "active")
    reserved = sum(1 for route in routes if route["route_status"] == "reserved")
    lines = [
        "# PRRP Public Route Report",
        "",
        "This report is generated from publication manifests. The PRRP routes listed here are typed observatory identifiers, not generic short links.",
        "",
        f"- Total routes: {len(routes)}",
        f"- Active routes: {active}",
        f"- Reserved routes: {reserved}",
        "",
        "| Route | Status | Type | Publication | Canonical URL |",
        "|---|---|---|---|---|",
    ]
    for route in routes:
        canonical = route["canonical_url"] or "planned"
        lines.append(f"| `{route['route_id']}` | {route['route_status']} | {route['type']} | {route['title']} | {canonical} |")
    lines.append("")
    return "\n".join(lines)


def write_or_check(path: Path, rendered: str, check: bool) -> list[Path]:
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != rendered:
            return [path]
        return []
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return []


if __name__ == "__main__":
    raise SystemExit(main())
