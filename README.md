# figureflow

Interactive flow diagrams in Python, styled shape-by-shape.

figureflow is a [Jupyter widget](https://anywidget.dev) for building and displaying
interactive flow diagrams without writing any JavaScript. Each node and edge is styled
per-element — shape, fill, border, font — set directly as Python keyword arguments, the
way you'd format a single shape in a drawing tool. It wraps
[React Flow](https://reactflow.dev) (`@xyflow/react` v12), so the same widget renders
across JupyterLab, Notebook, Colab, VS Code and marimo. The front-end is bundled into the
wheel, so it installs with one `pip install` and runs offline — no CDN.

> **Status: v0.1, skeleton.** The render-and-sync loop works today: you can construct a
> `Flow`, display it, drag nodes on the canvas, and read positions back into Python. Most
> of the styling and feature surface (shapes, fonts, edge styling, undo/redo, grouping,
> auto-layout, JSON/mermaid export, custom components) is present in the API but not yet
> wired — those methods raise `NotImplementedError` naming the iteration that fills them.

## Install

From source (not yet published to PyPI):

```bash
pip install -e .
```

The wheel ships a prebuilt front-end bundle, so end-user installs need **no** JavaScript
toolchain.

## Quick start

```python
from figureflow import Flow, Node, Edge, Shape

flow = Flow(
    nodes=[
        Node("a", "Start", pos=(0, 0), shape=Shape.stadium, fill="#e8f0fe"),
        Node("b", "Step",  pos=(0, 120), shape=Shape.rectangle),
        Node("c", "Done",  pos=(0, 240), shape=Shape.stadium, fill="#e6f4ea"),
    ],
    edges=[
        Edge("a", "b"),
        Edge("b", "c"),
    ],
    height=480,
)
flow  # display in a notebook cell
```

Edit on the canvas (drag a node, then drop), and read the geometry back:

```python
flow.positions()        # {"a": (x, y), "b": (x, y), "c": (x, y)}

flow.add_node(Node("d", "Extra", pos=(200, 120)))
flow.add_edge(Edge("c", "d"))
```

### API at a glance

| Symbol | Purpose |
| --- | --- |
| `Shape` | The 8 built-in shapes: `rectangle, rounded, stadium, ellipse, diamond, parallelogram, hexagon, cylinder`. |
| `Node(id, label="", pos=(0,0), **style)` | A styled node. |
| `Edge(source, target, **style)` | A styled edge. |
| `Flow(nodes=None, edges=None, color_mode="light", fit_view=True, height=480)` | The widget. |
| `Flow.add_node` / `Flow.add_edge` | Append an element and sync. |
| `Flow.positions()` | Current canvas geometry as `{id: (x, y)}`. |

Planned (gated to later iterations): `undo`/`redo`, `group`, `layout`, `to_json`/
`from_json`, `to_mermaid`, `register_node_type`/`register_edge_type`, `on`.

## Development

The Python package and the front-end build are separate. The front-end is a
**maintainer-side** esbuild bundle that vendors React + @xyflow/react (and its CSS) into
`src/figureflow/static/widget.js`. Use [bun](https://bun.sh):

```bash
bun install        # install front-end build dependencies
bun run build      # bundle js/index.js → src/figureflow/static/widget.js
bun run dev        # rebuild on change (--watch, with sourcemaps)
pip install -e .   # editable install of the Python package
```

`widget.js` is a checked-in build artifact — rebuild it after editing `js/index.js`.

The roadmap lives in [`docs/planning/`](docs/planning): `SKELETON.md` is the authoritative
target surface and `ITER_01`–`ITER_06` are the iterations that fill it in.

## License

See [LICENSE](LICENSE).
