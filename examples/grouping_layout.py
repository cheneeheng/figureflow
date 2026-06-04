"""grouping_layout.py — group() and layout()."""
from figureflow import Flow, Node, Edge, Shape

flow = Flow(
    nodes=[
        Node("a", "Fetch",   pos=(0,   0),   shape=Shape.rounded, fill="#e0f2fe"),
        Node("b", "Parse",   pos=(160, 0),   shape=Shape.rounded, fill="#e0f2fe"),
        Node("c", "Validate",pos=(320, 0),   shape=Shape.rounded, fill="#e0f2fe"),
        Node("d", "Store",   pos=(0,   160), shape=Shape.cylinder, fill="#f0fdf4"),
        Node("e", "Notify",  pos=(160, 160), shape=Shape.stadium,  fill="#fef9c3"),
    ],
    edges=[
        Edge("a", "b"), Edge("b", "c"), Edge("c", "d"), Edge("c", "e"),
    ],
    height=480,
)

# Group the ETL pipeline steps
group_id = flow.group(["a", "b", "c"], label="ETL Pipeline")
print("group id:", group_id)

# Auto-arrange with dagre (left-to-right)
flow.layout(direction="LR")

flow  # display in a notebook cell
