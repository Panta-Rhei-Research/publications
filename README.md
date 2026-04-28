# Publications

This repository is the public home for **open-access publication artefacts and source files** of the **Panta Rhei Research Program**.

## What lives here

- `research-papers/` - standalone public research papers and technical memos
- `research-notes/` - dated scholarly notes, response notes, pre-registrations, and verification notes
- `research-briefings/` - public-facing briefings, including Public-Good Briefings
- `research-monographs/`, `white-papers/`, `release-artifacts/`, and `errata/` - scaffolded public categories for later release waves
- `catalog/` - generated checksums and machine-readable publication inventory

Each seeded publication folder contains the PDF, a human-readable `README.md`, a machine-readable `manifest.json`, and, once stamped, an OpenTimestamps receipt for the exact PDF bytes.

## Editorial standard

`publications` is a release-grade surface. Material here should be citable, auditable, and ready for public inspection.

## Integrity model

Publication PDFs are tracked with SHA-256 and SHA-512 hashes. OpenTimestamps receipts provide proof that the exact PDF bytes existed at or before the attested time.

This integrity layer does **not** certify correctness, peer review, legal status, DOI registration, external acceptance, or content validity. It is a byte-level provenance and timestamp layer.

Generated files can be refreshed with:

```sh
python3 scripts/build_manifests.py
python3 scripts/verify_publications.py
```

OpenTimestamps receipts are created and upgraded by GitHub Actions on trusted `main` events and manual dispatches.

## Where to go next

- Website: https://panta-rhei.site
- TauLib: https://github.com/Panta-Rhei-Research/taulib
- Research: https://github.com/Panta-Rhei-Research/research
- Community: https://github.com/Panta-Rhei-Research/community

## Contributions

Improvements to released public artefacts are welcome when they are tightly scoped and evidence-based.

Good contributions here include:

- typo fixes and copy corrections
- source improvements for released public documents
- errata clarifications
- build and packaging improvements for public artefacts
