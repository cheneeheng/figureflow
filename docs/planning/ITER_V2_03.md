---
artifact: ITER_V2_03
status: ready
created: 2026-06-05
scope: The server adapter (MVP terminator) — Flow.serve() starts a dependency-free stdlib ThreadingHTTPServer on localhost with SSE for Python→browser pushes and POST for browser→Python edits, giving full bidirectional sync in a plain browser tab. FastAPI/websocket is explicitly deferred.
sections_changed: [03, 04, 05]
sections_unchanged: [01, 02]
depends_on: [SKELETON_V2, ITER_V2_01, ITER_V2_02]
mvp: true
---

# ITER_V2_03 — Stdlib SSE+POST server adapter (MVP)

> **The heaviest adapter — and the MVP terminator.** It re-introduces the
> web-app concerns anywidget hid (a wire protocol, threads, ports), but bounded
> hard: single user, localhost, ~1000 nodes, stdlib only. The two correctness
> risks are concurrency (threads touching one `Flow`) and the echo loop (push →
> client applies → client emits → loop); both are handled below by reusing the
> ITER_V2_01 sync-core rather than inventing server-specific logic.

## §01 · Concept
> Unchanged — see SKELETON_V2 §01. (`serve()` is the "plain browser, live" door.)

## §02 · Architecture
> No new model entities or persistent state. A `serve()` session (the server
> object, its thread, the set of connected SSE streams) is **transient
> infrastructure**, like the clipboard/history in v1 (SKELETON_V2 §02). State
> flows through the same sync-core and commit funnel as every other adapter; the
> server is just a different pipe carrying the same `to_json`-shaped payloads.

## §03 · Tech Stack
- **Standard library only.** `http.server.ThreadingHTTPServer` +
  `BaseHTTPRequestHandler`, `threading`, `json`, `webbrowser`, `socket`. **No new
  runtime dependency** (SKELETON_V2 §03) — the MVP server is `pip install
  figureflow` and nothing more.
> Otherwise unchanged — see SKELETON_V2 §03.

## §04 · Python layer

**`transport/server_adapter.py` (implement) + `Flow.serve(host="127.0.0.1",
port=0, *, open_browser=True, block=False) -> str`** (replace the stub) and
**`Flow.stop()`**:

- **Server:** `ThreadingHTTPServer` bound to `host` (default **`127.0.0.1`** —
  never `0.0.0.0`; `http.server` is not security-hardened, so localhost-only is
  the safety boundary). `port=0` lets the OS pick a free port; surface the chosen
  port. Run `serve_forever()` on a daemon thread so the notebook/REPL stays
  interactive; `block=True` joins it for `python script.py` use. `serve()` prints
  and returns the URL; `open_browser` launches it via `webbrowser`.
  > **Gotcha — `ThreadingHTTPServer`, not `HTTPServer`.** A single-threaded server
  > would block on the never-ending SSE stream and starve every POST. Threading
  > lets the stream live on one thread while `/change` POSTs land on others.

- **Routes** (request/response shapes explicit):
  - `GET /` → the shared `static/host.html` (ITER_V2_02), pointed at the live
    endpoints and constructing the **server JS adapter** (not the static one).
  - `GET /widget.js`, `GET /widget.css` → the vendored bundle, correct MIME types.
  - `GET /state` → `200 application/json`, body = `serialize.to_json(self)` — the
    initial snapshot the client loads before streaming begins.
  - `GET /events` → **SSE**: `200 text/event-stream`, `Cache-Control: no-cache`,
    `Connection: keep-alive`; the handler registers this stream and writes
    `data: <json-patch>\n\n` whenever the canonical `Flow` changes, plus a `:` ping
    comment every ~15 s to keep the connection alive. Unregister the stream on
    client disconnect (broken pipe).
  - `POST /change` → request body = a JSON patch `{nodes?, edges?, op}`; apply it
    to the canonical `Flow` **through the sync-core** (ITER_V2_01), so v1's commit
    funnel and undo seam see exactly one edit; respond `204`.

