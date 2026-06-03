---
artifact: SKELETON
status: ready
created: 2026-06-03
app: figureflow — interactive flow diagram widget for Python
stack: Python 3.9+, anywidget, traitlets, hatchling; bundled front-end (esbuild) vendoring React 18 + @xyflow/react v12 (+ dagre, added ITER_04)
sections: [01, 02, 03, 04, 05]
mvp_target: A pip-installable anywidget library (offline/self-contained front-end, no CDN) that renders an interactive flow diagram in any Jupyter host, with per-element shape + styling for nodes and edges, drag edits synced back to Python, multi-select + within-canvas styled copy/paste, a minimap, undo/redo of canvas edits, node grouping, automatic layout, lossless JSON save/load plus mermaid export, and a custom JS/TS component escape hatch — publishable as v0.1.
---

# SKELETON — figureflow

## §01 · Concept

figureflow lets a Python user build and display an interactive flow diagram without
touching JavaScript. Each node and edge is styled per-element — shape, fill,
border, font — set directly as Python keyword arguments, the way you'd format a
single shape in a drawing tool. It is a wrapper around React Flow
(`@xyflow/react` v12) built on anywidget, so the same widget renders across
JupyterLab, Notebook, Colab, VS Code and marimo with one pip install — and with
the front-end bundled into the wheel, it runs offline with no CDN dependency.
The core flow: construct `Flow(nodes=[...], edges=[...])`, display it, drag/edit
on the canvas, and read the modified geometry back into Python.

## §02 · Architecture

**Component diagram (text):**

```
Python process (kernel)                         Browser / front-end
┌───────────────────────────┐   traits (JSON)   ┌────────────────────────────┐
│ Flow (anywidget.AnyWidget)│ ◀───────sync─────▶ │ widget.js (bundled ESM)     │
│  - nodes  : List[Dict]    │  nodes/edges/...   │  ├─ React root              │
│  - edges  : List[Dict]    │                    │  ├─ <ReactFlow>             │
│  - color_mode/fit/height  │                    │  ├─ MiniMap / Controls      │
│  - _node_modules (reg.)   │   custom messages  │  ├─ nodeTypes={shape,group} │
│  - _edge_modules (reg.)   │ ◀──emit/on────────▶ │  ├─ edgeTypes={} (L3 only)  │
│ Node / Edge dataclasses   │                    │  ├─ history stack (undo)    │
│ Shape enum                │                    │  └─ vendored React + xyflow │
└───────────────────────────┘                    │     (bundled, no CDN)       │
                                                  └────────────────────────────┘
```

The front-end is a **prebuilt bundle**: a maintainer-side esbuild step vendors
React + @xyflow/react (+ dagre from ITER_04) into `static/widget.js`, which ships
in the wheel. End users never run npm; the maintainer/contributor build is the
only place a JS toolchain appears.

**Data model** (full target surface; implementations stubbed in skeleton):

- **Shape** (enum of strings): `rectangle, rounded, stadium, ellipse, diamond,
  parallelogram, hexagon, cylinder`.
- **Node**: `id, label, pos(x,y), shape, fill, border_color, border_width,
  font_family, font_size, font_color, bold, italic, text_align, width, height,
  html, svg_path, type, parent_id, extent, data`.
  - `html` (L2), `svg_path` (L1), `type` (L3) are escape-hatch fields, null by
    default.
  - `parent_id` (str | None) and `extent` (`"parent"` | None) support grouping
    (ITER_04); null by default for ungrouped nodes.
- **Edge**: `id, source, target, label, path_type(straight|bezier|step|
  smoothstep), marker_start, marker_end (each none|arrow|closed_arrow), color,
  width, dash(solid|dashed|dotted), font_family, font_size, font_color, bold,
  italic, label_bg, type`.
- **Shared text-style vocabulary**: the five fields `font_family, font_size,
  font_color, bold, italic` mean the same thing on both Node labels and Edge
  labels. Same names, same defaults, one mental model.
- **Internal global baseline**: a single module-level dict of default field
  values that fresh elements start from. NOT surfaced in any signature; not a
  theme, not user-settable. New element → baseline values → user overrides per
  element. Style lives on the element, so a duplicated element carries it.

