"""Serialization + the shared ingestion funnel for figureflow.

Public surface: ``to_json`` / ``from_json`` / ``to_mermaid`` (the wire format,
ITER_05) plus the v3 ``validate`` funnel and ``FlowValidationError``.

Error-message contract (the LLM-repair-loop style rule)
-------------------------------------------------------
Every problem — hard error or warning — is rendered as **one line**::

    <json-path>: <what is wrong>. <hint with valid alternatives>

e.g. ``nodes[3].shape: 'circle' is not a valid shape. Use one of: rectangle,
rounded, stadium, ellipse, diamond, parallelogram, hexagon, cylinder (closest
match: ellipse).`` Closest-match suggestions come from :mod:`difflib`.

:func:`validate` **collects** every problem and raises them together in a single
:class:`FlowValidationError` rather than failing on the first, so an LLM repair
loop can fix ten faults in one round-trip. It is the single funnel every
ingestion path (JSON here; mermaid and MCP inputs later) routes through.
"""
from __future__ import annotations

import difflib
import json
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

if TYPE_CHECKING:
    from figureflow import Flow

_SCHEMA = "figureflow/1"

_VALID_SHAPES: Tuple[str, ...] = (
    "rectangle",
    "rounded",
    "stadium",
    "ellipse",
    "diamond",
    "parallelogram",
    "hexagon",
    "cylinder",
)
_VALID_DIRECTIONS: Tuple[str, ...] = ("TB", "BT", "LR", "RL")

# Channel-form keys a node/edge legitimately carries at the top level. Anything
# else an author emits is folded into ``data`` (with a warning), never dropped.
_KNOWN_NODE_KEYS = frozenset(
    {
        "id",
        "type",
        "position",
        "data",
        "parentId",
        "extent",
        "selected",
        "width",
        "height",
        "style",
        "hidden",
        "draggable",
        "sourcePosition",
        "targetPosition",
        "zIndex",
    }
)
_KNOWN_EDGE_KEYS = frozenset(
    {
        "id",
        "source",
        "target",
        "type",
        "style",
        "markerStart",
        "markerEnd",
        "label",
        "labelStyle",
        "labelBgStyle",
        "labelShowBg",
        "selected",
        "animated",
        "hidden",
        "data",
        "zIndex",
        "sourceHandle",
        "targetHandle",
    }
)

# In-``data`` fields reported with a friendly flattened path (``nodes[i].shape``
# rather than ``nodes[i].data.shape``) per the error-message contract example.
_NUMERIC_DATA_KEYS = ("width", "height", "fontSize", "borderWidth")

Problem = Dict[str, str]


def _format_problem(p: Problem) -> str:
    """Render one problem dict as the single-line contract string."""
    line = f"{p['path']}: {p['message']}"
    hint = p.get("hint")
    if hint:
        line += f" {hint}"
    return line


class FlowValidationError(ValueError):
    """Raised by :func:`validate` carrying every collected problem at once.

    Attributes:
        problems: The collected ``{path, message, hint}`` dicts. ``__str__``
            renders one problem per line per the module error contract.
    """

    def __init__(self, problems: List[Problem]) -> None:
        self.problems = problems
        super().__init__("\n".join(_format_problem(p) for p in problems))

    def __str__(self) -> str:
        return "\n".join(_format_problem(p) for p in self.problems)


def _coerce_number(value: Any) -> Tuple[Any, bool, bool]:
    """Coerce a numeric-ish value.

    Returns:
        ``(coerced, ok, warned)`` — ``ok`` is ``False`` when the value is not
        numeric at all; ``warned`` is ``True`` when a numeric *string* was
        coerced (the forgiving path that earns a warning).
    """
    if isinstance(value, bool):
        return value, False, False
    if isinstance(value, (int, float)):
        return value, True, False
    if isinstance(value, str):
        try:
            num = float(value.strip())
        except ValueError:
            return value, False, False
        if num.is_integer():
            num = int(num)
        return num, True, True
    return value, False, False


