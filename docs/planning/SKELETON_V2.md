---
artifact: SKELETON_V2
status: ready
created: 2026-06-05
app: figureflow — interactive flow diagram widget for Python (v2: multi-transport)
stack: Python 3.9+, anywidget, traitlets, hatchling; bundled front-end (esbuild) vendoring React 18 + @xyflow/react v12 + dagre; NEW v2 — Python stdlib http.server (ThreadingHTTPServer) for the server adapter, zero new runtime deps
sections: [01, 02, 03, 04, 05]
mvp_target: One renderer, three live transports behind a single Transport seam — notebook (anywidget, ported from v1), a plain browser backed by a dependency-free stdlib SSE+POST localhost server with bidirectional sync, and a self-contained static HTML snapshot (client-side interactive, one-way manual export). Publishable as v0.2.
---

# SKELETON_V2 — figureflow multi-transport

> **Builds on the shipped v1 MVP** (SKELETON.md + ITER_01–05.md). v1 is the
> substrate: the `Node`/`Edge`/`Flow` model, the shape renderer, edge styling,
> the editing layer (undo/redo, copy/paste, minimap), grouping/auto-layout, and
> `to_json`/`from_json`/`to_mermaid` all already exist and are unchanged. v2
> changes **where and how the diagram is hosted**, not what it renders.

## §01 · Concept

v1 answered "render an interactive flow diagram **in a notebook**." v2 answers
"render the *same* diagram **anywhere** — notebook, a plain browser tab, or a
frozen file — from one codebase." The realization driving this version: anywidget
was never the library; it is one **delivery adapter**. The library is the Python
`Flow` model plus a transport-agnostic React renderer. So v2 extracts a
**transport seam** and gives that one renderer three front doors:

- `flow.display()` — notebook, live kernel round-trip (v1 behavior, now behind the seam).
- `flow.serve()` — a plain browser tab with full bidirectional sync to the live
  Python process, over a dependency-free stdlib HTTP server.
- `flow.to_html()` — a self-contained, offline, interactive snapshot; view and
  manipulate client-side, with a manual one-way "download JSON" escape.

The user-facing mental model is unchanged from v1 (build a `Flow`, style
per-element); v2 only adds *how you ship it to a viewer*.

## §02 · Architecture

**The transport seam** — one canonical state, one renderer, three interchangeable
pipes. The renderer never knows which pipe it sits on.

```
                        ┌──────────────────────────────────────────┐
                        │              PYTHON PROCESS                │
                        │   Flow  ── canonical state (v1 model)      │
                        │     │                                      │
                        │     ▼                                      │
                        │   sync-core ── diff + echo-guard           │
                        │     │          (solved ONCE, shared)       │
                        │     ▼                                      │
                        │   Transport (Py iface)                     │
                        │   bind · send_state · on_change · emit     │
                        └────┬──────────────┬──────────────┬─────────┘
                  ┌──────────┘     ┌────────┘     ┌─────────┘
                  ▼                ▼              ▼
            ┌──────────┐     ┌──────────┐   ┌──────────┐
            │ anywidget│     │  stdlib  │   │  static  │
            │ adapter  │     │ SSE+POST │   │  export  │
            │ (PORT v1)│     │  server  │   │ (one-way)│
            └────┬─────┘     └────┬─────┘   └────┬─────┘
            kernel comm    SSE↓ GET /events   no pipe:
            (traitlets)    POST↑ /change      baked JSON
═════════════════╪════════════════╪══════════════╪═════ browser boundary
                 ▼                ▼              ▼      ┐ one vendored
            (anywidget)      (server)       (static)   │ esbuild bundle
            JS adapter       JS adapter     JS adapter  │ ("the binary"):
                 └────────────────┼──────────────┘      │ renderer +
                                  ▼                      │ all 3 JS
                     ┌────────────────────────┐         │ adapters +
                     │  Transport (JS iface)   │         │ the JS iface
                     │  getState · subscribe   │         │
                     │  pushChange · sendEvent │         │
                     └───────────┬─────────────┘         │
                                 ▼                        │
                     ┌────────────────────────┐          │
                     │  RENDERER (v1, built    │          │
                     │  once): React Flow +    │          │
                     │  shape/style layer.     │          │
                     │  Pipe-agnostic.         │          │
                     └────────────────────────┘          ┘
```

