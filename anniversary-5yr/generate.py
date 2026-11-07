#!/usr/bin/env python3
"""5th wedding anniversary design for a 4" x 4" slate coaster (laser engrave).

Slate engraves LIGHT (the laser bleaches it pale grey), so everything drawn here is
engraved and the dark slate is the background. All text is converted to outlines, so
the laser software doesn't need the fonts.

Usage:
    python3 generate.py                                   # defaults below
    python3 generate.py --years 2021 2026
    python3 generate.py --names "Alex & Sam"              # adds the names under the 5th
    python3 generate.py --tile 4 --design 3.5

Writes slate_5th_anniversary[_<names>].svg (black fill = engrave, blue = tile guide only).
"""
import argparse
import math
import os
import re

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT_FONT = os.path.join(HERE, "fonts", "great-vibes-latin-400-normal.woff2")
SERIF_FONT = os.path.join(HERE, "fonts", "cormorant-garamond-latin-600-normal.woff2")


# ---------------------------------------------------------------- text → polygons
class FlatPen(BasePen):
    """Collects glyph contours as point lists, flattening curves."""

    def __init__(self, glyphset, steps=12):
        super().__init__(glyphset)
        self.contours, self.cur, self.steps = [], [], steps

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            u = 1 - t
            self.cur.append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                             u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            u = 1 - t
            self.cur.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                             u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))

    def _closePath(self):
        if len(self.cur) >= 3:
            self.contours.append(self.cur)
        self.cur = []

    _endPath = _closePath


class Font:
    def __init__(self, path):
        self.f = TTFont(path)
        self.gs = self.f.getGlyphSet()
        self.cmap = self.f.getBestCmap()
        self.upm = self.f["head"].unitsPerEm
        self.cap = getattr(self.f["OS/2"], "sCapHeight", 0) or self.upm * 0.7

    def text(self, s, cap_height, tracking=0.0):
        """Outline of `s`, scaled so capitals are `cap_height` tall, baseline-left at (0,0).
        tracking is extra space between letters, as a fraction of cap height.
        Digits use lining figures where the font has them (Cormorant defaults to old-style)."""
        k = cap_height / self.cap
        x, shapes = 0.0, []
        for ch in s:
            name = self.cmap.get(ord(ch))
            if name and ch.isdigit() and name + ".lf" in self.gs:
                name += ".lf"
            if name is None:
                raise SystemExit(f"character {ch!r} is not in {os.path.basename(self.f.reader.file.name)}")
            pen = FlatPen(self.gs)
            self.gs[name].draw(pen)
            glyph = Polygon()
            for c in pen.contours:      # even-odd fill: XOR the contours
                poly = Polygon(c).buffer(0)
                glyph = glyph.symmetric_difference(poly)
            shapes.append(affinity.translate(glyph, x, 0))
            x += self.gs[name].width + tracking * self.cap
        geom = unary_union(shapes)
        return affinity.scale(geom, k, k, origin=(0, 0))


def centred(geom, cx, y_baseline_shift=0.0):
    """Centre geom horizontally on cx and move its baseline to y_baseline_shift."""
    x0, _, x1, _ = geom.bounds
    return affinity.translate(geom, cx - (x0 + x1) / 2, y_baseline_shift)


# ---------------------------------------------------------------- ornaments
def leaf(length, width):
    """Pointed leaf (vesica), base at origin pointing along +x."""
    r = (length**2 / 4 + width**2 / 4) / width          # circle radius for the arcs
    d = r - width / 2
    a = Point(length / 2, d).buffer(r, resolution=64)
    b = Point(length / 2, -d).buffer(r, resolution=64)
    return a.intersection(b)


