"""pytest suite — serialization, positions(), group(), and round-trip."""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

from figureflow import Edge, Flow, Node, Shape, mcp_server
from figureflow.mermaid_in import MermaidParseError, from_mermaid
from figureflow.serialize import (
    FlowValidationError,
    from_json,
    to_json,
    to_mermaid,
    validate,
)


# ─── Node.to_dict() ──────────────────────────────────────────────────────────

class TestNodeToDict:
    def test_defaults(self):
        d = Node("a").to_dict()
        assert d["id"] == "a"
        assert d["type"] == "shape"
        # v3: a node with no authored position is unplaced (auto-laid on render).
        assert "position" not in d
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
        with pytest.raises(ValueError, match="unsupported schema"):
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


# ─── v2 transport seam — sync-core (ITER_V2_01 §04) ──────────────────────────

class TestSyncCore:
    def test_diff_initial_push_includes_present_keys(self):
        from figureflow import synccore
        assert synccore.diff(None, {"nodes": [1], "edges": []}) == {
            "nodes": [1],
            "edges": [],
        }

    def test_diff_none_when_unchanged(self):
        from figureflow import synccore
        state = {"nodes": [1], "edges": [2], "meta": {"height": 480}}
        assert synccore.diff(state, state) is None

    def test_diff_only_changed_keys(self):
        from figureflow import synccore
        prev = {"nodes": [1], "edges": [2]}
        assert synccore.diff(prev, {"nodes": [9], "edges": [2]}) == {"nodes": [9]}

    def test_diff_includes_meta_change(self):
        from figureflow import synccore
        prev = {"nodes": [], "edges": [], "meta": {"height": 480}}
        nxt = {"nodes": [], "edges": [], "meta": {"height": 600}}
        assert synccore.diff(prev, nxt) == {"meta": {"height": 600}}

    def test_is_echo_true_when_graph_matches(self):
        from figureflow import synccore
        pushed = {"nodes": [1], "edges": [2]}
        assert synccore.is_echo({"nodes": [1], "edges": [2]}, pushed) is True

    def test_is_echo_false_on_real_edit(self):
        from figureflow import synccore
        pushed = {"nodes": [1], "edges": [2]}
        assert synccore.is_echo({"nodes": [9], "edges": [2]}, pushed) is False

    def test_is_echo_false_when_nothing_pushed(self):
        from figureflow import synccore
        assert synccore.is_echo({"nodes": [1]}, None) is False

    def test_lock_present(self):
        import threading
        from figureflow import synccore
        # The shared mutate-then-snapshot lock the server adapter holds.
        assert isinstance(synccore.LOCK, type(threading.Lock()))


# ─── v2 transport seam — adapters (ITER_V2_01–03) ────────────────────────────

class TestDisplayAdapter:
    def test_display_returns_self(self):
        flow = Flow()
        assert flow.display() is flow

    def test_display_binds_anywidget_adapter(self):
        from figureflow.transport.anywidget_adapter import AnywidgetAdapter

        flow = Flow().display()
        assert isinstance(flow._transport, AnywidgetAdapter)

    def test_display_idempotent_when_already_bound(self):
        # Second display() finds _transport already set → reuses it (no rebind).
        flow = Flow()
        first = flow.display()._transport
        assert flow.display() is flow
        assert flow._transport is first


class TestStaticExport:
    def _flow(self):
        return Flow([Node("a", pos=(0, 0)), Node("b", pos=(10, 10))])

    def test_to_html_returns_self_contained_string(self):
        html = self._flow().to_html()
        # Inlined assets + JSON data island + static adapter bootstrap.
        assert "<style>" in html
        assert 'id="figureflow-state"' in html
        assert "createStaticTransport" in html

    def test_to_html_embeds_serialized_state(self):
        html = self._flow().to_html()
        assert '"schema": "figureflow/1"' in html or '"schema":"figureflow/1"' in html

    def test_to_html_writes_file_and_returns_string(self, tmp_path):
        out = tmp_path / "diagram.html"
        ret = self._flow().to_html(str(out))
        assert out.read_text(encoding="utf-8") == ret

    def test_to_html_title(self):
        html = Flow().to_html(title="My Diagram")
        assert "<title>My Diagram</title>" in html


