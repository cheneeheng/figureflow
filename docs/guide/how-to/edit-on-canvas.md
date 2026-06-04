# Edit on the canvas

Once a `Flow` is displayed, the canvas is interactive. This guide covers moving, selecting,
copying, deleting, and undoing — and how to read the result back into Python.

**Prerequisites:** a displayed `Flow` ([Getting started](../getting-started.md)).

## Navigate the canvas

| Action | How |
|--------|-----|
| Pan (move the view) | Drag with the **middle** or **right** mouse button |
| Zoom | Scroll, or use the zoom controls (bottom-left) |
| Overview | The minimap (bottom-right) shows the whole graph and the current viewport |

The left mouse button is reserved for selecting (below), so panning uses the middle/right
button.

**Verify:** middle-drag moves the whole diagram; the minimap viewport rectangle moves with it.

## Move nodes

Drag any node with the left mouse button. The position is committed back to Python when you
**release** the drag (not continuously while dragging).

**Verify:** drop a node, then run `flow.positions()` in a new cell — its coordinates reflect
the new spot. See [Read positions back](#read-positions-back-into-python).

## Select nodes

| Goal | How |
|------|-----|
| Select one node | Left-click it |
| Add to / remove from the selection | **Shift**-click |
| Box-select several | Left-drag a rectangle across empty canvas |

**Verify:** selected nodes show a highlighted outline.

## Copy and paste (within the canvas)

1. Select one or more nodes.
2. Press **Ctrl+C** (macOS: **Cmd+C**) to copy.
3. Press **Ctrl+V** (macOS: **Cmd+V**) to paste.

The clones keep all styling. They are offset by `(+24, +24)` from the originals, become the
new selection, and get fresh ids of the form `{originalId}-copy-{n}` (for example,
`step1-copy-1`). An edge is copied too **only when both of its endpoints are in the
selection**; its endpoints are remapped to the pasted copies.

> This is a within-canvas clipboard held in memory. It does not use your operating system
> clipboard, so you cannot paste into another app or another notebook.

**Verify:** paste a selected node and inspect `flow.nodes` — a node whose `id` ends in
`-copy-1` is present.

## Delete elements

Select one or more elements and press **Backspace** (or **Delete**). Removals are committed
back to Python.

**Verify:** the element disappears and is gone from `flow.nodes` / `flow.edges`.

## Undo and redo

Canvas edits — drags, deletes, pastes, and `layout()` results — are tracked in a history
(the most recent ~50 steps).

| Action | Keyboard | From Python |
|--------|----------|-------------|
| Undo | **Ctrl/Cmd+Z** | `flow.undo()` |
| Redo | **Ctrl/Cmd+Shift+Z** or **Ctrl/Cmd+Y** | `flow.redo()` |

Undo/redo step the **same** history whether you use the keyboard or the Python calls. When
the stack end is reached, the call is a no-op.

> **Boundary:** history covers *canvas* edits. Programmatic Python edits (`add_node`,
> `add_edge`, `group`) are authoritative and not individually undoable, and loading a
> diagram with `load_json()` clears the history. See [Save and load](save-and-load.md).

**Verify:** drag a node, press **Ctrl+Z** — it returns to its previous spot; **Ctrl+Shift+Z**
re-applies the move.

## Read positions back into Python

`positions()` returns the current coordinates of every node as last synced from the canvas:

```python
flow.positions()
# {'a': (40.0, -12.0), 'b': (0.0, 120.0), 'c': (0.0, 240.0)}
```

You can also iterate `flow.nodes` and `flow.edges` directly — they are the synced channel
dicts (including any pasted copies).

**Verify:** the returned coordinates match where the nodes sit on the canvas.

## See also

- [Group and lay out](group-and-layout.md) — bundle nodes and auto-arrange.
- [Save and load](save-and-load.md) — persist the arranged diagram.
