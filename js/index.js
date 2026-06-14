// figureflow front-end source. Bundled by esbuild into
// src/figureflow/static/widget.js with React + @xyflow/react + dagre vendored
// in — the published wheel ships only the prebuilt bundle, no CDN.

import React from "react";
import { createRoot } from "react-dom/client";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  applyNodeChanges,
  applyEdgeChanges,
  Handle,
  Position,
} from "@xyflow/react";
import dagre from "@dagrejs/dagre";
import xyflowCss from "@xyflow/react/dist/style.css";

import { createSyncCore } from "./synccore.js";
import { createAnywidgetTransport } from "./adapters/anywidget.js";
import { createStaticTransport } from "./adapters/static.js";
import { createServerTransport } from "./adapters/server.js";

// Expose vendored React + xyflow handles on a well-known global so runtime-
// loaded L3 custom components can share our React instance (avoids the
// "two Reacts" invalid-hook-call error). The transport seam (SKELETON_V2 §05)
// also publishes `mount` + the non-anywidget adapter factories here so the
// static-export and server host pages can boot the same bundle.
globalThis.figureflow = {
  React,
  xyflow: { Handle, Position },
  createStaticTransport,
  createServerTransport,
  // `mount` is assigned after App is defined (see bottom of file).
};

// Inject the vendored xyflow CSS once via a <style> tag.
function ensureStyle() {
  const id = "figureflow-xyflow-css";
  if (document.getElementById(id)) return;
  const style = document.createElement("style");
  style.id = id;
  style.textContent = xyflowCss;
  document.head.appendChild(style);
}

// ─── Text styling helpers ────────────────────────────────────────────────────

function textStyle(data) {
  return {
    fontFamily: data.fontFamily || "Inter, system-ui, sans-serif",
    fontSize: (data.fontSize || 13) + "px",
    color: data.fontColor || "#0f172a",
    fontWeight: data.bold ? 700 : 400,
    fontStyle: data.italic ? "italic" : "normal",
    textAlign: data.textAlign || "center",
  };
}

// ─── ShapeNode ───────────────────────────────────────────────────────────────

const HANDLE_STYLE = { background: "#94a3b8" };

function NodeHandles() {
  return React.createElement(
    React.Fragment,
    null,
    React.createElement(Handle, { type: "target", position: Position.Top, style: HANDLE_STYLE }),
    React.createElement(Handle, { type: "source", position: Position.Bottom, style: HANDLE_STYLE }),
    React.createElement(Handle, { type: "target", position: Position.Left, style: HANDLE_STYLE }),
    React.createElement(Handle, { type: "source", position: Position.Right, style: HANDLE_STYLE })
  );
}

