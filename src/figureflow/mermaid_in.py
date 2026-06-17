"""Mermaid flowchart import — the bounded v3 parser (ITER_V3_02).

Parses a **pinned subset** of the mermaid flowchart grammar into the figureflow
model. Hand-written, line-oriented, stdlib-only (``re`` + a small bracket
tokenizer); no parser library, so core stays dependency-free.

The parser is a pure function into the existing model: mermaid text →
``(nodes, edges, layout_direction, warnings)`` → the same
:func:`figureflow.serialize.validate` funnel as JSON → :class:`~figureflow.Flow`.
Nodes are created **unplaced** (``pos=None``); placement is entirely
ITER_V3_01's auto-layout-on-mount. Style fidelity is out by design — import is
structural, the inverse of ``to_mermaid``'s documented lossiness.

:class:`MermaidParseError` carries ``line``/``hint`` and uses the same one-line
message contract as :class:`~figureflow.serialize.FlowValidationError`.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from figureflow.serialize import _format_problem, validate

Problem = Dict[str, str]


class MermaidParseError(ValueError):
    """Raised on hard mermaid parse faults, collecting every problem at once."""

    def __init__(self, problems: List[Problem]) -> None:
        self.problems = problems
        super().__init__("\n".join(_format_problem(p) for p in problems))

    def __str__(self) -> str:
        return "\n".join(_format_problem(p) for p in self.problems)


# Diagram types figureflow does not import (named so the LLM repairs correctly).
_NON_FLOWCHART: Dict[str, str] = {
    "sequencediagram": "sequence diagram",
    "classdiagram": "class diagram",
    "statediagram": "state diagram",
    "statediagram-v2": "state diagram",
    "erdiagram": "entity-relationship diagram",
    "gantt": "gantt chart",
    "pie": "pie chart",
    "journey": "user journey",
    "gitgraph": "git graph",
    "mindmap": "mindmap",
    "timeline": "timeline",
    "quadrantchart": "quadrant chart",
    "requirementdiagram": "requirement diagram",
    "c4context": "C4 diagram",
}

# Directives consciously dropped (one warning per kind) — figureflow styling is
# per-element Python kwargs, not mermaid stylesheets.
_SKIP_DIRECTIVE_RE = re.compile(
    r"(classDef|class|style|linkStyle|click|accTitle|accDescr|direction)\b",
    re.IGNORECASE,
)

_DIR_MAP = {"TB": "TB", "TD": "TB", "BT": "BT", "LR": "LR", "RL": "RL"}

# Opening/closing bracket pairs, longest opener first so ``([`` wins over ``(``.
_BRACKETS: List[Tuple[str, str, str]] = [
    ("([", "])", "stadium"),
    ("((", "))", "ellipse"),
    ("[(", ")]", "cylinder"),
    ("[/", "/]", "parallelogram"),
    ("{{", "}}", "hexagon"),
    ("[", "]", "rectangle"),
    ("{", "}", "diamond"),
    ("(", ")", "rounded"),
]

_ID_RE = re.compile(r"[A-Za-z0-9_]+")
_AND_RE = re.compile(r"\s*&\s*")
_WORD_RE = re.compile(r"[A-Za-z0-9_-]+")

# Edge operators. The ``-- label -->`` inline form is tried before the bare
# operators; a trailing ``|label|`` covers the pipe form for every operator.
_EDGE_RE = re.compile(
    r"""
    (?:
        --\s+(?P<dlabel>[^>][^>]*?)\s+-->      # -- label -->
      | (?P<op>-\.->|-\.-|==>|===|-->|---)     # arrow / line operators
    )
    (?:\s*\|(?P<plabel>[^|]*)\|)?              # optional |label|
    """,
    re.VERBOSE,
)


def _clean_label(text: str) -> str:
    """Strip surrounding quotes and turn ``<br>``/``<br/>`` into newlines."""
    text = text.strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        text = text[1:-1]
    return re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)


def _strip_comment(line: str) -> str:
    idx = line.find("%%")
    return line[:idx] if idx != -1 else line


def _parse_header(line: str, lineno: int) -> Tuple[str, bool, Optional[Problem]]:
    """Parse the ``flowchart``/``graph`` header; return ``(dir, ok, error)``."""
    m = re.match(r"(?:flowchart|graph)\b\s*([A-Za-z]{2})?", line, re.IGNORECASE)
    if m:
        token = (m.group(1) or "TB").upper()
        return _DIR_MAP.get(token, "TB"), True, None
    word = _WORD_RE.match(line)
    name = word.group().lower() if word else line.lower()
    if name in _NON_FLOWCHART:
        return (
            "TB",
            False,
            {
                "path": f"line {lineno}",
                "message": f"{_NON_FLOWCHART[name]} is not supported.",
                "hint": "Only mermaid flowcharts ('flowchart'/'graph') import.",
            },
        )
    return (
        "TB",
        False,
        {
            "path": f"line {lineno}",
            "message": "expected a 'flowchart' or 'graph' header.",
            "hint": "Start the diagram with e.g. 'flowchart TD'.",
        },
    )


def _edge_from_match(m: "re.Match[str]") -> Dict[str, Any]:
    """Map an edge-operator match to figureflow edge style kwargs."""
    op = m.group("op") or "-->"  # dash-label form is a solid arrow
    raw_label = m.group("dlabel") or m.group("plabel") or ""
    spec: Dict[str, Any] = {
        "marker_end": "arrow",
        "dash": "solid",
        "width": 1.5,
        "label": _clean_label(raw_label) if raw_label else "",
    }
    if op == "---":
        spec["marker_end"] = "none"
    elif op == "-.->":
        spec["dash"] = "dashed"
    elif op == "-.-":
        spec["dash"] = "dashed"
        spec["marker_end"] = "none"
    elif op == "==>":
        spec["width"] = 3
    elif op == "===":
        spec["width"] = 3
        spec["marker_end"] = "none"
    return spec


def _match_node_token(
    stmt: str, pos: int, lineno: int
) -> Tuple[Optional[Tuple[str, str, str]], int, Optional[Problem]]:
    """Match ``id`` + optional shape brackets at ``pos``.

    Returns ``((id, shape, label), newpos, error)``; ``(None, pos, None)`` when no
    id is present (caller handles end-of-statement / stray token).
    """
    m = _ID_RE.match(stmt, pos)
    if not m:
        return None, pos, None
    nid = m.group()
    p = m.end()
    rest = stmt[p:]
    for opener, closer, shape in _BRACKETS:
        if rest.startswith(opener):
            close_idx = rest.find(closer, len(opener))
            if close_idx == -1:
                return (
                    None,
                    pos,
                    {
                        "path": f"line {lineno}",
                        "message": f"unbalanced '{opener}' in node '{nid}'.",
                        "hint": f"Close it with '{closer}'.",
                    },
                )
            label = rest[len(opener) : close_idx]
            newpos = p + close_idx + len(closer)
            return (nid, shape, _clean_label(label)), newpos, None
    return (nid, "rectangle", nid), p, None  # bare id


def _match_node_group(
    stmt: str, pos: int, lineno: int
) -> Tuple[Optional[List[Tuple[str, str, str]]], int, Optional[Problem]]:
    """Match a ``a & b & c`` fan of node tokens."""
    token, pos, err = _match_node_token(stmt, pos, lineno)
    if err:
        return None, pos, err
    if token is None:
        return None, pos, None
    group = [token]
    while True:
        m = _AND_RE.match(stmt, pos)
        if not m:
            break
        token, pos, err = _match_node_token(stmt, m.end(), lineno)
        if err:
            return None, pos, err
        if token is None:
            return None, pos, _stray(stmt, m.end(), lineno)
        group.append(token)
    return group, pos, None


def _stray(stmt: str, pos: int, lineno: int) -> Problem:
    snippet = stmt[pos:].strip()[:20] or "<end of line>"
    return {
        "path": f"line {lineno}",
        "message": f"unexpected token near {snippet!r}.",
        "hint": "Use a supported edge operator: -->, ---, -.->, ==>.",
    }


def _tokenize(
    stmt: str, lineno: int
) -> Tuple[Optional[List[Tuple[str, Any]]], Optional[Problem]]:
    """Split a statement into alternating ('nodes', group) / ('edge', spec)."""
    tokens: List[Tuple[str, Any]] = []
    pos = 0
    n = len(stmt)
    while pos < n:
        while pos < n and stmt[pos].isspace():
            pos += 1
        if pos >= n:
            break
        em = _EDGE_RE.match(stmt, pos)
        if em:
            tokens.append(("edge", _edge_from_match(em)))
            pos = em.end()
            continue
        group, newpos, err = _match_node_group(stmt, pos, lineno)
        if err:
            return None, err
        if group is None:
            return None, _stray(stmt, pos, lineno)
        tokens.append(("nodes", group))
        pos = newpos
    return tokens, None


def _parse(
    text: str,
) -> Tuple[List[Any], List[Any], str, List[Problem], List[Problem]]:
    """Parse mermaid text into ``(nodes, edges, direction, warnings, problems)``."""
    from figureflow import Edge, Node, Shape

    registry: Dict[str, Any] = {}
    order: List[str] = []
    explicit: set[str] = set()
    edges: List[Any] = []
    warnings: List[Problem] = []
    problems: List[Problem] = []
    warned_kinds: set[str] = set()
    direction = "TB"
    header_found = False
    group_stack: List[Optional[str]] = []
    subgraph_count = 0

    def effective_parent() -> Optional[str]:
        # The outermost stack entry is always a real gid (None is only ever
        # pushed *after* it, for a flattened nested subgraph), so the first
        # non-None is always at index 0 — the skip arc is defensive.
        for g in group_stack:
            if g is not None:  # pragma: no branch
                return g
        return None

    def register(token: Tuple[str, str, str]) -> str:
        nid, shape, label = token
        is_explicit = not (shape == "rectangle" and label == nid)
        parent = effective_parent()
        if nid not in registry:
            registry[nid] = Node(
                nid,
                label=label,
                shape=Shape(shape),
                pos=None,
                parent_id=parent,
                extent="parent" if parent else None,
            )
            order.append(nid)
            if is_explicit:
                explicit.add(nid)
        else:
            node = registry[nid]
            if is_explicit and nid not in explicit:
                node.label = label
                node.shape = Shape(shape)
                explicit.add(nid)
            if parent and node.parent_id is None:
                node.parent_id = parent
                node.extent = "parent"
        return nid

    def warn_directive(kind: str, lineno: int) -> None:
        key = kind.lower()
        if key in warned_kinds:
            return
        warned_kinds.add(key)
        warnings.append(
            {
                "path": f"line {lineno}",
                "message": f"'{kind}' is not imported.",
                "hint": "figureflow styling is per-element Python kwargs. Skipped.",
            }
        )

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = _strip_comment(raw).strip()
        if not line:
            continue

        if not header_found:
            direction, ok, err = _parse_header(line, lineno)
            if err:
                problems.append(err)
                return [], [], direction, warnings, problems
            header_found = True
            continue

        if line.lower() == "end":
            if group_stack:
                group_stack.pop()
            continue

        sm = re.match(r"subgraph\b\s*(.*)$", line, re.IGNORECASE)
        if sm:
            if group_stack:
                # Nested subgraph: warn once, flatten into the outer group.
                warn_directive("nested subgraph", lineno)
                group_stack.append(None)
                continue
            rem = sm.group(1).strip()
            title_m = re.match(r"([A-Za-z0-9_]+)\s*\[(.*)\]\s*$", rem)
            if title_m:
                gid = title_m.group(1)
                gtitle = _clean_label(title_m.group(2))
            elif rem:
                gtitle = _clean_label(rem)
                gid_m = _ID_RE.match(rem)
                gid = gid_m.group() if gid_m else f"subgraph_{subgraph_count}"
            else:
                subgraph_count += 1
                gid = f"subgraph_{subgraph_count}"
                gtitle = ""
            if gid in registry:
                subgraph_count += 1
                gid = f"subgraph_{subgraph_count}"
            registry[gid] = Node(
                gid,
                label=gtitle,
                type="group",
                pos=None,
                fill="rgba(226,232,240,0.4)",
                border_color="#94a3b8",
            )
            order.append(gid)
            group_stack.append(gid)
            continue

        directive = _SKIP_DIRECTIVE_RE.match(line)
        if directive:
            warn_directive(directive.group(1), lineno)
            continue

        tokens, err = _tokenize(line, lineno)
        if err:
            problems.append(err)
            continue
        if not tokens:  # pragma: no cover - defensive; blank lines filtered above
            continue

        last_ids: Optional[List[str]] = None
        pending: Optional[Dict[str, Any]] = None
        for kind, value in tokens:
            if kind == "nodes":
                ids = [register(t) for t in value]
                if pending is not None and last_ids is not None:
                    for a in last_ids:
                        for b in ids:
                            edges.append(
                                Edge(
                                    source=a,
                                    target=b,
                                    label=pending["label"],
                                    marker_end=pending["marker_end"],
                                    dash=pending["dash"],
                                    width=pending["width"],
                                )
                            )
                    pending = None
                last_ids = ids
            else:
                pending = value
        if pending is not None:
            problems.append(
                {
                    "path": f"line {lineno}",
                    "message": "edge operator has no target node.",
                    "hint": "Add a node after the arrow.",
                }
            )

    nodes = [registry[nid] for nid in order]
    return nodes, edges, direction, warnings, problems


def from_mermaid(s: str, *, strict: bool = False) -> "Any":
    """Build a :class:`~figureflow.Flow` from a mermaid flowchart.

    Args:
        s: The mermaid flowchart source.
        strict: When ``True``, warn-and-skip directives become errors.

    Returns:
        The reconstructed flow with unplaced nodes (auto-laid on first render).

    Raises:
        MermaidParseError: With every collected hard parse problem (or, under
            ``strict``, every warning).
    """
    from figureflow import Flow

    nodes, edges, direction, warnings, problems = _parse(s)
    if problems:
        raise MermaidParseError(problems)
    if strict and warnings:
        raise MermaidParseError(warnings)

    envelope = {
        "schema": "figureflow/1",
        "layout_direction": direction,
        "nodes": [n.to_dict() for n in nodes],
        "edges": [e.to_dict() for e in edges],
    }
    clean, validation_warnings = validate(envelope)
    flow = Flow(layout_direction=clean["layout_direction"])
    flow.nodes = list(clean["nodes"])
    flow.edges = list(clean["edges"])
    flow._import_warnings = [
        _format_problem(w) for w in warnings
    ] + validation_warnings
    return flow
