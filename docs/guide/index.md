# figureflow User Manual

**figureflow** builds interactive flow diagrams in Python and renders them in any
Jupyter host (JupyterLab, Notebook, Colab, VS Code, marimo). You describe nodes and
edges with Python, style each one per-element — shape, fill, border, font — and display
the result as a live, draggable canvas. No JavaScript required, and it runs offline (the
front-end is bundled into the wheel; no CDN).

This manual is for **people using figureflow to build diagrams**. It is organized by what
you want to *do*, not by what the library *has* — start at Getting started, then jump to
the how-to for your task.

## Contents

1. [Getting started](getting-started.md) — install figureflow and display your first diagram.
2. How-to guides — one task each:
   - [Style nodes](how-to/style-nodes.md) — shapes, fills, borders, fonts, custom SVG, raw HTML.
   - [Style edges](how-to/style-edges.md) — path type, arrowheads, dashes, labels.
   - [Edit on the canvas](how-to/edit-on-canvas.md) — drag, select, copy/paste, undo/redo, read positions back.
   - [Group and lay out](how-to/group-and-layout.md) — group nodes and auto-arrange with dagre.
   - [Save and load](how-to/save-and-load.md) — JSON round-trip and mermaid export.
   - [Import a diagram](how-to/import-diagrams.md) — `from_mermaid`, coordinate-free `from_json`, and repair-friendly validation.
   - [Display anywhere](how-to/display-anywhere.md) — notebook, live browser tab (`serve()`), or offline HTML (`to_html()`).
   - [Custom components](how-to/custom-components.md) — the L3 escape hatch: your own JS node + `emit`/`on`.
3. [Reference](reference.md) — full API, every style field, the shape table, keyboard shortcuts.
4. [Troubleshooting](troubleshooting.md) — symptom → fix for common stumbles.

**Operating the MCP server?** Letting an AI agent drive a live diagram is an operator task with
its own runbook: [MCP server](operations/mcp-server.md) — install, register a client, run, and
recover. Everyday diagram-building does not need it.

## The mental model

A diagram is a `Flow` holding a list of `Node`s and a list of `Edge`s:

```python
from figureflow import Flow, Node, Edge, Shape

flow = Flow(
    nodes=[
        Node("a", "Start",   pos=(0,   0), shape=Shape.stadium, fill="#e8f0fe"),
        Node("b", "Process", pos=(0, 120), shape=Shape.rectangle),
        Node("c", "Done",    pos=(0, 240), shape=Shape.stadium, fill="#e6f4ea"),
    ],
    edges=[
        Edge("a", "b"),
        Edge("b", "c", dash="dashed", label="result"),
    ],
    height=480,
)
flow  # last line of a notebook cell → renders the widget
```

Every visual choice lives on the element you set it on. Styling a node or edge is exactly
like formatting a single shape in a drawing tool — there is no global theme to manage.

> **Where to run it:** the live, interactive canvas only appears inside a notebook (the
> last expression in a cell must evaluate to the `Flow`). Running a `.py` file in a plain
> terminal builds the diagram and lets you inspect it from Python, but does not draw it.
> See [Getting started](getting-started.md).