function ShapeNodeInner({ data, selected }) {
  const fill = data.fill || "#ffffff";
  const borderColor = data.borderColor || "#334155";
  const borderWidth = data.borderWidth != null ? data.borderWidth : 1.5;
  const w = data.width || 130;
  const h = data.height || 56;
  const shape = data.shape || "rectangle";
  const ts = textStyle(data);
  const labelEl = data.html
    ? React.createElement("div", { dangerouslySetInnerHTML: { __html: data.html } })
    : React.createElement("span", { style: ts }, data.label || "");

  const centerLabel = {
    position: "absolute",
    inset: 0,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    pointerEvents: "none",
    padding: "4px",
    boxSizing: "border-box",
    ...ts,
  };

  // L1: custom SVG path overrides shape
  if (data.svgPath) {
    return React.createElement(
      "div",
      { style: { position: "relative", width: w, height: h } },
      React.createElement(
        "svg",
        { width: w, height: h, style: { overflow: "visible" } },
        React.createElement("path", {
          d: data.svgPath,
          fill,
          stroke: borderColor,
          strokeWidth: borderWidth,
        })
      ),
      React.createElement("div", { style: centerLabel }, labelEl),
      React.createElement(NodeHandles)
    );
  }

  // CSS-box shapes
  if (["rectangle", "rounded", "stadium", "ellipse"].includes(shape)) {
    const radii = { rectangle: 0, rounded: 8, stadium: 999, ellipse: "50%" };
    return React.createElement(
      "div",
      {
        style: {
          position: "relative",
          minWidth: 80,
          minHeight: 40,
          width: data.width ? w : undefined,
          height: data.height ? h : undefined,
          padding: "8px 14px",
          background: fill,
          border: `${borderWidth}px solid ${borderColor}`,
          borderRadius: radii[shape],
          boxSizing: "border-box",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          ...ts,
        },
      },
      labelEl,
      React.createElement(NodeHandles)
    );
  }

  // Polygon shapes: diamond, parallelogram, hexagon
  if (["diamond", "parallelogram", "hexagon"].includes(shape)) {
    const pw = data.width || 130;
    const ph = data.height || (shape === "diamond" ? 90 : 56);

    let points;
    if (shape === "diamond") {
      points = `${pw / 2},0 ${pw},${ph / 2} ${pw / 2},${ph} 0,${ph / 2}`;
    } else if (shape === "parallelogram") {
      const skew = 20;
      points = `${skew},0 ${pw},0 ${pw - skew},${ph} 0,${ph}`;
    } else {
      // hexagon
      const dx = pw * 0.25;
      points = `${dx},0 ${pw - dx},0 ${pw},${ph / 2} ${pw - dx},${ph} ${dx},${ph} 0,${ph / 2}`;
    }

    return React.createElement(
      "div",
      { style: { position: "relative", width: pw, height: ph } },
      React.createElement(
        "svg",
        { width: pw, height: ph, style: { overflow: "visible" } },
        React.createElement("polygon", {
          points,
          fill,
          stroke: borderColor,
          strokeWidth: borderWidth,
        })
      ),
      React.createElement("div", { style: centerLabel }, labelEl),
      React.createElement(NodeHandles)
    );
  }

  // Cylinder
  if (shape === "cylinder") {
    const pw = data.width || 130;
    const ph = data.height || 80;
    const ry = ph * 0.15;
    const rx = pw * 0.5;
    // Body: rect + two half-ellipses drawn as paths
    const bodyPath = `M 0,${ry} L 0,${ph - ry} A ${rx},${ry} 0 0 0 ${pw},${ph - ry} L ${pw},${ry} A ${rx},${ry} 0 0 0 0,${ry}`;
    const topEllipse = `M 0,${ry} A ${rx},${ry} 0 0 0 ${pw},${ry}`;
    return React.createElement(
      "div",
      { style: { position: "relative", width: pw, height: ph } },
      React.createElement(
        "svg",
        { width: pw, height: ph, style: { overflow: "visible" } },
        React.createElement("path", { d: bodyPath, fill, stroke: borderColor, strokeWidth: borderWidth }),
        React.createElement("path", { d: topEllipse, fill: "none", stroke: borderColor, strokeWidth: borderWidth })
      ),
      React.createElement("div", { style: centerLabel }, labelEl),
      React.createElement(NodeHandles)
    );
  }

  // Fallback: plain box
  return React.createElement(
    "div",
    {
      style: {
        position: "relative",
        padding: "8px 14px",
        background: fill,
        border: `${borderWidth}px solid ${borderColor}`,
        borderRadius: 4,
        boxSizing: "border-box",
        ...ts,
      },
    },
    labelEl,
    React.createElement(NodeHandles)
  );
}

const ShapeNode = React.memo(ShapeNodeInner);

// ─── GroupNode ───────────────────────────────────────────────────────────────

function GroupNodeInner({ data }) {
  const fill = data.fill || "rgba(226,232,240,0.4)";
  const borderColor = data.borderColor || "#94a3b8";
  const borderWidth = data.borderWidth != null ? data.borderWidth : 1.5;
  return React.createElement(
    "div",
    {
      style: {
        width: "100%",
        height: "100%",
        background: fill,
        border: `${borderWidth}px dashed ${borderColor}`,
        borderRadius: 8,
        boxSizing: "border-box",
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "flex-start",
        padding: "8px 12px",
        fontSize: 12,
        color: "#64748b",
      },
    },
    data.label || ""
  );
}

const GroupNode = React.memo(GroupNodeInner);

// ─── Module-level type maps (stable references) ───────────────────────────────

const _builtinNodeTypes = { shape: ShapeNode, group: GroupNode };
const _builtinEdgeTypes = {};

// Stable non-inline props for <ReactFlow> (inline arrays/objects remount the graph).
const PAN_ON_DRAG = [1, 2]; // middle + right button pan; left drag = box select
// These will be augmented by L3 registrations at runtime via useMemo in App.

// ─── Auto-layout (dagre) ─────────────────────────────────────────────────────

