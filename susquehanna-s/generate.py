#!/usr/bin/env python3
"""Generate laser-cut SVG layers for a 14" round stacked 'S' sign (flag background).

Units are inches. Origin of the design is the sign centre with +y up; SVG output
flips y. Run:  python3 generate.py   (needs: pip install shapely fonttools)
"""
import math
import os

import numpy as np

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
S_HEIGHT = 9.94            # height of the letter S
S_WIDTH = 7.44
S_CENTER = (0.52, 0.26)
S_OUTLINE = 0.17           # yellow outline width around the S
SUPPORT_INSET = 0.06       # hidden support under the S is inset this much
MIN_HALF = 0.045          # stripe pieces: features thinner than 0.09" are trimmed
STAR_R = 0.66              # star outer radius (≈1.25" across; photo stars are ~1.4" but the S here is fuller)

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


# ----------------------------------------------------------- flag stripes
# Stripe boundaries measured from a head-on photo of the locomotive logo
# (pixel scans of unit 3634, normalised to the outer circle and scaled to this 14" sign).
# Top to bottom: blue | b0 | white | b1 | red | b2 | white | b3 | red | b4 | white | b5 | red (to rim)
PHOTO_C, PHOTO_RX, PHOTO_RY = (511, 795), 190, 208
BOUNDARY_PX = [
    [(380, 889.5), (390, 889.5), (400, 884.5), (410, 883.5), (420, 880.5), (480, 854.5), (490, 851.5),
     (500, 846.5), (510, 840.5), (520, 836.5), (530, 829.5), (540, 825.5), (600, 788.5), (610, 789.5),
     (620, 783.5), (630, 779.5), (640, 776), (650, 772.5), (660, 767.5), (670, 765.5)],
    [(380, 901.5), (390, 900.5), (400, 898.5), (410, 896.5), (420, 894.5), (430, 893.5), (490, 867.5),
     (500, 862.5), (510, 857.5), (520, 853), (530, 847.5), (540, 842.5), (550, 839.5), (620, 803.5),
     (630, 800.5), (640, 796.5), (650, 793.5), (660, 791.5), (670, 788.5)],
    [(380, 914), (390, 915.5), (400, 914.5), (410, 913.5), (420, 911.5), (430, 910.5), (500, 888),
     (510, 884.5), (520, 879.5), (530, 876.5), (540, 872.5), (550, 869.5), (560, 865.5), (570, 861.5),
     (630, 836.5), (640, 833.5), (650, 831.5), (660, 829.5), (670, 828.5)],
    [(400, 926), (410, 926.5), (420, 925.5), (430, 924.5), (530, 893.5), (540, 890.5), (550, 887.5),
     (560, 885.5), (570, 881.5), (630, 864), (640, 862.5), (650, 860.5), (660, 858.5), (670, 857.5)],
    [(410, 943.5), (430, 943.5), (440, 943.5), (450, 942.5), (460, 941.5), (470, 940.5), (480, 938.5),
     (490, 937.5), (500, 935.5), (630, 906.5), (640, 906.5), (650, 904.5), (660, 904.5)],
    [(440, 966.5), (450, 964.5), (460, 964.5), (470, 963.5), (480, 963.5), (490, 963.5), (500, 962.5),
     (510, 960.5), (520, 959.5), (530, 959.5), (540, 958.5), (550, 957.5), (560, 957.5), (570, 955.5),
     (580, 954.5), (590, 953.5), (600, 951.5), (610, 950.5), (620, 947.5), (630, 946.5)],
]


def px_to_in(x, y):
    return ((x - PHOTO_C[0]) / PHOTO_RX * R_BASE, (PHOTO_C[1] - y) / PHOTO_RY * R_BASE)


def _fit(points, deg=3):
    xs, ys = zip(*(px_to_in(*p) for p in points))
    return np.poly1d(np.polyfit(xs, ys, deg))


BOUNDARIES = [_fit(pts) for pts in BOUNDARY_PX]


def _curve(i, n=240):
    xs = np.linspace(-R_FIELD - 0.3, R_FIELD + 0.3, n)
    return [(x, float(BOUNDARIES[i](x))) for x in xs]


