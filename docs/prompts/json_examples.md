# JSON emission examples

Emit a `figureflow/1` envelope. Positions are omitted — the renderer places nodes.

## Example 1 — a CI/CD pipeline (left-to-right)

**Prompt:** "Diagram a CI pipeline: commit triggers build, then test, then deploy;
if test fails, notify."

```json
{
  "schema": "figureflow/1",
  "layout_direction": "LR",
  "nodes": [
    {"id": "commit", "data": {"label": "Commit", "shape": "stadium"}},
    {"id": "build", "data": {"label": "Build", "shape": "rectangle"}},
    {"id": "test", "data": {"label": "Test", "shape": "diamond"}},
    {"id": "deploy", "data": {"label": "Deploy", "shape": "rectangle"}},
    {"id": "notify", "data": {"label": "Notify team", "shape": "rounded"}}
  ],
  "edges": [
    {"source": "commit", "target": "build"},
    {"source": "build", "target": "test"},
    {"source": "test", "target": "deploy", "label": "pass"},
    {"source": "test", "target": "notify", "label": "fail"}
  ]
}
```

## Example 2 — a state machine with per-element styling (top-to-bottom)

**Prompt:** "Show a request lifecycle: pending → active → done or cancelled.
Color the terminal states."

```json
{
  "schema": "figureflow/1",
  "layout_direction": "TB",
  "nodes": [
    {"id": "pending", "data": {"label": "Pending", "shape": "stadium"}},
    {"id": "active", "data": {"label": "Active", "shape": "rectangle"}},
    {"id": "done", "data": {"label": "Done", "shape": "stadium", "fill": "#e6f4ea", "borderColor": "#34a853"}},
    {"id": "cancelled", "data": {"label": "Cancelled", "shape": "stadium", "fill": "#fce8e6", "borderColor": "#ea4335"}}
  ],
  "edges": [
    {"source": "pending", "target": "active", "label": "start"},
    {"source": "active", "target": "done", "label": "complete"},
    {"source": "active", "target": "cancelled", "label": "cancel"}
  ]
}
```
