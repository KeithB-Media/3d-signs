#!/usr/bin/env python3
"""Turn a flat full-colour SVG of a sign into a multi-colour 3-D-printed light-box face.

The face is printed FACE-DOWN on the Bambu textured PEI plate (that gives the front its
matte, sparkly finish). Light from the box shines through it:

    front (bed side)                                   back (toward the LEDs)
    z = 0 ........ skin (default 0.6 mm): every colour of the art
    z = skin ..... backing (default 1.0 mm): white, it diffuses the light
    black areas run the full thickness, so they stay black when lit

Usage:
    python3 face.py ART.svg OUTDIR [--window 224] [--disc 239] [--skin 0.6] [--back 1.0]
                    [--merge "#F6CF14=#F5F5F2"] [--blackout 0.12] [--rotate 0]

ART.svg  flat artwork: filled paths, later paths painted over earlier ones (e.g. the
         preview_flat.svg the sign generators write). Only fill colours matter.
OUTDIR   gets face_<colour>.stl per filament, face.3mf (all parts in one object) and
         face_preview.svg.

Sizes are millimetres. The defaults match lightbox.scad (239 mm disc, 224 mm window).
Needs: pip install shapely numpy trimesh svgelements mapbox_earcut manifold3d
"""
import argparse
import json
import os
import zipfile

import numpy as np
import trimesh
from shapely import affinity
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.ops import unary_union
from svgelements import SVG, Path, Shape, Move, Close

WHITE = "#ffffff"


# ------------------------------------------------------------------ SVG -> regions
def _norm(c):
    return "#%02x%02x%02x" % (c.red, c.green, c.blue)


def _lum(hexc):
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _shape_to_geom(shape, tol):
    """svgelements Shape -> shapely geometry, honouring the fill rule."""
    path = abs(Path(shape))
    rings, cur = [], []
    for seg in path:
        if isinstance(seg, Move):
            if len(cur) > 2:
                rings.append(cur)
            cur = [(seg.end.x, seg.end.y)]
            continue
        if isinstance(seg, Close):
            if len(cur) > 2:
                rings.append(cur)
            cur = []
            continue
        n = 1 if type(seg).__name__ == "Line" else max(2, int(seg.length(error=1e-3) / tol))
        for t in np.linspace(0, 1, n + 1)[1:]:
            p = seg.point(t)
            cur.append((p.x, p.y))
    if len(cur) > 2:
        rings.append(cur)
    polys = [Polygon(r).buffer(0) for r in rings]
    polys = [p for p in polys if not p.is_empty]
    if not polys:
        return None
    # even-odd: XOR the rings (also right for ordinary nonzero art with holes)
    g = polys[0]
    for p in polys[1:]:
        g = g.symmetric_difference(p)
    return g.buffer(0)


def load_regions(svg_path, size_mm):
    """Return [(colour, geometry)] in paint order, scaled so the art is size_mm across,
    centred on the origin, +y up."""
    svg = SVG.parse(svg_path)
    vb = svg.viewbox
    w = vb.width if vb is not None else svg.width
    tol = w / 2000.0
    regions = []
    for el in svg.elements():
        if not isinstance(el, Shape) or el.fill is None or el.fill.value is None:
            continue
        if el.fill.alpha == 0:
            continue
        g = _shape_to_geom(el, tol)
        if g is not None and g.area > 0:
            regions.append((_norm(el.fill), g))
    allg = unary_union([g for _, g in regions])
    minx, miny, maxx, maxy = allg.bounds
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    k = size_mm / max(maxx - minx, maxy - miny)
    out = []
    for c, g in regions:
        g = affinity.translate(g, -cx, -cy)
        g = affinity.scale(g, k, -k, origin=(0, 0))          # SVG y is down
        out.append((c, g))
    return out


def flatten(regions):
    """Painter's algorithm: later shapes cover earlier ones. -> {colour: visible area}"""
    vis = {}
    for i, (c, g) in enumerate(regions):
        above = unary_union([h for _, h in regions[i + 1:]]) if i + 1 < len(regions) else None
        v = g.difference(above) if above is not None else g
        vis[c] = unary_union([vis[c], v]) if c in vis else v
    return {c: g for c, g in vis.items() if not g.is_empty}


# ------------------------------------------------------------------ meshes
def _polys(geom):
    if geom.is_empty:
        return []
    if isinstance(geom, Polygon):
        return [geom]
    return [p for p in getattr(geom, "geoms", []) if isinstance(p, Polygon) and p.area > 1e-4]


def extrude(geom, z0, z1):
    meshes = []
    for p in _polys(geom):
        m = trimesh.creation.extrude_polygon(p, z1 - z0)
        m.apply_translation((0, 0, z0))
        meshes.append(m)
    return trimesh.util.concatenate(meshes) if meshes else None


