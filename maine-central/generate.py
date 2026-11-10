#!/usr/bin/env python3
"""Generate laser-cut SVG layers for the two Maine Central stacked signs.

* square/  - 18" x 13-1/8" "The Pine Tree Route" herald, orange on green (3 layers)
* round/   - 14" round herald, yellow on green (4 layers)

The lettering and trees come from trace.json (traced from the herald images in
source/ by trace.py); rings, borders and discs are drawn exactly. Units are inches,
SVG coordinates (origin top-left, y down).

Run:  python3 generate.py      (needs: pip install shapely numpy)
"""
import json
import math
import os

import numpy as np
from shapely import affinity
from shapely.geometry import Point, Polygon, MultiPolygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
TRACE = json.load(open(os.path.join(HERE, "trace.json")))

COLORS = {
    "green": "#0B5A2C",
    "orange": "#F2852A",
    "yellow": "#FFD200",
}

SMOOTH = 0.03       # corner/edge smoothing radius for traced shapes (in)
SIMPLIFY = 0.003    # path simplification tolerance (in)
MIN_WIDTH = 0.08    # report any cut piece with features thinner than this (in)

# ---------------------------------------------------------------- square sign
SQ_W = 18.0                            # overall width
SQ_PX = SQ_W / 300.0                   # inches per image pixel (0.06")
SQ_H = round(219 * SQ_PX * 8) / 8      # 13.125"
SQ_BORDER = 0.50                       # orange border width (8.3 px on the herald)
SQ_CORNER = 0.125                      # outer corner radius (keeps the corners from chipping)
SQ_FIELD_CORNER = 0.45                 # green field corner radius (as on the herald)
SQ_RING_W = 0.20                       # ring around the tree (0.15" on the herald; widened to cut safely)

# ---------------------------------------------------------------- round sign
RD_D = 14.0
RD_PX = RD_D / 250.0                   # inches per image pixel (0.056")
RD_R = RD_D / 2
RD_RING_OUT = 6.38                     # yellow ring, outer radius (measured, 114 px)
RD_RING_IN = 6.15                      # yellow ring, inner radius = green field (110 px)


# ------------------------------------------------------------------ helpers
def rounded_rect(x0, y0, x1, y1, r):
    return box(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=32)


