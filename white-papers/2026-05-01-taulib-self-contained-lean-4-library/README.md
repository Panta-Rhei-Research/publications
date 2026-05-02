# TauLib: A Self-Contained Lean 4 Library for Category τ

Kernel + Mathlib Bridges + Registry-Driven Correspondence

## Metadata

- Type: White Paper
- Authors: Thorsten Fuchs and Anna-Sophie Fuchs
- Date: 2026-05-01
- Version: v2.0 (full rewrite)
- Status: Distribution release
- DOI: 10.5281/zenodo.19976503
- Website: https://panta-rhei.site/publications/white-papers/taulib/
- Source website page: `publications/white-papers/taulib/index.md`
- PDF: `white-paper-2026-05-01-taulib-self-contained-lean-4-library.pdf`
- LaTeX source: [`Panta-Rhei-Research/papers @ whitepaper-taulib-v2.0`](https://github.com/Panta-Rhei-Research/papers/tree/whitepaper-taulib-v2.0/whitepapers/taulib)

The DOI resolves to <https://doi.org/10.5281/zenodo.19976503>.

## Abstract

TauLib is a public Lean 4 library that formalises Category τ — the categorical framework of the Panta Rhei Research Program — from seven structural axioms K0–K6 on five generators (α, π, γ, η, ω) and one operator (ρ).

This v2.0 whitepaper documents three structural changes since v1.0 (post-peer-review v3, April 2026):

1. **The kernel–bridges architecture is first-class.** The τ-kernel (Books I–VII outside `Bridge/` subdirectories) imports zero Mathlib mathematical content. Mathlib bridges live in a separately-typed orthogonal layer. CI enforces the boundary on every push.

2. **Book I foundations are substantially extended** along the eight *hinge papers* (kernel-foundation, iota-tau, hyperfactorization, prime-polarity, address-resolution, boundary-algebra, holomorphy-first, tau-topos) and one framing memo (bundle-memo) — all currently circulating as internal preprints, awaiting external preprint-server submission. Book I is now 157 files, 1,580 theorems and 720 definitions.

3. **Across all seven books TauLib carries 4,892 theorems, 3,762 definitions, 94 typeclass instances, exactly 3 conjectural axioms (all in Book III, all paired with finite-decidable witnesses), and zero `sorry`**. Each count is asserted by CI on every push; drift is a build break.

## Companion Artefacts

The v2.0 release ships three companion artefacts alongside the paper PDF:

- **Red-team consolidation memo** — review of the v2.0-rc1 draft by 7 simulated Lean 4 expert reviewers (de Moura, Ullrich, Carneiro, Massot, Avigad, Buzzard, van Doorn) with severity-classified findings; 6/7 qualified-yes verdict. Lives at `papers/whitepapers/taulib/RED_TEAM_FINDINGS.md` in the source repo.
- **Claims-map audit report** — auditor output from `verify_claims_map.py` showing 39/39 checks passed against the pinned TauLib commit `72aa2b6c7d6be28511f9649d3120773179b19038`. Lives at `papers/whitepapers/taulib/main_claims_audit.md` in the source repo.
- **Reproducible audit script** — `papers/whitepapers/taulib/scripts/verify_claims_map.py` (~280L, stdlib-only) for re-auditing the paper's numerical and theorem citations against any TauLib commit.

## Claim Boundary

The whitepaper presents the architecture, foundations, and case studies of the TauLib library at the v2.0 pinned TauLib commit. The structural derivation theorem for ι_τ remains in flight (Lean module currently ships fiat constants pending closure of the `ROADMAP-3-HINGES.md` Phase 0–4 sequence). The CMB ℓ_1 prediction is reported as a measurable tension (~1.3 σ above the central Planck value), not a clean confirmation. The three Book III conjectural axioms are paired with finite-decidable witness functions; their universal claims are open in mathematical practice, not Lean-proven.

## Verification And Status Notes

- TauLib pinned commit: `72aa2b6c7d6be28511f9649d3120773179b19038` (2026-05-01)
- Reproducible build: `lake build && python3 scripts/check_no_sorry.py --root TauLib --expected-axioms 3 --expected-sorry 0` exits 0
- Claims-map auditor: 39/39 checks passed at the pinned commit
- Red-team verdict: 6/7 simulated reviewers qualified-yes; 1/7 qualified-no contingent on substantive findings (all addressed in the published v2.0)

## Citation Guidance

Thorsten Fuchs and Anna-Sophie Fuchs, "TauLib: A Self-Contained Lean 4 Library for Category τ — Kernel + Mathlib Bridges + Registry-Driven Correspondence," v2.0, May 2026. DOI: [10.5281/zenodo.19976503](https://doi.org/10.5281/zenodo.19976503).

BibTeX:

```bibtex
@misc{Fuchs-TauLib-Whitepaper-v2-2026,
  author       = {Fuchs, Thorsten and Fuchs, Anna-Sophie},
  title        = {{TauLib}: A Self-Contained {Lean}~4 Library for {Category} $\tau$ ---
                  Kernel + Mathlib Bridges + Registry-Driven Correspondence},
  year         = {2026},
  month        = may,
  version      = {v2.0},
  doi          = {10.5281/zenodo.19976503},
  howpublished = {Panta Rhei Research; Zenodo deposit
                  \url{https://doi.org/10.5281/zenodo.19976503}}
}
```

## Integrity

Cryptographic hashes and OpenTimestamps receipt status are recorded in `manifest.json`. The timestamp receipt proves the existence of the exact PDF bytes at or before the attested time; it does not certify correctness, peer review, legal status, DOI registration, or content validity.
