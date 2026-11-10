#!/usr/bin/env python3
"""Generate laser-cut SVG layers for a 14" square stacked Guilford Rail System sign.

Square take on the wide Guilford logo (reference/guilford_logo.jpg): the G with its
arrow on top, "Guilford Rail System" below it, then the orange bar.
Units are inches. Origin is the sign centre with +y up; SVG output flips y.
Run:  python3 generate_square.py   (needs: pip install shapely numpy fonttools)
"""
import os

from shapely import affinity
from shapely.geometry import box
from shapely.ops import unary_union

from common import letter_g, text_shape, write_all

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "square", "svg")

SIZE = 14.0                # outside size of the square
CORNER = 0.30              # corner radius of the backer
PINSTRIPE = 0.20           # white pinstripe showing around the edge
BORDER = 0.20              # gray border showing outside the pinstripe
FIELD = SIZE - 2 * (PINSTRIPE + BORDER)   # 13.20" gray field

TEXT = "Guilford Rail System"
MARGIN = 0.85              # lettering and G keep this far inside the field
G_HEIGHT = 7.00            # height of the G, arrow included
GAP_G_TEXT = 0.75          # G bottom to lettering cap top
GAP_TEXT_BAR = 0.55        # lettering baseline to bar top (the 'y' descender sits in here)
BAR_H = 1.45               # orange bar height (logo proportion: bar ~1.2x cap height)
TRACKING = 0.02            # extra space between letters (inches)


def rounded_square(side, r):
    return box(-side / 2 + r, -side / 2 + r, side / 2 - r, side / 2 - r).buffer(r, quad_segs=32)


def build():
    field = rounded_square(FIELD, max(CORNER - PINSTRIPE - BORDER, 0.02))
    width = FIELD - 2 * MARGIN

    # lettering sized to fill the width between the margins
    probe, w1 = text_shape(TEXT, 1.0, TRACKING)
    cap = width / w1
    text, tw = text_shape(TEXT, cap, TRACKING)

    # stack: G, lettering, bar - centred as a block in the field
    block = G_HEIGHT + GAP_G_TEXT + cap + GAP_TEXT_BAR + BAR_H
    top = block / 2
    g = letter_g(G_HEIGHT, (0.0, top - G_HEIGHT / 2))
    baseline = top - G_HEIGHT - GAP_G_TEXT - cap
    text = affinity.translate(text, -tw / 2, baseline)
    bar_top = baseline - GAP_TEXT_BAR
    bar = box(-FIELD / 2, bar_top - BAR_H, FIELD / 2, bar_top).intersection(field)

    white = unary_union([g, text])
    print(f"lettering cap height {cap:.2f}\", width {tw:.2f}\"")
    return [
        ("layer1_base_gray", "gray", rounded_square(SIZE, CORNER), 0.25,
         f"{SIZE:.2f}\" square - gray border / backer"),
        ("layer2_white_pinstripe", "white", rounded_square(SIZE - 2 * BORDER, CORNER - BORDER), 0.125,
         f"{SIZE - 2 * BORDER:.2f}\" square - white pinstripe"),
        ("layer3_gray_field", "gray", field, 0.125, f"{FIELD:.2f}\" square - gray field"),
        ("layer4_orange_bar", "orange", bar, 0.125, "orange bar"),
        ("layer5_white_g_lettering", "white", white, 0.125, "white G and 'Guilford Rail System' lettering"),
    ]


def main():
    write_all(build(), OUT, SIZE, SIZE, "square")


if __name__ == "__main__":
    main()
