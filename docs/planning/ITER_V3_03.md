---
artifact: ITER_V3_03
status: ready
created: 2026-06-12
scope: The agent door (MVP terminator) — an MCP server behind a figureflow[mcp] extra exposing create/get/replace/export tools over one live diagram, wrapping serve()'s browser canvas so the agent and the human edit the same Flow; plus llms.txt and the prompt pack. Core install stays dependency-free.
sections_changed: [02, 03, 04]
sections_unchanged: [01, 05]
depends_on: [SKELETON_V2, ITER_V2_04, ITER_V3_01, ITER_V3_02]
mvp: true
mvp_target: A pip-installable v0.3 where an LLM can author a diagram coordinate-free (JSON against a published schema, or the mermaid it already speaks), get all validation problems back in one repair-friendly message, and — via `pip install figureflow[mcp]` — drive a live browser canvas through MCP tools while a human edits the same diagram, with agent reads reflecting human edits and vice versa.
---

# ITER_V3_03 — MCP adapter + LLM docs (MVP)

> **The carve-out iteration.** Everything before this was core (no new
> dependency); this is the one piece that genuinely is LLM-infrastructure, so it
> follows the pattern reserved for the deferred FastAPI server (ITER_V2_03
> §Post-MVP): an **optional extra**, in-repo, one version. The MCP server is
> *not* a fifth transport — it is a **client of the existing surface**: tools
> call `from_json`/`from_mermaid`/`serve()`/`to_json`/`to_mermaid` and nothing
> deeper. The Transport seam already did the hard work; this iteration is thin
> on purpose, which is what makes it a safe terminator.

## §01 · Concept
> Unchanged — see ITER_V3_01 §01. (The MCP server is the door for agents that
> live outside Python — Claude Code, Cursor, Desktop; the in-Python agent
> already has the library directly.)

## §02 · Architecture

> Model unchanged. An MCP session is **transient infrastructure** (the v1
> clipboard / v2 server-session posture — SKELETON_V2 §02): one process, one
> canonical `Flow`, one `serve()` canvas.

```
agent (MCP client) ──stdio──▶ figureflow-mcp process
                                 │  tools → Flow API
                                 ▼
                               Flow ──serve()──▶ browser canvas ◀── human
```

**Concurrency falls out of v2:** the agent's tool calls mutate `Flow` on the
MCP thread; the human's edits arrive via `/change` POSTs — both paths already
funnel through the sync-core lock and commit funnel (ITER_V2_04 §04). Agent
writes broadcast to the browser over SSE stamped `client_id="python"`; human
edits land in the traits the next `get_diagram` reads. **No new sync logic.**

**One diagram per server process** — pinned. Multi-diagram sessions are
deferred (§Out of MVP).

## §03 · Tech Stack

- **New optional dependency:** the official **`mcp` Python SDK** (FastMCP
  server API), behind the extra **`figureflow[mcp]`** in `pyproject.toml`, plus
  a console script **`figureflow-mcp`** (stdio transport — the standard for
  locally-spawned servers). Core `pip install figureflow` is untouched.
- Import of the MCP module is **lazy/guarded**: `figureflow` core never imports
  `mcp`; the console script does, with a clear "install figureflow[mcp]"
  message if missing.

> Otherwise unchanged — see SKELETON_V2 §03.

## §04 · Python layer

**New module `src/figureflow/mcp_server.py`** + console-script entry. FastMCP
server named `figureflow`, holding `self.flow: Flow | None`. Tools (request →
response shapes pinned; all responses JSON-serializable dicts):

