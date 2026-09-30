#!/usr/bin/env python3
"""Record private ProspectPro phase timing and summarize historical bottlenecks."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
PHASES = (
    "intake",
    "workbook",
    "research_and_decisions",
    "company_research",
    "science_research",
    "outlook",
    "gap_analysis",
    "product_links",
    "contacts",
    "svg",
    "report",
)
SAFE_METRICS = {
    "workbook_cache_hit": "bool",
    "research_core_cache_hit": "bool",
    "research_contacts_cache_hit": "bool",
    "product_link_library_hits": "int",
    "product_link_web_searches": "int",
    "style_profile_reused": "bool",
    "outlook_threads_opened": "int",
    "web_batches": "int",
    "outlook_search_batches": "int",
    "outlook_messages_fetched": "int",
    "run_failed": "bool",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def load_state(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"Timing state not found: {path}")
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported timing-state schema.")
    return state


def begin(path: Path) -> int:
    if path.exists():
        previous = load_state(path)
        if not previous.get("finished_at"):
            raise ValueError("An unfinished timing run already uses this state path.")
    epoch = time.time()
    atomic_write(
        path,
        {
            "schema_version": SCHEMA_VERSION,
            "run_id": str(uuid.uuid4()),
            "started_at": now_iso(),
            "started_epoch": epoch,
            "finished_at": None,
            "total_duration_seconds": None,
            "phases": {},
            "metrics": {},
        },
    )
    print(f"Started ProspectPro timing run at {path}.")
    return 0


def start_phase(path: Path, phase: str) -> int:
    state = load_state(path)
    if state.get("finished_at"):
        raise ValueError("The timing run is already finished.")
    phase_state = state["phases"].setdefault(phase, {"duration_seconds": 0.0, "segments": []})
    if phase_state.get("active_started_epoch") is not None:
        raise ValueError(f"Phase is already active: {phase}")
    phase_state["active_started_at"] = now_iso()
    phase_state["active_started_epoch"] = time.time()
    atomic_write(path, state)
    print(f"Started phase: {phase}")
    return 0


def stop_phase(path: Path, phase: str) -> int:
    state = load_state(path)
    phase_state = state["phases"].get(phase)
    if not phase_state or phase_state.get("active_started_epoch") is None:
        raise ValueError(f"Phase is not active: {phase}")
    stopped_epoch = time.time()
    duration = max(0.0, stopped_epoch - float(phase_state.pop("active_started_epoch")))
    started_at = phase_state.pop("active_started_at")
    phase_state["duration_seconds"] = round(float(phase_state.get("duration_seconds", 0.0)) + duration, 3)
    phase_state["segments"].append(
        {
            "started_at": started_at,
            "stopped_at": now_iso(),
            "duration_seconds": round(duration, 3),
        }
    )
    atomic_write(path, state)
    print(f"Stopped phase: {phase} ({duration:.3f}s)")
    return 0


def parse_metric(key: str, value: str) -> bool | int:
    metric_type = SAFE_METRICS[key]
    if metric_type == "bool":
        normalized = value.strip().lower()
        if normalized not in {"true", "false"}:
            raise ValueError(f"{key} must be true or false.")
        return normalized == "true"
    parsed = int(value)
    if parsed < 0:
        raise ValueError(f"{key} cannot be negative.")
    return parsed


def mark(path: Path, key: str, value: str) -> int:
    state = load_state(path)
    if state.get("finished_at"):
        raise ValueError("The timing run is already finished.")
    state["metrics"][key] = parse_metric(key, value)
    atomic_write(path, state)
    print(f"Recorded metric: {key}")
    return 0


def append_history(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(existing + json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def finish(path: Path, history: Path | None) -> int:
    state = load_state(path)
    if state.get("finished_at"):
        raise ValueError("The timing run is already finished.")
    active = [name for name, phase in state["phases"].items() if phase.get("active_started_epoch") is not None]
    if active:
        raise ValueError(f"Stop active phases before finishing: {', '.join(active)}")
    state["finished_at"] = now_iso()
    state["total_duration_seconds"] = round(max(0.0, time.time() - float(state["started_epoch"])), 3)
    atomic_write(path, state)
    if history:
        record = {
            "schema_version": SCHEMA_VERSION,
            "run_id": state["run_id"],
            "started_at": state["started_at"],
            "finished_at": state["finished_at"],
            "total_duration_seconds": state["total_duration_seconds"],
            "phase_duration_seconds": {
                name: phase["duration_seconds"] for name, phase in state["phases"].items()
            },
            "metrics": state["metrics"],
        }
        append_history(history, record)
    print(f"Finished ProspectPro timing run ({state['total_duration_seconds']:.3f}s).")
    return 0


def summarize(history: Path) -> int:
    if not history.is_file():
        raise ValueError(f"Timing history not found: {history}")
    records = [json.loads(line) for line in history.read_text(encoding="utf-8").splitlines() if line.strip()]
    phase_values: dict[str, list[float]] = {phase: [] for phase in PHASES}
    totals = []
    for record in records:
        totals.append(float(record.get("total_duration_seconds", 0.0)))
        for phase, value in record.get("phase_duration_seconds", {}).items():
            if phase in phase_values:
                phase_values[phase].append(float(value))
    summary = {
        "run_count": len(records),
        "total_duration_seconds": {
            "average": round(statistics.mean(totals), 3) if totals else None,
            "median": round(statistics.median(totals), 3) if totals else None,
            "maximum": round(max(totals), 3) if totals else None,
        },
        "phases": {},
    }
    for phase, values in phase_values.items():
        if values:
            summary["phases"][phase] = {
                "run_count": len(values),
                "average_seconds": round(statistics.mean(values), 3),
                "median_seconds": round(statistics.median(values), 3),
                "maximum_seconds": round(max(values), 3),
            }
    summary["phases"] = dict(
        sorted(summary["phases"].items(), key=lambda item: item[1]["average_seconds"], reverse=True)
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    begin_parser = subparsers.add_parser("begin")
    begin_parser.add_argument("--state", required=True)

    start_parser = subparsers.add_parser("start")
    start_parser.add_argument("--state", required=True)
    start_parser.add_argument("--phase", choices=PHASES, required=True)

    stop_parser = subparsers.add_parser("stop")
    stop_parser.add_argument("--state", required=True)
    stop_parser.add_argument("--phase", choices=PHASES, required=True)

    mark_parser = subparsers.add_parser("mark")
    mark_parser.add_argument("--state", required=True)
    mark_parser.add_argument("--key", choices=tuple(SAFE_METRICS), required=True)
    mark_parser.add_argument("--value", required=True)

    finish_parser = subparsers.add_parser("finish")
    finish_parser.add_argument("--state", required=True)
    finish_parser.add_argument("--history")

    summary_parser = subparsers.add_parser("summary")
    summary_parser.add_argument("--history", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "begin":
            return begin(Path(args.state).expanduser().resolve())
        if args.command == "start":
            return start_phase(Path(args.state).expanduser().resolve(), args.phase)
        if args.command == "stop":
            return stop_phase(Path(args.state).expanduser().resolve(), args.phase)
        if args.command == "mark":
            return mark(Path(args.state).expanduser().resolve(), args.key, args.value)
        if args.command == "finish":
            history = Path(args.history).expanduser().resolve() if args.history else None
            return finish(Path(args.state).expanduser().resolve(), history)
        if args.command == "summary":
            return summarize(Path(args.history).expanduser().resolve())
    except Exception as exc:
        print(f"ProspectPro timing failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
