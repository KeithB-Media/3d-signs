#!/usr/bin/env python3
"""Generate laser-cut SVG layers for a 14" round stacked 'S' sign (flag background).

Units are inches. Origin of the design is the sign centre with +y up; SVG output
flips y. Run:  python3 generate.py   (needs: pip install shapely fonttools)
"""
import math
import os

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "svg")

# ---------------------------------------------------------------- dimensions
DIAM = 14.0
R_BASE = DIAM / 2          # 7.00  black outer rim (base)
R_YELLOW = 6.80            # yellow pinstripe ring
R_BLACK = 6.62             # inner black ring
R_FIELD = 6.45             # blue field / flag area
S_HEIGHT = 9.40            # height of the letter S
S_WIDTH = 6.70
S_CENTER = (0.10, -0.30)
S_OUTLINE = 0.17           # yellow outline width around the S
SUPPORT_INSET = 0.06       # hidden support under the S is inset this much
STAR_R = 0.43              # star outer radius (≈0.86" across)

COLORS = {
    "black": "#141414",
    "yellow": "#F6CF14",
    "blue": "#1F2F82",
    "white": "#F5F5F2",
    "red": "#D0202E",
}


# ------------------------------------------------------------------ helpers
def circle(r, n=720):
    return Point(0, 0).buffer(r, quad_segs=n // 4)


class FlattenPen(BasePen):
    """Collect glyph contours as polylines (curves sampled)."""

    def __init__(self, glyphSet, steps=24):
        super().__init__(glyphSet)
        self.contours, self.cur, self.steps = [], [], steps

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            mt = 1 - t
            self.cur.append((
                mt**3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t**3 * p3[0],
                mt**3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t**3 * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            mt = 1 - t
            self.cur.append((mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
                             mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]))

    def _closePath(self):
        if len(self.cur) > 2:
            self.contours.append(self.cur)
        self.cur = []

    _endPath = _closePath


def letter_s():
    font = TTFont(os.path.join(HERE, "fonts", "OldStandard-Bold.ttf"))
    gs = font.getGlyphSet()
    pen = FlattenPen(gs)
    gs[font.getBestCmap()[ord("S")]].draw(pen)
    shape = Polygon()
    for c in pen.contours:
        shape = shape.symmetric_difference(Polygon(c).buffer(0))
    x0, y0, x1, y1 = shape.bounds
    shape = affinity.translate(shape, -(x0 + x1) / 2, -(y0 + y1) / 2)
    shape = affinity.scale(shape, S_WIDTH / (x1 - x0), S_HEIGHT / (y1 - y0), origin=(0, 0))
    return affinity.translate(shape, *S_CENTER)


def star(cx, cy, r, rot=0.0):
    pts = []
    for i in range(10):
        a = math.pi / 2 + rot + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.40
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return Polygon(pts)


# Flag stripes: boundary curves in normalised coords (u, v in [-1, 1] of R_FIELD)
def wave_top(u):
    return -0.10 + 0.13 * u - 0.05 * math.cos(math.pi * u)


def band_t(u):
    return 0.150 + 0.030 * u     # stripe thickness, a touch wider on the right


def boundary(i, u):
    return wave_top(u) - i * band_t(u)


def band(i, n=200):
    """Region between boundary i (top) and i+1 (bottom), scaled to inches."""
    us = [-1.05 + 2.1 * k / n for k in range(n + 1)]
    top = [(u * R_FIELD, boundary(i, u) * R_FIELD) for u in us]
    bot = [(u * R_FIELD, boundary(i + 1, u) * R_FIELD) for u in reversed(us)]
    return Polygon(top + bot)


def below(i, n=200):
    us = [-1.05 + 2.1 * k / n for k in range(n + 1)]
    top = [(u * R_FIELD, boundary(i, u) * R_FIELD) for u in us]
    return Polygon(top + [(1.05 * R_FIELD, -2 * R_FIELD), (-1.05 * R_FIELD, -2 * R_FIELD)])


def swoosh(n=120):
    """Thin white crescent in the blue field just above the stripes (left side)."""
    a, b = -0.97, -0.18
    us = [a + (b - a) * k / n for k in range(n + 1)]
    lo = [(u, wave_top(u) + 0.055) for u in us]
    hi = [(u, wave_top(u) + 0.055 + 0.045 * abs(math.sin(math.pi * (u - a) / (b - a))) ** 0.8)
          for u in reversed(us)]
    return affinity.scale(Polygon(lo + hi), R_FIELD, R_FIELD, origin=(0, 0))


# Star positions (fraction of R_BASE), traced from the reference photos
STARS = [(-0.15, 0.80, 0.10), (-0.51, 0.62, -0.05), (0.50, 0.66, 0.05),
         (-0.75, 0.38, 0.0), (-0.56, 0.12, 0.08), (-0.84, -0.06, -0.06),
         (0.16, 0.33, 0.0), (0.79, 0.38, -0.08), (0.80, 0.14, 0.05),
         (0.48, 0.05, 0.10)]


def build():
    field = circle(R_FIELD)
    s = letter_s()
    s_outline = s.buffer(S_OUTLINE, join_style="round")
    support = s_outline.buffer(-SUPPORT_INSET)          # hidden under layer 7

    swish = swoosh()
    stripes = below(0).intersection(field)
    keepout = unary_union([s_outline, stripes, swish]).buffer(0.14)
    room = field.buffer(-0.18)
    stars = []
    for u, v, rot in STARS:
        x0, y0 = u * R_BASE, v * R_BASE
        best = None
        for k in range(400):          # spiral search for the nearest clear spot
            rr, a = 0.05 * k ** 0.5 * 1.6, k * 2.39996
            x, y = x0 + rr * math.cos(a), y0 + rr * math.sin(a)
            st = star(x, y, STAR_R, rot)
            if room.contains(st) and not st.intersects(keepout):
                best = st
                break
        if best is None:
            raise SystemExit(f"no room for star near {u},{v}")
        stars.append(best)

    white = unary_union([stripes, swish, *stars, support])
    reds = [band(i).intersection(field) for i in range(1, 12, 2)]
    red = unary_union(reds + [support])

    return [
        # (file stem, colour, geometry, thickness in, note)
        ("layer1_base_black", "black", circle(R_BASE), 0.25, "14.00\" disc - outer black rim / backer"),
        ("layer2_yellow_ring", "yellow", circle(R_YELLOW), 0.125, "13.60\" disc - yellow pinstripe"),
        ("layer3_black_ring", "black", circle(R_BLACK), 0.125, "13.24\" disc - inner black ring"),
        ("layer4_blue_field", "blue", field, 0.125, "12.90\" disc - blue field"),
        ("layer5_white_stripes_stars", "white", white, 0.125,
         "white stripes, swoosh and 10 stars (+ hidden S support)"),
        ("layer6_red_stripes", "red", red, 0.125, "red stripes (+ hidden S support)"),
        ("layer7_yellow_s_outline", "yellow", s_outline, 0.125, "yellow outline of the S"),
        ("layer8_black_s", "black", s, 0.125, "black S - top layer"),
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
        d = path_d(geom)
        cut = f'<path d="{d}" fill="none" stroke="#FF0000" stroke-width="0.01" fill-rule="evenodd"/>'
        with open(os.path.join(OUT, stem + ".svg"), "w") as f:
            f.write(svg_doc(cut, f"Layer {i} - {note} - paint {color}"))
        preview.append((stem, color, d, z, thick))
        pieces = len(geom.geoms) if isinstance(geom, MultiPolygon) else 1
        rows.append(f"| {i} | `svg/{stem}.svg` | {color} | {thick}\" | {pieces} | {note} |")
        z += thick

    # flat colour preview (layers stacked, all colours)
    body = "\n".join(f'<path d="{d}" fill="{COLORS[c]}" fill-rule="evenodd"/>' for _, c, d, _, _ in preview)
    with open(os.path.join(OUT, "preview_flat.svg"), "w") as f:
        f.write(svg_doc(body, "Flat colour preview"))

    # placement template: outlines of every layer in a different stroke colour
    tcols = ["#000", "#c90", "#555", "#00c", "#0a0", "#c00", "#f80", "#808"]
    body = "\n".join(f'<path d="{d}" fill="none" stroke="{tcols[k]}" stroke-width="0.015" fill-rule="evenodd"/>'
                     for k, (_, _, d, _, _) in enumerate(preview))
    with open(os.path.join(OUT, "placement_template.svg"), "w") as f:
        f.write(svg_doc(body, "Glue-up placement template (print 1:1)"))

    # data for the renderer
    import json
    with open(os.path.join(OUT, "layers.json"), "w") as f:
        json.dump([{"stem": s, "color": COLORS[c], "d": d, "z": z, "t": t}
                   for s, c, d, z, t in preview], f)
    print("\n".join(rows))
    print(f"total stack height: {z:.3f}\"")


if __name__ == "__main__":
    main()
