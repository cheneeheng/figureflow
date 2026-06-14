// Server JS adapter — plain browser, live bidirectional sync (ITER_V2_03,
// hardened by ITER_V2_04).
//
// Satisfies the Transport interface (SKELETON_V2 §05) over the stdlib SSE+POST
// server: SSE GET /events carries Python→browser pushes, fetch POST /change
// carries browser→Python edits. The split is forced by EventSource being
// GET-only and header-less (ITER_V2_03 §05): the upstream needs a body, so it
// can never ride EventSource.
//
// ITER_V2_04 §05 pins the sync contract for this adapter:
//   - Identity: one client_id (crypto.randomUUID) and a local seq counter,
//     minted once per transport; both stamp every pushChange POST envelope.
//   - Echo guard: incoming state envelopes whose client_id equals our own are
//     dropped here, before subscribers — identity suppression replaces the
//     flag guard for this (asynchronous) adapter only; the shared sync-core
//     flag still wraps push→local application in the renderer.
//   - Bootstrap: open /events first, buffer; fetch /state ({server_seq,
//     state}); apply the snapshot; drop buffered envelopes with seq <=
//     snapshot server_seq; apply the rest in seq order; go live. Ordering
//     alone closes the snapshot/stream gap — no replay machinery.
//   - A seq gap in live messages triggers the same /state re-fetch
//     (re-bootstrap is cheap at this scale).
//
// The factory is async and constructed exactly once by the host bootstrap
// (top-level await), so a single EventSource and a single identity exist for
// the page's lifetime; renderer effects only add/remove callbacks, and React
// 18 StrictMode's double-mount never opens a second stream or mints a second
// client_id.

export async function createServerTransport(opts = {}) {
  const base = opts.base || "";
  const clientId = crypto.randomUUID();
  let clientSeq = 0; // local POST counter; the server logs but never interprets it
  let lastServerSeq = -1; // highest server_seq seen (snapshot or envelope)

  // Latest snapshot, kept fresh by SSE pushes and local commits so getState()
  // (used by the synchronous mount and by client-side layout) is current.
  const snapshot = { nodes: [], edges: [], meta: {} };

  const stateSubs = new Set();
  const eventHandlers = {}; // name -> Set(cb)

  // Bootstrap/resync buffering: while true, state envelopes queue up instead
  // of applying, then drain in seq order once the /state snapshot lands.
  let buffering = true;
  let buffer = [];
  let resyncing = false;

  function applySnapshot(wrapped) {
    const state = wrapped.state || {};
    snapshot.nodes = state.nodes || [];
    snapshot.edges = state.edges || [];
    snapshot.meta = {
      colorMode: state.color_mode || "light",
      fitView: state.fit_view !== false,
      height: state.height || 480,
      layoutDirection: state.layout_direction || "TB",
      nodeModules: {},
      edgeModules: {},
    };
    lastServerSeq = wrapped.server_seq || 0;
    stateSubs.forEach((cb) =>
      cb({ nodes: snapshot.nodes, edges: snapshot.edges })
    );
  }

  function applyEnvelope(msg) {
    // {client_id, seq, nodes?, edges?} — full-array replacement (ITER_V2_04 §04).
    if (typeof msg.seq === "number") {
      if (lastServerSeq >= 0 && msg.seq > lastServerSeq + 1) {
        resync(); // missed an event — re-fetch /state instead of repairing
        return;
      }
      if (msg.seq <= lastServerSeq) return; // stale (pre-snapshot) envelope
      lastServerSeq = msg.seq;
    }
    if (msg.client_id === clientId) return; // our own commit echoed back
    if (msg.nodes !== undefined) snapshot.nodes = msg.nodes;
    if (msg.edges !== undefined) snapshot.edges = msg.edges;
    stateSubs.forEach((cb) => cb({ nodes: msg.nodes, edges: msg.edges }));
  }

  async function resync() {
    if (resyncing) return;
    resyncing = true;
    buffering = true;
    buffer = [];
    try {
      const wrapped = await (await fetch(base + "/state")).json();
      applySnapshot(wrapped);
      // Drain synchronously: drop pre-snapshot envelopes, apply the rest in
      // seq order, then go live. No event can interleave mid-block.
      const pending = buffer
        .filter((m) => !(typeof m.seq === "number" && m.seq <= lastServerSeq))
        .sort((a, b) => (a.seq || 0) - (b.seq || 0));
      buffering = false;
      buffer = [];
      resyncing = false;
      pending.forEach(applyEnvelope);
    } catch (err) {
      buffering = false;
      buffer = [];
      resyncing = false;
      console.error("[figureflow] /state bootstrap failed:", err);
    }
  }

  const source = new EventSource(base + "/events");
  source.onmessage = (e) => {
    let msg;
    try {
      msg = JSON.parse(e.data);
    } catch {
      return;
    }
    if (msg.kind === "event") {
      // Custom events carry no seq and bypass buffering/identity entirely.
      (eventHandlers[msg.name] || new Set()).forEach((cb) =>
        cb(msg.payload || {})
      );
      return;
    }
    if (buffering) {
      buffer.push(msg);
      return;
    }
    applyEnvelope(msg);
  };

  function post(body) {
    return fetch(base + "/change", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  }

  // Events-first bootstrap: wait until the stream is actually connected (the
  // server has registered our queue) before snapshotting, then drain. Any
  // residual race is self-healing via the seq-gap resync.
  await new Promise((resolve) => {
    source.addEventListener("open", resolve, { once: true });
    source.addEventListener("error", resolve, { once: true });
  });
  await resync();

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
      // before the (identity-suppressed) server round-trip.
      if (patch.nodes !== undefined) snapshot.nodes = patch.nodes;
      if (patch.edges !== undefined) snapshot.edges = patch.edges;
      clientSeq += 1;
      post({ client_id: clientId, seq: clientSeq, ...patch });
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
