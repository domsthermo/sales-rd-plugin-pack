#!/usr/bin/env python3
"""Render an adaptive ProspectPro lane-and-bubble SVG from a JSON specification."""

from __future__ import annotations

import argparse
import html
import json
import math
import textwrap
from pathlib import Path
from typing import Any


PALETTE = {
    "observed": {"fill": "#E8F5E9", "stroke": "#2E7D32", "label": "Observed purchase"},
    "inferred": {"fill": "#E3F2FD", "stroke": "#1565C0", "label": "Inferred from public science"},
    "opportunity": {"fill": "#FFF3E0", "stroke": "#EF6C00", "label": "Pitch / validate"},
    "neutral": {"fill": "#F4F5F7", "stroke": "#5F6B7A", "label": "Context"},
}

NODE_WIDTH = 230
NODE_HEIGHT = 112
NODE_GAP_X = 34
NODE_GAP_Y = 34
LABEL_WIDTH = 190
MARGIN = 34
CONTENT_TOP = 125


def wrap_lines(value: Any, width: int, maximum: int) -> list[str]:
    lines = textwrap.wrap(str(value or "").strip(), width=width, break_long_words=False, break_on_hyphens=False)
    if len(lines) > maximum:
        lines = lines[:maximum]
        lines[-1] = lines[-1].rstrip(" .") + "…"
    return lines


def validate_spec(spec: dict[str, Any]) -> None:
    if not isinstance(spec.get("lanes"), list) or not spec["lanes"]:
        raise ValueError("The SVG specification needs at least one lane.")
    identifiers: set[str] = set()
    for lane_index, lane in enumerate(spec["lanes"], start=1):
        if not isinstance(lane.get("nodes"), list) or not lane["nodes"]:
            raise ValueError(f"Lane {lane_index} needs at least one node.")
        for node in lane["nodes"]:
            identifier = str(node.get("id", "")).strip()
            if not identifier:
                raise ValueError("Every node needs a stable id.")
            if identifier in identifiers:
                raise ValueError(f"Duplicate node id: {identifier}")
            identifiers.add(identifier)
            if not str(node.get("title", "")).strip():
                raise ValueError(f"Node {identifier} needs a title.")
            status = node.get("status", "neutral")
            if status not in PALETTE:
                raise ValueError(f"Node {identifier} has unsupported status: {status}")
    for link in spec.get("links", []):
        if link.get("from") not in identifiers or link.get("to") not in identifiers:
            raise ValueError(f"Link references an unknown node: {link}")


