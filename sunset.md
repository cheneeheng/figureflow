# Sunsetting figureflow

**Status:** Sunset / archived — no longer maintained.
**Date:** 2026-06-17
**Final state:** Archived, as-is. The code stays public and installable, frozen at
its current version. There will be no further development, bug fixes, or
compatibility updates. **Use at your own risk** — it may break with future versions
of Jupyter, anywidget, or React Flow.

This document records the decision to sunset figureflow, the reasons behind it, and
the parts of the work worth being proud of.

## What figureflow was

figureflow is a pip-installable [anywidget](https://anywidget.dev) library that renders
interactive flow diagrams in any Jupyter host (JupyterLab, Notebook, Colab, VS Code,
marimo) by wrapping [React Flow](https://reactflow.dev) (`@xyflow/react` v12). Each node
and edge is styled per-element from Python — shape, fill, border, font — the way you'd
format a single shape in a drawing tool. The front-end ships as a prebuilt, vendored
bundle, so end users never run a JS toolchain and the widget works offline with no CDN.

It started as a curiosity: **can xyflow be wrapped in Python easily?** The answer turned
out to be yes — and the result was a genuinely working library that lets you build
diagrams from Python much like arranging shapes in PowerPoint.

## Why sunset it

Two questions drove the project, and both got answered:

1. **Can xyflow be wrapped in Python easily?** Yes. anywidget made wrapping a complex
   JS library for Jupyter far more tractable than expected. Curiosity satisfied.

2. **Can this be a library that LLM agents use to easily create interactive diagrams?**
   This was the second goal, and it's the one that ultimately led to the sunset. After
   building out the v3 LLM-ingestion surface — a JSON Schema, a single `validate()`
   funnel, `from_mermaid()`, and an MCP server — the honest conclusion was that the use
   cases for *interactive* agent-authored diagrams are limited compared to just emitting
   **static** diagrams. For most agent and document workflows, a static
   [mermaid](https://mermaid.js.org/) diagram is simpler, more portable, and good enough.
   The interactive layer added real cost without a clear payoff for that audience.

Both founding questions were resolved. There's no third question compelling enough to
justify ongoing maintenance, so the project is being wound down while it's in a clean,
complete state rather than left to bit-rot mid-feature.

## What it became — and what I'm proud of

The project went a lot further than a one-off experiment. Across three versions it grew
into a complete, shippable library, and a few things stand out:

- **PowerPoint-like per-element styling.** Every node and edge is styled individually from
  Python — shape, fill, border, fonts — directly as keyword arguments. Building a diagram
  feels like formatting shapes in a drawing tool, which was the whole "this is very cool"
  moment that kept the project going.

- **Zero-toolchain, offline widget.** React + @xyflow/react (+ its CSS) are bundled into a
  single prebuilt, vendored `widget.js` that ships in the wheel. End users install with one
  `pip install`, never touch a JS toolchain, and the widget works offline with no CDN. The
  bundle stayed self-contained from start to finish — no runtime network fetch ever crept in.

- **Display-anywhere transport seam.** One renderer behind three doors: `display()` for the
  notebook, `to_html()` for an offline interactive snapshot, and `serve()`/`stop()` for a
  live browser tab over a dependency-free stdlib SSE+POST server. Decoupling the renderer
  from the delivery channel turned out to be a clean, reusable design — and the server path
  was hardened with a pinned patch envelope, echo suppression, and an events-first bootstrap.

- **LLM-authorable diagrams.** v3 made the diagram machine-authorable: a shipped
  `figureflow/1` JSON Schema, a single `validate()` ingestion funnel that collects every
  problem into one repair-friendly error, optional node positions with renderer
  auto-layout, `Flow.from_mermaid()`, and an MCP server so an agent and a human could edit
  the same Flow. Even though this surface is also what revealed the project's ceiling, it
  was a satisfying piece of engineering.

## Lessons learned

- **For LLMs, static beats interactive.** The clearest takeaway: for agent-authored
  diagrams, static mermaid output is simpler and good enough. Interactive editing adds cost
  without a clear payoff for that use case. This is the insight that decided the sunset.

- **anywidget makes wrapping a JS library genuinely easy.** Bringing a complex front-end
  library like React Flow into Jupyter was far more approachable than expected. anywidget is
  a great tool for this kind of bridge.

- **The transport seam was worth it.** Separating the renderer from how it's delivered
  (notebook / HTML / live server) was a clean abstraction that paid for itself every time a
  new display target was added.

- **Scope discipline paid off.** Plan-driven iterations (`SKELETON.md` + `ITER_NN.md`) and
  honestly-gated stubs kept the project shippable at every stage. There was never a
  half-built mess; each version was a complete, coherent surface. That discipline is also
  what makes it safe to archive now — it's being frozen at a clean state, not abandoned
  mid-feature.

## What to use instead

If you found figureflow looking for a diagramming solution:

- **Static diagrams:** Use [mermaid](https://mermaid.js.org/). For most documentation,
  notebook, and LLM-agent workflows, a static mermaid diagram is simpler, more portable, and
  entirely sufficient — this is the realization that drove figureflow's sunset.

- **Interactive diagrams:** Use [React Flow](https://reactflow.dev) (`@xyflow/react`)
  directly if you genuinely need an interactive, editable canvas. figureflow was a Python
  wrapper around it; going to the source gives you the full, maintained library.

## Thanks

This was a fun one to build. It proved a curiosity, shipped a real working library, and
taught a clear lesson about where interactive diagrams do and don't earn their keep. That's
a good place to stop.
