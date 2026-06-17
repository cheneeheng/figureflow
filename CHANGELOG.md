# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2026-06-17

LLM-authorable release. A diagram can now be authored **coordinate-free** from
text an LLM already speaks — figureflow validates, places, and renders it. Three
new ingestion paths (`from_json`, `from_mermaid`, and an optional MCP server) all
funnel through one validator that collects every problem into a single
repair-friendly error. Core `pip install figureflow` stays dependency-free.

### Added

- **One ingestion funnel** — every path that builds a `Flow` from external text
  routes through a single `validate()` that *collects* all problems into one
  `FlowValidationError` (one line each: `path: what's wrong. hint`) instead of
  failing on the first, so a model can fix every fault in one round-trip.
  `strict=True` escalates forgiving coercions/skips to hard errors.
- **Optional node positions** — `Node(pos=None)` means *unplaced*; `to_dict()`
  omits `position` and the renderer auto-lays unplaced nodes on mount via the new
  `Flow(layout_direction=...)` trait (`TB` default, or `BT`/`LR`/`RL`).
  `positions()` reports only placed nodes; explicit `pos=(x, y)` still works.
- **`Flow.from_mermaid()`** — parses a pinned mermaid flowchart subset into a
  live Flow: node shapes map from the bracket syntax, edge labels carry over, and
  a `subgraph … end` block imports as a one-level group. Style directives are
  warn-and-skipped; grammar violations raise `MermaidParseError`.
- **Published `figureflow/1` JSON Schema** — ships in the wheel at
  `figureflow/static/figureflow.schema.json`, alongside `llms.txt` (the library
  in ~1 page for machine consumption) and a `docs/prompts/` few-shot pack
  (JSON + mermaid emission and a repair-loop transcript).
- **MCP server (optional `[mcp]` extra)** — a `figureflow-mcp` stdio console
  script wraps `serve()` so an agent and a human edit the same live canvas,
  exposing `create_diagram` / `get_diagram` / `replace_diagram` / `add_elements`
  / `close_diagram`. It calls only the public surface; core install adds no deps.

### Fixed

- **Blank canvas after auto-layout** — the post-layout refit now waits until
  React Flow has *measured* the placed nodes before calling `fitView`, instead of
  firing on a single `requestAnimationFrame` that could beat the ResizeObserver
  and frame a zero-size box.

[3.0.0]: https://github.com/cheneeheng/figureflow/releases/tag/v3.0.0

## [2.0.1] - 2026-06-14

Test-only release; no behavior or API changes.

### Changed

- Closed the remaining branch-coverage gaps in the test suite (idempotent
  `display()` rebind, `send_state` with partial meta, edges-only
  `handle_change`, a no-nonce layout request, and `stop()` with no server
  thread). The suite is now at 100% statement **and** branch coverage.

[2.0.1]: https://github.com/cheneeheng/figureflow/releases/tag/v2.0.1

## [2.0.0] - 2026-06-14

Multi-transport release. The same renderer now ships through three doors —
`display()` (notebook), `to_html()` (offline interactive snapshot), and
`serve()` / `stop()` (live browser tab over a dependency-free stdlib SSE+POST
server) — built on a shared transport seam. The front-end remains a prebuilt,
vendored, offline bundle.

### Added

- **Transport seam** — one renderer behind three transports, selected from Python:
  - `Flow.display()` renders the widget in any Jupyter host (returns `self`).
  - `Flow.to_html(path=...)` writes a self-contained, offline-interactive HTML
    snapshot with a "Download JSON" affordance.
  - `Flow.serve()` / `Flow.stop()` run a live, bidirectional browser tab over a
    dependency-free stdlib `ThreadingHTTPServer` (SSE `GET /events` down,
    `POST /change` up; localhost only).
- **Hardened server sync** — a pinned patch envelope (`client_id` + `seq`,
  full-array replacement), identity-based echo suppression, queue-based SSE
  writes, an events-first bootstrap that closes the snapshot/stream gap, and
  one-live-adapter-per-`Flow` scoping (`UserWarning` otherwise).
- **All-in-one examples notebook** — `examples/examples.ipynb` collects every
  example in one runnable notebook that renders each widget inline.

### Changed

- **Examples renumbered** `01_`–`05_`; the custom-component examples are merged
  into `04_custom_component.py`, demonstrating both notebook-safe handler
  patterns (collect-to-list and live `ipywidgets.Output`). README and the
  `docs/guide/` cross-references were updated to match.

### Fixed

- **L3 custom components rerun blank** — the dynamically imported component
  module is now cache-busted per mount so it re-binds React from
  `globalThis.figureflow` on every notebook rerun / kernel restart. Previously
  the cached module stranded the old React, causing an invalid-hook-call and a
  blank canvas on any rerun.
- **Duplicate event prints** — the custom-component example no longer stacks
  multiple printing `on("clicked", ...)` handlers, so one click prints once.

[2.0.0]: https://github.com/cheneeheng/figureflow/releases/tag/v2.0.0

## [1.0.0] - 2026-06-05

First stable release. figureflow is a pip-installable [anywidget](https://anywidget.dev)
library that renders interactive flow diagrams in any Jupyter host (JupyterLab, Notebook,
Colab, VS Code, marimo), wrapping [React Flow](https://reactflow.dev) (`@xyflow/react` v12).
The front-end ships as a prebuilt, vendored bundle, so end users never run a JS toolchain
and the widget works offline.

### Added

- **Per-element node styling** — shape, fill, border, and font configured per node from
  Python, the way you'd format a single shape in a drawing tool, plus the L1 `svg_path` and
  L2 `html` escape hatches.
- **Edge styling at parity** with nodes — `type`, `style`, markers, label, and `labelStyle`.
- **Multi-select** and within-canvas styled copy/paste.
- **Minimap** for canvas navigation.
- **Canvas undo/redo.**
- **Grouping** of nodes.
- **dagre auto-layout.**
- **Serialization** — JSON save/load and mermaid export.
- **L3 custom-component escape hatch** (`emit`/`on`) for fully custom front-end behavior,
  with `figureflow.d.ts` typings shipped in the wheel.
- Public Python API: `Shape`, `Node`, `Edge`, `Flow`.
- End-user manual under `docs/guide/` and runnable examples (`quickstart`,
  `grouping_layout`, `serialization`, `custom_component`).
- pytest suite covering `to_dict`, positions, grouping, JSON round-trip, and mermaid export.

[1.0.0]: https://github.com/cheneeheng/figureflow/releases/tag/v1.0.0