No new persistent entities are introduced by later iterations — undo/redo
history and the clipboard are transient front-end state, and serialization
(ITER_05) reads/writes the existing Node/Edge model, adding no fields.

**API surface** (Python):

| Symbol | Signature | One-line |
| --- | --- | --- |
| `Shape` | enum | The 8 built-in shapes. |
| `Node` | `Node(id, label="", pos=(0,0), **style)` | A styled node; `.to_dict()` serializes for the channel. |
| `Edge` | `Edge(source, target, **style)` | A styled edge; `.to_dict()` serializes. |
| `Flow` | `Flow(nodes=None, edges=None, color_mode="light", fit_view=True, height=480)` | The widget. |
| `Flow.add_node` | `(node)` | Append + sync. |
| `Flow.add_edge` | `(edge)` | Append + sync. |
| `Flow.positions` | `() -> {id: (x, y)}` | Current canvas geometry as last synced. |
| `Flow.undo` / `Flow.redo` | `()` | Step back/forward through canvas-edit history (ITER_03). |
| `Flow.group` | `(node_ids, label="") -> str` | Create a parent group containing the given nodes (ITER_04). |
| `Flow.layout` | `(algo="dagre", direction="TB", **opts)` | Auto-arrange nodes; positions sync back (ITER_04). |
| `Flow.to_json` | `() -> str` | Lossless JSON of the whole diagram (ITER_05). |
| `Flow.from_json` | `(s) -> Flow` *(classmethod)* | Rebuild a diagram from `to_json` output (ITER_05). |
| `Flow.to_mermaid` | `() -> str` | Export mermaid flowchart text, lossy (ITER_05). |
| `Flow.register_node_type` | `(name, module)` | Register a custom JS/TS node component (L3, ITER_06). |
| `Flow.register_edge_type` | `(name, module)` | Register a custom JS/TS edge component (L3, ITER_06). |
| `Flow.on` | `(event, callback)` | Subscribe to `emit()` events from custom components (ITER_06). |

There is no HTTP API, no auth, no database, and no cross-origin surface — this
is an in-process Jupyter widget. Those audit dimensions are N/A by construction.

## §03 · Tech Stack

- **Python** ≥ 3.9. **anywidget** ≥ 0.9 (widget substrate over the Jupyter
  Widgets messaging protocol), **traitlets** (synced state). Build backend:
  **hatchling**, `src/` layout, static JS/CSS force-included into the wheel.
- **Front-end (bundled, offline).** Source ESM in `js/`, bundled by **esbuild**
  into `src/figureflow/static/widget.js` with **React 18.3.1** and
  **@xyflow/react v12** vendored in (xyflow CSS bundled too — no runtime `<link>`,
  no CDN). esbuild dedupes to a single React instance. This is a maintainer-side
  build; the published wheel contains only the prebuilt bundle, so **end-user
  install stays no-build**.
- **Typings**: hand-written `.d.ts` shipped alongside the bundle so L3
  custom-component authors get TS autocomplete and may compile externally; the
  artifact figureflow loads at runtime is plain JS.

## §04 · Python layer (`src/figureflow/__init__.py`)

**Repo / module structure:**

```
pyproject.toml
package.json            # maintainer build only (esbuild, react, @xyflow/react)
js/
  index.js              # front-end source (bundled → static/widget.js)
src/figureflow/
  __init__.py           # Shape, Node, Edge, Flow, _BASELINE
  serialize.py          # to_json/from_json/to_mermaid (added ITER_05)
  static/
    widget.js           # PREBUILT bundle (esbuild output; checked in / built in CI)
    widget.css          # container sizing (xyflow CSS is bundled into widget.js)
    figureflow.d.ts        # custom-component typings (added ITER_06)
```

**Skeleton implementation** — one representative pattern, rest stubbed:

- `Shape` enum present with all 8 members.
- `Node`/`Edge` dataclasses present with the *full* field list above, but
  `to_dict()` emits only `id/type/position/data{label,fill,borderColor}` for
  nodes (with `type:"shape"`, or the ShapeNode renderer never binds and xyflow
  falls back to its default node) and `id/source/target` for edges in the
  skeleton — shape geometry, fonts, edge path/markers/dash, grouping are carried
  as fields but not yet honored by the front-end (later iterations wire them).