- **`create_diagram(source: str, format: "json"|"mermaid" = "json",
  open_browser: bool = True) -> {url, warnings: [str]}`** — build via
  `from_json`/`from_mermaid` (ITER_V3_01/02), `serve(quiet=True)` it
  (ITER_V2_03/04 + the `quiet` keyword below), return the URL for the human and
  the collected warnings for the agent. Calling it again replaces the session:
  `stop()` the old server first (ITER_V2_03's re-`serve()` rule).
- **`get_diagram() -> {json: str, mermaid: str}`** — current canonical state
  including human edits: `to_json(self.flow)` + `to_mermaid(self.flow)` (the
  mermaid copy lets the agent *reason* in the dialect it knows; the JSON copy
  is lossless).
- **`replace_diagram(source: str, format) -> {warnings}`** — parse `source` via
  the same `from_json`/`from_mermaid` machinery, then apply the resulting
  nodes/edges (and `layout_direction`) as a **wholesale load on the live
  `Flow`** — the `load_json` path, not a new `Flow` instance, so the running
  server and its SSE streams are untouched; the load pushes to the open browser
  and clears undo history per the ITER_03/ITER_05 wholesale-load rule.
- **`add_elements(nodes_json: str = "[]", edges_json: str = "[]") ->
  {warnings}`** — incremental adds through the same `validate()` funnel; new
  nodes may be unplaced (auto-layout places them on the next render pass,
  ITER_V3_01 §05).
- **`close_diagram() -> {}`** — `flow.stop()`.

**One core API touch — `Flow.serve()` gains `quiet: bool = False`:** suppresses
the URL print (ITER_V2_03 §04), return value unchanged. Added here because the
MCP entry point must keep stdout protocol-clean (gotcha below); redirecting
stdout around the call would be the fragile alternative.

**Error contract (the LLM-facing rule):** `FlowValidationError` /
`MermaidParseError` are caught and returned as **tool results**
`{error: "<the collected one-line messages>"}` — never raised as protocol
errors — so the agent's repair loop reads them as ordinary content. Tools
called before `create_diagram` return `{error: "no diagram; call
create_diagram first"}`.

> **Gotcha — stdio servers must not touch stdout.** The MCP stdio transport
> *is* stdout; any stray `print` corrupts the protocol. The MCP entry point
> routes all figureflow logging to **stderr**, and `serve()` is always called
> with `quiet=True` (the keyword added above).

> **Gotcha — port lifetime:** `serve(port=0)` per ITER_V2_03; the URL is only
> valid while the MCP process lives, which the `create_diagram` response states.

**LLM docs (shipped with this iteration, repo-level):**
- **`llms.txt`** — the library in ~1 page for machine consumption: the schema
  file location, `from_mermaid` subset summary (the ITER_V3_02 table,
  condensed), the error-message contract, MCP tool list.
- **`docs/prompts/`** — few-shot pack: two JSON-emission examples against the
  schema, two mermaid examples inside the supported subset, one repair-loop
  transcript (broken input → error → fixed input).

> Validation funnel — ITER_V3_01 §04. Parser — ITER_V3_02 §04. Server/sync —
> ITER_V2_03/04 §04.

## §05 · Front-end widget
> Unchanged — see ITER_V3_01 §05. (The MCP path reuses `serve()`'s host page
> and adapter wholesale; zero JS in this iteration.)

**Verification step:** (1) Register `figureflow-mcp` with an MCP client (Claude
Code or Desktop); from a prompt, have the agent `create_diagram` with mermaid —
browser opens, diagram renders laid-out. (2) Drag nodes as the human; agent's
`get_diagram` JSON reflects the moved positions. (3) Agent `add_elements` with
an unplaced node — it appears placed in the browser without a human action.
(4) Feed `create_diagram` invalid JSON — the tool *returns* the multi-problem
error, the agent repairs, second call succeeds. (5) `pip install figureflow`
(no extra) in a clean venv — core imports fine, `figureflow-mcp` exits with the
install-the-extra message. (6) Protocol stays clean: no stdout writes outside
MCP framing during a full session (pipe-capture check).

## Out of MVP scope

- **Multi-diagram MCP sessions** (several Flows per server, diagram ids on
  every tool). One canvas per process is the v0.3 posture.
- **MCP Apps in-chat canvas embedding** (tldraw-style interactive UI inside the
  chat client). v0.3 hands the human a browser tab via `serve()`; embedding is
  a fast-moving spec to revisit post-MVP.
- **Mermaid grammar beyond the ITER_V3_02 table** — other diagram types
  (sequence, class, state, gantt), `classDef`/style fidelity, nested
  subgraphs. Extensions add rows to the pinned table, not a redesign.
- **Agent-framework bindings** (LangChain tool wrappers, Jupyter AI) — the
  alternate distribution channel; revisit after observing where v0.3 adoption
  comes from.
- **Granular MCP edit tools** (`move_node`, `restyle_node`, per-element ops) —
  `replace_diagram`/`add_elements` cover the MVP loop; finer tools follow real
  agent usage, not speculation.
- Carried over from v1/v2: format import beyond mermaid, element-level
  diff/binary sync, multi-client sessions, system clipboard.
