# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