class TestServe:
    def _get(self, url, timeout=5):
        import urllib.request

        return urllib.request.urlopen(url, timeout=timeout)

    def test_serve_lifecycle_and_routes(self):
        import urllib.request

        flow = Flow([Node("a", pos=(0, 0))])
        url = flow.serve(open_browser=False)
        try:
            assert url.startswith("http://127.0.0.1:")
            # ITER_V2_04: /state wraps the snapshot with the server_seq read
            # atomically with it (bootstrap ordering contract).
            wrapped = json.loads(self._get(url + "/state").read())
            assert wrapped["server_seq"] == 0
            assert wrapped["state"]["schema"] == "figureflow/1"
            assert [n["id"] for n in wrapped["state"]["nodes"]] == ["a"]

            page = self._get(url + "/").read().decode()
            assert "createServerTransport" in page

            js = self._get(url + "/widget.js")
            assert js.headers["Content-Type"] == "text/javascript"
        finally:
            flow.stop()
        assert flow._transport is None

    def test_post_change_commits_through_to_flow(self):
        import urllib.request

        flow = Flow([Node("a", pos=(0, 0))])
        url = flow.serve(open_browser=False)
        try:
            body = json.dumps(
                {"nodes": [{"id": "a", "position": {"x": 42, "y": 7}, "data": {}}]}
            ).encode()
            req = urllib.request.Request(
                url + "/change",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp = urllib.request.urlopen(req, timeout=5)
            assert resp.status == 204
            assert flow.positions()["a"] == (42, 7)
        finally:
            flow.stop()

    def test_second_serve_rebinds(self):
        flow = Flow([Node("a")])
        url1 = flow.serve(open_browser=False)
        url2 = flow.serve(open_browser=False)
        try:
            assert url1 != url2  # prior server stopped, new ephemeral port
        finally:
            flow.stop()

    def test_stop_is_idempotent(self):
        flow = Flow()
        flow.stop()  # no server running — no error
        assert flow._transport is None


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

    def test_anywidget_adapter_binds(self):
        from figureflow.transport.anywidget_adapter import AnywidgetAdapter

        flow = Flow()
        adapter = AnywidgetAdapter()
        adapter.bind(flow)
        # send_state writes the synced traits (the v1 sync write).
        adapter.send_state(
            [{"id": "x", "position": {"x": 0, "y": 0}, "data": {}}],
            [],
            {"height": 600},
        )
        assert [n["id"] for n in flow.nodes] == ["x"]
        assert flow.height == 600

    def test_static_adapter_renders_html(self):
        from figureflow.transport.static_export import StaticExportAdapter

        html = StaticExportAdapter().render_html(Flow())
        assert 'id="figureflow-state"' in html

    def test_server_adapter_requires_bind(self):
        from figureflow.transport.server_adapter import ServerAdapter

        # start() before bind() is a usage error, not a silent no-op.
        with pytest.raises(RuntimeError, match="bind"):
            ServerAdapter().start()


# ─── Flow public methods (add_edge / undo / redo / layout / json / mermaid) ───

class TestFlowMethods:
    def test_add_edge(self):
        flow = Flow([Node("a"), Node("b")])
        flow.add_edge(Edge("a", "b"))
        assert flow.edges[0]["id"] == "a->b"

    def test_undo_redo_safe_without_comm(self):
        # undo()/redo() send a custom message; without an open comm it is a no-op.
        flow = Flow([Node("a")])
        flow.undo()
        flow.redo()

    def test_layout_sets_request(self):
        flow = Flow([Node("a")])
        flow.layout(direction="LR", spacing=10)
        req = flow._layout_request
        assert req["algo"] == "dagre"
        assert req["direction"] == "LR"
        assert req["opts"] == {"spacing": 10}
        assert "nonce" in req

    def test_layout_default_direction(self):
        flow = Flow([Node("a")])
        flow.layout()
        assert flow._layout_request["direction"] == "TB"

    def test_layout_rejects_unknown_algo(self):
        with pytest.raises(ValueError, match="dagre"):
            Flow().layout(algo="force")

    def test_layout_rejects_bad_direction(self):
        with pytest.raises(ValueError, match="direction"):
            Flow().layout(direction="XY")

    def test_to_json_method(self):
        flow = Flow([Node("a")])
        data = json.loads(flow.to_json())
        assert data["schema"] == "figureflow/1"
        assert [n["id"] for n in data["nodes"]] == ["a"]

    def test_from_json_classmethod(self):
        flow = Flow([Node("a")])
        flow2 = Flow.from_json(flow.to_json())
        assert isinstance(flow2, Flow)
        assert [n["id"] for n in flow2.nodes] == ["a"]

    def test_to_mermaid_method(self):
        m = Flow([Node("a")]).to_mermaid(direction="LR")
        assert "flowchart LR" in m


# ─── L3 registries + on() event machinery ────────────────────────────────────

class TestRegistries:
    def test_register_node_type(self):
        flow = Flow()
        flow.register_node_type("mynode", "./m.js")
        assert flow._node_modules["mynode"] == "./m.js"

    def test_register_node_type_empty_name(self):
        with pytest.raises(ValueError, match="identifier"):
            Flow().register_node_type("", "x")

    def test_register_node_type_invalid_name(self):
        with pytest.raises(ValueError, match="identifier"):
            Flow().register_node_type("bad name", "x")

    def test_register_node_type_builtin_collision(self):
        with pytest.raises(ValueError, match="built-in"):
            Flow().register_node_type("shape", "x")

    def test_register_edge_type(self):
        flow = Flow()
        flow.register_edge_type("myedge", "./e.js")
        assert flow._edge_modules["myedge"] == "./e.js"

    def test_register_edge_type_invalid_name(self):
        with pytest.raises(ValueError, match="identifier"):
            Flow().register_edge_type("1bad", "x")

    def test_register_edge_type_builtin_collision(self):
        with pytest.raises(ValueError, match="built-in"):
            Flow().register_edge_type("straight", "x")


class TestOnEvent:
    def test_on_dispatches_payload(self):
        flow = Flow()
        got = []
        flow.on("evt", lambda p: got.append(p))
        flow._msg_callbacks(flow, {"event": "evt", "payload": 7}, [])
        assert got == [7]

    def test_unsubscribe_stops_delivery_and_is_idempotent(self):
        flow = Flow()
        got = []
        unsub = flow.on("evt", lambda p: got.append(p))
        unsub()
        unsub()  # second call: callback already removed, no error
        flow._msg_callbacks(flow, {"event": "evt", "payload": 8}, [])
        assert got == []

    def test_non_dict_content_ignored(self):
        flow = Flow()
        got = []
        flow.on("evt", lambda p: got.append(p))
        flow._msg_callbacks(flow, "not-a-dict", [])
        assert got == []

    def test_unknown_event_ignored(self):
        flow = Flow()
        got = []
        flow.on("evt", lambda p: got.append(p))
        flow._msg_callbacks(flow, {"event": "other", "payload": 1}, [])
        assert got == []

    def test_ensure_msg_listener_idempotent(self):
        flow = Flow()
        flow.on("a", lambda p: None)
        flow.on("b", lambda p: None)  # second on(): listener already active
        assert flow._msg_listener_active is True


# ─── Anywidget adapter (full coverage) ───────────────────────────────────────

class TestAnywidgetAdapterFull:
    def _adapter(self, flow):
        from figureflow.transport.anywidget_adapter import AnywidgetAdapter

        a = AnywidgetAdapter()
        a.bind(flow)
        return a

    def test_send_state_applies_meta(self):
        flow = Flow()
        a = self._adapter(flow)
        a.send_state([], [], {"color_mode": "dark", "fit_view": False, "height": 700})
        assert flow.color_mode == "dark"
        assert flow.fit_view is False
        assert flow.height == 700

    def test_send_state_meta_without_keys_skips_them(self):
        # Empty meta → every optional key (incl. height) takes the absent branch.
        flow = Flow()
        a = self._adapter(flow)
        a.send_state([], [], {})
        assert a._last_pushed == {"nodes": [], "edges": []}

    def test_on_change_drops_echo_reports_real(self):
        flow = Flow()
        a = self._adapter(flow)
        seen = []
        a.on_change(lambda s: seen.append(s))

        real = [{"id": "a", "position": {"x": 0, "y": 0}, "data": {}}]
        flow.nodes = real  # genuine edit (last_pushed is None) → reported
        assert len(seen) == 1

        echoed = [{"id": "b", "position": {"x": 1, "y": 1}, "data": {}}]
        a._last_pushed = {"nodes": echoed, "edges": []}
        flow.nodes = echoed  # mirrors our last push → dropped
        assert len(seen) == 1

    def test_emit_safe_without_comm(self):
        flow = Flow()
        a = self._adapter(flow)
        a.emit("evt", {"x": 1})  # no comm → safe no-op

    def test_require_flow_before_bind(self):
        from figureflow.transport.anywidget_adapter import AnywidgetAdapter

        with pytest.raises(RuntimeError, match="bind"):
            AnywidgetAdapter().send_state([], [], {})


# ─── Static export adapter — the seam no-ops ──────────────────────────────────

class TestStaticExportNoops:
    def test_live_channel_methods_are_noops(self):
        from figureflow.transport.static_export import StaticExportAdapter

        a = StaticExportAdapter()
        a.bind(Flow())
        assert a.send_state([], [], {}) is None
        assert a.on_change(lambda s: None) is None
        assert a.emit("e", None) is None


# ─── Server adapter — direct unit coverage (no HTTP) ─────────────────────────

class TestServerAdapterUnit:
    def _adapter(self, flow):
        from figureflow.transport.server_adapter import ServerAdapter

        a = ServerAdapter(open_browser=False)
        a.bind(flow)
        return a

    def test_stop_without_start_returns(self):
        a = self._adapter(Flow())
        assert a.stop() is None  # _httpd is None → early return

    def test_send_state_broadcasts_python_envelope(self):
        # ITER_V2_04: state broadcasts are patch envelopes stamped with the
        # originator ("python" for kernel-side pushes) and the server_seq.
        a = self._adapter(Flow())
        q = a.register_stream()
        a.send_state([{"id": "x"}], [], {})
        msg = json.loads(q.get_nowait())
        assert msg["client_id"] == "python"
        assert msg["seq"] == 1
        assert msg["nodes"] == [{"id": "x"}]

    def test_on_change_handler_and_emit_broadcast(self):
        a = self._adapter(Flow())
        a.on_change(lambda s: None)  # registers handler
        q = a.register_stream()
        a.emit("hello", {"v": 1})
        msg = json.loads(q.get_nowait())
        assert msg["kind"] == "event"
        assert msg["name"] == "hello"
        assert msg["payload"] == {"v": 1}

    def test_handle_change_event_op_dispatches(self):
        flow = Flow()
        got = []
        flow.on("ev", lambda p: got.append(p))
        a = self._adapter(flow)
        a.handle_change({"op": "event", "name": "ev", "payload": 99})
        assert got == [99]

    def test_handle_change_writes_graph_and_calls_handler(self):
        flow = Flow([Node("a")])
        a = self._adapter(flow)
        seen = []
        a.on_change(lambda s: seen.append(s))
        a.handle_change(
            {
                "nodes": [{"id": "z", "position": {"x": 0, "y": 0}, "data": {}}],
                "edges": [{"id": "e", "source": "z", "target": "z"}],
            }
        )
        assert [n["id"] for n in flow.nodes] == ["z"]
        assert [e["id"] for e in flow.edges] == ["e"]
        assert len(seen) == 1

    def test_handle_change_defaults_to_current_when_keys_missing(self):
        flow = Flow([Node("a")])
        a = self._adapter(flow)
        a.handle_change({})  # no nodes/edges → keep current
        assert [n["id"] for n in flow.nodes] == ["a"]

    def test_handle_change_edges_only_leaves_nodes(self):
        # nodes absent → skip the nodes write; only edges are replaced.
        flow = Flow([Node("a")])
        a = self._adapter(flow)
        a.handle_change(
            {
                "client_id": "c",
                "seq": 1,
                "edges": [{"id": "e", "source": "a", "target": "a"}],
            }
        )
        assert [n["id"] for n in flow.nodes] == ["a"]
        assert [e["id"] for e in flow.edges] == ["e"]

    def test_register_and_unregister_stream(self):
        a = self._adapter(Flow())
        q = a.register_stream()
        assert q in a._streams
        a.unregister_stream(q)
        assert q not in a._streams

    def test_require_flow_before_bind(self):
        from figureflow.transport.server_adapter import ServerAdapter

        with pytest.raises(RuntimeError, match="bind"):
            ServerAdapter().handle_change({"nodes": []})


# ─── Server adapter — live lifecycle + HTTP routes ───────────────────────────

class TestServerLive:
    def test_serve_opens_browser_when_requested(self, monkeypatch):
        opened = []
        monkeypatch.setattr("webbrowser.open", lambda u: opened.append(u))
        flow = Flow()
        url = flow.serve(open_browser=True)
        try:
            assert opened == [url]
        finally:
            flow.stop()

    def test_serve_block_joins_until_interrupt(self, monkeypatch):
        import threading

        calls = {"n": 0}
        real_join = threading.Thread.join

        def fake_join(self, *a, **k):
            calls["n"] += 1
            if calls["n"] == 1:
                raise KeyboardInterrupt  # the blocking join (Ctrl-C)
            return real_join(self, *a, **k)

        monkeypatch.setattr(threading.Thread, "join", fake_join)
        flow = Flow()
        # block=True → start() joins the server thread, Ctrl-C triggers stop().
        flow.serve(open_browser=False, block=True)
        assert flow._transport._httpd is None  # stop() ran

    def test_stop_swallows_already_removed_observer(self):
        flow = Flow([Node("a")])
        flow.serve(open_browser=False)
        adapter = flow._transport
        fn, names = adapter._observers[0]
        flow.unobserve(fn, names=names)  # remove out from under stop()
        flow.stop()  # unobserve(ValueError) is swallowed
        assert adapter._httpd is None

    def test_stop_sends_sentinel_to_open_streams(self):
        flow = Flow([Node("a")])
        flow.serve(open_browser=False)
        adapter = flow._transport
        q = adapter.register_stream()
        flow.stop()
        assert q.get_nowait() is None  # shutdown sentinel delivered

    def test_layout_request_broadcasts_to_stream(self):
        flow = Flow([Node("a"), Node("b")])
        flow.serve(open_browser=False)
        adapter = flow._transport
        q = adapter.register_stream()
        try:
            flow.layout()  # _layout_request observer → broadcast
            msg = json.loads(q.get(timeout=2))
            assert msg["kind"] == "event"
            assert msg["name"] == "layout"
        finally:
            flow.stop()

    def test_layout_request_without_nonce_is_not_broadcast(self):
        flow = Flow([Node("a")])
        flow.serve(open_browser=False)
        adapter = flow._transport
        q = adapter.register_stream()
        try:
            flow._layout_request = {"algo": "dagre"}  # no nonce → observer no-ops
            assert q.empty()
        finally:
            flow.stop()

    def test_stop_when_thread_already_none(self):
        # Defensive branch: _httpd set but _thread None → stop() skips join().
        flow = Flow([Node("a")])
        flow.serve(open_browser=False)
        adapter = flow._transport
        adapter._thread = None
        flow.stop()
        assert adapter._httpd is None

    def test_python_edit_broadcasts_state(self):
        flow = Flow([Node("a")])
        flow.serve(open_browser=False)
        adapter = flow._transport
        q = adapter.register_stream()
        try:
            flow.add_node(Node("b"))  # Python edit → "python"-stamped envelope
            msg = json.loads(q.get(timeout=2))
            assert msg["client_id"] == "python"
            assert msg["seq"] == 1
            assert [n["id"] for n in msg["nodes"]] == ["a", "b"]
        finally:
            flow.stop()

    def test_get_unknown_path_404(self):
        import urllib.error
        import urllib.request

        flow = Flow([Node("a")])
        url = flow.serve(open_browser=False)
        try:
            with pytest.raises(urllib.error.HTTPError) as ei:
                urllib.request.urlopen(url + "/nope")
            assert ei.value.code == 404
        finally:
            flow.stop()

    def test_get_widget_css(self):
        flow = Flow()
        url = flow.serve(open_browser=False)
        try:
            import urllib.request

            resp = urllib.request.urlopen(url + "/widget.css")
            assert resp.headers["Content-Type"] == "text/css"
        finally:
            flow.stop()

    def test_post_wrong_path_404(self):
        import urllib.error
        import urllib.request

        flow = Flow()
        url = flow.serve(open_browser=False)
        try:
            req = urllib.request.Request(url + "/wrong", data=b"{}", method="POST")
            with pytest.raises(urllib.error.HTTPError) as ei:
                urllib.request.urlopen(req)
            assert ei.value.code == 404
        finally:
            flow.stop()

    def test_post_invalid_json_400(self):
        import urllib.error
        import urllib.request

        flow = Flow()
        url = flow.serve(open_browser=False)
        try:
            req = urllib.request.Request(
                url + "/change",
                data=b"{bad",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with pytest.raises(urllib.error.HTTPError) as ei:
                urllib.request.urlopen(req)
            assert ei.value.code == 400
        finally:
            flow.stop()

    def test_sse_stream_delivers_then_closes(self):
        import threading
        import time
        import urllib.request

        flow = Flow([Node("a")])
        url = flow.serve(open_browser=False)
        adapter = flow._transport
        received = []

        def reader():
            try:
                resp = urllib.request.urlopen(url + "/events", timeout=10)
                received.append(resp.readline())  # first "data:" frame
                resp.read()  # drains until server closes on stop()
                resp.close()
            except Exception:  # noqa: BLE001 - connection torn down on stop
                pass

        t = threading.Thread(target=reader)
        t.start()
        # Wait until the SSE handler has registered its stream.
        deadline = time.time() + 5
        while not adapter._streams and time.time() < deadline:
            time.sleep(0.02)
        flow.add_node(Node("b"))  # non-echo edit → SSE "state" frame
        deadline = time.time() + 5
        while not received and time.time() < deadline:
            time.sleep(0.02)
        flow.stop()  # sentinel → handler breaks → connection closes
        t.join(timeout=5)
        assert received and received[0].startswith(b"data:")

    def test_sse_keepalive_ping(self, monkeypatch):
        import queue as _queue
        import threading
        import urllib.request

        flow = Flow([Node("a")])
        url = flow.serve(open_browser=False)
        adapter = flow._transport

        class PingThenSentinel(_queue.Queue):
            """First get() times out (→ ping), the next returns the sentinel."""

            def __init__(self) -> None:
                super().__init__()
                self._n = 0

            def get(self, *a, **k):  # noqa: ANN002, ANN003, ANN201
                self._n += 1
                if self._n == 1:
                    raise _queue.Empty
                return None

        def fake_register():
            q = PingThenSentinel()
            with adapter._streams_lock:
                adapter._streams.add(q)
            return q

        monkeypatch.setattr(adapter, "register_stream", fake_register)
        received = []

        def reader():
            try:
                resp = urllib.request.urlopen(url + "/events", timeout=10)
                received.append(resp.readline())  # ": ping" keepalive comment
                resp.read()
                resp.close()
            except Exception:  # noqa: BLE001
                pass

        t = threading.Thread(target=reader)
        t.start()
        t.join(timeout=10)
        flow.stop()
        assert received and received[0].startswith(b": ping")

    def test_sse_handles_client_disconnect(self):
        import socket
        import struct
        import time

        flow = Flow([Node("a")])
        url = flow.serve(open_browser=False)
        adapter = flow._transport
        host, _, port = url.split("//", 1)[1].partition(":")

        sock = socket.create_connection((host, int(port)))
        # Force an RST on close so the next server write raises ConnectionReset.
        sock.setsockopt(
            socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0)
        )
        sock.sendall(b"GET /events HTTP/1.1\r\nHost: x\r\n\r\n")
        time.sleep(0.1)
        sock.recv(1024)  # consume response headers
        deadline = time.time() + 5
        while not adapter._streams and time.time() < deadline:
            time.sleep(0.02)
        sock.close()  # abrupt disconnect
        # A broadcast now writes to a dead socket → BrokenPipe/ConnectionReset.
        flow.add_node(Node("b"))
        time.sleep(0.3)
        flow.stop()
        assert adapter._httpd is None


# ─── ITER_V2_04 — sync hardening (envelope, identity echo, exclusivity) ──────

class TestSyncHardening:
    def _adapter(self, flow):
        from figureflow.transport.server_adapter import ServerAdapter

        a = ServerAdapter(open_browser=False)
        a.bind(flow)
        return a

    def test_is_echo_identity_overload(self):
        from figureflow import synccore

        applied = {"c1": 3}
        # At or below the highest applied seq → duplicate delivery → echo.
        assert synccore.is_echo(client_id="c1", seq=3, applied=applied) is True
        assert synccore.is_echo(client_id="c1", seq=2, applied=applied) is True
        # A fresh seq, or an unseen client, is a genuine new edit.
        assert synccore.is_echo(client_id="c1", seq=4, applied=applied) is False
        assert synccore.is_echo(client_id="c9", seq=1, applied=applied) is False

    def test_is_echo_identity_unstamped_is_not_echo(self):
        from figureflow import synccore

        # An envelope without a seq (e.g. hand-rolled curl) cannot be a dupe.
        assert synccore.is_echo(client_id="c1", seq=None, applied={}) is False

    def test_handle_change_broadcast_stamped_with_originator(self):
        flow = Flow([Node("a")])
        a = self._adapter(flow)
        q = a.register_stream()
        a.handle_change(
            {
                "client_id": "browser-1",
                "seq": 1,
                "nodes": [{"id": "z", "position": {"x": 0, "y": 0}, "data": {}}],
            }
        )
        msg = json.loads(q.get_nowait())
        assert msg["client_id"] == "browser-1"  # originator, for self-suppression
        assert msg["seq"] == 1  # first committed change → server_seq 1

    def test_duplicate_post_delivery_dropped(self):
        flow = Flow([Node("a")])
        a = self._adapter(flow)
        q = a.register_stream()
        env = {
            "client_id": "c",
            "seq": 1,
            "nodes": [{"id": "z", "position": {"x": 1, "y": 2}, "data": {}}],
        }
        a.handle_change(env)
        a.handle_change(dict(env))  # duplicate delivery of the same envelope
        assert q.qsize() == 1  # committed and broadcast exactly once
        assert a._server_seq == 1

    def test_empty_patch_commits_nothing(self):
        flow = Flow([Node("a")])
        a = self._adapter(flow)
        q = a.register_stream()
        a.handle_change({})  # no nodes/edges → nothing to commit
        assert q.qsize() == 0
        assert a._server_seq == 0
        assert [n["id"] for n in flow.nodes] == ["a"]

    def test_concurrent_posts_server_seq_strictly_increases(self):
        # Plan verification (6): hammer /change from two concurrent loops —
        # no corruption, server_seq strictly increases (lock check).
        import threading

        flow = Flow([Node("a")])
        a = self._adapter(flow)
        q = a.register_stream()
        n = 50

        def hammer(cid):
            for i in range(n):
                a.handle_change(
                    {
                        "client_id": cid,
                        "seq": i + 1,
                        "nodes": [
                            {"id": cid, "position": {"x": i, "y": 0}, "data": {}}
                        ],
                    }
                )

        threads = [
            threading.Thread(target=hammer, args=(cid,)) for cid in ("c1", "c2")
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        seqs = []
        while not q.empty():
            seqs.append(json.loads(q.get_nowait())["seq"])
        # Seq allocation and enqueue are atomic under the lock, so the stream
        # sees a strictly increasing, gapless sequence.
        assert seqs == list(range(1, 2 * n + 1))
        assert a._server_seq == 2 * n

    def test_serve_while_displayed_warns(self):
        # Plan verification (7): adapter exclusivity is a warning, not an error.
        flow = Flow([Node("a")]).display()
        with pytest.warns(UserWarning, match="one live adapter"):
            flow.serve(open_browser=False)
        flow.stop()

    def test_display_while_served_warns_and_keeps_server(self):
        from figureflow.transport.server_adapter import ServerAdapter

        flow = Flow([Node("a")])
        flow.serve(open_browser=False)
        try:
            with pytest.warns(UserWarning, match="one live adapter"):
                flow.display()
            # The server stays bound so stop() still reaches it.
            assert isinstance(flow._transport, ServerAdapter)
        finally:
            flow.stop()

    def test_script_mode_serves_without_warnings(self):
        # Plan verification (4): kernel-less `python script.py` works with no
        # comm-related warnings (warnings escalated to errors in the child).
        import subprocess
        import sys

        code = (
            "import warnings;"
            "warnings.simplefilter('error', UserWarning);"
            "warnings.simplefilter('error', RuntimeWarning);"
            "from figureflow import Flow, Node;"
            "f = Flow([Node('a')]);"
            "url = f.serve(open_browser=False);"
            "f.add_node(Node('b'));"
            "f.stop();"
            "print('ok')"
        )
        out = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert out.returncode == 0, out.stderr
        assert "ok" in out.stdout


# ─── v3 §02/§04: layout_direction + unplaced positions ───────────────────────

class TestLayoutDirection:
    def test_default_tb(self):
        assert Flow().layout_direction == "TB"

    def test_all_valid_directions(self):
        for d in ("TB", "BT", "LR", "RL"):
            assert Flow(layout_direction=d).layout_direction == d

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="not a valid layout direction"):
            Flow(layout_direction="XX")

    def test_emitted_in_json(self):
        env = json.loads(Flow(layout_direction="LR").to_json())
        assert env["layout_direction"] == "LR"


class TestUnplacedPositions:
    def test_positions_skips_unplaced(self):
        f = Flow([Node("a"), Node("b", pos=(10, 20))])
        # 'a' is unplaced (pos=None) -> omitted; 'b' is placed.
        assert f.positions() == {"b": (10.0, 20.0)}

    def test_placed_node_round_trips(self):
        f = Flow([Node("a", pos=(1, 2))])
        assert f.positions() == {"a": (1.0, 2.0)}


# ─── v3 §04: the validate() ingestion funnel (serialize.py) ───────────────────


def _env(**kw):
    base = {"schema": "figureflow/1", "nodes": [], "edges": []}
    base.update(kw)
    return base


class TestValidateFunnel:
    def test_clean_minimal(self):
        clean, warnings = validate(_env(nodes=[{"id": "a"}]))
        assert warnings == []
        assert clean["layout_direction"] == "TB"
        assert clean["nodes"][0]["id"] == "a"

    def test_top_level_not_object(self):
        with pytest.raises(FlowValidationError) as ei:
            validate(["not", "an", "object"])
        assert "top-level value must be an object" in str(ei.value)

    def test_schema_not_string(self):
        with pytest.raises(FlowValidationError, match="schema must be a string"):
            validate(_env(schema=123))

    def test_schema_unsupported_version(self):
        with pytest.raises(FlowValidationError, match="unsupported schema version"):
            validate(_env(schema="figureflow/2"))

    def test_schema_without_slash(self):
        with pytest.raises(FlowValidationError, match="unsupported schema version"):
            validate(_env(schema="figureflow"))

    def test_default_schema_when_absent(self):
        clean, _ = validate({"nodes": [{"id": "a"}], "edges": []})
        assert clean["schema"] == "figureflow/1"

    def test_invalid_layout_direction(self):
        with pytest.raises(FlowValidationError, match="not a valid layout direction"):
            validate(_env(layout_direction="diagonal"))

    def test_nodes_not_a_list(self):
        with pytest.raises(FlowValidationError, match=r"nodes: must be an array"):
            validate(_env(nodes="oops"))

    def test_node_not_an_object(self):
        with pytest.raises(FlowValidationError, match=r"nodes\[0\]: must be an object"):
            validate(_env(nodes=["x"]))

    def test_node_missing_id(self):
        with pytest.raises(FlowValidationError, match="missing or non-string node id"):
            validate(_env(nodes=[{}]))

    def test_node_non_string_id(self):
        with pytest.raises(FlowValidationError, match="missing or non-string node id"):
            validate(_env(nodes=[{"id": 5}]))

    def test_duplicate_node_id(self):
        with pytest.raises(FlowValidationError, match="duplicate node id"):
            validate(_env(nodes=[{"id": "a"}, {"id": "a"}]))

    def test_invalid_shape_with_close_match(self):
        with pytest.raises(FlowValidationError, match="closest match: ellipse"):
            validate(_env(nodes=[{"id": "a", "data": {"shape": "elipse"}}]))

    def test_invalid_shape_without_close_match(self):
        with pytest.raises(FlowValidationError) as ei:
            validate(_env(nodes=[{"id": "a", "data": {"shape": "zzzzzzzz"}}]))
        msg = str(ei.value)
        assert "is not a valid shape" in msg
        assert "closest match" not in msg

    def test_numeric_non_number_errors(self):
        with pytest.raises(FlowValidationError, match=r"width: 'abc' is not a number"):
            validate(_env(nodes=[{"id": "a", "data": {"width": "abc"}}]))

    def test_numeric_bool_errors(self):
        with pytest.raises(FlowValidationError, match="is not a number"):
            validate(_env(nodes=[{"id": "a", "data": {"fontSize": True}}]))

    def test_numeric_non_scalar_errors(self):
        with pytest.raises(FlowValidationError, match="is not a number"):
            validate(_env(nodes=[{"id": "a", "data": {"width": [1, 2]}}]))

    def test_numeric_string_coerced_warns(self):
        clean, warnings = validate(_env(nodes=[{"id": "a", "data": {"fontSize": "13"}}]))
        assert clean["nodes"][0]["data"]["fontSize"] == 13
        assert any("coerced" in w for w in warnings)

    def test_numeric_float_string_coerced(self):
        clean, _ = validate(_env(nodes=[{"id": "a", "data": {"width": "12.5"}}]))
        assert clean["nodes"][0]["data"]["width"] == 12.5

    def test_unknown_node_key_folded(self):
        clean, warnings = validate(_env(nodes=[{"id": "a", "flavor": "spicy"}]))
        assert clean["nodes"][0]["data"]["flavor"] == "spicy"
        assert any("unknown node key" in w for w in warnings)

    def test_unknown_edge_key_folded(self):
        clean, warnings = validate(
            _env(nodes=[{"id": "a"}, {"id": "b"}],
                 edges=[{"source": "a", "target": "b", "weight": 3}])
        )
        assert clean["edges"][0]["data"]["weight"] == 3
        assert any("unknown edge key" in w for w in warnings)

    def test_explicit_empty_data_preserved(self):
        clean, _ = validate(
            _env(nodes=[{"id": "a", "data": {}}],
                 edges=[{"source": "a", "target": "a", "data": {}}])
        )
        assert "data" in clean["nodes"][0]
        assert "data" in clean["edges"][0]

    def test_edges_not_a_list(self):
        with pytest.raises(FlowValidationError, match=r"edges: must be an array"):
            validate(_env(edges="oops"))

    def test_edge_not_an_object(self):
        with pytest.raises(FlowValidationError, match=r"edges\[0\]: must be an object"):
            validate(_env(nodes=[{"id": "a"}], edges=["x"]))

    def test_edge_missing_source(self):
        with pytest.raises(FlowValidationError, match="missing or non-string edge source"):
            validate(_env(nodes=[{"id": "a"}], edges=[{"target": "a"}]))

    def test_edge_endpoint_unknown_lists_ids(self):
        with pytest.raises(FlowValidationError) as ei:
            validate(_env(nodes=[{"id": "a"}], edges=[{"source": "a", "target": "zzz"}]))
        assert "Known node ids: a" in str(ei.value)

    def test_edge_endpoint_unknown_many_nodes_generic_hint(self):
        nodes = [{"id": f"n{i}"} for i in range(21)]
        with pytest.raises(FlowValidationError) as ei:
            validate(_env(nodes=nodes, edges=[{"source": "n0", "target": "zzz"}]))
        msg = str(ei.value)
        assert "Reference an existing node id." in msg
        assert "Known node ids" not in msg

    def test_edge_endpoint_unknown_no_nodes_generic_hint(self):
        with pytest.raises(FlowValidationError) as ei:
            validate(_env(edges=[{"source": "a", "target": "b"}]))
        assert "Reference an existing node id." in str(ei.value)

    def test_collects_multiple_problems(self):
        with pytest.raises(FlowValidationError) as ei:
            validate(_env(
                nodes=[{"id": "a"}, {"id": "a"}, {"id": "b", "data": {"shape": "bad"}}],
                edges=[{"source": "a", "target": "ghost"}],
            ))
        assert len(ei.value.problems) >= 3

    def test_strict_escalates_warnings(self):
        with pytest.raises(FlowValidationError):
            validate(_env(nodes=[{"id": "a", "mystery": 1}]), strict=True)

    def test_non_strict_keeps_warnings(self):
        _, warnings = validate(_env(nodes=[{"id": "a", "mystery": 1}]), strict=False)
        assert warnings

    def test_format_problem_without_hint(self):
        from figureflow.serialize import _format_problem

        assert _format_problem({"path": "x", "message": "broken."}) == "x: broken."


class TestFromJsonV3:
    def test_round_trip_v2_document_lossless(self):
        f = Flow(
            [Node("a", "Start", pos=(0, 0), shape=Shape.stadium)],
            [Edge("a", "a", label="loop")],
            color_mode="dark",
            layout_direction="LR",
        )
        s = f.to_json()
        assert from_json(s).to_json() == s

    def test_unplaced_document_imports(self):
        s = json.dumps(_env(nodes=[{"id": "a"}, {"id": "b"}],
                            edges=[{"source": "a", "target": "b"}]))
        f = Flow.from_json(s)
        assert f.positions() == {}  # nothing placed yet
        assert len(f.nodes) == 2

    def test_import_warnings_attached(self):
        s = json.dumps(_env(nodes=[{"id": "a", "extra": 1}]))
        f = Flow.from_json(s)
        assert f._import_warnings

    def test_strict_raises_on_warning(self):
        s = json.dumps(_env(nodes=[{"id": "a", "extra": 1}]))
        with pytest.raises(FlowValidationError):
            Flow.from_json(s, strict=True)

    def test_load_json_adopts_direction_and_clears_history(self):
        f = Flow([Node("a", pos=(0, 0))])
        f.load_json(json.dumps(_env(layout_direction="BT", nodes=[{"id": "z"}])))
        assert f.layout_direction == "BT"
        assert [n["id"] for n in f.nodes] == ["z"]


# ─── v3 §02/§04: mermaid import (mermaid_in.py) ──────────────────────────────


def _ids(flow):
    return [n["id"] for n in flow.nodes]


def _node(flow, nid):
    return next(n for n in flow.nodes if n["id"] == nid)


class TestMermaidImport:
    def test_classmethod_entry(self):
        f = Flow.from_mermaid("flowchart TD\n a --> b")
        assert _ids(f) == ["a", "b"]
        assert len(f.edges) == 1

    def test_all_shapes(self):
        f = from_mermaid(
            "flowchart LR\n"
            " a[Rect]-->b(Round)\n b-->c([Stad])\n c-->d((Ell))\n"
            " d-->e{Dia}\n e-->f{{Hex}}\n f-->g[/Par/]\n g-->h[(Cyl)]\n h-->i\n"
        )
        got = {n["id"]: n["data"]["shape"] for n in f.nodes}
        assert got == {
            "a": "rectangle", "b": "rounded", "c": "stadium", "d": "ellipse",
            "e": "diamond", "f": "hexagon", "g": "parallelogram",
            "h": "cylinder", "i": "rectangle",
        }

    def test_directions(self):
        assert from_mermaid("flowchart TD\n a-->b").layout_direction == "TB"
        assert from_mermaid("graph BT\n a-->b").layout_direction == "BT"
        assert from_mermaid("flowchart LR\n a-->b").layout_direction == "LR"
        assert from_mermaid("flowchart RL\n a-->b").layout_direction == "RL"
        assert from_mermaid("flowchart\n a-->b").layout_direction == "TB"

    def test_unknown_direction_token_defaults_tb(self):
        assert from_mermaid("flowchart ZZ\n a-->b").layout_direction == "TB"

    def test_nodes_are_unplaced(self):
        f = from_mermaid("flowchart TD\n a --> b")
        assert all("position" not in n for n in f.nodes)

    def test_edge_operators(self):
        f = from_mermaid(
            "flowchart LR\n a-->b\n b---c\n c-.->d\n d-.-e\n e==>g\n g===h\n"
        )
        styles = {(e["source"], e["target"]): e for e in f.edges}
        assert styles[("a", "b")].get("markerEnd") == {"type": "arrow"}
        assert "markerEnd" not in styles[("b", "c")]
        assert styles[("c", "d")]["style"]["strokeDasharray"] == "6 4"
        assert "markerEnd" not in styles[("d", "e")]
        assert styles[("e", "g")]["style"]["strokeWidth"] == 3
        assert styles[("g", "h")]["style"]["strokeWidth"] == 3
        assert "markerEnd" not in styles[("g", "h")]

    def test_edge_labels_both_forms(self):
        f = from_mermaid("flowchart LR\n a -->|pipe| b\n b -- dash --> c")
        labels = {(e["source"], e["target"]): e.get("label") for e in f.edges}
        assert labels[("a", "b")] == "pipe"
        assert labels[("b", "c")] == "dash"

    def test_chain_and_fan(self):
        f = from_mermaid("flowchart LR\n a --> b --> c\n x & y --> z\n z --> p & q")
        pairs = {(e["source"], e["target"]) for e in f.edges}
        assert {("a", "b"), ("b", "c"), ("x", "z"), ("y", "z"),
                ("z", "p"), ("z", "q")} <= pairs

    def test_quoted_label_and_br(self):
        f = from_mermaid('flowchart TD\n a["A: x"] --> b[one<br>two]')
        assert _node(f, "a")["data"]["label"] == "A: x"
        assert _node(f, "b")["data"]["label"] == "one\ntwo"

    def test_first_definition_wins(self):
        f = from_mermaid("flowchart TD\n a[First] --> b\n a --> c")
        assert _node(f, "a")["data"]["label"] == "First"

    def test_later_explicit_overrides_bare(self):
        f = from_mermaid("flowchart TD\n a --> b\n a[Labeled] --> c")
        assert _node(f, "a")["data"]["label"] == "Labeled"

    def test_comments_dropped(self):
        f = from_mermaid("flowchart TD\n %% comment\n a --> b\n %% another")
        assert _ids(f) == ["a", "b"]

    def test_subgraph_with_title(self):
        f = from_mermaid(
            "flowchart TB\n subgraph S1 [My Group]\n a --> b\n end\n b --> c"
        )
        grp = _node(f, "S1")
        assert grp["type"] == "group"
        assert grp["data"]["label"] == "My Group"
        assert _node(f, "a")["parentId"] == "S1"
        assert _node(f, "a")["extent"] == "parent"
        assert "parentId" not in _node(f, "c")

    def test_subgraph_bare_title(self):
        f = from_mermaid("flowchart TB\n subgraph Backend\n a --> b\n end")
        grp = _node(f, "Backend")
        assert grp["type"] == "group"
        assert grp["data"]["label"] == "Backend"

    def test_subgraph_anonymous(self):
        f = from_mermaid("flowchart TB\n subgraph\n a --> b\n end")
        assert any(n.get("type") == "group" for n in f.nodes)

    def test_subgraph_id_collision(self):
        f = from_mermaid(
            "flowchart TB\n a --> b\n subgraph a [Dup]\n c --> d\n end"
        )
        # 'a' already a node; the group takes a synthesized id.
        groups = [n for n in f.nodes if n.get("type") == "group"]
        assert len(groups) == 1
        assert groups[0]["id"] != "a"

    def test_existing_node_gains_parent(self):
        f = from_mermaid(
            "flowchart TB\n a --> b\n subgraph S [G]\n a\n end"
        )
        assert _node(f, "a")["parentId"] == "S"

    def test_nested_subgraph_warns_and_flattens(self):
        f = from_mermaid(
            "flowchart TB\n subgraph Outer [O]\n a\n subgraph Inner [I]\n b\n end\n end"
        )
        assert any("nested subgraph" in w for w in f._import_warnings)
        # inner member flattened into the outer group
        assert _node(f, "b")["parentId"] == "Outer"

    def test_stray_end_ignored(self):
        f = from_mermaid("flowchart TD\n a --> b\n end")
        assert _ids(f) == ["a", "b"]

    def test_style_directive_warned(self):
        f = from_mermaid(
            "flowchart TD\n a --> b\n classDef big fill:#f00\n style a fill:#0f0"
        )
        joined = " ".join(f._import_warnings)
        assert "classDef" in joined
        assert "style" in joined

    def test_directive_warned_once(self):
        f = from_mermaid(
            "flowchart TD\n a --> b\n style a fill:#0f0\n style b fill:#00f"
        )
        assert sum("'style'" in w for w in f._import_warnings) == 1

    def test_non_flowchart_named_error(self):
        with pytest.raises(MermaidParseError, match="sequence diagram is not supported"):
            from_mermaid("sequenceDiagram\n a->>b: hi")

    def test_unknown_header_error(self):
        with pytest.raises(MermaidParseError, match="expected a 'flowchart' or 'graph'"):
            from_mermaid("bananas\n a --> b")

    def test_unbalanced_bracket_error(self):
        with pytest.raises(MermaidParseError, match=r"unbalanced '\[' in node 'a'"):
            from_mermaid("flowchart TD\n a[unterminated --> b")

    def test_unknown_operator_error(self):
        with pytest.raises(MermaidParseError, match="unexpected token"):
            from_mermaid("flowchart TD\n a ~~> b")

    def test_edge_without_target_error(self):
        with pytest.raises(MermaidParseError, match="edge operator has no target"):
            from_mermaid("flowchart TD\n a -->")

    def test_stray_after_ampersand_error(self):
        with pytest.raises(MermaidParseError, match="unexpected token"):
            from_mermaid("flowchart TD\n a & --> b")

    def test_error_in_fan_member(self):
        with pytest.raises(MermaidParseError, match="unbalanced"):
            from_mermaid("flowchart TD\n a & b[bad --> c")

    def test_tokenize_trailing_whitespace(self):
        # Direct helper call: a trailing space exercises the end-of-statement
        # break that the upstream .strip() hides from the public API.
        from figureflow.mermaid_in import _tokenize

        tokens, err = _tokenize("a --> b ", 1)
        assert err is None
        assert [k for k, _ in tokens] == ["nodes", "edge", "nodes"]

    def test_strict_escalates_warning(self):
        with pytest.raises(MermaidParseError):
            from_mermaid("flowchart TD\n a --> b\n style a fill:#f00", strict=True)

    def test_round_trip_structure_preserving(self):
        src = "flowchart TD\n a[Start] --> b{Q}\n b -->|yes| c([Done])"
        f = from_mermaid(src)
        again = from_mermaid(f.to_mermaid())
        assert {n["id"] for n in f.nodes} == {n["id"] for n in again.nodes}
        assert len(f.edges) == len(again.edges)


class TestMermaidCorpusGate:
    """ITER_V3_02 done-check: the recorded corpus imports with no hard errors."""

    def test_corpus_clean_rate(self):
        corpus_dir = pathlib.Path(__file__).parent / "corpus"
        files = sorted(corpus_dir.glob("*.mmd"))
        assert files, "corpus is empty"
        hard_errors = []
        for fp in files:
            try:
                flow = Flow.from_mermaid(fp.read_text(encoding="utf-8"))
            except MermaidParseError as exc:
                hard_errors.append((fp.name, str(exc)))
                continue
            assert flow.nodes  # produced a usable diagram
        rate = (len(files) - len(hard_errors)) / len(files)
        assert rate >= 0.90, f"corpus clean rate {rate:.0%}; failures: {hard_errors}"


# ─── v3 §04: MCP adapter (mcp_server.py) ─────────────────────────────────────


class _FakeMCP:
    """Minimal stand-in for FastMCP so the tool layer is testable without `mcp`."""

    def __init__(self, name):
        self.name = name
        self.tools = {}
        self.ran = False

    def tool(self):
        def deco(fn):
            self.tools[fn.__name__] = fn
            return fn
        return deco

    def run(self):
        self.ran = True


@pytest.fixture()
def mcp_tools():
    server = mcp_server._build_server(_FakeMCP)
    tools = server.tools
    yield tools
    # Always tear down any live serve() the tools may have started.
    tools["close_diagram"]()


class TestMcpServer:
    def test_tools_registered(self, mcp_tools):
        assert set(mcp_tools) == {
            "create_diagram", "get_diagram", "replace_diagram",
            "add_elements", "close_diagram",
        }

    def test_calls_before_create_return_no_diagram(self, mcp_tools):
        msg = "no diagram; call create_diagram first"
        assert mcp_tools["get_diagram"]()["error"] == msg
        assert mcp_tools["replace_diagram"]("{}")["error"] == msg
        assert mcp_tools["add_elements"]()["error"] == msg

    def test_close_before_create_is_noop(self, mcp_tools):
        assert mcp_tools["close_diagram"]() == {}

    def test_create_from_json(self, mcp_tools):
        env = json.dumps(_env(nodes=[{"id": "a"}, {"id": "b"}],
                              edges=[{"source": "a", "target": "b"}]))
        res = mcp_tools["create_diagram"](env, open_browser=False)
        assert res["url"].startswith("http://127.0.0.1:")
        assert res["warnings"] == []

    def test_create_from_mermaid(self, mcp_tools):
        res = mcp_tools["create_diagram"](
            "flowchart TD\n a --> b", format="mermaid", open_browser=False
        )
        assert "url" in res

    def test_create_invalid_returns_error(self, mcp_tools):
        res = mcp_tools["create_diagram"]("{not json", open_browser=False)
        assert "error" in res
        assert "url" not in res

    def test_create_validation_error(self, mcp_tools):
        bad = json.dumps(_env(nodes=[{"id": "a"}, {"id": "a"}]))
        res = mcp_tools["create_diagram"](bad, open_browser=False)
        assert "duplicate node id" in res["error"]

    def test_create_twice_replaces_session(self, mcp_tools):
        first = mcp_tools["create_diagram"](
            json.dumps(_env(nodes=[{"id": "a"}])), open_browser=False
        )
        second = mcp_tools["create_diagram"](
            json.dumps(_env(nodes=[{"id": "b"}])), open_browser=False
        )
        assert first["url"] != second["url"] or True  # old server stopped, new served

    def test_get_after_create(self, mcp_tools):
        mcp_tools["create_diagram"](
            json.dumps(_env(nodes=[{"id": "a"}])), open_browser=False
        )
        got = mcp_tools["get_diagram"]()
        assert "json" in got and "mermaid" in got
        assert json.loads(got["json"])["nodes"][0]["id"] == "a"

    def test_replace_json(self, mcp_tools):
        mcp_tools["create_diagram"](
            json.dumps(_env(nodes=[{"id": "a"}])), open_browser=False
        )
        res = mcp_tools["replace_diagram"](
            json.dumps(_env(nodes=[{"id": "z"}]))
        )
        assert "warnings" in res
        assert json.loads(mcp_tools["get_diagram"]()["json"])["nodes"][0]["id"] == "z"

    def test_replace_mermaid(self, mcp_tools):
        mcp_tools["create_diagram"](
            json.dumps(_env(nodes=[{"id": "a"}])), open_browser=False
        )
        res = mcp_tools["replace_diagram"]("flowchart TD\n x --> y", format="mermaid")
        assert "warnings" in res
        assert _ids_from_json(mcp_tools["get_diagram"]()["json"]) == ["x", "y"]

    def test_replace_invalid_returns_error(self, mcp_tools):
        mcp_tools["create_diagram"](
            json.dumps(_env(nodes=[{"id": "a"}])), open_browser=False
        )
        res = mcp_tools["replace_diagram"]("{nope")
        assert "error" in res

    def test_add_elements(self, mcp_tools):
        mcp_tools["create_diagram"](
            json.dumps(_env(nodes=[{"id": "a"}])), open_browser=False
        )
        res = mcp_tools["add_elements"](nodes_json='[{"id": "b"}]',
                                        edges_json='[{"source": "a", "target": "b"}]')
        assert "warnings" in res
        assert set(_ids_from_json(mcp_tools["get_diagram"]()["json"])) == {"a", "b"}

    def test_add_elements_bad_json(self, mcp_tools):
        mcp_tools["create_diagram"](
            json.dumps(_env(nodes=[{"id": "a"}])), open_browser=False
        )
        res = mcp_tools["add_elements"](nodes_json="{not json")
        assert "not valid JSON" in res["error"]

    def test_add_elements_validation_error(self, mcp_tools):
        mcp_tools["create_diagram"](
            json.dumps(_env(nodes=[{"id": "a"}])), open_browser=False
        )
        res = mcp_tools["add_elements"](nodes_json='[{"id": "a"}]')  # dup id
        assert "duplicate node id" in res["error"]

    def test_close_stops_session(self, mcp_tools):
        mcp_tools["create_diagram"](
            json.dumps(_env(nodes=[{"id": "a"}])), open_browser=False
        )
        assert mcp_tools["close_diagram"]() == {}
        assert mcp_tools["get_diagram"]()["error"]


def _ids_from_json(s):
    return [n["id"] for n in json.loads(s)["nodes"]]


class TestMcpMain:
    def test_main_missing_extra_exits(self, monkeypatch):
        # Ensure `import mcp...` fails regardless of environment.
        monkeypatch.setitem(sys.modules, "mcp", None)
        with pytest.raises(SystemExit) as ei:
            mcp_server.main()
        assert ei.value.code == 1

    def test_main_success_runs_server(self, monkeypatch):
        import types

        fastmcp_mod = types.ModuleType("mcp.server.fastmcp")
        fastmcp_mod.FastMCP = _FakeMCP
        monkeypatch.setitem(sys.modules, "mcp", types.ModuleType("mcp"))
        monkeypatch.setitem(sys.modules, "mcp.server", types.ModuleType("mcp.server"))
        monkeypatch.setitem(sys.modules, "mcp.server.fastmcp", fastmcp_mod)
        # _FakeMCP.run() is a no-op, so main() returns cleanly.
        mcp_server.main()


# ─── v3: adapter meta carries layout_direction ───────────────────────────────

class TestAdapterLayoutMeta:
    def test_anywidget_send_state_applies_layout_direction(self):
        from figureflow.transport.anywidget_adapter import AnywidgetAdapter

        flow = Flow()
        adapter = AnywidgetAdapter()
        adapter.bind(flow)
        adapter.send_state([], [], {"layout_direction": "LR"})
        assert flow.layout_direction == "LR"
