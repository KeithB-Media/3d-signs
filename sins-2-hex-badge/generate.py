#!/usr/bin/env python3
"""Generate laser-cut SVG layers for a 24" tall hexagon badge with the simplified Sins II logo.

The layout follows the game's app icon: two "II" bars, SINS, then two pointed bars. The SINS
letters are the ones traced from the full logo (../sins-solar-empire-2/logo_trace.json);
the bars are drawn here with the same proportions as the logo's bars.
Units are inches. Origin is the sign centre with +y up; SVG output flips y.
Run:  python3 generate.py   (needs: pip install shapely)
"""
import json
import os

from shapely import affinity
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "svg")
TRACE = os.path.join(HERE, "..", "sins-solar-empire-2", "logo_trace.json")

# ---------------------------------------------------------------- dimensions
HEIGHT = 24.0              # point to point
WIDTH = 16.0               # flat side to flat side
SHOULDER = 9.0             # y where the straight sides meet the pointed top / bottom
CORNER_R = 0.35            # rounding of the badge corners
RIM = 0.25                 # black outer rim
TRIM = 0.125               # gold trim band
INNER = 0.125              # black band inside the trim

SINS_H = 5.3               # height of the SINS letters
BAR_W = 0.125              # bar width, as a fraction of the SINS width
BAR_GAP = 0.17             # gap between the two bars, as a fraction of the SINS width
ROW_GAP = 0.20             # gap between rows, as a fraction of SINS_H
TOP_BAR_H = 1.0            # top bars' height, as a fraction of SINS_H
BOT_BAR_H = 1.15           # bottom bars' height to the tip, as a fraction of SINS_H
TIP_DROP = 1.34            # bottom bars' slanted cut drops this many bar widths (as on the logo)

GLOW = 0.40                # blue band around the logo
EDGE = 0.13                # thin black edge directly under the white logo

COLORS = {
    "black": "#121216",
    "gold": "#C99A2E",
    "navy": "#13263B",
    "blue": "#3A6A99",
    "white": "#F4F5F2",
}


# ------------------------------------------------------------------ helpers
def pieces(g):
    return list(g.geoms) if isinstance(g, MultiPolygon) else [g]


def fill_holes(g):
    return unary_union([Polygon(p.exterior) for p in pieces(g)])


def badge(inset=0.0):
    w, h, s = WIDTH / 2, HEIGHT / 2, SHOULDER
    hexa = Polygon([(0, h), (w, s), (w, -s), (0, -h), (-w, -s), (-w, s)])
    g = hexa.buffer(-inset, join_style="mitre")
    return g.buffer(-CORNER_R, join_style="mitre").buffer(CORNER_R)


def sins_letters():
    with open(TRACE) as f:
        data = json.load(f)
    h = data["size"][1]
    # the small SINS: the four shapes on the top row, left of the bars
    shapes = [s for s in data["shapes"] if s["bbox"][1] < h * 0.3 and s["bbox"][0] < 420]
    assert len(shapes) == 4, len(shapes)
    g = unary_union([Polygon(s["outer"], s["holes"]).buffer(0) for s in shapes])
    minx, miny, maxx, maxy = g.bounds
    k = SINS_H / (maxy - miny)
    g = affinity.translate(g, -(minx + maxx) / 2, -(miny + maxy) / 2)
    return affinity.scale(g, k, -k, origin=(0, 0))


def logo():
    sins = sins_letters()
    minx, miny, maxx, maxy = sins.bounds
    sw = maxx - minx
    bw, gap, rg = BAR_W * sw, BAR_GAP * sw, ROW_GAP * SINS_H
    top_h, bot_h, drop = TOP_BAR_H * SINS_H, BOT_BAR_H * SINS_H, TIP_DROP * bw
    total = top_h + rg + SINS_H + rg + bot_h
    y_top = total / 2                                  # centre the whole stack
    sins = affinity.translate(sins, 0, y_top - top_h - rg - SINS_H / 2)
    parts = [sins]
    for side in (-1, 1):
        x_in, x_out = side * gap / 2, side * (gap / 2 + bw)
        parts.append(Polygon([(x_in, y_top), (x_out, y_top), (x_out, y_top - top_h), (x_in, y_top - top_h)]))
        yb = y_top - top_h - rg - SINS_H - rg          # top of the bottom bars
        tip = yb - bot_h
        parts.append(Polygon([(x_in, yb), (x_out, yb), (x_out, tip + drop), (x_in, tip)]))
    return unary_union(parts)


