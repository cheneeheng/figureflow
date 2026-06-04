"""figureflow — interactive flow diagram widget for Python.

Skeleton surface: ``Shape``, ``Node``, ``Edge`` and ``Flow`` are all present
with their full target field lists, but only the render+sync loop is wired up.
Later iterations fill the stubbed methods (named in each ``NotImplementedError``).
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import anywidget
import traitlets

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
    # shared text-style vocabulary
    "font_family": "sans-serif",
    "font_size": 12,
    "font_color": "#222222",
    "bold": False,
    "italic": False,
    # node style
    "shape": Shape.rectangle,
    "fill": "#ffffff",
    "border_color": "#222222",
    "border_width": 1,
    "text_align": "center",
    # edge style
    "path_type": "bezier",
    "marker_start": "none",
    "marker_end": "arrow",
    "edge_color": "#222222",
    "edge_width": 1,
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
    border_width: int = field(default_factory=lambda: _BASELINE["border_width"])
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
        # Skeleton: emit only what the ShapeNode renderer binds. type defaults
        # to "shape" so the custom renderer is used (else xyflow falls back to
        # its default node). Geometry/fonts/grouping ride along in later iters.
        return {
            "id": self.id,
            "type": self.type or "shape",
            "position": {"x": self.pos[0], "y": self.pos[1]},
            "data": {
                "label": self.label,
                "fill": self.fill,
                "borderColor": self.border_color,
            },
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
    width: int = field(default_factory=lambda: _BASELINE["edge_width"])
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
        # Skeleton: built-in edge styling (path/markers/dash) rides on xyflow's
        # native renderers in later iterations; emit only the topology here.
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
        }


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

    # --- stubs: surface visible, honestly gated to the filling iteration ---

    def undo(self) -> None:
        raise NotImplementedError("Flow.undo is implemented in ITER_03")

    def redo(self) -> None:
        raise NotImplementedError("Flow.redo is implemented in ITER_03")

    def group(self, node_ids: List[str], label: str = "") -> str:
        raise NotImplementedError("Flow.group is implemented in ITER_04")

    def layout(self, algo: str = "dagre", direction: str = "TB", **opts: Any) -> None:
        raise NotImplementedError("Flow.layout is implemented in ITER_04")

    def to_json(self) -> str:
        raise NotImplementedError("Flow.to_json is implemented in ITER_05")

    @classmethod
    def from_json(cls, s: str) -> "Flow":
        raise NotImplementedError("Flow.from_json is implemented in ITER_05")

    def to_mermaid(self) -> str:
        raise NotImplementedError("Flow.to_mermaid is implemented in ITER_05")

    def register_node_type(self, name: str, module: str) -> None:
        raise NotImplementedError("Flow.register_node_type is implemented in ITER_06")

    def register_edge_type(self, name: str, module: str) -> None:
        raise NotImplementedError("Flow.register_edge_type is implemented in ITER_06")

    def on(self, event: str, callback: Callable[..., Any]) -> None:
        raise NotImplementedError("Flow.on is implemented in ITER_06")