**Data model: unchanged.** No new persistent entities. `Node`/`Edge`/`Flow` are
exactly v1 (see SKELETON.md §02). The Transport, sync-core, server sessions, and
the static JSON island are **transient infrastructure**, not model fields — the
same posture v1 took toward the clipboard and undo history (ITER_03 §02).
Serialization already exists: `to_json`/`from_json` (ITER_05) are the wire format
every adapter reuses, so no adapter invents its own schema.

**The sync-core is the load-bearing extraction.** The diff (what changed →
what to push) and the **echo-guard** (a state we just pushed down must not bounce
back up as a fresh edit) lived inline in v1's anywidget JS. v2 lifts them *above*
the fork so they are solved once and every adapter inherits identical behavior —
rather than re-implemented three times with subtle drift.

**New API surface (Python)** — everything else is v1, unchanged:

| Symbol | Signature | One-line |
| --- | --- | --- |
| `Flow.display` | `() -> AnyWidget` | Notebook render via the anywidget adapter (v1 behavior, now seam-mediated). |
| `Flow.to_html` | `(path=None, *, title=None) -> str` | Self-contained static snapshot; writes to `path` if given, returns the HTML string (ITER_V2_02). |
| `Flow.serve` | `(host="127.0.0.1", port=0, *, open_browser=True, block=False) -> str` | Start a stdlib SSE+POST server; returns the URL (ITER_V2_03). |
| `Flow.stop` | `() -> None` | Stop a running `serve()` server (ITER_V2_03). |

> Unchanged v1 surface: `Shape`, `Node`, `Edge`, `Flow(...)`, `add_node`,
> `add_edge`, `positions`, `undo`/`redo`, `group`, `layout`,
> `to_json`/`from_json`, `to_mermaid`, `register_node_type`/`register_edge_type`,
> `on`. See SKELETON.md §02.

There is still no auth, no database, and no cross-origin surface. The server
adapter binds **localhost only**; cross-origin is N/A by construction (the host
page and the data come from the same `127.0.0.1` origin).

## §03 · Tech Stack

- **No new front-end dependency.** The renderer and all three JS adapters live in
  the *same* existing esbuild bundle (`static/widget.js`); React stays a single
  vendored instance (SKELETON.md §03). Static export and the server reuse that
  one bundle — no second React, no CDN.
- **No new runtime Python dependency.** The server adapter is built on the
  **standard library** `http.server` (`ThreadingHTTPServer`) + Server-Sent Events
  (a long-lived `text/event-stream` GET) for the down-channel and plain `fetch`
  POST for the up-channel. This is a deliberate right-sizing for a single-user,
  localhost, ~1000-node tool. Consequence: **the MVP-v2 server adds zero installs**
  — there is no `[server]` extra in v0.2.
- **Build/packaging** unchanged — hatchling, `src/` layout, the prebuilt bundle
  force-included in the wheel (SKELETON.md §03).

> Otherwise unchanged — see SKELETON.md §03.

## §04 · Python layer

**New package `src/figureflow/transport/`** (the seam). The v1 `Flow` keeps its
model and methods; v2 routes its three host entry points through adapters.

```
src/figureflow/
  __init__.py            # Flow gains display()/to_html()/serve()/stop() (this file unchanged otherwise)
  serialize.py           # v1 — to_json/from_json/to_mermaid (REUSED, unchanged)
  synccore.py            # NEW — diff + echo-guard, shared by all adapters
  transport/
    __init__.py
    base.py              # NEW — Transport ABC: bind/send_state/on_change/emit/start/stop
    anywidget_adapter.py # ITER_V2_01 — ports v1's anywidget wiring behind base.Transport
    static_export.py     # ITER_V2_02 — to_html(): bundle + JSON island, one-way
    server_adapter.py    # ITER_V2_03 — ThreadingHTTPServer, SSE GET + POST
  static/                # v1 bundle (REUSED by every adapter)
    widget.js
    widget.css
    host.html            # ITER_V2_02 — shared host-page template (static + server)
```

**`transport/base.py` — the contract** (the representative shape; concrete
adapters fill it iteration by iteration):
- `bind(flow)` — attach to the canonical `Flow`; the adapter reads/writes its
  nodes/edges through the sync-core, never poking trait internals directly.