def build():
    art = logo()
    return [
        # (file stem, colour, geometry, thickness in, note)
        ("layer1_base_black", "black", badge(0), 0.25, "hexagon backer - black outer rim"),
        ("layer2_gold_trim", "gold", badge(RIM), 0.125, "gold trim band"),
        ("layer3_black_inner", "black", badge(RIM + TRIM), 0.125, "black band inside the trim"),
        ("layer4_navy_field", "navy", badge(RIM + TRIM + INNER), 0.125, "navy field"),
        ("layer5_blue_glow", "blue", fill_holes(art.buffer(GLOW, quad_segs=32)), 0.125,
         "blue band around the logo"),
        ("layer6_black_edge", "black", art.buffer(EDGE, quad_segs=32), 0.125, "black edge under the logo"),
        ("layer7_white_logo", "white", art, 0.25, "SINS and the II bars - top layer"),
    ]


# ------------------------------------------------------------------ SVG out
def path_d(geom):
    out = []
    for p in pieces(geom):
        for ring in [p.exterior, *p.interiors]:
            pts = list(ring.coords)
            out.append("M" + " L".join(f"{x + WIDTH / 2:.4f},{HEIGHT / 2 - y:.4f}" for x, y in pts[:-1]) + " Z")
    return " ".join(out)


def svg_doc(body, title):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}in" height="{HEIGHT}in" '
            f'viewBox="0 0 {WIDTH} {HEIGHT}">\n<title>{title}</title>\n{body}\n</svg>\n')


def main():
    os.makedirs(OUT, exist_ok=True)
    preview, z, rows = [], 0.0, []
    for i, (stem, color, geom, thick, note) in enumerate(build(), 1):
        d = path_d(geom)
        cut = f'<path d="{d}" fill="none" stroke="#FF0000" stroke-width="0.01" fill-rule="evenodd"/>'
        with open(os.path.join(OUT, stem + ".svg"), "w") as f:
            f.write(svg_doc(cut, f"Layer {i} - {note} - paint {color}"))
        bx = geom.bounds
        rows.append(f"| {i} | `svg/{stem}.svg` | {color} | {thick}\" | {len(pieces(geom))} | "
                    f"{bx[2] - bx[0]:.2f}\" x {bx[3] - bx[1]:.2f}\" | {note} |")
        preview.append((stem, color, d, z, thick))
        z += thick

    body = "\n".join(f'<path d="{d}" fill="{COLORS[c]}" fill-rule="evenodd"/>' for _, c, d, _, _ in preview)
    with open(os.path.join(OUT, "preview_flat.svg"), "w") as f:
        f.write(svg_doc(body, "Flat colour preview"))

    tcols = ["#000", "#c90", "#555", "#00c", "#06c", "#c00", "#0a0"]
    body = "\n".join(f'<path d="{d}" fill="none" stroke="{tcols[k]}" stroke-width="0.015" fill-rule="evenodd"/>'
                     for k, (_, _, d, _, _) in enumerate(preview))
    with open(os.path.join(OUT, "placement_template.svg"), "w") as f:
        f.write(svg_doc(body, "Glue-up placement template (print 1:1)"))

    with open(os.path.join(OUT, "layers.json"), "w") as f:
        json.dump({"w": WIDTH, "h": HEIGHT, "layers": [{"stem": s, "color": COLORS[c], "d": d, "z": z, "t": t}
                                                      for s, c, d, z, t in preview]}, f)
    print("\n".join(rows))
    print(f"total stack height: {z:.3f}\"")


if __name__ == "__main__":
    main()
