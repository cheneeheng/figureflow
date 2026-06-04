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

Status: **v0.1 — full MVP implemented.** ITER_01–ITER_06 all landed: per-element node
shapes/styling (+ L1 `svg_path`, L2 `html`), edge styling at parity, multi-select +
within-canvas styled copy/paste, minimap, canvas undo/redo, grouping, dagre auto-layout,
JSON save/load + mermaid export, and the L3 custom-component escape hatch (`emit`/`on`).
No `NotImplementedError` stubs remain; `docs/planning/` is now the historical record of
how the surface was filled in.

## Layout

```
pyproject.toml            # hatchling, src-layout; force-includes static/ into the wheel
package.json              # MAINTAINER-ONLY front-end build (esbuild + react + @xyflow/react)
bun.lock                  # committed for reproducible builds
js/index.js               # front-end source (bundled → static/widget.js)
src/figureflow/
  __init__.py             # Shape, Node, Edge, Flow, _BASELINE
  serialize.py            # to_json / from_json / to_mermaid
  static/
    widget.js             # PREBUILT esbuild bundle (checked in)
    widget.css            # container sizing only (xyflow CSS is bundled into widget.js)
    figureflow.d.ts       # L3 custom-component typings (ships in the wheel)
examples/                 # runnable examples (quickstart, grouping_layout, serialization, custom_component)
tests/                    # pytest suite (to_dict, positions, group, JSON round-trip, mermaid)
docs/guide/               # end-user manual (getting started → custom components)
docs/planning/            # SKELETON.md (authoritative) + ITER_01..06.md (iterations)
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
