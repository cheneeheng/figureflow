"""Shared sync-core — the diff + echo-guard lifted above the adapter fork.

In v1 the "what changed → what to push" diff and the echo-guard (a state we just
pushed down must not bounce back up as a fresh edit) lived inline in the
anywidget JS. v2 lifts the Python half of that logic here so every transport
adapter (anywidget / static / server) inherits identical behavior instead of
re-deriving it three times with subtle drift (SKELETON_V2 §02, §04). The JS twin
of this guard lives in the bundle (SKELETON_V2 §05).
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


# The graph-bearing keys a patch carries. ``meta`` (flow-level settings) is
# diffed too, but only ``nodes``/``edges`` participate in the echo comparison —
# they are the channel a browser edit can bounce back on.
_GRAPH_KEYS = ("nodes", "edges")


def diff(prev: Optional[State], next: State) -> Optional[Patch]:
    """Compute what to push down, or ``None`` when nothing changed.

    Args:
        prev: The last-known state, or ``None`` for the initial push.
        next: The current canonical state.

    Returns:
        A patch carrying only the changed ``nodes``/``edges``/``meta`` keys, or
        ``None`` if ``prev`` and ``next`` are equivalent so adapters can skip an
        empty push. On the initial push (``prev`` is ``None``) every present key
        is included.
    """
    patch: Patch = {}
    for key in (*_GRAPH_KEYS, "meta"):
        if key not in next:
            continue
        if prev is None or prev.get(key) != next.get(key):
            patch[key] = next[key]
    return patch or None


def is_echo(incoming: State, last_pushed: Optional[State]) -> bool:
    """Return ``True`` when an upstream change merely reflects our own push.

    The Python-side half of the echo-guard: an edit coming up from the browser
    that only mirrors a state we just sent down is dropped, not re-committed, so
    push → client applies → client emits does not loop.

    Args:
        incoming: The state an adapter received from the browser.
        last_pushed: The most recent state this adapter pushed down, if any.

    Returns:
        ``True`` if ``incoming``'s graph (``nodes``/``edges``) equals
        ``last_pushed``'s and should be ignored; ``False`` if it is a genuine new
        edit to commit (or there is nothing yet pushed to echo).
    """
    if last_pushed is None:
        return False
    return all(
        incoming.get(key) == last_pushed.get(key) for key in _GRAPH_KEYS
    )
