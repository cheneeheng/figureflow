# figureflow examples

Runnable examples covering the main features. Each script **builds a diagram** and prints a
text summary, so you can run it from a terminal — then drop the same code into a notebook
cell (ending with `flow`) to see the live, interactive widget.

## Setup

```bash
pip install figureflow      # or, from a source checkout: pip install -e .
```

## Run

```bash
python examples/01_quickstart.py
python examples/02_grouping_layout.py
python examples/03_serialization.py
python examples/04_custom_component.py
python examples/05_display_targets.py     # add --serve for the live browser tab
```

| Example | Demonstrates |
|---------|--------------|
| [`01_quickstart.py`](01_quickstart.py) | All 8 node shapes, the L1 `svg_path` and L2 `html` escape hatches, and the four edge path types with markers/dashes/labels. |
| [`02_grouping_layout.py`](02_grouping_layout.py) | `Flow.group()` to bundle nodes into a labeled container, then `Flow.layout()` to auto-arrange with dagre. |
| [`03_serialization.py`](03_serialization.py) | Lossless `to_json()` / `from_json()` round-trip and a lossy `to_mermaid()` export. |
| [`04_custom_component.py`](04_custom_component.py) | The L3 escape hatch — a custom JS node registered via `register_node_type`, sending click events to Python through `emit` / `Flow.on`. Shows the base handler plus the two notebook-safe patterns: **A** collect payloads into a list to inspect in a later cell, and **B** route them into an `ipywidgets.Output` to watch live. |
| [`05_display_targets.py`](05_display_targets.py) | One `Flow`, three transports: `display()` (notebook), `to_html()` (offline snapshot), and `serve()` (live browser tab). |

## Canvas controls

In the interactive widget:

- **Left-drag** — box-select nodes.
- **Ctrl/Cmd + left-drag** (or middle/right-drag) — pan the canvas.
- **Shift + click** — add to the selection.

## Seeing the interactive widget

The drag-and-drop canvas only renders inside a notebook (JupyterLab, Notebook, Colab, VS
Code, marimo). To view an example live, either:

- copy the diagram from the script into a notebook cell and make the **last line** `flow`, or
- load the prebuilt flow from the script and display it. The filenames start with a digit,
  so they are not importable as `examples.01_quickstart` — load them by path instead:

  ```python
  import importlib.util, pathlib

  spec = importlib.util.spec_from_file_location(
      "quickstart", pathlib.Path("examples/01_quickstart.py")
  )
  mod = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(mod)
  mod.flow
  ```

`02_grouping_layout.py` and `04_custom_component.py` are most interesting in a notebook —
`layout()` re-arranges the canvas, and the custom component responds to clicks. Running them
as scripts still works and prints the Python-side state.

For full walkthroughs, see the [user manual](../docs/guide/index.md).
