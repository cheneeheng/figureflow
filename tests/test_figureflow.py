"""pytest suite — serialization, positions(), group(), and round-trip."""
from __future__ import annotations

import json

import pytest

from figureflow import Edge, Flow, Node, Shape
from figureflow.serialize import from_json, to_json, to_mermaid


# ─── Node.to_dict() ──────────────────────────────────────────────────────────

class TestNodeToDict:
    def test_defaults(self):
        d = Node("a").to_dict()
        assert d["id"] == "a"
        assert d["type"] == "shape"
        assert d["position"] == {"x": 0.0, "y": 0.0}
        data = d["data"]
        assert data["shape"] == "rectangle"
        assert data["fill"] == "#ffffff"
        assert data["borderColor"] == "#334155"
        assert data["borderWidth"] == 1.5
        assert data["fontFamily"] == "Inter, system-ui, sans-serif"
        assert data["fontSize"] == 13
        assert data["fontColor"] == "#0f172a"
        assert data["bold"] is False
        assert data["italic"] is False
        assert data["textAlign"] == "center"

    def test_all_eight_shapes(self):
        for shape in Shape:
            d = Node("x", shape=shape).to_dict()
            assert d["data"]["shape"] == shape.value

    def test_custom_type_passthrough(self):
        d = Node("x", type="mytype").to_dict()
        assert d["type"] == "mytype"

    def test_optional_fields_absent_when_none(self):
        d = Node("x").to_dict()
        assert "width" not in d["data"]
        assert "height" not in d["data"]
        assert "html" not in d["data"]
        assert "svgPath" not in d["data"]

    def test_optional_fields_present_when_set(self):
        d = Node("x", width=100, height=50, html="<b>hi</b>", svg_path="M 0 0").to_dict()
        assert d["data"]["width"] == 100
        assert d["data"]["height"] == 50
        assert d["data"]["html"] == "<b>hi</b>"
        assert d["data"]["svgPath"] == "M 0 0"

    def test_parent_id_and_extent(self):
        d = Node("c", parent_id="g1", extent="parent").to_dict()
        assert d["parentId"] == "g1"
        assert d["extent"] == "parent"

    def test_parent_id_absent_when_none(self):
        d = Node("x").to_dict()
        assert "parentId" not in d
        assert "extent" not in d

    def test_extra_data_merged(self):
        d = Node("x", data={"custom": 42}).to_dict()
        assert d["data"]["custom"] == 42


# ─── Edge.to_dict() ──────────────────────────────────────────────────────────

class TestEdgeToDict:
    def test_defaults(self):
        d = Edge("a", "b").to_dict()
        assert d["id"] == "a->b"
        assert d["source"] == "a"
        assert d["target"] == "b"
        assert d["type"] == "default"  # bezier → default
        assert d["style"]["stroke"] == "#334155"
        assert d["style"]["strokeWidth"] == 1.5
        assert "strokeDasharray" not in d["style"]
        assert d["markerEnd"] == {"type": "arrow"}
        assert "markerStart" not in d

    def test_path_type_mapping(self):
        cases = [
            ("bezier", "default"),
            ("straight", "straight"),
            ("step", "step"),
            ("smoothstep", "smoothstep"),
        ]
        for pt, expected in cases:
            d = Edge("a", "b", path_type=pt).to_dict()
            assert d["type"] == expected, pt

    def test_custom_type_overrides_path_type(self):
        d = Edge("a", "b", type="myedge", path_type="step").to_dict()
        assert d["type"] == "myedge"

    def test_dash_styles(self):
        assert "strokeDasharray" not in Edge("a", "b", dash="solid").to_dict()["style"]
        assert Edge("a", "b", dash="dashed").to_dict()["style"]["strokeDasharray"] == "6 4"
        assert Edge("a", "b", dash="dotted").to_dict()["style"]["strokeDasharray"] == "2 4"

    def test_marker_start(self):
        d = Edge("a", "b", marker_start="arrow").to_dict()
        assert d["markerStart"] == {"type": "arrow"}

    def test_marker_closed_arrow(self):
        d = Edge("a", "b", marker_end="closed_arrow").to_dict()
        assert d["markerEnd"] == {"type": "arrowclosed"}

    def test_marker_none_omitted(self):
        d = Edge("a", "b", marker_end="none", marker_start="none").to_dict()
        assert "markerEnd" not in d
        assert "markerStart" not in d

    def test_label_and_label_style(self):
        d = Edge("a", "b", label="hi").to_dict()
        assert d["label"] == "hi"
        assert "labelStyle" in d
        ls = d["labelStyle"]
        assert "fontFamily" in ls
        assert "fontSize" in ls
        assert "fill" in ls  # fontColor → fill in labelStyle

    def test_label_absent_when_empty(self):
        d = Edge("a", "b", label="").to_dict()
        assert "label" not in d
        assert "labelStyle" not in d

    def test_label_bg(self):
        d = Edge("a", "b", label_bg="#fff").to_dict()
        assert d["labelShowBg"] is True
        assert d["labelBgStyle"] == {"fill": "#fff"}

    def test_explicit_id(self):
        d = Edge("a", "b", id="custom-id").to_dict()
        assert d["id"] == "custom-id"


