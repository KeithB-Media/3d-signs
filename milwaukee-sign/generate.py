"""Milwaukee-style stacked laser-cut sign (personal gift, not for sale).

Builds a heavy, sheared block-letter "MILWAUKEE" wordmark on a red panel with an
optional "NOTHING BUT HEAVY DUTY" tagline, and writes one cut SVG per layer.
All units are inches; y points up internally and is flipped on output.
"""
import json
import math
import os

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "svg")

# ------------------------------------------------------------------ settings
W, H = 24.0, 7.0          # sign size
CORNER = 0.5              # backer corner radius
RIM = 0.30                # black rim showing around the red panel
RED_CORNER = 0.25
CAP = 3.0                 # wordmark cap height (shrunk if needed to fit)
SIDE = 0.75               # min clear red between the letter outline and panel edge
SLANT = 13.0              # italic shear, degrees
TRACK = 0.075             # gap between letters, in cap heights
OUTLINE = 0.16            # black outline around the white letters
TAGLINE = True            # include "NOTHING BUT HEAVY DUTY"
TAG_TEXT = "NOTHING BUT HEAVY DUTY"
TAG_CAP = 0.62            # tagline cap height
TAG_FONT = "/usr/share/fonts/opentype/inter/Inter-BlackItalic.otf"
TAG_GAP = 0.42            # space between wordmark and tagline

COLORS = {"black": "#141414", "red": "#d50f25", "white": "#f7f7f5"}

T = 0.27                  # stroke weight of the block letters (in cap heights)
BAR = 0.235               # horizontal bar weight (E, L)


# ------------------------------------------------------------------ helpers
def rrect(w, h, r):
    return box(-w / 2 + r, -h / 2 + r, w / 2 - r, h / 2 - r).buffer(r, quad_segs=24)


def stroke(pts, width, mitre=True):
    return LineString(pts).buffer(width / 2, cap_style="flat",
                                  join_style="mitre" if mitre else "round", mitre_limit=10)


def clip(g, w):
    return g.intersection(box(0, 0, w, 1))


# ------------------------------------------------------------------ block letters (cap height 1, upright)
def letter(ch):
    t = T
    if ch == "M":
        w = 1.08
        v = stroke([(t / 2, 1.6), (w / 2, 0.30), (w - t / 2, 1.6)], t * 1.08)
        g = unary_union([box(0, 0, t, 1), box(w - t, 0, w, 1), clip(v, w)])
        return g, w
    if ch == "I":
        return box(0, 0, t, 1), t
    if ch == "L":
        w = 0.66
        return unary_union([box(0, 0, t, 1), box(0, 0, w, BAR)]), w
    if ch == "W":
        w = 1.42
        v = stroke([(t / 2, -0.35), (w / 2, 0.66), (w - t / 2, -0.35)], t * 1.0)
        return unary_union([box(0, 0, t, 1), box(w - t, 0, w, 1), clip(v, w)]), w
    if ch == "A":
        w = 0.90
        ch_ = 0.26                                   # top corner chamfer
        outer = Polygon([(0, 0), (0, 1 - ch_), (ch_, 1), (w - ch_, 1), (w, 1 - ch_), (w, 0)])
        bar_lo, bar_hi = 0.30, 0.30 + BAR
        ic = ch_ * 0.55
        counter = Polygon([(t, bar_hi), (t, 1 - t - ic), (t + ic, 1 - t), (w - t - ic, 1 - t),
                           (w - t, 1 - t - ic), (w - t, bar_hi)])
        return outer.difference(counter).difference(box(t, -1, w - t, bar_lo)), w
    if ch == "U":
        w = 0.90
        ch_ = 0.12
        outer = Polygon([(0, 1), (0, ch_), (ch_, 0), (w - ch_, 0), (w, ch_), (w, 1)])
        ic = ch_ * 0.55
        inner = Polygon([(t, 2), (t, t + ic), (t + ic, t), (w - t - ic, t), (w - t, t + ic), (w - t, 2)])
        return outer.difference(inner), w
    if ch == "K":
        w = 0.88
        arm = stroke([(t * 0.6, 0.40), (w + 0.4, 1.0 + 0.4 * 0.62 / 0.6)], t * 1.05)
        leg = stroke([(t + 0.10, 0.56), (w + 0.25, -0.40)], t * 1.05)
        g = unary_union([box(0, 0, t, 1), clip(unary_union([arm, leg]), w)])
        return g, w
    if ch == "E":
        w = 0.66
        mid = 0.5 - BAR / 2
        return unary_union([box(0, 0, t, 1), box(0, 1 - BAR, w, 1), box(0, mid, w * 0.86, mid + BAR),
                            box(0, 0, w, BAR)]), w
    raise ValueError(ch)


def wordmark(text="MILWAUKEE"):
    x, parts = 0.0, []
    for ch in text:
        g, w = letter(ch)
        parts.append(affinity.translate(g, x, 0))
        x += w + TRACK
    shear = math.tan(math.radians(SLANT))
    letters = [affinity.affine_transform(p, [1, shear, 0, 1, 0, 0]) for p in parts]
    return letters


