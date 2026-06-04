"""custom_component.py — L3 escape hatch: register_node_type + emit/on.

The custom component is defined as a separate JS file. Save the snippet below
as `my_node.js` and serve it from a local file server, or use a data URL.

my_node.js:
    const { React, xyflow: { Handle, Position } } = globalThis.figureflow;
    export default function ClickableNode({ data, selected, emit }) {
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
from figureflow import Flow, Node, Edge

flow = Flow(
    nodes=[
        Node("x", "Click me!",  pos=(0,   0),   type="clickable"),
        Node("y", "Or me!",     pos=(200, 0),   type="clickable"),
    ],
    edges=[Edge("x", "y")],
    height=300,
)

# Register the custom component
flow.register_node_type("clickable", "./my_node.js")

# Subscribe to click events
def on_clicked(payload):
    print("Node clicked:", payload)

unsubscribe = flow.on("clicked", on_clicked)

flow  # display in a notebook cell
