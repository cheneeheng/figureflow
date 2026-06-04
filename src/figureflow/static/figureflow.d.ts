/**
 * figureflow custom-component typings (L3 escape hatch).
 *
 * Custom node/edge components are plain JS modules whose default export is a
 * React function component. The bundled figureflow runtime exposes the
 * vendored React instance and xyflow primitives on `globalThis.figureflow`
 * so custom components can share the same React instance without bundling
 * their own — importing "react" directly from a runtime-loaded module would
 * cause the "two Reacts" invalid-hook-call error.
 *
 * Usage in a custom component file:
 *
 *   const { React, xyflow: { Handle, Position } } = globalThis.figureflow;
 *   export default function MyNode({ data, selected, emit }) { ... }
 */

export interface FigureflowGlobal {
  React: typeof import("react");
  xyflow: {
    Handle: React.ComponentType<any>;
    Position: { Top: string; Bottom: string; Left: string; Right: string };
  };
}

declare global {
  var figureflow: FigureflowGlobal;
}

/** Props passed to every custom node component. */
export interface NodeProps<TData = Record<string, unknown>> {
  /** The node's data object (from Python Node.to_dict()["data"]). */
  data: TData;
  /** Whether this node is currently selected on the canvas. */
  selected: boolean;
  /** Send a named event + payload to the Python Flow.on() handler. */
  emit: (event: string, payload?: unknown) => void;
}

/** Props passed to every custom edge component. */
export interface EdgeProps<TData = Record<string, unknown>> {
  /** Source node id. */
  source: string;
  /** Target node id. */
  target: string;
  /** The edge's data object. */
  data: TData;
  /** Whether this edge is currently selected. */
  selected: boolean;
  /** Send a named event + payload to the Python Flow.on() handler. */
  emit: (event: string, payload?: unknown) => void;
}
