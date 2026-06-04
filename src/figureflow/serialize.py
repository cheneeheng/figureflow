"""Serialization helpers for figureflow: to_json / from_json / to_mermaid."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from figureflow import Flow

_SCHEMA = "figureflow/1"

_MERMAID_SHAPE: Dict[str, str] = {
    "rectangle": "[{label}]",
    "rounded": "({label})",
    "stadium": "([{label}])",
    "diamond": "{{{label}}}",
    "hexagon": "{{{{{label}}}}}",
    "parallelogram": "[/{label}/]",
    "cylinder": "[({label})]",
    "ellipse": "({label})",  # nearest mermaid equivalent
}


def to_json(flow: "Flow") -> str:
    envelope = {
        "schema": _SCHEMA,
        "color_mode": flow.color_mode,
        "fit_view": flow.fit_view,
        "height": flow.height,
        "nodes": list(flow.nodes),
        "edges": list(flow.edges),
    }
    return json.dumps(envelope)


def from_json(s: str) -> "Flow":
    from figureflow import Flow

    data = json.loads(s)
    schema = data.get("schema", "")
    major = schema.split("/")[1] if "/" in schema else ""
    if major != "1":
        raise ValueError(f"Unsupported figureflow schema '{schema}'; expected 'figureflow/1'")

    flow = Flow(
        color_mode=data.get("color_mode", "light"),
        fit_view=data.get("fit_view", True),
        height=data.get("height", 480),
    )
    # Stored dicts are already in channel form — assign directly.
    flow.nodes = list(data.get("nodes", []))
    flow.edges = list(data.get("edges", []))
    return flow


def to_mermaid(flow: "Flow", direction: str = "TB") -> str:
    lines: List[str] = [
        "%% figureflow export — structural only; per-element colors/fonts are not preserved",
        f"flowchart {direction}",
    ]

    for n in flow.nodes:
        nid = n["id"].replace("-", "_")
        data = n.get("data", {})
        label = data.get("label", n["id"])
        shape = data.get("shape", "rectangle")
        tmpl = _MERMAID_SHAPE.get(shape, "[{label}]")
        node_line = f"    {nid}{tmpl.format(label=label)}"
        lines.append(node_line)

    for e in flow.edges:
        src = e["source"].replace("-", "_")
        tgt = e["target"].replace("-", "_")
        label = e.get("label", "")
        style = e.get("style", {})
        dash = style.get("strokeDasharray")
        arrow = "-->" if not dash else "-.->"
        if label:
            lines.append(f"    {src} {arrow}|\"{label}\"| {tgt}")
        else:
            lines.append(f"    {src} {arrow} {tgt}")

    return "\n".join(lines)
