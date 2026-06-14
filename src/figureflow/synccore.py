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


def is_echo(
    incoming: Optional[State] = None,
    last_pushed: Optional[State] = None,
    *,
    client_id: Optional[str] = None,
    seq: Optional[int] = None,
    applied: Optional[Dict[str, int]] = None,
) -> bool:
    """Return ``True`` when an upstream change merely reflects our own push.

    Two forms, one per channel kind (ITER_V2_04 §04):

    **Content form** (positional ``incoming``/``last_pushed``) — the synchronous
    anywidget path: an edit coming up from the browser that only mirrors a state
    we just sent down is dropped, not re-committed, so push → client applies →
    client emits does not loop.

    **Identity form** (keyword ``client_id``/``seq``/``applied``) — the
    asynchronous server path, where a client's own commit returns to it over
    SSE and the flag/content guard cannot bracket the round-trip. Answers "is
    this incoming envelope from a ``client_id``+``seq`` I have already
    applied?", guarding against duplicate POST delivery. ``applied`` maps each
    ``client_id`` to the highest ``seq`` committed from it — a bounded map
    rather than a set of pairs, valid because each client's counter is
    monotonic.

    Args:
        incoming: The state an adapter received from the browser (content form).
        last_pushed: The most recent state this adapter pushed down, if any
            (content form).
        client_id: The originating client of an envelope (identity form).
        seq: The originator's sequence number for the envelope (identity form).
        applied: Per-client highest applied sequence numbers (identity form).

    Returns:
        ``True`` if the change is our own push bouncing back (or a duplicate
        delivery) and should be ignored; ``False`` if it is a genuine new edit
        to commit.
    """
    if client_id is not None:
        if seq is None or applied is None:
            return False
        return seq <= applied.get(client_id, -1)
    if incoming is None or last_pushed is None:
        return False
    return all(
        incoming.get(key) == last_pushed.get(key) for key in _GRAPH_KEYS
    )
