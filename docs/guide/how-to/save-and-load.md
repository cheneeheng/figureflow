# Save and load

Persist a diagram to JSON and rebuild it later — losslessly — or export a structural mermaid
flowchart.

**Prerequisites:** a `Flow` you want to save ([Getting started](../getting-started.md)).

## Save to JSON

`to_json()` returns a versioned, self-contained JSON string of the whole diagram — nodes,
edges, styling, group structure, positions, and the flow's `color_mode` / `fit_view` /
`height`:

```python
snapshot = flow.to_json()

with open("diagram.json", "w") as f:
    f.write(snapshot)
```

Because positions are included, a reload needs no re-layout.

**Verify:** `snapshot` is a non-empty string; the file contains `"schema": "figureflow/1"`.

## Rebuild a new flow from JSON

`Flow.from_json()` is a classmethod that constructs a **new** `Flow` from a snapshot:

```python
from figureflow import Flow

with open("diagram.json") as f:
    snapshot = f.read()

flow2 = Flow.from_json(snapshot)
flow2   # display the restored diagram
```

The round-trip is exact: `Flow.from_json(flow.to_json())` reproduces the nodes and edges
(modulo key ordering).

> **Errors:** a snapshot from an incompatible future schema raises `ValueError`
> (`Unsupported figureflow schema ...`). Snapshots written by figureflow `0.1.x` use schema
> `figureflow/1`.

**Verify:** `flow2` has the same node and edge counts as the original and renders identically.

## Replace a live diagram in place

To load a snapshot into an **already-displayed** widget (instead of creating a new one), use
`load_json()`:

```python
flow.load_json(snapshot)
```

This replaces the current nodes and edges on the live canvas and **clears the undo history**
(the loaded diagram becomes the new baseline).

**Verify:** the displayed canvas updates to the loaded diagram; an immediate `flow.undo()`
does nothing (history was cleared).

## Export a mermaid flowchart

`to_mermaid()` emits [mermaid](https://mermaid.js.org) flowchart text. This is a **lossy,
structural** export — node shapes, edges, labels, and dashing are mapped to mermaid syntax,
but per-element colors, fonts, and `svg_path`/`html` bodies are not preserved:

```python
print(flow.to_mermaid())
print(flow.to_mermaid(direction="LR"))   # default direction is "TB"
```

Example output:

```
%% figureflow export — structural only; per-element colors/fonts are not preserved
flowchart TB
    a([Start])
    b[Process]
    c([Done])
    a --> b
    b -.->|"result"| c
```

Shape mapping: rectangle `id[label]`, rounded `id(label)`, stadium `id([label])`, diamond
`id{label}`, hexagon `id{{label}}`, parallelogram `id[/label/]`, cylinder `id[(label)]`,
ellipse → rounded. Solid edges use `-->`, dashed/dotted edges use `-.->`. Hyphens in ids are
replaced with underscores so the output is valid mermaid.

**Verify:** paste the output into any mermaid renderer — it draws a flowchart with the right
shapes, edges, and labels.

> **Import is not supported.** figureflow exports to mermaid and JSON but does not parse
> mermaid (or other diagram grammars) back into a `Flow`. Use the JSON round-trip to restore
> a figureflow diagram.

## Custom components across a round-trip

If a node/edge uses a custom `type` ([Custom components](custom-components.md)), `to_json()`
records the type name and its `data`. On reload, the component re-binds **if the same type is
registered** in the new session; otherwise the element falls back to the built-in renderer.
Re-register your types before (or right after) loading.

## See also

- The runnable example: [`examples/03_serialization.py`](../../../examples/03_serialization.py).
- [Reference → Serialization](../reference.md#serialization-methods).
