# White Papers

Distribution-grade explanatory artefacts of the Panta Rhei Research Program.

White Papers clarify framework structure, formalisation work, infrastructure, methodology, or verification context. They are stable citable artefacts in the publications layer; released records carry either a Zenodo DOI or an explicit DOI-forthcoming status plus a reproducible build path.

## Index

- [`2026-05-01-taulib-self-contained-lean-4-library/`](2026-05-01-taulib-self-contained-lean-4-library/) — *TauLib: A Self-Contained Lean 4 Library for Category τ — Kernel + Mathlib Bridges + Registry-Driven Correspondence*. Authors: Thorsten Fuchs and Anna-Sophie Fuchs. v2.0 (2026-05-01). DOI: [10.5281/zenodo.19976503](https://doi.org/10.5281/zenodo.19976503).
- [`2026-05-03-inspection-architecture-high-scope-open-research/`](2026-05-03-inspection-architecture-high-scope-open-research/) — *Inspection Architecture for High-Scope Open Research — A practical blueprint for publishing ambitious independent research before asking for belief*. Authors: Thorsten Fuchs and Anna-Sophie Fuchs. v0.1 (2026-05-03). DOI forthcoming.

## Conventions

Each white paper directory follows the program's standard publication layout:

- `<type>-<date>-<slug>.pdf` — the canonical PDF
- `<type>-<date>-<slug>.pdf.ots` — OpenTimestamps receipt (CI-stamped after merge)
- `README.md` — human-readable abstract + metadata + citation guidance
- `manifest.json` — machine-readable manifest in the `panta-rhei-publication-manifest-v1` schema

The catalog scripts (`scripts/build_manifests.py`, `scripts/verify_publications.py`) treat `white-papers/` as a first-class publication root alongside `research-papers/`, `research-notes/`, and `research-briefings/public-good/`.

## See also

- White Papers website lane: <https://panta-rhei.site/publications/white-papers/>
- Source LaTeX repository: <https://github.com/Panta-Rhei-Research/papers/tree/main/whitepapers>
