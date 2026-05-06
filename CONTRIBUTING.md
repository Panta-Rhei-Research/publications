# Contributing

This repository accepts tightly scoped improvements to released public publication artifacts and their metadata.

Good contributions include:

- metadata corrections;
- broken-link fixes;
- typo/copy corrections;
- manifest, checksum, route, and catalog tooling improvements;
- errata clarifications;
- packaging improvements for released public artifacts.

Broad theory debate belongs in Organization Discussions, not repository issues. Issues here should identify concrete defects in a released artifact, metadata record, route, checksum, timestamp receipt, or repository workflow.

Before opening a pull request, run:

```sh
python3 scripts/build_manifests.py --check
python3 scripts/verify_publications.py
python3 scripts/validate_manifest.py
python3 scripts/build_catalog.py --check
python3 scripts/generate_route_report.py --check
python3 scripts/check_links.py --offline-short-routes
git diff --check
```
