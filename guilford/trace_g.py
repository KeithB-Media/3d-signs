#!/usr/bin/env python3
"""Trace the Guilford 'G' (with its arrow) from reference/guilford_logo.jpg.

Writes g_logo_trace.json: the G outline in inches-agnostic units where the G's
height is 1.0, origin at the centre of its bounding box, +y up.
Needs: pip install numpy pillow scikit-image shapely
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from shapely.geometry import Polygon
from skimage import measure

HERE = os.path.dirname(os.path.abspath(__file__))
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "reference", "guilford_logo.jpg")

img = np.asarray(Image.open(src).convert("RGB")).astype(float)
# white = bright and unsaturated (excludes the orange bar and the red "In Color")
white = (img.min(axis=2) > 150).astype(float)
W = img.shape[1]
white[:, int(0.34 * W):] = 0                 # left third only: the G
lum = gaussian_filter(white, 1.0)

contours = measure.find_contours(lum, 0.5)
polys = [Polygon([(c[1], c[0]) for c in cs]) for cs in contours if len(cs) > 50]
g = max(polys, key=lambda p: p.area).buffer(0)
g = g.simplify(0.35)                          # px; keeps straight edges and sharp corners

minx, miny, maxx, maxy = g.bounds
h = maxy - miny
cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
pts = [((x - cx) / h, (cy - y) / h) for x, y in g.exterior.coords]
holes = [[((x - cx) / h, (cy - y) / h) for x, y in r.coords] for r in g.interiors]
out = dict(source=os.path.basename(src), height_px=h, aspect=(maxx - minx) / h,
           outline=pts, holes=holes)
with open(os.path.join(HERE, "g_logo_trace.json"), "w") as f:
    json.dump(out, f)
print(f"G: {maxx - minx:.0f} x {h:.0f} px, {len(pts)} points, {len(holes)} holes")
