# Troubleshooting

Symptom → fix for the most common stumbles. If your issue isn't here, check the
[reference](reference.md) for exact signatures and defaults.

## The widget doesn't appear

A blank cell, a text repr like `Flow()`, or an error instead of a canvas.

- **The `Flow` isn't the last line of the cell.** A widget renders only when it is the
  cell's final expression. End the cell with the bare variable:
  ```python
  flow
  ```
- **anywidget/Jupyter front-end is stale.** Restart the kernel and refresh the browser tab.
  In JupyterLab, make sure the install is in the *same* environment the kernel runs in
  (`import sys; print(sys.executable)` in a cell, then `pip install figureflow` for that
  interpreter).
- **Running as a script, not in a notebook.** `python my_diagram.py` builds the `Flow` but
  cannot draw it — the interactive canvas needs a notebook. Inspect it from Python instead
  (`flow.positions()`, `flow.to_mermaid()`), or open the code in a notebook cell.

**Verify the install itself** independently of rendering:
```bash
python -c "import figureflow; print(figureflow.__all__)"
# ['Shape', 'Node', 'Edge', 'Flow']
```

## A node shows as a plain box, ignoring its shape

- **`svg_path`, `html`, or a custom `type` is set.** Each overrides the built-in `shape`:
  `svg_path` and a custom `type` replace the shape geometry, and `html` replaces the label.
  Clear the field you didn't mean to set.
- **`shape` passed as a bare string.** Use the enum: `shape=Shape.diamond`, not
  `shape="diamond"` (a raw string that isn't a known shape falls back to a plain box).

## My custom (L3) component doesn't render / "invalid hook call"

- **The module imports React directly.** Read React from the global instead:
  `const { React } = globalThis.figureflow;`. Importing `"react"` loads a second React and
  triggers the invalid-hook-call error. See
  [Custom components](how-to/custom-components.md#the-contract).
- **The module URL isn't reachable by the browser.** `import(url)` runs in the browser; a
  bare `"./my_node.js"` usually isn't served. Use an HTTPS URL or a `data:` URL
  ([how-to](how-to/custom-components.md#making-the-module-reachable)). A failed load logs a
  clear error to the **browser console** and falls back to the built-in renderer — open the
  console to see it.
- **`emit` is undefined.** It is delivered inside `data`, not as a top-level prop:
  `const { emit } = data;`.

## `flow.positions()` looks stale

Positions reflect the **last sync** from the canvas. A drag commits when you **release** the
mouse, not while dragging — finish the drag, then read `positions()` in a new cell. If you
just ran a layout, the new coordinates are available immediately after `layout()` returns.

## `group()` raised `ValueError`

- You passed an empty list, or ids that don't exist in the flow. Pass the ids of nodes that
  are already in the `Flow`. See [Group and lay out](how-to/group-and-layout.md).

## `layout()` raised `ValueError`

- **`algo` other than `"dagre"`** — only dagre is supported in v0.1.
- **`direction` outside `TB`/`BT`/`LR`/`RL`** — use one of those four.

## `from_json()` raised "Unsupported figureflow schema"

The snapshot was written by an incompatible schema version. figureflow `0.1.x` reads and
writes schema `figureflow/1`. Re-export the diagram from a compatible version, or hand-edit
the `"schema"` field only if you know the formats match.

## Undo did nothing

- **The history is empty or was cleared.** `load_json()` clears the undo history, and only
  *canvas* edits are tracked. Programmatic edits (`add_node`, `add_edge`, `group`,
  `layout` is tracked; `add_*` is not) and a fresh load have nothing to undo. See
  [Edit on the canvas → Undo and redo](how-to/edit-on-canvas.md#undo-and-redo).

## Colors/fonts disappeared after exporting to mermaid

Expected — `to_mermaid()` is a **structural** export. Shapes, edges, and labels survive;
per-element colors, fonts, and `svg_path`/`html` bodies do not. Use `to_json()` for a
lossless save. See [Save and load](how-to/save-and-load.md).
