// Server JS adapter — plain browser, live bidirectional sync (ITER_V2_03).
//
// Satisfies the Transport interface (SKELETON_V2 §05) over the stdlib SSE+POST
// server: SSE GET /events carries Python→browser pushes, fetch POST /change
// carries browser→Python edits. The split is forced by EventSource being
// GET-only and header-less (ITER_V2_03 §05): the upstream needs a body, so it
// can never ride EventSource.
//
// One EventSource is opened eagerly at construction (a single stream for the
// page's lifetime); registering/unregistering renderer effects only add/remove
// callbacks, so React 18 StrictMode's double-mount never opens a second stream.
//
// `initial` is the `/state` snapshot (the `serialize.to_json` envelope) the
// bootstrap fetched before mounting, so `getState()` can answer synchronously.

export function createServerTransport(initial, opts = {}) {
  const base = opts.base || "";

  // Latest snapshot, kept fresh by SSE pushes and local commits so getState()
  // (used by the synchronous mount and by client-side layout) is current.
  const snapshot = {
    nodes: initial.nodes || [],
    edges: initial.edges || [],
    meta: {
      colorMode: initial.color_mode || "light",
      fitView: initial.fit_view !== false,
      height: initial.height || 480,
      nodeModules: {},
      edgeModules: {},
    },
  };

  const stateSubs = new Set();
  const eventHandlers = {}; // name -> Set(cb)

  const source = new EventSource(base + "/events");
  source.onmessage = (e) => {
    let msg;
    try {
      msg = JSON.parse(e.data);
    } catch {
      return;
    }
    if (msg.kind === "state") {
      if (msg.nodes !== undefined) snapshot.nodes = msg.nodes;
      if (msg.edges !== undefined) snapshot.edges = msg.edges;
      stateSubs.forEach((cb) => cb({ nodes: msg.nodes, edges: msg.edges }));
    } else if (msg.kind === "event") {
      (eventHandlers[msg.name] || new Set()).forEach((cb) =>
        cb(msg.payload || {})
      );
    }
  };

  function post(body) {
    return fetch(base + "/change", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  }

  return {
    getState() {
      return {
        nodes: snapshot.nodes,
        edges: snapshot.edges,
        meta: snapshot.meta,
      };
    },

    subscribe(cb) {
      stateSubs.add(cb);
      return () => stateSubs.delete(cb);
    },

    pushChange(patch) {
      // Keep the local snapshot fresh so getState() reflects the edit even
      // before the (echo-suppressed) server round-trip.
      if (patch.nodes !== undefined) snapshot.nodes = patch.nodes;
      if (patch.edges !== undefined) snapshot.edges = patch.edges;
      post(patch);
    },

    sendEvent(name, payload) {
      post({ op: "event", name, payload });
    },

    onEvent(name, cb) {
      const set = (eventHandlers[name] = eventHandlers[name] || new Set());
      set.add(cb);
      return () => set.delete(cb);
    },
  };
}
