---
artifact: ITER_V3_01
status: ready
created: 2026-06-12
scope: LLM-hardened ingestion — publish the figureflow/1 JSON Schema as a shipped artifact, rebuild from_json validation around collected, repair-friendly errors, make node positions optional with renderer auto-layout-on-mount (driven by a new flow-level layout_direction), and pin the forgiving-coercion rules every later ingestion path (mermaid, MCP) reuses.
sections_changed: [01, 02, 04, 05]
sections_unchanged: [03]
depends_on: [SKELETON_V2, ITER_V2_04]
mvp: false
---

# ITER_V3_01 — LLM-hardened ingestion (v3 family, iterations-only)

> **The v3 family reuses the v2 scaffold** — no SKELETON_V3. v3 changes *who
> authors the diagram* (an LLM emitting JSON or mermaid), not where it is hosted
> or what it renders. The Transport seam (SKELETON_V2), the renderer
> (ITER_01–04), and serialization (ITER_05) are the substrate; this family adds
> ingestion paths and an agent-facing adapter on top. This first iteration is
> foundational: both `from_mermaid` (a later iteration) and the MCP tools (a
> later iteration) funnel through the validation layer and the
> positions-optional model built here, so it must exist before either.

## §01 · Concept

v3's user is a **language model** (and the human supervising it). An LLM
authoring a diagram has three needs a human API user doesn't: a published,
machine-readable schema to emit against; error messages written to drive a
repair loop ("what's wrong, where, what to emit instead" — all problems at once,
not fail-on-first); and freedom from inventing coordinates, which LLMs do badly.
This iteration delivers all three for the JSON path. The pitch sharpens to:
*"the LLM emits topology; figureflow validates, places, and renders it
interactively."*

## §02 · Architecture

> Model grows, never contradicts — one explicit amendment:

**`Node.pos` becomes `tuple[float, float] | None`, default `None` ("unplaced").**
This deliberately amends SKELETON §02's `pos=(0,0)` default: an explicit `(0,0)`
(or any tuple) behaves exactly as v1/v2; `None` means "no author opinion —
auto-place me." `to_dict()` omits `position` when unplaced. Every existing v1/v2
code path that sets positions is unaffected; only the *default for authors who
say nothing* changes, and it changes precisely so LLM-emitted JSON and (later)
mermaid never need coordinates. `positions()` reports only placed nodes; after
first render on any transport, all nodes are placed (§05) and it is total again.

**New flow-level field `Flow.layout_direction`** (`"TB"|"BT"|"LR"|"RL"`, default
`"TB"`, synced trait riding the Transport `meta` alongside `color_mode`/
`fit_view`/`height` — SKELETON_V2 §04). It is the `rankdir` the unplaced-node
auto-layout (§05) uses, and the field a later iteration's mermaid header maps
into. Additive-optional in the `figureflow/1` envelope: documents without it
default to `"TB"`, so existing v1/v2 JSON stays valid and `from_json` of old
documents is unaffected.

**New artifact, not a new entity:** `static/figureflow.schema.json` — a JSON
Schema (draft 2020-12) for the `figureflow/1` envelope (ITER_05). Descriptive,
shipped in the wheel, referenced by docs and by `llms.txt` (a later iteration).
The envelope is unchanged except for the one additive-optional
`layout_direction` key above; the schema documents the result.

**New exception types** (transient, not model): `FlowValidationError` carrying a
list of `{path, message, hint}` problems; its `__str__` renders one problem per
line. Defined in `serialize.py`.

## §03 · Tech Stack

> Unchanged — see SKELETON_V2 §03. Validation is hand-rolled against the known
> envelope (stdlib only); **no `jsonschema` dependency** — the shipped schema
> file is documentation/emission-target, not the runtime validator. This keeps
> core `pip install figureflow` dependency-free, per the v2 stance.

## §04 · Python layer

**`serialize.py` — validation rebuild for `from_json` / `load_json`.** Replace
ad-hoc parsing with a single `validate(payload) -> (clean_payload, warnings)`
used by every ingestion path (this iteration: JSON; later: mermaid output and
MCP tool inputs route through the same function):

- **Collect, don't bail.** Walk the whole payload; gather every problem into one
  `FlowValidationError` raised at the end. An LLM repair loop fixes ten problems
  in one round-trip instead of ten.
- **Error message contract** (state it as a style rule in a module docstring):
  one line per problem, shape `"<json-path>: <what is wrong>. <hint with valid
  alternatives>"` — e.g. `nodes[3].shape: 'circle' is not a valid shape. Use one
  of: rectangle, rounded, stadium, ellipse, diamond, parallelogram, hexagon,
  cylinder (closest match: ellipse).` Closest-match via stdlib
  `difflib.get_close_matches`.
