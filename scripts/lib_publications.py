#!/usr/bin/env python3
"""Shared helpers for publication artifact scripts."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = Path(os.environ.get("PANTA_RHEI_SITE_ROOT", ROOT.parent / "site"))
PUBLICATION_ROOTS = (
    ROOT / "research-papers",
    ROOT / "research-notes",
    ROOT / "research-briefings" / "public-good",
    ROOT / "anchor-documents",
    ROOT / "white-papers",
    ROOT / "monograph-supplements",
    ROOT / "synoptic-overviews",
    ROOT / "guided-tours",
    ROOT / "research-monographs",
    ROOT / "charter-essays",
)
CATALOG_DIR = ROOT / "catalog"
ROUTES_DIR = ROOT / "routes"

ALLOWED_TYPES = {
    "research_note",
    "research_paper",
    "research_briefing",
    "public_good_briefing",
    "white_paper",
    "charter_essay",
    "research_monograph",
    "monograph_supplement",
    "synoptic_overview",
    "guided_tour",
    "media_brief",
    "verification_manifest",
    "release_record",
    "erratum",
}

ALLOWED_ROLES = {
    "orientation",
    "dialogue",
    "technical",
    "verification",
    "translation",
    "governance",
    "correction",
}

ALLOWED_STATUS = {"released", "planned", "superseded", "withdrawn"}
ALLOWED_ROUTE_STATUS = {"active", "reserved", "planned", "not_applicable"}
ALLOWED_ARTIFACT_AVAILABILITY = {"local_pdf", "external_link", "planned"}

PUBLICATION_REGISTRY: dict[str, dict[str, Any]] = {
    "2026-04-27-semantic-space-has-a-shape": {
        "publication_id": "rn001",
        "publication_key": "research_notes.semantic_space_has_a_shape",
        "type": "research_note",
        "publication_role": "dialogue",
        "short_url": "https://prrp.site/rn001",
        "route_status": "reserved",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "results", "verify"],
        "related_routes": ["/publications/research-notes/semantic-space-has-a-shape/"],
    },
    "2026-04-25-structural-prior-dynamic-chirality-induced-spin-selectivity": {
        "publication_id": "rn002",
        "publication_key": "research_notes.structural_prior_dynamic_ciss",
        "type": "research_note",
        "publication_role": "dialogue",
        "short_url": "https://prrp.site/rn002",
        "route_status": "reserved",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "impact", "verify"],
        "related_routes": ["/publications/research-notes/structural-prior-dynamic-chirality-induced-spin-selectivity/"],
    },
    "2026-04-25-inflationary-observables-without-an-inflaton": {
        "publication_id": "rn003",
        "publication_key": "research_notes.inflationary_observables_without_inflaton",
        "type": "research_note",
        "publication_role": "dialogue",
        "short_url": "https://prrp.site/rn003",
        "route_status": "reserved",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "results", "verify"],
        "related_routes": ["/publications/research-notes/inflationary-observables-without-an-inflaton/"],
    },
    "2026-04-25-dark-matter-without-dark-matter-ksz-force-law": {
        "publication_id": "rn004",
        "publication_key": "research_notes.dark_matter_mond_category_tau",
        "type": "research_note",
        "publication_role": "dialogue",
        "short_url": "https://prrp.site/rn004",
        "route_status": "reserved",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "results", "verify"],
        "related_routes": ["/publications/research-notes/dark-matter-without-dark-matter-ksz-force-law/"],
    },
    "2026-04-25-black-holes-without-extra-dimensions": {
        "publication_id": "rn005",
        "publication_key": "research_notes.black_hole_stability_without_extra_dimensions",
        "type": "research_note",
        "publication_role": "dialogue",
        "short_url": "https://prrp.site/rn005",
        "route_status": "reserved",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "results", "verify"],
        "related_routes": ["/publications/research-notes/black-holes-without-extra-dimensions/"],
    },
    "2026-04-25-arithmetic-quantum-gravity-without-singularities": {
        "publication_id": "rn006",
        "publication_key": "research_notes.arithmetic_quantum_gravity_without_singularities",
        "type": "research_note",
        "publication_role": "dialogue",
        "short_url": "https://prrp.site/rn006",
        "route_status": "reserved",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "results", "verify"],
        "related_routes": ["/publications/research-notes/arithmetic-quantum-gravity-without-singularities/"],
    },
    "2026-05-15-aesthetic-topology-pre-symbolic-readout": {
        "publication_id": "rn007",
        "publication_key": "research_notes.aesthetic_topology_pre_symbolic_readout",
        "type": "research_note",
        "publication_role": "dialogue",
        "short_url": "https://prrp.site/rn007",
        "route_status": "reserved",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "corpus", "verify"],
        "related_routes": ["/publications/research-notes/aesthetic-topology-pre-symbolic-readout/"],
    },
    "2026-04-27-hyperfactorization-theorem": {
        "publication_id": "rp001",
        "publication_key": "research_papers.hyperfactorization_theorem",
        "type": "research_paper",
        "publication_role": "technical",
        "short_url": "https://prrp.site/rp001",
        "route_status": "reserved",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "corpus", "verify"],
        "related_routes": ["/publications/research-papers/hyperfactorization-theorem/"],
    },
    "2026-04-27-prime-polarity-theorem": {
        "publication_id": "rp002",
        "publication_key": "research_papers.prime_polarity_theorem",
        "type": "research_paper",
        "publication_role": "technical",
        "short_url": "https://prrp.site/rp002",
        "route_status": "reserved",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "corpus", "verify"],
        "related_routes": ["/publications/research-papers/prime-polarity-theorem/"],
    },
    "2026-04-27-master-constant-iota-tau": {
        "publication_id": "rp003",
        "publication_key": "research_papers.master_constant_iota_tau",
        "type": "research_paper",
        "publication_role": "technical",
        "short_url": "https://prrp.site/rp003",
        "route_status": "reserved",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "corpus", "verify"],
        "related_routes": ["/publications/research-papers/master-constant-iota-tau/"],
    },
    "2026-04-27-split-complex-boundary-algebra": {
        "publication_id": "rp004",
        "publication_key": "research_papers.split_complex_boundary_algebra_d",
        "type": "research_paper",
        "publication_role": "technical",
        "short_url": "https://prrp.site/rp004",
        "route_status": "reserved",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "corpus", "verify"],
        "related_routes": ["/publications/research-papers/split-complex-boundary-algebra/"],
    },
    "2026-04-27-tau-holomorphy-boundary-algebra": {
        "publication_id": "rp005",
        "publication_key": "research_papers.tau_holomorphy_boundary_algebra",
        "type": "research_paper",
        "publication_role": "technical",
        "short_url": "https://prrp.site/rp005",
        "route_status": "reserved",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "corpus", "verify"],
        "related_routes": ["/publications/research-papers/tau-holomorphy-boundary-algebra/"],
    },
    "2026-04-27-tau-topos-four-valued-internal-logic": {
        "publication_id": "rp006",
        "publication_key": "research_papers.tau_topos_four_valued_internal_logic",
        "type": "research_paper",
        "publication_role": "technical",
        "short_url": "https://prrp.site/rp006",
        "route_status": "reserved",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "corpus", "verify"],
        "related_routes": ["/publications/research-papers/tau-topos-four-valued-internal-logic/"],
    },
    "2026-04-27-address-resolution-not-calculation": {
        "publication_id": "rp007",
        "publication_key": "research_papers.address_resolution_not_calculation",
        "type": "research_paper",
        "publication_role": "technical",
        "short_url": "https://prrp.site/rp007",
        "route_status": "reserved",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "corpus", "verify"],
        "related_routes": ["/publications/research-papers/address-resolution-not-calculation/"],
    },
    "2026-04-27-tau-kernel-foundational-architecture": {
        "publication_id": "rp008",
        "publication_key": "research_papers.tau_kernel_foundational_architecture",
        "type": "research_paper",
        "publication_role": "technical",
        "short_url": "https://prrp.site/rp008",
        "route_status": "reserved",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "corpus", "verify"],
        "related_routes": ["/publications/research-papers/tau-kernel-foundational-architecture/"],
    },
    "2026-04-27-panta-rhei-foundational-bundle": {
        "publication_id": "rp009",
        "publication_key": "research_papers.panta_rhei_foundational_bundle",
        "type": "research_paper",
        "publication_role": "orientation",
        "short_url": "https://prrp.site/rp009",
        "route_status": "reserved",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "corpus", "verify"],
        "related_routes": ["/publications/research-papers/panta-rhei-foundational-bundle/"],
    },
    "2026-04-26-advanced-fission-safety-operations-licensing-fleet-modernization": {
        "publication_id": "pgb001",
        "publication_key": "public_good_briefings.advanced_fission_safety_operations_licensing_fleet_modernization",
        "type": "public_good_briefing",
        "publication_role": "translation",
        "status": "superseded",
        "short_url": "https://prrp.site/pgb001",
        "route_status": "reserved",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "impact", "verify"],
        "related_routes": ["/publications/research-briefings/public-good/advanced-fission-safety-operations-licensing-fleet-modernization/"],
    },
    "2026-05-01-taulib-self-contained-lean-4-library": {
        "publication_id": "lwp001",
        "publication_key": "legacy_white_papers.taulib_self_contained_lean4_library",
        "type": "white_paper",
        "publication_role": "technical",
        "status": "superseded",
        "short_url": "",
        "route_status": "not_applicable",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "verify", "corpus"],
        "related_routes": ["/publications/white-papers/taulib/"],
    },
    "2026-05-03-building-a-public-research-observatory": {
        "publication_id": "lwp002",
        "publication_key": "legacy_white_papers.building_public_research_observatory",
        "type": "white_paper",
        "publication_role": "orientation",
        "status": "superseded",
        "short_url": "",
        "route_status": "not_applicable",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "engage", "verify"],
        "related_routes": ["/publications/white-papers/building-a-public-research-observatory/"],
    },
    "2026-05-03-inspection-architecture-high-scope-open-research": {
        "publication_id": "lwp003",
        "publication_key": "legacy_white_papers.inspection_architecture_high_scope_open_research",
        "type": "white_paper",
        "publication_role": "orientation",
        "status": "superseded",
        "short_url": "",
        "route_status": "not_applicable",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "engage", "verify"],
        "related_routes": ["/publications/white-papers/inspection-architecture-high-scope-open-research/"],
    },
    "2026-05-03-the-shape-of-a-theory-of-reality": {
        "publication_id": "lwp004",
        "publication_key": "legacy_white_papers.shape_of_a_theory_of_reality",
        "type": "white_paper",
        "publication_role": "orientation",
        "status": "superseded",
        "short_url": "",
        "route_status": "not_applicable",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "program", "engage"],
        "related_routes": ["/publications/white-papers/the-shape-of-a-theory-of-reality/"],
    },
    "c001-standing-in-the-inquiry-of-being": {
        "publication_id": "c001",
        "publication_key": "charter_essays.standing_in_the_inquiry_of_being",
        "type": "charter_essay",
        "publication_role": "orientation",
        "status": "released",
        "short_url": "https://prrp.site/c001",
        "route_status": "active",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "program", "engage"],
        "related_routes": [
            "/program/about/standing-in-the-inquiry-of-being/",
            "/publications/anchor-documents/",
            "/publications/anchor-documents/c001-standing-in-the-inquiry-of-being/",
        ],
    },
    "wp000-panta-rhei-at-a-glance": {
        "publication_id": "wp000",
        "publication_key": "anchor_documents.panta_rhei_at_a_glance",
        "type": "white_paper",
        "publication_role": "orientation",
        "status": "released",
        "short_url": "https://prrp.site/wp000",
        "route_status": "active",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "discover", "program", "verify"],
        "related_routes": [
            "/publications/anchor-documents/wp000-panta-rhei-at-a-glance/",
            "/discover/",
            "/program/",
            "/verify/",
        ],
    },
    "wp001-panta-rhei-research-program-executive-overview": {
        "publication_id": "wp001",
        "publication_key": "anchor_documents.panta_rhei_research_program_executive_overview",
        "type": "white_paper",
        "publication_role": "orientation",
        "status": "released",
        "short_url": "https://prrp.site/wp001",
        "route_status": "active",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "program", "verify"],
        "related_routes": ["/publications/anchor-documents/wp001-panta-rhei-research-program-executive-overview/"],
    },
    "wp002-t-theory-executive-synopsis": {
        "publication_id": "wp002",
        "publication_key": "anchor_documents.t_theory_executive_synopsis",
        "type": "white_paper",
        "publication_role": "orientation",
        "status": "released",
        "short_url": "https://prrp.site/wp002",
        "route_status": "active",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "corpus", "results", "verify"],
        "related_routes": [
            "/publications/anchor-documents/wp002-t-theory-executive-synopsis/",
            "/corpus/construction-spine/",
            "/results/",
            "/verify/",
        ],
    },
    "wp003-taulib-technical-overview": {
        "publication_id": "wp003",
        "publication_key": "anchor_documents.taulib_technical_overview",
        "type": "white_paper",
        "publication_role": "technical",
        "status": "released",
        "short_url": "https://prrp.site/wp003",
        "route_status": "active",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "corpus", "verify"],
        "related_routes": [
            "/publications/anchor-documents/wp003-taulib-technical-overview/",
            "/verify/taulib/",
            "/verify/release-manifest/",
            "/verify/custom-axioms/",
            "/verify/tcb/",
        ],
    },
    "wp004-public-research-observatory-blueprint": {
        "publication_id": "wp004",
        "publication_key": "anchor_documents.public_research_observatory_blueprint",
        "type": "white_paper",
        "publication_role": "governance",
        "status": "released",
        "short_url": "https://prrp.site/wp004",
        "route_status": "active",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "program", "agenda", "corpus", "results", "verify", "impact", "engage"],
        "related_routes": [
            "/publications/anchor-documents/wp004-public-research-observatory-blueprint/",
            "/program/",
            "/agenda/",
            "/corpus/",
            "/results/",
            "/verify/",
            "/impact/",
            "/engage/",
        ],
    },
    "wp005-global-public-good-impact-overview": {
        "publication_id": "wp005",
        "publication_key": "anchor_documents.global_public_good_impact_overview",
        "type": "white_paper",
        "publication_role": "translation",
        "status": "released",
        "short_url": "https://prrp.site/wp005",
        "route_status": "active",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "impact", "results", "verify", "corpus", "engage"],
        "related_routes": [
            "/publications/anchor-documents/wp005-global-public-good-impact-overview/",
            "/impact/",
            "/impact/global-public-good/",
            "/publications/research-briefings/public-good/",
            "/results/",
            "/verify/",
            "/corpus/",
            "/engage/",
        ],
    },
    "c002-semantic-archaeology-coherent-theory-of-reality": {
        "publication_id": "c002",
        "publication_key": "charter_essays.semantic_archaeology_coherent_theory_of_reality",
        "type": "charter_essay",
        "publication_role": "orientation",
        "short_url": "https://prrp.site/c002",
        "route_status": "reserved",
        "license": "CC-BY-4.0",
        "related_lanes": ["publications", "program", "engage"],
        "related_routes": [],
    },
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip("\n")
    body = text[end + 4 :].lstrip("\n")
    data: dict[str, Any] = {}
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#") or line.startswith(" "):
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            items: list[str] = []
            j = i + 1
            while j < len(lines) and lines[j].startswith("  - "):
                items.append(clean_scalar(lines[j][4:].strip()))
                j += 1
            if items:
                data[key] = items
                i = j
                continue
            data[key] = ""
        else:
            data[key] = clean_scalar(value)
        i += 1
    return data, body


def clean_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    if value in {"true", "false"}:
        return value == "true"
    return value


def slugify(value: str) -> str:
    value = value.lower()
    value = value.replace("τ", "tau").replace("ι", "iota")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def extract_section(body: str, heading: str) -> str:
    pattern = rf"^## {re.escape(heading)}\s*$"
    match = re.search(pattern, body, flags=re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    next_match = re.search(r"^##\s+", body[start:], flags=re.MULTILINE)
    end = start + next_match.start() if next_match else len(body)
    section = body[start:end].strip()
    return re.sub(r"\n{3,}", "\n\n", section)


def extract_first(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def hash_file(path: Path) -> dict[str, str | int]:
    sha256 = hashlib.sha256()
    sha512 = hashlib.sha512()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(chunk)
            sha256.update(chunk)
            sha512.update(chunk)
    return {
        "bytes": size,
        "sha256": sha256.hexdigest(),
        "sha512": sha512.hexdigest(),
    }


def iter_publication_dirs() -> list[Path]:
    dirs: list[Path] = []
    for root in PUBLICATION_ROOTS:
        if not root.exists():
            continue
        for child in sorted(root.iterdir()):
            if child.is_dir() and is_publication_dir_name(child.name):
                dirs.append(child)
    return dirs


def is_publication_dir_name(name: str) -> bool:
    return bool(
        re.match(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+$", name)
        or re.match(r"^[a-z]{1,4}[0-9]{3}-[a-z0-9-]+$", name)
        or re.match(r"^book-[ivx]+$", name)
    )


def registry_entry(folder_name: str) -> dict[str, Any]:
    if folder_name in PUBLICATION_REGISTRY:
        return dict(PUBLICATION_REGISTRY[folder_name])
    dynamic = dynamic_registry_entry(folder_name)
    return dict(dynamic) if dynamic else {}


def dynamic_registry_entry(folder_name: str) -> dict[str, Any]:
    """Return deterministic route metadata for bulk-synced website records."""
    if folder_name.startswith("2026-05-02-"):
        slug = folder_name.removeprefix("2026-05-02-")
        index = public_good_slug_index().get(slug)
        if index:
            return {
                "publication_id": f"pgd{index:03d}",
                "publication_key": f"public_good_dossiers.{slug.replace('-', '_')}",
                "type": "public_good_briefing",
                "publication_role": "translation",
                "short_url": f"https://prrp.site/pgd{index:03d}",
                "route_status": "reserved",
                "license": "CC-BY-4.0",
                "related_lanes": ["publications", "impact", "verify"],
                "related_routes": [f"/publications/research-briefings/public-good/{slug}/"],
            }
    special: dict[str, dict[str, Any]] = {
        "2026-05-04-panta-rhei-executive-overview": {
            "publication_id": "lwp005",
            "publication_key": "legacy_white_papers.panta_rhei_executive_overview",
            "type": "white_paper",
            "publication_role": "orientation",
            "status": "superseded",
            "short_url": "",
            "route_status": "not_applicable",
            "license": "CC-BY-4.0",
            "related_lanes": ["publications", "discover", "verify"],
            "related_routes": ["/publications/white-papers/executive-overview/"],
        },
        "ms001-numerical-physics-ledger": {
            "publication_id": "ms001",
            "publication_key": "monograph_supplements.numerical_physics_ledger",
            "type": "monograph_supplement",
            "publication_role": "technical",
            "short_url": "https://prrp.site/ms001",
            "route_status": "reserved",
            "license": "CC-BY-4.0",
            "related_lanes": ["publications", "results", "verify"],
            "related_routes": ["/publications/monograph-supplements/numerical-physics-ledger/"],
        },
        "ms002-categorical-genesis": {
            "publication_id": "ms002",
            "publication_key": "monograph_supplements.categorical_genesis",
            "type": "monograph_supplement",
            "publication_role": "orientation",
            "short_url": "https://prrp.site/ms002",
            "route_status": "reserved",
            "license": "CC-BY-4.0",
            "related_lanes": ["publications", "results", "program"],
            "related_routes": ["/publications/monograph-supplements/categorical-genesis/"],
        },
        "so001-panta-rhei-conspectus": {
            "publication_id": "so001",
            "publication_key": "synoptic_overviews.panta_rhei_conspectus",
            "type": "synoptic_overview",
            "publication_role": "orientation",
            "short_url": "https://prrp.site/so001",
            "route_status": "reserved",
            "license": "CC-BY-4.0",
            "related_lanes": ["publications", "discover", "verify"],
            "related_routes": ["/publications/conspectus/"],
        },
    }
    if folder_name in special:
        return special[folder_name]
    guided_match = re.match(r"^gt(\d{3})-guided-tour-book-([ivx]+)$", folder_name)
    if guided_match:
        number = int(guided_match.group(1))
        roman = guided_match.group(2).upper()
        return {
            "publication_id": f"gt{number:03d}",
            "publication_key": f"guided_tours.book_{roman.lower()}",
            "type": "guided_tour",
            "publication_role": "verification",
            "short_url": f"https://prrp.site/gt{number:03d}",
            "route_status": "reserved",
            "license": "CC-BY-4.0",
            "related_lanes": ["publications", "verify", "corpus"],
            "related_routes": ["/publications/guided-tours/"],
        }
    monograph_match = re.match(r"^book-([ivx]+)$", folder_name)
    if monograph_match:
        slugs = ["book-i", "book-ii", "book-iii", "book-iv", "book-v", "book-vi", "book-vii"]
        if folder_name in slugs:
            index = slugs.index(folder_name) + 1
            return {
                "publication_id": f"rm{index:03d}",
                "publication_key": f"research_monographs.{folder_name.replace('-', '_')}",
                "type": "research_monograph",
                "publication_role": "technical",
                "short_url": f"https://prrp.site/rm{index:03d}",
                "route_status": "reserved",
                "license": "Amazon KDP terms for retail book artifacts; metadata under CC-BY-4.0.",
                "related_lanes": ["publications", "corpus", "verify"],
                "related_routes": [f"/publications/research-monographs/{folder_name}/", f"/publications/books/{folder_name}/"],
            }
    return {}


def public_good_slug_index() -> dict[str, int]:
    data_path = SITE_ROOT / "_data" / "impact" / "public-good-briefings.json"
    slugs: list[str] = []
    if data_path.exists():
        try:
            data = json.loads(data_path.read_text(encoding="utf-8"))
            slugs = sorted(str(item.get("slug", "")) for item in data if item.get("slug"))
        except json.JSONDecodeError:
            slugs = []
    if not slugs:
        public_good_root = ROOT / "research-briefings" / "public-good"
        slugs = sorted(
            child.name.removeprefix("2026-05-02-")
            for child in public_good_root.iterdir()
            if child.is_dir() and child.name.startswith("2026-05-02-")
        ) if public_good_root.exists() else []
    return {slug: index + 1 for index, slug in enumerate(slugs)}


def normalize_publication_type(value: str) -> str:
    clean = slugify(value).replace("-", "_")
    aliases = {
        "research_memo": "research_paper",
        "research_paper": "research_paper",
        "research_note": "research_note",
        "public_good_briefing": "public_good_briefing",
        "white_paper": "white_paper",
        "charter_essay": "charter_essay",
        "synoptic_overview": "synoptic_overview",
        "guided_tour": "guided_tour",
        "monograph_supplement": "monograph_supplement",
        "research_monograph": "research_monograph",
    }
    return aliases.get(clean, clean)


def normalize_status(value: str) -> str:
    clean = slugify(value).replace("-", "_")
    if clean in {
        "published",
        "distribution_release",
        "draft_white_paper_technical_briefing",
        "draft_technical_white_paper_blueprint",
        "draft_white_paper_conceptual_briefing",
        "released",
        "v0_9_rc",
        "release_candidate",
        "canonical",
    }:
        return "released"
    if clean in {"planned", "reserved"}:
        return "planned"
    return clean or "released"


def display_label(value: str) -> str:
    return value.replace("_", " ").title()


def quote_yaml(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def to_simple_yaml(data: Any, indent: int = 0) -> str:
    pad = " " * indent
    if isinstance(data, dict):
        lines: list[str] = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.append(to_simple_yaml(value, indent + 2))
            elif value is None:
                lines.append(f"{pad}{key}: null")
            elif isinstance(value, bool):
                lines.append(f"{pad}{key}: {'true' if value else 'false'}")
            elif isinstance(value, (int, float)):
                lines.append(f"{pad}{key}: {value}")
            else:
                lines.append(f"{pad}{key}: {quote_yaml(str(value))}")
        return "\n".join(lines)
    if isinstance(data, list):
        if not data:
            return f"{pad}[]"
        lines = []
        for item in data:
            if isinstance(item, dict):
                lines.append(f"{pad}-")
                lines.append(to_simple_yaml(item, indent + 2))
            elif isinstance(item, list):
                lines.append(f"{pad}-")
                lines.append(to_simple_yaml(item, indent + 2))
            elif item is None:
                lines.append(f"{pad}- null")
            else:
                lines.append(f"{pad}- {quote_yaml(str(item))}")
        return "\n".join(lines)
    return f"{pad}{quote_yaml(str(data))}"


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(data), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "id",
        "publication_id",
        "publication_key",
        "publication_type",
        "type",
        "publication_role",
        "status",
        "artifact_availability",
        "title",
        "date",
        "version",
        "doi",
        "website_url",
        "canonical_url",
        "short_url",
        "route_status",
        "pdf",
        "bytes",
        "sha256",
        "sha512",
        "ots_status",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
