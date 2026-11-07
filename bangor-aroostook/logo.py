"""Parametric model of the Bangor & Aroostook triangle logo.

Built from clean geometry (straight lines, circular arcs, scalloped waves) so that the cut
lines are smooth. The parameters are fitted to a scan of the logo by fit_logo.py and
stored in logo_params.json. Units are scan pixels, x measured from the symmetry axis,
y pointing DOWN (image convention); generate.py scales and flips it.
"""
import json
import math
import os

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
FAR = 1000.0


def rounded(poly, r):
    return poly.buffer(-r, join_style="round").buffer(r, join_style="round") if r > 0 else poly


def closing(g, r):
    return g.buffer(r, join_style="round").buffer(-r, join_style="round") if r > 0 else g


def triangle(p):
    """Rounded triangle: sharp apex at (0, tri_apex), base corners at (+-tri_hw, tri_base)."""
    t = Polygon([(0, p["tri_apex"]), (p["tri_hw"], p["tri_base"]), (-p["tri_hw"], p["tri_base"])])
    return rounded(t, p["tri_r"])


def scallop(p, y_low, x0=-FAR / 2, x1=FAR / 2, n=6000):
    """Wave edge: circular arcs hanging between sharp upward cusps at x = +-cusp, +-3cusp...
    y_low is the edge's lowest point (at x = 0)."""
    xs = np.linspace(x0, x1, n)
    per = 2 * p["cusp"]
    d = np.abs(xs - per * np.round(xs / per))      # distance to the nearest arc centre
    R = p["wave_R"]
    ys = y_low - (R - np.sqrt(np.maximum(R * R - d * d, 0)))
    return list(zip(xs, ys))


def below(curve):
    """Region below a curve (y-down: larger y)."""
    return Polygon(curve + [(curve[-1][0], FAR), (curve[0][0], FAR)])


def wave_band(p, y_top):
    band = below(scallop(p, y_top)).difference(below(scallop(p, y_top + p["wave_t"])))
    return band.intersection(box(-p["wave_xe"], -FAR, p["wave_xe"], FAR))


def chevron_region(apex_y, slope, r):
    """Filled region under an upside-down V with sharp apex (0, apex_y); legs have
    dx/dy = slope; apex rounded with radius r."""
    h = FAR / 4
    t = Polygon([(0, apex_y), (slope * h, apex_y + h), (-slope * h, apex_y + h)])
    return rounded(t, r)


def leg_offset_apex(apex_y, slope, w):
    """Apex of the inner chevron whose legs are w (perpendicular) inside the outer ones."""
    return apex_y + w * math.sqrt(1 + slope * slope) / slope


def upper(p):
    """The 'A' together with the upper wave (one piece)."""
    y_top = p["wave_y"] - p["wave_gap"]
    bot = below(scallop(p, y_top + p["wave_t"]))
    band = wave_band(p, y_top)
    outer = chevron_region(p["a_apex"], p["a_slope"], p["a_r"]).difference(bot)
    outer = outer.intersection(box(-p["wave_xe"], -FAR, p["wave_xe"], FAR))
    white = closing(unary_union([band, outer]), p["a_fillet"])
    white = white.intersection(box(-p["wave_xe"], -FAR, p["wave_xe"], FAR))
    inner_apex = leg_offset_apex(p["a_apex"], p["a_slope"], p["a_w"])
    hole = closing(unary_union([chevron_region(inner_apex, p["a_slope"], p["a_ri"]), bot]),
                   p["a_joint"])
    return white.difference(hole)


def lower(p):
    return wave_band(p, p["wave_y"])


def leaf(p):
    """Leaf: a pointed outline cut by a centre stem and V-shaped veins -> 7 pieces."""
    env = chevron_region(p["leaf_apex"], p["leaf_slope"], 0)
    m, g = p["vein_m"], p["vein_g"]

    def above_v(c):        # region above the V line y = c - m|x|  (y-down)
        return Polygon([(-FAR, c - m * FAR), (0, c), (FAR, c - m * FAR), (FAR, -FAR), (-FAR, -FAR)])

    cs = [p["vein_c0"] + k * p["vein_p"] for k in range(4)]
    region = env.intersection(above_v(cs[3]))
    for c in cs[:3]:
        region = region.difference(above_v(c + g).difference(above_v(c)))
    stem = box(-p["stem_w"] / 2, cs[0] + g - 1, p["stem_w"] / 2, FAR)
    return region.difference(stem)


def load_params():
    with open(os.path.join(HERE, "logo_params.json")) as f:
        return json.load(f)


def logo(p=None):
    p = p or load_params()
    return dict(triangle=triangle(p), upper=upper(p), lower=lower(p), leaf=leaf(p))