function runDagre(nodes, edges, direction) {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: direction || "TB", nodesep: 50, ranksep: 60 });

  const topLevel = nodes.filter((n) => !n.parentId);
  topLevel.forEach((n) => {
    g.setNode(n.id, {
      width: (n.data && n.data.width) || 130,
      height: (n.data && n.data.height) || (n.type === "group" ? 150 : 56),
    });
  });
  edges.forEach((e) => {
    if (g.hasNode(e.source) && g.hasNode(e.target)) {
      g.setEdge(e.source, e.target);
    }
  });

  dagre.layout(g);

  return nodes.map((n) => {
    if (n.parentId) return n; // children keep their parent-relative coords
    const pos = g.node(n.id);
    if (!pos) return n;
    return {
      ...n,
      position: {
        x: pos.x - (n.data && n.data.width ? n.data.width / 2 : 65),
        y: pos.y - (n.data && n.data.height ? n.data.height / 2 : 28),
      },
    };
  });
}

// ─── History helpers ─────────────────────────────────────────────────────────

const HISTORY_CAP = 50;

function pushHistory(histRef, nodesSnapshot, edgesSnapshot) {
  const { past, redoStack } = histRef.current;
  histRef.current = {
    past: [...past.slice(-(HISTORY_CAP - 1)), { nodes: nodesSnapshot, edges: edgesSnapshot }],
    redoStack: [],
  };
}

// ─── App ─────────────────────────────────────────────────────────────────────

