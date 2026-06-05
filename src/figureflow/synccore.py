"""Shared sync-core — the diff + echo-guard lifted above the adapter fork.

In v1 the "what changed → what to push" diff and the echo-guard (a state we just
pushed down must not bounce back up as a fresh edit) lived inline in the
anywidget JS. v2 lifts the Python half of that logic here so every transport
adapter (anywidget / static / server) inherits identical behavior instead of
re-deriving it three times with subtle drift (SKELETON_V2 §02, §04).

Skeleton state: the functions are present and honestly gated — they raise
``NotImplementedError`` naming the iteration that fills them in (ITER_V2_01),
matching the v1 stub pattern. The JS twin of this guard lives in the bundle
(SKELETON_V2 §05).
"""

from __future__ import annotations

import threading
from typing import Any, Dict, Optional

# One lock guarding mutate-then-snapshot across threads. The static and notebook
# adapters never contend on it; the stdlib server adapter (ITER_V2_03) holds it
# briefly around every read-for-push and applied mutation so concurrent POSTs and
# the SSE pusher cannot corrupt one ``Flow``.
LOCK = threading.Lock()

# A state dict is the ``to_json``-shaped payload every adapter exchanges:
# ``{"nodes": [...], "edges": [...], "meta": {...}}``.
State = Dict[str, Any]
Patch = Dict[str, Any]


def diff(prev: Optional[State], next: State) -> Optional[Patch]:
    """Compute what to push down, or ``None`` when nothing changed.

    Args:
        prev: The last-known state, or ``None`` for the initial push.
        next: The current canonical state.

    Returns:
        A patch describing the change, or ``None`` if ``prev`` and ``next`` are
        equivalent so adapters can skip an empty push.

    Raises:
        NotImplementedError: Always — implemented in ITER_V2_01.
    """
    raise NotImplementedError("figureflow.synccore.diff is implemented in ITER_V2_01")


def is_echo(incoming: State, last_pushed: Optional[State]) -> bool:
    """Return ``True`` when an upstream change merely reflects our own push.

    The Python-side half of the echo-guard: an edit coming up from the browser
    that only mirrors a state we just sent down is dropped, not re-committed, so
    push → client applies → client emits does not loop.

    Args:
        incoming: The state an adapter received from the browser.
        last_pushed: The most recent state this adapter pushed down, if any.

    Returns:
        ``True`` if ``incoming`` is an echo of ``last_pushed`` and should be
        ignored; ``False`` if it is a genuine new edit to commit.

    Raises:
        NotImplementedError: Always — implemented in ITER_V2_01.
    """
    raise NotImplementedError(
        "figureflow.synccore.is_echo is implemented in ITER_V2_01"
    )
