#!/usr/bin/env python3
"""Generate laser-cut SVG layers for a stacked Maine Eastern Railroad diamond sign.

Units are inches. Design origin is the sign centre with +y up; SVG output flips y.
Run:  python3 generate.py [side]   (side of the square in inches, default 12)
Needs: pip install shapely numpy fonttools
"""
import json
import math
import os
import sys

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import MultiPolygon, Point, Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "svg")

# ---------------------------------------------------------------- dimensions
SIDE = float(sys.argv[1]) if len(sys.argv) > 1 else 12.0   # outer square, edge to edge
HALF = SIDE / 2

# Everything below was measured on the reference image (reference_logo.png) in pixels,
# from the centre of the yellow disc. The outer square is 157.5 px from centre to edge.
PX_APOTHEM = 157.5
K = HALF / PX_APOTHEM                     # inches per logo pixel
A_WHITE = 144.0 * K                       # white stripe, outer edge (centre to edge)
A_INNER = 131.0 * K                       # inner green square
R_DISC = 115.5 * K                        # yellow disc radius
CAP = 24.5 * K                            # letter cap height
STROKE_GROW = 0.17 * K                    # letters are a touch bolder than the font
TOP_BASE = 84.5 * K                       # MAINE: baseline radius (letters point outward)
BOTTOM_BASE = 109.5 * K                   # EASTERN: baseline radius (letters point inward)
# letter centre angles, degrees clockwise from straight up, measured on the logo
TOP_TEXT = [("M", -37.5), ("A", -16.3), ("I", 0.4), ("N", 16.2), ("E", 35.3)]
BOTTOM_TEXT = [("E", -129.1), ("A", -146.2), ("S", -162.5), ("T", 180.0),
               ("E", 160.2), ("R", 141.1), ("N", 122.6)]
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
TREE_SMOOTH = 0.6 * K                     # smoothing radius for the traced tree
MIN_FEATURE = 0.05                        # tree spikes thinner than this (in) are trimmed

COLORS = {"green": "#13700A", "white": "#F7F7F3", "yellow": "#F2D60C"}


# ------------------------------------------------------------------ helpers
def square(a):
    """Diamond (square standing on a point) with centre-to-edge distance a."""
    d = a * math.sqrt(2)
    return Polygon([(0, d), (d, 0), (0, -d), (-d, 0)])


def circle(r, n=720):
    return Point(0, 0).buffer(r, quad_segs=n // 4)


def glyph(ch, _cache={}):
    """Glyph outline as a shapely shape: cap height = CAP, ink centred on x = 0, baseline y = 0."""
    if "font" not in _cache:
        f = TTFont(FONT)
        _cache.update(font=f, gs=f.getGlyphSet(), cmap=f.getBestCmap(),
                      cap=f["OS/2"].sCapHeight)
    gs, cap = _cache["gs"], _cache["cap"]
    pen = DecomposingRecordingPen(gs)
    gs[_cache["cmap"][ord(ch)]].draw(pen)
    rings, cur = [], []
    for op, args in pen.value:
        if op == "moveTo":
            cur = [args[0]]
        elif op == "lineTo":
            cur.append(args[0])
        elif op == "qCurveTo":            # TrueType quadratic B-spline, implied on-curve points
            ctrl, end = list(args[:-1]), args[-1]
            pts = [cur[-1]]
            for i, c in enumerate(ctrl):
                nxt = end if i == len(ctrl) - 1 else ((c[0] + ctrl[i + 1][0]) / 2, (c[1] + ctrl[i + 1][1]) / 2)
                p0 = pts[-1]
                for k in range(1, 9):
                    t = k / 8
                    pts.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * nxt[0],
                                (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * nxt[1]))
            cur.extend(pts[1:])
        elif op in ("closePath", "endPath"):
            if len(cur) > 2:
                rings.append(Polygon(cur).buffer(0))
            cur = []
    # TrueType: outer contours clockwise, holes counter-clockwise -> even-odd fill
    shape = Polygon()
    for r in rings:
        shape = shape.symmetric_difference(r)
    x0, _, x1, _ = shape.bounds
    shape = affinity.translate(shape, -(x0 + x1) / 2, 0)
    shape = affinity.scale(shape, CAP / cap, CAP / cap, origin=(0, 0))
    return shape.buffer(STROKE_GROW, join_style="mitre")


def letters():
    out = []
    for text, base_r, base_ang, flip in ((TOP_TEXT, TOP_BASE, 0, False), (BOTTOM_TEXT, BOTTOM_BASE, 180, True)):
        for ch, ang in text:
            g = glyph(ch)
            # top: baseline at +base_r, tops outward; bottom: baseline at -base_r, tops inward
            g = affinity.translate(g, 0, -base_r if flip else base_r)
            out.append(affinity.rotate(g, -(ang - base_ang), origin=(0, 0)))
    return out


