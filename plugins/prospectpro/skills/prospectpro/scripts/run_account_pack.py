#!/usr/bin/env python3
"""Prepare and finalize a fast ProspectPro evidence-to-report pipeline.

The internal account pack retains full audit detail.  The agent sees a much
smaller decision pack and returns only the judgments that cannot be derived
deterministically.  Finalization expands those decisions into the full report,
maps, product links, contact matching, and caches in one process.
"""

from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import match_gaps_to_contacts
import product_link_library
import render_svg_map
import run_metrics


SCHEMA_VERSION = 3
DECISION_SCHEMA_VERSION = 1
OPERATIONAL_TERMS = (
    "freight",
    "shipping",
    "handling charge",
    "dry ice",
    "hazardous",
    "delivery",
    "sales tax",
    "price discount",
)
PRODUCT_QUERY_STOPWORDS = {
    "and",
    "assay",
    "assays",
    "for",
    "kit",
    "kits",
    "product",
    "products",
    "reagent",
    "reagents",
    "the",
}
SGN_LEGAL_SUFFIXES = {"co", "company", "corp", "corporation", "inc", "incorporated", "llc", "lp", "ltd", "limited", "plc"}
SGN_GENERIC_QUERY_TOKENS = {
    "bio",
    "biotech",
    "biotherapeutics",
    "biosciences",
    "lab",
    "labs",
    "life",
    "medicine",
    "pharma",
    "pharmaceuticals",
    "sciences",
    "therapeutics",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def account_cache_key(account: str, domain: str | None = None) -> str:
    identity = normalize_text(domain or account)
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]


def is_operational(group: str, sku: str) -> bool:
    text = f"{group} {sku}".casefold()
    return group.strip().upper().startswith("FR") or any(term in text for term in OPERATIONAL_TERMS)


def parse_sgn_label(label: str) -> tuple[str | None, str]:
    match = re.match(r"^\s*(\d+)\s*[-–—]\s*(.*?)\s*$", label)
    if match:
        return match.group(1), match.group(2)
    return None, label.strip()


def company_tokens(value: str) -> list[str]:
    _, name = parse_sgn_label(value)
    tokens = re.findall(r"[a-z0-9]+", normalize_text(name))
    while tokens and tokens[-1] in SGN_LEGAL_SUFFIXES:
        tokens.pop()
    return tokens


def fuzzy_sgn_score(query_tokens: list[str], candidate_tokens: list[str]) -> float:
    if not query_tokens or not candidate_tokens:
        return 0.0
    query_phrase = " ".join(query_tokens)
    candidate_phrase = " ".join(candidate_tokens)
    if query_phrase in candidate_phrase:
        return 1.0
    span_size = min(len(query_tokens), len(candidate_tokens))
    span_scores = [
        SequenceMatcher(None, query_phrase, " ".join(candidate_tokens[index:index + span_size])).ratio()
        for index in range(len(candidate_tokens) - span_size + 1)
    ]
    token_scores = (
        [SequenceMatcher(None, query_tokens[0], candidate_token).ratio() for candidate_token in candidate_tokens]
        if len(query_tokens) == 1
        else []
    )
    whole_score = SequenceMatcher(None, query_phrase, candidate_phrase).ratio()
    return max([whole_score, *span_scores, *token_scores])


def common_account_name(matches: list[dict[str, Any]]) -> str:
    token_lists = [company_tokens(str(item["value"])) for item in matches]
    common: list[str] = []
    for token_group in zip(*token_lists):
        if len(set(token_group)) != 1:
            break
        common.append(token_group[0])
    if common:
        return " ".join(common).upper()
    names = [parse_sgn_label(str(item["value"]))[1] for item in matches]
    return min(names, key=lambda value: (len(value), value.casefold()))


def resolve_sgn_accounts(query: str, known_accounts: list[dict[str, Any]]) -> dict[str, Any]:
    requested = normalize_text(query)
    candidates = []
    for item in known_accounts:
        label = str(item.get("value", "")).strip()
        if not label:
            continue
        sgn_id, name = parse_sgn_label(label)
        candidates.append({
            "value": label,
            "sgn_id": sgn_id,
            "name": name,
            "row_count": int(item.get("row_count") or 0),
            "tokens": company_tokens(label),
        })
    if not candidates:
        raise ValueError("No SGN account identifiers were found in the workbook.")

    exact_label = [item for item in candidates if normalize_text(item["value"]) == requested]
    exact_id = [item for item in candidates if item["sgn_id"] == query.strip()]
    if len(exact_label) == 1 or len(exact_id) == 1:
        selected = exact_label or exact_id
        selected[0]["match_score"] = 1.0
        return {
            "method": "exact_sgn",
            "display_name": selected[0]["name"],
            "matches": selected,
        }

    query_tokens = company_tokens(query)
    if not query_tokens:
        raise ValueError("The customer query does not contain a usable SGN company name or numeric SGN identifier.")
    if len(query_tokens) == 1 and query_tokens[0] in SGN_GENERIC_QUERY_TOKENS:
        raise ValueError(f"Customer query {query!r} is too broad for safe SGN roll-up matching.")
    scored = []
    for item in candidates:
        score = fuzzy_sgn_score(query_tokens, item["tokens"])
        scored.append({**item, "match_score": round(score, 4)})
    scored.sort(key=lambda item: (-item["match_score"], -item["row_count"], item["value"].casefold()))
    best_score = scored[0]["match_score"]
    compact_query = "".join(query_tokens)
    threshold = 0.70 if len(compact_query) >= 6 else 0.80
    if len(compact_query) < 4 and best_score < 1.0:
        raise ValueError(f"Customer query {query!r} is too short for safe fuzzy SGN matching.")
    if best_score < threshold:
        suggestions = " | ".join(item["value"] for item in scored[:5])
        raise ValueError(f"No SGN company name closely matches {query!r}. Nearest SGNs: {suggestions}")

    selected = [item for item in scored if item["match_score"] >= threshold]
    if len(selected) > 20:
        raise ValueError(
            f"Customer query {query!r} matched {len(selected)} SGNs and is too broad. Use a more specific company name or exact numeric SGN."
        )
    return {
        "method": "fuzzy_sgn_rollup",
        "display_name": common_account_name(selected),
        "matches": selected,
    }


