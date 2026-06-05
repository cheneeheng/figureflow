"""The Transport contract — the seam every adapter implements.

One canonical ``Flow`` state, one renderer, three interchangeable pipes. An
adapter reads/writes the diagram through the shared sync-core (``synccore``),
never poking trait internals directly, so the diff and echo-guard are solved once
(SKELETON_V2 §02, §04).

This module defines the full contract in the skeleton because it *is* the seam
being drawn. The concrete adapters are honestly gated until their iterations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Dict, List

if TYPE_CHECKING:
    from figureflow import Flow

# An upstream handler receives a committed canvas edit as a patch dict.
ChangeHandler = Callable[[Dict[str, Any]], None]


class Transport(ABC):
    """Abstract pipe between the canonical ``Flow`` and the React renderer.

    ``start``/``stop`` default to no-ops so the static adapter (ITER_V2_02),
    which has no live pipe, inherits them for free.
    """

    @abstractmethod
    def bind(self, flow: "Flow") -> None:
        """Attach to the canonical ``Flow``.

        The adapter reads/writes its nodes/edges through the sync-core, never
        poking trait internals directly.

        Args:
            flow: The canonical state holder.
        """

    @abstractmethod
    def send_state(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        meta: Dict[str, Any],
    ) -> None:
        """Push canonical state down to the browser.

        Args:
            nodes: The node payloads in channel (``to_dict``) form.
            edges: The edge payloads in channel form.
            meta: Flow-level settings — ``color_mode``, ``fit_view``, ``height``.
        """

    @abstractmethod
    def on_change(self, handler: ChangeHandler) -> None:
        """Register the upstream handler for browser-committed edits.

        The handler funnels through the sync-core so the echo-guard and v1's undo
        seam still see exactly one commit per edit.

        Args:
            handler: Called with the change patch when the browser commits.
        """

    @abstractmethod
    def emit(self, event: str, payload: Any) -> None:
        """Send a custom message down to the browser.

        v1's ``on()`` machinery rides this channel.

        Args:
            event: The event name.
            payload: The JSON-serializable event payload.
        """

    def start(self) -> None:
        """Start the live pipe. No-op by default (e.g. static export)."""
        return None

    def stop(self) -> None:
        """Stop the live pipe. No-op by default (e.g. static export)."""
        return None
