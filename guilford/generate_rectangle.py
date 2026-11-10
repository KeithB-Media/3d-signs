#!/usr/bin/env python3
"""Generate laser-cut SVG layers for a 24" x 9" stacked Guilford Rail System sign.

Same layout as the wide logo (reference/guilford_logo.jpg): the G with its arrow on the
left, "Guilford Rail System" on the right, and the orange bar running off the right edge.
Positions are taken from the logo image (pixel measurements below) and scaled to fit.
Units are inches. Origin is the sign centre with +y up; SVG output flips y.
Run:  python3 generate_rectangle.py   (needs: pip install shapely numpy fonttools)
"""
import os

from shapely import affinity
from shapely.geometry import box
from shapely.ops import unary_union

from common import letter_g, text_shape, write_all

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "rectangle", "svg")

SIGN_W, SIGN_H = 24.0, 9.0
CORNER = 0.30              # corner radius of the backer
PINSTRIPE = 0.20           # white pinstripe showing around the edge
BORDER = 0.20              # gray border showing outside the pinstripe
FIELD_W = SIGN_W - 2 * (PINSTRIPE + BORDER)   # 23.2"
FIELD_H = SIGN_H - 2 * (PINSTRIPE + BORDER)   # 8.2"
MARGIN_X = 0.85            # G and lettering keep this far inside the field
MARGIN_Y = 0.95
TEXT = "Guilford Rail System"
TRACKING = 0.02

# measured on reference/guilford_logo.jpg (pixels, y down)
PX_G = (71, 193, 797, 902)          # G bounding box
PX_TEXT = (929, 320, 2524, 475)     # lettering: left, top (ascenders), right, bottom (descender)
PX_BAR = (881, 509, 700)            # bar: left, top, bottom (runs to the right edge)


def rounded_rect(w, h, r):
    return box(-w / 2 + r, -h / 2 + r, w / 2 - r, h / 2 - r).buffer(r, quad_segs=32)


def build():
    field = rounded_rect(FIELD_W, FIELD_H, 0.02)
    left, right = PX_G[0], PX_TEXT[2]
    top, bot = PX_G[1], PX_G[3]
    s = min((FIELD_W - 2 * MARGIN_X) / (right - left), (FIELD_H - 2 * MARGIN_Y) / (bot - top))
    cx, cy = (left + right) / 2, (top + bot) / 2
    X = lambda px: (px - cx) * s
    Y = lambda py: (cy - py) * s

    g_h = (PX_G[3] - PX_G[1]) * s
    g = letter_g(g_h, (X((PX_G[0] + PX_G[2]) / 2), Y((PX_G[1] + PX_G[3]) / 2)))

    # lettering: fit its width to the logo, then line up its top with the logo's
    _, w1 = text_shape(TEXT, 1.0, TRACKING)
    tw_target = (PX_TEXT[2] - PX_TEXT[0]) * s
    cap = tw_target / w1
    text, tw = text_shape(TEXT, cap, TRACKING)
    text = affinity.translate(text, X(PX_TEXT[0]) - text.bounds[0], Y(PX_TEXT[1]) - text.bounds[3])

    bar = box(X(PX_BAR[0]), Y(PX_BAR[2]), FIELD_W / 2, Y(PX_BAR[1])).intersection(field)
    print(f"scale {s * 1000:.2f} in per 1000 px; G {g_h:.2f}\" tall; lettering cap {cap:.2f}\"")

    return [
        ("layer1_base_gray", "gray", rounded_rect(SIGN_W, SIGN_H, CORNER), 0.25,
         f"{SIGN_W:.0f}\" x {SIGN_H:.0f}\" - gray border / backer"),
        ("layer2_white_pinstripe", "white",
         rounded_rect(SIGN_W - 2 * BORDER, SIGN_H - 2 * BORDER, CORNER - BORDER), 0.125,
         f"{SIGN_W - 2 * BORDER:.1f}\" x {SIGN_H - 2 * BORDER:.1f}\" - white pinstripe"),
        ("layer3_gray_field", "gray", field, 0.125, f"{FIELD_W:.1f}\" x {FIELD_H:.1f}\" - gray field"),
        ("layer4_orange_bar", "orange", bar, 0.125, "orange bar"),
        ("layer5_white_g_lettering", "white", unary_union([g, text]), 0.125,
         "white G and 'Guilford Rail System' lettering"),
    ]


def main():
    write_all(build(), OUT, SIGN_W, SIGN_H, "rect")


if __name__ == "__main__":
    main()
