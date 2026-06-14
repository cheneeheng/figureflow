# MCP server — operator runbook

How to install, register, run, and recover the figureflow **MCP server**: a small process that
lets an AI agent (Claude Code, Claude Desktop, Cursor, or any MCP client) author and edit a
diagram while a human watches and edits the same canvas in a browser.

This page is for whoever **operates** the server. If you just want to import or author diagrams
from Python, see the [import how-to](../how-to/import-diagrams.md) — you do not need this.

## System overview

```
agent (MCP client) ──stdio──▶ figureflow-mcp process
                                 │  tools → Flow API
                                 ▼
                               Flow ──serve()──▶ browser canvas ◀── human
```

- The MCP client **spawns** `figureflow-mcp` as a subprocess and talks to it over **stdio**
  (stdin/stdout). There is no network port to manage for the MCP channel itself.
- The server holds **one** canonical `Flow`. The agent mutates it through tools; the human edits
  it in a browser tab opened by figureflow's built-in [`serve()`](../how-to/display-anywhere.md)
  (a localhost-only stdlib HTTP server on an OS-assigned port). Both sides see each other's edits.
- The server is **stateless across restarts** — there is no database. Closing the process drops
  the diagram and invalidates the browser URL.

## Prerequisites

- Python ≥ 3.9 and `pip`, in the environment the MCP client will launch.
- The optional `mcp` extra (next section). The core `figureflow` install does **not** pull in
  `mcp` — the server is opt-in.