# ─── Flow.positions() ────────────────────────────────────────────────────────

class TestPositions:
    def test_positions_reflect_initial(self):
        flow = Flow(nodes=[
            Node("a", pos=(10.0, 20.0)),
            Node("b", pos=(30.0, 40.0)),
        ])
        pos = flow.positions()
        assert pos["a"] == (10.0, 20.0)
        assert pos["b"] == (30.0, 40.0)

    def test_add_node_appears_in_positions(self):
        flow = Flow()
        flow.add_node(Node("x", pos=(5.0, 6.0)))
        assert flow.positions()["x"] == (5.0, 6.0)


# ─── Flow.group() ────────────────────────────────────────────────────────────

class TestGroup:
    def _three_node_flow(self):
        return Flow(nodes=[
            Node("a", "A", pos=(0.0,   0.0)),
            Node("b", "B", pos=(200.0, 0.0)),
            Node("c", "C", pos=(100.0, 200.0)),
        ])

    def test_returns_group_id(self):
        flow = self._three_node_flow()
        gid = flow.group(["a", "b"], label="AB")
        assert gid == "group-0"

    def test_group_node_present(self):
        flow = self._three_node_flow()
        gid = flow.group(["a", "b"])
        ids = [n["id"] for n in flow.nodes]
        assert gid in ids
        grp = next(n for n in flow.nodes if n["id"] == gid)
        assert grp["type"] == "group"

    def test_children_have_parent_id(self):
        flow = self._three_node_flow()
        gid = flow.group(["a", "b"])
        children = [n for n in flow.nodes if n.get("parentId") == gid]
        assert len(children) == 2

    def test_children_extent_parent(self):
        flow = self._three_node_flow()
        gid = flow.group(["a", "b"])
        for n in flow.nodes:
            if n.get("parentId") == gid:
                assert n["extent"] == "parent"

    def test_children_positions_parent_relative(self):
        flow = Flow(nodes=[
            Node("a", pos=(100.0, 100.0)),
            Node("b", pos=(300.0, 100.0)),
        ])
        gid = flow.group(["a", "b"])
        grp = next(n for n in flow.nodes if n["id"] == gid)
        gx = grp["position"]["x"]
        gy = grp["position"]["y"]
        for n in flow.nodes:
            if n.get("parentId") == gid:
                # child position should be positive (within group)
                assert n["position"]["x"] >= 0
                assert n["position"]["y"] >= 0

    def test_non_member_nodes_unchanged(self):
        flow = self._three_node_flow()
        orig_c = next(n for n in flow.nodes if n["id"] == "c")
        orig_pos = dict(orig_c["position"])
        flow.group(["a", "b"])
        c_after = next(n for n in flow.nodes if n["id"] == "c")
        assert c_after["position"] == orig_pos

    def test_empty_node_ids_raises(self):
        flow = self._three_node_flow()
        with pytest.raises(ValueError):
            flow.group([])

    def test_second_group_id_increments(self):
        flow = self._three_node_flow()
        flow.group(["a"])
        gid2 = flow.group(["b"])
        assert gid2 == "group-1"


