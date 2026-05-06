# Publication Folder Conventions

Released artifacts currently use stable date-slug folders so existing checksummed PDFs and timestamp receipts remain byte-stable.

PRRP route IDs such as `rn001`, `rp001`, and `wp001` are recorded in `manifest.json`. Future path migrations may adopt route-ID folders, but this sprint does not rename existing artifacts.

Every released publication folder contains:

- `README.md`
- `manifest.json`
- one canonical PDF
- an OpenTimestamps receipt when stamped

Planned entries may contain only `README.md` and `manifest.json`.