- `_BASELINE` dict defined at module level; `Node`/`Edge` defaults read from it.
- `Flow` subclasses `anywidget.AnyWidget` with traits `nodes, edges,
  color_mode, fit_view, height` synced; `_node_modules`/`_edge_modules` and the
  `on()` machinery are declared but inert until ITER_06.
- `add_node/add_edge/positions` implemented (pure trait manipulation).
- `undo/redo` (ITER_03), `group/layout` (ITER_04),
  `to_json/from_json/to_mermaid` (ITER_05), and
  `register_node_type/register_edge_type/on` (ITER_06) are present as stubs that
  raise `NotImplementedError` naming the filling iteration — surface visible,
  honestly gated.

**How to run locally:**
- *Maintainer:* `npm install && npm run build` (esbuild → `static/widget.js`),
  then `pip install -e .`.
- *Notebook:* `from figureflow import Flow, Node; Flow(nodes=[Node("a","Hi")])`.

**Environment variables:** none.

## §05 · Front-end widget (`js/index.js` → bundled `static/widget.js`)

**Render entry:** `export default { render({ model, el }) }` mounts a React 18
`createRoot` into `el`, renders `<App model={model}/>`, returns an unmount
cleanup. React, xyflow, and xyflow CSS are imported from the bundle (vendored),
not a CDN.

**Skeleton component tree:**

```
App(model)
└─ ReactFlow(nodes, edges, nodeTypes, onNodesChange, ...)
   ├─ Background
   ├─ Controls
   └─ ShapeNode  (single node type; skeleton renders a plain bordered box)
```

- `nodeTypes`/`edgeTypes` are defined **at module level** (stable reference —
  defining them inside `App` would remount the whole graph every render).
  `nodeTypes = { shape: ShapeNode }` (a `group` entry is added in ITER_04);
  `edgeTypes` starts empty `{}` — built-in edge styling rides on each edge's
  `type`/`style` fields (xyflow's native edge renderers), not a custom edge
  component. The `edgeTypes` map is populated only by L3 registration (ITER_06).
- `App` seeds local `useState` from `model.get("nodes"/"edges")`, listens for
  `change:nodes`/`change:edges` to update local state, and uses an `echo` ref
  guard so Python→JS writes don't bounce back as edits.
- Skeleton sync: `onNodesChange` applies changes client-side via
  `applyNodeChanges`; commits back to the model only on drag-stop and add/remove.
  This **single commit seam** is where ITER_03's undo history will hook.
- **Placeholder data strategy:** skeleton `ShapeNode` ignores shape/font fields
  and draws a generic bordered box, proving the render+sync loop before
  ITER_01 makes shapes real.

> No screens/routes/empty-states in the web sense — a widget renders one canvas.
> Loading state = "nodes not yet synced" shows an empty canvas; acceptable for
> skeleton.

## Out of MVP scope

- Binary / diff sync for graphs beyond ~1000 nodes (tens of thousands) —
  documented as a next step in ITER_06.
- System-clipboard / cross-application copy — documented as a next step in
  ITER_06; in-MVP copy/paste is within-canvas only.
- **Format *import*** (parsing mermaid or other grammars *into* figureflow).
  Export (JSON + mermaid) IS in the MVP (ITER_05); import is deferred — it needs
  a foreign-grammar parser and a layout pass for coordinate-less input, the one
  unbounded item we consciously cut. Documented as a next step in ITER_06.
- Undo/redo of *programmatic* Python-API edits — canvas-edit undo/redo IS in the
  MVP (ITER_03); tracking arbitrary Python mutations is deferred.
- Heavy obstacle-avoiding edge routing (edges that bend around nodes). Light
  routing — straight/step/smoothstep paths — IS in the MVP (ITER_02).
- A first-class TypeScript-buildable front-end package (we ship a prebuilt JS
  bundle + `.d.ts`, not a published, compile-against-source TS package).
