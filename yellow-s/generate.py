#!/usr/bin/env python3
"""Generate laser-cut SVG layers for the stacked yellow 'S' signs.

Two designs, each with an optional raised outer rim:
  round  - black S on a yellow disc inside a black ring (source/logo.png)
  panel  - yellow panel with a black border, a black ring around the S and
           "SUSQUEHANNA" lettered underneath
  --rim  - the outer black ring / border is built up with extra frame layers so it is
           flush with the top of the S (the highest part of the sign)

Usage:
  python3 generate.py                      # all four variants at the default sizes
  python3 generate.py round [--rim] [--size 14]
  python3 generate.py panel [--rim] [--size 14]     (size = panel width)
Needs: pip install shapely numpy fonttools

Units are inches, origin at the design centre, +y up (SVG output flips y).
"""
import argparse
import json
import os

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import MultiPolygon, Point, Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
COLORS = {"black": "#141414", "yellow": "#FFCB33"}

RISER_INSET = 0.06     # hidden riser under the S is inset this much (in)
S_SMOOTH = 0.01        # light open/close on the traced S to drop pixel noise (in)
T_BASE, T_LAYER = 0.25, 0.125   # backer thickness, all other layers

with open(os.path.join(HERE, "s_trace.json")) as f:
    TRACE = json.load(f)
YELLOW_R = TRACE["yellow_r"]   # yellow disc radius / outer radius on the round logo (0.9324)

# ---- panel proportions, measured from the panel logo (pixels of a 272 px wide image)
PANEL_PX = dict(
    w=272, h=300,           # outer size
    border=7,               # black border width
    ring_c=(136, 130),      # ring centre
    ring_r=112, ring_w=7,   # ring outer radius, ring width
    text_top=250, text_bottom=279, text_x=(28, 245),   # "SUSQUEHANNA" cap box
)
PANEL_TEXT = "SUSQUEHANNA"
TEXT_MIN_STROKE = 0.10   # lettering is thickened (if needed) so no stroke is thinner than this


# ------------------------------------------------------------------ geometry helpers
def circle(r, c=(0, 0), n=720):
    return Point(*c).buffer(r, quad_segs=n // 4)


def letter_s(height, center=(0, 0)):
    """The traced S, scaled to the given height and centred (like on the logo) at center.

    The trace is centred on the logo's circle, so scaling about the origin keeps the
    S where it sits on the logo."""
    k = height / 1.42483       # traced S height in outer-radius units
    s = affinity.scale(Polygon(TRACE["s"]).buffer(0), k, k, origin=(0, 0))
    s = affinity.translate(s, *center)
    s = s.buffer(S_SMOOTH).buffer(-2 * S_SMOOTH).buffer(S_SMOOTH)
    return s.simplify(0.003)


class FlattenPen(BasePen):
    """Collects glyph contours as polylines (curves flattened)."""

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
            a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
            self.cur.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                             a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            t = i / self.steps
            a, b, c = (1 - t) ** 2, 2 * (1 - t) * t, t ** 2
            self.cur.append((a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1]))

    def _closePath(self):
        if len(self.cur) > 2:
            self.contours.append(self.cur)
        self.cur = []

    _endPath = _closePath


