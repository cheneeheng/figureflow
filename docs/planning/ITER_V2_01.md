---
artifact: ITER_V2_01
status: ready
created: 2026-06-05
scope: The seam refactor — extract the shared sync-core (diff + echo-guard), rewire the renderer to consume an abstract Transport interface, and port the existing v1 anywidget wiring in as concrete adapter #1, with v1 behavior preserved exactly.
sections_changed: [04, 05]
sections_unchanged: [01, 02, 03]
depends_on: [SKELETON_V2]
mvp: false
---

# ITER_V2_01 — Transport seam refactor (anywidget as adapter #1)

> **Foundational, not flashy — and that's expected.** This iteration ships **no
> new user-visible feature**: a notebook that worked before still works, byte-for-
> byte the same. Its entire job is to move the existing sync logic behind the seam
> so the next two adapters can plug in without re-implementing it. Foundational-
> first is the deliberate choice here (per the planning guidance): everything else
> depends on this extraction, so it must be established cleanly now rather than
> retrofitted around two already-built adapters. The risk is *regression*, not
> design — the done-check is "v1 demos behave identically."

## §01 · Concept
> Unchanged — see SKELETON_V2 §01.

## §02 · Architecture
> No new entities or traits. This iteration realizes the seam drawn in
> SKELETON_V2 §02: the sync-core moves above the adapter fork; the renderer and
> the anywidget wiring are split along the `Transport` interface. The anywidget
> comm channel, traits, and message protocol are exactly v1's — only the *call
> path* changes (renderer → JS `Transport` → anywidget adapter → model, instead
> of renderer → model directly).

## §03 · Tech Stack
> Unchanged — see SKELETON_V2 §03. No dependency added; this is pure refactor.

## §04 · Python layer

**`synccore.py` (implement).** Lift v1's diff/echo logic out of the inline
anywidget path into a small, adapter-agnostic module:
- `diff(prev, next) -> patch` — what to push down (or `None` when nothing changed),
  so adapters don't each re-derive it.
- `is_echo(incoming, last_pushed) -> bool` — the Python-side half of the guard:
  an upstream change that merely reflects a state we just pushed is dropped, not
  re-committed. (The JS-side guard half is in §05.)
- The single commit funnel that v1's undo seam (ITER_03 §05) hooks must still be
  the one place every committed edit passes — moving it here must not create a
  second commit path.

**`transport/base.py` (implement the ABC).** Exactly the contract from
SKELETON_V2 §04 (`bind/send_state/on_change/emit/start/stop`). `start`/`stop`
default to no-ops so the static adapter (ITER_V2_02) inherits them for free.

**`transport/anywidget_adapter.py` (implement — adapter #1).** `Flow` **remains the
v1 `anywidget.AnyWidget` subclass** — it stays the canonical state holder (its
`nodes`/`edges` traits *are* the state) and provides the comm channel. The adapter
does not wrap a *separate* widget; it implements the `Transport` contract over
`Flow`'s own trait I/O:
- `bind(flow)` stores the `Flow`; `send_state` writes the `nodes`/`edges` traits
  (the v1 sync write); `on_change` registers a trait observer that routes incoming
  edits through `synccore.is_echo` before committing — i.e. the v1 echo behavior,
  now sourced from the shared core.
- `emit`/`on` ride the existing custom-message machinery (SKELETON.md §04).
- `start`/`stop` are no-ops (the kernel comm is managed by Jupyter, not by us).

**`Flow.display()` (rewire).** Bind an `AnywidgetAdapter` to the renderer and return
the widget (`self`, since `Flow` *is* the `AnyWidget`). Because `Flow` stays an
`AnyWidget` subclass, v1 ergonomics are preserved — evaluating `Flow(...)` as a
cell's last line still auto-renders via `_repr_mimebundle_`, so existing v1 user
code does not break. Same traits, same render; only the renderer's internal call
path changes (now via the JS `Transport`), invisible to v1's other methods
(`positions`, `undo`, `group`, `layout` all still read/write the same traits).

> `add_node/add_edge/positions/undo/redo/group/layout/to_json/from_json/
> to_mermaid` unchanged — see SKELETON.md §04 and ITER_01–05.

## §05 · Front-end widget

**Introduce the JS `Transport` interface** (SKELETON_V2 §05) and a shared JS
**sync-core** holding the echo `ref` guard. In v1 this guard wrapped model→local
application directly (ITER_03 §05); move it into the sync-core unchanged so it
still wraps *only* push→local application — never local→push — across all future
adapters. Restoring a snapshot (undo/redo, ITER_03) must continue to commit
without being recorded as a new history entry, and without being swallowed as an
echo — verify that invariant survives the move.

**Rewire the renderer to the interface.** The React `App` reads initial state via
`transport.getState()`, listens via `transport.subscribe(...)`, and the v1
**commit seam** (drag-stop / add / remove / paste / layout, ITER_03 §05) now calls
`transport.pushChange(...)` instead of writing the model directly.

**Implement the anywidget JS adapter** satisfying the interface against
`model.get/set/on` — the representative implementation the other two adapters mirror.

**Carried-forward gotchas (must survive the refactor):**
- `nodeTypes`/`edgeTypes` stay module-level (do not let the rewire pull them into
  `App`).
- One-time effects (model listener, `subscribe`) stay `useRef`-guarded with
  cleanups for StrictMode.
- Single React instance — no adapter imports a second React; all share the bundle.

> Renderer/shapes — see ITER_01 §05. Edges — ITER_02 §05. Editing/undo/minimap —
> ITER_03 §05. Grouping/layout — ITER_04 §05.

**Verification step:** re-run the v1 done-checks through `display()` after the
refactor — (1) all 8 shapes + svg_path + html render identically; (2) drag-stop
syncs back, `positions()` reflects it; (3) `Ctrl+Z`/`Shift+Z` undo/redo and
copy/paste behave exactly as v1; (4) `layout()` result commits as one undo entry.
Any divergence is a regression, not a new behavior.
