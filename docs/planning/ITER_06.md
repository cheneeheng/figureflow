---
artifact: ITER_06
status: ready
created: 2026-06-03
scope: Custom JS/TS component escape hatch (L3) — type registry, runtime ESM loading, the {data, selected, emit} contract and emit→flow.on channel, the vendored-React bridge for runtime modules — plus shipped .d.ts typings and PyPI-ready offline packaging. Documents diff-sync, system-clipboard, and format import as post-MVP next steps.
sections_changed: [02, 03, 04, 05]
sections_unchanged: [01]
depends_on: [SKELETON, ITER_01, ITER_02, ITER_03, ITER_04, ITER_05]
mvp: true
---

# ITER_06 — Escape hatch & packaging (MVP)

> Final iteration. After this, cumulative state equals the `mvp_target` in
> SKELETON. Nothing is planned past it.

## §01 · Concept
> Unchanged — see SKELETON § 01.

## §02 · Architecture

> Entities unchanged — see SKELETON § 02. This iteration activates two synced
> registry traits and the custom-message channel that were declared inert in the
> skeleton:
- `_node_modules : Dict[str,str]` and `_edge_modules : Dict[str,str]` — maps of
  `type name → ESM module URL/path`, synced to the front-end.
- Custom-message channel: front-end `emit(name, payload)` → anywidget custom
  message → Python dispatch to handlers registered via `Flow.on(name, cb)`.

No HTTP/auth/db surface is introduced (still N/A — in-process widget).

## §03 · Tech Stack

- **New artifact:** `static/figureflow.d.ts` — hand-written typings for the custom
  component contract (`NodeProps`, `EdgeProps`, `emit` signature, and the
  `figureflow` runtime global below). Ships in the wheel via the existing
  `force-include` of `static/`. Authors writing `.ts` get autocomplete and may
  compile externally; figureflow loads only plain `.js` at runtime. No bundler is
  added for *users* — the maintainer-side esbuild step (SKELETON § 03) is
  unchanged.
- No new runtime dependencies.

## §04 · Python layer

**`register_node_type(name, module)` / `register_edge_type(name, module)`**
(replace the skeleton `NotImplementedError` stubs):
- Validate `name` is a non-empty identifier not colliding with built-ins
  (`shape`, `group` for nodes; built-in edge path types for edges). Store
  `{name: module}` in `_node_modules`/`_edge_modules` (triggers sync). `module`
  may be an absolute URL or a path the front-end can fetch.
- A `Node(type=name)` / `Edge(type=name)` then routes to the custom component.
  (Edge `type` precedence over `path_type` is defined in ITER_02 § 04.)

**`on(event, callback)`** (replace stub):
- Register `callback` under `event` in an internal handler dict. On widget init,
  attach a single anywidget custom-message listener that dispatches incoming
  `{event, payload}` to the matching callbacks. Support multiple handlers per
  event; return an unsubscribe handle.

**Serialization & custom types:** `to_json` (ITER_05) records the custom `type`
name and `data`; on reload the component re-binds if the same type is registered,
else falls back to the built-in renderer. Note this in the serialize docs.

## §05 · Front-end widget

**Runtime component loading:**
- On init and on `change:_node_modules`/`change:_edge_modules`, dynamically
  `import(moduleUrl)` each registered module. Each module `default`-exports a
  React component `({ data, selected, emit }) => element`.
- Merge loaded components with built-ins into the `nodeTypes`/`edgeTypes` maps.

> **Gotcha — vendored-React bridge (created by the offline bundle).** Because the
> front-end bundle vendors its own React + xyflow (SKELETON § 03), a runtime-
> imported L3 module cannot `import "react"` and share our instance the way a
> CDN setup would dedupe. Expose the bundle's React and the xyflow primitives a
> custom component needs (e.g. `Handle`, `Position`) on a single well-known
> global — `globalThis.figureflow = { React, xyflow }` — set once when the bundle
> loads. Custom modules read from that global instead of importing React; the
> `.d.ts` documents the contract. Without this, custom components hit the "two
> Reacts" invalid-hook-call error.

