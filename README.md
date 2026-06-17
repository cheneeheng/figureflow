# figureflow

> [!WARNING]
> **This project has been sunset and is no longer maintained.** It is archived
> as-is: the code stays public and installable, frozen at its current version,
> but there will be no further development, bug fixes, or compatibility updates.
> **Use at your own risk** — it may break with future versions of Jupyter,
> anywidget, or React Flow. See [`sunset.md`](sunset.md) for why, what it became,
> and what to use instead.

Interactive flow diagrams in Python, styled shape-by-shape.

figureflow is a [Jupyter widget](https://anywidget.dev) for building and displaying
interactive flow diagrams without writing any JavaScript. Each node and edge is styled
per-element — shape, fill, border, font — set directly as Python keyword arguments, the
way you'd format a single shape in a drawing tool. It wraps
[React Flow](https://reactflow.dev) (`@xyflow/react` v12), so the same widget renders
across JupyterLab, Notebook, Colab, VS Code and marimo. The front-end is bundled into the
wheel, so it installs with one `pip install` and runs offline — no CDN.

## Install

```bash
pip install figureflow        # once published to PyPI
# or, from source:
pip install -e .
```

The wheel ships a prebuilt front-end bundle — end-user installs need **no** JavaScript
toolchain.

## Quick start

```python
from figureflow import Flow, Node, Edge, Shape

flow = Flow(
    nodes=[
        Node("a", "Start",  pos=(0,   0),   shape=Shape.stadium,   fill="#e8f0fe"),
        Node("b", "Process",pos=(0, 120),   shape=Shape.rectangle),
        Node("c", "Done",   pos=(0, 240),   shape=Shape.stadium,   fill="#e6f4ea"),
    ],
    edges=[
        Edge("a", "b"),
        Edge("b", "c", dash="dashed", label="result"),
    ],
    height=480,
)
flow  # display in a notebook cell
```

Drag nodes on the canvas, then read positions back into Python:

```python
flow.positions()       # {"a": (x, y), "b": (x, y), "c": (x, y)}
flow.add_node(Node("d", "Extra", pos=(200, 120)))
flow.add_edge(Edge("c", "d"))
```

## API

| Symbol | Signature | Purpose |
|--------|-----------|---------|
| `Shape` | enum | 8 built-in shapes: `rectangle, rounded, stadium, ellipse, diamond, parallelogram, hexagon, cylinder` |
| `Node` | `Node(id, label="", pos=(0,0), **style)` | Styled node; `.to_dict()` serializes for the channel |
| `Edge` | `Edge(source, target, **style)` | Styled edge; `.to_dict()` serializes |
| `Flow` | `Flow(nodes=None, edges=None, color_mode="light", fit_view=True, height=480)` | The widget |
| `Flow.add_node` | `(node)` | Append + sync |
| `Flow.add_edge` | `(edge)` | Append + sync |
| `Flow.positions` | `() → {id: (x,y)}` | Current canvas geometry |
| `Flow.display` | `() → Flow` | Render in a notebook (anywidget; the default cell-output door) |
| `Flow.to_html` | `(path=None, *, title=None) → str` | Self-contained offline interactive snapshot; writes to `path` if given |
| `Flow.serve` | `(host="127.0.0.1", port=0, *, open_browser=True, block=False) → str` | Live bidirectional sync in a plain browser tab (stdlib server); returns the URL |
| `Flow.stop` | `() → None` | Stop a running `serve()` server |
| `Flow.undo` / `Flow.redo` | `()` | Step through canvas-edit history |
| `Flow.group` | `(node_ids, label="") → str` | Create a parent group; returns group id |
| `Flow.layout` | `(algo="dagre", direction="TB", **opts)` | Auto-arrange nodes via dagre |
| `Flow.to_json` | `() → str` | Lossless JSON snapshot |
| `Flow.from_json` | `(s) → Flow` *(classmethod)* | Rebuild from `to_json` output |
| `Flow.load_json` | `(s)` | Replace nodes/edges in-place + clear undo history |
| `Flow.to_mermaid` | `(direction="TB") → str` | Lossy mermaid flowchart export |
| `Flow.register_node_type` | `(name, module)` | Register a custom JS node component (L3) |
| `Flow.register_edge_type` | `(name, module)` | Register a custom JS edge component (L3) |
| `Flow.on` | `(event, callback) → unsubscribe` | Subscribe to `emit()` events from custom components |

### Node style fields

`shape, fill, border_color, border_width, font_family, font_size, font_color, bold, italic,
text_align, width, height, html, svg_path, type, parent_id, extent`

### Edge style fields

`path_type` (`bezier|straight|step|smoothstep`), `marker_start`, `marker_end`
(`none|arrow|closed_arrow`), `color, width, dash` (`solid|dashed|dotted`),
`font_family, font_size, font_color, bold, italic, label, label_bg, type`

### Canvas interactions

- **Drag nodes** to reposition; positions sync back to Python on drag-stop.
- **Multi-select**: Shift-click or drag a selection box to select multiple nodes.
- **Copy/paste**: `Ctrl/Cmd+C` / `Ctrl/Cmd+V` — clones keep styling; pasted ids
  follow `{origId}-copy-{n}`.
- **Undo/redo**: `Ctrl/Cmd+Z` / `Ctrl/Cmd+Shift+Z` (or `Ctrl+Y`); also callable
  from Python as `flow.undo()` / `flow.redo()`.
- **Minimap**: shown in the bottom-right corner.

## Node shapes

| Shape | Description |
|-------|-------------|
| `rectangle` | Plain box |
| `rounded` | Box with rounded corners |
| `stadium` | Pill / stadium shape |
| `ellipse` | Oval |
| `diamond` | Decision diamond |
| `parallelogram` | Slanted box |
| `hexagon` | Hexagonal box |
| `cylinder` | Database cylinder |

**L1 — custom geometry:** pass `svg_path="M ..."` to render any SVG path as the node body.

**L2 — raw HTML:** pass `html="<b>...</b>"` to render arbitrary HTML in the node body.

**L3 — custom JS component:** `flow.register_node_type("name", "./my_node.js")` and set
`Node(..., type="name")`. The component receives `{data, selected, emit}`. Use
`globalThis.figureflow.React` (and `xyflow` handles) to share the bundled React instance.
TypeScript typings ship in `static/figureflow.d.ts`.

## Serialization

```python
# Save
json_str = flow.to_json()

# Restore (new widget)
flow2 = Flow.from_json(json_str)

# Replace in place (clears undo history)
flow.load_json(json_str)

# Mermaid (structural only — colors/fonts not preserved)
print(flow.to_mermaid())
```

## LLM authoring (v3)

An LLM can author a diagram **coordinate-free** — emit topology, and the renderer
validates, places, and renders it.

```python
# Build from the mermaid an LLM already speaks (bounded flowchart subset)
flow = Flow.from_mermaid("""
flowchart TD
    A([Start]) --> B{Decision}
    B -->|yes| C[Do the thing]
""")

# Or from the figureflow/1 JSON envelope, with positions omitted
flow = Flow.from_json(envelope_str)
```

- **Positions are optional.** A node with no `pos` is *unplaced*; the renderer
  auto-lays unplaced nodes on first render using `Flow(layout_direction=...)`
  (`"TB"` default, or `BT`/`LR`/`RL`). After first render `flow.positions()` is total.
- **Repair-friendly errors.** `from_json` / `from_mermaid` collect every problem
  into one `FlowValidationError` / `MermaidParseError` (one line each:
  `path: what's wrong. hint`), so a model fixes all faults in one round-trip.
  Pass `strict=True` to escalate forgiving coercions/skips to errors.
- **Published schema.** The `figureflow/1` JSON Schema ships in the wheel at
  `figureflow/static/figureflow.schema.json`; see `llms.txt` and `docs/prompts/`.

### MCP server (optional extra)

```bash
pip install 'figureflow[mcp]'     # console script: figureflow-mcp (stdio)
```

Exposes `create_diagram` / `get_diagram` / `replace_diagram` / `add_elements` /
`close_diagram` tools over one live `serve()` canvas, so an agent and a human edit
the same diagram. Core `pip install figureflow` stays dependency-free.

## Grouping & layout

```python
group_id = flow.group(["a", "b", "c"], label="My Group")
flow.layout(direction="LR")      # dagre left-to-right
```

## Display targets

The same `Flow` renders through three interchangeable transports — one renderer,
three front doors. The mental model (build a `Flow`, style per-element) is identical;
only how you ship it to a viewer changes.

```python
# 1) Notebook — live kernel round-trip (the default; a bare `flow` cell also works)
flow.display()

# 2) Plain browser tab — full bidirectional sync to the live Python process,
#    over a dependency-free stdlib server (localhost only). Returns the URL.
url = flow.serve()              # add block=True for `python script.py`
# ... edit in the browser; flow.positions() reflects it; flow.add_node(...) pushes live ...
flow.stop()

# 3) Self-contained offline snapshot — interactive client-side (pan/zoom/drag),
#    no Python behind it. Reimport edits via the in-page "Download JSON" button.
html = flow.to_html("diagram.html")
restored = Flow.from_json(open("figureflow.json").read())   # the downloaded layout
```

`serve()` binds `127.0.0.1` only and adds **no dependencies** (stdlib SSE + POST).
`to_html()` inlines the vendored bundle, so the file opens via `file://` with no network.

## Examples

Runnable examples live in [`examples/`](examples). Each script builds a diagram and prints a
text summary, so you can run it from a terminal — then drop the same code into a notebook cell
(ending with `flow`) to see it rendered interactively:

```bash
pip install -e .                  # install figureflow first
python examples/01_quickstart.py        # all 8 shapes + edge styles (+ L1 SVG / L2 HTML nodes)
python examples/02_grouping_layout.py   # group() + dagre layout()
python examples/03_serialization.py     # to_json / from_json round-trip + to_mermaid
python examples/04_custom_component.py   # L3 custom JS node + emit/on events
python examples/05_display_targets.py    # display() / to_html() / serve() (add --serve)
```

See [`examples/README.md`](examples/README.md) for what each one demonstrates and how to view
the live widget.

## Documentation

- **User manual** — [`docs/guide/`](docs/guide): a task-by-task guide covering installation,
  building diagrams, the full style reference, canvas interactions, grouping & layout,
  serialization, custom components, and troubleshooting.
- **Design & roadmap** — [`docs/planning/`](docs/planning): `SKELETON.md` + `ITER_01`–`ITER_06`
  are the v1 target surface and its iterations; `SKELETON_V2.md` + `ITER_V2_01`–`ITER_V2_04`
  add the multi-transport seam (`display()` / `to_html()` / `serve()`); `ITER_V3_01`–`ITER_V3_03`
  add LLM-authorable ingestion (`from_json` / `from_mermaid`, the `figureflow/1` schema, MCP).

## Development

The Python package and the front-end build are separate. Use [bun](https://bun.sh):

```bash
bun install              # install front-end build dependencies
bun run build            # bundle js/index.js → src/figureflow/static/widget.js
bun run dev              # rebuild on change (--watch, with sourcemaps)
pip install -e ".[dev]"  # editable install of the Python package + pytest
python -m pytest tests/  # run the test suite
```

`widget.js` is a checked-in build artifact — rebuild after editing `js/index.js`.

## Out of MVP scope

- DOT / Graphviz *import*, and mermaid diagram types beyond flowcharts
  (sequence/class/state/gantt) — mermaid flowchart import (`from_mermaid`) and
  mermaid/JSON export are supported.
- System-clipboard / cross-application copy/paste — within-canvas only.
- Undo/redo of programmatic Python edits — canvas-edit undo/redo is supported.
- Heavy obstacle-avoiding edge routing — straight/step/smoothstep light routing is supported.

## License

See [LICENSE](LICENSE).
