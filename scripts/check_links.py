#!/usr/bin/env python3
"""Check publication URL shapes and optionally live HTTP reachability."""

from __future__ import annotations

import argparse
import urllib.error
import urllib.request

from lib_publications import iter_publication_dirs, load_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline-short-routes", action="store_true", help="Validate prrp.site route shapes without fetching them.")
    parser.add_argument("--live", action="store_true", help="Fetch canonical and DOI URLs.")
    args = parser.parse_args()

    errors: list[str] = []
    for item_dir in iter_publication_dirs():
        manifest = load_manifest(item_dir / "manifest.json")
        pub = manifest.get("publication", {})
        canonical = pub.get("canonical_url", "")
        short = pub.get("short_url", "")
        doi_url = pub.get("doi_url", "")
        if manifest.get("status") == "released" and not canonical.startswith("https://panta-rhei.site/"):
            errors.append(f"{manifest['id']}: invalid canonical URL")
        if short and not short.startswith("https://prrp.site/"):
            errors.append(f"{manifest['id']}: invalid short URL")
        if args.live:
            for url in [canonical, doi_url]:
                if url:
                    errors.extend(fetch(url, manifest["id"]))
        if args.live and short and not args.offline_short_routes:
            errors.extend(fetch(short, manifest["id"]))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Publication link checks passed.")
    return 0


def fetch(url: str, publication_id: str) -> list[str]:
    request = urllib.request.Request(url, headers={"User-Agent": "Panta-Rhei-Publications-Link-Check/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status >= 400:
                return [f"{publication_id}: {url} returned HTTP {response.status}"]
    except (urllib.error.URLError, TimeoutError) as error:
        return [f"{publication_id}: {url} failed: {error}"]
    return []


if __name__ == "__main__":
    raise SystemExit(main())
