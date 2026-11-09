#!/usr/bin/env python3
"""Generate laser-cut SVG layers for two stacked Erie Lackawanna "EL" signs.

* square/ - the logo as drawn: rounded yellow square, maroon diamond, white disc, maroon L-E.
* round/  - round version: a raised black ring overlaps the diamond's points.

Units are inches. Origin is the sign centre with +y up; the SVG output flips y.
Run:  python3 generate.py   (needs: pip install shapely numpy)
"""
import json
import os

from shapely.geometry import Polygon, Point, MultiPolygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------ logo geometry
# Measured from a 2000 x 2000 px drawing of the logo (centre at 1000,1000).
# All values are px from the centre; they are scaled to inches per sign below.
PX_DIAMOND = 942           # centre to each point of the diamond
PX_WHITE = 600             # radius of the white disc
PX_RING_IN = 851           # round version: inner edge of the black ring
PX_RING_OUT = 935          # round version: outer edge of the black ring
PX_LTR_W = 357.5           # letter block half-width
PX_LTR_H = 460.5           # letter block half-height
PX_BAR = 201               # thickness of the L stem and every bar
PX_SLOT = 45               # gap between the L stem and the E bars

# ------------------------------------------------------------ sign settings
SQUARE_SIDE = 14.0         # square sign: side length (in)
ROUND_DIAM = 14.0          # round sign: outer diameter of the black ring (in)
SQUARE_CORNER_R = 0.5      # radius of the square's rounded corners (in)

COLORS = {
    "yellow": "#FCCF33",
    "maroon": "#671F1E",
    "white": "#F7F7F4",
    "black": "#141414",
}


def circle(r, n=720):
    return Point(0, 0).buffer(r, quad_segs=n // 4)


def diamond(h):
    return Polygon([(0, h), (h, 0), (0, -h), (-h, 0)])


def letters(k):
    """The L and the two E bars (3 pieces), scaled by k inches/px."""
    w, h, b, g = PX_LTR_W * k, PX_LTR_H * k, PX_BAR * k, PX_SLOT * k
    stem = box(-w, -h, -w + b, h)
    bottom = box(-w, -h, w, -h + b)
    ell = unary_union([stem, bottom])
    x0 = -w + b + g
    top = box(x0, h - b, w, h)
    mid = box(x0, -b / 2, w, b / 2)
    return MultiPolygon([ell, top, mid])


# ------------------------------------------------------------ the two signs
def square_sign():
    k = SQUARE_SIDE / 2 / 1000                 # drawing is 2000 px square
    half = SQUARE_SIDE / 2
    base = box(-half, -half, half, half)
    if SQUARE_CORNER_R > 0:
        base = base.buffer(-SQUARE_CORNER_R, join_style="mitre").buffer(SQUARE_CORNER_R)
    s = SQUARE_SIDE
    return dict(
        size=(s, s),
        layers=[
            # (file stem, colour, geometry, z (in), thickness (in), note)
            ("layer1_yellow_base", "yellow", base, 0.0, 0.25,
             f'{s:.2f}" square - yellow background / backer'),
            ("layer2_maroon_diamond", "maroon", diamond(PX_DIAMOND * k), 0.25, 0.125,
             f'diamond, {2 * PX_DIAMOND * k:.2f}" point to point'),
            ("layer3_white_disc", "white", circle(PX_WHITE * k), 0.375, 0.125,
             f'{2 * PX_WHITE * k:.2f}" white disc'),
            ("layer4_maroon_letters", "maroon", letters(k), 0.5, 0.125,
             "L and the two E bars (3 pieces)"),
        ])


def round_sign():
    k = ROUND_DIAM / 2 / PX_RING_OUT
    r_out, r_in = PX_RING_OUT * k, PX_RING_IN * k
    r_mid = (r_in + r_out) / 2                  # diamond points end here, hidden under the ring
    d = ROUND_DIAM
    ring = circle(r_out).difference(circle(r_in))
    spacer = circle(r_out).difference(circle(r_mid))
    return dict(
        size=(d, d),
        layers=[
            ("layer1_yellow_base", "yellow", circle(r_out), 0.0, 0.25,
             f'{d:.2f}" disc - yellow face, black edge / backer'),
            ("layer2a_maroon_diamond", "maroon", diamond(PX_DIAMOND * k).intersection(circle(r_mid)), 0.25, 0.125,
             f'diamond, points trimmed to a {2 * r_mid:.2f}" circle (they run under the ring)'),
            ("layer2b_black_ring_spacer", "black", spacer, 0.25, 0.125,
             f'{2 * r_mid:.2f}" ID x {d:.2f}" OD ring - holds the top ring level'),
            ("layer3a_white_disc", "white", circle(PX_WHITE * k), 0.375, 0.125,
             f'{2 * PX_WHITE * k:.2f}" white disc'),
            ("layer3b_black_ring", "black", ring, 0.375, 0.125,
             f'{2 * r_in:.2f}" ID x {d:.2f}" OD black ring - overlaps the diamond points'),
            ("layer4_maroon_letters", "maroon", letters(k), 0.5, 0.125,
             "L and the two E bars (3 pieces)"),
        ])


# ------------------------------------------------------------ SVG out
def path_d(geom, w, h):
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    out = []
    for p in polys:
        for ring in [p.exterior, *p.interiors]:
            pts = list(ring.coords)[:-1]
            out.append("M" + " L".join(f"{x + w / 2:.4f},{h / 2 - y:.4f}" for x, y in pts) + " Z")
    return " ".join(out)


def svg_doc(body, title, w, h):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}in" height="{h}in" '
            f'viewBox="0 0 {w} {h}">\n<title>{title}</title>\n{body}\n</svg>\n')


