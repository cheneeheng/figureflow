"""serialization.py — to_json / from_json round-trip + to_mermaid."""
from figureflow import Flow, Node, Edge, Shape

flow = Flow(
    nodes=[
        Node("start", "Start", pos=(0,   0),   shape=Shape.stadium,    fill="#e8f0fe"),
        Node("proc",  "Process",pos=(0, 120),  shape=Shape.rectangle,  fill="#ffffff"),
        Node("end",   "End",   pos=(0, 240),   shape=Shape.stadium,    fill="#e6f4ea"),
    ],
    edges=[
        Edge("start", "proc", label="→"),
        Edge("proc",  "end",  label="done", dash="dashed"),
    ],
)

# Lossless JSON round-trip
snapshot = flow.to_json()
print("JSON length:", len(snapshot), "chars")

restored = Flow.from_json(snapshot)
assert len(restored.nodes) == len(flow.nodes)
assert len(restored.edges) == len(flow.edges)
print("Round-trip OK")

# Mermaid export (lossy — structural only)
mermaid = flow.to_mermaid(direction="TD")
print("\nMermaid output:")
print(mermaid)
