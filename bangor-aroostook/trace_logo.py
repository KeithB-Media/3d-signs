#!/usr/bin/env python3
"""Trace the Bangor & Aroostook triangle logo from a scan (teal logo on a light card).

Writes logo_trace.json: the rounded triangle outline and the light artwork inside it
(the "A" with the upper wave, the lower wave and the 7 leaf pieces), in pixels.
The logo is symmetric, so the mask is averaged with its mirror image before tracing.

    pip install opencv-python-headless numpy pillow
    python3 trace_logo.py card.jpg [x0 y0 x1 y1]     # optional crop box around the logo
"""
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
UP = 6            # work at 6x resolution so the smoothing doesn't eat corners


def main():
    path = sys.argv[1]
    box = [int(v) for v in sys.argv[2:6]] if len(sys.argv) >= 6 else [200, 290, 600, 650]
    img = cv2.imread(path)[box[1]:box[3], box[0]:box[2]].astype(np.float32)
    b, g, r = img[..., 0], img[..., 1], img[..., 2]
    # teal: low red, high green/blue. Soft score 0..1 keeps anti-aliasing for sub-pixel edges.
    teal = np.clip(((g + b) / 2 - r - 40) / 80, 0, 1)
    teal = cv2.GaussianBlur(teal, (0, 0), 0.8)

    # find the symmetry axis: the triangle's horizontal centre
    ys, xs = np.nonzero(teal > 0.5)
    axis = (xs.min() + xs.max()) / 2
    w = teal.shape[1]
    # shift so the axis is the image centre, then average with the mirror
    m = np.float32([[1, 0, w / 2 - axis], [0, 1, 0]])
    teal = cv2.warpAffine(teal, m, (w, teal.shape[0]), flags=cv2.INTER_LINEAR)
    teal = (teal + teal[:, ::-1]) / 2

    big = cv2.resize(teal, None, fx=UP, fy=UP, interpolation=cv2.INTER_CUBIC)
    big = cv2.GaussianBlur(big, (0, 0), UP * 0.7)
    mask = (big > 0.5).astype(np.uint8)

    # outer triangle = filled outer contour of the teal
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    tri = max(cnts, key=cv2.contourArea)
    filled = np.zeros_like(mask)
    cv2.drawContours(filled, [tri], -1, 1, -1)
    art = (filled & (1 - mask)).astype(np.uint8)
    art = cv2.morphologyEx(art, cv2.MORPH_OPEN, np.ones((UP, UP), np.uint8))   # drop specks

    acnts, hier = cv2.findContours(art, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    pieces = []
    for i, c in enumerate(acnts):
        if hier[0][i][3] != -1 or cv2.contourArea(c) < (3 * UP) ** 2:
            continue
        pieces.append(c)

    def pts(c, eps=0.25):
        c = cv2.approxPolyDP(c, eps * UP, True)
        return [[float(x) / UP, float(y) / UP] for x, y in c[:, 0]]

    out = {"source": os.path.basename(path), "crop": box, "triangle": pts(tri),
           "art": [pts(c) for c in sorted(pieces, key=lambda c: -cv2.contourArea(c))]}
    with open(os.path.join(HERE, "logo_trace.json"), "w") as f:
        json.dump(out, f)
    print(f"triangle: {len(out['triangle'])} pts; art pieces: {[len(p) for p in out['art']]}")


if __name__ == "__main__":
    main()
