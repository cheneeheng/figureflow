"""serialization.py — lossless to_json / from_json round-trip + lossy to_mermaid.

Run it as a script to perform the round-trip and print the mermaid export:

    python examples/serialization.py

Or paste the diagram into a notebook cell and end the cell with ``flow`` to render it.
"""
from figureflow import Edge, Flow, Node, Shape


def build() -> Flow:
    return Flow(
        nodes=[
            Node("start", "Start",   pos=(0,   0), shape=Shape.stadium,   fill="#e8f0fe"),
            Node("proc",  "Process", pos=(0, 120), shape=Shape.rectangle, fill="#ffffff"),
            Node("end",   "End",     pos=(0, 240), shape=Shape.stadium,   fill="#e6f4ea"),
        ],
        edges=[
            Edge("start", "proc", label="next"),
            Edge("proc",  "end",  label="done", dash="dashed"),
        ],
    )


flow = build()

if __name__ == "__main__":
    # Lossless JSON round-trip.
    snapshot = flow.to_json()
    print("JSON snapshot:", len(snapshot), "chars")

    restored = Flow.from_json(snapshot)
    assert len(restored.nodes) == len(flow.nodes)
    assert len(restored.edges) == len(flow.edges)
    assert restored.to_json() == snapshot   # exact round-trip
    print("Round-trip OK — from_json(to_json(flow)) reproduces the diagram.")

    # Lossy mermaid export (structure + labels only).
    print("\nmermaid export:\n")
    print(flow.to_mermaid(direction="TB"))
    print("\nDisplay it: paste this file's diagram into a notebook cell ending with `flow`.")
