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

Status: **v1 MVP + v2 multi-transport, both implemented.** ITER_01–ITER_06 landed the v1
surface: per-element node shapes/styling (+ L1 `svg_path`, L2 `html`), edge styling at parity,
multi-select + within-canvas styled copy/paste, minimap, canvas undo/redo, grouping, dagre
auto-layout, JSON save/load + mermaid export, and the L3 custom-component escape hatch
(`emit`/`on`). SKELETON_V2 + ITER_V2_01–03 then added the **transport seam**: one renderer
behind three doors — `display()` (notebook), `to_html()` (offline interactive snapshot), and
`serve()`/`stop()` (live browser tab over a dependency-free stdlib SSE+POST server). No
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
  __init__.py             # Shape, Node, Edge, Flow, _BASELINE; display/to_html/serve/stop
  serialize.py            # to_json / from_json / to_mermaid (the shared wire format)
  synccore.py             # v2 — diff + is_echo + LOCK, shared by every adapter
  transport/              # v2 transport seam (Python side)
    base.py               # Transport ABC: bind/send_state/on_change/emit/start/stop
    anywidget_adapter.py  # notebook (ITER_V2_01)
    static_export.py      # to_html() + shared host-page renderer (ITER_V2_02)
    server_adapter.py     # ThreadingHTTPServer SSE+POST (ITER_V2_03)
  static/
    widget.js             # PREBUILT esbuild bundle (checked in)
    widget.css            # container sizing only (xyflow CSS is bundled into widget.js)
    host.html             # shared host-page template (static export + server)
    figureflow.d.ts       # L3 custom-component typings (ships in the wheel)
examples/                 # runnable examples (quickstart, grouping_layout, serialization, custom_component, display_targets)
tests/                    # pytest suite (to_dict, positions, group, JSON round-trip, mermaid, transport seam)
docs/guide/               # end-user manual (getting started → display anywhere → custom components)
docs/planning/            # v1: SKELETON.md + ITER_01..06.md; v2: SKELETON_V2.md + ITER_V2_01..03.md
```

## Commands

Use **bun**, not npm, for all front-end work.

```bash
bun install              # install front-end build deps
bun run build            # esbuild → src/figureflow/static/widget.js (minified)
bun run dev              # same, with --watch + sourcemap
pip install -e ".[dev]"  # editable install of the Python package + pytest
python -m pytest tests/ -v     # run the Python test suite
python examples/quickstart.py  # run an example as a script (prints a text summary)
```

`widget.js` is a build artifact that is checked in — **rebuild it (`bun run build`) after
editing `js/index.js`**, or the change won't reach the widget.

## Conventions

- **Plan-driven (historical).** `docs/planning/SKELETON.md` defined the full target surface
  and `ITER_01..06.md` filled it in — all six are implemented. Treat them as the spec/rationale
  of record. If you extend *past* the MVP, follow the same pattern: spec the section, resolve it
  against the most recent `ITER_NN.md` that changed it, else `SKELETON.md`.
- **Honestly-gated stubs (pattern, for new work).** No stubs remain in the MVP. If you add a
  not-yet-built method beyond it, raise `NotImplementedError` naming the filling iteration
  (e.g. `"Flow.import_mermaid is implemented in ITER_07"`) rather than shipping a silent no-op.
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

Format *import* (parsing mermaid into figureflow), system-clipboard copy, undo/redo of
programmatic Python edits, obstacle-avoiding edge routing, and a compile-against-source TS
package. See `docs/planning/SKELETON.md` § "Out of MVP scope".