def write_3mf(path, parts):
    """One object made of several parts (one per filament). Bambu Studio / OrcaSlicer /
    PrusaSlicer load it as a single object whose parts you assign to AMS slots."""
    objs, comps = [], []
    for i, (name, mesh) in enumerate(parts, 1):
        v = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in mesh.vertices)
        t = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in mesh.faces)
        objs.append(f'<object id="{i}" name="{name}" type="model"><mesh><vertices>{v}</vertices>'
                    f'<triangles>{t}</triangles></mesh></object>')
        comps.append(f'<component objectid="{i}"/>')
    top = len(parts) + 1
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n'
             '<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<resources>{"".join(objs)}<object id="{top}" name="face" type="model">'
             f'<components>{"".join(comps)}</components></object></resources>'
             f'<build><item objectid="{top}" transform="1 0 0 0 1 0 0 0 1 128 128 0"/></build></model>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr("_rels/.rels",
                   '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr("3D/3dmodel.model", model)


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("svg")
    ap.add_argument("outdir")
    ap.add_argument("--disc", type=float, default=239.0, help="face disc diameter, mm (lightbox face_d)")
    ap.add_argument("--window", type=float, default=224.0, help="visible window in the bezel, mm")
    ap.add_argument("--art", type=float, default=None, help="art diameter, mm (default window + 2)")
    ap.add_argument("--skin", type=float, default=0.6, help="colour skin thickness, mm (3 layers @0.2)")
    ap.add_argument("--back", type=float, default=1.0, help="white backing thickness, mm")
    ap.add_argument("--blackout", type=float, default=0.12,
                    help="colours darker than this luminance (0-1) run full thickness and block light")
    ap.add_argument("--merge", action="append", default=[],
                    help='print one colour with another filament, e.g. "#f6cf14=#f5f5f2" (fewer AMS slots)')
    ap.add_argument("--coupon", type=float, nargs=3, metavar=("X", "Y", "D"),
                    help="test piece: only a D mm circle of the face, centred at X,Y mm (front view)")
    ap.add_argument("--rotate", type=float, default=0.0, help="rotate the art, degrees")
    a = ap.parse_args()

    art_d = a.art or a.window + 2
    T = a.skin + a.back
    os.makedirs(a.outdir, exist_ok=True)

    regions = load_regions(a.svg, art_d)
    merges = dict(m.lower().split("=") for m in a.merge)
    regions = [(merges.get(c, c), g) for c, g in regions]
    vis = flatten(regions)
    if a.rotate:
        vis = {c: affinity.rotate(g, a.rotate, origin=(0, 0)) for c, g in vis.items()}

    disc = Point(0, 0).buffer(a.disc / 2, quad_segs=180)
    if a.coupon:                                                # cut out a small test piece
        cx, cy, cd = a.coupon
        cut = Point(cx, cy).buffer(cd / 2, quad_segs=90)
        vis = {c: affinity.translate(g.intersection(cut), -cx, -cy) for c, g in vis.items()}
        vis = {c: g for c, g in vis.items() if g.area > 0.5}
        disc = affinity.translate(disc.intersection(cut), -cx, -cy)
    art = unary_union(list(vis.values()))
    margin = disc.difference(art.buffer(0.01))                 # outside the art: black, no light
    white = max(vis, key=_lum)                                  # lightest colour = backing filament
    dark = [c for c in vis if _lum(c) < a.blackout]
    black = dark[0] if dark else "#141414"

    solids = {}                                                 # colour -> [(geom, z0, z1)]
    for c, g in vis.items():
        g = g.buffer(0)
        if c in dark:
            solids.setdefault(black, []).append((g, 0, T))
        else:
            solids.setdefault(c, []).append((g, 0, a.skin))
    # white skin: overlap it into the white backing (a hair inside it) so the two merge cleanly
    if white in solids:
        solids[white] = [(g.buffer(-0.002), 0, a.skin + 0.1) for g, z0, z1 in solids[white]]
    solids.setdefault(black, []).append((margin, 0, T))
    blackout = unary_union([g for g, z0, z1 in solids[black]])
    solids.setdefault(white, []).append((disc.difference(blackout), a.skin, T))

    # print face-down: mirror so the art reads correctly from the bed side (the front)
    parts, info = [], []
    for c, items in solids.items():
        ms = [extrude(affinity.scale(g, -1, 1, origin=(0, 0)), z0, z1) for g, z0, z1 in items]
        ms = [m for m in ms if m is not None]
        if not ms:
            continue
        m = trimesh.boolean.union(ms, engine="manifold") if len(ms) > 1 else ms[0]
        name = f"face_{c.lstrip('#')}"
        m.export(os.path.join(a.outdir, name + ".stl"))
        parts.append((name, m))
        role = "blackout (full thickness)" if c == black else \
            "skin + white backing" if c == white else "skin"
        info.append(dict(file=name + ".stl", colour=c, role=role,
                         visible_area_cm2=round(vis.get(c, margin).area / 100, 1) if c in vis else None))
    write_3mf(os.path.join(a.outdir, "face.3mf"), parts)

    # unmirrored front-view preview
    body = []
    for c in [black] + [c for c in vis if c != black]:
        g = blackout if c == black else vis[c].difference(blackout)
        for p in _polys(g):
            d = " ".join("M" + " L".join(f"{x:.2f},{-y:.2f}" for x, y in list(r.coords)[:-1]) + " Z"
                         for r in [p.exterior, *p.interiors])
            body.append(f'<path d="{d}" fill="{c}" fill-rule="evenodd"/>')
    r = a.disc / 2
    with open(os.path.join(a.outdir, "face_preview.svg"), "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{a.disc}mm" height="{a.disc}mm" '
                f'viewBox="{-r} {-r} {a.disc} {a.disc}">{"".join(body)}'
                f'<circle r="{a.window / 2}" fill="none" stroke="#888" stroke-width="0.5" stroke-dasharray="3 3"/></svg>')
    with open(os.path.join(a.outdir, "face.json"), "w") as f:
        json.dump(dict(disc_mm=a.disc, window_mm=a.window, art_mm=art_d, skin_mm=a.skin,
                       thickness_mm=T, filaments=info), f, indent=1)
    print(f"{len(parts)} filaments, {T:.1f} mm thick, art {art_d:.0f} mm on a {a.disc:.0f} mm disc")
    for i in info:
        print(f"  {i['colour']}  {i['role']:28s} {i['file']}")


if __name__ == "__main__":
    main()
