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
 *   export default function MyNode({ data, selected }) {
 *     // emit is injected into data by figureflow:
 *     const { emit } = data;
 *     return React.createElement("div", { onClick: () => emit("clicked", {}) }, data.label);
 *   }
 *
 * Note: `emit` is delivered inside `data` (not as a separate top-level prop)
 * because xyflow's custom component API only exposes user-defined data through
 * the `data` prop. Authors should destructure it from `data`.
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

/** Base data fields injected into every node's data object by figureflow. */
export interface FigureflowNodeData {
  label?: string;
  shape?: string;
  fill?: string;
  borderColor?: string;
  borderWidth?: number;
  fontFamily?: string;
  fontSize?: number;
  fontColor?: string;
  bold?: boolean;
  italic?: boolean;
  textAlign?: string;
  width?: number;
  height?: number;
  html?: string;
  svgPath?: string;
  /** Send a named event + payload to the Python Flow.on() handler. */
  emit: (event: string, payload?: unknown) => void;
  [key: string]: unknown;
}

/**
 * Props passed to every custom node component.
 * `emit` is accessed via `data.emit` (injected by figureflow at render time).
 */
export interface NodeProps<TData extends FigureflowNodeData = FigureflowNodeData> {
  id: string;
  data: TData;
  selected: boolean;
  type?: string;
}

/** Props passed to every custom edge component. */
export interface EdgeProps<TData = Record<string, unknown>> {
  id: string;
  source: string;
  target: string;
  data?: TData;
  selected: boolean;
}
