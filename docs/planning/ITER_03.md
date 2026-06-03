---
artifact: ITER_03
status: ready
created: 2026-06-03
scope: The editing layer — memoized nodes + viewport culling for the ~1000-node target, multi-select, within-canvas styled copy/paste, a minimap, and undo/redo of canvas edits hooked at the commit seam.
sections_changed: [02, 04, 05]
sections_unchanged: [01, 03]
depends_on: [SKELETON, ITER_01, ITER_02]
mvp: false
---

# ITER_03 — Editing layer (perf, select, copy/paste, minimap, undo/redo)

> **Empirical-risk iteration.** The ~1000-node target is a measurement, not a
> guarantee. The bottleneck is React re-rendering custom nodes, not the sync
> channel. The mitigations below are xyflow's documented guidance; their
> sufficiency must be confirmed by rendering a 1000-node graph in a notebook and
> checking pan/drag stays smooth. If it doesn't, the next lever is diff-sync —
> deferred (SKELETON § Out of MVP scope) — so treat that as a post-MVP fork, not
> a scope expansion here. This is intentionally the heaviest iteration: it owns
> the commit seam, so the undo history that all later mutations rely on must be
> established here rather than retrofitted.

## §01 · Concept
> Unchanged — see SKELETON § 01.

## §02 · Architecture
> No new persistent entities or synced traits. Copy/paste, the clipboard, and the
> undo/redo history are **transient front-end state**; pasted elements reach
> Python through the existing `nodes`/`edges` trait commit path (SKELETON § 05),
> not a new channel. The **commit seam** named in SKELETON § 05 is formalized
> here as the single place every canvas edit funnels through — and the single
> place history snapshots.

## §03 · Tech Stack
> Unchanged — see SKELETON § 03. Minimap and history use xyflow primitives and
> React state; no new dependency.

## §04 · Python layer

- **Read-back hardening.** `positions()` already returns `{id:(x,y)}` from the
  synced `nodes`. Confirm pasted nodes appear in `flow.nodes` after a paste
  (they arrive as `add` changes → committed to the trait), so `positions()` and
  iteration over `flow.nodes` see them with no extra API.
- **ID generation for paste** is owned by the front-end (uniqueness guaranteed
  against current ids); document the scheme so Python code inspecting `flow.nodes`
  knows pasted ids look like `{origId}-copy-{n}`.
- **`undo()` / `redo()`** (replace the skeleton `NotImplementedError` stubs):
  thin Python triggers that send a custom message instructing the front-end to
  step its history (the stack lives in the front-end, § 05). After a step the
  front-end commits the restored `{nodes, edges}` back through the seam, so
  `flow.nodes`/`positions()` reflect the result. No-op (silently) when the stack
  end is reached.

No new public traits.

## §05 · Front-end widget

**Performance:**
- **Memoize node components** — wrap `ShapeNode` (and subcomponents) in
  `React.memo` so unaffected nodes don't re-render when one node moves.
- **Stable callbacks/objects** — `nodeTypes`/`edgeTypes` already module-level
  (SKELETON § 05); make `onNodesChange`/`onEdgesChange` `useCallback`-stable and
  avoid inline object/array props on `<ReactFlow>`.
- **Viewport culling** — set `onlyRenderVisibleElements` on `<ReactFlow>`.
- Keep the drag-stop commit (not per-frame).

**Minimap:** render `<MiniMap>` (with `<Controls>`); style it to the color mode.
Drop-in; no state of its own.

**Multi-select:** enable box-select and additive shift-click via xyflow props
(`selectionOnDrag`, `multiSelectionKeyCode`, `panOnDrag` tuned so drag-select and
panning don't conflict — document the keys, e.g. Shift = add, Space/middle = pan).

**Within-canvas styled copy/paste:**
- Capture `Ctrl/Cmd+C`/`V` at the widget root (listener guarded for StrictMode
  double-mount; cleaned up on unmount).
- **Copy:** snapshot selected nodes (full `data`, so style travels) and edges
  whose *both* endpoints are selected, into an in-memory clipboard ref (not the
  OS clipboard — within-canvas only, per scope).
- **Paste:** clone with fresh ids (`{origId}-copy-{n}`), offset positions
  (+24,+24), remap copied edges' endpoints, select the pasted set. Emit as `add`
  changes so they flow through the seam and commit to the traits.

**Undo/redo (hooked at the commit seam):**
- Maintain a capped history (e.g. last 50) of `{nodes, edges}` snapshots plus a
  redo stack, in a ref. **Every canvas-originated commit** at the seam —
  drag-stop, delete, paste (and later group/layout, applied through the
  same seam) — pushes the *prior* state and clears redo. One gesture = one entry
  (drag-stop, not per-frame; a paste is one entry).
- `Ctrl/Cmd+Z` = undo, `Ctrl/Cmd+Shift+Z` (and `Ctrl+Y`) = redo; the Python
  `undo()/redo()` messages drive the same stack.
- Restoring a snapshot sets local state **and** commits it to the model — but
  must not itself be recorded as a new history entry (guard the restore path),
  and the `echo` ref must continue to wrap only model→local application so a
  restore commit isn't dropped as an echo.
- **Boundary (MVP):** the stack records canvas edits. A wholesale programmatic
  load (e.g. `from_json`, a later iteration) **clears** the history rather than pushing one
  giant entry; other direct Python mutations (`add_node`, `group`) are
  authoritative and not individually tracked in v0.1 (SKELETON § Out of MVP).

> Edge rendering — see ITER_02 § 05. Node rendering — see ITER_01 § 05.

**Verification step:** (1) ~1000 nodes — pan/drag smooth with culling + memo.
(2) Box-select styled nodes with an internal edge, copy, paste — clones keep
styling, get unique ids, the edge duplicates, `flow.nodes` reflects it.
(3) Drag a node, `Ctrl+Z` returns it; `Ctrl+Shift+Z` re-applies; minimap tracks.
