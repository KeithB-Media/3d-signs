#!/usr/bin/env python3
"""Trace the logo's S from a head-on photo and write s_logo_trace.json.

Usage: python3 trace_s.py PHOTO.jpg
Needs: pip install opencv-python-headless scipy shapely numpy
The photo calibration (circle centre/radii in pixels) matches generate.py PHOTO_*.
"""
import json
import sys

import cv2
import numpy as np
from scipy import ndimage as ndi
from shapely.geometry import Polygon

PHOTO_C, PHOTO_RX, PHOTO_RY = (511, 795), 190, 208   # outer circle in the photo (pixels)
R_BASE = 7.0
CROP = (380, 610, 660, 990)                          # region holding the S
UP = 6                                               # upsampling factor


def trace(path):
    img = cv2.imread(path)
    x0, y0, x1, y1 = CROP
    c = cv2.resize(img[y0:y1, x0:x1], None, fx=UP, fy=UP, interpolation=cv2.INTER_CUBIC)
    b, g, r = [c[:, :, i].astype(int) for i in range(3)]
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    yellow = (r > 150) & (g > 120) & (b < 120) & (r - b > 70)
    dark = (mx < 95) | ((mx < 150) & (mx - mn < 40))      # black, incl. glare-greyed black
    yy, xx = np.mgrid[0:yellow.shape[0], 0:yellow.shape[1]]
    ix, iy = x0 + xx / UP, y0 + yy / UP
    field = ((ix - PHOTO_C[0]) / (PHOTO_RX * 0.925)) ** 2 + ((iy - PHOTO_C[1]) / (PHOTO_RY * 0.925)) ** 2 < 1
    yel = ndi.binary_closing(yellow & field, structure=np.ones((5, 5)), iterations=2)
    # the black S body is the largest dark region bounded by the yellow outline
    cand = dark & field & ~ndi.binary_dilation(yel, iterations=2)
    lab, n = ndi.label(cand)
    core = lab == (np.argmax(ndi.sum(cand, lab, range(1, n + 1))) + 1)
    core = ndi.binary_fill_holes(ndi.binary_closing(core, iterations=3))
    cs, _ = cv2.findContours(core.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cnt = max(cs, key=cv2.contourArea)[:, 0, :].astype(float)
    return np.array([((x0 + x / UP - PHOTO_C[0]) / PHOTO_RX * R_BASE,
                      (PHOTO_C[1] - (y0 + y / UP)) / PHOTO_RY * R_BASE) for x, y in cnt])


def resample(pts, step):
    closed = np.vstack([pts, pts[:1]])
    seg = np.hypot(*np.diff(closed, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.arange(0, s[-1], step)
    return np.stack([np.interp(t, s, closed[:, 0]), np.interp(t, s, closed[:, 1])], 1)


# Real corners only occur at the two serifs (everything else is a smooth curve;
# glare in the photo can otherwise fake a corner). Boxes in inches: (xmin, ymin, xmax, ymax).
SERIF_BOXES = [(-3.5, -4.8, -1.4, -0.9), (2.2, 1.7, 4.2, 5.0)]


def clean(pts, step=0.02, corner_win=0.14, corner_deg=55, sigma=0.40, merge_dist=0.15):
    """Smooth the traced outline but keep serif corners and spur tips sharp."""
    p = resample(pts, step)
    n, w = len(p), max(2, int(corner_win / step))
    a = p[(np.arange(n) - w) % n] - p
    b = p[(np.arange(n) + w) % n] - p
    ang = np.degrees(np.arccos(np.clip((a * b).sum(1) / (np.hypot(*a.T) * np.hypot(*b.T)), -1, 1)))
    in_serif = np.array([any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in SERIF_BOXES)
                         for x, y in p])
    sharp = (ang < 180 - corner_deg) & in_serif
    # one corner per run of sharp points (the sharpest)
    corners = []
    i = 0
    while i < n:
        if sharp[i]:
            j = i
            while j + 1 < n and sharp[j + 1]:
                j += 1
            corners.append(i + int(np.argmin(ang[i:j + 1])))
            i = j + 1
        else:
            i += 1
    # corners closer together than merge_dist are one corner seen twice: smoothing between
    # them leaves a tiny extra point, so keep only the sharper one
    merged = []
    for c in corners:
        if merged and np.hypot(*(p[c] - p[merged[-1]])) < merge_dist:
            if ang[c] < ang[merged[-1]]:
                merged[-1] = c
        else:
            merged.append(c)
    if len(merged) > 1 and np.hypot(*(p[merged[0]] - p[merged[-1]])) < merge_dist:
        if ang[merged[-1]] < ang[merged[0]]:
            merged[0] = merged[-1]
        merged.pop()
    corners = merged or [0]
    out = []
    sg = sigma / step
    for k, c0 in enumerate(corners):
        c1 = corners[(k + 1) % len(corners)]
        idx = np.arange(c0, c0 + ((c1 - c0) % n or n) + 1) % n
        seg = p[idx]
        m = len(seg)
        sm = seg.copy()
        if m > 4:
            # gaussian smoothing with the two corner endpoints pinned
            pad = min(int(3 * sg), m - 2)
            ext = np.vstack([2 * seg[0] - seg[pad:0:-1], seg, 2 * seg[-1] - seg[-2:-pad - 2:-1]])
            ker = np.exp(-0.5 * (np.arange(-pad, pad + 1) / sg) ** 2)
            ker /= ker.sum()
            for d in range(2):
                sm[:, d] = np.convolve(ext[:, d], ker, "valid")[:m]
            sm[0], sm[-1] = seg[0], seg[-1]
        out.extend(sm[:-1].tolist())
    out = convexify_top_left(np.array(out))
    return Polygon(out).buffer(0).simplify(0.003), [p[c].tolist() for c in corners]


def convexify_top_left(ring, x_stop=-2.9, y_stop=2.4):
    """The outer edge of the S from its top round to its left side is one convex
    curve on the locomotive; photo glare leaves a dent there. Walk the outline from
    the topmost point towards the left side and replace that stretch with its
    convex envelope."""
    n = len(ring)
    top = int(np.argmax(ring[:, 1]))
    step = 1 if ring[(top + 5) % n, 0] < ring[top, 0] else -1   # direction heading left
    idx = [top]
    i = top
    while True:
        i = (i + step) % n
        idx.append(i)
        if ring[i, 0] <= x_stop or ring[i, 1] <= y_stop or len(idx) > n // 2:
            break
    arc = ring[idx]
    # convex envelope of the arc (monotone chain, outer side only)
    hull = [arc[0]]
    for q in arc[1:]:
        hull.append(q)
        while len(hull) >= 3:
            (ax, ay), (bx, by), (cx, cy) = hull[-3], hull[-2], hull[-1]
            cross = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
            if cross * step < 0:      # b lies inside the envelope: drop it
                hull.pop(-2)
            else:
                break
    hull = np.array(hull)
    # a convex envelope bridges the dent with a straight chord; instead fit one smooth
    # cubic Bezier through the undamaged envelope points, tangent to the outline at both ends
    keep = [q for q in hull if np.min(np.hypot(*(arc - q).T)) < 1e-9]
    keep = np.array(keep)
    p0, p3 = arc[0], arc[-1]
    t0 = arc[min(8, len(arc) - 1)] - arc[0]
    t0 /= np.hypot(*t0)
    t3 = arc[-1] - arc[-9]
    t3 /= np.hypot(*t3)
    d = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(keep, axis=0).T))])
    tt = d / d[-1]
    b0, b1, b2, b3 = (1 - tt) ** 3, 3 * (1 - tt) ** 2 * tt, 3 * (1 - tt) * tt ** 2, tt ** 3
    base = np.outer(b0 + b1, p0) + np.outer(b2 + b3, p3)
    A = np.concatenate([np.stack([b1 * t0[0], -b2 * t3[0]], 1), np.stack([b1 * t0[1], -b2 * t3[1]], 1)])
    rhs = np.concatenate([keep[:, 0] - base[:, 0], keep[:, 1] - base[:, 1]])
    (alpha, beta), *_ = np.linalg.lstsq(A, rhs, rcond=None)
    c1, c2 = p0 + alpha * t0, p3 - beta * t3
    u = np.linspace(0, 1, len(idx))[:, None]
    new = (1 - u) ** 3 * p0 + 3 * (1 - u) ** 2 * u * c1 + 3 * (1 - u) * u ** 2 * c2 + u ** 3 * p3
    ring = ring.copy()
    ring[idx] = new
    return ring


if __name__ == "__main__":
    raw = trace(sys.argv[1])
    poly, corners = clean(raw)
    print(f"corners kept sharp: {len(corners)}  bounds: {[round(v, 2) for v in poly.bounds]}")
    with open("s_logo_trace.json", "w") as f:
        json.dump({"note": "S letterform traced from a head-on photo of the locomotive logo "
                           "(inches, sign centre origin, +y up). Yellow outline measured ~0.21in.",
                   "core": [[round(x, 4), round(y, 4)] for x, y in poly.exterior.coords]}, f)
