#!/usr/bin/env python3
"""Generate laser-cut SVG layers for a 14" round stacked Bangor and Aroostook sign.

Units are inches, origin at the sign centre, +y up (SVG output flips y).
    pip install shapely numpy fonttools
    python3 generate.py          # writes svg/ and jigs/
"""
import json
import math
import os

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.ops import unary_union

import logo

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "svg")
JIGS = os.path.join(HERE, "jigs")

# ---------------------------------------------------------------- dimensions
DIAM = 14.0
R_BASE = DIAM / 2          # 7.00  gold outer rim (base)
R_BLUE = 6.85              # blue lettering band
R_GOLD = 5.45              # inner gold pinstripe
R_FIELD = 5.30             # white field
R_LOGO = 4.75              # the triangle's corners touch a circle of this radius
LOGO_DROP = 0.0            # move the logo down (in) from optical centre, if wanted

FONT = os.path.join(HERE, "fonts", "Oswald-Bold.woff")
TEXT_TOP = "BANGOR AND AROOSTOOK"
TEXT_BOTTOM = "RAILROAD"
CAP = 0.82                 # cap height of the lettering
TOP_SPAN = 146             # degrees the top line covers; sets the letter spacing
WORD_GAP = 0.22            # extra space at word breaks (in, on top of the font's space)
DIAMOND = 0.62             # separator diamonds (height along the band, in)
ART_ROUND = 0.015          # tiny corner rounding on the white logo pieces (laser-friendly)
LEAF_ROUND = 0.03          # the leaf pieces' sharp tips are rounded a little more
JIG_CLEAR = 0.012          # clearance around pieces in the glue-up jigs

COLORS = {
    "gold": "#C9A24B",
    "blue": "#1F6FB4",
    "white": "#F4F2EA",
    "teal": "#0F9C9A",
}


