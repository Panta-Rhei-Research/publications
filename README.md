# Publications

This repository is the public artifact and release layer of the **Panta Rhei Research Program**.

The Panta Rhei Research Program is an independent open research program dedicated to building a coherent theory of reality.

This repository holds release-grade publication artifacts: research monographs, research papers, research notes, briefings, white papers, ledgers, release artifacts, and errata.

## 🧩 Role in the Public Research System

Publications is not the primary construction body. That role belongs to the Corpus.

Publications is the stable artifact layer connected to:

- **Program** — doctrine and inspection-observatory rationale;
- **Agenda** — obligations and source policies (Structural Challenge Ledger, Core Semantics & Recovery, Kernel/Model/Reality, Construction Roadmap);
- **Corpus** — construction body and registry/TauLib projections;
- **Results** — current program stances and world readouts (Landmark Results, World Readouts, Challenge Responses, Core Semantics & Recovery Status);
- **Verify** — formalization, falsification, release manifest, and assessment protocols.

## 📖 What Lives Here

- `research-papers/` - standalone public research papers and technical memos
- `research-notes/` - dated scholarly notes, response notes, pre-registrations, and verification notes
- `research-briefings/` - public-facing briefings, including Public-Good Briefings
- `white-papers/` - citable explanatory artifacts, including the inspection architecture, theory-of-reality, and public research observatory press packages
- `research-monographs/`, `release-artifacts/`, and `errata/` - scaffolded public categories for later release waves
- `catalog/` - generated checksums and machine-readable publication inventory

Each seeded publication folder contains the PDF, a human-readable `README.md`, a machine-readable `manifest.json`, and, once stamped, an OpenTimestamps receipt for the exact PDF bytes.

## Editorial standard

`publications` is a release-grade surface. Material here should be citable, auditable, and ready for public inspection.

## 🪞 Integrity Model

Publication PDFs are tracked with SHA-256 and SHA-512 hashes. OpenTimestamps receipts provide proof that the exact PDF bytes existed at or before the attested time.

This integrity layer does **not** certify correctness, peer review, legal status, DOI registration, external acceptance, or content validity. It is a byte-level provenance and timestamp layer.

Publication integrity is byte-level provenance, not scientific validation.

Generated files can be refreshed with:

```sh
python3 scripts/build_manifests.py
python3 scripts/verify_publications.py
```

OpenTimestamps receipts are created and upgraded by GitHub Actions on trusted `main` events and manual dispatches.

## 🎯 Where to Go Next

- 🌐 **Website:** https://panta-rhei.site
- 🧭 **Agenda:** https://panta-rhei.site/agenda/
- 📚 **Corpus:** https://panta-rhei.site/corpus/
- 🔭 **Results:** https://panta-rhei.site/results/
- 🪞 **Verify:** https://panta-rhei.site/verify/
- 🚀 **Release Manifest:** https://panta-rhei.site/verify/release-manifest/
- 🔬 **TauLib:** https://github.com/Panta-Rhei-Research/taulib
- 📓 **Research:** https://github.com/Panta-Rhei-Research/research
- 💬 **Community:** https://github.com/Panta-Rhei-Research/community
- 💬 **Public discussions:** https://github.com/orgs/Panta-Rhei-Research/discussions

## 📐 Engagement Without Endorsement

We do not ask first for agreement.

We ask for structured open-research engagement: careful reading, public questions, critique, reproducibility checks, domain review, correction, infrastructure contribution, and responsible communication.

Participation does not imply endorsement of the framework. A reader may ask a question without accepting the theory. A reviewer may challenge a result without joining the program. A contributor may improve documentation, metadata, tooling, packaging, or formalization without endorsing any conclusion.

## 🪞 Verification Note

Artifacts and repository integrity checks make parts of the program inspectable. They do not by themselves establish empirical truth, bridge adequacy, semantic correspondence, peer review, or external scientific acceptance.

For current release metrics and verification boundaries, see the [Release Manifest](https://panta-rhei.site/verify/release-manifest/).

## 🔁 Contributions

Improvements to released public artifacts are welcome when they are tightly scoped and evidence-based.

Good contributions here include:

- typo fixes and copy corrections
- source improvements for released public documents
- errata clarifications
- build and packaging improvements for public artifacts
