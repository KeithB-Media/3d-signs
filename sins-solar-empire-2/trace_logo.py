#!/usr/bin/env python3
"""Trace the black Sins of a Solar Empire II logo (source/logo.png) into polygons.

Writes logo_trace.json: a list of shapes, each {"outer": [[x,y],...], "holes": [[[x,y],...],...]}
in source-image pixels (y down). The (R) mark is left out.
Run:  python3 trace_logo.py [image]   (needs: pip install opencv-python-headless numpy)
"""
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
UP = 4            # trace at 4x for smoother edges
EPS = 0.35        # polygon simplification tolerance, source pixels


def main(path):
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if im.shape[2] == 4:                       # transparent PNG: composite on white
        a = im[:, :, 3:4] / 255.0
        im = (im[:, :, :3] * a + 255 * (1 - a)).astype(np.uint8)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    big = cv2.resize(gray, None, fx=UP, fy=UP, interpolation=cv2.INTER_CUBIC)
    big = cv2.GaussianBlur(big, (5, 5), 0)
    _, ink = cv2.threshold(big, 128, 255, cv2.THRESH_BINARY_INV)
    contours, hier = cv2.findContours(ink, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    hier = hier[0]
    shapes = []
    h, w = gray.shape
    for i, c in enumerate(contours):
        if hier[i][3] != -1:
            continue                           # a hole; handled with its parent
        x, y, bw, bh = cv2.boundingRect(c)
        x, y, bw, bh = x / UP, y / UP, bw / UP, bh / UP
        if bw * bh < 30:
            continue                           # specks
        if x > w - 60 and y < h * 0.45 and bw < 40:
            continue                           # the (R) mark
        def pts(cc):
            ap = cv2.approxPolyDP(cc, EPS * UP, True)[:, 0, :] / UP
            return [[round(float(px), 3), round(float(py), 3)] for px, py in ap]
        holes, j = [], hier[i][2]
        while j != -1:
            if cv2.contourArea(contours[j]) > 30 * UP * UP:
                holes.append(pts(contours[j]))
            j = hier[j][0]
        shapes.append({"outer": pts(c), "holes": holes, "bbox": [x, y, bw, bh]})
    shapes.sort(key=lambda s: (s["bbox"][1] > h * 0.33, s["bbox"][0]))
    with open(os.path.join(HERE, "logo_trace.json"), "w") as f:
        json.dump({"size": [w, h], "shapes": shapes}, f)
    print(f"{len(shapes)} shapes traced")
    for s in shapes:
        print("  bbox", [round(v, 1) for v in s["bbox"]], "holes", len(s["holes"]))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "source", "logo.png"))
