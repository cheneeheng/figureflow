// pyxyflow front-end source. Bundled by esbuild into
// src/pyxyflow/static/widget.js with React + @xyflow/react (and xyflow CSS)
// vendored in — the published wheel runs offline, no CDN, no runtime <link>.
import * as React from "react";
import { createRoot } from "react-dom/client";
import {
  ReactFlow,
  Background,
  Controls,
  applyNodeChanges,
  applyEdgeChanges,
} from "@xyflow/react";
// `--loader:.css=text` (esbuild) brings the xyflow stylesheet in as a string so
// it can be injected as a <style> tag — bundled, not linked from a CDN.
import xyflowCss from "@xyflow/react/dist/style.css";

const { useState, useEffect, useRef, useCallback } = React;

// Skeleton ShapeNode: ignores shape/font fields and draws a generic bordered
// box, proving the render+sync loop before ITER_01 makes shapes real.
function ShapeNode({ data }) {
  return React.createElement(
    "div",
    {
      style: {
        padding: "8px 12px",
        border: `1px solid ${(data && data.borderColor) || "#111827"}`,
        borderRadius: "4px",
        background: (data && data.fill) || "#ffffff",
      },
    },
    (data && data.label) || ""
  );
}

// Defined at module level for stable references — defining these inside App
// would remount the whole graph on every render. `edgeTypes` starts empty;
// built-in edge styling rides on each edge's native fields, and the map is
// populated only by L3 registration (ITER_06).
const nodeTypes = { shape: ShapeNode };
const edgeTypes = {};

function App({ model }) {
  const [nodes, setNodes] = useState(() => model.get("nodes") || []);
  const [edges, setEdges] = useState(() => model.get("edges") || []);
  // Echo guard so Python->JS writes don't bounce back as edits.
  const echo = useRef(false);

  // Python -> JS: mirror trait changes into local state.
  useEffect(() => {
    const onNodes = () => {
      echo.current = true;
      setNodes(model.get("nodes") || []);
    };
    const onEdges = () => {
      echo.current = true;
      setEdges(model.get("edges") || []);
    };
    model.on("change:nodes", onNodes);
    model.on("change:edges", onEdges);
    return () => {
      model.off("change:nodes", onNodes);
      model.off("change:edges", onEdges);
    };
  }, [model]);

  // Single commit seam (JS -> Python). This is where ITER_03's undo history
  // will hook. Commit back only on drag-stop and add/remove.
  const commitNodes = useCallback(
    (next) => {
      if (echo.current) {
        echo.current = false;
        return;
      }
      model.set("nodes", next);
      model.save_changes();
    },
    [model]
  );

  const onNodesChange = useCallback(
    (changes) => {
      setNodes((cur) => {
        const next = applyNodeChanges(changes, cur);
        const commitWorthy = changes.some(
          (c) =>
            c.type === "remove" ||
            c.type === "add" ||
            (c.type === "position" && c.dragging === false)
        );
        if (commitWorthy) commitNodes(next);
        return next;
      });
    },
    [commitNodes]
  );

  const onEdgesChange = useCallback((changes) => {
    setEdges((cur) => applyEdgeChanges(changes, cur));
  }, []);

  return React.createElement(
    ReactFlow,
    {
      nodes,
      edges,
      nodeTypes,
      edgeTypes,
      onNodesChange,
      onEdgesChange,
      colorMode: model.get("color_mode") || "light",
      fitView: model.get("fit_view") !== false,
    },
    React.createElement(Background, null),
    React.createElement(Controls, null)
  );
}

export default {
  render({ model, el }) {
    // Inject vendored xyflow CSS (bundled, no CDN/<link>).
    const style = document.createElement("style");
    style.textContent = xyflowCss;
    el.appendChild(style);

    const container = document.createElement("div");
    container.className = "pyxyflow-widget";
    container.style.height = `${model.get("height") || 480}px`;
    el.appendChild(container);

    const root = createRoot(container);
    root.render(React.createElement(App, { model }));

    return () => {
      root.unmount();
      el.removeChild(container);
      el.removeChild(style);
    };
  },
};
