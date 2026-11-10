#!/usr/bin/env python3
"""Trace the black S and the circle sizes from the flat logo image; write s_trace.json.

Usage: python3 trace_s.py [source/logo.png]
Needs: pip install opencv-python-headless numpy shapely pillow
The logo is a black outer ring, a yellow disc and a black S. Coordinates are written
normalised to the outer circle (radius 1, centre origin, +y up), so generate.py can
scale them to any sign size.
"""
import json
import os
import sys

import cv2
import numpy as np
from PIL import Image
from shapely.geometry import Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
UP = 4          # upsampling factor; cubic interpolation gives sub-pixel edges


def load(path):
    im = np.array(Image.open(path).convert("RGBA")).astype(float)
    a = im[..., 3:4] / 255
    rgb = im[..., :3] * a + 255 * (1 - a)          # transparent corners -> white
    return rgb


def main(path):
    rgb = load(path)
    alpha_disc = np.array(Image.open(path).convert("RGBA"))[..., 3] > 128
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    yellow = (r > 180) & (g > 140) & (b < 140)

    # outer circle and yellow disc: fit from their pixel areas and centroids
    def disc(mask):
        ys, xs = np.nonzero(mask)
        return xs.mean(), ys.mean(), (mask.sum() / np.pi) ** 0.5
    cx, cy, R = disc(alpha_disc)
    yfill = cv2.morphologyEx(yellow.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3)))
    cnts, _ = cv2.findContours(yfill, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    ymask = np.zeros_like(yfill)
    cv2.drawContours(ymask, [max(cnts, key=cv2.contourArea)], -1, 1, -1)
    _, _, Ry = disc(ymask.astype(bool))

    # the S: dark pixels inside the yellow disc, at sub-pixel precision
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    lum = np.where(ymask.astype(bool), lum, 255)
    big = cv2.resize(lum, None, fx=UP, fy=UP, interpolation=cv2.INTER_CUBIC)
    dark = (big < 110).astype(np.uint8)
    cnts, _ = cv2.findContours(dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cnts, key=cv2.contourArea)[:, 0, :].astype(float)
    pts = [((x / UP + 0.5 / UP - 0.5 - cx) / R, (cy - (y / UP + 0.5 / UP - 0.5)) / R) for x, y in c]
    s = Polygon(pts).buffer(0).simplify(0.0004)
    out = {
        "note": "Traced from source/logo.png. Units: outer circle radius = 1, centre origin, +y up.",
        "outer_px": [round(cx, 2), round(cy, 2), round(R, 2)],
        "yellow_r": round(Ry / R, 4),
        "s": [[round(x, 5), round(y, 5)] for x, y in s.exterior.coords[:-1]],
    }
    with open(os.path.join(HERE, "s_trace.json"), "w") as f:
        json.dump(out, f)
    print(f"outer circle r={R:.1f}px at ({cx:.1f},{cy:.1f}); yellow disc r={Ry / R:.4f} of outer; "
          f"S: {len(out['s'])} points")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "source", "logo.png"))
