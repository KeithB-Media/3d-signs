"""Trace the red Milwaukee logo from a flat image into polygons (logo_trace.json).

Usage: python3 trace_logo.py source/logo.png
The logo is all straight edges, so the coverage (alpha, or red-ness on a white background) is upsampled, thresholded at
50 % (sub-pixel edges from the anti-aliasing) and each contour is simplified to a polygon.
Pieces smaller than MIN_AREA (the (R) mark) are dropped.
"""
import json
import os
import sys

import cv2
import numpy as np

UP = 8              # upsampling factor
EPS = 0.45          # polygon simplification tolerance, in source pixels
MIN_AREA = 900      # source px^2; drops the (R) mark (~500 px^2), keeps the i dot (~1400)


def main(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(np.float32)
    b, g, r = im[:, :, 0], im[:, :, 1], im[:, :, 2]
    red = np.clip((r - g) / max(1.0, float(np.percentile(r - g, 99.5))), 0, 1)
    if im.shape[2] == 4:                       # transparent PNG: coverage is in the alpha
        red = (im[:, :, 3] / 255.0) * (r - g > 40)
    big = cv2.resize(red, None, fx=UP, fy=UP, interpolation=cv2.INTER_CUBIC)
    mask = (big > 0.5).astype(np.uint8)
    contours, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    hier = hier[0]
    pieces = []
    for i, c in enumerate(contours):
        if hier[i][3] != -1:                    # holes are attached to their parent below
            continue
        if cv2.contourArea(c) / UP ** 2 < MIN_AREA:
            continue
        rings = [c]
        k = hier[i][2]
        while k != -1:
            rings.append(contours[k])
            k = hier[k][0]
        out = []
        for ring in rings:
            a = cv2.approxPolyDP(ring, EPS * UP, True)[:, 0, :]
            out.append([[round((x + 0.5) / UP - 0.5, 2), round((y + 0.5) / UP - 0.5, 2)] for x, y in a])
        pieces.append(out)
    pieces.sort(key=lambda p: min(x for x, _ in p[0]))
    dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo_trace.json")
    with open(dst, "w") as f:
        json.dump({"source": os.path.basename(path), "pieces": pieces}, f)
    print(f"{len(pieces)} pieces, {sum(len(r) for p in pieces for r in p)} points -> {dst}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "source/logo.png")