def lettering(text, x0, x1, y_base, cap):
    """Text in Old Standard Bold, caps scaled to `cap` high and condensed to span x0..x1."""
    font = TTFont(os.path.join(HERE, "fonts", "OldStandard-Bold.ttf"))
    gs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font["hmtx"]
    capu = font["OS/2"].sCapHeight
    glyphs, x = [], 0.0
    for ch in text:
        name = cmap[ord(ch)]
        pen = FlattenPen(gs)
        gs[name].draw(pen)
        g = Polygon()
        for c in pen.contours:      # even-odd: counters cut holes
            g = g.symmetric_difference(Polygon(c).buffer(0))
        glyphs.append(affinity.translate(g, x, 0))
        x += hmtx[name][0]
    txt = unary_union(glyphs)
    minx, _, maxx, _ = txt.bounds
    sy = cap / capu
    sx = (x1 - x0) / (maxx - minx)
    txt = affinity.scale(txt, sx, sy, origin=(0, 0))
    txt = affinity.translate(txt, x0 - minx * sx, y_base)
    # keep every stroke cuttable: thicken until a TEXT_MIN_STROKE opening keeps all of it
    grow = 0.0
    while True:
        t = txt.buffer(grow, join_style="mitre") if grow else txt
        opened = t.buffer(-TEXT_MIN_STROKE / 2).buffer(TEXT_MIN_STROKE / 2)
        if t.difference(opened).area < 0.002 * t.area or grow >= 0.03:
            return t, grow
        grow += 0.005


def stack(base, field, frame, art_full, art_parts, s, rim):
    """Layer list shared by both designs.

    base: backer outline (black). field: yellow piece. frame: outer black band visible
    around the field. art_parts: black pieces at the 3rd level besides the S riser.
    """
    riser = s.buffer(-RISER_INSET, join_style="mitre")
    lay = [("layer1_base_black", "black", base, T_BASE, "backer - outer black ring / border")]
    if rim:
        # field sits inside the rim; the rim is built up from frame rings to the S top
        lay.append(("layer2_yellow_field", "yellow", field, T_LAYER, "yellow field"))
        lay.append(("layer2b_rim_ring", "black", frame, T_LAYER, "rim ring 1 of 3 (same level as layer 2)"))
        lay.append(("layer3_black", "black", unary_union([riser, *art_parts, frame]), T_LAYER,
                    "S riser" + (" + ring + lettering" if art_parts else "") + " + rim ring 2 of 3"))
        lay.append(("layer4_black_s", "black", unary_union([s, frame]), T_LAYER, "black S + rim ring 3 of 3"))
    else:
        lay.append(("layer2_yellow_field", "yellow", field, T_LAYER, "yellow field"))
        lay.append(("layer3_black", "black", unary_union([riser, *art_parts]), T_LAYER,
                    "hidden S riser" + (" + ring + lettering" if art_parts else "")))
        lay.append(("layer4_black_s", "black", s, T_LAYER, "black S - top layer"))
    return lay


def round_design(size, rim):
    R = size / 2
    r_y = YELLOW_R * R
    s = letter_s(1.42483 * R)
    base = circle(R)
    field = circle(r_y)
    frame = base.difference(field)
    lay = stack(base, field, frame, None, [], s, rim)
    return dict(w=size, h=size, layers=lay,
                notes=[f"{size:g}\" round, yellow disc {2 * r_y:.2f}\", rim width {R - r_y:.3f}\""])


def panel_design(width, rim):
    P = PANEL_PX
    k = width / P["w"]
    W, H = width, P["h"] * k

    def pt(x, y):           # image px -> inches, centre origin, +y up
        return ((x - P["w"] / 2) * k, (P["h"] / 2 - y) * k)
    base = box(-W / 2, -H / 2, W / 2, H / 2)
    field = base.buffer(-P["border"] * k, join_style="mitre")
    frame = base.difference(field)
    c = pt(*P["ring_c"])
    r_out, r_in = P["ring_r"] * k, (P["ring_r"] - P["ring_w"]) * k
    ring = circle(r_out, c).difference(circle(r_in, c))
    # the S fills the ring like it fills the yellow disc on the round logo
    s = letter_s(1.42483 * r_in / YELLOW_R, c)
    x0, _ = pt(P["text_x"][0], 0)
    x1, yb = pt(P["text_x"][1], P["text_bottom"])
    cap = (P["text_bottom"] - P["text_top"]) * k
    text, grow = lettering(PANEL_TEXT, x0, x1, yb, cap)
    lay = stack(base, field, frame, None, [ring, text], s, rim)
    return dict(w=W, h=H, layers=lay,
                notes=[f"{W:.2f}\" x {H:.2f}\" panel, border {P['border'] * k:.2f}\", "
                       f"ring {2 * r_out:.2f}\" OD x {(r_out - r_in):.2f}\" wide, letters {cap:.2f}\" tall"
                       + (f" (thickened {grow:.3f}\")" if grow else "")])


