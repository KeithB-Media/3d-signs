#!/usr/bin/env python3
"""Trace the lettering and trees from the two herald images in source/.

Writes trace.json: every light-coloured (orange / yellow) shape in each herald as
polygons in image pixels (y down), with the circles/borders measured too.
generate.py turns these into inch-sized cut layers.

Run:  python3 trace.py        (needs: pip install opencv-python-headless numpy)
"""
import json
import os

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UP = 16          # upsampling factor before thresholding (smooth edges from a small image)
BLUR = 0.55      # gaussian blur, in source pixels, applied after upsampling


def light_mask(path):
    """0..1 'light colour' value: red channel is ~0 on the green field and ~250 on orange/yellow."""
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    return np.clip(a[..., 0] / 240.0, 0, 1)


def contours(t, region=None):
    """Return list of (outer, [holes]) in source-pixel coords for the light shapes."""
    h, w = t.shape
    big = cv2.resize(t, (w * UP, h * UP), interpolation=cv2.INTER_CUBIC)
    big = cv2.GaussianBlur(big, (0, 0), BLUR * UP)
    m = (big > 0.5).astype(np.uint8)
    if region is not None:
        m &= region
    cs, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    out = []
    if hier is None:
        return out
    hier = hier[0]
    for i, c in enumerate(cs):
        if hier[i][3] != -1:
            continue
        holes = []
        j = hier[i][2]
        while j != -1:
            holes.append(cs[j])
            j = hier[j][0]
        conv = lambda c: [[(float(x) + 0.5) / UP - 0.5, (float(y) + 0.5) / UP - 0.5] for x, y in c[:, 0, :]]
        if cv2.contourArea(c) < (2 * UP) ** 2:
            continue
        out.append({"outer": conv(c), "holes": [conv(hh) for hh in holes if cv2.contourArea(hh) > UP * UP]})
    return out


def bbox(p):
    xs = [x for x, _ in p["outer"]]
    ys = [y for _, y in p["outer"]]
    return min(xs), min(ys), max(xs), max(ys)


def main():
    res = {}

    # ---------------- square herald (300 x 219): orange on green
    t = light_mask(os.path.join(HERE, "source", "herald_square.png"))
    h, w = t.shape
    # blank out the orange border so only the artwork inside the green field is traced
    region = np.zeros((h * UP, w * UP), np.uint8)
    region[11 * UP:(h - 11) * UP, 11 * UP:(w - 11) * UP] = 1
    shapes = contours(t, region)
    for s in shapes:
        s["bbox"] = bbox(s)
    res["square"] = {"size": [w, h], "shapes": shapes}

    # ---------------- round herald (250 x 250): yellow on green, black outside
    t = light_mask(os.path.join(HERE, "source", "herald_round.png"))
    h, w = t.shape
    yy, xx = np.mgrid[0:h * UP, 0:w * UP]
    rr = np.hypot((xx + 0.5) / UP - w / 2, (yy + 0.5) / UP - h / 2)
    region = (rr < 104).astype(np.uint8)          # inside the yellow ring
    shapes = contours(t, region)
    for s in shapes:
        s["bbox"] = bbox(s)
    res["round"] = {"size": [w, h], "shapes": shapes}

    with open(os.path.join(HERE, "trace.json"), "w") as f:
        json.dump(res, f)
    for k, v in res.items():
        print(k, len(v["shapes"]), "shapes")
        for s in v["shapes"]:
            print("   bbox", [round(b) for b in s["bbox"]], "holes", len(s["holes"]))


if __name__ == "__main__":
    main()
