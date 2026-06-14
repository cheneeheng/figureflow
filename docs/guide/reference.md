# Reference

A flat reference for every public symbol, style field, and shortcut. For task-oriented
walkthroughs, see the [how-to guides](index.md).

```python
from figureflow import Flow, Node, Edge, Shape
```

## `Shape`

A string enum of the eight built-in node shapes:

`rectangle`, `rounded`, `stadium`, `ellipse`, `diamond`, `parallelogram`, `hexagon`,
`cylinder`.

| Shape | Description | Default size when not set |
|-------|-------------|---------------------------|
| `rectangle` | Plain box (default) | auto-size to label (min 80×40) |
| `rounded` | Rounded corners | auto-size to label |
| `stadium` | Pill / capsule | auto-size to label |
| `ellipse` | Oval | auto-size to label |
| `diamond` | Decision diamond | 130×90 |
| `parallelogram` | Slanted box | 130×56 |
| `hexagon` | Hexagon | 130×56 |
| `cylinder` | Database cylinder | 130×80 |

## `Node`

```python
Node(id, label="", pos=None, **style)
```

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| `id` | str | — (required) | Unique id within the flow |
| `label` | str | `""` | Text shown in the node |
| `pos` | (float, float) \| None | `None` | Top-left `(x, y)` on the canvas. `None` = **unplaced**: the renderer auto-places it on first render (see [Import a diagram](how-to/import-diagrams.md#positions-are-optional)). An explicit tuple — including `(0, 0)` — is honored as-is. |
| `shape` | `Shape` | `Shape.rectangle` | Built-in shape |
| `fill` | str | `"#ffffff"` | Background color |
| `border_color` | str | `"#334155"` | Outline color |
| `border_width` | float | `1.5` | Outline thickness (px) |
| `font_family` | str | `"Inter, system-ui, sans-serif"` | Label font stack |
| `font_size` | int | `13` | Label size (pt) |
| `font_color` | str | `"#0f172a"` | Label color |
| `bold` | bool | `False` | Bold label |
| `italic` | bool | `False` | Italic label |
| `text_align` | str | `"center"` | `left` / `center` / `right` |
| `width` | float \| None | `None` | Explicit width (px); else auto/shape default |
| `height` | float \| None | `None` | Explicit height (px); else auto/shape default |
| `svg_path` | str \| None | `None` | **L1** custom SVG path; overrides `shape` |
| `html` | str \| None | `None` | **L2** raw HTML body; replaces the label |
| `type` | str \| None | `None` | **L3** custom component type name; overrides `shape` |
| `parent_id` | str \| None | `None` | Group membership (usually set by `Flow.group`) |
| `extent` | str \| None | `None` | `"parent"` constrains a child to its group |
| `data` | dict | `{}` | Extra key/values merged into the node's data payload |

`Node.to_dict()` → the channel dict (`id`, `type`, `position`, `data{...}`). It emits every
style field; `type=None` maps to the built-in `"shape"` renderer.

## `Edge`

```python
Edge(source, target, **style)
```

| Field | Type | Default | Meaning |
|-------|------|---------|---------|
| `source` | str | — (required) | Source node id |
| `target` | str | — (required) | Target node id |
| `id` | str \| None | `"{source}->{target}"` | Edge id |
| `label` | str | `""` | Text along the edge (empty → no label) |
| `path_type` | str | `"bezier"` | `bezier` / `straight` / `step` / `smoothstep` |
| `marker_start` | str | `"none"` | `none` / `arrow` / `closed_arrow` |
| `marker_end` | str | `"arrow"` | `none` / `arrow` / `closed_arrow` |
| `color` | str | `"#334155"` | Line color |
| `width` | float | `1.5` | Line thickness (px) |
| `dash` | str | `"solid"` | `solid` / `dashed` / `dotted` |
| `font_family` | str | `"Inter, system-ui, sans-serif"` | Label font stack |
| `font_size` | int | `13` | Label size (pt) |
| `font_color` | str | `"#0f172a"` | Label color |
| `bold` | bool | `False` | Bold label |
| `italic` | bool | `False` | Italic label |
| `label_bg` | str \| None | `None` | Background color behind the label |
| `type` | str \| None | `None` | **L3** custom component type; overrides `path_type` |

`Edge.to_dict()` → the channel dict (`id`, `source`, `target`, `type`, `style`, and
`markerStart`/`markerEnd`/`label`/`labelStyle`/`labelBgStyle` as applicable).

> **Shared text vocabulary:** the five fields `font_family`, `font_size`, `font_color`,
> `bold`, `italic` mean the same thing on `Node` labels and `Edge` labels — same names, same
> defaults.

## `Flow`

```python
Flow(nodes=None, edges=None, color_mode="light", fit_view=True, height=480,
     layout_direction="TB")
```

| Argument | Type | Default | Meaning |
|----------|------|---------|---------|
| `nodes` | list[Node] \| None | `None` | Initial nodes |
| `edges` | list[Edge] \| None | `None` | Initial edges |
| `color_mode` | str | `"light"` | Canvas theme: `"light"` or `"dark"` |
| `fit_view` | bool | `True` | Fit the graph to the viewport on render |
| `height` | int | `480` | Canvas height in pixels |
| `layout_direction` | str | `"TB"` | Direction the auto-layout places **unplaced** nodes: `TB` / `BT` / `LR` / `RL`. `ValueError` on any other value. |

### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `add_node` | `(node: Node) -> None` | Append a node; syncs to the canvas |
| `add_edge` | `(edge: Edge) -> None` | Append an edge; syncs to the canvas |
| `positions` | `() -> {id: (x, y)}` | Current canvas geometry as last synced |
| `undo` | `() -> None` | Step back through canvas-edit history (no-op when empty) |
| `redo` | `() -> None` | Step forward through canvas-edit history (no-op when empty) |
| `group` | `(node_ids, label="") -> str` | Wrap nodes in a container; returns the group id. `ValueError` if `node_ids` is empty / unknown |
| `layout` | `(algo="dagre", direction="TB", **opts) -> None` | Auto-arrange via dagre. `ValueError` on a non-`dagre` algo or a direction outside `TB/BT/LR/RL` |
| `to_json` | `() -> str` | Lossless JSON snapshot (includes `layout_direction`) |
| `from_json` | `(s, *, strict=False) -> Flow` *(classmethod)* | Build a new `Flow` from a snapshot; positions optional. Raises `FlowValidationError` listing every problem; `strict=True` escalates warnings to errors |
| `from_mermaid` | `(s, *, strict=False) -> Flow` *(classmethod)* | Build a new `Flow` from a [mermaid flowchart](how-to/import-diagrams.md) (bounded subset). Raises `MermaidParseError`; `strict=True` escalates skipped-directive warnings |
| `load_json` | `(s, *, strict=False) -> None` | Replace nodes/edges in place (adopts the snapshot's `layout_direction`); clears undo history |
| `to_mermaid` | `(direction="TB") -> str` | Lossy mermaid flowchart export |
| `register_node_type` | `(name, module) -> None` | Register an L3 node component. `ValueError` on an invalid/colliding name |
| `register_edge_type` | `(name, module) -> None` | Register an L3 edge component. `ValueError` on an invalid/colliding name |
| `on` | `(event, callback) -> unsubscribe` | Subscribe to `emit()` events; returns an unsubscribe function |
| `display` | `() -> Flow` | Render in a notebook (returns `self`; a bare `flow` cell does the same) |
| `to_html` | `(path=None, *, title=None) -> str` | Self-contained offline interactive snapshot; writes to `path` if given, returns the HTML |
| `serve` | `(host="127.0.0.1", port=0, *, open_browser=True, block=False, quiet=False) -> str` | Live bidirectional sync in a browser tab (stdlib server, localhost only); returns the URL. `quiet=True` suppresses the URL print (used by the MCP server) |
| `stop` | `() -> None` | Stop a running `serve()` server (no-op if none) |

### Display targets

`display()`, `to_html()`, and `serve()` are three interchangeable doors onto the same
renderer (the v2 transport seam). See the how-to: [Display anywhere](how-to/display-anywhere.md).

### Serialization and import methods

JSON snapshots use the envelope schema `"figureflow/1"` and include `color_mode`, `fit_view`,
`height`, `layout_direction`, `nodes`, and `edges`. Placed positions are saved; **a node may omit
its position** (it is then auto-placed on render). The shipped JSON Schema at
`figureflow/static/figureflow.schema.json` (draft 2020-12) documents the full envelope.

`to_mermaid` is structural only (no per-element colors/fonts/`svg_path`/`html`). The inverse,
`from_mermaid`, imports a bounded mermaid flowchart subset — also structural. Both `from_json`
and `from_mermaid` route through one validation funnel that **collects every problem** into a
single exception and surfaces non-fatal fix-ups as warnings (escalated by `strict=True`). See
[Import a diagram](how-to/import-diagrams.md).

### Exceptions

| Exception | Raised by | Carries |
|-----------|-----------|---------|
| `FlowValidationError` | `from_json`, `load_json` (and `validate`) | `.problems` — a list of `{path, message, hint}`; `str(exc)` is one problem per line. Subclass of `ValueError`. |
| `MermaidParseError` | `from_mermaid` | `.problems` (same shape, with line numbers); `str(exc)` is one per line. Subclass of `ValueError`. |

Both are importable from the top level: `from figureflow import FlowValidationError, MermaidParseError`.

### MCP server

`pip install 'figureflow[mcp]'` adds the `figureflow-mcp` console script — an MCP server that
exposes the import functions and `serve()` to an AI agent. It is an operator-facing component;
see the [MCP server runbook](operations/mcp-server.md).

## Canvas controls

| Action | Input |
|--------|-------|
| Move a node | Left-drag the node (commits on release) |
| Pan the view | Middle- or right-mouse drag |
| Zoom | Scroll, or the controls (bottom-left) |
| Select one | Left-click |
| Add to selection | Shift-click |
| Box-select | Left-drag across empty canvas |
| Copy / paste (within canvas) | **Ctrl/Cmd+C** / **Ctrl/Cmd+V** |
| Delete selected | **Backspace** / **Delete** |
| Undo | **Ctrl/Cmd+Z** (or `flow.undo()`) |
| Redo | **Ctrl/Cmd+Shift+Z**, **Ctrl/Cmd+Y** (or `flow.redo()`) |

Pasted ids follow `{originalId}-copy-{n}`; pastes are offset `(+24, +24)`. Edges are
defined from Python (you cannot draw a new edge between handles on the canvas), but they can
be selected, copied (when both endpoints are selected), and deleted.

## Not in scope

Mermaid flowchart *import* is supported (`from_mermaid`), but still out of scope: other mermaid
diagram types (sequence/class/state/gantt), `classDef`/style fidelity, nested subgraphs, and
non-mermaid grammars (DOT); multi-diagram MCP sessions and granular per-element MCP edit tools;
system-clipboard copy/paste across apps; undo/redo of programmatic Python edits; obstacle-avoiding
edge routing; and a compile-against-source TypeScript package. See
`docs/planning/ITER_V3_03.md` § "Out of MVP scope" and `docs/planning/SKELETON.md` § "Out of MVP scope".
