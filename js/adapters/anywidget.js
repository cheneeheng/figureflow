// Anywidget JS adapter — the representative Transport implementation (ITER_V2_01).
//
// Satisfies the JS Transport interface (SKELETON_V2 §05) against anywidget's
// `model.get/set/on`. The renderer never touches `model` directly; it talks only
// to this object, so the same renderer drives the static and server adapters too.
//
// Transport interface:
//   getState()            -> { nodes, edges, meta }
//   subscribe(cb)         -> unsubscribe   (Python pushed new state/meta down)
//   pushChange(patch)     -> void          (a local canvas edit goes up)
//   sendEvent(name, payload) -> void       (custom message up; v1 emit)
//   onEvent(name, cb)     -> unsubscribe   (custom message down; undo/redo/layout)

function readMeta(model) {
  return {
    colorMode: model.get("color_mode") || "light",
    fitView: model.get("fit_view") !== false,
    height: model.get("height") || 480,
    layoutDirection: model.get("layout_direction") || "TB",
    nodeModules: model.get("_node_modules") || {},
    edgeModules: model.get("_edge_modules") || {},
  };
}

export function createAnywidgetTransport(model) {
  return {
    getState() {
      return {
        nodes: model.get("nodes") || [],
        edges: model.get("edges") || [],
        meta: readMeta(model),
      };
    },

    subscribe(cb) {
      // Granular pushes preserve v1's per-channel echo semantics: each trait
      // change delivers just its slice, and the renderer marks an echo per slice.
      const onNodes = () => cb({ nodes: model.get("nodes") || [] });
      const onEdges = () => cb({ edges: model.get("edges") || [] });
      const onMeta = () => cb({ meta: readMeta(model) });
      model.on("change:nodes", onNodes);
      model.on("change:edges", onEdges);
      model.on("change:color_mode", onMeta);
      model.on("change:layout_direction", onMeta);
      model.on("change:_node_modules", onMeta);
      model.on("change:_edge_modules", onMeta);
      return () => {
        model.off("change:nodes", onNodes);
        model.off("change:edges", onEdges);
        model.off("change:color_mode", onMeta);
        model.off("change:layout_direction", onMeta);
        model.off("change:_node_modules", onMeta);
        model.off("change:_edge_modules", onMeta);
      };
    },

    pushChange(patch) {
      // The v1 commit write: set the traits and flush once.
      if (patch.nodes !== undefined) model.set("nodes", patch.nodes);
      if (patch.edges !== undefined) model.set("edges", patch.edges);
      model.save_changes();
    },

    sendEvent(name, payload) {
      model.send({ event: name, payload });
    },

    onEvent(name, cb) {
      // Layout still rides its dedicated trait (Python's layout() is unchanged);
      // every other down-event is a custom comm message (undo/redo/clear_history).
      if (name === "layout") {
        const handler = () => {
          const req = model.get("_layout_request");
          if (req && req.nonce) cb(req);
        };
        model.on("change:_layout_request", handler);
        return () => model.off("change:_layout_request", handler);
      }
      const handler = (_model, msg) => {
        if (msg && msg.type === name) cb(msg);
      };
      model.on("msg:custom", handler);
      return () => model.off("msg:custom", handler);
    },
  };
}