- **Concurrency (the load-bearing detail):** the SSE pusher thread and the
  `/change` handler threads all touch one `Flow`. Wrap every read-for-push and
  every applied mutation in a single **`threading.Lock`** kept in the sync-core.
  > **Gotcha — shared-state race (the "MAX+1 under concurrency" cousin).** Two
  > concurrent POSTs, or a POST racing the pusher, corrupt state without the lock.
  > One lock, held briefly around mutate-then-snapshot, is sufficient at this
  > scale.

- **Echo across the network:** when `/change` commits, the resulting push must
  **not** be re-sent to the origin client as a fresh edit — reuse
  `synccore.is_echo` (ITER_V2_01); the server is just another transport feeding
  the same guard, so no server-specific echo logic is written.

- **`stop()`** calls `shutdown()` + `server_close()`, joins the thread, and closes
  open SSE streams. `serve()` twice without `stop()` stops the prior server first.

> Model, `to_json`/`from_json`, and all v1 methods unchanged — see SKELETON.md §02
> and ITER_05. Static export reused for the host page — see ITER_V2_02 §04.

## §05 · Front-end widget

**Implement the server JS adapter** against the `Transport` interface
(SKELETON_V2 §05):
- `getState()` — `fetch("/state")` for the initial snapshot.
- `subscribe(cb)` — open `new EventSource("/events")`; on each message, parse and
  hand to the sync-core (echo-guarded, ITER_V2_01) before applying to local state.
- `pushChange(patch)` — `fetch("/change", {method:"POST", body: JSON})`. The v1
  commit seam (drag-stop/add/remove/paste/layout, ITER_03 §05) already routes
  through `pushChange` after ITER_V2_01, so no per-gesture wiring is added here.
- `sendEvent`/`onEvent` — POST for custom events / consume them on the SSE stream
  (the v1 `on()` path over this transport).

> **Gotcha — EventSource is GET-only and cannot set headers.** That is exactly why
> the split is SSE-**GET** down + `fetch`-**POST** up: the upstream needs a body,
> so it can never ride `EventSource`. (If auth were ever added — it is not, in this
> localhost MVP — the down-channel would have to move to `fetch`+`ReadableStream`.)

> **Gotcha — StrictMode double-invoke.** The `EventSource` connection lives in a
> `useRef`-guarded effect that returns a cleanup closing the stream; React 18 dev
> double-mount must not open two streams. (Same pattern as v1's listeners,
> ITER_01 §05.)

Carried forward: module-level `nodeTypes`/`edgeTypes`; single React instance from
the shared bundle (the server serves the *same* `widget.js` that the static export inlines).

> Renderer/shapes/edges/editing/grouping — see ITER_01–ITER_04 §05. Seam/sync-core
> — ITER_V2_01 §05. Host page — ITER_V2_02 §05.

**Verification step:** (1) `serve()` a ~1000-node grouped, styled diagram; the
browser opens, renders, pan/drag stays smooth (v1 culling+memo, ITER_03). (2) Drag
a node in the browser → assert `flow.positions()` in Python reflects it (POST→sync-
core→commit). (3) Mutate `flow` in Python (`add_node`, `layout`) → assert the
browser updates live via SSE, with no echo bounce. (4) `stop()` closes the stream
cleanly; a second `serve()` rebinds.

## Post-MVP next step (deferred)

**FastAPI + websocket server** *(explicitly deferred per the planning request).*
The stdlib SSE+POST server is full-duplex and dependency-free, sufficient for the
single-user, localhost, ~1000-node MVP. A websocket server (FastAPI + uvicorn +
`websockets`, behind a `figureflow[server]` extra) becomes warranted only for
**binary diff-sync** of tens-of-thousands of nodes (websockets carry binary
natively; SSE is text-only) or **multi-client shared sessions** — both already
out of MVP scope (SKELETON_V2 §Out of MVP). Crucially, it slots in **behind the
same `Transport` interface** (ITER_V2_01): a fourth adapter, not a rewrite.
