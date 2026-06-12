// Shared JS sync-core — the echo-guard, lifted above the adapter fork.
//
// In v1 this guard wrapped model→local application inline in the renderer
// (ITER_03 §05). v2 moves it here unchanged so it still wraps *only* push→local
// application (state Python sent down), never local→push, across every adapter
// (SKELETON_V2 §05, ITER_V2_01 §05). The Python twin lives in synccore.py.
//
// ITER_V2_04: the server adapter's asynchronous round-trip cannot be bracketed
// by this flag, so that adapter drops its own SSE envelopes by client identity
// *before* they reach subscribers (js/adapters/server.js). This flag guard
// stays the anywidget path's mechanism and still wraps only push→local
// application — the suppression predicate is adapter-supplied.

// One echo flag per renderer instance. `markEcho()` is called immediately before
// a `subscribe`-driven setNodes/setEdges; the very next onNodesChange/onEdgesChange
// reads it via `isEcho()` to skip re-committing that applied push, then unconditionally
// clears it with `clearEcho()` — exactly the v1 cycle.
export function createSyncCore() {
  const echo = { current: false };
  return {
    markEcho() {
      echo.current = true;
    },
    isEcho() {
      return echo.current;
    },
    clearEcho() {
      echo.current = false;
    },
  };
}
