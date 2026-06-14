"""05_display_targets.py — one Flow, three transports: display() / to_html() / serve().

The same diagram ships to a notebook, a frozen offline file, or a live browser tab
through the v2 transport seam. Run it as a script to write a static snapshot and
(optionally) start the live server:

    python examples/05_display_targets.py            # writes diagram.html
    python examples/05_display_targets.py --serve    # also serves a live browser tab

Or paste the diagram into a notebook cell and end the cell with ``flow`` to render it
(that auto-render is exactly what ``flow.display()`` returns).
"""
from __future__ import annotations

import sys

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
    # 1) Notebook door — returns the widget (self); a bare `flow` cell renders it too.
    assert flow.display() is flow

    # 2) Static door — a self-contained, offline, interactive snapshot.
    html = flow.to_html("diagram.html", title="Display targets")
    print(f"Wrote diagram.html ({len(html)} chars) — open it with no network.")
    print("In the browser, rearrange nodes and click 'Download JSON' to export them;")
    print("Flow.from_json(open('figureflow.json').read()) reimports that layout.")

    # 3) Server door — live bidirectional sync in a plain browser tab (localhost only).
    # One live adapter per Flow at a time (ITER_V2_04): `flow` above is bound to
    # the notebook door by display(), so the live server gets its own Flow.
    if "--serve" in sys.argv:
        live = build()
        url = live.serve()  # prints + returns the URL; opens the browser
        print(f"Serving live at {url} — drag a node, then check live.positions().")
        try:
            input("Press Enter to stop the server...\n")
        finally:
            live.stop()
    else:
        print("Pass --serve to also start the live server (flow.serve()).")
