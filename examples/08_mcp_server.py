"""08_mcp_server.py — let an agent and a human co-edit one diagram over MCP (v3).

The ``figureflow-mcp`` stdio server (behind the ``figureflow[mcp]`` extra) wraps
``serve()``: an agent calls the tools below to build/replace the diagram while the human
drags nodes in a live browser tab, and ``get_diagram`` reads the human's edits back. The
server is a *client* of the public surface only — core ``figureflow`` stays
dependency-free.

This script does not run the stdio server (an MCP client drives that over stdin/stdout);
it prints how to launch it and the client config you drop into an agent host:

    python examples/08_mcp_server.py
"""
from __future__ import annotations

import importlib.util

# The five tools the server exposes, in the order an agent typically uses them.
TOOLS = {
    "create_diagram":  "Build from JSON or mermaid and serve a browser tab for the human.",
    "get_diagram":     "Read the canonical state back, including the human's drag edits.",
    "replace_diagram": "Swap the live diagram wholesale (the running server is untouched).",
    "add_elements":    "Add nodes/edges incrementally; unplaced nodes auto-place on render.",
    "close_diagram":   "Stop the server and end the session.",
}

# Client config (e.g. Claude Desktop's claude_desktop_config.json).
CLIENT_CONFIG = """{
  "mcpServers": {
    "figureflow": { "command": "figureflow-mcp" }
  }
}"""


if __name__ == "__main__":
    has_mcp = importlib.util.find_spec("mcp") is not None
    print("MCP extra installed:", "yes" if has_mcp else "no — run: pip install 'figureflow[mcp]'")

    print("\nLaunch the stdio server (an MCP client spawns this for you):\n    figureflow-mcp")

    print("\nTools exposed to the agent:")
    for name, doc in TOOLS.items():
        print(f"  {name:<16} {doc}")

    print("\nWire it into an agent host (e.g. Claude Desktop config):\n")
    print(CLIENT_CONFIG)

    print(
        "\nTypical loop: create_diagram(source=...) -> human drags nodes -> "
        "get_diagram() -> add_elements(...)/replace_diagram(...) -> close_diagram()."
    )
