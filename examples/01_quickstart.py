"""01_quickstart.py — all 8 shapes, the L1 SVG and L2 HTML escape hatches, and edge styles.

Run it as a script to print a text summary of the diagram:

    python examples/01_quickstart.py

Or paste this into a notebook cell and end the cell with ``flow`` to render the
interactive widget.
"""
from figureflow import Edge, Flow, Node, Shape


def build() -> Flow:
    return Flow(
        nodes=[
            Node("rect",  "Rectangle",     pos=(0,   0),   shape=Shape.rectangle,     fill="#e0f2fe"),
            Node("round", "Rounded",       pos=(200, 0),   shape=Shape.rounded,       fill="#f0fdf4"),
            Node("stad",  "Stadium",       pos=(400, 0),   shape=Shape.stadium,       fill="#fef9c3"),
            Node("ell",   "Ellipse",       pos=(600, 0),   shape=Shape.ellipse,       fill="#fce7f3"),
            Node("dia",   "Diamond",       pos=(0,   160), shape=Shape.diamond,       fill="#ede9fe"),
            Node("para",  "Parallelogram", pos=(200, 160), shape=Shape.parallelogram, fill="#fff7ed"),
            Node("hex",   "Hexagon",       pos=(400, 160), shape=Shape.hexagon,       fill="#f0fdf4"),
            Node("cyl",   "Cylinder",      pos=(600, 160), shape=Shape.cylinder,      fill="#fef2f2"),
            Node("svg",   "Custom SVG",    pos=(0,   320),
                 svg_path="M 10,30 A 20,20,0,0,1,50,30 A 20,20,0,0,1,90,30 Q 90,60,50,90 Q 10,60,10,30 z",
                 fill="#fce7f3", width=100, height=100),
            Node("html",  "",              pos=(200, 320),
                 html="<b style='color:#1d4ed8'>Raw HTML</b><br/><em>node body</em>"),
        ],
        edges=[
            Edge("rect",  "dia",  label="bezier",     path_type="bezier"),
            Edge("round", "para", label="step",       path_type="step",       dash="dashed"),
            Edge("stad",  "hex",  label="smoothstep", path_type="smoothstep", dash="dotted"),
            Edge("ell",   "cyl",  label="straight",   path_type="straight",   marker_start="arrow"),
        ],
        height=600,
    )


flow = build()

if __name__ == "__main__":
    print(f"Built a Flow with {len(flow.nodes)} nodes and {len(flow.edges)} edges.")
    print("\nNodes (id → rendered as):")
    for n in flow.nodes:
        data = n["data"]
        if data.get("svgPath"):
            kind = "custom SVG (L1)"
        elif data.get("html"):
            kind = "raw HTML (L2)"
        else:
            kind = data.get("shape", "?")
        print(f"  {n['id']:>6}  →  {kind}")
    print("\nmermaid export:\n")
    print(flow.to_mermaid())
    print("\nDisplay it: paste this file's diagram into a notebook cell ending with `flow`.")
