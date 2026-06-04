# Style edges

Connect nodes and control how each connector looks — its path, arrowheads, line style, and
label. Like nodes, every option is a keyword argument set per-edge.

**Prerequisites:** a `Flow` with at least two nodes ([Style nodes](style-nodes.md)).

> **Edges are defined in Python, not drawn on the canvas.** figureflow does not support
> dragging between node handles to create a new edge. You add and style edges from Python;
> the canvas renders them. (You *can* delete an edge on the canvas — see
> [Edit on the canvas](edit-on-canvas.md).)

## Connect two nodes

An edge needs a `source` and a `target` — the `id`s of two existing nodes:

```python
from figureflow import Edge

Edge("a", "b")
```

By default the edge gets an arrowhead at the target end and an id of `"a->b"`. Pass `id=`
to set your own (useful when two edges share the same endpoints).

**Verify:** a line with an arrow connects node `a` to node `b`.

## Choose the path type

```python
Edge("a", "b", path_type="smoothstep")
```

| `path_type` | Connector |
|-------------|-----------|
| `bezier` | Smooth curve (default) |
| `straight` | Straight line |
| `step` | Right-angle steps |
| `smoothstep` | Right-angle steps with rounded corners |

`step` and `smoothstep` are the library's light edge routing. Obstacle-avoiding routing
(edges that bend around nodes) is out of scope.

**Verify:** the connector follows the chosen geometry.

## Set arrowheads

Control each end independently:

```python
Edge("a", "b", marker_start="arrow", marker_end="closed_arrow")
```

| Value | End decoration |
|-------|----------------|
| `none` | No arrowhead |
| `arrow` | Open arrowhead |
| `closed_arrow` | Filled (closed) arrowhead |

Defaults: `marker_end="arrow"`, `marker_start="none"`.

**Verify:** the arrowheads match — e.g. an open arrow at the source, a filled one at the target.

## Set line color, width, and dash

```python
Edge("a", "b", color="#dc2626", width=2.5, dash="dashed")
```

- `color` — line color (default `#334155`).
- `width` — line thickness in pixels (default `1.5`).
- `dash` — `solid` (default), `dashed`, or `dotted`.

**Verify:** the line shows the color, thickness, and dash pattern you set.

## Add and style a label

Edge labels use the **same five text fields as node labels** — same names, same defaults:

```python
Edge(
    "a", "b",
    label="success",
    font_size=12, font_color="#15803d", bold=True,
    label_bg="#dcfce7",      # optional background chip behind the label
)
```

- `label` — text shown along the edge (default empty → no label).
- `font_family`, `font_size`, `font_color`, `bold`, `italic` — style the label text.
- `label_bg` — a background color drawn behind the label; omit it for no background.

**Verify:** the label appears mid-edge in the chosen style, on a colored chip if you set
`label_bg`.

## Add an edge after the flow is displayed

```python
flow.add_edge(Edge("c", "d", label="late link"))
```

**Verify:** the new edge appears on the live canvas immediately.

## See also

- [Style nodes](style-nodes.md) — the nodes your edges connect.
- [Reference → Edge style fields](../reference.md#edge) — every field in one table.
