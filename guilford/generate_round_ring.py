#!/usr/bin/env python3
"""Generate laser-cut SVG layers for a 14" round Guilford 'G' sign with an orange outer ring.

Variant of the round sign (generate.py): no stripes - the orange becomes a wide outer
border ring, with a white pinstripe inside it and the G on a plain gray field.
Units are inches. Origin is the sign centre with +y up; SVG output flips y.
Run:  python3 generate_round_ring.py   (needs: pip install shapely numpy)
"""
import os

from shapely.geometry import Point

from common import letter_g, write_all

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "round-ring", "svg")

DIAM = 14.0
R_ORANGE = DIAM / 2        # 7.00  orange outer ring (base)
R_WHITE = 6.40             # white pinstripe ring      -> orange ring shows 0.60" wide
R_FIELD = 6.22             # gray field                -> pinstripe shows 0.18" wide
G_HEIGHT = 8.40            # height of the G, arrow included
G_CENTER = (0.0, 0.0)      # centre of the G's bounding box


def circle(r, n=720):
    return Point(0, 0).buffer(r, quad_segs=n // 4)


def build():
    return [
        ("layer1_base_orange", "orange", circle(R_ORANGE), 0.25,
         f"{2 * R_ORANGE:.2f}\" disc - orange outer ring / backer"),
        ("layer2_white_ring", "white", circle(R_WHITE), 0.125, f"{2 * R_WHITE:.2f}\" disc - white pinstripe"),
        ("layer3_gray_field", "gray", circle(R_FIELD), 0.125, f"{2 * R_FIELD:.2f}\" disc - gray field"),
        ("layer4_white_g", "white", letter_g(G_HEIGHT, G_CENTER), 0.25, "white G - top layer"),
    ]


def main():
    write_all(build(), OUT, DIAM, DIAM, "circle")


if __name__ == "__main__":
    main()