def _clean_node(
    node: Dict[str, Any], path: str
) -> Tuple[Dict[str, Any], List[Problem], List[Problem]]:
    """Clean one channel-form node; return ``(clean, warnings, problems)``."""
    warnings: List[Problem] = []
    problems: List[Problem] = []
    clean: Dict[str, Any] = {}
    data: Dict[str, Any] = dict(node.get("data") or {})
    had_data = "data" in node

    for key, value in node.items():
        if key in _KNOWN_NODE_KEYS:
            clean[key] = value
        else:
            data[key] = value
            had_data = True
            warnings.append(
                {
                    "path": f"{path}.{key}",
                    "message": f"unknown node key '{key}' folded into data.",
                    "hint": "Known keys: id, type, position, data, parentId, extent.",
                }
            )

    shape = data.get("shape")
    if shape is not None and shape not in _VALID_SHAPES:
        hint = f"Use one of: {', '.join(_VALID_SHAPES)}"
        close = difflib.get_close_matches(str(shape), _VALID_SHAPES, n=1)
        if close:
            hint += f" (closest match: {close[0]})"
        hint += "."
        problems.append(
            {
                "path": f"{path}.shape",
                "message": f"'{shape}' is not a valid shape.",
                "hint": hint,
            }
        )

    for key in _NUMERIC_DATA_KEYS:
        if key in data:
            coerced, ok, warned = _coerce_number(data[key])
            if not ok:
                problems.append(
                    {
                        "path": f"{path}.{key}",
                        "message": f"'{data[key]}' is not a number.",
                        "hint": f"{key} must be numeric.",
                    }
                )
            else:
                if warned:
                    warnings.append(
                        {
                            "path": f"{path}.{key}",
                            "message": f"numeric string {data[key]!r} coerced to {coerced}.",
                            "hint": "Emit numbers without quotes.",
                        }
                    )
                data[key] = coerced

    if data or had_data:
        clean["data"] = data
    return clean, warnings, problems


def _clean_edge(
    edge: Dict[str, Any], path: str
) -> Tuple[Dict[str, Any], List[Problem]]:
    """Clean one channel-form edge; return ``(clean, warnings)``.

    Endpoint existence is checked by the caller (it needs the node-id set).
    """
    warnings: List[Problem] = []
    clean: Dict[str, Any] = {}
    data: Dict[str, Any] = dict(edge.get("data") or {})
    had_data = "data" in edge

    for key, value in edge.items():
        if key in _KNOWN_EDGE_KEYS:
            clean[key] = value
        else:
            data[key] = value
            had_data = True
            warnings.append(
                {
                    "path": f"{path}.{key}",
                    "message": f"unknown edge key '{key}' folded into data.",
                    "hint": "Known keys: id, source, target, type, style, label.",
                }
            )

    if data or had_data:
        clean["data"] = data
    return clean, warnings