> **Gotcha — stable type maps (critical here).** `nodeTypes`/`edgeTypes` must
> remain referentially stable except when a registration actually changes, or
> xyflow remounts the entire graph. Keep the merged map in a `useMemo`/ref keyed
> on the set of registered names + load completion — never rebuild per render.
> Extends the SKELETON § 05 module-level rule to the dynamic case.

**The `emit` contract:**
- Each custom component receives `emit(name, payload)`; calling it sends an
  anywidget custom message `{event:name, payload}` to Python (dispatched to
  `Flow.on`). Built-in interactions (drag/add/remove/copy-paste/undo/group/
  layout) keep flowing through the traits/commit seam — `emit` is *only* for
  custom components, so the trait contract stays small and stable.
- `selected` is passed through from xyflow selection state.

**Loading/StrictMode:** dynamic-import effects are guarded (ref flag) so dev
double-mount doesn't double-import; a failed import logs a clear console error
and falls back to the built-in renderer rather than crashing the canvas.

> Node rendering — see ITER_01 § 05. Edge rendering — see ITER_02 § 05.
> Editing/perf/minimap/undo — see ITER_03 § 05. Grouping/layout — see
> ITER_04 § 05. Serialization — see ITER_05 § 04.

## Packaging (MVP done-check)

- `README.md` (pitch + quick start + design notes); `examples/`: `quickstart.py`
  (all shapes/edges), `grouping_layout.py` (group + `layout()`),
  `serialization.py` (`to_json`/`from_json` round-trip + `to_mermaid`), and
  `custom_component.py` (L3 + `emit`/`on`).
- `pyproject.toml` metadata complete; `package.json` + esbuild config build the
  bundle; CI runs `npm ci && npm run build` then `python -m build`, producing a
  wheel whose `static/widget.js` is the vendored bundle (no CDN at runtime).
- Build sanity: `pip install` of the wheel into a clean, **network-isolated** env
  still renders the quickstart in a notebook (proves the offline-bundle goal).
  `pytest` over `to_dict()` serialization, `positions()`, `group()`, and
  `from_json(to_json(x)) == x` round-trip.

## Post-MVP next steps (documented, not built)

> Recorded so the boundary is explicit and the follow-on work is scoped:
- **Format import** — parsing mermaid (or GraphViz DOT, etc.) *into* figureflow.
  Needs a foreign-grammar parser and, because imported text has no coordinates,
  a pass through `layout()` (ITER_04) to place nodes. The unbounded item cut
  from the MVP; export (ITER_05) is the in-scope half.
- **Diff/binary sync** for graphs beyond ~1000 nodes: replace whole-list trait
  writes with id-keyed diffs (and/or binary buffers) at the commit seam
  (ITER_03) to cut serialization cost at tens of thousands of nodes.
- **System-clipboard / cross-application copy:** today's copy/paste is an
  in-memory within-canvas clipboard (ITER_03). Extending to the OS clipboard
  would allow paste across sessions and other apps.
- **Undo/redo of programmatic Python edits** — v0.1 tracks canvas edits only
  (ITER_03 boundary).

**Verification step:** register a custom node component that calls
`emit("clicked", {id})` on click; confirm a Python `flow.on("clicked", ...)`
handler fires with the payload, that the custom component renders without an
invalid-hook-call (proving the React bridge), and that built-in nodes still
render and sync.

**MVP reached:** offline, pip-installable widget; per-element styled nodes
(8 shapes + L1/L2) and edges at parity (incl. light routing); fast, editable
canvas (~1000 nodes, multi-select, styled copy/paste, minimap, canvas undo/redo);
node grouping; automatic layout; lossless JSON save/load + mermaid export; and an
L3 custom-component escape hatch with `emit`/`on`, the vendored-React bridge, and
`.d.ts` typings. Matches `mvp_target`. Everything else is post-MVP (SKELETON
§ Out of MVP scope + the next-steps above).
