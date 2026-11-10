#!/usr/bin/env python3
"""Nest every piece for a production run onto 24" x 96" strips of 1/8" MDF.

* The laser cuts 23.5" across the strip. To be safe, the strip is split into
  23.5" x 23.5" blocks, so each block can be its own job - no part crosses a block line.
* Parts longer than 23.5" (the rectangle's base and pinstripe) go in a long section of
  72.5" at the start of a strip; that strip's last 23.5" is an ordinary block.
  Those strips need the feeder to cut a part longer than one block in one job.
* 1/4" layers are cut twice from 1/8" stock and laminated.

Writes cut-sheets/strip_NN.svg (whole strip) and cut-sheets/blocks/strip_NN_X.svg (one
job per block). Red = cut. Blue = labels and block lines: set to "do not output".
Run:  python3 nest.py [sets]      (default 5 of each design)
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation
from scipy.signal import fftconvolve
from shapely import affinity
from shapely.geometry import MultiPolygon

import generate
import generate_rectangle
import generate_round_ring
import generate_square

HERE = os.path.dirname(os.path.abspath(__file__))

args = [a for a in sys.argv[1:] if not a.startswith("--")]
SETS = int(args[0]) if args else 5
FULL = "--full-strip" in sys.argv   # the feeder cuts a whole 96" strip as one job
RINGS = "--rings" in sys.argv       # cut hidden lower layers as rings; parts nest in the centres
SIZE = next((float(a.split("=")[1]) for a in sys.argv if a.startswith("--size=")), 14.0)
SCALE = SIZE / 14.0                 # 14" round/square at 1.0; the rectangle scales with them
LAND = 0.75                         # glue land: how far a ring runs under the layer above it
OUT = os.path.join(HERE, "cut-sheets", "_".join(
    [f"{SIZE:g}in"] + (["rings"] if RINGS else []) + (["full-strip"] if FULL else ["blocks"])))
STOCK_W = 24.0             # material width
CUT_W = 23.5               # cutting width across the strip
STRIP_L = 96.0
BLOCK = STRIP_L if FULL else 23.5   # block length along the strip
LONG = STRIP_L - 23.5      # long section for parts over 23.5" (block mode)
GAP = 0.15                 # minimum space between parts and to block edges
RES = 0.05                 # nesting grid (inches per cell)

# (code, name, module, index of the gray field layer: everything below it is hidden
#  except a thin band, so with --rings those layers become rings - except the backer)
DESIGNS = [("RND", "round", generate, 4), ("RING", "round ring", generate_round_ring, 3),
           ("SQ", "square", generate_square, 3), ("RECT", "rectangle", generate_rectangle, 3)]


def pieces():
    out = []
    for code, _, mod, field_i in DESIGNS:
        layers = mod.build()
        for i, (stem, color, geom, thick, _) in enumerate(layers, 1):
            copies = round(thick / 0.125)
            g0 = affinity.scale(geom.simplify(0.002), SCALE, -SCALE, origin=(0, 0))   # SVG y-down
            above = affinity.scale(layers[i][2], SCALE, -SCALE, origin=(0, 0)) if i < len(layers) else None
            for c in range(copies):
                # a ring keeps LAND of glue under the next layer up; the backer (copy a of layer 1) stays solid
                ring = RINGS and i < field_i and not (i == 1 and c == 0)
                g = g0.difference(above.buffer(-LAND)) if ring else g0
                # a layer made of a big part plus small ones (the G and its lettering) is
                # nested as two units: the G, and the lettering kept together as one line
                units = [g]
                if isinstance(g, MultiPolygon):
                    big = [q for q in g.geoms if q.area > 0.3 * g.area]
                    rest = [q for q in g.geoms if q.area <= 0.3 * g.area]
                    units = big + ([MultiPolygon(rest)] if rest else [])
                for s in range(1, SETS + 1):
                    for u, geom_u in enumerate(units):
                        part = "" if len(units) == 1 else (" G" if u == 0 else " text")
                        tag = f"{code} L{i}{'ab'[c] if copies > 1 else ''}{' ring' if ring else ''}{part} #{s}"
                        out.append(dict(label=tag, color=color, geom=geom_u))
    return out


def raster(geom, shape=None):
    minx, miny, maxx, maxy = geom.bounds
    w, h = shape or (int(np.ceil(maxx / RES)) + 1, int(np.ceil(maxy / RES)) + 1)
    img = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(img)
    for p in (geom.geoms if isinstance(geom, MultiPolygon) else [geom]):
        d.polygon([(x / RES, y / RES) for x, y in p.exterior.coords], fill=1)
        for r in p.interiors:
            d.polygon([(x / RES, y / RES) for x, y in r.coords], fill=0)
    return np.asarray(img, dtype=bool)


class Region:
    def __init__(self, length):
        self.length = length
        self.occ = np.zeros((int(CUT_W / RES), int(length / RES)), dtype=bool)  # rows = across
        m = int(np.ceil(GAP / RES))
        self.occ[:m, :] = self.occ[-m:, :] = self.occ[:, :m] = self.occ[:, -m:] = True
        self.placed = []

    def try_place(self, variants):
        best = None
        for g, mask in variants:
            mh, mw = mask.shape
            if mh > self.occ.shape[0] or mw > self.occ.shape[1]:
                continue
            hit = fftconvolve(self.occ.astype(np.float32), mask[::-1, ::-1].astype(np.float32), mode="valid")
            free = np.argwhere(hit < 0.5)
            if not len(free):
                continue
            # leftmost along the strip, then nearest the edge
            k = np.lexsort((free[:, 0], free[:, 1]))[0]
            r, c = free[k]
            if best is None or (c, r) < (best[1][1], best[1][0]):
                best = (g, (r, c), mask)
        if best is None:
            return False
        g, (r, c), mask = best
        self.occ[r:r + mask.shape[0], c:c + mask.shape[1]] |= mask
        return affinity.translate(g, c * RES, r * RES)


def variants(geom):
    out = []
    dil = int(np.ceil(GAP / RES)) + 1
    yy, xx = np.mgrid[-dil:dil + 1, -dil:dil + 1]
    disk = xx ** 2 + yy ** 2 <= dil ** 2
    seen = set()
    for ang in (0, 90, 180, 270):
        g = affinity.rotate(geom, ang, origin=(0, 0))
        minx, miny, _, _ = g.bounds
        g = affinity.translate(g, -minx + dil * RES, -miny + dil * RES)
        key = tuple(round(v, 2) for v in g.bounds)
        if key in seen:
            continue
        seen.add(key)
        m = np.pad(raster(g), ((0, dil), (0, dil)))
        out.append((g, binary_dilation(m, disk)))
    return out


def fits_block(geom):
    minx, miny, maxx, maxy = geom.bounds
    a, b = sorted((maxx - minx, maxy - miny))
    pad = 4 * GAP + 2 * RES          # edge margin on both sides plus the part's own clearance
    return a <= CUT_W - pad and b <= BLOCK - pad


def main():
    import shutil
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(os.path.join(OUT, "blocks") if not FULL else OUT, exist_ok=True)

    ps = pieces()
    long_ps = [p for p in ps if not fits_block(p["geom"])]
    short_ps = [p for p in ps if fits_block(p["geom"])]

    cache = {}

    def var(p):
        k = id(p["geom"])
        if k not in cache:
            cache[k] = variants(p["geom"])
        return cache[k]

    def pack(long_ps, short_ps):
        strips = []            # each strip: list of (x offset, Region)
        longs = []

        for p in long_ps:
            for reg in longs:
                g = reg.try_place(var(p))
                if g:
                    reg.placed.append((p, g))
                    break
            else:
                reg = Region(LONG)
                g = reg.try_place(var(p))
                if not g:
                    raise SystemExit(f"{p['label']} does not fit a {LONG}\" section")
                reg.placed.append((p, g))
                longs.append(reg)
                strips.append([(0.0, reg), (LONG, Region(BLOCK))])

        regions = [r for s in strips for _, r in s]
        for p in short_ps:
            for reg in regions:
                g = reg.try_place(var(p))
                if g:
                    reg.placed.append((p, g))
                    break
            else:
                reg = Region(BLOCK)
                g = reg.try_place(var(p))
                if not g:
                    raise SystemExit(f"{p['label']} does not fit a block")
                reg.placed.append((p, g))
                regions.append(reg)
                per_strip = int(STRIP_L // BLOCK)
                if not strips or len(strips[-1]) >= per_strip or strips[-1][0][1].length != BLOCK:
                    strips.append([])
                strips[-1].append((len(strips[-1]) * BLOCK, reg))
        return strips

    # greedy packing depends on the order: try a few and keep the fewest strips
    def size_key(p):
        minx, miny, maxx, maxy = p["geom"].bounds
        return max(maxx - minx, maxy - miny)

    orders = [lambda q: -q["geom"].area, lambda q: -size_key(q),
              lambda q: -(size_key(q) ** 2 + q["geom"].area)]
    best = None
    for key in orders:
        st = pack(sorted(long_ps, key=key), sorted(short_ps, key=key))
        last = sum(len(r.placed) for _, r in st[-1])
        score = (len(st), last)
        print(f"  order {orders.index(key) + 1}: {len(st)} strips")
        if best is None or score < best[0]:
            best = (score, st)
    strips = best[1]

    # ---- write SVGs
    y0 = (STOCK_W - CUT_W) / 2

    def path(g, ox, oy):
        polys = g.geoms if isinstance(g, MultiPolygon) else [g]
        d = []
        for poly in polys:
            for ring in [poly.exterior, *poly.interiors]:
                pts = list(ring.coords)[:-1]
                d.append("M" + " L".join(f"{x + ox:.4f},{y + oy:.4f}" for x, y in pts) + " Z")
        return " ".join(d)

    def body(reg, ox, oy):
        cut, lab = [], []
        for p, g in reg.placed:
            cut.append(path(g, ox, oy))
            c = g.representative_point() if g.geom_type == "Polygon" else max(g.geoms, key=lambda q: q.area).representative_point()
            size = 0.45 if g.area > 20 else 0.22
            lab.append(f'<text x="{c.x + ox:.3f}" y="{c.y + oy:.3f}" font-size="{size}" text-anchor="middle" '
                       f'font-family="sans-serif">{p["label"]} {p["color"]}</text>')
        return cut, lab

    def doc(w, h, cut, guides, labels, title):
        return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}in" height="{h}in" viewBox="0 0 {w} {h}">\n'
                f'<title>{title}</title>\n'
                f'<g id="guides_do_not_output" fill="none" stroke="#0066FF" stroke-width="0.02">{"".join(guides)}</g>\n'
                f'<g id="labels_do_not_output" fill="#0066FF">{"".join(labels)}</g>\n'
                f'<g id="cut" fill="none" stroke="#FF0000" stroke-width="0.01">'
                f'<path fill-rule="evenodd" d="{" ".join(cut)}"/></g>\n</svg>\n')

    rows = []
    for si, strip in enumerate(strips, 1):
        cut, labels, guides = [], [], [f'<rect x="0" y="0" width="{STRIP_L}" height="{STOCK_W}"/>']
        for bi, (ox, reg) in enumerate(strip):
            letter = "ABCD"[bi] if not FULL else "full"
            guides.append(f'<rect x="{ox}" y="{y0}" width="{reg.length}" height="{CUT_W}" stroke-dasharray="0.3 0.2"/>')
            labels.append(f'<text x="{ox + 0.3}" y="{y0 + 0.5}" font-size="0.4" font-family="sans-serif">'
                          f'strip {si} block {letter}{" (LONG)" if reg.length > BLOCK else ""}</text>')
            c, l = body(reg, ox, y0)
            cut += c
            labels += l
            rows.append((si, letter, reg))
            if FULL:
                continue
            bc, bl = body(reg, 0, 0)
            with open(os.path.join(OUT, "blocks", f"strip_{si:02d}_{letter}{'_LONG' if reg.length > BLOCK else ''}.svg"), "w") as f:
                f.write(doc(reg.length, CUT_W, bc, [f'<rect x="0" y="0" width="{reg.length}" height="{CUT_W}"/>'], bl,
                            f"strip {si} block {letter}"))
        with open(os.path.join(OUT, f"strip_{si:02d}.svg"), "w") as f:
            f.write(doc(STRIP_L, STOCK_W, cut, guides, labels, f"strip {si} of {len(strips)} - 1/8 MDF 24x96"))

    n_parts = sum(len(r.placed) for _, _, r in rows)
    print(f"{n_parts} parts for {SETS} of each design on {len(strips)} strips "
          f"({(len(strips) + 1) // 2} full 4x8 sheets cut in half lengthwise)")
    for si, letter, reg in rows:
        used = sum(g.area for _, g in reg.placed) / (reg.length * CUT_W)
        print(f"  strip {si:2d} {letter}{' LONG' if reg.length > BLOCK else '     '}: {len(reg.placed):3d} parts, {used:4.0%} used")


if __name__ == "__main__":
    main()