def validate(
    payload: Any, *, strict: bool = False
) -> Tuple[Dict[str, Any], List[str]]:
    """Validate a ``figureflow/1`` envelope, collecting every problem.

    The single ingestion funnel: JSON (:func:`from_json`), mermaid output, and
    MCP tool inputs all route through here.

    Args:
        payload: The decoded envelope object.
        strict: When ``True``, warnings are escalated to errors.

    Returns:
        ``(clean_payload, warnings)`` — a normalized envelope and the list of
        one-line warning strings (empty when nothing was coerced or folded).

    Raises:
        FlowValidationError: With every collected hard problem (or, under
            ``strict``, every warning) rendered one per line.
    """
    problems: List[Problem] = []
    warning_dicts: List[Problem] = []

    if not isinstance(payload, dict):
        raise FlowValidationError(
            [
                {
                    "path": "$",
                    "message": (
                        f"top-level value must be an object, got "
                        f"{type(payload).__name__}."
                    ),
                    "hint": "Emit a figureflow/1 envelope object.",
                }
            ]
        )

    schema = payload.get("schema", _SCHEMA)
    if not isinstance(schema, str):
        problems.append(
            {
                "path": "schema",
                "message": "schema must be a string.",
                "hint": "Use 'figureflow/1'.",
            }
        )
    else:
        major = schema.split("/")[1] if "/" in schema else ""
        if major != "1":
            problems.append(
                {
                    "path": "schema",
                    "message": f"unsupported schema version {schema!r}.",
                    "hint": "Use 'figureflow/1'.",
                }
            )

    direction = payload.get("layout_direction", "TB")
    if direction not in _VALID_DIRECTIONS:
        problems.append(
            {
                "path": "layout_direction",
                "message": f"{direction!r} is not a valid layout direction.",
                "hint": f"Use one of: {', '.join(_VALID_DIRECTIONS)}.",
            }
        )
        direction = "TB"

    raw_nodes = payload.get("nodes", [])
    clean_nodes: List[Dict[str, Any]] = []
    node_ids: List[str] = []
    seen_ids: set[str] = set()
    if not isinstance(raw_nodes, list):
        problems.append(
            {
                "path": "nodes",
                "message": f"must be an array, got {type(raw_nodes).__name__}.",
                "hint": "Provide a list of node objects.",
            }
        )
        raw_nodes = []

    for i, node in enumerate(raw_nodes):
        path = f"nodes[{i}]"
        if not isinstance(node, dict):
            problems.append(
                {
                    "path": path,
                    "message": f"must be an object, got {type(node).__name__}.",
                    "hint": "Each node is an object with a string 'id'.",
                }
            )
            continue
        nid = node.get("id")
        if not isinstance(nid, str) or not nid:
            problems.append(
                {
                    "path": f"{path}.id",
                    "message": "missing or non-string node id.",
                    "hint": "Give every node a unique string id.",
                }
            )
        else:
            if nid in seen_ids:
                problems.append(
                    {
                        "path": f"{path}.id",
                        "message": f"duplicate node id {nid!r}.",
                        "hint": "Node ids must be unique.",
                    }
                )
            else:
                seen_ids.add(nid)
                node_ids.append(nid)
        clean, node_warnings, node_problems = _clean_node(node, path)
        warning_dicts.extend(node_warnings)
        problems.extend(node_problems)
        clean_nodes.append(clean)

    raw_edges = payload.get("edges", [])
    clean_edges: List[Dict[str, Any]] = []
    if not isinstance(raw_edges, list):
        problems.append(
            {
                "path": "edges",
                "message": f"must be an array, got {type(raw_edges).__name__}.",
                "hint": "Provide a list of edge objects.",
            }
        )
        raw_edges = []

    known_ids = set(node_ids)
    if len(node_ids) <= 20 and node_ids:
        id_hint = f"Known node ids: {', '.join(node_ids)}."
    else:
        id_hint = "Reference an existing node id."

    for i, edge in enumerate(raw_edges):
        path = f"edges[{i}]"
        if not isinstance(edge, dict):
            problems.append(
                {
                    "path": path,
                    "message": f"must be an object, got {type(edge).__name__}.",
                    "hint": "Each edge has a 'source' and a 'target'.",
                }
            )
            continue
        for end in ("source", "target"):
            value = edge.get(end)
            if not isinstance(value, str) or not value:
                problems.append(
                    {
                        "path": f"{path}.{end}",
                        "message": f"missing or non-string edge {end}.",
                        "hint": id_hint,
                    }
                )
            elif value not in known_ids:
                problems.append(
                    {
                        "path": f"{path}.{end}",
                        "message": f"{end} {value!r} names no node.",
                        "hint": id_hint,
                    }
                )
        clean, edge_warnings = _clean_edge(edge, path)
        warning_dicts.extend(edge_warnings)
        clean_edges.append(clean)

    if problems:
        raise FlowValidationError(problems)
    if strict and warning_dicts:
        raise FlowValidationError(warning_dicts)

    clean_payload: Dict[str, Any] = {
        "schema": _SCHEMA,
        "color_mode": payload.get("color_mode", "light"),
        "fit_view": payload.get("fit_view", True),
        "height": payload.get("height", 480),
        "layout_direction": direction,
        "nodes": clean_nodes,
        "edges": clean_edges,
    }
    return clean_payload, [_format_problem(w) for w in warning_dicts]


def to_json(flow: "Flow") -> str:
    """Lossless JSON snapshot of the whole diagram (the ``figureflow/1`` envelope)."""
    envelope = {
        "schema": _SCHEMA,
        "color_mode": flow.color_mode,
        "fit_view": flow.fit_view,
        "height": flow.height,
        "layout_direction": flow.layout_direction,
        "nodes": list(flow.nodes),
        "edges": list(flow.edges),
    }
    return json.dumps(envelope)


def from_json(s: str, *, strict: bool = False) -> "Flow":
    """Rebuild a diagram from a ``figureflow/1`` envelope.

    Routes through :func:`validate`: every problem in a malformed document comes
    back in one :class:`FlowValidationError`. Collected warnings are attached to
    the returned flow as ``_import_warnings``.

    Args:
        s: The JSON envelope text.
        strict: When ``True``, forgiving coercions/foldings become errors.

    Returns:
        The reconstructed :class:`~figureflow.Flow`.
    """
    from figureflow import Flow

    payload = json.loads(s)
    clean, warnings = validate(payload, strict=strict)
    flow = Flow(
        color_mode=clean["color_mode"],
        fit_view=clean["fit_view"],
        height=clean["height"],
        layout_direction=clean["layout_direction"],
    )
    flow.nodes = list(clean["nodes"])
    flow.edges = list(clean["edges"])
    flow._import_warnings = warnings
    return flow


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


def to_mermaid(flow: "Flow", direction: str = "TB") -> str:
    """Export mermaid flowchart text (lossy — structure + labels only)."""
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
