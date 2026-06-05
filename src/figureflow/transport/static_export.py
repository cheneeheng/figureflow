"""Static export adapter — frozen offline snapshot (one-way).

The cheapest consumer of the seam: state is baked in at write time, so there is
no live pipe. ``send_state`` never fires upstream; ``Flow.to_html()`` reuses the
v1 ``serialize.to_json`` envelope as a JSON island, inlines the vendored bundle,
and the browser-side static JS adapter captures client edits in-memory for a
one-way "download JSON" escape (SKELETON_V2 §04, ITER_V2_02).

Skeleton state: gated. ``Flow.to_html()`` raises ``NotImplementedError`` naming
ITER_V2_02, which fills in this adapter and the shared ``static/host.html``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Dict, Optional

from figureflow.transport.base import ChangeHandler, Transport

if TYPE_CHECKING:
    from figureflow import Flow

_ITER = "ITER_V2_02"


class StaticExportAdapter(Transport):
    """Renders a ``Flow`` to a self-contained, client-side-interactive page."""

    def bind(self, flow: "Flow") -> None:
        raise NotImplementedError(
            f"StaticExportAdapter.bind is implemented in {_ITER}"
        )

    def send_state(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        meta: Dict[str, Any],
    ) -> None:
        raise NotImplementedError(
            f"StaticExportAdapter.send_state is implemented in {_ITER}"
        )

    def on_change(self, handler: ChangeHandler) -> None:
        raise NotImplementedError(
            f"StaticExportAdapter.on_change is implemented in {_ITER}"
        )

    def emit(self, event: str, payload: Any) -> None:
        raise NotImplementedError(
            f"StaticExportAdapter.emit is implemented in {_ITER}"
        )

    def render_html(
        self, flow: "Flow", *, title: Optional[str] = None
    ) -> str:
        """Produce the self-contained HTML snapshot string.

        Raises:
            NotImplementedError: Always — implemented in ITER_V2_02.
        """
        raise NotImplementedError(
            f"StaticExportAdapter.render_html is implemented in {_ITER}"
        )

    # start/stop inherit the base no-ops (no live pipe).