# ------------------------------------------------------------------ SVG output
def path_d(geom, W, H):
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    out = []
    for p in polys:
        for ring in [p.exterior, *p.interiors]:
            pts = list(ring.coords)
            out.append("M" + " L".join(f"{x + W / 2:.4f},{H / 2 - y:.4f}" for x, y in pts[:-1]) + " Z")
    return " ".join(out)


def svg_doc(body, title, W, H):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.4f}in" height="{H:.4f}in" '
            f'viewBox="0 0 {W:.4f} {H:.4f}">\n<title>{title}</title>\n{body}\n</svg>\n')


def write(name, design):
    out = os.path.join(HERE, "svg", name)
    os.makedirs(out, exist_ok=True)
    W, H = design["w"], design["h"]
    preview, z, rows = [], 0.0, []
    level = 0.0
    for stem, color, geom, thick, note in design["layers"]:
        if "rim_ring" in stem:          # sits beside the previous layer, same level
            zz = level - thick
        else:
            zz, level = level, level + thick
        d = path_d(geom, W, H)
        cut = f'<path d="{d}" fill="none" stroke="#FF0000" stroke-width="0.01" fill-rule="evenodd"/>'
        with open(os.path.join(out, stem + ".svg"), "w") as f:
            f.write(svg_doc(cut, f"{stem} - {note} - paint {color}", W, H))
        preview.append((stem, color, d, zz, thick))
        pieces = len(geom.geoms) if isinstance(geom, MultiPolygon) else 1
        rows.append(f"  {stem:22s} {color:6s} {thick}\"  {pieces:3d} piece(s)  {note}")

    body = "\n".join(f'<path d="{d}" fill="{COLORS[c]}" fill-rule="evenodd"/>'
                     for _, c, d, _, _ in sorted(preview, key=lambda p: p[3]))
    with open(os.path.join(out, "preview_flat.svg"), "w") as f:
        f.write(svg_doc(body, "Flat colour preview", W, H))
    tcols = ["#000", "#c90", "#0a0", "#c00", "#808", "#00c"]
    body = "\n".join(f'<path d="{d}" fill="none" stroke="{tcols[i % 6]}" stroke-width="0.015" '
                     f'fill-rule="evenodd"/>' for i, (_, _, d, _, _) in enumerate(preview))
    with open(os.path.join(out, "placement_template.svg"), "w") as f:
        f.write(svg_doc(body, "Glue-up placement template (print 1:1)", W, H))
    with open(os.path.join(out, "layers.json"), "w") as f:
        json.dump({"W": W, "H": H, "layers": [{"stem": s, "color": COLORS[c], "d": d, "z": zz, "t": t}
                                              for s, c, d, zz, t in preview]}, f)
    print(f"svg/{name}/  - {design['notes'][0]}")
    print("\n".join(rows))
    print(f"  total height {level:.3f}\"")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("design", nargs="?", choices=["round", "panel"])
    ap.add_argument("--rim", action="store_true")
    ap.add_argument("--size", type=float, default=14.0)
    a = ap.parse_args()
    jobs = [(a.design, a.rim)] if a.design else [("round", False), ("round", True),
                                                   ("panel", False), ("panel", True)]
    for design, rim in jobs:
        fn = round_design if design == "round" else panel_design
        name = design + ("_rim" if rim else "") + ("" if a.size == 14.0 else f"_{a.size:g}in")
        write(name, fn(a.size, rim))


if __name__ == "__main__":
    main()