function App({ transport }) {
  const initial = React.useRef(transport.getState()).current;
  const [nodes, setNodes] = React.useState(() => initial.nodes || []);
  const [edges, setEdges] = React.useState(() => initial.edges || []);
  const [meta, setMeta] = React.useState(() => initial.meta || {});
  // Shared sync-core echo-guard: Python→JS pushes must not bounce back as edits.
  const sync = React.useRef(createSyncCore()).current;
  // Flag to skip recording the next seam commit as a history entry (restore path).
  const skipHistoryRef = React.useRef(false);
  // Undo/redo stacks stored in a ref (not state) to avoid re-renders.
  const histRef = React.useRef({ past: [], redoStack: [] });
  // In-memory clipboard for within-canvas copy/paste.
  const clipboardRef = React.useRef(null);
  // Tracks loaded L3 dynamic components: { nodeTypes: {}, edgeTypes: {} }
  const [dynTypes, setDynTypes] = React.useState({ nodeTypes: {}, edgeTypes: {} });
  const loadedModulesRef = React.useRef({ node: {}, edge: {} });
  // Per-mount cache-buster for dynamic import(): the browser keys its module map
  // by URL, so a `data:`/blob L3 module is evaluated once and binds React from
  // globalThis.figureflow at that moment. On a notebook rerun/kernel-restart the
  // bundle re-evaluates with a fresh React, but the cached module keeps the stale
  // one — rendering its hooked nodes (Handle) then throws and blanks the canvas.
  // A unique import fragment forces a re-evaluation against the current React.
  const importNonceRef = React.useRef(
    `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`
  );

  // Merged type maps — stable unless registrations change.
  const nodeTypes = React.useMemo(
    () => ({ ..._builtinNodeTypes, ...dynTypes.nodeTypes }),
    [dynTypes.nodeTypes]
  );
  const edgeTypes = React.useMemo(
    () => ({ ..._builtinEdgeTypes, ...dynTypes.edgeTypes }),
    [dynTypes.edgeTypes]
  );

  // ── Transport → local state sync (push→local; the only echo-guarded path) ──
  React.useEffect(() => {
    return transport.subscribe((state) => {
      if (state.nodes !== undefined) {
        sync.markEcho();
        setNodes(state.nodes);
      }
      if (state.edges !== undefined) {
        sync.markEcho();
        setEdges(state.edges);
      }
      if (state.meta !== undefined) setMeta(state.meta);
    });
  }, [transport, sync]);

  // ── Layout request (Python pushes a "layout" event; dagre runs client-side) ─
  React.useEffect(() => {
    return transport.onEvent("layout", (req) => {
      // Read current state from the transport (always up-to-date; avoids stale
      // closure and the nested-setter anti-pattern).
      const cur = transport.getState();
      const arranged = runDagre(cur.nodes || [], cur.edges || [], req.direction);
      // Push to history so layout is a single undoable entry (ITER_03 seam).
      pushHistory(histRef, cur.nodes || [], cur.edges || []);
      transport.pushChange({ nodes: arranged });
    });
  }, [transport]);

  // ── L3 dynamic module loading (keyed off meta module maps) ────────────────
  React.useEffect(() => {
    const loadModules = async (modulesMap, kind) => {
      const loaded = {};
      for (const [name, url] of Object.entries(modulesMap)) {
        if (loadedModulesRef.current[kind][name]) {
          loaded[name] = loadedModulesRef.current[kind][name];
          continue;
        }
        try {
          const bust = (url.includes("#") ? "&" : "#") + "ff=" + importNonceRef.current;
          const mod = await import(/* @vite-ignore */ url + bust);
          const comp = mod.default;
          loadedModulesRef.current[kind][name] = comp;
          loaded[name] = comp;
        } catch (err) {
          console.error(`[figureflow] Failed to load ${kind} module '${name}' from '${url}':`, err);
        }
      }
      return loaded;
    };

    const reload = async () => {
      const [nodeLoaded, edgeLoaded] = await Promise.all([
        loadModules(meta.nodeModules || {}, "node"),
        loadModules(meta.edgeModules || {}, "edge"),
      ]);
      setDynTypes({ nodeTypes: nodeLoaded, edgeTypes: edgeLoaded });
    };

    reload();
  }, [meta.nodeModules, meta.edgeModules]);

  // ── Down-events: undo / redo / clear_history (from Python) ────────────────
  React.useEffect(() => {
    const restore = (snapshot, nextHist) => {
      histRef.current = nextHist;
      skipHistoryRef.current = true;
      setNodes(snapshot.nodes);
      setEdges(snapshot.edges);
      transport.pushChange({ nodes: snapshot.nodes, edges: snapshot.edges });
    };
    const unsubs = [
      transport.onEvent("undo", () => {
        const { past, redoStack } = histRef.current;
        if (!past.length) return;
        const prev = past[past.length - 1];
        restore(prev, {
          past: past.slice(0, -1),
          redoStack: [{ nodes, edges }, ...redoStack],
        });
      }),
      transport.onEvent("redo", () => {
        const { past, redoStack } = histRef.current;
        if (!redoStack.length) return;
        const next = redoStack[0];
        restore(next, {
          past: [...past, { nodes, edges }],
          redoStack: redoStack.slice(1),
        });
      }),
      transport.onEvent("clear_history", () => {
        histRef.current = { past: [], redoStack: [] };
      }),
    ];
    return () => unsubs.forEach((u) => u());
  }, [transport, nodes, edges]);

  // ── Keyboard: copy/paste, undo/redo ──────────────────────────────────────
  React.useEffect(() => {
    const onKey = (e) => {
      const metaKey = e.ctrlKey || e.metaKey;
      if (!metaKey) return;

      if (e.key === "z" && !e.shiftKey) {
        e.preventDefault();
        const { past, redoStack } = histRef.current;
        if (!past.length) return;
        const prev = past[past.length - 1];
        histRef.current = {
          past: past.slice(0, -1),
          redoStack: [{ nodes: nodes, edges: edges }, ...redoStack],
        };
        skipHistoryRef.current = true;
        setNodes(prev.nodes);
        setEdges(prev.edges);
        transport.pushChange({ nodes: prev.nodes, edges: prev.edges });
        return;
      }

      if ((e.key === "z" && e.shiftKey) || e.key === "y") {
        e.preventDefault();
        const { past, redoStack } = histRef.current;
        if (!redoStack.length) return;
        const next = redoStack[0];
        histRef.current = {
          past: [...past, { nodes: nodes, edges: edges }],
          redoStack: redoStack.slice(1),
        };
        skipHistoryRef.current = true;
        setNodes(next.nodes);
        setEdges(next.edges);
        transport.pushChange({ nodes: next.nodes, edges: next.edges });
        return;
      }

      if (e.key === "c") {
        const selectedNodes = nodes.filter((n) => n.selected);
        const selectedIds = new Set(selectedNodes.map((n) => n.id));
        const selectedEdges = edges.filter(
          (e2) => selectedIds.has(e2.source) && selectedIds.has(e2.target)
        );
        clipboardRef.current = { nodes: selectedNodes, edges: selectedEdges };
        return;
      }

      if (e.key === "v" && clipboardRef.current) {
        const { nodes: cNodes, edges: cEdges } = clipboardRef.current;
        if (!cNodes.length) return;

        // Generate copy ids: {origId}-copy-{n}
        const countMap = {};
        const idMap = {};
        cNodes.forEach((n) => {
          const base = n.id;
          const existing = nodes.filter((x) => x.id.startsWith(base + "-copy-"));
          countMap[base] = existing.length + 1;
          idMap[base] = `${base}-copy-${countMap[base]}`;
        });

        const pastedNodes = cNodes.map((n) => ({
          ...n,
          id: idMap[n.id],
          selected: true,
          position: { x: n.position.x + 24, y: n.position.y + 24 },
        }));
        const pastedEdges = cEdges.map((e2) => ({
          ...e2,
          id: `${idMap[e2.source] || e2.source}->${idMap[e2.target] || e2.target}`,
          source: idMap[e2.source] || e2.source,
          target: idMap[e2.target] || e2.target,
          selected: true,
        }));

        const nextNodes = [...nodes.map((n) => ({ ...n, selected: false })), ...pastedNodes];
        const nextEdges = [...edges.map((e2) => ({ ...e2, selected: false })), ...pastedEdges];

        pushHistory(histRef, nodes, edges);
        setNodes(nextNodes);
        setEdges(nextEdges);
        transport.pushChange({ nodes: nextNodes, edges: nextEdges });
      }
    };

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [transport, nodes, edges]);

  // ── Commit seam ───────────────────────────────────────────────────────────
  const commitSeam = React.useCallback(
    (nextNodes, nextEdges, currentNodes, currentEdges) => {
      if (!skipHistoryRef.current) {
        pushHistory(histRef, currentNodes, currentEdges);
      }
      skipHistoryRef.current = false;
      const patch = { nodes: nextNodes };
      if (nextEdges !== undefined) patch.edges = nextEdges;
      transport.pushChange(patch);
    },
    [transport]
  );

  const onNodesChange = React.useCallback(
    (changes) => {
      setNodes((current) => {
        const next = applyNodeChanges(changes, current);
        const commit = changes.some(
          (c) =>
            c.type === "remove" ||
            c.type === "add" ||
            (c.type === "position" && c.dragging === false)
        );
        if (commit && !sync.isEcho()) {
          commitSeam(next, undefined, current, edges);
        }
        sync.clearEcho();
        return next;
      });
    },
    [commitSeam, edges, sync]
  );

  const onEdgesChange = React.useCallback(
    (changes) => {
      setEdges((current) => {
        const next = applyEdgeChanges(changes, current);
        const commit = changes.some((c) => c.type === "remove" || c.type === "add");
        if (commit && !sync.isEcho()) {
          commitSeam(nodes, next, nodes, current);
        }
        sync.clearEcho();
        return next;
      });
    },
    [commitSeam, nodes, sync]
  );

  // emit function for L3 custom components
  const emit = React.useCallback(
    (eventName, payload) => {
      transport.sendEvent(eventName, payload);
    },
    [transport]
  );

  // Inject emit into node data for L3 components
  const nodesWithEmit = React.useMemo(
    () => nodes.map((n) => ({ ...n, data: { ...n.data, emit } })),
    [nodes, emit]
  );

  const colorMode = meta.colorMode || "light";
  const fitView = meta.fitView !== false;

  return React.createElement(
    ReactFlow,
    {
      nodes: nodesWithEmit,
      edges,
      nodeTypes,
      edgeTypes,
      onNodesChange,
      onEdgesChange,
      colorMode,
      fitView,
      onlyRenderVisibleElements: true,
      selectionOnDrag: true,
      multiSelectionKeyCode: "Shift",
      panOnDrag: PAN_ON_DRAG,
    },
    React.createElement(Background, null),
    React.createElement(Controls, null),
    React.createElement(MiniMap, null),
    transport.downloadAffordance
      ? React.createElement(DownloadButton, { transport })
      : null
  );
}

// ─── Download JSON control (static export only; ITER_V2_02) ───────────────────

function DownloadButton({ transport }) {
  const onClick = React.useCallback(() => {
    const json = transport.serializeState();
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "figureflow.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [transport]);

  return React.createElement(
    "button",
    {
      onClick,
      style: {
        position: "absolute",
        top: 8,
        right: 8,
        zIndex: 10,
        padding: "6px 12px",
        fontSize: 12,
        fontFamily: "Inter, system-ui, sans-serif",
        background: "#0f172a",
        color: "#ffffff",
        border: "none",
        borderRadius: 6,
        cursor: "pointer",
      },
    },
    "Download JSON"
  );
}

// ─── Mount: shared entry for every adapter ────────────────────────────────────

function mountApp(el, transport, opts = {}) {
  ensureStyle();
  el.classList.add("figureflow");
  el.style.position = el.style.position || "relative";
  el.style.height = `${opts.height || 480}px`;
  const root = createRoot(el);
  root.render(React.createElement(App, { transport }));
  return () => root.unmount();
}

globalThis.figureflow.mount = mountApp;

// anywidget entry — the notebook door of the seam (ITER_V2_01).
export default {
  render({ model, el }) {
    const transport = createAnywidgetTransport(model);
    return mountApp(el, transport, { height: model.get("height") || 480 });
  },
};
