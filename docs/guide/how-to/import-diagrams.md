# Import a diagram (and author coordinate-free)

Build a `Flow` from text instead of hand-placing nodes: import a [mermaid](https://mermaid.js.org)
flowchart, or load a `figureflow/1` JSON envelope. Either way you can **omit positions** — the
renderer lays the diagram out for you on first display. This is the path an LLM uses to author a
diagram (emit topology; figureflow validates, places, and renders it).

**Prerequisites:** figureflow installed ([Getting started](../getting-started.md)). Importing
needs only the core install — no extra dependencies.

## Import a mermaid flowchart

`Flow.from_mermaid()` parses a bounded subset of the mermaid flowchart grammar into a `Flow`:

```python
from figureflow import Flow

flow = Flow.from_mermaid("""
flowchart TD
    A([Start]) --> B{Decision}
    B -->|yes| C[Do the thing]
    B -->|no|  D[Stop]
""")
flow   # display — the nodes are auto-arranged top-to-bottom
```

The header direction (`TD`/`TB`, `BT`, `LR`, `RL`) becomes the layout direction. Nodes are
created **unplaced**, so the canvas auto-arranges them on first render (see
[Positions are optional](#positions-are-optional) below).

**Verify:** the diagram renders laid out, with a stadium **Start**, a diamond **Decision**, and
two labelled edges.

### What mermaid is supported

Import is **structural** — it is the inverse of `to_mermaid()`'s lossy export, so node/edge
*styling* in the mermaid source is intentionally dropped (figureflow styling is per-element
Python kwargs). The supported grammar:

| Construct | Accepted forms |
|-----------|----------------|
| Header | `flowchart <dir>` or `graph <dir>`; `dir` ∈ `TB TD BT LR RL` (`TD`→`TB`); missing → `TB` |
| Node shapes | `id[label]` rectangle, `id(label)` rounded, `id([label])` stadium, `id((label))` ellipse, `id{label}` diamond, `id{{label}}` hexagon, `id[/label/]` parallelogram, `id[(label)]` cylinder; bare `id` → rectangle |
| Labels | unquoted, `"quoted"`, `<br>`/`<br/>` → newline; first definition of an id wins |
| Edges | `-->` `---` `-.->` `-.-` `==>` `===` (arrow vs none; `-.` dashed; `==` thick) |
| Edge labels | `-->|label|` and `-- label -->` |
| Chains & fans | `a --> b --> c`, `a & b --> c`, `a --> b & c` |
| Subgraph | `subgraph id [title] … end` → a one-level [group](group-and-layout.md) |
| Comments | `%%` to end of line (dropped) |

Style directives (`classDef`, `class`, `style`, `linkStyle`, `click`, `direction`) and nested
subgraphs are **skipped with a warning**, not errored. Other mermaid diagram types
(`sequenceDiagram`, `classDiagram`, `gantt`, …) are not flowcharts and raise an error naming the
unsupported type.

## Import a JSON envelope

`Flow.from_json()` rebuilds a diagram from a `figureflow/1` envelope. Positions are optional
here too — omit them and the renderer places the nodes:

```python
from figureflow import Flow

envelope = """
{
  "schema": "figureflow/1",
  "layout_direction": "LR",
  "nodes": [
    {"id": "ingest", "data": {"label": "Ingest", "shape": "stadium"}},
    {"id": "clean",  "data": {"label": "Clean"}},
    {"id": "store",  "data": {"label": "Store", "shape": "cylinder"}}
  ],
  "edges": [
    {"source": "ingest", "target": "clean"},
    {"source": "clean",  "target": "store"}
  ]
}
"""

flow = Flow.from_json(envelope)
flow
```

The full envelope shape is documented by the JSON Schema shipped in the wheel at
`figureflow/static/figureflow.schema.json` (draft 2020-12). A round-trip of a fully-specified
diagram is lossless: `Flow.from_json(flow.to_json())` reproduces the original (see
[Save and load](save-and-load.md)).

**Verify:** the file imports without error and renders a three-node pipeline left-to-right.

## Positions are optional

A node with no `pos` (Python) or no `position` (JSON) is **unplaced**. On the first render — on
any display target — the renderer runs the dagre layout over the unplaced nodes using the flow's
`layout_direction`, then commits the result:

```python
from figureflow import Flow, Node, Edge

flow = Flow(
    nodes=[Node("a", "Start"), Node("b", "End")],   # no pos= → unplaced
    edges=[Edge("a", "b")],
    layout_direction="LR",                           # "TB" (default) | "BT" | "LR" | "RL"
)

flow.positions()   # {}  — nothing placed yet
flow               # display: nodes are auto-arranged left-to-right
# after the canvas renders, flow.positions() reports both nodes
```

- **Authored positions are kept.** If some nodes have a `pos` and others don't, only the
  unplaced ones are auto-placed. (Auto-placed nodes can land on top of authored ones; drag them
  apart, or call `flow.layout()` to re-arrange everything — see
  [Group and lay out](group-and-layout.md).)
- **`positions()` is empty until the canvas renders.** It reports only placed nodes, so it
  returns `{}` for an all-unplaced flow you haven't displayed yet. After the first render (or a
  `flow.layout()` call) it is complete.

**Verify:** `flow.positions()` returns `{}` before display and a coordinate per node after.

## Fix a bad diagram in one pass

Import does not stop at the first mistake — it **collects every problem** and raises them
together, one per line, each in the form `path: what is wrong. hint`. This lets you (or an LLM)
fix everything in a single edit:

```python
from figureflow import Flow, FlowValidationError

bad = """
{
  "schema": "figureflow/1",
  "nodes": [
    {"id": "a", "data": {"shape": "circle"}},
    {"id": "a", "data": {"shape": "rectangle"}}
  ],
  "edges": [{"source": "a", "target": "end"}]
}
"""

try:
    Flow.from_json(bad)
except FlowValidationError as exc:
    print(exc)
```

Output:

```
nodes[0].shape: 'circle' is not a valid shape. Use one of: rectangle, rounded, stadium, ellipse, diamond, parallelogram, hexagon, cylinder.
nodes[1].id: duplicate node id 'a'. Node ids must be unique.
edges[0].target: target 'end' names no node. Known node ids: a.
```

Mermaid import raises the same kind of message as `MermaidParseError` (with line numbers).
Each exception carries the structured list on `exc.problems` if you want to handle them in code.

**Verify:** the broken envelope above prints exactly three lines, one per fault.

### Forgiving by default, strict on demand

Some issues are **warnings**, not errors — import succeeds and fixes them up:

- an unknown node/edge key is folded into the element's `data`;
- a numeric value sent as a string (`"13"`) is coerced to a number;
- a skipped mermaid style directive.

By default these pass quietly. Pass `strict=True` to escalate every warning to an error — useful
in a CI check or when you want an LLM held to the exact schema:

```python
Flow.from_json(envelope, strict=True)      # warnings become a FlowValidationError
Flow.from_mermaid(source, strict=True)     # skipped directives become a MermaidParseError
```

**Verify:** an envelope with an unknown key like `{"id": "a", "color": "red"}` imports under the
default and raises under `strict=True`.

## Drive a live diagram from an AI agent

If you want an external agent (Claude Code, Claude Desktop, Cursor) to author and edit a diagram
while a human watches in a browser, run the optional MCP server — it wraps these same import
functions and `serve()`. That is an operator task: see the
[MCP server runbook](../operations/mcp-server.md).

## See also

- [Save and load](save-and-load.md) — `to_json` / `to_mermaid` (the export direction).
- [Group and lay out](group-and-layout.md) — `flow.layout()` and grouping.
- [Reference → Serialization](../reference.md#serialization-and-import-methods) — exact signatures and exceptions.
