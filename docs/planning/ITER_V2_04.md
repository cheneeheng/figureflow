---
artifact: ITER_V2_04
status: ready
created: 2026-06-12
scope: Server-sync hardening patch — pin the wire envelope (client identity + sequence numbers), replace the flag-based echo guard with identity-based suppression on the network path, specify queue-based SSE writes, close the snapshot/stream gap, scope adapter exclusivity, and verify the no-kernel script path. No new features; this corrects under-specified sync behavior found in the pre-implementation audit of ITER_V2_03.
sections_changed: [02, 04, 05]
sections_unchanged: [01, 03]
depends_on: [SKELETON_V2, ITER_V2_01, ITER_V2_02, ITER_V2_03]
mvp: true
---

# ITER_V2_04 — Sync hardening patch (supersedes ITER_V2_03 as MVP terminator)

> **A correctness patch, not a feature.** The audit of ITER_V2_03 found its sync
> section sound in architecture but under-specified in four places that would
> surface as bugs mid-implementation: the echo guard does not transfer to an
> asynchronous transport as written, the wire format is undefined, the SSE write
> path implies a cross-thread socket race, and the snapshot/stream bootstrap has
> a loss window. This iteration pins all four plus two scope/verification gaps.
> Where ITER_V2_03 conflicts with this document, **this document wins**. Because
> implementation has started, every change below is additive or a substitution at
> a named seam — nothing requires re-architecting work already done under
> ITER_V2_01/02.

## §01 · Concept
> Unchanged — see SKELETON_V2 §01.

## §02 · Architecture

> Model unchanged — see SKELETON_V2 §02. One clarification in the same spirit as
> v1's clipboard/history posture: the **patch envelope** defined in §04
> (`client_id`, `seq`, payload) is transient wire metadata, not model fields.
> `Node`/`Edge` dicts inside the envelope are exactly the v1 channel shape;
> nothing new persists, and `to_json` output is unaffected.

**Adapter exclusivity (scope pin).** v0.2 supports **one live adapter per `Flow`
at a time**. `serve()` on a `Flow` that is currently displayed in a notebook (or
vice versa) is *mechanically possible but officially unsupported*: emit a
`UserWarning` naming the limitation and continue. Static export is exempt — it is
a snapshot, not a live pipe, and may be taken at any moment. Concurrent
multi-adapter sync (notebook + browser simultaneously live) is deferred and
documented alongside the multi-client deferral (SKELETON_V2 §Out of MVP).

## §03 · Tech Stack
> Unchanged — see SKELETON_V2 §03. Stdlib only; `uuid` (Python) and
> `crypto.randomUUID()` (browser) cover client identity with no new dependency.

## §04 · Python layer

