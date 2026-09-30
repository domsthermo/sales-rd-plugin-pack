#!/usr/bin/env python3
"""Maintain and query ProspectPro's verified Thermo Fisher product-link library."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


SCHEMA_VERSION = 1
DEFAULT_SEED = Path(__file__).resolve().parent.parent / "references" / "thermo-product-links.json"
CURATED_COLLECTION = "prospectpro-top-50-biology-rnd"
CURATED_ENTRY_COUNT = 50
EXCLUDED_SCOPE_TERMS = (
    "chemical",
    "chemicals",
    "chromatography",
    "mass spec",
    "mass spectrometry",
)


def today_iso() -> str:
    return date.today().isoformat()


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def canonical_url(raw_url: str) -> str:
    parsed = urlsplit(raw_url.strip())
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not (host == "thermofisher.com" or host.endswith(".thermofisher.com")):
        raise ValueError("Product links must be HTTPS URLs on an official thermofisher.com domain.")
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError("Product links cannot contain credentials or a nonstandard port.")
    path = re.sub(r"/{2,}", "/", parsed.path).rstrip("/") or "/"
    return urlunsplit(("https", host, path, "", ""))


def stable_id(name: str, url: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:48]
    suffix = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
    return f"{slug}-{suffix}" if slug else suffix


def validate_entry(entry: dict[str, Any]) -> dict[str, Any]:
    required = ("name", "category", "specificity", "url", "status", "verified_at", "verified_title", "verification_method")
    missing = [field for field in required if not str(entry.get(field, "")).strip()]
    if missing:
        raise ValueError(f"Product-link entry is missing: {', '.join(missing)}")
    if entry["status"] != "verified":
        raise ValueError("Only status=verified entries may be stored in this library.")
    if entry["verification_method"] not in {"official-page-opened", "official-product-page-opened"}:
        raise ValueError("Verification method must document that the official page was opened.")
    datetime.strptime(entry["verified_at"], "%Y-%m-%d")
    entry = dict(entry)
    entry["url"] = canonical_url(entry["url"])
    entry["id"] = str(entry.get("id") or stable_id(entry["name"], entry["url"]))
    entry["keywords"] = sorted({str(value).strip().lower() for value in entry.get("keywords", []) if str(value).strip()})
    scope_text = " ".join(
        [str(entry["name"]), str(entry["category"]), str(entry["verified_title"]), *entry["keywords"]]
    ).lower()
    excluded = [term for term in EXCLUDED_SCOPE_TERMS if term in scope_text]
    if excluded:
        raise ValueError(
            "Product-link entry falls outside ProspectPro's biological R&D scope: "
            + ", ".join(sorted(set(excluded)))
        )
    return entry


def load_library(path: Path, allow_missing: bool = False) -> dict[str, Any]:
    if not path.exists():
        if allow_missing:
            return {"schema_version": SCHEMA_VERSION, "updated_at": None, "entries": []}
        raise ValueError(f"Library not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != SCHEMA_VERSION or not isinstance(data.get("entries"), list):
        raise ValueError(f"Unsupported product-link library schema: {path}")
    data["entries"] = [validate_entry(entry) for entry in data["entries"]]
    return data


def merge_entries(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_url = {entry["url"]: entry for entry in (validate_entry(item) for item in existing)}
    for candidate in (validate_entry(item) for item in incoming):
        current = by_url.get(candidate["url"])
        if current is None or candidate["verified_at"] >= current["verified_at"]:
            by_url[candidate["url"]] = candidate
    return sorted(by_url.values(), key=lambda item: (item["category"], item["name"].lower()))


def save_library(path: Path, entries: list[dict[str, Any]]) -> None:
    atomic_write(
        path,
        {
            "schema_version": SCHEMA_VERSION,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "entries": entries,
        },
    )


def initialize(library_path: Path, seed_path: Path) -> int:
    raw_seed = json.loads(seed_path.read_text(encoding="utf-8"))
    if raw_seed.get("collection") == CURATED_COLLECTION:
        if raw_seed.get("entry_count") != CURATED_ENTRY_COUNT or len(raw_seed.get("entries", [])) != CURATED_ENTRY_COUNT:
            raise ValueError(f"The packaged biology/R&D seed must contain exactly {CURATED_ENTRY_COUNT} entries.")
        excluded_scope = {str(value).lower() for value in raw_seed.get("scope", {}).get("excluded", [])}
        required_exclusions = {"chemicals", "chromatography", "mass spectrometry"}
        if excluded_scope != required_exclusions:
            raise ValueError("The packaged seed must explicitly exclude chemicals, chromatography, and mass spectrometry.")
    seed = load_library(seed_path)
    library = load_library(library_path, allow_missing=True)
    merged = merge_entries(library["entries"], seed["entries"])
    save_library(library_path, merged)
    print(f"Product-link library ready with {len(merged)} verified entries.")
    return 0


def search(library_path: Path, query: str, max_results: int, max_age_days: int) -> int:
    library = load_library(library_path)
    tokens = {token for token in re.findall(r"[a-z0-9]+", query.lower()) if len(token) > 1}
    cutoff = date.today() - timedelta(days=max_age_days)
    results = []
    for entry in library["entries"]:
        haystack = " ".join(
            [entry["name"], entry["category"], entry["specificity"], *entry.get("keywords", [])]
        ).lower()
        name_tokens = set(re.findall(r"[a-z0-9]+", entry["name"].lower()))
        haystack_tokens = set(re.findall(r"[a-z0-9]+", haystack))
        score = sum(3 if token in name_tokens else 1 for token in tokens if token in haystack_tokens)
        if query.strip().lower() in entry["name"].lower():
            score += 6
        if query.strip() and score == 0:
            continue
        verified = datetime.strptime(entry["verified_at"], "%Y-%m-%d").date()
        results.append({**entry, "match_score": score, "stale": verified < cutoff})
    results.sort(key=lambda item: (-item["match_score"], item["stale"], item["name"].lower()))
    print(json.dumps(results[:max_results], indent=2, ensure_ascii=False))
    return 0


def upsert(library_path: Path, args: argparse.Namespace) -> int:
    library = load_library(library_path, allow_missing=True)
    entry = validate_entry(
        {
            "id": args.id,
            "name": args.name,
            "category": args.category,
            "specificity": args.specificity,
            "url": args.url,
            "keywords": [part.strip() for part in args.keywords.split(",") if part.strip()],
            "status": "verified",
            "verified_at": args.verified_at,
            "verified_title": args.verified_title,
            "verification_method": args.verification_method,
        }
    )
    entries = merge_entries(library["entries"], [entry])
    save_library(library_path, entries)
    print(f"Stored verified link: {entry['name']} ({entry['url']})")
    return 0


def stale(library_path: Path, max_age_days: int) -> int:
    library = load_library(library_path)
    cutoff = date.today() - timedelta(days=max_age_days)
    entries = [
        entry
        for entry in library["entries"]
        if datetime.strptime(entry["verified_at"], "%Y-%m-%d").date() < cutoff
    ]
    print(json.dumps(entries, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create or refresh a backend library from the packaged seed")
    init_parser.add_argument("--library", required=True)
    init_parser.add_argument("--seed", default=str(DEFAULT_SEED))

    search_parser = subparsers.add_parser("search", help="Search verified entries before browsing")
    search_parser.add_argument("--library", required=True)
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--max-results", type=int, default=5)
    search_parser.add_argument("--max-age-days", type=int, default=180)

    upsert_parser = subparsers.add_parser("upsert", help="Add a link after opening and verifying the official page")
    upsert_parser.add_argument("--library", required=True)
    upsert_parser.add_argument("--id")
    upsert_parser.add_argument("--name", required=True)
    upsert_parser.add_argument("--category", required=True)
    upsert_parser.add_argument("--specificity", choices=("portfolio", "workflow", "product-family", "product"), required=True)
    upsert_parser.add_argument("--url", required=True)
    upsert_parser.add_argument("--keywords", default="")
    upsert_parser.add_argument("--verified-at", default=today_iso())
    upsert_parser.add_argument("--verified-title", required=True)
    upsert_parser.add_argument(
        "--verification-method",
        choices=("official-page-opened", "official-product-page-opened"),
        default="official-page-opened",
    )

    stale_parser = subparsers.add_parser("stale", help="List entries that need re-verification")
    stale_parser.add_argument("--library", required=True)
    stale_parser.add_argument("--max-age-days", type=int, default=180)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        library = Path(args.library).expanduser().resolve()
        if args.command == "init":
            return initialize(library, Path(args.seed).expanduser().resolve())
        if args.command == "search":
            return search(library, args.query, args.max_results, args.max_age_days)
        if args.command == "upsert":
            return upsert(library, args)
        if args.command == "stale":
            return stale(library, args.max_age_days)
    except Exception as exc:
        print(f"ProspectPro product-link library failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
