---
artifact: ITER_04
status: ready
created: 2026-06-03
scope: Node grouping (parent/child containers, drag-into-group) and automatic layout (vendored dagre, Flow.layout).
sections_changed: [03, 04, 05]
sections_unchanged: [01, 02]
depends_on: [SKELETON, ITER_01, ITER_02, ITER_03]
mvp: false
---

# ITER_04 — Grouping & auto-layout

## §01 · Concept
> Unchanged — see SKELETON § 01.

## §02 · Architecture
> Data model unchanged — `Node.parent_id` and `Node.extent` were declared in
> SKELETON § 02; this iteration honors them. No new entities or traits beyond a
> layout-trigger channel (see § 04/§ 05). `Flow.group`/`Flow.layout` move from
> stub to implemented.

## §03 · Tech Stack
- **New dependency (bundled):** **dagre** (`@dagrejs/dagre`) vendored into the
  esbuild bundle for layout computation. No new runtime/end-user dependency — it
  rides in the existing prebuilt `static/widget.js`. (elk is the heavier
  alternative; dagre is sufficient for the MVP's directed flowcharts.)
> Otherwise unchanged — see SKELETON § 03.

## §04 · Python layer

**`group(node_ids, label="") -> str`** (replace stub):
- Create a new "group" node: `id` = generated (`group-{n}`), `type="group"`,
  with a container style (fill/border from baseline, larger). Append it.
- For each id in `node_ids`, set that node's `parent_id` = the group id and
  `extent="parent"` (children can't be dragged outside the parent).
- Initial group geometry: compute a bounding box around the members (+ padding)
  and set the group node's `pos` and `width`/`height`. Children positions become
  parent-relative (xyflow convention) — convert on grouping.
- Return the new group id. Pure trait manipulation → syncs like any add.

**`layout(algo="dagre", direction="TB", **opts) -> None`** (replace stub):
- Validate `algo` (MVP: only `"dagre"`; reserve the arg for future engines) and
  `direction` (`TB|BT|LR|RL`). Stash the request on a synced trait
  `_layout_request` (a dict: `{algo, direction, opts, nonce}`; the `nonce`
  forces a change event even for identical requests).
- The front-end computes new positions and writes them back through `nodes`
  (§ 05), so after `layout()` the kernel-side `flow.positions()` reflects the
  arranged coordinates with no extra call.

> `add_node/add_edge/positions` unchanged — see SKELETON § 04.

## §05 · Front-end widget

**Grouping render:**
- Group nodes (`data.type === "group"` / node `type "group"`) render as a styled
  container `div` behind their children; registered as a `group` entry in the
  module-level `nodeTypes` map (stable-reference rule still applies).
- Children carry `parentId` + `extent:"parent"` (mapped from `parent_id`/
  `extent`) so xyflow constrains child dragging to the parent and moves children
  with the parent. Dragging a node onto a group can set its parent (MVP: support
  the programmatic `group()` path first; drag-to-reparent is a nice-to-have
  within this iteration, gated behind it working cleanly).

**Auto-layout:**
- On `change:_layout_request`, build a dagre graph from current nodes (sized by
  rendered/declared `width`×`height`) and edges, set `rankdir` from `direction`,
  run layout, and translate dagre's center coordinates to xyflow's top-left
  `position`.
- For grouped graphs (MVP scope): lay out top-level nodes and groups; lay out
  each group's children within the group's box. Keep nesting to one level for
  the MVP — deeper nesting is not promised.
- Apply computed positions by committing updated `nodes` to the model through
  the **commit seam** (ITER_03 § 05). Because layout's result is applied at the
  seam as one canvas-originated commit, undo/redo covers it automatically — a
  `layout()` is a single undo entry, no extra wiring. The `echo` guard must
  continue to wrap only model→local application (per ITER_03 § 05), so a
  `layout()` result is not mistaken for an echo and dropped.

> Node rendering — see ITER_01 § 05. Edge rendering — see ITER_02 § 05.
> Performance/editing — see ITER_03 § 05.

**Verification step:** (1) `group([...])` three nodes; confirm they render inside
a container, drag together, and children stay within it. (2) `layout(direction=
"LR")` on a ~30-node graph; confirm a sane left-to-right arrangement and that
`flow.positions()` reflects the new coordinates.