def write_sign(name, sign):
    out = os.path.join(HERE, name, "svg")
    os.makedirs(out, exist_ok=True)
    w, h = sign["size"]
    preview, rows, top = [], [], 0.0
    for stem, color, geom, z, t, note in sign["layers"]:
        d = path_d(geom, w, h)
        cut = f'<path d="{d}" fill="none" stroke="#FF0000" stroke-width="0.01" fill-rule="evenodd"/>'
        with open(os.path.join(out, stem + ".svg"), "w") as f:
            f.write(svg_doc(cut, f"{stem} - {note} - paint {color}", w, h))
        preview.append(dict(stem=stem, color=COLORS[color], d=d, z=z, t=t))
        pieces = len(geom.geoms) if isinstance(geom, MultiPolygon) else 1
        rows.append(f"| `svg/{stem}.svg` | {color} | {t}\" | {pieces} | {note} |")
        top = max(top, z + t)

    body = "\n".join(f'<path d="{L["d"]}" fill="{L["color"]}" fill-rule="evenodd"/>' for L in preview)
    with open(os.path.join(out, "preview_flat.svg"), "w") as f:
        f.write(svg_doc(body, "Flat colour preview", w, h))

    tcols = ["#000", "#c90", "#0a0", "#00c", "#c00", "#808"]
    body = "\n".join(f'<path d="{L["d"]}" fill="none" stroke="{tcols[i % len(tcols)]}" '
                     f'stroke-width="0.015" fill-rule="evenodd"/>' for i, L in enumerate(preview))
    with open(os.path.join(out, "placement_template.svg"), "w") as f:
        f.write(svg_doc(body, "Glue-up placement template (print 1:1)", w, h))

    with open(os.path.join(out, "layers.json"), "w") as f:
        json.dump(dict(w=w, h=h, layers=preview), f)
    print(f"\n{name}:")
    print("\n".join(rows))
    print(f"total stack height: {top:.3f}\"")


def main():
    write_sign("square", square_sign())
    write_sign("round", round_sign())


if __name__ == "__main__":
    main()
