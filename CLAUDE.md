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

Status: **v0.1, skeleton stage.** The render + sync loop works; most styling/feature
surface is present in the API but gated to later iterations (see Planning docs).

## Layout

```
pyproject.toml            # hatchling, src-layout; force-includes static/ into the wheel
package.json              # MAINTAINER-ONLY front-end build (esbuild + react + @xyflow/react)
bun.lock                  # committed for reproducible builds
js/index.js               # front-end source (bundled → static/widget.js)
src/figureflow/
  __init__.py             # Shape, Node, Edge, Flow, _BASELINE
  static/
    widget.js             # PREBUILT esbuild bundle (checked in)
    widget.css            # container sizing only (xyflow CSS is bundled into widget.js)
docs/planning/            # SKELETON.md (authoritative) + ITER_01..06.md (iterations)
```

## Commands

Use **bun**, not npm, for all front-end work.

```bash
bun install            # install front-end build deps
bun run build          # esbuild → src/figureflow/static/widget.js (minified)
bun run dev            # same, with --watch + sourcemap
pip install -e .       # editable install of the Python package
```

`widget.js` is a build artifact that is checked in — **rebuild it (`bun run build`) after
editing `js/index.js`**, or the change won't reach the widget.

## Conventions

- **Plan-driven.** `docs/planning/SKELETON.md` defines the full target surface; `ITER_NN.md`
  files fill it in. Implement only what a section specifies. Resolution order for a section:
  most recent `ITER_NN.md` whose `sections_changed` includes it, else `SKELETON.md`.
- **Honestly-gated stubs.** Methods not yet implemented raise `NotImplementedError` naming
  the filling iteration (e.g. `"Flow.undo is implemented in ITER_03"`). Keep that pattern.
- **Skeleton `to_dict` is a subset.** `Node`/`Edge` carry their full field lists, but
  `to_dict()` only emits what the front-end currently honors (`id/type/position/data` for
  nodes, `id/source/target` for edges). Later iterations widen this — don't widen it ahead
  of the iteration that calls for it.
- **`_BASELINE`** is the single module-level dict of default field values fresh elements
  start from. It is internal — never surface it in a signature; it is not a theme.
- **Front-end is maintainer-side.** Never add a runtime CDN `<link>` or network fetch; the
  bundle must stay self-contained. Vendor everything through the esbuild step.
- **Stable type maps.** `nodeTypes`/`edgeTypes` are defined at JS module level (not inside
  `App`) so the graph isn't remounted every render.
- Python targets **≥ 3.9**; keep `from __future__ import annotations` and 3.9-compatible
  typing.

## Out of MVP scope

Format *import* (parsing mermaid into figureflow), system-clipboard copy, undo/redo of
programmatic Python edits, obstacle-avoiding edge routing, and a compile-against-source TS
package. See `docs/planning/SKELETON.md` § "Out of MVP scope".
