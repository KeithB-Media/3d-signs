#!/usr/bin/env python3
"""Trace the spruce tree from the Maine Eastern logo image into tree_trace.json.

Usage:  python3 trace_tree.py [reference_logo.png]
Needs:  pip install opencv-python-headless numpy

Output points are in logo pixels, relative to the centre of the yellow circle, +y up.
generate.py scales them to the sign.
"""
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CENTRE_PX = (223.3, 222.6)  # centre of the yellow disc in the reference image (circle fit)
UP = 8                       # supersampling factor for a sub-pixel outline


def main(path):
    img = cv2.imread(path)[:, :, ::-1].astype(np.float32)
    # 'greenness' from the red channel: 0 on the yellow disc (R~240), 1 on green (R~19)
    t = np.clip((240 - img[..., 0]) / 221, 0, 1)

    cx, cy = CENTRE_PX

    # the tree is the large green blob inside the disc
    Y, X = np.indices(t.shape)
    inside = (X - cx) ** 2 + (Y - cy) ** 2 < 112 ** 2
    n, lab, stats, _ = cv2.connectedComponentsWithStats(((t > 0.5) & inside).astype(np.uint8), 8)
    tree = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    x, y, w, h, _ = stats[tree]
    pad = 4
    x0, y0 = x - pad, y - pad
    # use the soft greenness around the tree (anti-aliased edge), but only near the blob
    near = cv2.dilate((lab[y0:y + h + pad, x0:x + w + pad] == tree).astype(np.uint8), np.ones((3, 3), np.uint8))
    crop = t[y0:y + h + pad, x0:x + w + pad] * near

    big = cv2.resize(crop, None, fx=UP, fy=UP, interpolation=cv2.INTER_CUBIC)
    big = cv2.GaussianBlur(big, (0, 0), UP * 0.35)
    mask = (big > 0.5).astype(np.uint8)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cnts, key=cv2.contourArea)[:, 0, :].astype(float)
    px = c / UP + [x0 - 0.5 + 0.5 / UP, y0 - 0.5 + 0.5 / UP]
    pts = [(round(float(u - cx), 3), round(float(cy - v), 3)) for u, v in px]
    out = {"source": os.path.basename(path), "centre_px": [round(float(cx), 2), round(float(cy), 2)],
           "tree": pts}
    with open(os.path.join(HERE, "tree_trace.json"), "w") as f:
        json.dump(out, f)
    print(f"traced tree: {len(pts)} points, {w}x{h} px, circle centre ({cx:.1f}, {cy:.1f})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "reference_logo.png"))
