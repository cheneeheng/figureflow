// figureflow front-end source. Bundled by esbuild into
// src/figureflow/static/widget.js with React + @xyflow/react (+ xyflow CSS)
// vendored in — the published wheel ships only the prebuilt bundle, no CDN.

import React from "react";
import { createRoot } from "react-dom/client";
import {
  ReactFlow,
  Background,
  Controls,
  applyNodeChanges,
} from "@xyflow/react";
import xyflowCss from "@xyflow/react/dist/style.css";

// Inject the vendored xyflow CSS once via a <style> tag (bundled into this
// file as text — no runtime <link>, no CDN).
function ensureStyle() {
  const id = "figureflow-xyflow-css";
  if (document.getElementById(id)) return;
  const style = document.createElement("style");
  style.id = id;
  style.textContent = xyflowCss;
  document.head.appendChild(style);
}

// Skeleton node renderer: a plain bordered box. It ignores the shape/font
// fields and proves the render+sync loop; ITER_01 makes shapes real.
function ShapeNode({ data }) {
  return React.createElement(
    "div",
    {
      style: {
        padding: "8px 12px",
        borderRadius: 4,
        border: `1px solid ${(data && data.borderColor) || "#222"}`,
        background: (data && data.fill) || "#fff",
        fontSize: 12,
      },
    },
    (data && data.label) || ""
  );
}

// Module-level type maps — stable references so the graph isn't remounted on
// every render. ITER_04 adds a `group` entry; ITER_06 populates `edgeTypes`
// (built-in edge styling rides on xyflow's native renderers, not a custom
// component).
const nodeTypes = { shape: ShapeNode };
const edgeTypes = {};

function App({ model }) {
  const [nodes, setNodes] = React.useState(() => model.get("nodes") || []);
  const [edges, setEdges] = React.useState(() => model.get("edges") || []);
  // Guard so Python->JS writes don't bounce back to the model as edits.
  const echo = React.useRef(false);

  React.useEffect(() => {
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

  const onNodesChange = React.useCallback(
    (changes) => {
      setNodes((current) => {
        const next = applyNodeChanges(changes, current);
        // Single commit seam: commit to the model only on drag-stop / add /
        // remove. ITER_03's undo history hooks here.
        const commit = changes.some(
          (c) =>
            c.type === "remove" ||
            c.type === "add" ||
            (c.type === "position" && c.dragging === false)
        );
        if (commit && !echo.current) {
          model.set("nodes", next);
          model.save_changes();
        }
        echo.current = false;
        return next;
      });
    },
    [model]
  );

  return React.createElement(
    ReactFlow,
    {
      nodes,
      edges,
      nodeTypes,
      edgeTypes,
      onNodesChange,
      colorMode: model.get("color_mode") || "light",
      fitView: model.get("fit_view") !== false,
    },
    React.createElement(Background, null),
    React.createElement(Controls, null)
  );
}

export default {
  render({ model, el }) {
    ensureStyle();
    el.classList.add("figureflow");
    el.style.height = `${model.get("height") || 480}px`;
    const root = createRoot(el);
    root.render(React.createElement(App, { model }));
    return () => root.unmount();
  },
};
