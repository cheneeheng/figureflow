"""pyxyflow — interactive flowchart widget for Python.

A per-element-styled flowchart built on anywidget + React Flow (@xyflow/react).
This module is the SKELETON implementation: the full Node/Edge/Flow surface is
present, but only the construct -> display -> drag -> read-back loop is wired.
Fields and methods that later iterations fill in are carried honestly — extra
style fields are stored but not yet honored by the front-end, and gated methods
raise ``NotImplementedError`` naming the iteration that implements them.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

import anywidget
import traitlets

__all__ = ["Shape", "Node", "Edge", "Flow"]

_STATIC = pathlib.Path(__file__).parent / "static"


class Shape(str, Enum):
    """The 8 built-in node shapes."""

    RECTANGLE = "rectangle"
    ROUNDED = "rounded"
    STADIUM = "stadium"
    ELLIPSE = "ellipse"
    DIAMOND = "diamond"
    PARALLELOGRAM = "parallelogram"
    HEXAGON = "hexagon"
    CYLINDER = "cylinder"


# Internal global baseline: the single source of default field values fresh
# elements start from. NOT surfaced in any signature, not a theme, not
# user-settable. New element -> baseline values -> per-element user overrides.
# Style lives on the element, so a duplicated element carries it.
_BASELINE: Dict[str, object] = {
    # Shared text-style vocabulary (means the same on Node and Edge labels).
    "font_family": "sans-serif",
    "font_size": 14,
    "font_color": "#111827",
    "bold": False,
    "italic": False,
    # Node-only defaults.
    "shape": Shape.RECTANGLE,
    "fill": "#ffffff",
    "border_color": "#111827",
    "border_width": 1,
    "text_align": "center",
    # Edge-only defaults.
    "path_type": "bezier",
    "marker_start": "none",
    "marker_end": "arrow",
    "color": "#111827",
    "width": 1,
    "dash": "solid",
    "label_bg": "#ffffff",
}


@dataclass
class Node:
    """A styled node.

    The full target field list is present; ``to_dict()`` emits only the subset
    the skeleton front-end honors. Remaining fields are carried for later
    iterations (shape geometry, fonts: ITER_01/ITER_02; grouping: ITER_04).
    """

    id: str
    label: str = ""
    pos: Tuple[float, float] = (0.0, 0.0)
    shape: Shape = _BASELINE["shape"]  # type: ignore[assignment]
    fill: str = _BASELINE["fill"]  # type: ignore[assignment]
    border_color: str = _BASELINE["border_color"]  # type: ignore[assignment]
    border_width: float = _BASELINE["border_width"]  # type: ignore[assignment]
    font_family: str = _BASELINE["font_family"]  # type: ignore[assignment]
    font_size: int = _BASELINE["font_size"]  # type: ignore[assignment]
    font_color: str = _BASELINE["font_color"]  # type: ignore[assignment]
    bold: bool = _BASELINE["bold"]  # type: ignore[assignment]
    italic: bool = _BASELINE["italic"]  # type: ignore[assignment]
    text_align: str = _BASELINE["text_align"]  # type: ignore[assignment]
    width: Optional[float] = None
    height: Optional[float] = None
    # Escape-hatch fields (null by default): svg_path (L1), html (L2), type (L3).
    html: Optional[str] = None
    svg_path: Optional[str] = None
    type: Optional[str] = None
    # Grouping (ITER_04): null by default for ungrouped nodes.
    parent_id: Optional[str] = None
    extent: Optional[str] = None
    data: Optional[dict] = None

    def to_dict(self) -> dict:
        """Serialize for the sync channel.

        Skeleton emits ``id/type/position/data{label,fill,borderColor}`` with
        ``type="shape"`` so the ShapeNode renderer binds (otherwise xyflow would
        fall back to its default node). Shape/font/grouping fields are not yet
        carried across — later iterations wire them.
        """
        x, y = self.pos
        return {
            "id": self.id,
            "type": self.type or "shape",
            "position": {"x": x, "y": y},
            "data": {
                "label": self.label,
                "fill": self.fill,
                "borderColor": self.border_color,
            },
        }


@dataclass
class Edge:
    """A styled edge.

    Full target field list present; ``to_dict()`` emits only ``id/source/target``
    in the skeleton. Path type, markers, dash and label styling are carried for
    ITER_02.
    """

    source: str
    target: str
    id: Optional[str] = None
    label: str = ""
    path_type: str = _BASELINE["path_type"]  # type: ignore[assignment]
    marker_start: str = _BASELINE["marker_start"]  # type: ignore[assignment]
    marker_end: str = _BASELINE["marker_end"]  # type: ignore[assignment]
    color: str = _BASELINE["color"]  # type: ignore[assignment]
    width: float = _BASELINE["width"]  # type: ignore[assignment]
    dash: str = _BASELINE["dash"]  # type: ignore[assignment]
    font_family: str = _BASELINE["font_family"]  # type: ignore[assignment]
    font_size: int = _BASELINE["font_size"]  # type: ignore[assignment]
    font_color: str = _BASELINE["font_color"]  # type: ignore[assignment]
    bold: bool = _BASELINE["bold"]  # type: ignore[assignment]
    italic: bool = _BASELINE["italic"]  # type: ignore[assignment]
    label_bg: str = _BASELINE["label_bg"]  # type: ignore[assignment]
    type: Optional[str] = None

    def __post_init__(self) -> None:
        if self.id is None:
            self.id = f"{self.source}->{self.target}"

    def to_dict(self) -> dict:
        """Serialize for the sync channel (skeleton: id/source/target only)."""
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
        }


class Flow(anywidget.AnyWidget):
    """The interactive flowchart widget.

    Construct ``Flow(nodes=[...], edges=[...])``, display it, drag/edit on the
    canvas, and read the modified geometry back with ``positions()``.
    """

    _esm = _STATIC / "widget.js"
    _css = _STATIC / "widget.css"

    nodes = traitlets.List(traitlets.Dict()).tag(sync=True)
    edges = traitlets.List(traitlets.Dict()).tag(sync=True)
    color_mode = traitlets.Unicode("light").tag(sync=True)
    fit_view = traitlets.Bool(True).tag(sync=True)
    height = traitlets.Int(480).tag(sync=True)

    # Custom JS/TS component registries (L3, ITER_06): declared but inert here.
    _node_modules = traitlets.Dict().tag(sync=True)
    _edge_modules = traitlets.Dict().tag(sync=True)

    def __init__(
        self,
        nodes: Optional[List[Union["Node", dict]]] = None,
        edges: Optional[List[Union["Edge", dict]]] = None,
        color_mode: str = "light",
        fit_view: bool = True,
        height: int = 480,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self.color_mode = color_mode
        self.fit_view = fit_view
        self.height = height
        # on() event machinery (ITER_06): declared but inert.
        self._callbacks: Dict[str, list] = {}
        self.nodes = [self._as_dict(n) for n in (nodes or [])]
        self.edges = [self._as_dict(e) for e in (edges or [])]

    @staticmethod
    def _as_dict(item: Union["Node", "Edge", dict]) -> dict:
        if isinstance(item, dict):
            return item
        return item.to_dict()

    def add_node(self, node: Union["Node", dict]) -> None:
        """Append a node and sync to the front-end."""
        self.nodes = [*self.nodes, self._as_dict(node)]

    def add_edge(self, edge: Union["Edge", dict]) -> None:
        """Append an edge and sync to the front-end."""
        self.edges = [*self.edges, self._as_dict(edge)]

    def positions(self) -> Dict[str, Tuple[float, float]]:
        """Current canvas geometry as last synced: ``{id: (x, y)}``."""
        out: Dict[str, Tuple[float, float]] = {}
        for n in self.nodes:
            p = n.get("position", {})
            out[n["id"]] = (p.get("x", 0.0), p.get("y", 0.0))
        return out

    # --- Surface visible, honestly gated to the iteration that fills it. ---

    def undo(self) -> None:
        """Step back through canvas-edit history."""
        raise NotImplementedError("Flow.undo is implemented in ITER_03.")

    def redo(self) -> None:
        """Step forward through canvas-edit history."""
        raise NotImplementedError("Flow.redo is implemented in ITER_03.")

    def group(self, node_ids: List[str], label: str = "") -> str:
        """Create a parent group containing the given nodes."""
        raise NotImplementedError("Flow.group is implemented in ITER_04.")

    def layout(self, algo: str = "dagre", direction: str = "TB", **opts: object) -> None:
        """Auto-arrange nodes; positions sync back."""
        raise NotImplementedError("Flow.layout is implemented in ITER_04.")

    def to_json(self) -> str:
        """Lossless JSON of the whole diagram."""
        raise NotImplementedError("Flow.to_json is implemented in ITER_05.")

    @classmethod
    def from_json(cls, s: str) -> "Flow":
        """Rebuild a diagram from ``to_json`` output."""
        raise NotImplementedError("Flow.from_json is implemented in ITER_05.")

    def to_mermaid(self) -> str:
        """Export mermaid flowchart text (lossy)."""
        raise NotImplementedError("Flow.to_mermaid is implemented in ITER_05.")

    def register_node_type(self, name: str, module: str) -> None:
        """Register a custom JS/TS node component (L3)."""
        raise NotImplementedError("Flow.register_node_type is implemented in ITER_06.")

    def register_edge_type(self, name: str, module: str) -> None:
        """Register a custom JS/TS edge component (L3)."""
        raise NotImplementedError("Flow.register_edge_type is implemented in ITER_06.")

    def on(self, event: str, callback) -> None:
        """Subscribe to ``emit()`` events from custom components."""
        raise NotImplementedError("Flow.on is implemented in ITER_06.")