def run_normalizer(
    workbook: Path,
    output: Path,
    cache_dir: Path,
    accounts: list[str] | None,
    sheet: str | None,
    account_field: str | None = None,
) -> dict[str, Any]:
    script = Path(__file__).resolve().parent / "normalize_workbook.py"
    command = [
        sys.executable,
        str(script),
        str(workbook),
        "--output",
        str(output),
        "--cache-dir",
        str(cache_dir),
        "--schema",
        "auto",
    ]
    for account in accounts or []:
        command.extend(["--account", account])
    if account_field:
        command.extend(["--account-field", account_field])
    if sheet:
        command.extend(["--sheet", sheet])
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or result.stdout.strip() or "Workbook normalization failed.")
    return load_json(output)


def rollup_product_families(product_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in product_rows:
        group = str(row.get("group") or "Unmapped").strip()
        sku = str(row.get("sku") or "").strip()
        if is_operational(group, sku):
            continue
        item = grouped.setdefault(
            group,
            {
                "product_family": group,
                "latest_ytd_sales": 0.0,
                "prior_ytd_sales": 0.0,
                "latest_ytd_quantity": 0.0,
                "prior_ytd_quantity": 0.0,
                "skus": [],
            },
        )
        for field in ("latest_ytd_sales", "prior_ytd_sales", "latest_ytd_quantity", "prior_ytd_quantity"):
            item[field] += float(row.get(field) or 0.0)
        if sku and sku not in item["skus"]:
            item["skus"].append(sku)
    result = []
    for item in grouped.values():
        item["latest_ytd_sales"] = round(item["latest_ytd_sales"], 2)
        item["prior_ytd_sales"] = round(item["prior_ytd_sales"], 2)
        item["latest_ytd_quantity"] = round(item["latest_ytd_quantity"], 3)
        item["prior_ytd_quantity"] = round(item["prior_ytd_quantity"], 3)
        item["change"] = round(item["latest_ytd_sales"] - item["prior_ytd_sales"], 2)
        item["skus"] = item["skus"][:8]
        result.append(item)
    return sorted(result, key=lambda item: (-max(abs(item["latest_ytd_sales"]), abs(item["prior_ytd_sales"])), item["product_family"]))


def cache_status(cache_path: Path) -> dict[str, Any]:
    if not cache_path.is_file():
        return {
            "available": False,
            "core_fresh": False,
            "contacts_fresh": False,
            "dynamic_refresh_required": True,
            "cached": None,
        }
    cached = load_json(cache_path)
    today = date.today()

    def fresh(field: str, days: int) -> bool:
        raw = cached.get("verified_at", {}).get(field)
        if not raw:
            return False
        try:
            verified = datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            return False
        return (today - verified).days <= days

    return {
        "available": True,
        "core_fresh": fresh("core", 90),
        "contacts_fresh": fresh("contacts", 30),
        "dynamic_refresh_required": True,
        "cached": cached,
    }


def build_spec_template(pack_path: Path, pack: dict[str, Any]) -> dict[str, Any]:
    coverage = pack["workbook"]["coverage"]
    ytd = pack["workbook"]["ytd"]
    return {
        "schema_version": SCHEMA_VERSION,
        "pack": str(pack_path),
        "account": {
            "name": pack["account"]["name"],
            "domain": "",
            "scope": (
                f"{ytd['latest_year']} YTD through {coverage['latest_ytd_cutoff']} versus "
                f"{ytd['prior_year']} PYTD through {coverage['prior_ytd_cutoff']} · "
                f"{len(pack['account']['sgns'])} matched SGN{'s' if len(pack['account']['sgns']) != 1 else ''}"
            ),
        },
        "company_summary": "",
        "recent_developments": [],
        "footprint": [],
        "lapsed_products": [],
        "gaps": [],
        "contacts": [],
        "technique_map": {"title": "", "subtitle": "", "description": "", "lanes": []},
        "workflow_map": {"title": "", "subtitle": "", "description": "", "lanes": []},
        "email": {"recipient": "", "subject": "", "body": ""},
        "research": {
            "identity": {},
            "core_science": {},
            "contacts": [],
            "sources": [],
        },
        "sources": [],
        "operations": {
            "web_batches": 0,
            "outlook_search_batches": 0,
            "outlook_messages_fetched": 0,
            "style_profile_reused": False,
            "product_link_web_searches": 0,
        },
    }


def default_scope(pack: dict[str, Any]) -> str:
    coverage = pack["workbook"]["coverage"]
    ytd = pack["workbook"]["ytd"]
    count = len(pack["account"]["sgns"])
    return (
        f"{ytd['latest_year']} YTD through {coverage['latest_ytd_cutoff']} versus "
        f"{ytd['prior_year']} PYTD through {coverage['prior_ytd_cutoff']} · "
        f"{count} matched SGN{'s' if count != 1 else ''}"
    )


def compact_family(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "product_family": row.get("product_family"),
        "ytd": row.get("latest_ytd_sales", 0),
        "pytd": row.get("prior_ytd_sales", 0),
        "change": row.get("change", 0),
        "skus": row.get("skus", [])[:4],
    }


def compact_lapsed(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "sku": row.get("sku"),
        "product_family": row.get("group"),
        "last_purchase": row.get("last_positive_purchase_date"),
        "purchase_dates": row.get("positive_purchase_date_count", 0),
        "days_since_purchase": row.get("days_since_last_positive_purchase"),
        "historical_sales": row.get("historical_positive_sales", 0),
        "prior_ytd_sales": row.get("prior_ytd_sales", 0),
    }


def build_decision_pack(pack: dict[str, Any]) -> dict[str, Any]:
    """Return only evidence needed for a single model synthesis."""
    ytd = pack["workbook"]["ytd"]
    latest = float(ytd.get("latest_ytd_sales") or 0)
    prior = float(ytd.get("prior_ytd_sales") or 0)
    change_pct = round((latest - prior) / abs(prior) * 100, 1) if prior else None
    cached = pack.get("research_cache", {}).get("cached") or {}
    return {
        "_protocol": "Update this existing file once. Do not delete, recreate, or replace it with another decisions file.",
        "schema_version": DECISION_SCHEMA_VERSION,
        "account": {
            "name": pack["account"]["name"],
            "query": pack["account"]["query"],
            "matched_sgns": [item["value"] for item in pack["account"]["sgns"]],
            "domain_hint": pack["account"].get("domain_hint"),
            "scope": default_scope(pack),
        },
        "period": {
            "latest_year": ytd["latest_year"],
            "latest_ytd_sales": latest,
            "prior_year": ytd["prior_year"],
            "prior_ytd_sales": prior,
            "change_percent": change_pct,
        },
        "top_purchase_families": [
            compact_family(row)
            for row in pack["workbook"]["product_family_rollup"][:12]
        ],
        "lapsed_candidates": [
            compact_lapsed(row)
            for row in pack["workbook"].get("lapsed_candidates", [])
        ],
        "cache_seed": {
            "core_fresh": bool(pack.get("research_cache", {}).get("core_fresh")),
            "contacts_fresh": bool(pack.get("research_cache", {}).get("contacts_fresh")),
            "core": cached.get("core") if pack.get("research_cache", {}).get("core_fresh") else None,
            "contacts": cached.get("contacts") if pack.get("research_cache", {}).get("contacts_fresh") else None,
        },
        "decision_contract": {
            "retain_gaps": "retain every credible anchored opportunity; do not impose an arbitrary count",
            "lapsed": "select only credible recurring consumables; migration is not lapse",
            "contacts": "verified current employment only; never guess email",
            "absence_language": "not observed in the supplied purchase history for the matched SGNs and period",
            "maps": "generated and structurally verified automatically; do not author or preview map specifications",
            "footprint": "generated automatically; do not reproduce purchase tables",
        },
    }


def build_decision_template() -> dict[str, Any]:
    """Small model-authored payload; no report layout or duplicated workbook facts."""
    return {
        "_protocol": "Update this existing file once. Do not delete, recreate, or replace it with another decisions file.",
        "schema_version": DECISION_SCHEMA_VERSION,
        "company_summary": "",
        "recent_developments": [],
        "lapsed_products": [],
        "gaps": [],
        "contacts": [],
        "email": {"recipient": "", "subject": "", "body": ""},
        "research": {"identity": {}, "core_science": {}},
        "sources": [],
        "operations": {
            "web_batches": 0,
            "outlook_search_batches": 0,
            "outlook_messages_fetched": 0,
            "style_profile_reused": False,
            "product_link_web_searches": 0,
        },
    }


def slug(value: Any, fallback: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", normalize_text(value)).strip("-")
    return result or fallback


def trend_note(current: float, prior: float) -> str:
    if prior == 0 and current > 0:
        return "New matched-period purchasing activity; validate the workflow and expansion path."
    if current == 0 and prior > 0:
        return "No current-period spend observed; distinguish migration, project timing, and true lapse."
    difference = current - prior
    if abs(difference) < 1:
        return "Matched-period purchasing is essentially stable."
    direction = "increased" if difference > 0 else "decreased"
    pct = abs(difference) / abs(prior) * 100 if prior else 0
    return f"Matched-period purchasing {direction} {pct:.0f}%; validate the operational driver."


def build_footprint(pack: dict[str, Any]) -> list[dict[str, Any]]:
    ytd = pack["workbook"]["ytd"]
    latest = float(ytd.get("latest_ytd_sales") or 0)
    prior = float(ytd.get("prior_ytd_sales") or 0)
    rows = [{
        "area": "Total matched SGN",
        "ytd": latest,
        "pytd": prior,
        "suggests": trend_note(latest, prior),
    }]
    for family in pack["workbook"]["product_family_rollup"][:6]:
        current = float(family.get("latest_ytd_sales") or 0)
        previous = float(family.get("prior_ytd_sales") or 0)
        rows.append({
            "area": family.get("product_family"),
            "ytd": current,
            "pytd": previous,
            "suggests": trend_note(current, previous),
        })
    return rows


def build_maps(account_name: str, footprint: list[dict[str, Any]], gaps: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    observed_nodes = []
    for index, row in enumerate(footprint[1:5], start=1):
        observed_nodes.append({
            "id": f"observed-{index}",
            "title": str(row.get("area") or "Observed purchase"),
            "subtitle": f"YTD {money(row.get('ytd'))}; PYTD {money(row.get('pytd'))}",
            "status": "observed",
        })
    opportunity_nodes = [{
        "id": f"opportunity-{index}",
        "title": gap["name"],
        "subtitle": gap["why"],
        "status": "opportunity",
    } for index, gap in enumerate(gaps, start=1)]
    technique = {
        "title": f"{account_name.title()} Purchase and Opportunity Landscape",
        "subtitle": "Observed purchasing and focused opportunities to validate",
        "description": "Automatically generated from matched purchase history and qualified gaps.",
        "lanes": [
            {"label": "Observed purchases", "nodes": observed_nodes, "connect": False},
            {"label": "Validate next", "nodes": opportunity_nodes, "connect": False},
        ],
    }
    workflow_lanes = []
    for index, gap in enumerate(gaps, start=1):
        workflow_lanes.append({
            "label": f"Priority {gap['priority']}",
            "nodes": [
                {"id": f"anchor-{index}", "title": "Observed anchor", "subtitle": gap["anchor"], "status": "observed"},
                {"id": f"gap-{index}", "title": gap["name"], "subtitle": gap["gap"], "status": "opportunity"},
                {"id": f"motion-{index}", "title": "Seller motion", "subtitle": gap["motion"], "status": "neutral"},
            ],
        })
    workflow = {
        "title": f"{account_name.title()} Evidence-to-Action Map",
        "subtitle": "Observed anchor → gap to validate → seller motion",
        "description": "Automatically generated from the qualified opportunity decisions.",
        "lanes": workflow_lanes,
    }
    return technique, workflow


def expand_decisions(pack: dict[str, Any], decisions: dict[str, Any]) -> dict[str, Any]:
    """Expand a compact decision payload into the legacy full report spec."""
    if int(decisions.get("schema_version") or 0) != DECISION_SCHEMA_VERSION:
        raise ValueError(f"Decisions need schema_version {DECISION_SCHEMA_VERSION}.")
    raw_gaps = decisions.get("gaps")
    if not isinstance(raw_gaps, list) or not raw_gaps:
        raise ValueError("Decisions must contain at least one qualified gap.")
    gaps = []
    for index, item in enumerate(raw_gaps, start=1):
        name = str(item.get("name") or "").strip()
        anchor = str(item.get("anchor") or "").strip()
        gap_text = str(item.get("gap") or "").strip()
        motion = str(item.get("motion") or "").strip()
        question = str(item.get("discovery_question") or "").strip()
        if not all((name, anchor, gap_text, motion, question)):
            raise ValueError(f"Gap {index} needs name, anchor, gap, motion, and discovery_question.")
        tags = [str(value).strip() for value in item.get("tags", []) if str(value).strip()]
        query = item.get("product_query") or name
        queries = query if isinstance(query, list) else [query]
        gaps.append({
            "id": f"gap-{slug(name, str(index))}",
            "priority": index,
            "name": name,
            "anchor": anchor,
            "gap": gap_text,
            "motion": motion,
            "why": f"{anchor} → {gap_text} → {motion}",
            "estimated_annual_revenue": item.get("estimated_annual_revenue"),
            "product_queries": [str(value) for value in queries[:3] if str(value).strip()],
            "discovery_question": question,
            "workflows": tags,
            "techniques": tags,
            "keywords": tags,
        })

    contacts = []
    for index, item in enumerate(decisions.get("contacts", []), start=1):
        name = str(item.get("name") or "").strip()
        role = str(item.get("current_role") or "").strip()
        if not name or not role or not bool(item.get("current_employer_verified")):
            continue
        tags = [str(value).strip() for value in item.get("tags", []) if str(value).strip()]
        contacts.append({
            "id": slug(name, f"contact-{index}"),
            "name": name,
            "current_role": role,
            "team": item.get("team", ""),
            "current_employer_verified": True,
            "verified_email": item.get("verified_email", ""),
            "why_relevant": item.get("why_relevant") or (
                f"Verified current {role}"
                + (f" on the {item.get('team')} team" if item.get("team") else "")
                + "; relevant where the supplied evidence tags overlap a qualified gap."
            ),
            "outreach_angle": item.get("outreach_angle") or (
                "Lead with the matched workflow evidence and ask how the adjacent step is handled today."
            ),
            "relationship_strength": item.get("relationship_strength", "unknown"),
            "workflows": tags,
            "techniques": tags,
            "keywords": tags,
            "source_ids": item.get("source_ids", []),
        })

    candidate_by_sku = {
        normalize_text(row.get("sku")): row
        for row in pack["workbook"].get("lapsed_candidates", [])
    }
    lapsed = []
    for item in decisions.get("lapsed_products", []):
        choice = {"sku": item} if isinstance(item, str) else item
        if not isinstance(choice, dict):
            continue
        requested = normalize_text(choice.get("sku"))
        candidate = candidate_by_sku.get(requested)
        if not candidate:
            continue
        label = choice.get("product") or candidate.get("sku")
        dates = int(candidate.get("positive_purchase_date_count") or 0)
        last_purchase = candidate.get("last_positive_purchase_date")
        lapsed.append({
            "product": label,
            "last_purchase": last_purchase,
            "status": choice.get("status") or (
                f"Win-back hypothesis: {dates} historical positive purchase dates; "
                f"last positive purchase {last_purchase or 'not available'}"
            ),
            "motion": choice.get("motion") or (
                "Confirm the workflow is still active and distinguish supplier change, format change, "
                "site transfer, and true lapse before proposing recapture."
            ),
        })

    footprint = build_footprint(pack)
    technique_map, workflow_map = build_maps(pack["account"]["name"], footprint, gaps)
    research = decisions.get("research") or {}
    sources = decisions.get("sources") or []
    research_contacts = [
        {"id": item["id"], "name": item["name"], "current_role": item["current_role"], "source_ids": item.get("source_ids", [])}
        for item in contacts
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "account": {
            "name": pack["account"]["name"],
            "domain": (research.get("identity") or {}).get("domain", pack["account"].get("domain_hint") or ""),
            "scope": default_scope(pack),
        },
        "company_summary": decisions.get("company_summary", ""),
        "recent_developments": decisions.get("recent_developments", [])[:3],
        "footprint": footprint,
        "lapsed_products": lapsed,
        "gaps": gaps,
        "contacts": contacts,
        "technique_map": technique_map,
        "workflow_map": workflow_map,
        "email": decisions.get("email") or {"recipient": "", "subject": "", "body": ""},
        "research": {
            "identity": research.get("identity", {}),
            "core_science": research.get("core_science", {}),
            "contacts": research_contacts,
            "sources": sources,
        },
        "sources": sources,
        "operations": decisions.get("operations") or {},
    }


def prepare(args: argparse.Namespace) -> int:
    workbook = Path(args.workbook).expanduser().resolve()
    if not workbook.is_file():
        raise ValueError(f"Workbook not found: {workbook}")
    backend = Path(args.backend).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    decision_pack_path = (
        Path(args.decision_pack).expanduser().resolve()
        if args.decision_pack
        else output.with_name("decision-pack.json")
    )
    decision_template_path = (
        Path(args.decision_template).expanduser().resolve()
        if args.decision_template
        else output.with_name("decisions.json")
    )
    backend.mkdir(parents=True, exist_ok=True)
    metrics_state = backend / "current-run.json"
    history = backend / "run-history.jsonl"
    run_metrics.begin(metrics_state)

    run_metrics.start_phase(metrics_state, "intake")
    library = backend / "thermo-product-links.json"
    product_link_library.initialize(library, product_link_library.DEFAULT_SEED)
    run_metrics.stop_phase(metrics_state, "intake")

    run_metrics.start_phase(metrics_state, "workbook")
    profiling_output = backend / "workbook-profile.json"
    profile = run_normalizer(
        workbook,
        profiling_output,
        backend / "workbook-cache",
        None,
        args.sheet,
        "site_id",
    )
    resolution = resolve_sgn_accounts(args.customer, profile.get("known_accounts", []))
    selected_sgns = [item["value"] for item in resolution["matches"]]
    normalized_output = backend / "normalized-purchases.json"
    normalized = run_normalizer(
        workbook,
        normalized_output,
        backend / "workbook-cache",
        selected_sgns,
        args.sheet,
        "site_id",
    )
    run_metrics.stop_phase(metrics_state, "workbook")
    run_metrics.mark(metrics_state, "workbook_cache_hit", str(bool(normalized.get("backend", {}).get("cache_hit"))).lower())

    cache_key = account_cache_key(" | ".join(sorted(selected_sgns)), args.domain)
    research_cache_path = backend / "research-cache" / f"{cache_key}.json"
    pack = {
        "schema_version": SCHEMA_VERSION,
        "prepared_at": now_iso(),
        "account": {
            "query": args.customer,
            "name": resolution["display_name"],
            "account_field": "SGN",
            "resolution_method": resolution["method"],
            "sgns": [
                {key: value for key, value in item.items() if key != "tokens"}
                for item in resolution["matches"]
            ],
            "domain_hint": args.domain or None,
            "research_cache_key": cache_key,
        },
        "workbook": {
            "source": normalized["source"],
            "coverage": normalized["coverage"],
            "reconciliation": normalized["reconciliation"],
            "ytd": normalized["ytd"],
            "warnings": normalized.get("warnings", []),
            "product_family_rollup": rollup_product_families(normalized.get("product_rows", [])),
            "product_rows": [row for row in normalized.get("product_rows", []) if not is_operational(str(row.get("group", "")), str(row.get("sku", "")))],
            "lapsed_candidates": normalized.get("lapsed_products", []),
            "backend": normalized.get("backend", {}),
        },
        "research_cache": cache_status(research_cache_path),
        "execution_contract": {
            "public_web": {
                "discovery_batches": 1,
                "open_batches": 1,
                "exception_batches": 1,
                "dynamic_items_always_refreshed": ["recent news", "clinical trials"],
            },
            "outlook": {
                "discovery_batches": 1,
                "fetch_batches": 1,
                "strategy": "exact domain and exact known contacts first; stop when empty",
            },
            "connector_output": "Return only ids, subject/name, sender/role, recipients, date, preview, and pagination metadata until selected.",
        },
        "paths": {
            "backend": str(backend),
            "metrics_state": str(metrics_state),
            "metrics_history": str(history),
            "product_library": str(library),
            "research_cache": str(research_cache_path),
        },
    }
    atomic_write(output, pack)
    decision_pack = build_decision_pack(pack)
    atomic_write(decision_pack_path, decision_pack)
    atomic_write(decision_template_path, build_decision_template())
    run_metrics.start_phase(metrics_state, "research_and_decisions")
    print(json.dumps({
        "status": "prepared",
        "account": resolution["display_name"],
        "account_field": "SGN",
        "resolution_method": resolution["method"],
        "matched_sgns": selected_sgns,
        "internal_pack": str(output),
        "decision_pack": str(decision_pack_path),
        "decision_template": str(decision_template_path),
        "decision_pack_bytes": decision_pack_path.stat().st_size,
        "workbook_cache_hit": bool(normalized.get("backend", {}).get("cache_hit")),
        "research_cache": {
            "core_fresh": pack["research_cache"]["core_fresh"],
            "contacts_fresh": pack["research_cache"]["contacts_fresh"],
            "dynamic_refresh_required": True,
        },
    }, indent=2))
    return 0


def score_product_links(library: dict[str, Any], query: str, max_results: int = 1) -> list[dict[str, Any]]:
    tokens = {
        token
        for token in re.findall(r"[a-z0-9]+", query.casefold())
        if len(token) > 1 and token not in PRODUCT_QUERY_STOPWORDS
    }
    results = []
    today = date.today()
    for entry in library.get("entries", []):
        haystack = " ".join([entry["name"], entry["category"], entry["specificity"], *entry.get("keywords", [])]).casefold()
        name_tokens = set(re.findall(r"[a-z0-9]+", entry["name"].casefold()))
        haystack_tokens = set(re.findall(r"[a-z0-9]+", haystack))
        score = sum(3 if token in name_tokens else 1 for token in tokens if token in haystack_tokens)
        if query.strip().casefold() in entry["name"].casefold():
            score += 6
        if not score:
            continue
        verified = datetime.strptime(entry["verified_at"], "%Y-%m-%d").date()
        stale = (today - verified).days > 180
        results.append({
            "name": entry["name"],
            "url": entry["url"],
            "specificity": entry["specificity"],
            "verified_at": entry["verified_at"],
            "stale": stale,
            "match_score": score,
        })
    results.sort(key=lambda item: (-item["match_score"], item["stale"], item["name"].casefold()))
    return results[:max_results]


def validate_svg_spec(spec: dict[str, Any], label: str) -> dict[str, Any]:
    render_svg_map.validate_spec(spec)
    node_count = sum(len(lane.get("nodes", [])) for lane in spec.get("lanes", []))
    longest_title = max((len(str(node.get("title", ""))) for lane in spec["lanes"] for node in lane["nodes"]), default=0)
    return {
        "label": label,
        "status": "passed",
        "qa_mode": "deterministic_adaptive_layout",
        "node_count": node_count,
        "longest_title": longest_title,
        "warnings": [],
    }


def markdown_escape(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def money(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, str):
        return value
    return f"${float(value):,.0f}"


def markdown_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    lines.extend("| " + " | ".join(markdown_escape(cell) for cell in row) + " |" for row in rows)
    return lines


def render_report(spec: dict[str, Any], pack: dict[str, Any], gap_links: dict[str, list[dict[str, Any]]], matches: dict[str, Any], technique_name: str, workflow_name: str) -> str:
    account = spec.get("account", {})
    lines = [f"# {account.get('name') or pack['account']['name']} Account Whitespace Brief", ""]
    if account.get("scope"):
        lines.extend([f"**Scope:** {account['scope']}", ""])
    lines.extend(["## Company Summary", "", str(spec.get("company_summary", "")).strip(), ""])
    lines.extend(["## Recent Developments", ""])
    developments = spec.get("recent_developments", [])[:3]
    lines.extend([f"- {item}" for item in developments] or ["- No material recent development found."])
    lines.extend(["", "## Current Purchase Footprint", ""])
    lines.extend(markdown_table(
        ["Product area", "YTD net sales", "PY net sales", "What it suggests"],
        [[row.get("area"), money(row.get("ytd")), money(row.get("pytd")), row.get("suggests")] for row in spec.get("footprint", [])],
    ))
    workbook_name = Path(str(pack["workbook"]["source"]["file"])).name
    lines.extend(["", f"Workbook: {workbook_name} · Sheet: {pack['workbook']['source']['sheet']}", ""])
    lines.extend(["## Technique Landscape", "", f"![Technique landscape]({technique_name})", "", "## Workflow Map", "", f"![Workflow map]({workflow_name})", ""])
    if spec.get("lapsed_products"):
        lines.extend(["## Lapsed Products", ""])
        lines.extend(markdown_table(
            ["Product", "Last positive purchase", "Status", "Suggested motion"],
            [[row.get("product"), row.get("last_purchase"), row.get("status"), row.get("motion")] for row in spec["lapsed_products"]],
        ))
        lines.append("")
    lines.extend(["## Product Whitespace", ""])
    gap_rows = []
    for gap in sorted(spec.get("gaps", []), key=lambda item: (item.get("priority", 999), item.get("name", ""))):
        links = gap_links.get(str(gap.get("id")), [])
        link_text = ", ".join(f"[{item['name']}]({item['url']})" for item in links if not item.get("stale"))
        gap_rows.append([
            gap.get("priority"),
            gap.get("name"),
            gap.get("why"),
            money(gap.get("estimated_annual_revenue")),
            link_text or "Needs verified product page",
        ])
    lines.extend(markdown_table(["Priority", "Gap", "Why it fits", "Estimated annual revenue if closed", "Products to pitch"], gap_rows))
    questions = [gap.get("discovery_question") for gap in spec.get("gaps", []) if gap.get("discovery_question")]
    if questions:
        lines.extend(["", "## Discovery Questions", "", *[f"- {question}" for question in questions]])
    email = spec.get("email", {})
    lines.extend(["", "## Outreach Draft", ""])
    if email.get("recipient"):
        lines.append(f"**To:** {email['recipient']}")
    lines.extend([f"**Subject:** {email.get('subject', '')}", "", str(email.get("body", "")).strip(), ""])
    lines.extend(["## Key Contacts", ""])
    contact_details = {str(item.get("id")): item for item in spec.get("contacts", [])}
    contact_rows = []
    for row in matches.get("contacts_for_report", []):
        detail = contact_details.get(str(row.get("contact_id")), {})
        contact_rows.append([
            row.get("contact_name"),
            f"{row.get('current_role') or ''}; {row.get('team') or ''}".strip("; "),
            ", ".join(item["gap_name"] for item in row.get("matched_gaps", [])),
            detail.get("why_relevant", ""),
            detail.get("outreach_angle", ""),
            row.get("verified_email") or "",
        ])
    lines.extend(markdown_table(["Contact", "Current role/team", "Matched gaps", "Why relevant", "Best outreach angle", "Verified email"], contact_rows))
    lines.extend(["", "## Sources", ""])
    for source in spec.get("sources", []):
        if source.get("url") and source.get("label"):
            lines.append(f"- [{source['label']}]({source['url']})")
    return "\n".join(lines).rstrip() + "\n"


def save_research_cache(path: Path, spec: dict[str, Any]) -> None:
    research = spec.get("research", {})
    today = date.today().isoformat()
    cached = {
        "schema_version": SCHEMA_VERSION,
        "account_identity": spec.get("account", {}),
        "verified_at": {"core": today, "contacts": today, "dynamic_last_seen": today},
        "core": {
            "identity": research.get("identity", {}),
            "science": research.get("core_science", {}),
            "company_summary": spec.get("company_summary", ""),
            "sources": research.get("sources", []),
        },
        "contacts": research.get("contacts", spec.get("contacts", [])),
        "dynamic_last_seen": {
            "recent_developments": spec.get("recent_developments", []),
            "sources": spec.get("sources", []),
        },
    }
    atomic_write(path, cached)


def finalize(args: argparse.Namespace) -> int:
    pack = load_json(Path(args.pack).expanduser().resolve())
    backend = Path(pack["paths"]["backend"]).resolve()
    state = Path(pack["paths"]["metrics_state"]).resolve()
    history = Path(pack["paths"]["metrics_history"]).resolve()
    timing_state = run_metrics.load_state(state)
    phase_state = timing_state.get("phases", {}).get("research_and_decisions", {})
    if phase_state.get("active_started_epoch") is not None:
        run_metrics.stop_phase(state, "research_and_decisions")
    if args.decisions:
        decisions = load_json(Path(args.decisions).expanduser().resolve())
        spec = expand_decisions(pack, decisions)
    elif args.spec:
        # Backward compatibility for a v1.2 full specification.
        spec = load_json(Path(args.spec).expanduser().resolve())
    else:
        raise ValueError("finalize requires --decisions (preferred) or --spec (legacy).")
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    expanded_spec_path = backend / "expanded-account-spec.json"
    atomic_write(expanded_spec_path, spec)

    run_metrics.start_phase(state, "product_links")
    library_path = Path(pack["paths"]["product_library"]).resolve()
    library = product_link_library.load_library(library_path)
    gap_links: dict[str, list[dict[str, Any]]] = {}
    library_hits = 0
    for gap in spec.get("gaps", []):
        selected: list[dict[str, Any]] = []
        seen_urls: set[str] = set()
        for query in gap.get("product_queries", []):
            for item in score_product_links(library, str(query)):
                if item["url"] not in seen_urls:
                    selected.append(item)
                    seen_urls.add(item["url"])
        selected.sort(key=lambda item: (-item["match_score"], item["stale"], item["name"].casefold()))
        gap_links[str(gap.get("id"))] = selected[:3]
        library_hits += sum(1 for item in selected[:3] if not item["stale"])
    run_metrics.mark(state, "product_link_library_hits", str(library_hits))
    run_metrics.mark(state, "product_link_web_searches", str(int(spec.get("operations", {}).get("product_link_web_searches", 0))))
    run_metrics.stop_phase(state, "product_links")

    run_metrics.start_phase(state, "contacts")
    match_payload = {"gaps": spec.get("gaps", []), "contacts": spec.get("contacts", [])}
    matches = match_gaps_to_contacts.analyze(
        match_payload,
        max_contacts_per_gap=max(1, len(spec.get("contacts", []))),
    )
    run_metrics.stop_phase(state, "contacts")

    run_metrics.start_phase(state, "svg")
    technique_spec = spec.get("technique_map", {})
    workflow_spec = spec.get("workflow_map", {})
    technique_qa = validate_svg_spec(technique_spec, "technique_map")
    workflow_qa = validate_svg_spec(workflow_spec, "workflow_map")
    technique_path = output_dir / "techniques.svg"
    workflow_path = output_dir / "workflow-map.svg"
    atomic_write_text(technique_path, render_svg_map.render(technique_spec))
    atomic_write_text(workflow_path, render_svg_map.render(workflow_spec))
    run_metrics.stop_phase(state, "svg")

    run_metrics.start_phase(state, "report")
    report = render_report(spec, pack, gap_links, matches, technique_path.name, workflow_path.name)
    report_path = Path(args.report_output).expanduser().resolve() if args.report_output else output_dir / "account-brief.md"
    atomic_write_text(report_path, report)
    save_research_cache(Path(pack["paths"]["research_cache"]).resolve(), spec)
    final_pack = {
        "schema_version": SCHEMA_VERSION,
        "created_at": now_iso(),
        "account": spec.get("account", {}),
        "gap_product_links": gap_links,
        "contact_matches": matches,
        "svg_qa": [technique_qa, workflow_qa],
        "email": spec.get("email", {}),
        "sources": spec.get("sources", []),
        "outputs": {
            "report": str(report_path),
            "techniques_svg": str(technique_path),
            "workflow_svg": str(workflow_path),
            "expanded_spec": str(expanded_spec_path),
        },
    }
    final_pack_path = output_dir / "final-pack.json"
    atomic_write(final_pack_path, final_pack)
    run_metrics.stop_phase(state, "report")

    operations = spec.get("operations", {})
    for key in ("web_batches", "outlook_search_batches", "outlook_messages_fetched"):
        run_metrics.mark(state, key, str(int(operations.get(key, 0))))
    run_metrics.mark(state, "style_profile_reused", str(bool(operations.get("style_profile_reused", False))).lower())
    run_metrics.mark(state, "research_core_cache_hit", str(bool(pack.get("research_cache", {}).get("core_fresh"))).lower())
    run_metrics.mark(state, "research_contacts_cache_hit", str(bool(pack.get("research_cache", {}).get("contacts_fresh"))).lower())
    run_metrics.mark(state, "run_failed", "false")
    run_metrics.finish(state, history)
    print(json.dumps({
        "status": "finalized",
        "report": str(report_path),
        "final_pack": str(final_pack_path),
        "product_link_hits": library_hits,
        "contacts_selected": len(matches.get("contacts_for_report", [])),
        "svg_qa": "passed",
        "unresolved_product_gaps": [
            gap.get("name")
            for gap in spec.get("gaps", [])
            if not any(not item.get("stale") for item in gap_links.get(str(gap.get("id")), []))
        ],
    }, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare", help="Normalize the workbook and create a decision-ready account pack")
    prepare_parser.add_argument("workbook")
    prepare_parser.add_argument(
        "--customer",
        required=True,
        help="Customer name for fuzzy SGN roll-up matching, or an exact full/numeric SGN for one-account scope",
    )
    prepare_parser.add_argument("--backend", required=True)
    prepare_parser.add_argument("--output", required=True)
    prepare_parser.add_argument("--decision-pack")
    prepare_parser.add_argument("--decision-template")
    prepare_parser.add_argument("--domain", help="Known official company domain, when already verified")
    prepare_parser.add_argument("--sheet")

    finalize_parser = subparsers.add_parser("finalize", help="Resolve links, match contacts, render SVGs, cache research, and build the report")
    finalize_parser.add_argument("--pack", required=True)
    finalize_parser.add_argument("--decisions", help="Compact model-authored decisions payload")
    finalize_parser.add_argument("--spec", help="Legacy v1.2 full report specification")
    finalize_parser.add_argument("--output-dir", required=True)
    finalize_parser.add_argument("--report-output")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "prepare":
            return prepare(args)
        if args.command == "finalize":
            return finalize(args)
    except Exception as exc:
        try:
            if args.command == "prepare":
                backend = Path(args.backend).expanduser().resolve()
                state_path = backend / "current-run.json"
                history_path = backend / "run-history.jsonl"
            else:
                pack = load_json(Path(args.pack).expanduser().resolve())
                state_path = Path(pack["paths"]["metrics_state"]).resolve()
                history_path = Path(pack["paths"]["metrics_history"]).resolve()
            if state_path.is_file():
                state = run_metrics.load_state(state_path)
                if not state.get("finished_at"):
                    for phase, phase_state in state.get("phases", {}).items():
                        if phase_state.get("active_started_epoch") is not None:
                            run_metrics.stop_phase(state_path, phase)
                    run_metrics.mark(state_path, "run_failed", "true")
                    run_metrics.finish(state_path, history_path)
        except Exception:
            pass
        print(f"ProspectPro account-pack pipeline failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
