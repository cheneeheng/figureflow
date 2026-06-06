"""figureflow — interactive flow diagram widget for Python.

Public surface: ``Shape``, ``Node``, ``Edge`` and ``Flow``. The full MVP is
implemented — per-element node/edge styling (plus L1 ``svg_path`` / L2 ``html``),
canvas editing (multi-select, copy/paste, undo/redo), grouping, dagre auto-layout,
JSON + mermaid export, and the L3 custom-component escape hatch
(``register_node_type`` / ``register_edge_type`` / ``on``).
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

import anywidget
import traitlets

if TYPE_CHECKING:
    from figureflow.transport.base import Transport

__all__ = ["Shape", "Node", "Edge", "Flow"]

_STATIC = pathlib.Path(__file__).parent / "static"


class Shape(str, Enum):
    """The 8 built-in node shapes."""

    rectangle = "rectangle"
    rounded = "rounded"
    stadium = "stadium"
    ellipse = "ellipse"
    diamond = "diamond"
    parallelogram = "parallelogram"
    hexagon = "hexagon"
    cylinder = "cylinder"


# Internal global baseline: a single module-level dict of default field values
# that fresh elements start from. NOT surfaced in any signature; not a theme,
# not user-settable. New element -> baseline values -> per-element overrides.
# The five text-style fields mean the same thing on Node and Edge labels.
_BASELINE: Dict[str, Any] = {
    # shared text-style vocabulary (same names/defaults on Node and Edge labels)
    "font_family": "Inter, system-ui, sans-serif",
    "font_size": 13,
    "font_color": "#0f172a",
    "bold": False,
    "italic": False,
    # node style
    "shape": Shape.rectangle,
    "fill": "#ffffff",
    "border_color": "#334155",
    "border_width": 1.5,
    "text_align": "center",
    # edge style
    "path_type": "bezier",
    "marker_start": "none",
    "marker_end": "arrow",
    "edge_color": "#334155",
    "edge_width": 1.5,
    "dash": "solid",
}


@dataclass
class Node:
    """A styled node. ``to_dict()`` serializes it for the sync channel.

    The full target field list is present; the skeleton ``to_dict`` only emits
    the subset the front-end honors today. ``html``/``svg_path``/``type`` are
    escape-hatch fields and ``parent_id``/``extent`` support grouping
    (ITER_04) — all null by default.
    """

    id: str
    label: str = ""
    pos: Tuple[float, float] = (0.0, 0.0)
    shape: Shape = field(default_factory=lambda: _BASELINE["shape"])
    fill: str = field(default_factory=lambda: _BASELINE["fill"])
    border_color: str = field(default_factory=lambda: _BASELINE["border_color"])
    border_width: float = field(default_factory=lambda: _BASELINE["border_width"])
    font_family: str = field(default_factory=lambda: _BASELINE["font_family"])
    font_size: int = field(default_factory=lambda: _BASELINE["font_size"])
    font_color: str = field(default_factory=lambda: _BASELINE["font_color"])
    bold: bool = field(default_factory=lambda: _BASELINE["bold"])
    italic: bool = field(default_factory=lambda: _BASELINE["italic"])
    text_align: str = field(default_factory=lambda: _BASELINE["text_align"])
    width: Optional[float] = None
    height: Optional[float] = None
    html: Optional[str] = None
    svg_path: Optional[str] = None
    type: Optional[str] = None
    parent_id: Optional[str] = None
    extent: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        shape_val = self.shape.value if isinstance(self.shape, Shape) else self.shape
        data: Dict[str, Any] = {
            "label": self.label,
            "shape": shape_val,
            "fill": self.fill,
            "borderColor": self.border_color,
            "borderWidth": self.border_width,
            "fontFamily": self.font_family,
            "fontSize": self.font_size,
            "fontColor": self.font_color,
            "bold": self.bold,
            "italic": self.italic,
            "textAlign": self.text_align,
            **self.data,
        }
        if self.width is not None:
            data["width"] = self.width
        if self.height is not None:
            data["height"] = self.height
        if self.html is not None:
            data["html"] = self.html
        if self.svg_path is not None:
            data["svgPath"] = self.svg_path
        d: Dict[str, Any] = {
            "id": self.id,
            "type": self.type or "shape",
            "position": {"x": self.pos[0], "y": self.pos[1]},
            "data": data,
        }
        if self.parent_id is not None:
            d["parentId"] = self.parent_id
        if self.extent is not None:
            d["extent"] = self.extent
        return d


def _text_style_dict(obj: Any) -> Dict[str, Any]:
    """Shared text-style vocabulary serialized to camelCase for the channel."""
    return {
        "fontFamily": obj.font_family,
        "fontSize": obj.font_size,
        "fill": obj.font_color,
        "fontWeight": 700 if obj.bold else 400,
        "fontStyle": "italic" if obj.italic else "normal",
    }


@dataclass
class Edge:
    """A styled edge. ``to_dict()`` serializes it for the sync channel.

    The full target field list is present; the skeleton ``to_dict`` only emits
    ``id``/``source``/``target``. ``id`` is derived from the endpoints when not
    given.
    """

    source: str
    target: str
    id: Optional[str] = None
    label: str = ""
    path_type: str = field(default_factory=lambda: _BASELINE["path_type"])
    marker_start: str = field(default_factory=lambda: _BASELINE["marker_start"])
    marker_end: str = field(default_factory=lambda: _BASELINE["marker_end"])
    color: str = field(default_factory=lambda: _BASELINE["edge_color"])
    width: float = field(default_factory=lambda: _BASELINE["edge_width"])
    dash: str = field(default_factory=lambda: _BASELINE["dash"])
    font_family: str = field(default_factory=lambda: _BASELINE["font_family"])
    font_size: int = field(default_factory=lambda: _BASELINE["font_size"])
    font_color: str = field(default_factory=lambda: _BASELINE["font_color"])
    bold: bool = field(default_factory=lambda: _BASELINE["bold"])
    italic: bool = field(default_factory=lambda: _BASELINE["italic"])
    label_bg: Optional[str] = None
    type: Optional[str] = None

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = f"{self.source}->{self.target}"

    def to_dict(self) -> Dict[str, Any]:
        _PATH_MAP = {"bezier": "default", "straight": "straight", "step": "step", "smoothstep": "smoothstep"}
        _DASH_MAP = {"solid": None, "dashed": "6 4", "dotted": "2 4"}

        # custom type (L3) overrides path_type
        edge_type = self.type if self.type else _PATH_MAP.get(self.path_type, "default")

        style: Dict[str, Any] = {
            "stroke": self.color,
            "strokeWidth": self.width,
        }
        dash = _DASH_MAP.get(self.dash)
        if dash:
            style["strokeDasharray"] = dash

        d: Dict[str, Any] = {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "type": edge_type,
            "style": style,
        }

        def _marker(m: str) -> Optional[Dict[str, str]]:
            if m == "arrow":
                return {"type": "arrow"}
            if m == "closed_arrow":
                return {"type": "arrowclosed"}
            return None

        ms = _marker(self.marker_start)
        me = _marker(self.marker_end)
        if ms:
            d["markerStart"] = ms
        if me:
            d["markerEnd"] = me

        if self.label:
            d["label"] = self.label
            d["labelStyle"] = _text_style_dict(self)

        if self.label_bg is not None:
            d["labelBgStyle"] = {"fill": self.label_bg}
            d["labelShowBg"] = True

        return d


class Flow(anywidget.AnyWidget):
    """The interactive flow-diagram widget.

    Synced traits drive the bundled front-end. Canvas edits (drag-stop,
    add/remove) flow back into ``nodes``/``edges``. The L3 registries and the
    ``on()`` event machinery are declared but inert until ITER_06.
    """

    _esm = _STATIC / "widget.js"
    _css = _STATIC / "widget.css"

    nodes = traitlets.List().tag(sync=True)
    edges = traitlets.List().tag(sync=True)
    color_mode = traitlets.Unicode("light").tag(sync=True)
    fit_view = traitlets.Bool(True).tag(sync=True)
    height = traitlets.Int(480).tag(sync=True)

    # L3 custom-component registries — synced but inert until ITER_06.
    _node_modules = traitlets.Dict().tag(sync=True)
    _edge_modules = traitlets.Dict().tag(sync=True)
    # Layout trigger trait (ITER_04): front-end watches this and runs dagre.
    _layout_request = traitlets.Dict().tag(sync=True)

    def __init__(
        self,
        nodes: Optional[List[Node]] = None,
        edges: Optional[List[Edge]] = None,
        color_mode: str = "light",
        fit_view: bool = True,
        height: int = 480,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.color_mode = color_mode
        self.fit_view = fit_view
        self.height = height
        # v2 transport seam: the bound adapter (lazily created by display()/
        # serve()). None until a host door is opened.
        self._transport: Optional["Transport"] = None
        # on() machinery — declared but inert until ITER_06.
        self._handlers: Dict[str, List[Callable[..., Any]]] = {}
        self.nodes = [n.to_dict() for n in (nodes or [])]
        self.edges = [e.to_dict() for e in (edges or [])]

    def add_node(self, node: Node) -> None:
        """Append a node and sync."""
        self.nodes = [*self.nodes, node.to_dict()]

    def add_edge(self, edge: Edge) -> None:
        """Append an edge and sync."""
        self.edges = [*self.edges, edge.to_dict()]

    def positions(self) -> Dict[str, Tuple[float, float]]:
        """Current canvas geometry as last synced: ``{id: (x, y)}``."""
        out: Dict[str, Tuple[float, float]] = {}
        for n in self.nodes:
            pos = n.get("position", {})
            out[n["id"]] = (pos.get("x", 0.0), pos.get("y", 0.0))
        return out

    # --- ITER_03: undo/redo trigger custom messages; history lives in JS ---

    def undo(self) -> None:
        """Step back through canvas-edit history (no-op when stack empty)."""
        self.send({"type": "undo"})

    def redo(self) -> None:
        """Step forward through canvas-edit history (no-op when stack empty)."""
        self.send({"type": "redo"})

    def group(self, node_ids: List[str], label: str = "") -> str:
        """Create a parent group containing the given nodes; return the group id."""
        group_n = sum(1 for n in self.nodes if n.get("type") == "group")
        group_id = f"group-{group_n}"

        # Collect member positions and sizes to compute bounding box
        members = [n for n in self.nodes if n["id"] in node_ids]
        if not members:
            raise ValueError("node_ids must reference existing nodes")

        padding = 32
        min_x = min(n["position"]["x"] for n in members)
        min_y = min(n["position"]["y"] for n in members)
        max_x = max(n["position"]["x"] + (n.get("data", {}).get("width") or 130) for n in members)
        max_y = max(n["position"]["y"] + (n.get("data", {}).get("height") or 56) for n in members)

        gx = min_x - padding
        gy = min_y - padding
        gw = max_x - min_x + padding * 2
        gh = max_y - min_y + padding * 2

        group_dict: Dict[str, Any] = {
            "id": group_id,
            "type": "group",
            "position": {"x": gx, "y": gy},
            "data": {"label": label, "width": gw, "height": gh},
            "style": {"width": gw, "height": gh},
        }

        # Make children parent-relative and assign parentId/extent
        updated: List[Dict[str, Any]] = []
        for n in self.nodes:
            if n["id"] in node_ids:
                nc = dict(n)
                nc["parentId"] = group_id
                nc["extent"] = "parent"
                nc["position"] = {
                    "x": n["position"]["x"] - gx,
                    "y": n["position"]["y"] - gy,
                }
                updated.append(nc)
            else:
                updated.append(n)

        self.nodes = [*updated, group_dict]
        return group_id

    def layout(self, algo: str = "dagre", direction: str = "TB", **opts: Any) -> None:
        """Auto-arrange nodes via the front-end layout engine."""
        import uuid

        if algo != "dagre":
            raise ValueError(f"Unsupported layout algorithm '{algo}'; MVP supports 'dagre' only")
        if direction not in ("TB", "BT", "LR", "RL"):
            raise ValueError(f"direction must be one of TB, BT, LR, RL; got '{direction}'")
        self._layout_request = {
            "algo": algo,
            "direction": direction,
            "opts": opts,
            "nonce": str(uuid.uuid4()),
        }

    def to_json(self) -> str:
        """Lossless JSON snapshot of the whole diagram."""
        from figureflow.serialize import to_json as _to_json
        return _to_json(self)

    @classmethod
    def from_json(cls, s: str) -> "Flow":
        """Rebuild a diagram from ``to_json`` output."""
        from figureflow.serialize import from_json as _from_json
        return _from_json(s)

    def load_json(self, s: str) -> None:
        """Replace current nodes/edges from JSON and clear undo history."""
        import json
        data = json.loads(s)
        self.nodes = list(data.get("nodes", []))
        self.edges = list(data.get("edges", []))
        self.send({"type": "clear_history"})

    def to_mermaid(self, direction: str = "TB") -> str:
        """Export mermaid flowchart text (lossy — structure + labels only)."""
        from figureflow.serialize import to_mermaid as _to_mermaid
        return _to_mermaid(self, direction=direction)

    # --- v2: transport seam — three host entry points (SKELETON_V2 §04) -------
    # ``Flow`` is itself the canonical state holder and the anywidget. The seam
    # routes its three doors through transport adapters; in the skeleton only
    # ``display()`` is wired (the v1 way), the rest are honestly gated.

    def display(self) -> "Flow":
        """Render in a notebook via the anywidget adapter.

        v1 behavior, now the explicit notebook door of the transport seam. Binds
        an :class:`~figureflow.transport.anywidget_adapter.AnywidgetAdapter` to
        this ``Flow`` and returns ``self``. Since ``Flow`` *is* the ``AnyWidget``,
        the v1 auto-render path (``_repr_mimebundle_`` on a cell's last line) is
        unchanged and the live data flow runs through the JS half of the seam
        (renderer → JS ``Transport`` → anywidget JS adapter → ``model``); the
        bound Python adapter is its trait-side counterpart.

        Returns:
            ``self`` — the widget to render.
        """
        from figureflow.transport.anywidget_adapter import AnywidgetAdapter

        if self._transport is None:
            self._transport = AnywidgetAdapter()
            self._transport.bind(self)
        return self

    def to_html(self, path: Optional[str] = None, *, title: Optional[str] = None) -> str:
        """Write a self-contained, offline, client-side-interactive snapshot.

        Args:
            path: If given, the HTML is written there (UTF-8); the string is
                returned either way.
            title: Optional page ``<title>``.

        Returns:
            The self-contained HTML string.
        """
        from figureflow.transport.static_export import StaticExportAdapter

        adapter = StaticExportAdapter()
        adapter.bind(self)
        html_str = adapter.render_html(self, title=title)
        if path is not None:
            pathlib.Path(path).write_text(html_str, encoding="utf-8")
        return html_str

    def serve(
        self,
        host: str = "127.0.0.1",
        port: int = 0,
        *,
        open_browser: bool = True,
        block: bool = False,
    ) -> str:
        """Serve the diagram in a plain browser tab with live bidirectional sync.

        Starts a dependency-free stdlib SSE+POST server bound to localhost.

        Args:
            host: Bind address; localhost only (never ``0.0.0.0``).
            port: ``0`` lets the OS pick a free port.
            open_browser: Launch the URL via ``webbrowser``.
            block: Join the server thread (for ``python script.py`` use).

        Returns:
            The served URL.
        """
        from figureflow.transport.server_adapter import ServerAdapter

        # A second serve() stops the prior server first.
        if isinstance(self._transport, ServerAdapter):
            self._transport.stop()
        adapter = ServerAdapter(
            host, port, open_browser=open_browser, block=block
        )
        adapter.bind(self)
        self._transport = adapter
        adapter.start()
        return adapter.url

    def stop(self) -> None:
        """Stop a running ``serve()`` server (no-op if none is running)."""
        from figureflow.transport.server_adapter import ServerAdapter

        if isinstance(self._transport, ServerAdapter):
            self._transport.stop()
            self._transport = None

    _BUILTIN_NODE_TYPES = frozenset({"shape", "group"})
    _BUILTIN_EDGE_TYPES = frozenset({"default", "straight", "step", "smoothstep"})

    def register_node_type(self, name: str, module: str) -> None:
        """Register a custom JS node component (L3 escape hatch)."""
        if not name or not name.isidentifier():
            raise ValueError(f"'{name}' is not a valid identifier")
        if name in self._BUILTIN_NODE_TYPES:
            raise ValueError(f"'{name}' collides with a built-in node type")
        self._node_modules = {**self._node_modules, name: module}

    def register_edge_type(self, name: str, module: str) -> None:
        """Register a custom JS edge component (L3 escape hatch)."""
        if not name or not name.isidentifier():
            raise ValueError(f"'{name}' is not a valid identifier")
        if name in self._BUILTIN_EDGE_TYPES:
            raise ValueError(f"'{name}' collides with a built-in edge type")
        self._edge_modules = {**self._edge_modules, name: module}

    def on(self, event: str, callback: Callable[..., Any]) -> Callable[[], None]:
        """Subscribe to emit() events from custom components. Returns unsubscribe."""
        self._handlers.setdefault(event, []).append(callback)
        self._ensure_msg_listener()

        def unsubscribe() -> None:
            handlers = self._handlers.get(event, [])
            if callback in handlers:
                handlers.remove(callback)

        return unsubscribe

    def _ensure_msg_listener(self) -> None:
        if getattr(self, "_msg_listener_active", False):
            return
        self._msg_listener_active = True

        def _on_msg(widget: Any, content: Any, buffers: Any) -> None:
            if not isinstance(content, dict):
                return
            event = content.get("event")
            payload = content.get("payload")
            for cb in list(self._handlers.get(event, [])):
                cb(payload)

        self.on_msg(_on_msg)
