# Group and lay out

Bundle related nodes into a labeled container, and let figureflow arrange the graph for you
with the dagre layout engine.

**Prerequisites:** a `Flow` with several nodes ([Style nodes](style-nodes.md)).

## Group nodes into a container

`group()` wraps existing nodes in a parent container node and returns the new group's id:

```python
group_id = flow.group(["a", "b", "c"], label="ETL Pipeline")
print(group_id)   # "group-0"
```

What happens:

- A container node (`type="group"`) is added behind the members, sized to a bounding box
  around them plus padding, with your `label` shown in its corner.
- Each member becomes a **child** of the group: it is constrained to the parent's bounds and
  moves with the parent when you drag the container.
- Member coordinates become parent-relative (handled for you).

Group ids increment: the first group is `group-0`, the next `group-1`, and so on.

> **Errors:** `group([])` — or a list whose ids don't match any node — raises `ValueError`.
> Pass ids that exist in the flow.

**Verify:** the named container renders behind its members; dragging the container moves all
of them together, and a child cannot be dragged outside it.

## Auto-arrange with `layout()`

`layout()` computes positions with dagre and writes them back to the canvas:

```python
flow.layout()                    # top-to-bottom (default)
flow.layout(direction="LR")      # left-to-right
```

- `direction` — `"TB"` (top→bottom, default), `"BT"` (bottom→top), `"LR"` (left→right),
  or `"RL"` (right→left). Any other value raises `ValueError`.
- `algo` — only `"dagre"` is supported; passing anything else raises `ValueError`.
- The layout result is applied as a single canvas edit, so **one `layout()` call is one
  undo step** ([Edit on the canvas → Undo and redo](edit-on-canvas.md#undo-and-redo)).

After the call, `flow.positions()` reflects the arranged coordinates — no extra step needed.

**Verify:** run `flow.layout(direction="LR")` on a connected graph; nodes spread left-to-right
in dependency order, and `flow.positions()` shows the new coordinates.

## Group, then lay out

The two compose. A common pattern is to group a sub-pipeline, then auto-arrange the whole
diagram:

```python
flow.group(["fetch", "parse", "validate"], label="Ingest")
flow.layout(direction="LR")
```

Top-level nodes and groups are arranged together; each group's children are arranged within
its box. Nesting is one level deep for the MVP.

**Verify:** the grouped nodes stay inside their container while the overall graph is arranged
left-to-right.

## See also

- The runnable example: [`examples/grouping_layout.py`](../../../examples/grouping_layout.py).
- [Save and load](save-and-load.md) — persist the arranged result (positions are saved, so a
  reload needs no re-layout).
