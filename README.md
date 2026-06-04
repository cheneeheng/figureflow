# figureflow

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

## Grouping & layout

```python
group_id = flow.group(["a", "b", "c"], label="My Group")
flow.layout(direction="LR")      # dagre left-to-right
```

## Examples

Runnable examples live in [`examples/`](examples). Each script builds a diagram and prints a
text summary, so you can run it from a terminal — then drop the same code into a notebook cell
(ending with `flow`) to see it rendered interactively:

```bash
pip install -e .                  # install figureflow first
python examples/quickstart.py     # all 8 shapes + edge styles (+ L1 SVG / L2 HTML nodes)
python examples/grouping_layout.py  # group() + dagre layout()
python examples/serialization.py    # to_json / from_json round-trip + to_mermaid
python examples/custom_component.py  # L3 custom JS node + emit/on events
```

See [`examples/README.md`](examples/README.md) for what each one demonstrates and how to view
the live widget.

## Documentation

- **User manual** — [`docs/guide/`](docs/guide): a task-by-task guide covering installation,
  building diagrams, the full style reference, canvas interactions, grouping & layout,
  serialization, custom components, and troubleshooting.
- **Design & roadmap** — [`docs/planning/`](docs/planning): `SKELETON.md` is the authoritative
  target surface and `ITER_01`–`ITER_06` are the iterations that filled it in.

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

- Format *import* (parsing mermaid/DOT into figureflow) — export is supported.
- System-clipboard / cross-application copy/paste — within-canvas only.
- Undo/redo of programmatic Python edits — canvas-edit undo/redo is supported.
- Heavy obstacle-avoiding edge routing — straight/step/smoothstep light routing is supported.

## License

See [LICENSE](LICENSE).
