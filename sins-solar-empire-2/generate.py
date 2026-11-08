#!/usr/bin/env python3
"""Generate laser-cut SVG layers for a 24" tall stacked Sins of a Solar Empire II logo sign.

The logo outline comes from logo_trace.json (traced from source/logo.png by trace_logo.py).
Units are inches. Origin of the design is the sign centre with +y up; SVG output flips y.
Run:  python3 generate.py   (needs: pip install shapely numpy)
"""
import json
import os

from shapely import affinity
from shapely.geometry import MultiPolygon, Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "svg")

# ---------------------------------------------------------------- dimensions
SIGN_H = 24.0          # overall height of the backer
BACKER = 1.10          # backer extends this far beyond the logo (enough to join every piece)
GLOW = 0.45            # blue band around the logo
EDGE = 0.15            # thin black edge directly under the white logo
SPLIT = True           # cut the backer in two halves (each fits a 24" x 18" bed)
SPLICE_W = 4.0         # width of the splice plate that joins the halves on the back
MIN_HALF = 0.03        # features thinner than 0.06" are trimmed off

COLORS = {
    "navy": "#13263B",
    "blue": "#3A6A99",
    "black": "#0B0F14",
    "white": "#F4F5F2",
    "plywood": "#C9A878",
}


# ------------------------------------------------------------------ helpers
def tidy(g, r=MIN_HALF):
    """Remove slivers thinner than 2*r (morphological opening)."""
    return g.buffer(-r, join_style="mitre").buffer(r, join_style="mitre")


def fill_holes(g):
    polys = g.geoms if isinstance(g, MultiPolygon) else [g]
    return unary_union([Polygon(p.exterior) for p in polys])


def pieces(g):
    return list(g.geoms) if isinstance(g, MultiPolygon) else [g]


def load_logo():
    """Logo pieces in inches, scaled so the backer is SIGN_H tall, centred on the origin."""
    with open(os.path.join(HERE, "logo_trace.json")) as f:
        data = json.load(f)
    polys = [Polygon(s["outer"], s["holes"]).buffer(0) for s in data["shapes"]]
    logo = unary_union(polys)
    minx, miny, maxx, maxy = logo.bounds
    k = (SIGN_H - 2 * BACKER) / (maxy - miny)
    logo = affinity.translate(logo, -(minx + maxx) / 2, -(miny + maxy) / 2)
    logo = affinity.scale(logo, k, -k, origin=(0, 0))          # pixels (y down) -> inches (y up)
    return tidy(logo), k


def seam_x(logo):
    """x of the widest clear vertical gap near the middle (between the bars and the words)."""
    best = None
    minx, miny, maxx, maxy = logo.bounds
    x = -3.0
    while x <= 3.0:
        clear = logo.distance(box(x, miny - 1, x, maxy + 1))
        if best is None or clear > best[1]:
            best = (x, clear)
        x += 0.01
    return best[0]


def build():
    logo, k = load_logo()
    ink = fill_holes(logo)
    backer = fill_holes(ink.buffer(BACKER, quad_segs=32))
    glow = fill_holes(logo.buffer(GLOW, quad_segs=32))
    edge = logo.buffer(EDGE, quad_segs=32)

    extra = []
    note = "backer"
    if SPLIT:
        sx = seam_x(logo)
        minx, miny, maxx, maxy = backer.bounds
        left = backer.intersection(box(minx - 1, miny - 1, sx, maxy + 1))
        right = backer.intersection(box(sx, miny - 1, maxx + 1, maxy + 1))
        backer = MultiPolygon(pieces(left) + pieces(right))
        splice = backer.buffer(0.01).intersection(box(sx - SPLICE_W / 2, miny, sx + SPLICE_W / 2, maxy))
        splice = splice.buffer(-0.5, join_style="mitre")
        extra.append(("layer0_splice_plate_back", "plywood", fill_holes(unary_union(splice)), 0.25,
                      "splice plate - glue to the BACK across the seam"))
        note = f"backer, cut in two halves at x = {sx:+.2f}\" from centre"
    layers = [
        ("layer1_backer", "navy", backer, 0.25, note),
        ("layer2_blue_glow", "blue", glow, 0.125, "blue band around the logo"),
        ("layer3_black_edge", "black", edge, 0.125, "black edge under the logo"),
        ("layer4_white_logo", "white", logo, 0.25, "logo - top layer"),
    ]
    return layers, extra, k


# ------------------------------------------------------------------ SVG out
def main():
    os.makedirs(OUT, exist_ok=True)
    layers, extra, k = build()
    minx, miny, maxx, maxy = unary_union([g for _, _, g, _, _ in layers]).bounds
    W, H = maxx - minx, maxy - miny

    def path_d(geom):
        out = []
        for p in pieces(geom):
            if p.is_empty:
                continue
            for ring in [p.exterior, *p.interiors]:
                pts = list(ring.coords)
                out.append("M" + " L".join(f"{x - minx:.4f},{maxy - y:.4f}" for x, y in pts[:-1]) + " Z")
        return " ".join(out)

    def svg_doc(body, title):
        return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.3f}in" height="{H:.3f}in" '
                f'viewBox="0 0 {W:.4f} {H:.4f}">\n<title>{title}</title>\n{body}\n</svg>\n')

    preview, z, rows = [], 0.0, []
    for stem, color, geom, thick, note in extra + layers:
        d = path_d(geom)
        cut = f'<path d="{d}" fill="none" stroke="#FF0000" stroke-width="0.01" fill-rule="evenodd"/>'
        with open(os.path.join(OUT, stem + ".svg"), "w") as f:
            f.write(svg_doc(cut, f"{note} - paint {color}"))
        bx = geom.bounds
        rows.append(f"| `svg/{stem}.svg` | {color} | {thick}\" | {len(pieces(geom))} | "
                    f"{bx[2] - bx[0]:.1f}\" x {bx[3] - bx[1]:.1f}\" | {note} |")
        if not stem.startswith("layer0"):
            preview.append((stem, color, d, z, thick))
            z += thick

    body = "\n".join(f'<path d="{d}" fill="{COLORS[c]}" fill-rule="evenodd"/>' for _, c, d, _, _ in preview)
    with open(os.path.join(OUT, "preview_flat.svg"), "w") as f:
        f.write(svg_doc(body, "Flat colour preview"))

    tcols = ["#000", "#06c", "#c00", "#0a0"]
    body = "\n".join(f'<path d="{d}" fill="none" stroke="{tcols[i]}" stroke-width="0.015" fill-rule="evenodd"/>'
                     for i, (_, _, d, _, _) in enumerate(preview))
    with open(os.path.join(OUT, "placement_template.svg"), "w") as f:
        f.write(svg_doc(body, "Glue-up placement template (print 1:1)"))

    with open(os.path.join(OUT, "layers.json"), "w") as f:
        json.dump({"w": W, "h": H, "layers": [{"stem": s, "color": COLORS[c], "d": d, "z": z, "t": t}
                                              for s, c, d, z, t in preview]}, f)
    print("\n".join(rows))
    print(f"sign: {W:.2f}\" wide x {H:.2f}\" tall, {z:.3f}\" thick; logo scale {k * 1000:.2f} in per 1000 px")


if __name__ == "__main__":
    main()
