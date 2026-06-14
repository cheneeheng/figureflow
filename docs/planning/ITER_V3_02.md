---
artifact: ITER_V3_02
status: ready
created: 2026-06-12
scope: Mermaid import, bounded — Flow.from_mermaid() parsing a pinned subset of the mermaid flowchart grammar into the figureflow model, with repair-friendly errors, warn-and-skip on unsupported directives, subgraph→group mapping, and placement via the ITER_V3_01 auto-layout path. Other mermaid diagram types and style fidelity are explicitly out.
sections_changed: [02, 04]
sections_unchanged: [01, 03, 05]
depends_on: [SKELETON_V2, ITER_V2_04, ITER_V3_01]
mvp: false
---

# ITER_V3_02 — Mermaid flowchart import (bounded)

> **Empirical-risk iteration — the v3 gamble, deliberately fenced.** Import was
> v1's "one unbounded item we consciously cut" (SKELETON §Out of MVP). It comes
> in now because the strategy demands it (LLMs already emit mermaid; figureflow
> upgrades it to interactive), and it stays bounded because **the grammar is
> pinned in this document** — the parser's job is the table below, not "parse
> mermaid." The risk is empirical, like ITER_01/ITER_03 before it: the pinned
> subset must be validated against a corpus of ~50 real LLM-generated
> flowcharts (the done-check). If corpus coverage is poor, the fix is adding
> rows to the table in a follow-up — not reopening this design. If it balloons
> anyway, the v3 MVP falls back to JSON-only ingestion: the terminator (a later
> iteration) does not depend on this parser's completeness, only on its
> existence behind `format="mermaid"`.

## §01 · Concept
> Unchanged — see ITER_V3_01 §01. (`from_mermaid` is the zero-new-tokens door:
> the LLM emits the dialect it already knows; figureflow makes it interactive.)

## §02 · Architecture

> Model unchanged — the parser is a **pure function into the existing model**:
> mermaid text → `(nodes: list[Node], edges: list[Edge], warnings)` → the same
> `validate()` funnel as JSON (ITER_V3_01) → `Flow`. Nodes are created
> **unplaced** (`pos=None`); placement is entirely ITER_V3_01's
> auto-layout-on-mount. No new traits, no front-end work, no new entities.
> `MermaidParseError` (carries `line`, `hint`; same one-line message contract as
> `FlowValidationError`) is transient, defined beside the parser.

## §03 · Tech Stack
> Unchanged — see SKELETON_V2 §03. The parser is hand-written line-oriented
> stdlib Python (`re` + a small tokenizer for bracket pairs). **No parser
> library** — the pinned subset below does not warrant one, and core stays
> dependency-free.

## §04 · Python layer

**New module `src/figureflow/mermaid_in.py`** (mirror of `serialize.py`'s
`to_mermaid` direction) **+ `Flow.from_mermaid(s, *, strict=False) -> Flow`**
(classmethod, new public symbol — the one v3 addition to the core API surface
alongside ITER_V3_01's `strict` keywords).

**The pinned grammar (the contract — parse exactly this):**

| Construct | Accepted forms | Maps to |
| --- | --- | --- |
| Header | `flowchart <dir>` / `graph <dir>`; dir `TB TD BT LR RL` (`TD`→`TB`); missing dir → `TB` | `Flow.layout_direction` (ITER_V3_01 §02) — consumed by the auto-layout pass |
| Node shapes | `id[label]` `id(label)` `id([label])` `id((label))` `id{label}` `id{{label}}` `id[/label/]` `id[(label)]`; bare `id` | rectangle, rounded, stadium, ellipse, diamond, hexagon, parallelogram, cylinder; bare → rectangle, label=id |
| Labels | unquoted, `"quoted"`, `<br>`/`<br/>` → newline; first definition wins, later bare references reuse | `Node.label` |
| Edge ops | `-->` `---` `-.->` `-.-` `==>` `===` | arrow/none `marker_end`; `-.`→`dash="dashed"`; `==`→`width` 3 |
| Edge labels | `-->|label|` and `-- label -->` (both inline forms) | `Edge.label` |
| Chains & fans | `a --> b --> c`; `a & b --> c`; `a --> b & c` | expanded to individual edges |
| Subgraph | `subgraph id [title] … end`, **one level** (matches ITER_04's one-level grouping); nested → warning, inner flattened | an unplaced group node (label=title) + `parent_id`/`extent="parent"` set directly on members — **not** via `Flow.group()`, whose bounding-box math (ITER_04 §04) needs placed members; geometry comes from the unplaced-group rule in ITER_V3_01 §05 |
| Comments | `%%` to end of line | dropped |

**Warn-and-skip (collected as warnings, content preserved nowhere):**
`classDef`, `class`, `style`, `linkStyle`, `click`, `direction` inside a
subgraph, accessibility directives, interaction syntax. One warning per
directive kind, with line numbers — e.g. `line 12: 'classDef' is not imported;
figureflow styling is per-element Python kwargs. Directive skipped.` Style
fidelity is **out by design**: import is structural, the inverse of
`to_mermaid`'s documented lossiness (ITER_05 §04).

**Hard errors (`MermaidParseError`, collected like ITER_V3_01):** non-flowchart
header (`sequenceDiagram`, `classDiagram`, … — name the unsupported type and
state only flowcharts import); unbalanced shape brackets (line + the opening
token); unknown edge operator (line + the nearest supported one). `strict=True`
escalates warnings, mirroring `from_json`.

**Round-trip note (sets the verification bar honestly):**
`to_mermaid(from_mermaid(x))` is structure-preserving (same nodes, shapes,
edges, labels, groups), **not** byte-identical — id ordering and label quoting
may normalize. Assert graph-equality, not string equality.

> `from_json`/validation funnel — see ITER_V3_01 §04. `to_mermaid` — ITER_05
> §04. `group()` — ITER_04 §04.

## §05 · Front-end widget
> Unchanged — see ITER_V3_01 §05 (unplaced-node auto-layout does all the work;
> the parser ships no JS).

**Verification step:** (1) **The corpus check (the gate):** collect ~50
LLM-generated flowcharts (prompt a few current models for varied diagrams —
pipelines, state flows, org charts, with subgraphs and edge labels); ≥ 90% must
import with zero hard errors, and every hard error message must be specific
enough that pasting it back to the LLM yields a fixed diagram in one round.
Record the corpus in `tests/corpus/`. (2) Each grammar-table row has a unit
test importing and asserting the mapped model. (3) A subgraph'd diagram imports
into a working group (drag-together per ITER_04). (4) Structure-preserving
round-trip per the note above. (5) `sequenceDiagram` input fails with the
named-type error, not a generic parse failure.
