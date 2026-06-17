"""MCP adapter — the agent door (ITER_V3_03, MVP terminator).

A FastMCP server exposing create/get/replace/add/close tools over **one live
diagram**. It is *not* a fifth transport — it is a **client of the existing
surface**: tools call ``from_json`` / ``from_mermaid`` / ``serve()`` / ``to_json``
/ ``to_mermaid`` and nothing deeper. The agent's tool calls and the human's
browser edits funnel through the same v2 sync-core; concurrency falls out of
ITER_V2_04 with no new sync logic.

This module is imported only by the ``figureflow-mcp`` console script — never by
``figureflow`` core, which stays dependency-free. The ``mcp`` SDK is imported
lazily in :func:`main`, with a clear install message when the extra is missing.

Gotcha — stdio servers must not touch stdout. The MCP stdio transport *is*
stdout; any stray ``print`` corrupts the protocol. All logging routes to stderr
and ``serve()`` is always called with ``quiet=True``.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from figureflow import Flow

_NO_DIAGRAM: Dict[str, str] = {"error": "no diagram; call create_diagram first"}


class _Session:
    """The single canonical diagram per server process (one canvas, pinned)."""

    def __init__(self) -> None:
        self.flow: "Flow | None" = None


def _warnings_of(flow: "Flow") -> List[str]:
    return list(getattr(flow, "_import_warnings", []))


def _build_server(fast_mcp: Any) -> Any:
    """Construct the FastMCP server and register the diagram tools.

    Args:
        fast_mcp: The ``FastMCP`` class (passed in so the ``mcp`` import stays
            lazy in :func:`main`).

    Returns:
        A configured FastMCP server ready to ``run()``.
    """
    server = fast_mcp("figureflow")
    session = _Session()

    @server.tool()
    def create_diagram(
        source: str,
        format: str = "json",
        open_browser: bool = True,
    ) -> Dict[str, Any]:
        """Build a diagram and serve it in a browser tab for the human.

        Args:
            source: A figureflow/1 JSON envelope, or mermaid flowchart text.
            format: ``"json"`` (default) or ``"mermaid"``.
            open_browser: Open the served URL in the human's browser.

        Returns:
            ``{url, warnings}`` — the URL is valid only while this process
            lives. On a validation/parse fault, ``{error}`` instead.
        """
        from figureflow import Flow, FlowValidationError, MermaidParseError

        try:
            if format == "mermaid":
                flow = Flow.from_mermaid(source)
            else:
                flow = Flow.from_json(source)
        except (FlowValidationError, MermaidParseError, json.JSONDecodeError) as exc:
            return {"error": str(exc)}

        if session.flow is not None:
            session.flow.stop()  # re-serve replaces the session (ITER_V2_03)
        session.flow = flow
        url = flow.serve(open_browser=open_browser, quiet=True)
        return {"url": url, "warnings": _warnings_of(flow)}

    @server.tool()
    def get_diagram() -> Dict[str, Any]:
        """Return the current canonical state, including the human's edits.

        Returns:
            ``{json, mermaid}`` — the lossless JSON and a mermaid copy the agent
            can reason in. ``{error}`` if no diagram exists yet.
        """
        if session.flow is None:
            return dict(_NO_DIAGRAM)
        from figureflow.serialize import to_json, to_mermaid

        return {
            "json": to_json(session.flow),
            "mermaid": to_mermaid(session.flow),
        }

    @server.tool()
    def replace_diagram(source: str, format: str = "json") -> Dict[str, Any]:
        """Replace the live diagram wholesale (the running server is untouched).

        Args:
            source: A figureflow/1 JSON envelope, or mermaid flowchart text.
            format: ``"json"`` (default) or ``"mermaid"``.

        Returns:
            ``{warnings}``, or ``{error}`` on a fault / before ``create_diagram``.
        """
        if session.flow is None:
            return dict(_NO_DIAGRAM)
        from figureflow import Flow, FlowValidationError, MermaidParseError

        try:
            if format == "mermaid":
                tmp = Flow.from_mermaid(source)
                warnings = _warnings_of(tmp)
                session.flow.load_json(tmp.to_json())
                warnings += _warnings_of(session.flow)
            else:
                session.flow.load_json(source)
                warnings = _warnings_of(session.flow)
        except (FlowValidationError, MermaidParseError, json.JSONDecodeError) as exc:
            return {"error": str(exc)}
        return {"warnings": warnings}

    @server.tool()
    def add_elements(
        nodes_json: str = "[]",
        edges_json: str = "[]",
    ) -> Dict[str, Any]:
        """Add nodes/edges incrementally; unplaced nodes auto-place on render.

        Args:
            nodes_json: JSON array of node objects (channel form).
            edges_json: JSON array of edge objects.

        Returns:
            ``{warnings}``, or ``{error}`` on a fault / before ``create_diagram``.
        """
        if session.flow is None:
            return dict(_NO_DIAGRAM)
        from figureflow import FlowValidationError
        from figureflow.serialize import validate

        try:
            new_nodes = json.loads(nodes_json)
            new_edges = json.loads(edges_json)
        except json.JSONDecodeError as exc:
            return {"error": f"$: nodes_json/edges_json is not valid JSON. {exc}"}

        combined = {
            "schema": "figureflow/1",
            "layout_direction": session.flow.layout_direction,
            "nodes": list(session.flow.nodes) + list(new_nodes),
            "edges": list(session.flow.edges) + list(new_edges),
        }
        try:
            clean, warnings = validate(combined)
        except FlowValidationError as exc:
            return {"error": str(exc)}
        session.flow.nodes = clean["nodes"]
        session.flow.edges = clean["edges"]
        return {"warnings": warnings}

    @server.tool()
    def close_diagram() -> Dict[str, Any]:
        """Stop the served browser session and drop the diagram."""
        if session.flow is not None:
            session.flow.stop()
            session.flow = None
        return {}

    return server


def main() -> None:
    """Console-script entry point for ``figureflow-mcp`` (stdio transport).

    Routes all logging to stderr to keep the stdio protocol clean, and prints a
    clear install hint if the optional ``mcp`` extra is missing.
    """
    import logging
    import sys

    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        print(
            "figureflow-mcp requires the optional 'mcp' extra. Install with:\n"
            "    pip install 'figureflow[mcp]'",
            file=sys.stderr,
        )
        raise SystemExit(1)

    server = _build_server(FastMCP)
    server.run()


if __name__ == "__main__":  # pragma: no cover - console-script entry guard
    main()
