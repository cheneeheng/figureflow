---
artifact: ITER_01
status: ready
created: 2026-06-03
scope: Node rendering — all 8 built-in shapes with full per-node styling, plus L1 custom SVG-path geometry and L2 raw-HTML escape hatches.
sections_changed: [04, 05]
sections_unchanged: [01, 02, 03]
depends_on: [SKELETON]
mvp: false
---

# ITER_01 — Node shapes & styling

> **Empirical-risk iteration.** Shape geometry, text fit, and handle placement
> on non-rectangular shapes cannot be verified in a headless environment. The
> author must render the demo in a notebook and confirm visuals; expect small
> follow-up tweaks (handle offsets, SVG padding). This risk is in *rendering
> correctness*, not in the design — the field set and API do not change.

## §01 · Concept
> Unchanged — see SKELETON § 01.

## §02 · Architecture
> Data model unchanged — see SKELETON § 02. This iteration makes `Node.to_dict()`
> emit the full `data` payload and makes the front-end honor it. No new entities,
> routes, or traits.

## §03 · Tech Stack
> Unchanged — see SKELETON § 03.

## §04 · Python layer

**`Node.to_dict()` — full serialization.** Emit every style field into `data`:
`label, shape, fill, borderColor, borderWidth, fontFamily, fontSize, fontColor,
bold, italic, textAlign, width, height, html, svgPath`, plus `**self.data`.
The `type` field is `None` by default (matching SKELETON § 02, "null by
default"); `to_dict()` maps `None`→`"shape"` so the built-in renderer binds. A
custom `type` name (L3, a later iteration) overrides this and passes through unchanged.

**Field defaults** read from `_BASELINE` (module-level dict), e.g.
`fill="#ffffff", border_color="#334155", border_width=1.5,
font_family="Inter, system-ui, sans-serif", font_size=13, font_color="#0f172a",
bold=False, italic=False, text_align="center"`. Per-element overrides only; the
baseline is never exposed in the `Node` signature beyond these field defaults.

**L1 — custom geometry.** New `svg_path` field (str | None). When set, the
front-end renders that SVG path instead of a built-in polygon, sized to
`width`/`height` (defaulting 130×56). Pure Python; no JS authoring.

**L2 — raw HTML.** `html` field already present; when set, the node body renders
the HTML instead of `label`. Static only (no React in the string).

No new public methods. `add_node` and `positions` unchanged.

## §05 · Front-end widget

**`ShapeNode` becomes shape-aware.** Read `data.shape` and branch:

- **CSS-box shapes** (`rectangle, rounded, stadium, ellipse`): a `div` with
  `background=fill`, `border={borderWidth}px solid {borderColor}`, and
  `borderRadius` of `0 / 8px / 999px / 50%` respectively. Auto-sizes to label
  (min 80×40); honors explicit `width`/`height` when given.
- **Polygon shapes** (`diamond, parallelogram, hexagon`): an `<svg>` of size
  `width×height` (defaults: diamond 130×90, others 130×56) drawing a `<polygon>`
  with `fill`, `stroke=borderColor`, `strokeWidth=borderWidth`, and an absolutely
  centered text overlay `div`.
- **`cylinder`**: an `<svg>` `<path>` body + a top ellipse arc stroke; centered
  text overlay.
- **`svg_path` set (L1):** render `<svg><path d={svgPath} .../></svg>` at
  `width×height` with the same fill/stroke, centered text overlay. Takes
  precedence over the `shape` branch.
- **`html` set (L2):** render the body via `dangerouslySetInnerHTML` instead of
  the label text. Takes precedence over label.

**Text styling** applied to the label container from `data`: `fontFamily,
fontSize+px, color=fontColor, fontWeight=bold?700:400, fontStyle, textAlign`.
Reused for edge labels in a later iteration (same field names).

**Handles.** Four handles (top target, bottom source, left target, right source)
on every node. For polygon/cylinder shapes they sit on the bounding-box edges —
note for the notebook check: they may visually float off a diamond's points;
acceptable for v0.1, refine later if needed.

**Gotcha addressed — stable `nodeTypes`.** `nodeTypes = { shape: ShapeNode }`
stays defined at module level (per SKELETON § 05). Adding shape logic must not
move it inside `App`, or every state change remounts all nodes.

**Gotcha addressed — StrictMode double-invoke.** One-time effects (model
listener registration; any imperative setup) are guarded so React 18 dev
double-mount does not double-register — listener effects return cleanups. (xyflow
CSS now ships inside the bundle per SKELETON § 03, so there is no runtime
`<link>` injection to guard against.)

**Verification step (required):** render a demo exercising all 8 shapes + a
`svg_path` node + an `html` node; confirm shapes, fills, borders, fonts, and
handle anchoring look right. This is the iteration's done-check.
