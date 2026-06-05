---
artifact: ITER_V2_02
status: ready
created: 2026-06-05
scope: The static HTML export adapter — Flow.to_html() writes a self-contained, offline, client-side-interactive snapshot (bundle + JSON island), with a one-way "download JSON" escape and no live round-trip.
sections_changed: [04, 05]
sections_unchanged: [01, 02, 03]
depends_on: [SKELETON_V2, ITER_V2_01]
mvp: false
---

# ITER_V2_02 — Static HTML export adapter

> **The cheapest adapter, on purpose.** Static export is the simplest possible
> consumer of the seam — one-way, no live round-trip — so it proves the `Transport`
> interface works for a non-anywidget pipe before the heavier server adapter
> takes it on. If `to_html()` renders a correct, manipulable diagram, the seam is
> sound.

## §01 · Concept
> Unchanged — see SKELETON_V2 §01. (`to_html()` is the "frozen snapshot" door.)

## §02 · Architecture
> No new entities or traits. Reuses the v1 wire format: `to_html` serializes via
> the *existing* `serialize.to_json` (ITER_05) into a JSON island embedded in the
> page. The static adapter's "pipe" is no pipe — state is baked in at write time,
> so `pushChange` has no network target and instead captures edits in-memory for
> the download affordance (§05), never reaching Python live (SKELETON_V2 §02).

## §03 · Tech Stack
> Unchanged — see SKELETON_V2 §03. The page inlines the *existing* vendored bundle
> (`static/widget.js` + `widget.css`); no CDN, no network at view time, opens via
> `file://`.

## §04 · Python layer

**`transport/static_export.py` (implement) + `Flow.to_html(path=None, *,
title=None) -> str`** (replace the stub):
- Serialize the current diagram with `serialize.to_json(self)` (ITER_05) — the
  same lossless envelope `from_json` reads, so a downloaded JSON re-imports exactly.
- Read the prebuilt `static/widget.js` and `widget.css` from the package and the
  shared `static/host.html` template — a page shell with substitution points for
  head assets (inlined here, linked by the server) and adapter selection, so both
  modes reuse one template (introduced here; the server consumes it in ITER_V2_03).
- Produce one HTML string with: the CSS inlined in a `<style>`, the bundle inlined
  in a `<script>`, the diagram JSON in a **`<script type="application/json"
  id="figureflow-state">`** island (a data island, *not* a string literal — avoids
  `</script>` and quote-escaping hazards), and a small bootstrap that constructs
  the **static JS adapter** with that island and mounts the renderer.
- If `path` is given, write the string there (UTF-8) and still return it; if not,
  just return it (notebook users can `display(HTML(...))` it).
- `start`/`stop` inherit the base no-ops (no live pipe).

This method is **pure and side-effect-free** beyond an optional file write — it
reads the live `Flow` once and freezes it. No server, no thread, no port.

> `to_json`/`from_json` unchanged — see ITER_05. Model unchanged — SKELETON.md §02.

## §05 · Front-end widget

**Implement the static JS adapter** against the `Transport` interface
(SKELETON_V2 §05):
- `getState()` — parse the `#figureflow-state` JSON island once and return it.
- `subscribe(cb)` — register but never fire (no upstream pushes); return a no-op
  unsubscribe.
- `pushChange(patch)` — **does not error and does not silently vanish**: it
  updates an in-memory "current state" the download affordance reads, so a user
  who rearranges nodes can export *their* layout, not the original. There is no
  network call.
- `sendEvent` — no-op (custom-component events have no Python to reach here).

**Client-side interactivity is fully live** because React Flow runs in the
browser: pan, zoom, drag, multi-select, and the minimap all work from the bundle
alone (ITER_01–ITER_03 renderers are unchanged). What's absent is *only* the
push-back to Python.

**One-way escape — "Download JSON" control.** A small button (rendered only in
static mode, keyed off the adapter) serializes the adapter's current in-memory
state to a `.json` download via a Blob URL. Document that this file is
`from_json`-compatible, closing the manual round-trip: edit in the browser →
download → `Flow.from_json(open(...).read())` back in Python.

**Carried-forward gotchas:** module-level `nodeTypes`/`edgeTypes`; StrictMode-
guarded one-time setup (the island parse runs once); single React instance from
the shared bundle (no second React introduced by the static path).

> Renderer/shapes/edges/editing — see ITER_01–ITER_04 §05. Seam/sync-core —
> ITER_V2_01 §05.

**Verification step:** (1) build a styled, grouped diagram; `to_html("out.html")`;
open the file with no network — confirm all shapes/edges/labels render and pan/
zoom/drag/minimap work offline. (2) Rearrange nodes, click Download JSON, and
assert `Flow.from_json(downloaded)` reproduces the *rearranged* layout (proving
`pushChange` captured client edits into the export). (3) Confirm `subscribe`
never fires and no network request is made at view time.
