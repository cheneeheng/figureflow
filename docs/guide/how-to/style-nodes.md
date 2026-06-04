# Style nodes

Give each node its shape, colors, border, and text. Every option is a keyword argument on
`Node` — set only the ones you want to change; the rest fall back to sensible defaults.

**Prerequisites:** figureflow installed and a notebook open ([Getting started](../getting-started.md)).

## Create a node

A node needs an `id` (unique within the flow). A label and position are optional but
usually wanted:

```python
from figureflow import Node, Shape

Node("step1", "Validate input", pos=(120, 40))
```

- `id` — string, must be unique across the flow.
- `label` — text shown in the node (default empty).
- `pos` — `(x, y)` top-left position on the canvas (default `(0, 0)`).

**Verify:** add it to a `Flow` and display — the node shows your label at the given spot.

## Pick a shape

Pass one of the eight built-in shapes via the `Shape` enum:

```python
Node("d", "Decision?", shape=Shape.diamond)
```

| `Shape` value | Looks like |
|---------------|------------|
| `Shape.rectangle` | Plain box (default) |
| `Shape.rounded` | Box with rounded corners |
| `Shape.stadium` | Pill / capsule |
| `Shape.ellipse` | Oval |
| `Shape.diamond` | Decision diamond |
| `Shape.parallelogram` | Slanted box |
| `Shape.hexagon` | Hexagon |
| `Shape.cylinder` | Database cylinder |

**Verify:** render all eight — run `python examples/quickstart.py` first to confirm the
names, then drop the same nodes into a notebook to see each shape.

## Set fill, border, and size

```python
Node(
    "n", "Styled",
    shape=Shape.rounded,
    fill="#e0f2fe",          # any CSS color
    border_color="#1d4ed8",
    border_width=2,          # pixels
    width=160,               # optional; otherwise auto-sizes to the label
    height=60,
)
```

- `fill` — background color (default `#ffffff`).
- `border_color` — outline color (default `#334155`).
- `border_width` — outline thickness in pixels (default `1.5`).
- `width` / `height` — explicit size in pixels. Leave them out and box shapes auto-size to
  the label (minimum 80×40); polygon and cylinder shapes default to roughly 130×56
  (diamond 130×90, cylinder 130×80).

**Verify:** the node shows your fill and a visibly thicker/colored border.

## Style the label text

The same five text fields work on nodes **and** edges — one vocabulary, one mental model:

```python
Node(
    "t", "Bold & blue",
    font_family="Georgia, serif",
    font_size=16,
    font_color="#1d4ed8",
    bold=True,
    italic=False,
    text_align="center",     # left | center | right
)
```

- `font_family` — CSS font stack (default `"Inter, system-ui, sans-serif"`).
- `font_size` — points (default `13`).
- `font_color` — text color (default `#0f172a`).
- `bold` / `italic` — booleans (default `False`).
- `text_align` — `left`, `center`, or `right` (default `center`).

**Verify:** the label renders in the chosen font, size, color, and weight.

## Escape hatch L1 — a custom shape from an SVG path

When none of the eight shapes fit, draw your own with an SVG path. It is filled and
stroked with the node's `fill` / `border_color` just like a built-in shape:

```python
Node(
    "heart", "Custom",
    svg_path="M 10,30 A 20,20,0,0,1,50,30 A 20,20,0,0,1,90,30 Q 90,60,50,90 Q 10,60,10,30 z",
    width=100, height=100,
    fill="#fce7f3", border_color="#db2777",
)
```

- `svg_path` — an SVG `<path>` `d` string. It is sized to `width`×`height` (default
  130×56), so set those to match your path's coordinate range.
- A set `svg_path` **takes precedence over `shape`**.

**Verify:** the node body is your path outline, filled with `fill`, with the label
centered over it.

## Escape hatch L2 — raw HTML in the node body

For richer static content, render an HTML string instead of a plain label:

```python
Node(
    "card",
    html="<b style='color:#1d4ed8'>Title</b><br/><small>subtitle</small>",
)
```

- `html` — a static HTML string rendered as the node body. It **replaces the label**.
- It is static markup only — no `<script>`, no React. For interactive components, use the
  [custom component escape hatch (L3)](custom-components.md).

> **Note:** `html` is inserted as raw markup. Only pass HTML you trust — treat it like any
> `innerHTML` assignment.

**Verify:** the node shows your formatted HTML instead of label text.

## Add a node after the flow is displayed

You don't have to define every node up front. Append one and it syncs to the live canvas:

```python
flow.add_node(Node("d", "Extra", pos=(200, 120)))
```

**Verify:** the new node appears on the already-rendered canvas without re-running the
cell that created `flow`.

## See also

- [Style edges](style-edges.md) — connect your nodes.
- [Reference → Node style fields](../reference.md#node) — every field in one table.
