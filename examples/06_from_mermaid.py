"""06_from_mermaid.py — author a diagram from a mermaid flowchart (v3 ingestion).

``Flow.from_mermaid()`` parses a pinned flowchart subset into a live Flow: node shapes
map from the bracket syntax, edge labels carry over, and a ``subgraph … end`` block
imports as a one-level group. The mermaid text has no coordinates, so every node is
*unplaced* and the renderer auto-lays them out on mount via ``layout_direction``.

    python examples/06_from_mermaid.py

Or paste the diagram into a notebook cell and end the cell with ``flow`` to render it.
"""
from __future__ import annotations

from figureflow import Flow

MERMAID = """flowchart TD
    A([Submit request]) --> B{Reviewer}
    B -->|approve| C[Provision access]
    B -->|reject| D[Send rejection]
    C --> E([Done])
    D --> E
"""


def build() -> Flow:
    # from_mermaid routes through the same v3 validate() funnel as from_json.
    return Flow.from_mermaid(MERMAID)


flow = build()

if __name__ == "__main__":
    print(
        f"Parsed {len(flow.nodes)} nodes, {len(flow.edges)} edges "
        f"(layout_direction={flow.layout_direction!r} — from the `flowchart TD` header)."
    )
    # Mermaid carries no coordinates: positions() reports only placed nodes, so it is
    # empty here — the renderer auto-arranges every node on mount.
    print("Placed nodes:", flow.positions() or "none — renderer auto-lays on mount")
    print("\nDisplay it: paste this file's diagram into a notebook cell ending with `flow`.")
