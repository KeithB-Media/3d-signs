#!/usr/bin/env python3
"""Simplified one-tone version of the sign for laser-engraved coasters.

Engraved (dark): outer ring, blue field, red stripes, the S.
Left as bare wood: the yellow pinstripe, white stripes, stars, swoosh, S outline.
The three thin rings of the sign become one engraved ring + one bare pinstripe, and
the S outline is widened so the S still reads at coaster size.

Usage: python3 coaster.py [diameter_in ...]     (default: 4.0 and 3.5)
Writes coaster/coaster_<D>in.svg (black fill = engrave, red hairline = optional cut).

Slate:  python3 coaster.py slate [tile_in design_in]   (default: 4.0 3.5)
Writes an INVERTED file for slate, which engraves light: the logo's light parts are
engraved and the dark slate shows as the field, red stripes and S.
"""
import contextlib
import io
import os
import sys

from shapely import affinity
from shapely.geometry import MultiPolygon
from shapely.ops import unary_union

import generate as g

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "coaster")

# all in sign units (the 14" design); scaled down at the end
RING_OUT, RING_IN = 7.00, 6.72      # engraved outer ring
FIELD_R = 6.48                      # engraved field starts here (6.72-6.48 = bare pinstripe)
S_GAP = 0.34                        # bare outline around the S (wider than the sign's 0.21)
STAR_CLEAR = 0.10                   # keep stars this far from the S outline
MIN_FEATURE_IN = 0.02               # drop engraved/bare details thinner than this on the coaster


def artwork():
    with contextlib.redirect_stdout(io.StringIO()):
        p = g.parts()
    s = p["s"]
    s_gap = s.buffer(S_GAP, join_style="round")
    # the wider S outline crowds some stars: shrink those, and leave one out if it still touches
    stars = []
    for st in p["stars"]:
        for k in (1.0, 0.9, 0.8, 0.7, 0.6):
            cand = affinity.scale(st, k, k, origin=st.centroid)
            if cand.distance(s_gap) >= STAR_CLEAR:
                stars.append(cand)
                break
    bare = unary_union([p["stripes"].difference(p["red"]), p["swoosh"], *stars, s_gap])
    field = g.circle(FIELD_R).difference(bare)
    ring = g.circle(RING_OUT).difference(g.circle(RING_IN))
    return unary_union([ring, field, s])


def clean(geom, scale):
    """Remove engraved and bare slivers too fine to show at this size."""
    h = MIN_FEATURE_IN / 2 / scale
    geom = geom.buffer(-h).buffer(h)          # thin engraved slivers
    return geom.buffer(h).buffer(-h)          # thin bare slivers


def svg(geom, diam):
    scale = diam / (2 * RING_OUT)
    geom = affinity.scale(geom, scale, scale, origin=(0, 0))
    r = diam / 2
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    d = []
    for p in polys:
        for ring in [p.exterior, *p.interiors]:
            pts = list(ring.coords)[:-1]
            d.append("M" + " L".join(f"{x + r:.4f},{r - y:.4f}" for x, y in pts) + " Z")
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{diam}in" height="{diam}in" '
            f'viewBox="0 0 {diam} {diam}">\n'
            f'<title>Susquehanna S coaster - {diam}in - black = engrave, red = optional cut</title>\n'
            f'<g id="engrave"><path d="{" ".join(d)}" fill="#000000" fill-rule="evenodd"/></g>\n'
            f'<g id="cut"><circle cx="{r}" cy="{r}" r="{r}" fill="none" stroke="#FF0000" '
            f'stroke-width="0.003"/></g>\n</svg>\n')


def slate_svg(art, tile=4.0, design=3.5):
    """Slate: the laser turns slate pale grey, so engrave the logo's LIGHT parts
    (pinstripe, white stripes, stars, swoosh, S outline) and let the natural dark slate be
    the blue field, red stripes and S. The design circle (pinstripe outer edge) is `design`
    inches, centred on a `tile`-inch square, leaving a margin for the chipped edges."""
    scale = design / (2 * RING_IN)
    light = clean(g.circle(RING_IN).difference(art), scale)
    geom = affinity.scale(light, scale, scale, origin=(0, 0))
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
            f'<title>Susquehanna S slate coaster - {design}in design on {tile}in tile - '
            f'black = engrave, blue = alignment guide only</title>\n'
            f'<g id="guide"><rect x="0.002" y="0.002" width="{tile - 0.004}" height="{tile - 0.004}" '
            f'fill="none" stroke="#0000FF" stroke-width="0.004"/></g>\n'
            f'<g id="engrave"><path d="{" ".join(d)}" fill="#000000" fill-rule="evenodd"/></g>\n'
            f'</svg>\n')


def main():
    if sys.argv[1:2] == ["slate"]:
        os.makedirs(OUT, exist_ok=True)
        args = [float(a) for a in sys.argv[2:]]
        tile, design = (args + [4.0, 3.5][len(args):])[:2]
        name = f"slate_coaster_{design:g}in_on_{tile:g}in.svg"
        with open(os.path.join(OUT, name), "w") as f:
            f.write(slate_svg(artwork(), tile, design))
        print("wrote", os.path.join("coaster", name))
        return
    sizes = [float(a) for a in sys.argv[1:]] or [4.0, 3.5]
    os.makedirs(OUT, exist_ok=True)
    art = artwork()
    for diam in sizes:
        scale = diam / (2 * RING_OUT)
        name = f"coaster_{diam:g}in.svg"
        with open(os.path.join(OUT, name), "w") as f:
            f.write(svg(clean(art, scale), diam))
        print("wrote", os.path.join("coaster", name))


if __name__ == "__main__":
    main()