def render(spec: dict[str, Any]) -> str:
    validate_spec(spec)
    lane_layouts = []
    canvas_width = 960
    current_y = CONTENT_TOP

    for lane in spec["lanes"]:
        nodes = lane["nodes"]
        requested_columns = lane.get("columns")
        columns = int(requested_columns) if requested_columns else min(4, max(1, len(nodes)))
        columns = max(1, min(columns, len(nodes)))
        rows = math.ceil(len(nodes) / columns)
        lane_height = rows * NODE_HEIGHT + max(0, rows - 1) * NODE_GAP_Y + 52
        lane_width = LABEL_WIDTH + columns * NODE_WIDTH + max(0, columns - 1) * NODE_GAP_X + MARGIN * 2
        canvas_width = max(canvas_width, lane_width)
        lane_layouts.append({"lane": lane, "columns": columns, "rows": rows, "y": current_y, "height": lane_height})
        current_y += lane_height + 24

    used_statuses = []
    for layout in lane_layouts:
        for node in layout["lane"]["nodes"]:
            status = node.get("status", "neutral")
            if status not in used_statuses:
                used_statuses.append(status)
    legend_height = 42 if used_statuses else 0
    canvas_height = current_y + legend_height + 24

    node_positions: dict[str, dict[str, float]] = {}
    for layout in lane_layouts:
        for index, node in enumerate(layout["lane"]["nodes"]):
            column = index % layout["columns"]
            row = index // layout["columns"]
            x = MARGIN + LABEL_WIDTH + column * (NODE_WIDTH + NODE_GAP_X)
            y = layout["y"] + 30 + row * (NODE_HEIGHT + NODE_GAP_Y)
            node_positions[node["id"]] = {"x": x, "y": y, "w": NODE_WIDTH, "h": NODE_HEIGHT}

    links = list(spec.get("links", []))
    for layout in lane_layouts:
        lane = layout["lane"]
        if lane.get("connect", True):
            for first, second in zip(lane["nodes"], lane["nodes"][1:]):
                pair = {"from": first["id"], "to": second["id"]}
                if pair not in links:
                    links.append(pair)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" viewBox="0 0 {canvas_width} {canvas_height}" width="100%" height="auto">',
        f"<title>{html.escape(str(spec.get('title', 'ProspectPro map')))}</title>",
        f"<desc>{html.escape(str(spec.get('description', 'Customer-specific technique and workflow map.')))}</desc>",
        "<defs>",
        '<marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#637083"/></marker>',
        '<filter id="shadow" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#172B4D" flood-opacity="0.12"/></filter>',
        "</defs>",
        f'<rect width="{canvas_width}" height="{canvas_height}" fill="#FFFFFF"/>',
        f'<text x="{MARGIN}" y="45" font-family="Arial, sans-serif" font-size="26" font-weight="700" fill="#172B4D">{html.escape(str(spec.get("title", "ProspectPro map")))}</text>',
    ]

    subtitle = str(spec.get("subtitle", "")).strip()
    if subtitle:
        parts.append(f'<text x="{MARGIN}" y="73" font-family="Arial, sans-serif" font-size="14" fill="#5F6B7A">{html.escape(subtitle)}</text>')

    legend_x = MARGIN
    for status in used_statuses:
        palette = PALETTE[status]
        parts.append(f'<rect x="{legend_x}" y="88" width="18" height="18" rx="5" fill="{palette["fill"]}" stroke="{palette["stroke"]}" stroke-width="2"/>')
        parts.append(f'<text x="{legend_x + 26}" y="102" font-family="Arial, sans-serif" font-size="12" fill="#344563">{html.escape(palette["label"])}</text>')
        legend_x += 26 + len(palette["label"]) * 7 + 24

    for layout in lane_layouts:
        lane = layout["lane"]
        y = layout["y"]
        parts.append(f'<rect x="{MARGIN}" y="{y}" width="{canvas_width - MARGIN * 2}" height="{layout["height"]}" rx="16" fill="#FAFBFC" stroke="#DFE1E6"/>')
        lane_lines = wrap_lines(lane.get("label", "Lane"), 18, 3)
        for index, line in enumerate(lane_lines):
            parts.append(f'<text x="{MARGIN + 18}" y="{y + 42 + index * 20}" font-family="Arial, sans-serif" font-size="16" font-weight="700" fill="#172B4D">{html.escape(line)}</text>')

    for link in links:
        source = node_positions[link["from"]]
        target = node_positions[link["to"]]
        sx = source["x"] + source["w"]
        sy = source["y"] + source["h"] / 2
        tx = target["x"]
        ty = target["y"] + target["h"] / 2
        if tx > sx and abs(ty - sy) < NODE_HEIGHT:
            control = max(28, (tx - sx) / 2)
            path = f"M {sx} {sy} C {sx + control} {sy}, {tx - control} {ty}, {tx} {ty}"
        else:
            sx = source["x"] + source["w"] / 2
            sy = source["y"] + source["h"]
            tx = target["x"] + target["w"] / 2
            ty = target["y"]
            middle = (sy + ty) / 2
            path = f"M {sx} {sy} C {sx} {middle}, {tx} {middle}, {tx} {ty}"
        parts.append(f'<path d="{path}" fill="none" stroke="#637083" stroke-width="2" marker-end="url(#arrow)"/>')

    for layout in lane_layouts:
        for node in layout["lane"]["nodes"]:
            position = node_positions[node["id"]]
            palette = PALETTE[node.get("status", "neutral")]
            parts.append(
                f'<rect x="{position["x"]}" y="{position["y"]}" width="{position["w"]}" height="{position["h"]}" '
                f'rx="22" fill="{palette["fill"]}" stroke="{palette["stroke"]}" stroke-width="2.5" filter="url(#shadow)"/>'
            )
            title_lines = wrap_lines(node["title"], 24, 2)
            subtitle_lines = wrap_lines(node.get("subtitle", ""), 34, 3)
            text_y = position["y"] + 31
            for index, line in enumerate(title_lines):
                parts.append(f'<text x="{position["x"] + 16}" y="{text_y + index * 18}" font-family="Arial, sans-serif" font-size="15" font-weight="700" fill="#172B4D">{html.escape(line)}</text>')
            subtitle_y = text_y + len(title_lines) * 18 + 8
            for index, line in enumerate(subtitle_lines):
                parts.append(f'<text x="{position["x"] + 16}" y="{subtitle_y + index * 16}" font-family="Arial, sans-serif" font-size="12" fill="#344563">{html.escape(line)}</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", help="Path to the JSON map specification")
    parser.add_argument("output", help="Path for the rendered SVG")
    args = parser.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(spec), encoding="utf-8")
    print(f"Rendered {sum(len(lane['nodes']) for lane in spec['lanes'])} nodes to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