# ─── Serialization round-trip ────────────────────────────────────────────────

class TestSerialization:
    def _styled_flow(self):
        return Flow(
            nodes=[
                Node("a", "Start", pos=(0.0, 0.0),   shape=Shape.stadium, fill="#e8f0fe"),
                Node("b", "Step",  pos=(0.0, 120.0), shape=Shape.rectangle),
                Node("c", "End",   pos=(0.0, 240.0), shape=Shape.diamond,  fill="#e6f4ea"),
            ],
            edges=[
                Edge("a", "b", label="go", dash="dashed"),
                Edge("b", "c", path_type="step"),
            ],
            color_mode="dark",
            height=600,
        )

    def test_round_trip_node_count(self):
        flow = self._styled_flow()
        assert len(from_json(to_json(flow)).nodes) == 3

    def test_round_trip_edge_count(self):
        flow = self._styled_flow()
        assert len(from_json(to_json(flow)).edges) == 2

    def test_round_trip_exact(self):
        flow = self._styled_flow()
        snap = to_json(flow)
        flow2 = from_json(snap)
        assert to_json(flow2) == snap

    def test_schema_field(self):
        flow = Flow()
        data = json.loads(to_json(flow))
        assert data["schema"] == "figureflow/1"

    def test_metadata_preserved(self):
        flow = Flow(color_mode="dark", fit_view=False, height=600)
        data = json.loads(to_json(flow))
        assert data["color_mode"] == "dark"
        assert data["fit_view"] is False
        assert data["height"] == 600

    def test_from_json_rejects_unknown_schema(self):
        bad = json.dumps({"schema": "figureflow/99", "nodes": [], "edges": []})
        with pytest.raises(ValueError, match="Unsupported"):
            from_json(bad)

    def test_round_trip_with_group(self):
        flow = Flow(nodes=[
            Node("a", pos=(0.0, 0.0)),
            Node("b", pos=(200.0, 0.0)),
            Node("c", pos=(0.0, 200.0)),
        ])
        flow.group(["a", "b"], label="G")
        snap = to_json(flow)
        flow2 = from_json(snap)
        assert len(flow2.nodes) == len(flow.nodes)
        # group node preserved
        grp = next((n for n in flow2.nodes if n["type"] == "group"), None)
        assert grp is not None

    def test_load_json_replaces_in_place(self):
        flow = Flow(nodes=[Node("x", pos=(0.0, 0.0))])
        snap = to_json(flow)
        flow.add_node(Node("y", pos=(100.0, 0.0)))
        assert len(flow.nodes) == 2
        flow.load_json(snap)
        assert len(flow.nodes) == 1


# ─── to_mermaid() ─────────────────────────────────────────────────────────────

