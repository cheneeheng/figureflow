# CLAUDE.md

Guidance for working in this repository.

## What this is

**figureflow** is a pip-installable [anywidget](https://anywidget.dev) library that
renders interactive flow diagrams in any Jupyter host (JupyterLab, Notebook, Colab,
VS Code, marimo). It wraps [React Flow](https://reactflow.dev) (`@xyflow/react` v12).
Each node and edge is styled per-element from Python — shape, fill, border, font — the
way you'd format a single shape in a drawing tool.

The front-end is a **prebuilt, vendored bundle**: React + @xyflow/react (+ its CSS) are
bundled into `src/figureflow/static/widget.js`, which ships in the wheel. End users never
run a JS toolchain and the widget works offline (no CDN).

Status: **v1 MVP + v2 multi-transport + v3 LLM ingestion, all implemented.** ITER_01–ITER_06
landed the v1 surface: per-element node shapes/styling (+ L1 `svg_path`, L2 `html`), edge styling
at parity, multi-select + within-canvas styled copy/paste, minimap, canvas undo/redo, grouping,
dagre auto-layout, JSON save/load + mermaid export, and the L3 custom-component escape hatch
(`emit`/`on`). SKELETON_V2 + ITER_V2_01–03 then added the **transport seam**: one renderer
behind three doors — `display()` (notebook), `to_html()` (offline interactive snapshot), and
`serve()`/`stop()` (live browser tab over a dependency-free stdlib SSE+POST server).
ITER_V2_04 hardened the server sync path: a pinned patch envelope (`client_id` + `seq`,
full-array replacement), identity-based echo suppression, queue-based SSE writes, an
events-first bootstrap that closes the snapshot/stream gap, and one-live-adapter-per-Flow
scoping (`UserWarning` otherwise).

ITER_V3_01–03 then made the diagram **LLM-authorable** (no SKELETON_V3 — v3 reuses the v2
scaffold). V3_01: a shipped `figureflow/1` JSON Schema, a single `validate()` ingestion funnel
that collects every problem into one repair-friendly `FlowValidationError`, optional node
positions (`pos=None` ⇒ unplaced) with renderer auto-layout-on-mount driven by a new
`Flow.layout_direction` trait. V3_02: `Flow.from_mermaid()` parsing a pinned flowchart subset
(`MermaidParseError`, warn-and-skip on style directives, subgraph→group). V3_03 (MVP
terminator): an MCP server behind the `figureflow[mcp]` extra (`figureflow-mcp` stdio console
script) wrapping `serve()` so an agent and a human edit the same Flow, plus `llms.txt` and the
`docs/prompts/` few-shot pack. Core `pip install figureflow` stays dependency-free. No
`NotImplementedError` stubs remain; `docs/planning/` is the historical record.

## Layout

```
pyproject.toml            # hatchling, src-layout; force-includes static/ into the wheel
package.json              # MAINTAINER-ONLY front-end build (esbuild + react + @xyflow/react)
bun.lock                  # committed for reproducible builds
js/index.js               # front-end source — renderer + mount (bundled → static/widget.js)
js/synccore.js            # shared JS sync-core (echo-guard), above the adapter fork
js/adapters/              # JS Transport adapters: anywidget.js, static.js, server.js
src/figureflow/
  __init__.py             # Shape, Node, Edge, Flow, _BASELINE; display/to_html/serve/stop; from_json/from_mermaid/strict
  serialize.py            # to_json / from_json / to_mermaid + the v3 validate() funnel + FlowValidationError
  mermaid_in.py           # v3 — Flow.from_mermaid: bounded flowchart parser + MermaidParseError (ITER_V3_02)
  mcp_server.py           # v3 — FastMCP server (figureflow-mcp), behind the [mcp] extra + lazy import (ITER_V3_03)
  synccore.py             # v2 — diff + is_echo + LOCK, shared by every adapter
  transport/              # v2 transport seam (Python side)
    base.py               # Transport ABC: bind/send_state/on_change/emit/start/stop
    anywidget_adapter.py  # notebook (ITER_V2_01)
    static_export.py      # to_html() + shared host-page renderer (ITER_V2_02)
    server_adapter.py     # ThreadingHTTPServer SSE+POST (ITER_V2_03, hardened in ITER_V2_04)
  static/
    widget.js             # PREBUILT esbuild bundle (checked in)
    widget.css            # container sizing only (xyflow CSS is bundled into widget.js)
    host.html             # shared host-page template (static export + server)
    figureflow.d.ts       # L3 custom-component typings (ships in the wheel)
    figureflow.schema.json # v3 — descriptive figureflow/1 JSON Schema (ships in the wheel, ITER_V3_01)
llms.txt                  # v3 — the library in ~1 page for machine consumption (ITER_V3_03)
docs/prompts/             # v3 — few-shot pack: JSON + mermaid emission, repair-loop transcript
examples/                 # runnable examples (quickstart, grouping_layout, serialization, custom_component, display_targets)
tests/                    # pytest suite (to_dict, positions, group, round-trip, mermaid, transport seam, validate, MCP)
tests/corpus/             # v3 — LLM-style mermaid flowcharts, the ITER_V3_02 import gate (≥90% clean)
docs/guide/               # end-user manual (getting started → display anywhere → custom components)
docs/planning/            # v1: SKELETON.md + ITER_01..06.md; v2: SKELETON_V2 + ITER_V2_01..04; v3: ITER_V3_01..03
```

## Commands

Use **bun**, not npm, for all front-end work.

```bash
bun install              # install front-end build deps
bun run build            # esbuild → src/figureflow/static/widget.js (minified)
bun run dev              # same, with --watch + sourcemap
pip install -e ".[dev]"  # editable install of the Python package + pytest
pip install -e ".[mcp]"  # adds the optional `mcp` SDK for the figureflow-mcp server (v3)
python -m pytest tests/ -v     # run the Python test suite
python -m pytest tests/ --cov=figureflow --cov-branch   # 100% line + branch coverage
python examples/quickstart.py  # run an example as a script (prints a text summary)
figureflow-mcp                 # run the MCP stdio server (requires the [mcp] extra)
```

`widget.js` is a build artifact that is checked in — **rebuild it (`bun run build`) after
editing `js/index.js`**, or the change won't reach the widget.

## Conventions

- **Plan-driven (historical).** `docs/planning/SKELETON.md` defined the full target surface
  and `ITER_01..06.md` filled it in — all six are implemented. Treat them as the spec/rationale
  of record. If you extend *past* the MVP, follow the same pattern: spec the section, resolve it
  against the most recent `ITER_NN.md` that changed it, else `SKELETON.md`.
- **Honestly-gated stubs (pattern, for new work).** No stubs remain through the v3 MVP. If you
  add a not-yet-built method beyond it, raise `NotImplementedError` naming the filling iteration
  (e.g. `"move_node is a post-MVP granular MCP tool"`) rather than shipping a silent no-op.
- **One ingestion funnel (v3).** Every path that builds a `Flow` from external text —
  `from_json`, `from_mermaid`, and the MCP tools — routes through `serialize.validate()`, which
  *collects* all problems into one `FlowValidationError`/`MermaidParseError` (one line each:
  `path: what's wrong. hint`) instead of failing fast. `strict=True` escalates forgiving
  coercions/skips to errors. Do not add a second, fail-on-first validation path.
- **Positions are optional (v3).** `Node.pos=None` means "unplaced"; `to_dict()` omits
  `position` and the renderer auto-lays unplaced nodes on mount via `Flow.layout_direction`.
  `positions()` reports only placed nodes. Keep `pos=(0,0)`-style explicit placement working.
- **MCP is a client, not a transport (v3).** `mcp_server.py` calls the public surface
  (`from_json`/`from_mermaid`/`serve()`/`to_json`/`to_mermaid`) only; it must never import deeper
  internals, and `figureflow` core must never import `mcp` (lazy import in `main()`).
  stdio servers must keep stdout protocol-clean — `serve()` is always called with `quiet=True`.
- **`to_dict()` emits the full payload.** `Node.to_dict()` serializes every style field into
  `data` (shape, fill, border, fonts, `width/height`, `html`, `svgPath`); `Edge.to_dict()`
  emits `type/style/markers/label/labelStyle`. Keep the camelCase keys in lock-step with what
  the front-end (`js/index.js`) reads — the two are a contract.
- **`_BASELINE`** is the single module-level dict of default field values fresh elements
  start from. It is internal — never surface it in a signature; it is not a theme.
- **Front-end is maintainer-side.** Never add a runtime CDN `<link>` or network fetch; the
  bundle must stay self-contained. Vendor everything through the esbuild step.
- **Stable type maps.** `nodeTypes`/`edgeTypes` are defined at JS module level (not inside
  `App`) so the graph isn't remounted every render.
- Python targets **≥ 3.9**; keep `from __future__ import annotations` and 3.9-compatible
  typing.
- **Docs travel with the API.** `README.md`, the `docs/guide/` manual, and `examples/` all
  document the public surface — update them in the same change that alters a signature,
  field name, or default.

## Out of MVP scope

Mermaid flowchart *import* landed in v3 (`from_mermaid`), but still out: mermaid diagram types
beyond flowcharts (sequence/class/state/gantt), `classDef`/style fidelity, and nested subgraphs
(extensions add rows to the ITER_V3_02 grammar table, not a redesign); multi-diagram MCP
sessions and granular MCP edit tools (`move_node`, per-element ops); MCP Apps in-chat canvas
embedding; agent-framework bindings (LangChain, Jupyter AI). Carried over from v1/v2:
system-clipboard copy, undo/redo of programmatic Python edits, obstacle-avoiding edge routing,
and a compile-against-source TS package. See `docs/planning/ITER_V3_03.md` § "Out of MVP scope"
and `docs/planning/SKELETON.md` § "Out of MVP scope".