def circle(cx, cy, r, n=720):
    return Point(cx, cy).buffer(r, quad_segs=n // 4)


def clean(g):
    """Round off pixel wobble: open + close by SMOOTH, then simplify."""
    r = SMOOTH
    g = g.buffer(r, quad_segs=16).buffer(-2 * r, quad_segs=16).buffer(r, quad_segs=16)
    return g.simplify(SIMPLIFY, preserve_topology=True)


def shape_poly(s, scale, dx=0.0, dy=0.0):
    f = lambda pts: [((x + 0.5) * scale + dx, (y + 0.5) * scale + dy) for x, y in pts]
    return Polygon(f(s["outer"]), [f(h) for h in s["holes"]]).buffer(0)


def fit_circle(pts):
    """Least-squares circle through points -> (cx, cy, r)."""
    p = np.asarray(pts)
    A = np.c_[2 * p[:, 0], 2 * p[:, 1], np.ones(len(p))]
    b = (p ** 2).sum(1)
    cx, cy, c = np.linalg.lstsq(A, b, rcond=None)[0]
    return cx, cy, math.sqrt(c + cx * cx + cy * cy)


def in_box(s, x0, y0, x1, y1):
    bx0, by0, bx1, by1 = s["bbox"]
    cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
    return x0 <= cx <= x1 and y0 <= cy <= y1


def pieces(g):
    return list(g.geoms) if isinstance(g, MultiPolygon) else [g]


def thin_report(name, g):
    """Area of the piece lost by an opening of MIN_WIDTH - i.e. features thinner than that."""
    lost = g.difference(g.buffer(-MIN_WIDTH / 2).buffer(MIN_WIDTH / 2 + 1e-4))
    a = sum(p.area for p in pieces(lost) if p.area > 1e-4)
    if a > 0.002:
        print(f"   note: {name}: {a:.3f} sq in thinner than {MIN_WIDTH}\" (check tips)")


# ------------------------------------------------------------------ square
def square_layers():
    shapes = TRACE["square"]["shapes"]
    s = SQ_PX
    # the herald is 219 px tall -> 13.14"; centre it vertically on the 13.125" sign
    dy = (SQ_H - 219 * s) / 2
    art = []
    ring = None
    for sh in shapes:
        bx0, by0, bx1, by1 = sh["bbox"]
        if bx1 - bx0 > 90:                       # the ring around the tree
            o = fit_circle(sh["outer"])
            i = fit_circle(sh["holes"][0])
            cx, cy = (o[0] + i[0]) / 2, (o[1] + i[1]) / 2
            ring = (cx, cy, o[2], i[2])
            continue
        art.append(clean(shape_poly(sh, s, 0, dy)))
    cx, cy, ro, ri = ring
    ccx, ccy = (cx + 0.5) * s, (cy + 0.5) * s + dy
    rmid = (ro + ri) / 2 * s
    ring_g = circle(ccx, ccy, rmid + SQ_RING_W / 2).difference(circle(ccx, ccy, rmid - SQ_RING_W / 2))
    print(f"   ring: centre ({ccx:.2f}, {ccy:.2f}), {2 * rmid + SQ_RING_W:.2f}\" OD, {SQ_RING_W}\" wide")
    art_g = unary_union(art + [ring_g])

    base = rounded_rect(0, 0, SQ_W, SQ_H, SQ_CORNER)
    b = SQ_BORDER
    field = rounded_rect(b, b, SQ_W - b, SQ_H - b, SQ_FIELD_CORNER)
    return (SQ_W, SQ_H), [
        ("layer1_base_orange", "orange", base, 0.25,
         f"{SQ_W:g}\" x {SQ_H:g}\" backer - shows as the orange border"),
        ("layer2_green_field", "green", field, 0.125,
         f"{SQ_W - 2 * b:g}\" x {SQ_H - 2 * b:g}\" green field"),
        ("layer3_orange_art", "orange", art_g, 0.25,
         "lettering, ring and pine tree (separate pieces)"),
    ]


# ------------------------------------------------------------------ round
def round_layers():
    shapes = TRACE["round"]["shapes"]
    s = RD_PX
    art = unary_union([clean(shape_poly(sh, s)) for sh in shapes])
    c = RD_R
    return (RD_D, RD_D), [
        ("layer1_base_green", "green", circle(c, c, RD_R), 0.25,
         f"{RD_D:.2f}\" disc - outer green rim / backer"),
        ("layer2_yellow_ring", "yellow", circle(c, c, RD_RING_OUT), 0.125,
         f"{2 * RD_RING_OUT:.2f}\" disc - yellow pinstripe ring"),
        ("layer3_green_field", "green", circle(c, c, RD_RING_IN), 0.125,
         f"{2 * RD_RING_IN:.2f}\" disc - green field"),
        ("layer4_yellow_art", "yellow", art, 0.25,
         "lettering and pine tree (separate pieces)"),
    ]


# ------------------------------------------------------------------ SVG out
def path_d(geom):
    out = []
    for p in pieces(geom):
        if p.is_empty:
            continue
        for ring in [p.exterior, *p.interiors]:
            pts = list(ring.coords)
            out.append("M" + " L".join(f"{x:.4f},{y:.4f}" for x, y in pts[:-1]) + " Z")
    return " ".join(out)


def svg_doc(size, body, title):
    w, h = size
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}in" height="{h:g}in" '
            f'viewBox="0 0 {w:g} {h:g}">\n<title>{title}</title>\n{body}\n</svg>\n')


def write_sign(name, size, layers):
    out = os.path.join(HERE, name, "svg")
    os.makedirs(out, exist_ok=True)
    print(f"{name}: {size[0]:g}\" x {size[1]:g}\"")
    preview, z = [], 0.0
    for i, (stem, color, geom, thick, note) in enumerate(layers, 1):
        thin_report(stem, geom)
        d = path_d(geom)
        cut = f'<path d="{d}" fill="none" stroke="#FF0000" stroke-width="0.01" fill-rule="evenodd"/>'
        with open(os.path.join(out, stem + ".svg"), "w") as f:
            f.write(svg_doc(size, cut, f"Layer {i} - {note} - paint {color}"))
        preview.append((stem, color, d, z, thick))
        print(f"   | {i} | `{stem}.svg` | {color} | {thick}\" | {len(pieces(geom))} pcs | {note} |")
        z += thick

    body = "\n".join(f'<path d="{d}" fill="{COLORS[c]}" fill-rule="evenodd"/>' for _, c, d, _, _ in preview)
    with open(os.path.join(out, "preview_flat.svg"), "w") as f:
        f.write(svg_doc(size, body, "Flat colour preview"))

    tcols = ["#000", "#0a0", "#c60", "#00c"]
    body = "\n".join(f'<path d="{d}" fill="none" stroke="{tcols[k]}" stroke-width="0.015" fill-rule="evenodd"/>'
                     for k, (_, _, d, _, _) in enumerate(preview))
    with open(os.path.join(out, "placement_template.svg"), "w") as f:
        f.write(svg_doc(size, body, "Glue-up placement template (print 1:1)"))

    with open(os.path.join(out, "layers.json"), "w") as f:
        json.dump({"w": size[0], "h": size[1], "round": name == "round",
                   "layers": [{"stem": s, "color": COLORS[c], "d": d, "z": zz, "t": t}
                              for s, c, d, zz, t in preview]}, f)
    print(f"   total stack height: {z:.3f}\"")


def main():
    write_sign("square", *square_layers())
    write_sign("round", *round_layers())


if __name__ == "__main__":
    main()