- `send_state(nodes, edges, meta)` — push canonical state down to the browser.
  `meta` is the flow-level settings (`color_mode`, `fit_view`, `height`).
- `on_change(handler)` — register the upstream handler invoked when the browser
  commits a canvas edit; the handler funnels through the sync-core so the
  echo-guard and v1's undo seam (ITER_03 §05) still see exactly one commit.
- `emit(event, payload)` — custom message down (v1's `on()` machinery rides this).
- `start()` / `stop()` — lifecycle; **no-ops for the static adapter** (no live pipe).

**`synccore.py` — shared diff + echo-guard** (the v1 logic, lifted out of the
anywidget JS to be adapter-agnostic on the Python side; its JS twin lives in
§05). One place computes "did this change originate locally or from a push we
just sent," so no adapter re-derives it.

**Skeleton state of the entry points:**
- `display()` — returns the working anywidget (still wired the v1 way in the
  skeleton; ITER_V2_01 moves it behind `base.Transport` with no behavior change).
- `to_html()` / `serve()` / `stop()` — present, raising `NotImplementedError`
  naming the filling iteration (the same honest-gating pattern v1 used).

**How to run locally:** unchanged for the maintainer build (SKELETON.md §04).
Notebook quickstart unchanged. `serve()`/`to_html()` quickstarts arrive with
their iterations.

**Environment variables:** none.

## §05 · Front-end widget

**Renderer is unchanged** (React Flow + the v1 shape/style/edit layers). v2 only
changes *what it talks to*: instead of reading the anywidget `model` directly, it
will consume an abstract **JS `Transport`**:

- `getState() -> {nodes, edges, meta}`
- `subscribe(cb) -> unsubscribe` — Python pushed new state down.
- `pushChange(patch)` — a local canvas edit goes up (the v1 commit seam, ITER_03
  §05, now delegates to this).
- `sendEvent(name, payload)` / `onEvent(name, cb)` — custom messages (v1 `on()`).

The **echo-guard** moves into the shared JS sync-core so it wraps only
`subscribe`-driven (push→local) application across *every* adapter, exactly as v1
did for model→local writes (ITER_03 §05).

**Three JS adapters, one bundle:**
- **anywidget adapter** — wraps `model.get/set/on` to satisfy the interface
  (ITER_V2_01, the representative implementation).
- **server adapter** — `EventSource("/events")` for `subscribe`; `fetch("/change",
  {method:"POST"})` for `pushChange` (ITER_V2_03, stub here).
- **static adapter** — `getState()` returns the baked JSON island; `pushChange`
  has no network target, so it captures client edits in-memory to feed a
  "download JSON" affordance (ITER_V2_02, stub here).

**Gotcha carried forward — stable `nodeTypes`/`edgeTypes`.** They stay
module-level (SKELETON.md §05; reference: framework config objects compared by
reference). The seam refactor must not pull them into a component.

**Gotcha carried forward — StrictMode double-invoke.** Any one-time setup an
adapter adds (the anywidget listener; the server's `EventSource` connection) is
guarded with a `useRef` flag and returns a cleanup, per v1 (ITER_01 §05).

## Out of MVP scope

- **FastAPI / websocket server.** *(explicitly deferred per the planning
  request.)* The MVP server is stdlib SSE+POST, which is full-duplex and
  dependency-free for a single localhost user. A websocket server (FastAPI +
  uvicorn + `websockets`, gated behind a `[server]` extra) is the upgrade path
  only when binary diff-sync or heavy multi-client concurrency is needed — neither
  applies at the ~1000-node MVP target. Documented as the next step in ITER_V2_03.
- **Binary / diff sync** for tens-of-thousands of nodes (carried over from v1's
  out-of-scope; the websocket path above is its prerequisite).
- **Multi-client / shared-session** serving (two browsers editing one `serve()`).
  The MVP server is single-user.
- **Live round-trip from the static HTML.** A `file://` snapshot has no Python
  behind it; its only path back is the manual "download JSON" → re-`from_json`.
  Automatic round-trip requires `display()` or `serve()` by construction.
- **System-clipboard / cross-application** copy (carried over from v1).
- **Format import** (foreign grammar → figureflow), carried over from v1.
