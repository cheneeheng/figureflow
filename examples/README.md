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
python examples/quickstart.py
python examples/grouping_layout.py
python examples/serialization.py
python examples/custom_component.py
python examples/display_targets.py        # add --serve for the live browser tab
```

| Example | Demonstrates |
|---------|--------------|
| [`quickstart.py`](quickstart.py) | All 8 node shapes, the L1 `svg_path` and L2 `html` escape hatches, and the four edge path types with markers/dashes/labels. |
| [`grouping_layout.py`](grouping_layout.py) | `Flow.group()` to bundle nodes into a labeled container, then `Flow.layout()` to auto-arrange with dagre. |
| [`serialization.py`](serialization.py) | Lossless `to_json()` / `from_json()` round-trip and a lossy `to_mermaid()` export. |
| [`custom_component.py`](custom_component.py) | The L3 escape hatch — a custom JS node registered via `register_node_type`, sending click events to Python through `emit` / `Flow.on`. |
| [`display_targets.py`](display_targets.py) | One `Flow`, three transports: `display()` (notebook), `to_html()` (offline snapshot), and `serve()` (live browser tab). |

## Seeing the interactive widget

The drag-and-drop canvas only renders inside a notebook (JupyterLab, Notebook, Colab, VS
Code, marimo). To view an example live, either:

- copy the diagram from the script into a notebook cell and make the **last line** `flow`, or
- import the prebuilt flow and display it:

  ```python
  from examples.quickstart import flow
  flow
  ```

`grouping_layout.py` and `custom_component.py` are most interesting in a notebook —
`layout()` re-arranges the canvas, and the custom component responds to clicks. Running them
as scripts still works and prints the Python-side state.

For full walkthroughs, see the [user manual](../docs/guide/index.md).
