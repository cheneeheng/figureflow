# figureflow

Interactive flow diagrams in Python, styled shape-by-shape.

The Python package is **`pyxyflow`** — an [anywidget](https://anywidget.dev)
wrapper around [React Flow](https://reactflow.dev) (`@xyflow/react`). It renders
an interactive flowchart in any Jupyter host (JupyterLab, Notebook, Colab, VS
Code, marimo) from a single pip install, with the front-end bundled into the
wheel so it runs offline with no CDN.

> **Status:** skeleton. The construct → display → drag → read-back loop is wired;
> per-element shape/styling, undo/redo, grouping, layout, save/load and the
> custom-component escape hatch are stubbed and gated to named iterations
> (`docs/planning/`).

## Usage

```python
from pyxyflow import Flow, Node, Edge

flow = Flow(
    nodes=[Node("a", "Start"), Node("b", "End", pos=(200, 100))],
    edges=[Edge("a", "b")],
)
flow  # display in a notebook cell

flow.positions()  # {"a": (0.0, 0.0), "b": (200.0, 100.0)} — updates after dragging
```

## Install / run

End users install from a built wheel (no JS toolchain required):

```bash
pip install pyxyflow
```

### Maintainer / from source

The front-end bundle (`src/pyxyflow/static/widget.js`) is built with esbuild and
is not checked in; build it before an editable install:

```bash
npm install && npm run build   # esbuild -> src/pyxyflow/static/widget.js
pip install -e .
```
