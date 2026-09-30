#!/usr/bin/env python3
"""Match qualified ProspectPro gaps to verified contacts using explicit evidence tags."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


TECHNICAL_ROLE_TERMS = {
    "scientist", "research", "development", "assay", "biology", "biologist", "immunology",
    "genomics", "proteomics", "cell", "molecular", "translational", "bioanalytical", "process",
}
COMMERCIAL_ROLE_TERMS = {
    "procurement", "purchasing", "sourcing", "buyer", "operations", "lab manager", "laboratory manager",
}
GENERIC_EXECUTIVE_TERMS = {"chief executive", "ceo", "president", "founder", "board"}


def normalize_phrase(value: Any) -> str:
    text = re.sub(r"[^a-z0-9]+", " ", str(value or "").lower())
    return re.sub(r"\s+", " ", text).strip()


def normalized_set(values: Any) -> set[str]:
    if not isinstance(values, list):
        return set()
    return {normalize_phrase(value) for value in values if normalize_phrase(value)}


def tokens(value: Any) -> set[str]:
    return {term for term in normalize_phrase(value).split() if len(term) > 2}


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def validate_payload(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    gaps = payload.get("gaps")
    contacts = payload.get("contacts")
    if not isinstance(gaps, list) or not isinstance(contacts, list):
        raise ValueError("Input must contain gaps and contacts arrays.")
    for gap in gaps:
        if not gap.get("id") or not gap.get("name"):
            raise ValueError("Every gap needs an id and name.")
    for contact in contacts:
        if not contact.get("id") or not contact.get("name"):
            raise ValueError("Every contact needs an id and name.")
    return gaps, contacts


def match_one(gap: dict[str, Any], contact: dict[str, Any]) -> dict[str, Any] | None:
    if contact.get("current_employer_verified") is not True:
        return None

    gap_workflows = normalized_set(gap.get("workflows", []))
    gap_techniques = normalized_set(gap.get("techniques", []))
    gap_keywords = normalized_set(gap.get("keywords", []))
    contact_workflows = normalized_set(contact.get("workflows", []))
    contact_techniques = normalized_set(contact.get("techniques", []))
    contact_keywords = normalized_set(contact.get("keywords", []))

    workflow_matches = sorted(gap_workflows & contact_workflows)
    technique_matches = sorted(gap_techniques & contact_techniques)
    keyword_matches = sorted(gap_keywords & contact_keywords)
    role_text = normalize_phrase(f"{contact.get('current_role', '')} {contact.get('team', '')}")
    role_tokens = tokens(role_text)
    scientific_role = bool(role_tokens & TECHNICAL_ROLE_TERMS)
    commercial_role = any(term in role_text for term in COMMERCIAL_ROLE_TERMS)
    generic_executive = any(term in role_text for term in GENERIC_EXECUTIVE_TERMS)

    score = 4 * len(workflow_matches) + 3 * len(technique_matches) + len(keyword_matches)
    match_type = "technical" if workflow_matches or technique_matches else None
    reasons = []
    if workflow_matches:
        reasons.append("workflow: " + ", ".join(workflow_matches))
    if technique_matches:
        reasons.append("technique: " + ", ".join(technique_matches))
    if keyword_matches:
        reasons.append("topic: " + ", ".join(keyword_matches[:3]))

    if scientific_role and (workflow_matches or technique_matches or keyword_matches):
        score += 2
    if commercial_role:
        score += 2
        if match_type is None:
            match_type = "commercial"
        reasons.append("purchasing or lab-operations path")
    relationship = normalize_phrase(contact.get("relationship_strength"))
    if relationship == "active":
        score += 2
        reasons.append("active relationship")
    elif relationship == "known":
        score += 1
        reasons.append("known relationship")

    if generic_executive and not (workflow_matches or technique_matches):
        return None
    if match_type is None or score < 3:
        return None

    return {
        "gap_id": gap["id"],
        "gap_name": gap["name"],
        "contact_id": contact["id"],
        "contact_name": contact["name"],
        "current_role": contact.get("current_role"),
        "team": contact.get("team"),
        "verified_email": contact.get("verified_email") or None,
        "match_type": match_type,
        "match_score": score,
        "match_reasons": reasons,
        "source_ids": contact.get("source_ids", []),
    }


def analyze(payload: dict[str, Any], max_contacts_per_gap: int) -> dict[str, Any]:
    gaps, contacts = validate_payload(payload)
    matches = []
    unmatched_gaps = []
    for gap in sorted(gaps, key=lambda item: (item.get("priority", 999), item["name"])):
        gap_matches = [match for contact in contacts if (match := match_one(gap, contact))]
        gap_matches.sort(key=lambda item: (-item["match_score"], item["contact_name"].lower()))
        if gap_matches:
            matches.extend(gap_matches[:max_contacts_per_gap])
        else:
            unmatched_gaps.append({"gap_id": gap["id"], "gap_name": gap["name"]})

    contacts_by_id = {contact["id"]: contact for contact in contacts}
    consolidated = {}
    for match in matches:
        row = consolidated.setdefault(
            match["contact_id"],
            {
                "contact_id": match["contact_id"],
                "contact_name": match["contact_name"],
                "current_role": match["current_role"],
                "team": match["team"],
                "verified_email": match["verified_email"],
                "matched_gaps": [],
                "best_match_score": 0,
                "source_ids": contacts_by_id[match["contact_id"]].get("source_ids", []),
            },
        )
        row["matched_gaps"].append({"gap_id": match["gap_id"], "gap_name": match["gap_name"]})
        row["best_match_score"] = max(row["best_match_score"], match["match_score"])

    contact_rows = sorted(
        consolidated.values(),
        key=lambda item: (-item["best_match_score"], item["contact_name"].lower()),
    )
    return {
        "gap_matches": matches,
        "contacts_for_report": contact_rows,
        "unmatched_gaps": unmatched_gaps,
        "rules": {
            "verified_current_employer_required": True,
            "guessed_email_allowed": False,
            "generic_executive_without_workflow_evidence_excluded": True,
            "note": "Scores rank explicit evidence overlap; they do not prove buying authority or product ownership.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="JSON containing qualified gaps and verified contacts")
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-contacts-per-gap", type=int, default=2)
    args = parser.parse_args()
    try:
        if args.max_contacts_per_gap < 1:
            raise ValueError("--max-contacts-per-gap must be at least 1.")
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        result = analyze(payload, args.max_contacts_per_gap)
        atomic_write(Path(args.output), result)
    except Exception as exc:
        print(f"ProspectPro gap-to-contact matching failed: {exc}", file=sys.stderr)
        return 2
    print(
        f"Matched {len(result['gap_matches'])} gap-contact pairs across "
        f"{len(result['contacts_for_report'])} verified contacts."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
