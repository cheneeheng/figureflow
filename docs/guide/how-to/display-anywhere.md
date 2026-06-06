# Display anywhere

Render the same `Flow` in a notebook, as a frozen offline file, or as a live browser tab.
One renderer, three interchangeable front doors — the way you *build* a diagram never changes.

**Prerequisites:** a `Flow` to display ([Getting started](../getting-started.md)).

## The three doors

| Method | Where it renders | Round-trip back to Python |
|--------|------------------|---------------------------|
| `display()` | Inside a notebook cell | Live (kernel comm) |
| `serve()` | A plain browser tab | Live (localhost server) |
| `to_html()` | A self-contained `.html` file | Manual ("Download JSON") |

## 1. Notebook — `display()`

The default. Ending a cell with a bare `flow` already renders it; `display()` is the explicit
form and returns the widget:

```python
flow.display()   # or just: flow
```

Drag a node and `flow.positions()` reflects it; `flow.add_node(...)`, `flow.layout()`, and
`flow.undo()` all drive the live canvas.

## 2. Live browser tab — `serve()`

Start a small server and open the diagram in an ordinary browser, with full two-way sync to
your running Python process:

```python
url = flow.serve()          # prints + returns the URL, opens the browser
# ... drag in the browser → flow.positions() updates;
# ... flow.add_node(...) / flow.layout() push to the browser live ...
flow.stop()                 # shut the server down
```

- Binds **`127.0.0.1` only** — never exposed off your machine — and adds **no dependencies**
  (it uses the Python standard library: Server-Sent Events down, `POST` up).
- `open_browser=False` skips launching a tab; `block=True` keeps the process alive for
  `python script.py` use (Ctrl+C stops it). Calling `serve()` again stops the previous server
  first.
- Single-user and localhost by design — see [Out of scope](#out-of-scope).

## 3. Offline snapshot — `to_html()`

Freeze the diagram into one self-contained HTML file. It is fully interactive client-side
(pan, zoom, drag, minimap) and opens straight from disk with **no network** — the front-end
bundle is inlined:

```python
html = flow.to_html("diagram.html", title="My diagram")
# Open diagram.html in any browser, even offline.
```

There is no Python behind a file, so edits do not sync back automatically. The page carries a
**Download JSON** button that exports your rearranged layout; reimport it with `from_json`:

```python
from figureflow import Flow
restored = Flow.from_json(open("figureflow.json").read())
```

That downloaded JSON is the same lossless envelope as [`to_json()`](save-and-load.md), so the
round-trip is exact.

`to_html()` with no `path` just returns the string — handy in a notebook:

```python
from IPython.display import HTML
HTML(flow.to_html())
```

## Out of scope

- **No multi-client sessions.** `serve()` is single-user; two browsers editing one server is
  not supported.
- **No live round-trip from a static file.** A `file://` snapshot has no Python behind it; its
  only path back is the manual Download JSON → `from_json`.
- **No remote/public serving.** `serve()` is localhost-only by construction; it is not a
  hardened web server.
