#!/usr/bin/env python3
"""Generate laser-cut SVG layers for a 14" round stacked Guilford 'G' sign.

Gray / orange / white, built the same way as the Susquehanna S sign. The G (with its
arrow) is traced from reference/guilford_logo.jpg by trace_g.py.

Units are inches. Origin is the sign centre with +y up; SVG output flips y.
Run:  python3 generate.py   (needs: pip install shapely numpy)
"""
import os

from shapely.geometry import Point, box
from shapely.ops import unary_union

from common import letter_g, write_all

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "svg")

# ---------------------------------------------------------------- dimensions
DIAM = 14.0
R_BASE = DIAM / 2          # 7.00  gray outer rim (base)
R_WHITE = 6.80             # white pinstripe ring
R_ORANGE = 6.62            # orange ring
R_FIELD = 6.45             # gray field

# the G (traced from reference/guilford_logo.jpg with trace_g.py)
G_HEIGHT = 8.40            # height of the G, arrow included
G_CENTER = (0.0, 0.40)     # centre of the G's bounding box
G_OUTLINE = 0.22           # gray outline around the G
SUPPORT_INSET = 0.06       # hidden support under the G is inset this much

# stripes across the lower field (the locomotive's orange band with white pinstripes)
STRIPE_TOP = -2.55
STRIPE_BOT = -4.35
PIN = 0.25                 # white pinstripe width above and below the orange band
MIN_HALF = 0.045           # pieces thinner than 0.09" at the rim are trimmed


def circle(r, n=720):
    return Point(0, 0).buffer(r, quad_segs=n // 4)


def parts():
    field = circle(R_FIELD)
    g = letter_g(G_HEIGHT, G_CENTER)
    g_outline = g.buffer(G_OUTLINE, join_style="mitre", mitre_limit=2.5)
    support = g_outline.buffer(-SUPPORT_INSET)
    clean = lambda s: s.intersection(field).buffer(-MIN_HALF).buffer(MIN_HALF)
    white = clean(box(-8, STRIPE_BOT, 8, STRIPE_TOP))
    orange = clean(box(-8, STRIPE_BOT + PIN, 8, STRIPE_TOP - PIN))
    return dict(field=field, g=g, g_outline=g_outline, support=support, white=white, orange=orange)


def build():
    p = parts()
    return [
        # (file stem, colour, geometry, thickness in, note)
        ("layer1_base_gray", "gray", circle(R_BASE), 0.25, "14.00\" disc - outer gray rim / backer"),
        ("layer2_white_ring", "white", circle(R_WHITE), 0.125, "13.60\" disc - white pinstripe"),
        ("layer3_orange_ring", "orange", circle(R_ORANGE), 0.125, "13.24\" disc - orange ring"),
        ("layer4_gray_field", "gray", p["field"], 0.125, "12.90\" disc - gray field"),
        ("layer5_white_stripe", "white", unary_union([p["white"], p["support"]]), 0.125,
         "white stripe band (+ hidden G support)"),
        ("layer6_orange_stripe", "orange", unary_union([p["orange"], p["support"]]), 0.125,
         "orange stripe (+ hidden G support)"),
        ("layer7_gray_g_outline", "gray", p["g_outline"], 0.125, "gray outline of the G"),
        ("layer8_white_g", "white", p["g"], 0.125, "white G - top layer"),
    ]


def main():
    write_all(build(), OUT, DIAM, DIAM, "circle")


if __name__ == "__main__":
    main()
