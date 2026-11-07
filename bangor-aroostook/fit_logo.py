#!/usr/bin/env python3
"""Fit the parametric logo (logo.py) to the raw trace (logo_trace.json) -> logo_params.json.

Each part (triangle, A + upper wave, lower wave, leaf) is fitted on its own by
minimising the area that differs between the model and the trace.
    pip install shapely numpy scipy opencv-python-headless
    python3 fit_logo.py
"""
import json
import os

import cv2
import numpy as np
from scipy.optimize import minimize
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

import logo

HERE = os.path.dirname(os.path.abspath(__file__))
SC = 4          # raster resolution (pixels per scan pixel)

INIT = dict(
    tri_apex=-39, tri_base=344, tri_hw=210, tri_r=40,
    cusp=48.3, wave_R=68, wave_y=266.7, wave_t=30.7, wave_xe=122.7, wave_gap=51.7,
    a_apex=55, a_slope=0.5625, a_r=25, a_w=27, a_ri=8, a_fillet=15, a_joint=12,
    leaf_apex=150.4, leaf_slope=0.536, vein_m=0.9, vein_c0=168, vein_p=25, vein_g=7, stem_w=8,
)
GROUPS = {
    "triangle": ["tri_apex", "tri_base", "tri_hw", "tri_r"],
    "lower": ["cusp", "wave_R", "wave_y", "wave_t", "wave_xe"],
    "upper": ["wave_gap", "a_apex", "a_slope", "a_r", "a_w", "a_ri", "a_fillet", "a_joint"],
    "leaf": ["leaf_apex", "leaf_slope", "vein_m", "vein_c0", "vein_p", "vein_g", "stem_w"],
}


def raster(geom, shape):
    img = np.zeros(shape, np.uint8)
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    for p in polys:
        if p.is_empty:
            continue
        cv2.fillPoly(img, [np.round((np.array(p.exterior.coords) + [200, 0]) * SC).astype(np.int32)], 1)
        for r in p.interiors:
            cv2.fillPoly(img, [np.round((np.array(r.coords) + [200, 0]) * SC).astype(np.int32)], 0)
    return img


def main():
    tr = json.load(open(os.path.join(HERE, "logo_trace.json")))
    shape = (380 * SC, 400 * SC)

    def poly(pts):
        return Polygon([(x - 200, y) for x, y in pts]).buffer(0)
    target = {
        "triangle": raster(poly(tr["triangle"]), shape),
        "upper": raster(poly(tr["art"][0]), shape),
        "lower": raster(poly(tr["art"][1]), shape),
        "leaf": raster(unary_union([poly(a) for a in tr["art"][2:]]), shape),
    }
    p = dict(INIT)
    for _ in range(2):
        for name, keys in GROUPS.items():
            def cost(v):
                q = dict(p, **dict(zip(keys, v)))
                try:
                    g = getattr(logo, name)(q)
                except Exception:
                    return 1e12
                return float(np.count_nonzero(raster(g, shape) != target[name]))
            x0 = [p[k] for k in keys]
            res = minimize(cost, x0, method="Nelder-Mead",
                           options=dict(maxiter=1500, xatol=0.01, fatol=1, initial_simplex=None))
            p.update(dict(zip(keys, res.x)))
            iou = 1 - res.fun / max(1, np.count_nonzero(target[name]))
            print(f"{name:9s} mismatch {res.fun / SC / SC:8.1f} px^2  ({iou:.3f} of area)")
    p = {k: round(float(v), 3) for k, v in p.items()}
    with open(os.path.join(HERE, "logo_params.json"), "w") as f:
        json.dump(p, f, indent=1)
    print(json.dumps(p))


if __name__ == "__main__":
    main()