def laurel_branch(radius, a_start, a_end, n, side):
    """Leaves along an arc from angle a_start (base) to a_end (tip), degrees.
    side=+1 runs counter-clockwise, -1 clockwise. Returns one geometry."""
    stem_w = 0.022
    pts = []
    steps = 80
    for i in range(steps + 1):
        a = math.radians(a_start + (a_end - a_start) * i / steps)
        pts.append((radius * math.cos(a), radius * math.sin(a)))
    from shapely.geometry import LineString
    stem = LineString(pts).buffer(stem_w / 2, cap_style="round")
    parts = [stem]
    for i in range(n):
        t = (i + 0.5) / n
        a = a_start + (a_end - a_start) * t
        size = 1.0 - 0.45 * t                           # leaves shrink towards the tip
        L, W = 0.30 * size, 0.115 * size
        ar = math.radians(a)
        px, py = radius * math.cos(ar), radius * math.sin(ar)
        tangent = a + 90 * side                         # direction of travel along the stem
        for out in (+1, -1):                            # one leaf outside, one inside
            ang = tangent + out * 38 * side * -1
            lf = affinity.rotate(leaf(L, W), ang, origin=(0, 0))
            parts.append(affinity.translate(lf, px, py))
    # a leaf at the tip
    ar = math.radians(a_end)
    tip = affinity.rotate(leaf(0.17, 0.07), a_end + 90 * side, origin=(0, 0))
    parts.append(affinity.translate(tip, radius * math.cos(ar), radius * math.sin(ar)))
    return unary_union(parts)


def heart(size):
    """Heart about `size` wide, centred on the origin."""
    r = size / 4
    a = Point(-r, 0).buffer(r, resolution=48)
    b = Point(r, 0).buffer(r, resolution=48)
    tri = Polygon([(-2 * r * 0.98, -r * 0.35), (2 * r * 0.98, -r * 0.35), (0, -size * 0.78)])
    left = Polygon([(-2 * r, 0), (0, 0), (0, -size * 0.78)])
    h = unary_union([a, b, tri, left, affinity.scale(left, -1, 1, origin=(0, 0))])
    h = h.buffer(0.004).buffer(-0.004)
    _, y0, _, y1 = h.bounds
    return affinity.translate(h, 0, -(y0 + y1) / 2)


def rings(r, w, gap):
    """Two interlocking wedding rings, centred on the origin, `r` outer radius."""
    off = r * 0.62
    a = Point(-off, 0).buffer(r, resolution=96).difference(Point(-off, 0).buffer(r - w, resolution=96))
    b = Point(off, 0).buffer(r, resolution=96).difference(Point(off, 0).buffer(r - w, resolution=96))
    # over/under: B passes over A at the top crossing, A over B at the bottom one
    top_cut = a.intersection(b.buffer(gap))
    top_cut = unary_union([g for g in getattr(top_cut, "geoms", [top_cut]) if g.centroid.y > 0])
    bot_cut = b.intersection(a.buffer(gap))
    bot_cut = unary_union([g for g in getattr(bot_cut, "geoms", [bot_cut]) if g.centroid.y < 0])
    return unary_union([a.difference(top_cut), b.difference(bot_cut)])


