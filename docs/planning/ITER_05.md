---
artifact: ITER_05
status: ready
created: 2026-06-03
scope: Serialization — lossless JSON save/load round-trip of a diagram, plus lossy mermaid flowchart export. Import (foreign grammar → pyxyflow) is explicitly deferred.
sections_changed: [03, 04]
sections_unchanged: [01, 02, 05]
depends_on: [SKELETON, ITER_01, ITER_02, ITER_04]
mvp: false
---

# ITER_05 — Serialization (export)

## §01 · Concept
> Unchanged — see SKELETON § 01.

## §02 · Architecture
> No data-model change — serialization reads/writes the existing Node/Edge model
> (SKELETON § 02). No new traits or front-end work; this is a Python-side module.

## §03 · Tech Stack
- **New module:** `src/pyxyflow/serialize.py` (declared in SKELETON § 04
  structure). No new dependency — JSON is stdlib; mermaid export is string
  building.
> Otherwise unchanged — see SKELETON § 03.

## §04 · Python layer

**`to_json() -> str`** (replace stub). Emit a versioned envelope using the same
per-element dicts the channel already uses (so it is lossless against pyxyflow's
own schema):
```
{ "schema": "pyxyflow/1",
  "color_mode": ..., "fit_view": ..., "height": ...,
  "nodes": [ <Node.to_dict()>, ... ],
  "edges": [ <Edge.to_dict()>, ... ] }
```
`json.dumps` over that. Because positions are included, a reload needs no layout.

**`from_json(s) -> Flow`** (classmethod, replace stub). Parse, check `schema`
(reject unknown major versions with a clear error), and construct
`Flow(nodes=<stored node dicts>, edges=<stored edge dicts>,
color_mode=..., fit_view=..., height=...)`. The stored dicts are already in
channel form, so reconstruction is exact round-trip — `to_json(from_json(x)) ==
x` (modulo key ordering). On an existing live widget, a `load_json(s)` instance
method replaces `nodes`/`edges` wholesale; per ITER_03 § 05 this wholesale load
**clears the undo history** rather than pushing a single giant entry.

**`to_mermaid() -> str`** (replace stub). Emit `flowchart TB` (direction
configurable). Map each shape to its nearest mermaid node syntax — rectangle
`id[label]`, rounded `id(label)`, stadium `id([label])`, diamond `id{label}`,
hexagon `id{{label}}`, parallelogram `id[/label/]`, cylinder `id[(label)]`,
ellipse → rounded fallback. Edges: `A -->|label| B`, dashed edges `A -.-> B`,
arrowheads per `marker_end`. **Lossy by design:** per-element colors/fonts and
custom `svg_path`/`html` do not survive the mapping; emit a short comment header
noting the export is structural. (Optional: `classDef` blocks for fills, behind a
flag — but the MVP guarantee is structure + labels, not fidelity.)

> **Import is out of scope** (SKELETON § Out of MVP). Parsing mermaid or other
> grammars *into* pyxyflow needs a foreign-grammar parser plus a layout pass for
> coordinate-less input; deferred and documented in the final iteration.

## §05 · Front-end widget
> Unchanged — serialization is entirely Python-side. See ITER_01–ITER_04 § 05.

**Verification step:** (1) build a styled, grouped diagram; assert
`from_json(to_json(flow))` reproduces nodes/edges (incl. styling, `parent_id`)
exactly. (2) `to_mermaid()` output renders as a valid flowchart in a mermaid
viewer, with the right shapes, edges, and labels.