def tree():
    with open(os.path.join(HERE, "tree_trace.json")) as f:
        pts = json.load(f)["tree"]
    t = affinity.scale(Polygon(pts).buffer(0), K, K, origin=(0, 0))
    s = TREE_SMOOTH
    t = t.buffer(s).buffer(-2 * s).buffer(s)                       # smooth the pixel trace
    t = t.buffer(-MIN_FEATURE / 2).buffer(MIN_FEATURE / 2)       # trim hair-thin spikes
    if isinstance(t, MultiPolygon):
        t = max(t.geoms, key=lambda g: g.area)
    return t.simplify(0.003)


def build():
    art = unary_union([tree(), *letters()])
    return [
        # (file stem, colour, geometry, thickness in, note)
        ("layer1_base_green", "green", square(HALF), 0.25,
         f"{SIDE:.2f}\" square - outer green border / backer"),
        ("layer2_white_stripe", "white", square(A_WHITE), 0.125,
         f"{2 * A_WHITE:.2f}\" square - white stripe"),
        ("layer3_green_square", "green", square(A_INNER), 0.125,
         f"{2 * A_INNER:.2f}\" square - inner green"),
        ("layer4_yellow_disc", "yellow", circle(R_DISC), 0.125,
         f"{2 * R_DISC:.2f}\" disc - yellow"),
        ("layer5_green_tree_letters", "green", art, 0.125,
         "spruce tree + 12 letters MAINE / EASTERN - top layer"),
    ]


# ------------------------------------------------------------------ SVG out
# The cut files are drawn with the square's edges level (art turned 45 deg), so every
# layer fits on square stock of SIDE x SIDE. Previews show the sign hung on its point.
CUT_ROT = 45


def path_d(geom, rot=0):
    if rot:
        geom = affinity.rotate(geom, rot, origin=(0, 0))
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    out = []
    W = sheet(rot) / 2
    for p in polys:
        if p.is_empty:
            continue
        for ring in [p.exterior, *p.interiors]:
            pts = list(ring.coords)
            out.append("M" + " L".join(f"{x + W:.4f},{W - y:.4f}" for x, y in pts[:-1]) + " Z")
    return " ".join(out)


def sheet(rot):
    return SIDE if rot else SIDE * math.sqrt(2)


def svg_doc(body, title, rot):
    w = sheet(rot)
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.4f}in" height="{w:.4f}in" '
            f'viewBox="0 0 {w:.4f} {w:.4f}">\n<title>{title}</title>\n{body}\n</svg>\n')


def main():
    os.makedirs(OUT, exist_ok=True)
    layers = build()
    rows, z, preview = [], 0.0, []
    for i, (stem, color, geom, thick, note) in enumerate(layers, 1):
        d = path_d(geom, CUT_ROT)
        cut = f'<path d="{d}" fill="none" stroke="#FF0000" stroke-width="0.01" fill-rule="evenodd"/>'
        with open(os.path.join(OUT, stem + ".svg"), "w") as f:
            f.write(svg_doc(cut, f"Layer {i} - {note} - paint {color}", CUT_ROT))
        pieces = len(geom.geoms) if isinstance(geom, MultiPolygon) else 1
        rows.append(f"| {i} | `svg/{stem}.svg` | {color} | {thick}\" | {pieces} | {note} |")
        preview.append((stem, color, geom, z, thick))
        z += thick

    # flat colour preview, hung on its point
    body = "\n".join(f'<path d="{path_d(g)}" fill="{COLORS[c]}" fill-rule="evenodd"/>' for _, c, g, _, _ in preview)
    with open(os.path.join(OUT, "preview_flat.svg"), "w") as f:
        f.write(svg_doc(body, "Flat colour preview", 0))

    # placement template (same orientation as the cut files): every layer's outline
    tcols = ["#000", "#888", "#0a0", "#c90", "#c00"]
    body = "\n".join(f'<path d="{path_d(g, CUT_ROT)}" fill="none" stroke="{tcols[k]}" stroke-width="0.015" '
                     f'fill-rule="evenodd"/>' for k, (_, _, g, _, _) in enumerate(preview))
    with open(os.path.join(OUT, "placement_template.svg"), "w") as f:
        f.write(svg_doc(body, "Glue-up placement template (print 1:1)", CUT_ROT))

    # data for the renderer (diamond orientation)
    with open(os.path.join(OUT, "layers.json"), "w") as f:
        json.dump({"size": sheet(0), "layers": [{"stem": s, "color": COLORS[c], "d": path_d(g), "z": z, "t": t}
                                                 for s, c, g, z, t in preview]}, f)

    # thinnest parts of the top layer (a cut-ability check)
    art = layers[-1][2]
    for w in (0.06, 0.08, 0.10):
        lost = art.area - art.buffer(-w / 2).buffer(w / 2).area
        print(f"  top layer area narrower than {w:.2f}\": {lost:.4f} sq in")
    print("\n".join(rows))
    print(f"total stack height: {z:.3f}\"  |  hung on point: {sheet(0):.2f}\" tall")


if __name__ == "__main__":
    main()