**The patch envelope (replaces ITER_V2_03's `{nodes?, edges?, op}`).** One
envelope for both directions on the server path; the undefined `op` field is
**dropped**:

```
{ "client_id": "<uuid>",        # originator: a browser client id, or "python"
  "seq": <int>,                  # see sequence rules below
  "nodes": [ ... ]?,             # full-array REPLACEMENT when present
  "edges": [ ... ]? }            # full-array REPLACEMENT when present
```

- **Semantics: full replacement, not diff.** For the ~1000-node localhost MVP,
  a present `nodes`/`edges` key replaces that array wholesale. `synccore.diff`
  (ITER_V2_01) decides *whether* and *which keys* to send — it does not produce
  element-level deltas in v0.2. Element-level diffing stays coupled to the
  deferred binary-diff path (SKELETON_V2 §Out of MVP).
- **Sequence rules.** The server keeps one monotonically increasing
  **`server_seq`**, incremented under the sync-core lock on every committed
  change (from any origin). Every SSE broadcast carries the `server_seq` of the
  state it describes, plus the `client_id` of the change's originator
  (`"python"` for kernel-side mutations like `add_node`/`layout`). Clients keep
  their own local counter for POSTs; the server does not interpret it beyond
  logging.
- **Framing.** SSE messages are `data: <single-line JSON>\n\n` —
  `json.dumps(envelope)` with **no `indent`** (a newline inside `data:` silently
  truncates the event). State this in a code comment at the write site.

**`synccore.py` — echo guard, network half (amends ITER_V2_01).** The v1 flag
guard ("I am applying a push right now") is synchronous and cannot work when a
client's own commit returns to it asynchronously over SSE. The server path
therefore uses **identity-based suppression** instead:

- Python side: when `/change` commits, the resulting broadcast is stamped with
  the originating `client_id`. `synccore.is_echo` gains an identity overload —
  on the server path it answers "is this incoming envelope from a client_id+seq
  I have already applied?" guarding against duplicate POST delivery.
- The anywidget path is **unchanged**: the existing flag-based guard from
  ITER_V2_01 remains correct there because that channel is synchronous. This is
  an *additive* extension to `synccore` — if ITER_V2_01 is already implemented,
  no shipped behavior changes.

**`transport/server_adapter.py` — SSE write mechanics (replaces ITER_V2_03's
"the handler writes whenever the Flow changes").** No thread ever writes to a
socket it does not own:

- Each `GET /events` handler creates a **per-connection `queue.Queue`**,
  registers it (under the lock) in the adapter's stream set, then loops:
  `queue.get(timeout=15)` → write the envelope; on `queue.Empty` → write a `:`
  ping comment. Broken pipe → unregister (under the lock) and return.
- The broadcast path (called from the sync-core commit, any thread) only
  **enqueues** to every registered queue. The lock is held around
  mutate-then-snapshot-then-enqueue, **never around a socket write**.

**Bootstrap ordering (closes the snapshot/stream gap).** `GET /state` responds
with the `to_json` envelope **wrapped** as `{"server_seq": <int>, "state":
<to_json envelope>}`, the seq read under the lock with the snapshot. The client
contract (§05) is: open `/events` first, buffer, then fetch `/state`, then drop
buffered messages with `seq <= snapshot server_seq` and apply the rest in order.
The server needs no replay machinery — ordering alone closes the window.

**Script-mode support (verification gap).** `Flow` remains an
`anywidget.AnyWidget` subclass (ITER_V2_01); instantiating it and calling
`serve(block=True)` under plain `python script.py` — no kernel, no comm — must
work without errors or comm-related warnings. If anywidget emits noise in the
kernel-less case, suppress it at `serve()` entry; do not restructure the class.

> Routes, lock placement, lifecycle (`stop()`, re-`serve()`), and everything
> else — unchanged, see ITER_V2_03 §04. `to_json`/`from_json` — see ITER_05.

## §05 · Front-end widget

**Server JS adapter — identity and bootstrap (amends ITER_V2_03 §05):**

- On construction, generate a **`client_id`** via `crypto.randomUUID()`, held in
  a `useRef` so StrictMode double-mount does not mint two identities. Keep a
  local `seq` counter; stamp both onto every `pushChange` POST envelope.
- **JS echo guard for the server path:** the `subscribe` handler **drops any
  incoming envelope whose `client_id` equals its own**. This replaces — for this
  adapter only — the flag-based guard, which cannot bracket an asynchronous
  round-trip. The shared sync-core keeps the flag guard for the anywidget
  adapter; the suppression predicate is adapter-supplied, so the sync-core's
  "wraps only push→local application" invariant (ITER_V2_01 §05) is unchanged.
- **Bootstrap:** open `EventSource("/events")` first; buffer messages; `fetch
  ("/state")`; apply the snapshot; discard buffered envelopes with `seq <=`
  snapshot `server_seq`; apply the remainder in seq order; switch to live
  application. The buffer lives in the same `useRef`-guarded effect as the
  `EventSource` (cleanup closes the stream — ITER_V2_03 §05 gotcha unchanged).
- A `seq` gap in live messages (missed event after a transient drop) triggers a
  re-fetch of `/state` rather than any repair protocol — re-bootstrap is cheap
  at this scale.

**Undo interaction (invariant check, no new wiring).** A restore commit
(undo/redo, ITER_03 §05) goes up via `pushChange` like any commit, stamped with
this client's id, and is therefore self-suppressed when broadcast back — the
"restore must not be swallowed as an echo" invariant holds because suppression
keys on *identity*, not content, and the restore was applied locally before the
POST.

> Static adapter — unchanged, see ITER_V2_02 §05 (no pipe, no identity needed).
> Renderer/editing — ITER_01–ITER_04 §05. Seam — ITER_V2_01 §05.

**Doc-hygiene note (no code):** ITER_V2_02 §04's "the server consumes it in
ITER_V2_03" should read "a later iteration" per the established forward-citation
rule; one-line edit to that file.

**Verification step:** (1) Rapid successive drags in the browser — each commits
once, no echo re-application, `flow.positions()` matches the final state.
(2) Python-side `add_node` + `layout()` while the browser is connected — browser
updates live; the browser's own subsequent drag is not bounced back to it.
(3) Kill the network mid-session (dev tools offline → online) — client
re-bootstraps via `/state` and converges. (4) `python script.py` with
`serve(block=True)` — serves, edits round-trip, Ctrl-C exits cleanly, no
kernel-less warnings. (5) Idle 60+ s — pings keep the SSE stream alive. (6)
Hammer `/change` with two concurrent POST loops — no corruption, `server_seq`
strictly increases (lock check). (7) `serve()` while displayed in a notebook —
the `UserWarning` fires.
