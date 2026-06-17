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
# ['Shape', 'Node', 'Edge', 'Flow', 'FlowValidationError', 'MermaidParseError']
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

## `from_json()` / `from_mermaid()` raised an error with several lines

Import does not stop at the first mistake — it **collects every problem** and raises one
`FlowValidationError` (JSON) or `MermaidParseError` (mermaid), one line per problem in the form
`path: what is wrong. hint`. Read all the lines and fix them together, then re-import once.
Common faults: an unknown `shape`, a duplicate node id, an edge naming a node that doesn't exist,
or an unsupported `schema` major version. The structured list is on `exc.problems`. See
[Import a diagram](how-to/import-diagrams.md#fix-a-bad-diagram-in-one-pass).

## Import rejected something I expected it to accept

- **`strict=True` is on.** Under strict mode, forgiving fix-ups (numeric strings like `"13"`,
  unknown keys folded into `data`, skipped mermaid style directives) become errors. Drop
  `strict=True` to let them pass with a warning.
- **The mermaid uses an unsupported construct.** Only flowcharts import, and only the bounded
  grammar in [Import a diagram → What mermaid is supported](how-to/import-diagrams.md#what-mermaid-is-supported).
  `sequenceDiagram`/`classDiagram`/`gantt`/etc. fail by design with a message naming the type;
  `classDef`/`style`/nested subgraphs are skipped with a warning, not imported.

## Imported nodes overlap, or sit in the wrong place

Imported diagrams are auto-laid out because their nodes are **unplaced**. If you mixed authored
positions with unplaced nodes, an auto-placed node can land on an authored one — drag it clear,
or call `flow.layout()` to re-arrange the whole graph ([Group and lay out](how-to/group-and-layout.md)).
For an all-unplaced import (the usual case) this does not happen.

## `flow.positions()` is empty right after import

Expected for an all-unplaced diagram you haven't displayed yet — `positions()` reports only
*placed* nodes. The renderer places unplaced nodes on the first render; display the flow (or call
`flow.layout()`), then read `positions()` again. See
[Import a diagram → Positions are optional](how-to/import-diagrams.md#positions-are-optional).

## Undo did nothing

- **The history is empty or was cleared.** `load_json()` clears the undo history, and only
  *canvas* edits are tracked. Programmatic edits (`add_node`, `add_edge`, `group`,
  `layout` is tracked; `add_*` is not) and a fresh load have nothing to undo. See
  [Edit on the canvas → Undo and redo](how-to/edit-on-canvas.md#undo-and-redo).

## Colors/fonts disappeared after exporting to mermaid

Expected — `to_mermaid()` is a **structural** export. Shapes, edges, and labels survive;
per-element colors, fonts, and `svg_path`/`html` bodies do not. Use `to_json()` for a
lossless save. See [Save and load](how-to/save-and-load.md).
