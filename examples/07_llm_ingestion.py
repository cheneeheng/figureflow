"""07_llm_ingestion.py — the v3 repair loop: one error lists every problem at once.

``from_json`` (and ``from_mermaid``, and the MCP tools) route through a single
``validate()`` funnel that *collects* every fault into one ``FlowValidationError``
instead of failing on the first. An LLM reads all the lines, fixes them together, and
re-emits once — the loop that makes coordinate-free authoring robust.

    python examples/07_llm_ingestion.py
"""
from __future__ import annotations

from figureflow import Flow, FlowValidationError

# Round 1 — three faults: an invalid shape, a duplicate id, and a dangling edge target.
BROKEN = """{
  "schema": "figureflow/1",
  "nodes": [
    {"id": "a", "data": {"label": "Start", "shape": "circle"}},
    {"id": "a", "data": {"label": "Work", "shape": "rectangle"}}
  ],
  "edges": [{"source": "a", "target": "end"}]
}"""

# Round 2 — every fault fixed together: rename the duplicate, pick a valid shape
# (`ellipse`, the closest intent to "circle"), and add the missing `end` node.
FIXED = """{
  "schema": "figureflow/1",
  "nodes": [
    {"id": "start", "data": {"label": "Start", "shape": "ellipse"}},
    {"id": "work", "data": {"label": "Work", "shape": "rectangle"}},
    {"id": "end", "data": {"label": "End", "shape": "stadium"}}
  ],
  "edges": [
    {"source": "start", "target": "work"},
    {"source": "work", "target": "end"}
  ]
}"""


def build() -> Flow:
    return Flow.from_json(FIXED)


flow = build()

if __name__ == "__main__":
    # Round 1: every problem comes back in one error, one repair-friendly line each.
    try:
        Flow.from_json(BROKEN)
    except FlowValidationError as exc:
        print("Round 1 — validate() collected every problem at once:\n")
        print(exc)
        print(f"\n({len(exc.problems)} problems in one error — not fail-on-first.)")

    # Round 2: the repaired emission validates cleanly and renders laid-out — no
    # coordinates were ever emitted, so the renderer places the nodes on mount.
    print("\nRound 2 — repaired input validates cleanly:")
    print(f"  {len(flow.nodes)} nodes, {len(flow.edges)} edges, no coordinates emitted.")
    print("\nDisplay it: paste FIXED into a notebook cell as `Flow.from_json(FIXED)`.")
