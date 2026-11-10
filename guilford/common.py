"""Shared helpers for the Guilford signs: the traced G, lettering and SVG output."""
import json
import os

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))

# colours sampled from the reference logo (preview only - cut files carry no colour)
COLORS = {
    "gray": "#4F4F4F",
    "orange": "#DE6747",
    "white": "#F4F3EF",
}

FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"  # Helvetica Bold metrics


def letter_g(height, center=(0.0, 0.0)):
    """The G with its arrow, traced from the reference logo (see trace_g.py)."""
    with open(os.path.join(HERE, "g_logo_trace.json")) as f:
        t = json.load(f)
    g = Polygon(t["outline"], t["holes"]).buffer(0)
    g = affinity.scale(g, height, height, origin=(0, 0))
    return affinity.translate(g, *center)


class _FlatPen(BasePen):
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
            self.rings.append(self.cur)
        self.cur = []

    _endPath = _closePath


def text_shape(text, cap_height, tracking=0.0):
    """Lettering as polygons. Baseline at y=0, starting at x=0. Returns (shape, width)."""
    font = TTFont(FONT)
    gs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font["hmtx"]
    upm = font["head"].unitsPerEm
    cap = font["OS/2"].sCapHeight or 0.716 * upm
    k = cap_height / cap
    x, shapes = 0.0, []
    for ch in text:
        name = cmap[ord(ch)]
        pen = _FlatPen(gs)
        gs[name].draw(pen)
        glyph = Polygon()
        for ring in pen.rings:
            glyph = glyph.symmetric_difference(Polygon(ring).buffer(0))
        if not glyph.is_empty:
            shapes.append(affinity.translate(affinity.scale(glyph, k, k, origin=(0, 0)), x, 0))
        x += hmtx[name][0] * k + tracking
    return unary_union(shapes), x - tracking


def path_d(geom, ox, oy):
    """SVG path data; (ox, oy) is the design origin's position on the page (y flipped)."""
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    out = []
    for p in polys:
        if p.is_empty:
            continue
        for ring in [p.exterior, *p.interiors]:
            pts = list(ring.coords)
            out.append("M" + " L".join(f"{x + ox:.4f},{oy - y:.4f}" for x, y in pts[:-1]) + " Z")
    return " ".join(out)


def write_all(layers, out_dir, w, h, outline_shape="circle"):
    """Write cut files, flat preview, placement template and layers.json for render.js."""
    os.makedirs(out_dir, exist_ok=True)

    def doc(body, title):
        return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}in" height="{h}in" '
                f'viewBox="0 0 {w} {h}">\n<title>{title}</title>\n{body}\n</svg>\n')

    preview, z, rows = [], 0.0, []
    for i, (stem, color, geom, thick, note) in enumerate(layers, 1):
        geom = geom.simplify(0.002)
        d = path_d(geom, w / 2, h / 2)
        cut = f'<path d="{d}" fill="none" stroke="#FF0000" stroke-width="0.01" fill-rule="evenodd"/>'
        with open(os.path.join(out_dir, stem + ".svg"), "w") as f:
            f.write(doc(cut, f"Layer {i} - {note} - paint {color}"))
        preview.append((stem, color, d, z, thick))
        pieces = len(geom.geoms) if isinstance(geom, MultiPolygon) else 1
        rows.append(f"| {i} | `{stem}.svg` | {color} | {thick}\" | {pieces} | {note} |")
        z += thick

    body = "\n".join(f'<path d="{d}" fill="{COLORS[c]}" fill-rule="evenodd"/>' for _, c, d, _, _ in preview)
    with open(os.path.join(out_dir, "preview_flat.svg"), "w") as f:
        f.write(doc(body, "Flat colour preview"))

    tcols = ["#000", "#c90", "#555", "#00c", "#0a0", "#c00", "#f80", "#808"]
    body = "\n".join(f'<path d="{d}" fill="none" stroke="{tcols[k]}" stroke-width="0.015" fill-rule="evenodd"/>'
                     for k, (_, _, d, _, _) in enumerate(preview))
    with open(os.path.join(out_dir, "placement_template.svg"), "w") as f:
        f.write(doc(body, "Glue-up placement template (print 1:1)"))

    with open(os.path.join(out_dir, "layers.json"), "w") as f:
        json.dump({"w": w, "h": h, "shape": outline_shape,
                   "layers": [{"stem": s, "color": COLORS[c], "d": d, "z": z, "t": t}
                              for s, c, d, z, t in preview]}, f)
    print("\n".join(rows))
    print(f"total stack height: {z:.3f}\"")
