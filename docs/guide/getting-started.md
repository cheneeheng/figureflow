# Getting started

Install figureflow and display your first interactive diagram.

## Before you begin

- **Python 3.9 or newer.**
- **A Jupyter host** to see the interactive canvas: JupyterLab, classic Notebook, Google
  Colab, VS Code (with the Jupyter extension), or marimo. Any one works — the same widget
  renders in all of them.
- No JavaScript toolchain. The front-end ships prebuilt inside the package and runs
  offline (no CDN, no network fetch).

## Install

```bash
pip install figureflow
```

Installing from a source checkout instead:

```bash
pip install -e .
```

**Verify the install** from a terminal:

```bash
python -c "import figureflow; print(figureflow.__all__)"
```

Expected output:

```
['Shape', 'Node', 'Edge', 'Flow']
```

If you see those four names, the package is installed.

## Display your first diagram

1. Start your notebook host (for example, `jupyter lab`).
2. In a cell, build a `Flow` and put the variable on the **last line** so the cell renders it:

   ```python
   from figureflow import Flow, Node, Edge, Shape

   flow = Flow(
       nodes=[
           Node("a", "Start",   pos=(0,   0), shape=Shape.stadium, fill="#e8f0fe"),
           Node("b", "Process", pos=(0, 120)),
           Node("c", "Done",    pos=(0, 240), shape=Shape.stadium, fill="#e6f4ea"),
       ],
       edges=[
           Edge("a", "b"),
           Edge("b", "c", label="result", dash="dashed"),
       ],
       height=480,
   )
   flow
   ```

3. Run the cell.

**Verify:** a canvas appears with three nodes connected top-to-bottom, a minimap in the
bottom-right corner, and zoom controls in the bottom-left. Drag a node — it moves and
stays where you drop it.

**If nothing renders:** see [Troubleshooting → The widget doesn't appear](troubleshooting.md#the-widget-doesnt-appear).

## Read your edits back into Python

After dragging nodes on the canvas, run a new cell to read the current geometry:

```python
flow.positions()
# {'a': (40.0, -12.0), 'b': (0.0, 120.0), 'c': (0.0, 240.0)}
```

The coordinates reflect where the nodes sit on the canvas right now. This is the core
loop: **build in Python → arrange on the canvas → read back in Python.**

## Run the bundled examples

The repository ships runnable examples in [`examples/`](../../examples). Each one builds a
diagram and prints a summary, so you can run it straight from a terminal:

```bash
python examples/01_quickstart.py
```

Then copy the same code into a notebook cell (ending with `flow`) to see it rendered. See
[`examples/README.md`](../../examples/README.md) for what each script demonstrates.

## Next steps

- [Style nodes](how-to/style-nodes.md) — pick shapes and colors.
- [Style edges](how-to/style-edges.md) — arrowheads, dashes, labels.
- [Edit on the canvas](how-to/edit-on-canvas.md) — select, copy/paste, undo/redo.
