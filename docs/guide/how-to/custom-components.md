# Custom components (the L3 escape hatch)

When the built-in shapes and edge styles aren't enough, you can supply your own React
component written in JavaScript, and have it send events back to Python. This is the most
advanced feature and the only one that involves writing JavaScript.

**Prerequisites:**

- Comfortable with a little JavaScript / React.
- A way to make a small `.js` file reachable by the browser as a URL — a static file server,
  a published URL, or a `data:` URL (shown below).

**When you do *not* need this:** for static rich content, use a node's `html` field
([Style nodes → L2](style-nodes.md#escape-hatch-l2--raw-html-in-the-node-body)). For a custom
outline, use `svg_path` ([L1](style-nodes.md#escape-hatch-l1--a-custom-shape-from-an-svg-path)).
Reach for L3 only when you need interactivity or behavior.

## The contract

A custom node component is a plain JS module whose **default export** is a React function
component. figureflow calls it with `{ data, selected }`, and injects an `emit` function into
`data`:

```js
// my_node.js
const { React, xyflow: { Handle, Position } } = globalThis.figureflow;

export default function ClickableNode({ data, selected }) {
  const { emit } = data;                 // emit is delivered inside data
  return React.createElement(
    "div",
    {
      onClick: () => emit("clicked", { id: data.label }),
      style: {
        padding: "10px 16px",
        background: selected ? "#dbeafe" : "#f8fafc",
        border: "2px solid #3b82f6",
        borderRadius: 8,
        cursor: "pointer",
      },
    },
    React.createElement(Handle, { type: "target", position: Position.Top }),
    data.label,
    React.createElement(Handle, { type: "source", position: Position.Bottom })
  );
}
```

Two rules that matter:

1. **Get React from the global, never import it.** figureflow's front-end vendors its own
   React, so your module must read `globalThis.figureflow.React` (and the xyflow primitives
   it needs, like `Handle` and `Position`). Importing `"react"` directly loads a second copy
   of React and triggers the "invalid hook call" error.
2. **`emit` lives on `data`.** xyflow only passes user data through the `data` prop, so
   figureflow injects `emit` there. Destructure it as `const { emit } = data`.

TypeScript authors: the contract (`NodeProps`, `EdgeProps`, the `emit` signature, the
`globalThis.figureflow` global) is typed in `figureflow.d.ts`, shipped inside the package's
`static/` directory. You can compile against it externally; figureflow loads only plain `.js`
at runtime.

## Register the component and use it

In Python, register a **type name** pointing at your module's URL, then set that `type` on a
node:

```python
from figureflow import Flow, Node, Edge

flow = Flow(
    nodes=[
        Node("x", "Click me!", pos=(0, 0),   type="clickable"),
        Node("y", "Or me!",    pos=(200, 0), type="clickable"),
    ],
    edges=[Edge("x", "y")],
    height=300,
)

flow.register_node_type("clickable", "https://example.com/my_node.js")
flow
```

- `register_node_type(name, module)` — `name` must be a valid Python identifier and must not
  collide with the built-ins `shape` or `group`. `module` is a URL (or path) the browser can
  `import()`.
- `register_edge_type(name, module)` — same, for edges; `name` must not collide with
  `default`, `straight`, `step`, or `smoothstep`.
- A `Node(type=name)` (or `Edge(type=name)`) then renders with your component instead of the
  built-in one.

> **Errors:** an invalid or colliding `name` raises `ValueError`. If the module fails to
> load (bad URL, syntax error), figureflow logs a clear error to the browser console and
> falls back to the built-in renderer rather than crashing the canvas.

**Verify:** the two nodes render with your component's styling and respond to hover/click.

## Receive events in Python with `on()`

`emit(name, payload)` in the component sends an event to Python. Subscribe with `on()`:

```python
def on_clicked(payload):
    print("Node clicked:", payload)

unsubscribe = flow.on("clicked", on_clicked)
```

- `on(event, callback)` registers `callback` for `event` and returns an **unsubscribe**
  function — call `unsubscribe()` to stop listening.
- Multiple handlers per event are supported; each receives the `payload` your component
  passed to `emit`.

**Verify:** click a `clickable` node in the notebook — your handler prints the payload
(e.g. `Node clicked: {'id': 'Click me!'}`).

## Making the module reachable

`import(url)` runs in the browser, so the URL must be reachable from there. Options:

- **A served URL** (recommended for real projects): host `my_node.js` on a static server or
  any HTTPS URL.
- **A `data:` URL** (handy for a fully self-contained notebook): inline the module source.

```python
import urllib.parse

module_src = open("my_node.js").read()
data_url = "data:text/javascript," + urllib.parse.quote(module_src)
flow.register_node_type("clickable", data_url)
```

A bare relative path like `"./my_node.js"` only works if your Jupyter host actually serves
that file at that URL — which it usually does not. Prefer a served or `data:` URL.

## See also

- The runnable example: [`examples/custom_component.py`](../../../examples/custom_component.py).
- The typings: `src/figureflow/static/figureflow.d.ts`.
- [Save and load → Custom components across a round-trip](save-and-load.md#custom-components-across-a-round-trip).
