// Static JS adapter — frozen, offline, one-way snapshot (ITER_V2_02).
//
// The cheapest consumer of the Transport interface (SKELETON_V2 §05): state is
// baked into a JSON island at write time, so `subscribe` never fires and
// `pushChange` has no network target. Instead it captures client edits in an
// in-memory "current state" that the Download JSON affordance reads, so a user
// who rearranges nodes exports *their* layout, not the original.
//
// `island` is the `serialize.to_json` envelope (ITER_05):
//   { schema, color_mode, fit_view, height, nodes, edges }

export function createStaticTransport(island) {
  // Mutable current state seeded from the baked island.
  const current = {
    nodes: island.nodes || [],
    edges: island.edges || [],
  };

  return {
    getState() {
      return {
        nodes: current.nodes,
        edges: current.edges,
        meta: {
          colorMode: island.color_mode || "light",
          fitView: island.fit_view !== false,
          height: island.height || 480,
          nodeModules: {},
          edgeModules: {},
        },
      };
    },

    // No upstream pushes (no Python behind a file://): register, never fire.
    subscribe() {
      return () => {};
    },

    // No network target — capture the edit so the export reflects it.
    pushChange(patch) {
      if (patch.nodes !== undefined) current.nodes = patch.nodes;
      if (patch.edges !== undefined) current.edges = patch.edges;
    },

    // Custom-component events have no Python to reach.
    sendEvent() {},
    onEvent() {
      return () => {};
    },

    // Capabilities consumed by the renderer's Download JSON button.
    downloadAffordance: true,
    serializeState() {
      // Re-emit a `from_json`-compatible envelope with the current layout.
      return JSON.stringify({
        schema: island.schema || "figureflow/1",
        color_mode: island.color_mode || "light",
        fit_view: island.fit_view !== false,
        height: island.height || 480,
        nodes: current.nodes,
        edges: current.edges,
      });
    },
  };
}
