---
artifact: ITER_02
status: ready
created: 2026-06-03
scope: Edge rendering at node parity — path type, end markers, line style/dash, and styled labels using the shared text-style vocabulary.
sections_changed: [03, 04, 05]
sections_unchanged: [01, 02]
depends_on: [SKELETON, ITER_01]
mvp: false
---

# ITER_02 — Edge styling at node parity

## §01 · Concept
> Unchanged — see SKELETON § 01.

## §02 · Architecture
> Data model unchanged — see SKELETON § 02 (Edge fields were specified there in
> full). This iteration honors those fields end-to-end. No new traits or methods.

## §03 · Tech Stack
> Unchanged — see SKELETON § 03. Edge path types and markers are native to
> `@xyflow/react` v12; no new dependency. The `step`/`smoothstep` path types are
> the MVP's **light edge routing** (orthogonal/curved connectors); heavy
> obstacle-avoiding routing remains out of scope (SKELETON § Out of MVP scope).

## §04 · Python layer

**`Edge.to_dict()` — full serialization.** Map fields to the xyflow edge shape:

- `id` → `id` (default `"{source}->{target}"`), `source`, `target`.
- `path_type` (`straight|bezier|step|smoothstep`, default `bezier`) → xyflow
  edge `type` (`straight|default|step|smoothstep`; `bezier`→`default`).
  **Precedence:** `path_type` and the L3 custom `type` field both target xyflow's
  single `type` key. `to_dict()` emits `type = custom_type if set else
  mapped(path_type)` — a custom edge component (L3, a later iteration) owns its own path, so it
  overrides `path_type`. Built-in edges leave `type` unset, so `path_type` wins.
- `marker_start`/`marker_end` (`none|arrow|closed_arrow`, default end=`arrow`,
  start=`none`) → `markerStart`/`markerEnd` objects
  (`{type:"arrow"|"arrowclosed"}`) or omitted when `none`.
- `color`, `width`, `dash` (`solid|dashed|dotted`, default `solid`) →
  `style={ stroke, strokeWidth, strokeDasharray }` where dasharray is
  `none / "6 4" / "2 4"`.
- `label` → `label`; label text style from the **shared vocabulary**
  (`font_family, font_size, font_color, bold, italic`) → `labelStyle`
  (`fontFamily, fontSize, fill=fontColor, fontWeight, fontStyle`).
- `label_bg` (color | None, default None) → `labelBgStyle`/`labelShowBg` when set.

**Shared text-style vocabulary — single source.** Factor the five label-style
fields and their `_BASELINE` defaults into one place reused by both `Node` and
`Edge` (e.g. a small `_text_style_dict(obj)` helper, or a shared dataclass mixin)
so the names and defaults cannot drift between the two. This is the concrete
realization of the "one mental model" decision.

No new public methods. `add_edge` unchanged.

## §05 · Front-end widget

- Edges now carry real `type`, `markerStart/End`, `style` (with `strokeDasharray`),
  `label`, `labelStyle`, and optional label background — all passed straight to
  `<ReactFlow edges={...}>`. xyflow renders path type, arrowheads, dashing, and
  the styled label natively; no custom edge component is needed for the built-in
  surface (custom edge *components* are the L3 path, a later iteration).
- Confirm `applyEdgeChanges` still only commits add/remove back to the model
  (per SKELETON § 05) — edge style is author-set from Python, not canvas-edited,
  in this MVP.

> Node rendering unchanged — see ITER_01 § 05.

**Verification step:** render edges covering each `path_type`, both marker ends,
each `dash`, and a styled label with a background; confirm parity with node-label
styling (same font controls produce the same look).