- **Hard errors:** duplicate node ids; edge `source`/`target` naming a missing
  node id (name it and list known ids when ≤ 20); unknown `shape`; non-numeric
  `width`/`height`/`font_size`; wrong top-level types; unknown major `schema`
  version (existing ITER_05 rule, now phrased per the contract).
- **Forgiving coercions (warnings, not errors):** unknown node/edge keys are
  folded into `data` and warned; missing optional fields take `_BASELINE`
  defaults (existing behavior, now stated); numeric strings (`"13"`) coerce to
  numbers with a warning; missing `position` is **not** a problem at all —
  unplaced is first-class now. Warnings return as a list of the same
  one-line-shaped strings; `from_json(s, strict=False)` default, `strict=True`
  escalates warnings to errors.
- `from_json`/`load_json` keep their ITER_05 signatures plus the `strict`
  keyword; `load_json` still clears undo history (ITER_03 §05 rule).

**`Node` change:** `pos` default `None` per §02; `to_dict()` omits `position`
when `None`. `Flow.positions()` skips unplaced nodes.

**`Flow` change:** constructor gains `layout_direction="TB"` (validated against
the four values, error per the message contract); emitted by `to_json`, accepted
by `from_json`/`validate` as optional-with-default per §02.

**Schema file:** author `static/figureflow.schema.json` describing the
`figureflow/1` envelope — every Node/Edge field, enums for `shape`, `path_type`,
markers, dash; `position` not required. Force-included in the wheel like the
other static assets (SKELETON §03 packaging).

> `to_json`/`to_mermaid` unchanged — see ITER_05. Transports unchanged — see
> ITER_V2_01–04.

## §05 · Front-end widget

**Auto-layout on unplaced nodes — a renderer behavior, so all three transports
inherit it.** On state application (initial mount *and* any `subscribe` push),
if any node lacks a `position`: run the existing dagre pass (ITER_04 §05 — the
code path `_layout_request` already exercises; dagre is already in the bundle)
with `rankdir` from the synced `layout_direction` (§02), then commit the placed
result **through the commit seam** via `pushChange`:

- On live transports (anywidget, server) the placement round-trips to Python, so
  `flow.positions()` becomes total after first render with no extra call —
  same contract `layout()` established in ITER_04.
- On the static adapter the commit lands in the in-memory state the Download
  JSON affordance reads (ITER_V2_02 §05) — a `to_html()` of a never-displayed,
  unplaced diagram still renders laid-out and exports placed coordinates.
- It is one canvas-originated commit at the seam → **one undo entry**, and the
  identity-stamped envelope (ITER_V2_04) means no echo bounce on the server
  path. No new sync logic.
- Placement runs at most once per state application (guard: only when unplaced
  nodes exist; placed results contain no unplaced nodes, so no loop).
- **Mixed placement (some nodes authored, some not):** dagre runs on the full
  graph; authored positions are kept, only unplaced nodes take their computed
  ones. Stated plainly: this can overlap an auto-placed node with an authored
  one — accepted for v0.3, since the recovery is one drag or a full `layout()`,
  and the primary case (LLM emission) is all-unplaced anyway. Collision
  avoidance is not promised.
- **Unplaced groups:** a group node that is itself unplaced is sized and
  positioned *after* its children — lay out children first, then set the parent
  to their bounding box plus the ITER_04 padding (the same geometry rule
  `group()` applies, computed here client-side because unplaced members have no
  box to measure in Python). One level of nesting, per ITER_04.

**Carried-forward gotchas:** module-level `nodeTypes`/`edgeTypes`; the layout
pass lives behind the existing StrictMode-guarded effect; single React
instance.

> Renderer/shapes/edges/editing — ITER_01–ITER_04 §05. Seam — ITER_V2_01 §05.
> Server sync — ITER_V2_04 §05.

**Verification step:** (1) Feed `from_json` a deliberately broken payload with
five distinct faults — one exception lists all five, each matching the message
contract. (2) Round-trip a position-less 20-node JSON through `display()`:
renders laid out, `positions()` total afterward, single `Ctrl+Z` entry. (3) Same
payload through `to_html()` with no display: opens laid out offline; Download
JSON contains positions. (4) `strict=True` turns an unknown-key warning into an
error. (5) `to_json(from_json(x)) == x` still holds for fully-specified v2
documents (no regression to the lossless guarantee).
