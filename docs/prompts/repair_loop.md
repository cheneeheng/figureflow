# Repair-loop transcript

figureflow collects every problem into one error. Read all the lines, fix them
together, re-emit once. This is the loop that makes coordinate-free authoring
robust.

## Round 1 — broken input

The agent emits JSON with three faults: an invalid shape, a duplicate id, and an
edge pointing at a node that does not exist.

```json
{
  "schema": "figureflow/1",
  "nodes": [
    {"id": "a", "data": {"label": "Start", "shape": "circle"}},
    {"id": "a", "data": {"label": "Work", "shape": "rectangle"}}
  ],
  "edges": [{"source": "a", "target": "end"}]
}
```

## The error (returned as a tool result, one problem per line)

```
nodes[0].shape: 'circle' is not a valid shape. Use one of: rectangle, rounded, stadium, ellipse, diamond, parallelogram, hexagon, cylinder.
nodes[1].id: duplicate node id 'a'. Node ids must be unique.
edges[0].target: target 'end' names no node. Known node ids: a.
```

## Round 2 — every fault fixed at once

The agent renames the duplicate, picks a valid shape (`ellipse`, the closest
intent to "circle"), and adds the missing `end` node.

```json
{
  "schema": "figureflow/1",
  "nodes": [
    {"id": "start", "data": {"label": "Start", "shape": "ellipse"}},
    {"id": "work", "data": {"label": "Work", "shape": "rectangle"}},
    {"id": "end", "data": {"label": "End", "shape": "stadium"}}
  ],
  "edges": [
    {"source": "start", "target": "work"},
    {"source": "work", "target": "end"}
  ]
}
```

This validates cleanly. The diagram renders laid-out — no coordinates were ever
emitted.
