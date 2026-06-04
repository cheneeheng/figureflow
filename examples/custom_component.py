"""custom_component.py — the L3 escape hatch: register_node_type + emit/on.

A custom node is a plain JS module whose default export is a React function
component. It must read React from ``globalThis.figureflow`` (not ``import "react"``)
so it shares figureflow's vendored React instance, and it sends events to Python by
calling ``emit(name, payload)`` (delivered inside ``data``).

This example inlines the module as a ``data:`` URL so it works in a notebook with no
external file server. Run as a script to print the setup:

    python examples/custom_component.py

Then paste the diagram into a notebook cell ending with ``flow`` to render it and
click a node — the Python ``on("clicked", ...)`` handler fires with the payload.
"""
import urllib.parse

from figureflow import Edge, Flow, Node

# ── The custom node component (plain JS / React via the figureflow global) ──────
MODULE_SRC = """
const { React, xyflow: { Handle, Position } } = globalThis.figureflow;
export default function ClickableNode({ data, selected }) {
  const { emit } = data;                 // emit is injected into data by figureflow
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
"""

# A data: URL makes the module reachable by the browser without a file server.
MODULE_URL = "data:text/javascript," + urllib.parse.quote(MODULE_SRC)


def build() -> Flow:
    return Flow(
        nodes=[
            Node("x", "Click me!", pos=(0,   0), type="clickable"),
            Node("y", "Or me!",    pos=(200, 0), type="clickable"),
        ],
        edges=[Edge("x", "y")],
        height=300,
    )


flow = build()

# Register the custom component under the type name used on the nodes above.
flow.register_node_type("clickable", MODULE_URL)


# Subscribe to the events the component emits. on() returns an unsubscribe handle.
def on_clicked(payload):
    print("Node clicked:", payload)


unsubscribe = flow.on("clicked", on_clicked)

if __name__ == "__main__":
    print("Registered node types:", list(flow._node_modules.keys()))
    print("Nodes using a custom type:",
          [n["id"] for n in flow.nodes if n.get("type") == "clickable"])
    print("\nThis example is interactive — render it in a notebook (end a cell with `flow`)")
    print("and click a node to see the on('clicked', ...) handler fire.")
    print("Call unsubscribe() to stop listening.")
