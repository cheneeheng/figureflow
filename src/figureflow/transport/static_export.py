"""Static export adapter — frozen offline snapshot (one-way).

The cheapest consumer of the seam: state is baked in at write time, so there is
no live pipe. ``Flow.to_html()`` reuses the v1 ``serialize.to_json`` envelope as a
JSON data island, inlines the vendored bundle (``widget.js`` + ``widget.css``) into
the shared ``static/host.html`` template, and the browser-side static JS adapter
captures client edits in-memory for a one-way "download JSON" escape (SKELETON_V2
§04, ITER_V2_02).

This module also owns :func:`render_host_page`, the template filler the server
adapter (ITER_V2_03) reuses so static and server share one page shell.
"""

from __future__ import annotations

import html
import pathlib
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from figureflow.transport.base import ChangeHandler, Transport

if TYPE_CHECKING:
    from figureflow import Flow

_STATIC = pathlib.Path(__file__).resolve().parent.parent / "static"


def _escape_island(json_text: str) -> str:
    """Make JSON safe inside a ``<script type="application/json">`` data island.

    The HTML parser ends the element at the first ``</`` of a ``</script>``; the
    sequence ``<\\/`` is still valid JSON (``\\/`` is an allowed escape), so the
    island parses unchanged while never closing the tag early.
    """
    return json_text.replace("</", "<\\/")


def _escape_inline_js(js_text: str) -> str:
    """Make a bundle safe to inline in a ``<script>`` element.

    ``</script`` can only occur inside a string or regex literal in the minified
    bundle; ``<\\/script`` is equivalent there, so the script runs identically
    while the tag never closes early.
    """
    return js_text.replace("</script", "<\\/script")


def render_host_page(
    *,
    title: str,
    head: str,
    island: str,
    bundle: str,
    bootstrap: str,
) -> str:
    """Fill the shared ``static/host.html`` template (static + server).

    Args:
        title: Page ``<title>`` text (already escaped).
        head: Head assets markup — inlined ``<style>`` (static) or a ``<link>``
            (server).
        island: The state markup — a JSON data island (static) or empty (server,
            which fetches ``/state``).
        bundle: The bundle markup — an inline ``<script type="module">`` (static)
            or a ``<script src>`` (server).
        bootstrap: The ``<script type="module">`` that constructs the adapter and
            mounts the renderer.

    Returns:
        The assembled HTML document.
    """
    template = (_STATIC / "host.html").read_text(encoding="utf-8")
    return (
        template.replace("{{TITLE}}", title)
        .replace("{{HEAD}}", head)
        .replace("{{ISLAND}}", island)
        .replace("{{BUNDLE}}", bundle)
        .replace("{{BOOTSTRAP}}", bootstrap)
    )


_STATIC_BOOTSTRAP = """
const island = JSON.parse(
  document.getElementById("figureflow-state").textContent
);
const transport = globalThis.figureflow.createStaticTransport(island);
globalThis.figureflow.mount(
  document.getElementById("figureflow-root"),
  transport,
  { height: island.height }
);
""".strip()


class StaticExportAdapter(Transport):
    """Renders a ``Flow`` to a self-contained, client-side-interactive page."""

    def __init__(self) -> None:
        self._flow: Optional["Flow"] = None

    def bind(self, flow: "Flow") -> None:
        """Attach to the ``Flow`` whose snapshot is frozen at render time."""
        self._flow = flow

    def send_state(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        meta: Dict[str, Any],
    ) -> None:
        """No-op — a static snapshot has no live down-channel."""
        return None

    def on_change(self, handler: ChangeHandler) -> None:
        """No-op — a static snapshot has no upstream pipe."""
        return None

    def emit(self, event: str, payload: Any) -> None:
        """No-op — no Python is reachable from a ``file://`` snapshot."""
        return None

    def render_html(self, flow: "Flow", *, title: Optional[str] = None) -> str:
        """Produce the self-contained HTML snapshot string.

        Reads the live ``Flow`` once and freezes it: serializes via
        ``serialize.to_json`` into a JSON data island, inlines the prebuilt
        ``widget.css`` and ``widget.js``, and emits the static bootstrap. Pure
        and side-effect-free (the optional file write lives in ``Flow.to_html``).

        Args:
            flow: The diagram to freeze.
            title: Optional page ``<title>``; defaults to ``"figureflow"``.

        Returns:
            The self-contained HTML string.
        """
        from figureflow.serialize import to_json

        island_json = _escape_island(to_json(flow))
        css = (_STATIC / "widget.css").read_text(encoding="utf-8")
        js = _escape_inline_js((_STATIC / "widget.js").read_text(encoding="utf-8"))

        return render_host_page(
            title=html.escape(title or "figureflow"),
            head=f"<style>{css}</style>",
            island=(
                '<script type="application/json" id="figureflow-state">'
                f"{island_json}</script>"
            ),
            bundle=f'<script type="module">{js}</script>',
            bootstrap=f'<script type="module">{_STATIC_BOOTSTRAP}</script>',
        )

    # start/stop inherit the base no-ops (no live pipe).
