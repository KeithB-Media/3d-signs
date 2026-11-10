#!/usr/bin/env python3
"""Generate laser-cut SVG layers for a 14" round stacked Guilford 'G' sign.

Gray / orange / white, built the same way as the Susquehanna S sign. The G is a
parametric geometric letter (no photo trace yet) - tune the G_* settings below.

Units are inches. Origin is the sign centre with +y up; SVG output flips y.
Run:  python3 generate.py   (needs: pip install shapely numpy)
"""
import json
import os

from shapely.geometry import Point, MultiPolygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "svg")

# ---------------------------------------------------------------- dimensions
DIAM = 14.0
R_BASE = DIAM / 2          # 7.00  gray outer rim (base)
R_WHITE = 6.80             # white pinstripe ring
R_ORANGE = 6.62            # orange ring
R_FIELD = 6.45             # gray field

# the G
G_CENTER = (0.0, 0.55)     # centre of the G's bowl
G_R_OUT = 4.10             # outer radius of the bowl
G_STROKE = 1.30            # stroke width of the bowl
G_GAP_X = 0.35             # opening starts this far right of the bowl centre
G_TOP_CUT = 2.55           # upper terminal is cut flat at this height (above bowl centre)
G_BAR_TOP = 0.20           # crossbar top (above bowl centre)
G_BAR_BOT = -1.05          # crossbar bottom - the bar joins the lower arm
G_BAR_X = 0.45             # crossbar inner end (right of bowl centre)
G_ROUND = 0.08             # corner rounding
G_OUTLINE = 0.22           # gray outline around the G
SUPPORT_INSET = 0.06       # hidden support under the G is inset this much

# stripes across the lower field (the locomotive's orange band with white pinstripes)
STRIPE_TOP = -2.55
STRIPE_BOT = -4.35
PIN = 0.25                 # white pinstripe width above and below the orange band
MIN_HALF = 0.045           # pieces thinner than 0.09" at the rim are trimmed

COLORS = {
    "gray": "#7B7F82",
    "orange": "#E8701E",
    "white": "#F4F3EF",
}


def circle(r, n=720):
    return Point(0, 0).buffer(r, quad_segs=n // 4)


def letter_g():
    cx, cy = G_CENTER
    ro, ri = G_R_OUT, G_R_OUT - G_STROKE
    bowl = Point(cx, cy).buffer(ro, quad_segs=180).difference(Point(cx, cy).buffer(ri, quad_segs=180))
    # opening on the right: everything right of the gap line between the bar and the upper terminal
    bowl = bowl.difference(box(cx + G_GAP_X, cy + G_BAR_TOP, cx + ro + 1, cy + G_TOP_CUT))
    bar = box(cx + G_BAR_X, cy + G_BAR_BOT, cx + ro, cy + G_BAR_TOP)
    bar = bar.intersection(Point(cx, cy).buffer(ro, quad_segs=180))
    g = unary_union([bowl, bar])
    return g.buffer(G_ROUND).buffer(-2 * G_ROUND).buffer(G_ROUND)


def parts():
    field = circle(R_FIELD)
    g = letter_g()
    g_outline = g.buffer(G_OUTLINE, join_style="round")
    support = g_outline.buffer(-SUPPORT_INSET)
    clean = lambda s: s.intersection(field).buffer(-MIN_HALF).buffer(MIN_HALF)
    white = clean(box(-8, STRIPE_BOT, 8, STRIPE_TOP))
    orange = clean(box(-8, STRIPE_BOT + PIN, 8, STRIPE_TOP - PIN))
    return dict(field=field, g=g, g_outline=g_outline, support=support, white=white, orange=orange)


def build():
    p = parts()
    return [
        # (file stem, colour, geometry, thickness in, note)
        ("layer1_base_gray", "gray", circle(R_BASE), 0.25, "14.00\" disc - outer gray rim / backer"),
        ("layer2_white_ring", "white", circle(R_WHITE), 0.125, "13.60\" disc - white pinstripe"),
        ("layer3_orange_ring", "orange", circle(R_ORANGE), 0.125, "13.24\" disc - orange ring"),
        ("layer4_gray_field", "gray", p["field"], 0.125, "12.90\" disc - gray field"),
        ("layer5_white_stripe", "white", unary_union([p["white"], p["support"]]), 0.125,
         "white stripe band (+ hidden G support)"),
        ("layer6_orange_stripe", "orange", unary_union([p["orange"], p["support"]]), 0.125,
         "orange stripe (+ hidden G support)"),
        ("layer7_gray_g_outline", "gray", p["g_outline"], 0.125, "gray outline of the G"),
        ("layer8_white_g", "white", p["g"], 0.125, "white G - top layer"),
    ]


# ------------------------------------------------------------------ SVG out
def path_d(geom):
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    out = []
    for p in polys:
        if p.is_empty:
            continue
        for ring in [p.exterior, *p.interiors]:
            pts = list(ring.coords)
            out.append("M" + " L".join(f"{x + R_BASE:.4f},{R_BASE - y:.4f}" for x, y in pts[:-1]) + " Z")
    return " ".join(out)


def svg_doc(body, title):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{DIAM}in" height="{DIAM}in" '
            f'viewBox="0 0 {DIAM} {DIAM}">\n<title>{title}</title>\n{body}\n</svg>\n')


def main():
    os.makedirs(OUT, exist_ok=True)
    layers = build()
    preview, z, rows = [], 0.0, []
    for i, (stem, color, geom, thick, note) in enumerate(layers, 1):
        geom = geom.simplify(0.002)
        d = path_d(geom)
        cut = f'<path d="{d}" fill="none" stroke="#FF0000" stroke-width="0.01" fill-rule="evenodd"/>'
        with open(os.path.join(OUT, stem + ".svg"), "w") as f:
            f.write(svg_doc(cut, f"Layer {i} - {note} - paint {color}"))
        preview.append((stem, color, d, z, thick))
        pieces = len(geom.geoms) if isinstance(geom, MultiPolygon) else 1
        rows.append(f"| {i} | `svg/{stem}.svg` | {color} | {thick}\" | {pieces} | {note} |")
        z += thick

    body = "\n".join(f'<path d="{d}" fill="{COLORS[c]}" fill-rule="evenodd"/>' for _, c, d, _, _ in preview)
    with open(os.path.join(OUT, "preview_flat.svg"), "w") as f:
        f.write(svg_doc(body, "Flat colour preview"))

    tcols = ["#000", "#c90", "#555", "#00c", "#0a0", "#c00", "#f80", "#808"]
    body = "\n".join(f'<path d="{d}" fill="none" stroke="{tcols[k]}" stroke-width="0.015" fill-rule="evenodd"/>'
                     for k, (_, _, d, _, _) in enumerate(preview))
    with open(os.path.join(OUT, "placement_template.svg"), "w") as f:
        f.write(svg_doc(body, "Glue-up placement template (print 1:1)"))

    with open(os.path.join(OUT, "layers.json"), "w") as f:
        json.dump([{"stem": s, "color": COLORS[c], "d": d, "z": z, "t": t}
                   for s, c, d, z, t in preview], f)
    print("\n".join(rows))
    print(f"total stack height: {z:.3f}\"")


if __name__ == "__main__":
    main()
