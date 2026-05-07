# Corpus Metadata Projection

This folder stores the public-safe publication metadata projection generated from the private `corpus` repository.

`corpus` owns canonical semantic publication metadata: publication IDs, titles, dates, route status, claim boundaries, DOI/ISBN/ASIN fields, artifact availability, and integrity references.

`publications` owns the released artifact mirror: PDFs, local manifests, checksums, OpenTimestamps receipts, and cloneable provenance folders.

The files in this folder are generated snapshots. Do not edit them by hand in this repository.

Refresh from a local Corpus checkout with:

```sh
CORPUS_EXPORTS_DIR=../corpus/exports/public python3 scripts/sync_corpus_metadata.py
python3 scripts/validate_corpus_metadata_projection.py
```

The projection records planned and external-link publication records as metadata, but checksum catalogs remain limited to PDF-bearing released or superseded artifacts.
