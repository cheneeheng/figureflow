"""Anywidget adapter — notebook transport (adapter #1).

The representative implementation the other two adapters mirror. ``Flow`` remains
the v1 ``anywidget.AnyWidget`` subclass and stays the canonical state holder; this
adapter implements the ``Transport`` contract over ``Flow``'s own trait I/O rather
than wrapping a separate widget (SKELETON_V2 §04, ITER_V2_01 §04).

Because ``Flow`` *is* the widget, the live notebook data flow is the JS side of the
seam (renderer → JS ``Transport`` → anywidget JS adapter → ``model``). This Python
adapter is its server-side counterpart: it reads/writes the same synced traits and
routes any upstream observer through ``synccore.is_echo`` so a state we just pushed
is not re-committed. It registers no redundant commit path of its own — the v1
trait sync remains the single funnel (ITER_V2_01 §04).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from figureflow import synccore
from figureflow.transport.base import ChangeHandler, Transport

if TYPE_CHECKING:
    from figureflow import Flow


class AnywidgetAdapter(Transport):
    """Implements ``Transport`` over a ``Flow``'s anywidget trait channel."""

    def __init__(self) -> None:
        self._flow: Optional["Flow"] = None
        self._handler: Optional[ChangeHandler] = None
        self._last_pushed: Optional[synccore.State] = None

    def bind(self, flow: "Flow") -> None:
        """Attach to the canonical ``Flow`` (the trait-backed state holder)."""
        self._flow = flow

    def send_state(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        meta: Dict[str, Any],
    ) -> None:
        """Push canonical state down by writing the synced traits (v1 sync write)."""
        flow = self._require_flow()
        flow.nodes = list(nodes)
        flow.edges = list(edges)
        if "color_mode" in meta:
            flow.color_mode = meta["color_mode"]
        if "fit_view" in meta:
            flow.fit_view = meta["fit_view"]
        if "height" in meta:
            flow.height = meta["height"]
        self._last_pushed = {"nodes": list(nodes), "edges": list(edges)}

    def on_change(self, handler: ChangeHandler) -> None:
        """Observe trait writes, dropping echoes of our own pushes via the sync-core."""
        flow = self._require_flow()
        self._handler = handler

        def _observe(_change: Any) -> None:
            incoming: synccore.State = {
                "nodes": list(flow.nodes),
                "edges": list(flow.edges),
            }
            if synccore.is_echo(incoming, self._last_pushed):
                return
            handler(incoming)

        flow.observe(_observe, names=["nodes", "edges"])

    def emit(self, event: str, payload: Any) -> None:
        """Send a custom message down over the existing comm (v1 ``on()`` path)."""
        self._require_flow().send({"event": event, "payload": payload})

    # start/stop inherit the base no-ops (the kernel comm is managed by Jupyter).

    def _require_flow(self) -> "Flow":
        if self._flow is None:
            raise RuntimeError("AnywidgetAdapter used before bind()")
        return self._flow