# ------------------------------------------------------------------ tagline from a font
class PolyPen(BasePen):
    def __init__(self, glyphset, steps=10):
        super().__init__(glyphset)
        self.rings, self.cur, self.steps = [], [], steps

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            s = i / self.steps
            a, b, c, d = (1 - s) ** 3, 3 * (1 - s) ** 2 * s, 3 * (1 - s) * s ** 2, s ** 3
            self.cur.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                             a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, self.steps + 1):
            s = i / self.steps
            self.cur.append(((1 - s) ** 2 * p0[0] + 2 * (1 - s) * s * p1[0] + s ** 2 * p2[0],
                             (1 - s) ** 2 * p0[1] + 2 * (1 - s) * s * p1[1] + s ** 2 * p2[1]))

    def _closePath(self):
        if len(self.cur) >= 3:
            self.rings.append(Polygon(self.cur).buffer(0))
        self.cur = []

    _endPath = _closePath


def text_shapes(text, path, cap):
    font = TTFont(path)
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    capH = font["OS/2"].sCapHeight
    k = cap / capH
    x, out = 0.0, []
    for ch in text:
        name = cmap[ord(ch)]
        pen = PolyPen(gs)
        gs[name].draw(pen)
        g = Polygon()
        for r in pen.rings:                    # even-odd fill
            g = g.symmetric_difference(r)
        if not g.is_empty:
            out.append(affinity.translate(affinity.scale(g, k, k, origin=(0, 0)), x, 0))
        x += gs[name].width * k
    return out


# ------------------------------------------------------------------ layout
def center(geoms, cx, cy):
    u = unary_union(geoms)
    minx, miny, maxx, maxy = u.bounds
    dx, dy = cx - (minx + maxx) / 2, cy - (miny + maxy) / 2
    return [affinity.translate(g, dx, dy) for g in geoms]


def parts():
    word = wordmark()
    minx, _, maxx, _ = unary_union(word).bounds
    cap = min(CAP, (W - 2 * RIM - 2 * SIDE - 2 * OUTLINE) / (maxx - minx))
    word = [affinity.scale(g, cap, cap, origin=(0, 0)) for g in word]
    tag = text_shapes(TAG_TEXT, TAG_FONT, TAG_CAP) if TAGLINE else []
    block_h = cap + (TAG_GAP + TAG_CAP if TAGLINE else 0)
    word_cy = block_h / 2 - cap / 2
    word = center(word, 0, word_cy)
    if tag:
        tag = center(tag, 0, word_cy - cap / 2 - TAG_GAP - TAG_CAP / 2)
    print(f"wordmark cap height: {cap:.2f}\"")
    return word, tag


def build():
    word, tag = parts()
    base = rrect(W, H, CORNER)
    red = rrect(W - 2 * RIM, H - 2 * RIM, RED_CORNER)
    white = unary_union(word)
    outline = white.buffer(OUTLINE, join_style="mitre", mitre_limit=3)
    layers = [
        ("layer1_base_black", "black", base, 0.25, f'{W:g}" x {H:g}" backer, black rim'),
        ("layer2_red_panel", "red", red, 0.125, "red panel"),
        ("layer3_black_outline", "black", outline, 0.125, "black outline behind MILWAUKEE (one piece)"),
        ("layer4_white_letters", "white", white, 0.125, "white MILWAUKEE letters (9 pieces)"),
    ]
    if tag:
        layers.append(("layer5_white_tagline", "white", unary_union(tag), 0.125,
                       "white tagline letters (glue straight onto the red)"))
    return layers


# ------------------------------------------------------------------ SVG out
def path_d(geom):
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    out = []
    for p in polys:
        if p.is_empty:
            continue
        for ring in [p.exterior, *p.interiors]:
            pts = list(ring.coords)
            out.append("M" + " L".join(f"{x + W / 2:.4f},{H / 2 - y:.4f}" for x, y in pts[:-1]) + " Z")
    return " ".join(out)


def svg_doc(body, title):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}in" height="{H}in" '
            f'viewBox="0 0 {W} {H}">\n<title>{title}</title>\n{body}\n</svg>\n')


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
        if stem == "layer5_white_tagline":
            preview[-1] = (stem, color, d, 0.375, thick)   # glued onto the red panel
            z -= thick

    body = "\n".join(f'<path d="{d}" fill="{COLORS[c]}" fill-rule="evenodd"/>' for _, c, d, _, _ in preview)
    with open(os.path.join(OUT, "preview_flat.svg"), "w") as f:
        f.write(svg_doc(body, "Flat colour preview"))

    tcols = ["#000", "#c00", "#555", "#00c", "#0a0"]
    body = "\n".join(f'<path d="{d}" fill="none" stroke="{tcols[k]}" stroke-width="0.015" fill-rule="evenodd"/>'
                     for k, (_, _, d, _, _) in enumerate(preview))
    with open(os.path.join(OUT, "placement_template.svg"), "w") as f:
        f.write(svg_doc(body, "Glue-up placement template (print 1:1)"))

    with open(os.path.join(OUT, "layers.json"), "w") as f:
        json.dump({"w": W, "h": H, "layers": [{"stem": s, "color": COLORS[c], "d": d, "z": z, "t": t}
                                              for s, c, d, z, t in preview]}, f)
    print("\n".join(rows))
    print(f"total stack height: {max(p[3] + p[4] for p in preview):.3f}\"")


if __name__ == "__main__":
    main()