def below(i):
    """Everything below boundary i."""
    c = _curve(i)
    return Polygon(c + [(c[-1][0], -2 * R_BASE), (c[0][0], -2 * R_BASE)])


def band(i):
    """Region between boundary i (top) and i+1 (bottom)."""
    return below(i).difference(below(i + 1))


# Swoosh: white crescent from the left rim, passing behind the S serif and ending in
# the S's lower counter. Top/bottom edges measured from the same photo (pixels).
SWOOSH_TOP_PX = [(390, 859), (400, 856), (410, 854), (420, 849), (460, 831), (470, 828)]
SWOOSH_BOT_PX = [(390, 863), (400, 861), (410, 860), (420, 857), (460, 838), (470, 834)]
SWOOSH_TIPS_PX = [(355, 865), (494, 819)]
SWOOSH_TIP = 0.07        # tips are blunted to this width so they survive cutting


def swoosh():
    tl, tr = (px_to_in(*p) for p in SWOOSH_TIPS_PX)
    top = [tl] + [px_to_in(*p) for p in SWOOSH_TOP_PX] + [tr]
    bot = [tl] + [px_to_in(*p) for p in SWOOSH_BOT_PX] + [tr]

    def smooth(pts, n=200):
        xs, ys = zip(*pts)
        f = np.poly1d(np.polyfit(xs, ys, 3))
        return xs[0], xs[-1], f

    x0, x1, ft = smooth(top)
    _, _, fb = smooth(bot)
    xs = np.linspace(x0, x1, 200)
    upper = [(x, float(ft(x)) + SWOOSH_TIP / 2) for x in xs]
    lower = [(x, float(min(fb(x), ft(x))) - SWOOSH_TIP / 2) for x in xs[::-1]]
    return Polygon(upper + lower).buffer(0.0)


# Star centres (photo pixels, same head-on photo) and size
STARS_PX = [(455, 625), (568, 640), (400, 680), (625, 675), (527, 702),
            (357, 735), (642, 733), (578, 753), (405, 780), (357, 833)]
STAR_ROT = [0.10, -0.05, 0.0, 0.08, 0.0, -0.06, 0.05, 0.12, 0.0, -0.08]


def build():
    field = circle(R_FIELD)
    s = letter_s()
    s_outline = s.buffer(S_OUTLINE, join_style="round")
    support = s_outline.buffer(-SUPPORT_INSET)          # hidden under layer 7

    swish = swoosh()
    stripes = below(0).intersection(field).buffer(-MIN_HALF).buffer(MIN_HALF)
    keepout = unary_union([s_outline, stripes, swish]).buffer(0.07)
    room = field.buffer(-0.02)
    stars = []
    for (px, py), rot in zip(STARS_PX, STAR_ROT):
        x0, y0 = px_to_in(px, py)
        best = None
        # keep each star close to its photo position: try a short nudge first,
        # then shrink it a little before resorting to a longer move
        for scale, reach in ((1.0, 120), (0.9, 120), (0.8, 160), (0.72, 200), (0.72, 2500)):
            for k in range(reach):
                rr, a = 0.03 * k ** 0.5 * 1.6, k * 2.39996
                x, y = x0 + rr * math.cos(a), y0 + rr * math.sin(a)
                st = star(x, y, STAR_R * scale, rot)
                if room.contains(st) and not st.intersects(keepout) and \
                        not any(st.distance(o) < 0.15 for o in stars):
                    best = st
                    break
            if best is not None:
                break
        if best is None:
            raise SystemExit(f"no room for star near {x0:.2f},{y0:.2f}")
        if rr > 0.05 or scale < 1:
            print(f"  star at ({x0:.2f},{y0:.2f}): moved {rr:.2f}\", size {scale:.0%}")
        stars.append(best)

    white = unary_union([stripes, swish, *stars, support])
    reds = [band(1).intersection(field), band(3).intersection(field), below(5).intersection(field)]
    # trim knife-edge points where stripes meet the rim (anything thinner than 2*MIN_HALF)
    red = unary_union(reds).buffer(-MIN_HALF).buffer(MIN_HALF)
    red = unary_union([red, support])

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