- A desktop browser on the same machine (the human's canvas opens locally).

## Installation

1. Install figureflow with the MCP extra:
   ```bash
   pip install 'figureflow[mcp]'
   ```
2. Confirm the console script is on `PATH`:
   ```bash
   which figureflow-mcp
   ```
   Expected: a path to the `figureflow-mcp` executable.

**Verify the extra resolved.** Without arguments the server waits for an MCP client on stdin, so
test the *import path* instead:

```bash
python -c "import mcp; from figureflow import mcp_server; print('mcp extra OK')"
```

Expected output:
```
mcp extra OK
```

**If it fails:** `ModuleNotFoundError: No module named 'mcp'` means the extra is not installed in
this interpreter — re-run the install for the *same* Python the client uses
(`python -c "import sys; print(sys.executable)"`).

## Configuration — register with an MCP client

The server takes no flags or environment variables; configuration is entirely on the **client**
side, where you tell it how to spawn `figureflow-mcp`.

**Claude Code** — register the server by command:
```bash
claude mcp add figureflow figureflow-mcp
```

**Claude Desktop / Cursor / other JSON-config clients** — add an entry under `mcpServers`:
```json
{
  "mcpServers": {
    "figureflow": {
      "command": "figureflow-mcp"
    }
  }
}
```
Use the absolute path from `which figureflow-mcp` for `command` if the client does not inherit
your shell `PATH`. Restart the client after editing its config.

> **Tip — pin the interpreter.** If you use virtualenvs, set `command` to the venv's
> `figureflow-mcp` (e.g. `/path/to/venv/bin/figureflow-mcp`) so the client launches the
> environment where you installed the extra.

**Verify:** the client lists `figureflow` among its connected MCP servers, and its tools
(`create_diagram`, `get_diagram`, `replace_diagram`, `add_elements`, `close_diagram`) are
available to the agent.

## Routine operations

You normally do not start or stop the server by hand — the MCP client spawns it on demand and
terminates it when the client exits. The agent drives it through five tools:

| Tool | Signature | Effect |
|------|-----------|--------|
| `create_diagram` | `(source, format="json"\|"mermaid", open_browser=True) -> {url, warnings}` | Build a diagram from JSON/mermaid and open the human's browser canvas. Returns the URL and any import warnings. Calling it again **replaces** the session (stops the old server first). |
| `get_diagram` | `() -> {json, mermaid}` | Current canonical state, **including the human's edits** (e.g. dragged positions). |
| `replace_diagram` | `(source, format="json"\|"mermaid") -> {warnings}` | Reload the live diagram wholesale; the running browser updates in place. |
| `add_elements` | `(nodes_json="[]", edges_json="[]") -> {warnings}` | Add nodes/edges incrementally; unplaced nodes auto-place on the next render. |
| `close_diagram` | `() -> {}` | Stop the browser session and drop the diagram. |

To start a session by hand for testing, drive it from the agent with `create_diagram` (no manual
command needed). To exercise the whole loop, see the **Verify the full loop** check below.

## Monitoring

- **Logs go to stderr.** The stdio transport *is* stdout, so the server routes all logging to
  **stderr** (where the MCP client surfaces it). To watch logs, open the client's MCP/server log
  view.
- **Healthy signs:** `create_diagram` returns a `http://127.0.0.1:<port>` URL; the browser tab
  renders the diagram laid out; `get_diagram` reflects positions after the human drags a node.
- **The URL is process-scoped.** It is valid only while the `figureflow-mcp` process lives. If
  the client restarts the server, the agent must `create_diagram` again to get a fresh URL.

**Health check (the full loop), runnable without an MCP client** — drives the tool layer directly:
```bash
python - <<'PY'
from figureflow import mcp_server

class FakeMCP:
    def __init__(self, name): self.tools = {}
    def tool(self):
        def d(fn): self.tools[fn.__name__] = fn; return fn
        return d

srv = mcp_server._build_server(FakeMCP)
t = srv.tools
print(t["create_diagram"]('flowchart TD\n a-->b', format="mermaid", open_browser=False))
print(t["get_diagram"]().keys())
print(t["close_diagram"]())
PY
```
Expected: a `{'url': 'http://127.0.0.1:...', 'warnings': [...]}` line, then `dict_keys(['json',
'mermaid'])`, then `{}`.

## Incident procedures

### `figureflow-mcp` exits immediately with an install message

**Detection:** the client reports the server failed to start; stderr shows:
```
figureflow-mcp requires the optional 'mcp' extra. Install with:
    pip install 'figureflow[mcp]'
```
**Remediation:** the `mcp` SDK is missing from the interpreter the client launched. Install the
extra into *that* environment (see [Installation](#installation)) and point the client's
`command` at its `figureflow-mcp`. **Verify** with the import check above.

### The client cannot connect / the protocol looks corrupted

**Cause:** something wrote to **stdout** outside the MCP framing (a stray `print`, a library
banner). The figureflow server keeps stdout clean and calls `serve(quiet=True)` precisely to
avoid this. If you have added custom code around the server, route all of its output to stderr.
**Verify:** capture the process stdout during a session — it must contain only MCP protocol
frames, no plain-text lines.

### The agent's tools return `{"error": ...}` instead of acting

This is **by design**, not a crash. Invalid input (bad JSON, an unknown shape, a duplicate id, a
dangling edge, or any pre-`create_diagram` call) is returned as a tool result so the agent can
read the message and retry — see the collected, one-line error format in the
[import how-to](../how-to/import-diagrams.md#fix-a-bad-diagram-in-one-pass). No operator action
is needed; the agent repairs and re-calls.

### The browser tab is blank or the URL is dead

**Cause:** the `figureflow-mcp` process was restarted or closed, which stops `serve()` and
invalidates the URL. **Remediation:** have the agent call `create_diagram` again; it opens a new
canvas. There is nothing to restore — the diagram lives only in the running process.

## Rollback / recovery

There is no persistent state to roll back. To recover a diagram across a restart, capture it
**before** shutdown with `get_diagram` (its `json` field is lossless) and feed that JSON back to
`create_diagram` in the next session.

## Escalation

The MCP server is a thin client of the core library — it calls `from_json`, `from_mermaid`,
`serve()`, `to_json`, and `to_mermaid` and nothing deeper. If a failure is not covered above:

- Reproduce it against the core API directly (`Flow.from_mermaid(...)`, `flow.serve()`) to
  isolate whether the bug is in import, in `serve()`, or in the MCP layer.
- Capture the stderr log and the offending `source` string.
- File an issue at the project repository with that reproduction.

## See also

- [Import a diagram](../how-to/import-diagrams.md) — the import/validation behavior the tools wrap.
- [Display anywhere](../how-to/display-anywhere.md) — `serve()`, the browser transport the server uses.
- [Reference → Serialization and import](../reference.md#serialization-and-import-methods).
