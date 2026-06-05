"""Anywidget adapter — notebook transport (adapter #1).

The representative implementation the other two adapters mirror. ``Flow`` remains
the v1 ``anywidget.AnyWidget`` subclass and stays the canonical state holder; this
adapter implements the ``Transport`` contract over ``Flow``'s own trait I/O rather
than wrapping a separate widget (SKELETON_V2 §04, ITER_V2_01 §04).

Skeleton state: gated. ``Flow.display()`` still renders the v1 way (it returns the
``AnyWidget`` directly); ITER_V2_01 moves that call path behind this adapter with
no behavior change.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Dict

from figureflow.transport.base import ChangeHandler, Transport

if TYPE_CHECKING:
    from figureflow import Flow

_ITER = "ITER_V2_01"


class AnywidgetAdapter(Transport):
    """Implements ``Transport`` over a ``Flow``'s anywidget trait channel."""

    def bind(self, flow: "Flow") -> None:
        raise NotImplementedError(
            f"AnywidgetAdapter.bind is implemented in {_ITER}"
        )

    def send_state(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        meta: Dict[str, Any],
    ) -> None:
        raise NotImplementedError(
            f"AnywidgetAdapter.send_state is implemented in {_ITER}"
        )

    def on_change(self, handler: ChangeHandler) -> None:
        raise NotImplementedError(
            f"AnywidgetAdapter.on_change is implemented in {_ITER}"
        )

    def emit(self, event: str, payload: Any) -> None:
        raise NotImplementedError(
            f"AnywidgetAdapter.emit is implemented in {_ITER}"
        )

    # start/stop inherit the base no-ops (the kernel comm is managed by Jupyter).