class TestToMermaid:
    def test_header(self):
        m = to_mermaid(Flow())
        assert m.startswith("%%")
        assert "flowchart TB" in m

    def test_direction_override(self):
        assert "flowchart LR" in to_mermaid(Flow(), direction="LR")

    def test_node_shapes(self):
        shapes_and_expected = [
            (Shape.rectangle,    "["),
            (Shape.rounded,      "("),
            (Shape.stadium,      "(["),
            (Shape.diamond,      "{"),
            (Shape.cylinder,     "[("),
            (Shape.parallelogram, "[/"),
        ]
        for shape, marker in shapes_and_expected:
            flow = Flow(nodes=[Node("n", "X", shape=shape)])
            m = to_mermaid(flow)
            assert marker in m, f"shape={shape} expected '{marker}' in mermaid"

    def test_edge_label(self):
        flow = Flow(
            nodes=[Node("a", pos=(0, 0)), Node("b", pos=(0, 100))],
            edges=[Edge("a", "b", label="yes")],
        )
        m = to_mermaid(flow)
        assert '"yes"' in m

    def test_dashed_edge(self):
        flow = Flow(
            nodes=[Node("a", pos=(0, 0)), Node("b", pos=(0, 100))],
            edges=[Edge("a", "b", dash="dashed")],
        )
        assert "-.->" in to_mermaid(flow)

    def test_solid_edge(self):
        flow = Flow(
            nodes=[Node("a", pos=(0, 0)), Node("b", pos=(0, 100))],
            edges=[Edge("a", "b", dash="solid")],
        )
        m = to_mermaid(flow)
        assert "-->" in m
        assert "-.->" not in m

    def test_id_hyphens_replaced(self):
        flow = Flow(nodes=[Node("my-node", pos=(0, 0))])
        assert "my_node" in to_mermaid(flow)


# ─── v2 transport seam (SKELETON_V2) ─────────────────────────────────────────

class TestTransportSeam:
    def test_display_returns_self(self):
        flow = Flow()
        assert flow.display() is flow

    def test_to_html_gated_to_iteration(self):
        with pytest.raises(NotImplementedError, match="ITER_V2_02"):
            Flow().to_html()

    def test_serve_gated_to_iteration(self):
        with pytest.raises(NotImplementedError, match="ITER_V2_03"):
            Flow().serve()

    def test_stop_gated_to_iteration(self):
        with pytest.raises(NotImplementedError, match="ITER_V2_03"):
            Flow().stop()


class TestSyncCore:
    def test_diff_gated_to_iteration(self):
        from figureflow import synccore
        with pytest.raises(NotImplementedError, match="ITER_V2_01"):
            synccore.diff(None, {})

    def test_is_echo_gated_to_iteration(self):
        from figureflow import synccore
        with pytest.raises(NotImplementedError, match="ITER_V2_01"):
            synccore.is_echo({}, None)

    def test_lock_present(self):
        import threading
        from figureflow import synccore
        # The shared mutate-then-snapshot lock the server adapter will hold.
        assert isinstance(synccore.LOCK, type(threading.Lock()))


class TestTransportContract:
    def test_base_is_abstract(self):
        from figureflow.transport import Transport
        with pytest.raises(TypeError):
            Transport()  # cannot instantiate the ABC directly

    def test_start_stop_default_noops(self):
        from figureflow.transport import Transport

        class _Concrete(Transport):
            def bind(self, flow):
                pass

            def send_state(self, nodes, edges, meta):
                pass

            def on_change(self, handler):
                pass

            def emit(self, event, payload):
                pass

        t = _Concrete()
        assert t.start() is None
        assert t.stop() is None

    def test_adapters_subclass_transport(self):
        from figureflow.transport import Transport
        from figureflow.transport.anywidget_adapter import AnywidgetAdapter
        from figureflow.transport.static_export import StaticExportAdapter
        from figureflow.transport.server_adapter import ServerAdapter
        for cls in (AnywidgetAdapter, StaticExportAdapter, ServerAdapter):
            assert issubclass(cls, Transport)

    def test_anywidget_adapter_gated(self):
        from figureflow.transport.anywidget_adapter import AnywidgetAdapter
        with pytest.raises(NotImplementedError, match="ITER_V2_01"):
            AnywidgetAdapter().bind(Flow())

    def test_static_adapter_gated(self):
        from figureflow.transport.static_export import StaticExportAdapter
        with pytest.raises(NotImplementedError, match="ITER_V2_02"):
            StaticExportAdapter().render_html(Flow())

    def test_server_adapter_gated(self):
        from figureflow.transport.server_adapter import ServerAdapter
        with pytest.raises(NotImplementedError, match="ITER_V2_03"):
            ServerAdapter().start()
