# Corpus Governance Snapshots

The files under `catalog/corpus-governance/` and the root `errata.yml` are
generated public-safe snapshots from the private Corpus repository.

These snapshots help the Publications repository stay cloneable as an artifact
and provenance mirror. They do not make this repository the canonical source
for semantic corrections, Corpus Changelog entries, edition history, or release
history. Corpus owns the canonical semantic metadata; Publications owns
artifact bytes, manifests, checksums, and OpenTimestamps receipts.

## Current Snapshot Files

- `errata.yml`: public publication-facing errata mirror.
- `catalog/corpus-governance/errata.*`: JSON, YAML, CSV, and NDJSON errata exports.
- `catalog/corpus-governance/edition-history.*`: current and archival monograph edition metadata.
- `catalog/corpus-governance/release-history.*`: public-safe Corpus release-history metadata.
- `catalog/corpus-governance/release-artifacts.*`: public-safe generated release artifact inventory.

Regenerate these files from Corpus with:

```sh
python3 scripts/export_errata_for_publications_repo.py
```

Then copy the generated `exports/public/publications-repo/` snapshot into this
repository. Do not edit generated snapshot files by hand.
