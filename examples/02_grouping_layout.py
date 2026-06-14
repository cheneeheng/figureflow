"""02_grouping_layout.py — group() bundles nodes; layout() auto-arranges with dagre.

Run it as a script to print the group id and the arranged coordinates:

    python examples/02_grouping_layout.py

Or paste this into a notebook cell and end the cell with ``flow`` to render the
interactive widget.
"""
from figureflow import Edge, Flow, Node, Shape


def build() -> Flow:
    return Flow(
        nodes=[
            Node("a", "Fetch",    pos=(0,   0),   shape=Shape.rounded,  fill="#e0f2fe"),
            Node("b", "Parse",    pos=(160, 0),   shape=Shape.rounded,  fill="#e0f2fe"),
            Node("c", "Validate", pos=(320, 0),   shape=Shape.rounded,  fill="#e0f2fe"),
            Node("d", "Store",    pos=(0,   160), shape=Shape.cylinder, fill="#f0fdf4"),
            Node("e", "Notify",   pos=(160, 160), shape=Shape.stadium,  fill="#fef9c3"),
        ],
        edges=[
            Edge("a", "b"), Edge("b", "c"), Edge("c", "d"), Edge("c", "e"),
        ],
        height=480,
    )


flow = build()

# Group the ingest steps into a labeled container.
group_id = flow.group(["a", "b", "c"], label="ETL Pipeline")

# Auto-arrange left-to-right with dagre. (In a notebook the canvas re-arranges;
# the new coordinates are also available immediately via flow.positions().)
flow.layout(direction="LR")

if __name__ == "__main__":
    print(f"Created group: {group_id}")
    print(f"Flow now has {len(flow.nodes)} nodes ({sum(1 for n in flow.nodes if n.get('type') == 'group')} group).")
    print("\nChildren of the group (parent-relative positions):")
    for n in flow.nodes:
        if n.get("parentId") == group_id:
            p = n["position"]
            print(f"  {n['id']}: ({p['x']:.0f}, {p['y']:.0f})  extent={n.get('extent')}")
    print("\nDisplay it: paste this file's diagram into a notebook cell ending with `flow`.")