def circle(r, n=720):
    return Point(0, 0).buffer(r, quad_segs=n // 4)


# ---------------------------------------------------------------------- logo
def logo_parts():
    """The logo, scaled and centred on the sign (inches, +y up)."""
    parts = logo.logo()
    tri = parts["triangle"]
    # centre of the circle through the three corners: on the axis, equidistant from
    # the apex and the base corners
    minx, miny, maxx, maxy = tri.bounds         # y down: miny = apex, maxy = base
    pts = list(tri.exterior.coords)

    def far(cy):
        return max(math.hypot(x, y - cy) for x, y in pts)
    lo, hi = miny, maxy
    for _ in range(60):                          # minimise the enclosing radius
        a, b = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        lo, hi = (lo, b) if far(a) < far(b) else (a, hi)
    cy = (lo + hi) / 2
    s = R_LOGO / far(cy)

    def place(g):
        g = affinity.translate(g, 0, -cy)
        g = affinity.scale(g, s, -s, origin=(0, 0))      # flip y: image -> sign
        return affinity.translate(g, 0, -LOGO_DROP)
    art = {k: place(v) for k, v in parts.items()}
    for k, r in (("upper", ART_ROUND), ("lower", ART_ROUND), ("leaf", LEAF_ROUND)):
        art[k] = art[k].buffer(-r).buffer(r)
    return art


# ------------------------------------------------------------------ lettering
class FlatPen(BasePen):
    """Collects glyph contours as point lists, flattening curves."""

    def __init__(self, glyphset, steps=12):
        super().__init__(glyphset)
        self.rings, self.cur, self.steps = [], [], steps

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            u = 1 - t
            self.cur.append(tuple(u ** 3 * a + 3 * u * u * t * b + 3 * u * t * t * c + t ** 3 * d
                                  for a, b, c, d in zip(p0, p1, p2, p3)))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            u = 1 - t
            self.cur.append(tuple(u * u * a + 2 * u * t * b + t * t * c for a, b, c in zip(p0, p1, p2)))

    def _closePath(self):
        if len(self.cur) > 2:
            self.rings.append(self.cur)
        self.cur = []

    _endPath = _closePath


class Font:
    def __init__(self, path, cap):
        f = TTFont(path)
        self.gs, self.cmap = f.getGlyphSet(), f.getBestCmap()
        self.k = cap / f["OS/2"].sCapHeight

    def advance(self, ch):
        return self.gs[self.cmap[ord(ch)]].width * self.k

    def glyph(self, ch):
        """Glyph outline in inches, baseline at y=0, horizontally centred on its advance."""
        g = self.gs[self.cmap[ord(ch)]]
        pen = FlatPen(self.gs)
        g.draw(pen)
        shape = Polygon()
        for ring in pen.rings:
            shape = shape.symmetric_difference(Polygon(ring).buffer(0))
        return affinity.scale(affinity.translate(shape, -g.width / 2, 0), self.k, self.k, origin=(0, 0))


def layout(font, text, tracking):
    """(char, centre position along the line) for each non-space character; line centred on 0."""
    pos, x = [], 0.0
    for i, ch in enumerate(text):
        w = font.advance(ch)
        if ch == " ":
            x += w + WORD_GAP
            continue
        pos.append((ch, x + w / 2))
        x += w + (tracking if i + 1 < len(text) and text[i + 1] != " " else 0)
    return [(c, p - x / 2) for c, p in pos], x


def diamond(h):
    """Separator: a diamond, long axis along the band."""
    return Polygon([(h / 2, 0), (0, h * 0.3), (-h / 2, 0), (0, -h * 0.3)])


def lettering():
    font = Font(FONT, CAP)
    r_mid = (R_BLUE + R_GOLD) / 2
    # letter spacing that makes the top line cover TOP_SPAN degrees at the band's middle
    lo, hi = 0.0, 1.0
    for _ in range(50):
        t = (lo + hi) / 2
        _, w = layout(font, TEXT_TOP, t)
        lo, hi = (t, hi) if w / r_mid < math.radians(TOP_SPAN) else (lo, t)
    tracking = (lo + hi) / 2
    pieces = []
    # top: letters stand on the inner side of the band, reading clockwise
    top, _ = layout(font, TEXT_TOP, tracking)
    for ch, s in top:
        g = affinity.translate(font.glyph(ch), 0, r_mid - CAP / 2)
        pieces.append((ch, affinity.rotate(g, -math.degrees(s / r_mid), origin=(0, 0))))
    # bottom: letters stand on the outer side, upright, reading counter-clockwise
    bot, wb = layout(font, TEXT_BOTTOM, tracking)
    for ch, s in bot:
        g = affinity.translate(font.glyph(ch), 0, -r_mid - CAP / 2)
        pieces.append((ch, affinity.rotate(g, math.degrees(s / r_mid), origin=(0, 0))))
    # separator diamonds halfway between the end of the top line and the bottom line
    a_top = TOP_SPAN / 2
    a_bot = math.degrees(wb / r_mid) / 2
    mid = (90 - a_top + (-90 + a_bot)) / 2           # angle (deg, from +x) on the right side
    for ang in (mid, 180 - mid):
        d = affinity.rotate(affinity.translate(diamond(DIAMOND), 0, r_mid), ang - 90, origin=(0, 0))
        pieces.append(("◆", d))
    print(f"  lettering: cap {CAP}\", tracking {tracking:.3f}\", top {TOP_SPAN} deg, "
          f"bottom {2 * a_bot:.0f} deg, separators {-mid:.0f} deg below horizontal")
    return pieces


# ------------------------------------------------------------------- layers
def build():
    art = logo_parts()
    letters = lettering()
    white_art = unary_union([art["upper"], art["lower"], art["leaf"]])
    text = unary_union([g for _, g in letters])
    return [
        # (stem, colour, geometry, z of the surface it is glued to, thickness, note)
        ("layer1_base_gold", "gold", circle(R_BASE), 0.0, 0.25, "14.00\" disc - gold outer rim / backer"),
        ("layer2_blue_band", "blue", circle(R_BLUE), 0.25, 0.125, "13.70\" disc - blue lettering band"),
        ("layer3_gold_ring", "gold", circle(R_GOLD), 0.375, 0.125, "10.90\" disc - gold pinstripe"),
        ("layer4_white_field", "white", circle(R_FIELD), 0.5, 0.125, "10.60\" disc - white field"),
        ("layer5_teal_triangle", "teal", art["triangle"], 0.625, 0.125, "teal triangle"),
        ("layer6_white_logo", "white", white_art, 0.75, 0.125,
         "white A + upper wave, lower wave, 7 leaf pieces"),
        ("layer7_white_lettering", "white", text, 0.375, 0.125,
         "white letters + 2 diamonds - glued onto the blue band (layer 2)"),
    ], art, letters


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


def cut(geom):
    return f'<path d="{path_d(geom)}" fill="none" stroke="#FF0000" stroke-width="0.01" fill-rule="evenodd"/>'


def thinnest(geom):
    """Approximate thinnest feature: largest r such that opening by r keeps nearly all area."""
    lo, hi = 0.0, 0.5
    for _ in range(20):
        r = (lo + hi) / 2
        kept = geom.buffer(-r).buffer(r).area / geom.area
        lo, hi = (r, hi) if kept > 0.995 else (lo, r)
    return 2 * lo


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(JIGS, exist_ok=True)
    layers, art, letters = build()
    preview, rows = [], []
    for i, (stem, color, geom, z, thick, note) in enumerate(layers, 1):
        with open(os.path.join(OUT, stem + ".svg"), "w") as f:
            f.write(svg_doc(cut(geom), f"Layer {i} - {note} - paint {color}"))
        d = path_d(geom)
        preview.append(dict(stem=stem, color=COLORS[color], d=d, z=z, t=thick))
        pieces = len(geom.geoms) if isinstance(geom, MultiPolygon) else 1
        rows.append(f"| {i} | `svg/{stem}.svg` | {color} | {thick}\" | {pieces} | {note} |")

    body = "\n".join(f'<path d="{L["d"]}" fill="{L["color"]}" fill-rule="evenodd"/>' for L in preview)
    with open(os.path.join(OUT, "preview_flat.svg"), "w") as f:
        f.write(svg_doc(body, "Flat colour preview"))
    tcols = ["#000", "#00c", "#c90", "#888", "#0a0", "#c00", "#808"]
    body = "\n".join(f'<path d="{L["d"]}" fill="none" stroke="{tcols[k]}" stroke-width="0.015" '
                     f'fill-rule="evenodd"/>' for k, L in enumerate(preview))
    with open(os.path.join(OUT, "placement_template.svg"), "w") as f:
        f.write(svg_doc(body, "Glue-up placement template (print 1:1)"))
    with open(os.path.join(OUT, "layers.json"), "w") as f:
        json.dump(preview, f)

    # ---- glue-up jigs (cut from card or scrap; they are not part of the sign)
    letters_u = unary_union([g for _, g in letters])
    letter_holes = unary_union([Polygon(p.exterior) for p in
                                (letters_u.geoms if isinstance(letters_u, MultiPolygon) else [letters_u])])
    jigs = {
        # sits on the blue band, its inner edge against the raised gold ring: self-centring
        "jig_lettering_ring": (circle(R_BLUE).difference(circle(R_GOLD + JIG_CLEAR))
                               .difference(letter_holes.buffer(JIG_CLEAR)),
                               "Lettering jig - lay on the blue band against the gold ring, drop letters in"),
        # same size as the white field: lay it on the field, edges flush, drop the triangle in
        "jig_triangle": (circle(R_FIELD).difference(art["triangle"].buffer(JIG_CLEAR)),
                         "Triangle jig - lay on the white field, edges flush, drop the teal triangle in"),
        # same shape as the teal triangle: lay it on the triangle, edges flush, drop the art in
        "jig_logo_art": (art["triangle"].difference(
            unary_union([Polygon(p.exterior) for p in
                         unary_union([art["upper"], art["lower"], art["leaf"]]).geoms]).buffer(JIG_CLEAR)),
                         "Logo jig - lay on the teal triangle, edges flush, drop the white pieces in"),
    }
    for stem, (g, title) in jigs.items():
        with open(os.path.join(JIGS, stem + ".svg"), "w") as f:
            f.write(svg_doc(cut(g), title))

    print("\n".join(rows))
    for name, g in (("logo art", unary_union([art["upper"], art["lower"], art["leaf"]])),
                    ("leaf", art["leaf"]), ("lettering", letters_u)):
        print(f"  thinnest {name}: ~{thinnest(g):.2f}\"")
    tri = art["triangle"].bounds
    print(f"  triangle {tri[2] - tri[0]:.2f}\" wide x {tri[3] - tri[1]:.2f}\" tall")
    print(f"  stack height at the logo: {layers[5][3] + layers[5][4]:.3f}\"")


if __name__ == "__main__":
    main()
