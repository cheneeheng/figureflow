"""Server adapter — plain browser, live bidirectional sync (MVP terminator).

A dependency-free stdlib ``ThreadingHTTPServer`` bound to localhost: SSE
(``GET /events``) carries Python→browser pushes, ``POST /change`` carries
browser→Python edits. The session (server object, daemon thread, connected SSE
streams) is transient infrastructure, not model state. Concurrency is guarded by
the single ``synccore.LOCK``; the echo loop is handled by reusing
``synccore.is_echo`` rather than inventing server-specific logic (SKELETON_V2 §04,
ITER_V2_03).

Skeleton state: gated. ``Flow.serve()`` and ``Flow.stop()`` raise
``NotImplementedError`` naming ITER_V2_03, which fills in this adapter, the routes,
and the server JS adapter.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, Dict

from figureflow.transport.base import ChangeHandler, Transport

if TYPE_CHECKING:
    from figureflow import Flow

_ITER = "ITER_V2_03"


class ServerAdapter(Transport):
    """Serves a ``Flow`` over a localhost stdlib SSE+POST HTTP server."""

    def bind(self, flow: "Flow") -> None:
        raise NotImplementedError(
            f"ServerAdapter.bind is implemented in {_ITER}"
        )

    def send_state(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        meta: Dict[str, Any],
    ) -> None:
        raise NotImplementedError(
            f"ServerAdapter.send_state is implemented in {_ITER}"
        )

    def on_change(self, handler: ChangeHandler) -> None:
        raise NotImplementedError(
            f"ServerAdapter.on_change is implemented in {_ITER}"
        )

    def emit(self, event: str, payload: Any) -> None:
        raise NotImplementedError(
            f"ServerAdapter.emit is implemented in {_ITER}"
        )

    def start(self) -> None:
        """Bind the server and run ``serve_forever`` on a daemon thread.

        Raises:
            NotImplementedError: Always — implemented in ITER_V2_03.
        """
        raise NotImplementedError(
            f"ServerAdapter.start is implemented in {_ITER}"
        )

    def stop(self) -> None:
        """Shut the server down and close open SSE streams.

        Raises:
            NotImplementedError: Always — implemented in ITER_V2_03.
        """
        raise NotImplementedError(
            f"ServerAdapter.stop is implemented in {_ITER}"
        )
