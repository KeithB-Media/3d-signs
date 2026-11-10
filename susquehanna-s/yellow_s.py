#!/usr/bin/env python3
"""Yellow-S-only version of the logo (no flag): black disc, yellow pinstripe ring,
black S with its yellow outline. Writes svg/preview_yellow_s.svg, a flat colour SVG
for ../lightbox/face.py.  Run: python3 yellow_s.py
"""
import contextlib
import io
import os

import generate as g

with contextlib.redirect_stdout(io.StringIO()):
    p = g.parts()
C = g.COLORS
layers = [
    ("black", g.circle(g.R_BASE)),
    ("yellow", g.circle(g.R_YELLOW)),
    ("black", g.circle(g.R_BLACK)),        # black ring + black field (no flag)
    ("yellow", p["s_outline"]),
    ("black", p["s"]),
]
body = "\n".join(f'<path d="{g.path_d(geom)}" fill="{C[c]}" fill-rule="evenodd"/>' for c, geom in layers)
path = os.path.join(g.OUT, "preview_yellow_s.svg")
with open(path, "w") as f:
    f.write(g.svg_doc(body, "Yellow S only - flat colour preview"))
print("wrote", path)