# ---------------------------------------------------------------- layout
def artwork(years, names):
    """Design in inches on a 3.5" circle centred on (0,0). Scaled to --design later."""
    script, serif = Font(SCRIPT_FONT), Font(SERIF_FONT)
    parts = []

    # laurel wreath: two branches from the bottom up each side, open at the top
    R = 1.62
    parts.append(laurel_branch(R, -78, 52, 8, +1))         # right side, going up (CCW)
    parts.append(affinity.scale(parts[-1], -1, 1, origin=(0, 0)))   # mirror for the left
    parts.append(affinity.translate(heart(0.19), 0, -R))  # heart where the stems meet
    parts.append(affinity.translate(heart(0.13), 0, R - 0.05))   # small heart in the open top

    # centre block, stacked top-down by actual outline bounds
    rows = []                                              # (geometry, gap above it)
    rows.append((script.text("Happy", 0.40), 0))

    five = serif.text("5", 0.78 if names else 1.00)        # smaller to make room for names
    th = serif.text("th", 0.25 if names else 0.30)
    fx1, fy1 = five.bounds[2], five.bounds[3]
    th = affinity.translate(th, fx1 + 0.035 - th.bounds[0], fy1 - th.bounds[3])  # tops aligned
    rows.append((unary_union([five, th]), 0.10))

    rows.append((serif.text("ANNIVERSARY", 0.165, tracking=0.20), 0.13))

    if names:
        nm = script.text(names, 0.24)
        nx0, _, nx1, _ = nm.bounds
        if nx1 - nx0 > 2.3:                                  # keep long names inside the wreath
            k = 2.3 / (nx1 - nx0)
            nm = affinity.scale(nm, k, k, origin=(0, 0))
        rows.append((nm, 0.10))

    # years with interlocking rings between them
    rg = rings(0.105, 0.022, 0.018)
    yr_h = 0.13
    y0 = serif.text(str(years[0]), yr_h, tracking=0.12)
    y1 = serif.text(str(years[1]), yr_h, tracking=0.12)
    gap = 0.12
    w0 = y0.bounds[2] - y0.bounds[0]
    rw = rg.bounds[2] - rg.bounds[0]
    yrs = unary_union([affinity.translate(y0, -rw / 2 - gap - w0 - y0.bounds[0], 0),
                       affinity.translate(rg, 0, yr_h / 2),
                       affinity.translate(y1, rw / 2 + gap - y1.bounds[0], 0)])
    rows.append((yrs, 0.12))

    # stack, then centre the whole block vertically (nudged up a touch: the wreath is open at the top)
    y, placed = 0.0, []
    for g, gap_above in rows:
        y -= gap_above
        x0, gy0, x1, gy1 = g.bounds
        placed.append(affinity.translate(g, -(x0 + x1) / 2, y - gy1))
        y -= gy1 - gy0
    block = unary_union(placed)
    by0, by1 = block.bounds[1], block.bounds[3]
    parts.append(affinity.translate(block, 0, 0.04 - (by0 + by1) / 2))

    return unary_union(parts)


def svg(geom, tile, design, title):
    # the wreath (plus leaves) is about 3.5" across at scale 1
    x0, y0, x1, y1 = geom.bounds
    span = max(x1 - x0, y1 - y0)
    k = design / span
    geom = affinity.scale(geom, k, k, origin=(0, 0))
    x0, y0, x1, y1 = geom.bounds
    geom = affinity.translate(geom, -(x0 + x1) / 2, -(y0 + y1) / 2)
    c = tile / 2
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    d = []
    for p in polys:
        for ring in [p.exterior, *p.interiors]:
            pts = list(ring.coords)[:-1]
            d.append("M" + " L".join(f"{x + c:.4f},{c - y:.4f}" for x, y in pts) + " Z")
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{tile}in" height="{tile}in" '
            f'viewBox="0 0 {tile} {tile}">\n'
            f'<title>{title} - {design}in design on {tile}in slate tile - '
            f'black = engrave, blue = alignment guide only</title>\n'
            f'<g id="guide"><rect x="0.002" y="0.002" width="{tile - 0.004}" height="{tile - 0.004}" '
            f'fill="none" stroke="#0000FF" stroke-width="0.004"/></g>\n'
            f'<g id="engrave"><path d="{" ".join(d)}" fill="#000000" fill-rule="evenodd"/></g>\n'
            f'</svg>\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", nargs=2, type=int, default=[2021, 2026], metavar=("WED", "NOW"))
    ap.add_argument("--names", default="", help='e.g. "Alex & Sam" (script font)')
    ap.add_argument("--tile", type=float, default=4.0, help="tile size, inches")
    ap.add_argument("--design", type=float, default=3.5, help="artwork size, inches")
    a = ap.parse_args()
    geom = artwork(a.years, a.names)
    slug = "_" + re.sub(r"[^a-z0-9]+", "_", a.names.lower()).strip("_") if a.names else ""
    out = os.path.join(HERE, f"slate_5th_anniversary{slug}.svg")
    with open(out, "w") as f:
        f.write(svg(geom, a.tile, a.design, "5th wedding anniversary slate coaster"))
    print("wrote", os.path.relpath(out, HERE))


if __name__ == "__main__":
    main()
