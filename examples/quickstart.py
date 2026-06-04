"""quickstart.py — all 8 shapes and edge styles."""
from figureflow import Flow, Node, Edge, Shape

flow = Flow(
    nodes=[
        Node("rect",  "Rectangle",    pos=(0,   0),   shape=Shape.rectangle,    fill="#e0f2fe"),
        Node("round", "Rounded",       pos=(200, 0),   shape=Shape.rounded,      fill="#f0fdf4"),
        Node("stad",  "Stadium",       pos=(400, 0),   shape=Shape.stadium,      fill="#fef9c3"),
        Node("ell",   "Ellipse",       pos=(600, 0),   shape=Shape.ellipse,      fill="#fce7f3"),
        Node("dia",   "Diamond",       pos=(0,   160), shape=Shape.diamond,      fill="#ede9fe"),
        Node("para",  "Parallelogram", pos=(200, 160), shape=Shape.parallelogram, fill="#fff7ed"),
        Node("hex",   "Hexagon",       pos=(400, 160), shape=Shape.hexagon,      fill="#f0fdf4"),
        Node("cyl",   "Cylinder",      pos=(600, 160), shape=Shape.cylinder,     fill="#fef2f2"),
        Node("svg",   "Custom SVG",    pos=(0,   320),
             svg_path="M 10,30 A 20,20,0,0,1,50,30 A 20,20,0,0,1,90,30 Q 90,60,50,90 Q 10,60,10,30 z",
             fill="#fce7f3", width=100, height=100),
        Node("html",  "",              pos=(200, 320),
             html="<b style='color:#1d4ed8'>Raw HTML</b><br/><em>node body</em>"),
    ],
    edges=[
        Edge("rect",  "dia",  label="bezier",      path_type="bezier"),
        Edge("round", "para", label="step",        path_type="step",       dash="dashed"),
        Edge("stad",  "hex",  label="smoothstep",  path_type="smoothstep", dash="dotted"),
        Edge("ell",   "cyl",  label="straight",    path_type="straight",   marker_start="arrow"),
    ],
    height=600,
)

flow  # display in a notebook cell
