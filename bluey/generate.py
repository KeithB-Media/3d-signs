#!/usr/bin/env python3
"""Generate laser-cut SVG layers for a stacked stand-up blue heeler pup figure (~12" tall).

Units are inches, +y up, feet at y=0; SVG output flips y.
Run:  python3 generate.py   (needs: pip install shapely numpy)
"""
import json
import os

import numpy as np
from shapely import affinity
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "svg")

SCALE = 1.0          # 1.0 = about 12.6" tall figure; everything scales with it
OUTLINE = 0.16       # navy outline showing around the figure (backer offset)
MARGIN = 0.4         # sheet margin around parts

COLORS = {
    "outline": "#1B1B2E",
    "blue": "#88C1EC",
    "navy": "#33366B",
    "pale blue": "#D6EEF9",
    "tan": "#EFCF77",
    "white": "#FFFFFF",
    "black": "#161616",
    "mouth": "#6B1A2A",
    "red": "#E0606A",
    "green": "#7DBF5A",
}


# ------------------------------------------------------------------ helpers
def ell(cx, cy, rx, ry, rot=0):
    e = affinity.scale(Point(0, 0).buffer(1, quad_segs=64), rx, ry)
    return affinity.translate(affinity.rotate(e, rot, origin=(0, 0)), cx, cy)


def capsule(p0, p1, w):
    return LineString([p0, p1]).buffer(w / 2, quad_segs=32)


def curve(pts, w, n=60):
    """Smooth thick stroke through control points (Catmull-Rom)."""
    P = np.array(pts, float)
    P = np.vstack([P[0], P, P[-1]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return LineString(out).buffer(w / 2, quad_segs=32)


def smooth(g, r=0.08):
    """Round off sharp inside and outside corners."""
    return g.buffer(r, quad_segs=24).buffer(-2 * r, quad_segs=24).buffer(r, quad_segs=24)


def mirror(g):
    return affinity.scale(g, -1, 1, origin=(0, 0))


def both(g):
    return unary_union([g, mirror(g)])


def rpoly(pts, r):
    return Polygon(pts).buffer(-r).buffer(r, quad_segs=24)


# ------------------------------------------------------------------ figure
def close(g, r):
    """Fill inside corners / narrow notches with radius r (outside corners unchanged)."""
    return g.buffer(r, quad_segs=24).buffer(-r, quad_segs=24)


# The pose follows the reference picture (jumping, arms up). Shapes are laid out in
# reference-picture pixels (x right, y down, ~64 px per inch) and converted to inches.
PPI_REF = 64.0
REF_X0, REF_Y0 = 470.0, 1370.0


def P(x, y):
    return ((x - REF_X0) / PPI_REF, (REF_Y0 - y) / PPI_REF)


def pe(x, y, rx, ry, rot=0):
    cx, cy = P(x, y)
    return ell(cx, cy, rx / PPI_REF, ry / PPI_REF, -rot)


def pp(pts, r=0):
    g = Polygon([P(*q) for q in pts])
    return g.buffer(-r / PPI_REF).buffer(r / PPI_REF, quad_segs=24) if r else g


def pc(pts, w):
    return curve([P(*q) for q in pts], w / PPI_REF)


def fluffy(x, y, r, n=5, rot=0):
    """Cartoon paw: a disc with n soft bumps."""
    g = [pe(x, y, r * 0.75, r * 0.75)]
    for k in range(n):
        a = np.radians(rot + 360 * k / n)
        g.append(pe(x + r * 0.55 * np.cos(a), y + r * 0.55 * np.sin(a), r * 0.42, r * 0.42))
    return unary_union(g)


def parts():
    # ---- outline pieces
    ear_l = pp([(282, 815), (352, 632), (405, 750)], 14)
    ear_r = pp([(405, 745), (478, 598), (525, 735)], 14)
    head = pp([(272, 830), (300, 775), (420, 728), (520, 712), (580, 770), (612, 790),
               (608, 845), (565, 875), (545, 935), (500, 1000), (440, 1000), (380, 960),
               (320, 960), (285, 905)], 26)
    torso = pp([(320, 930), (590, 850), (628, 1135), (395, 1200)], 34)
    arm_l = pc([(380, 1000), (300, 985), (225, 965)], 44)
    arm_r = pc([(585, 950), (640, 905), (690, 865)], 42)
    hand_l = fluffy(205, 965, 40, 5, 180)
    hand_r = fluffy(695, 860, 38, 5, -40)
    leg_l = pc([(430, 1170), (418, 1250), (405, 1320)], 54)
    leg_r = pc([(560, 1140), (620, 1200), (680, 1255)], 50)
    foot_l = pe(398, 1338, 48, 33, -5)
    foot_r = pe(698, 1268, 50, 34, 40)
    tail = pc([(380, 1125), (330, 1165), (275, 1195), (225, 1212)], 58)
    tail_end = fluffy(215, 1212, 42, 4, 200)
    figure = close(unary_union([ear_l, ear_r, head, torso, arm_l, arm_r, hand_l, hand_r,
                                leg_l, leg_r, foot_l, foot_r, tail, tail_end]), 0.08)

    # grassy mound joining both feet so it can stand in the base
    gx = np.linspace(310, 780, 60)
    top = [(x, 1372 - 70 * np.exp(-((x - 705) / 60) ** 2) - 6 * np.sin(x / 9)) for x in gx]
    grass = pp([(310, 1372)] + top + [(780, 1372)], 4).union(pp([(300, 1360), (790, 1360), (790, 1372), (300, 1372)]))
    grass = smooth(grass.difference(figure.buffer(0.0)), 0.03)
    grass = unary_union([g for g in getattr(grass, "geoms", [grass]) if g.area > 0.3])
    figure = figure.difference(box(-20, -20, 20, 0.0))

    # ---- level 3 (on the blue body / grass)
    eye_l = pe(422, 842, 50, 56, -10)
    eye_r = pe(497, 792, 32, 41, -15)
    eyes = unary_union([eye_l, eye_r])
    muzzle = pp([(472, 850), (505, 800), (545, 768), (600, 775), (625, 800), (620, 852), (570, 880),
                 (548, 930), (520, 975), (478, 955)], 18).intersection(figure.buffer(-0.0))
    mouth = pp([(440, 958), (548, 940), (532, 990), (500, 1018), (462, 1012)], 16)
    muzzle = muzzle.difference(mouth.buffer(0.07)).difference(eyes.buffer(0.07))
    dark_head = head.intersection(pp([(240, 680), (570, 680), (548, 735), (500, 762), (440, 790),
                                      (400, 880), (392, 975), (240, 990)]))
    dark_head = dark_head.difference(eye_l.buffer(13 / PPI_REF)).difference(eye_r.buffer(10 / PPI_REF))
    spots = unary_union([pe(352, 1050, 18, 30, 15), pe(368, 1110, 15, 22, 10)])
    tail_tip = unary_union([tail_end, tail.intersection(pp([(150, 1100), (282, 1150), (290, 1260), (150, 1300)]))])
    dark = unary_union([ear_l, ear_r, dark_head, spots.intersection(figure), tail_tip])
    dark = smooth(dark.difference(eyes.buffer(0.07)).difference(pe(380, 762, 34, 19, -25).buffer(0.07)), 0.03)
    dark = dark.intersection(figure).buffer(-0.04).buffer(0.04)
    brows = unary_union([pe(380, 762, 34, 19, -25), pe(484, 720, 32, 16, -10)])
    belly = pp([(412, 1050), (500, 1020), (595, 1010), (615, 1130), (430, 1192)], 38)
    pale = unary_union([belly, hand_l, hand_r, foot_l, foot_r, brows]).intersection(figure)

    # ---- level 4
    inner = unary_union([pp([(308, 790), (350, 668), (378, 745)], 9),
                         pp([(432, 735), (474, 628), (500, 718)], 9)])
    inner = inner.difference(brows.buffer(0.07)).intersection(dark.buffer(-0.03))
    pupils = unary_union([pe(420, 852, 13, 20, -10), pe(492, 803, 10, 16, -15)])
    nose = pe(585, 808, 32, 27, 25).intersection(muzzle.buffer(-0.04))
    tongue = pe(490, 1005, 34, 13, -8).intersection(mouth.buffer(-0.05))
    teeth = pp([(450, 962), (540, 946), (536, 966), (452, 980)], 6).intersection(mouth.buffer(-0.05))

    return figure, grass, [
        ("layer3_navy", "navy", dark, 3, "ears, head patch, back spots, tail tip"),
        ("layer3_pale_blue", "pale blue", pale, 3, "belly, paws, feet, eyebrows"),
        ("layer3_tan", "tan", muzzle, 3, "muzzle"),
        ("layer3_white", "white", eyes, 3, "eyes"),
        ("layer3_mouth", "mouth", mouth, 3, "open mouth"),
        ("layer4_tan", "tan", inner, 4, "inner ears (on the navy ears)"),
        ("layer4_black", "black", pupils, 4, "pupils (on the eyes)"),
        ("layer4_navy", "navy", nose, 4, "nose (on the muzzle)"),
        ("layer4_red", "red", tongue, 4, "tongue (in the mouth)"),
        ("layer4_white", "white", teeth, 4, "teeth (in the mouth)"),
    ]


def scaled(g):
    return affinity.scale(g, SCALE, SCALE, origin=(0, 0))


THICK = {1: 0.25, 2: 0.125, 3: 0.125, 4: 0.125}


def build():
    fig, grass, upper = parts()
    both_ = unary_union([fig, grass])
    backer = close(both_.buffer(OUTLINE, quad_segs=24), 0.08)
    backer = backer.difference(box(-20, -20, 20, 0.0))
    # 0.75" tab below the ground line that sits in the base slot
    xs = both_.intersection(box(-20, 0, 20, 0.3)).bounds
    tab = box(xs[0], -0.75, xs[2], 0.3)
    backer = smooth(unary_union([backer, tab]), 0.04)
    layers = [("layer1_backer", "outline", backer, 1, "full outline + 0.75\" tab for the base slot"),
              ("layer2_body_blue", "blue", fig, 2, "whole body"),
              ("layer2_grass", "green", grass, 2, "grass mound under the feet")] + upper
    for stem, _, g, lvl, _ in layers[1:]:
        below = unary_union([h for _, _, h, l, _ in layers if l == lvl - 1])
        over = g.difference(below.buffer(1e-6)).area
        if over > 1e-4:
            print(f"  WARNING {stem}: {over:.4f} sq in overhangs level {lvl - 1}")
        thin = g.difference(g.buffer(-0.05).buffer(0.05)).area
        if thin > 0.01:
            print(f"  note {stem}: {thin:.3f} sq in of features thinner than 0.1\"")
    z = {1: 0.0}
    for l in (2, 3, 4):
        z[l] = z[l - 1] + THICK[l - 1]
    return [(s, c, scaled(g), THICK[l], n, z[l], l) for s, c, g, l, n in layers], []


def base_parts(backer, backer_t):
    """Stand: a top plate with a slot for the tab, glued to a solid bottom plate."""
    tab_x = backer.intersection(box(-20, -1, 20, -0.1)).bounds
    w = max(7.0, tab_x[2] - tab_x[0] + 1.5)
    c = (tab_x[0] + tab_x[2]) / 2
    plate = box(c - w / 2, -1.6, c + w / 2, 1.6).buffer(-0.35).buffer(0.35, quad_segs=24)
    tab_w = backer.intersection(box(-20, -1, 20, -0.1)).bounds
    slot = box(tab_w[0] - 0.01, -backer_t / 2 - 0.006, tab_w[2] + 0.01, backer_t / 2 + 0.006)
    return plate.difference(slot), plate


# ------------------------------------------------------------------ SVG out
def path_d(geom, ox, oy):
    polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    out = []
    for p in polys:
        if p.is_empty:
            continue
        for ring in [p.exterior, *p.interiors]:
            pts = list(ring.coords)
            out.append("M" + " L".join(f"{x - ox:.4f},{oy - y:.4f}" for x, y in pts[:-1]) + " Z")
    return " ".join(out)


def line_d(line, ox, oy):
    return "M" + " L".join(f"{x - ox:.4f},{oy - y:.4f}" for x, y in line)


def svg_doc(body, title, w, h):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}in" height="{h:.3f}in" '
            f'viewBox="0 0 {w:.4f} {h:.4f}">\n<title>{title}</title>\n{body}\n</svg>\n')


def cut_path(d):
    return f'<path d="{d}" fill="none" stroke="#FF0000" stroke-width="0.01" fill-rule="evenodd"/>'


def main():
    os.makedirs(OUT, exist_ok=True)
    layers, mouth = build()
    minx, miny, maxx, maxy = layers[0][2].bounds
    ox, oy = minx - MARGIN, maxy + MARGIN           # shared origin: all figure layers line up
    W, H = maxx - minx + 2 * MARGIN, maxy - miny + 2 * MARGIN

    preview, rows = [], []
    for i, (stem, color, geom, thick, note, z, lvl) in enumerate(layers, 1):
        d = path_d(geom, ox, oy)
        body = cut_path(d)
        if False:
            body += "\n" + "\n".join(
                f'<path d="{line_d(m, ox, oy)}" fill="none" stroke="#0000FF" stroke-width="0.01"/>'
                for m in mouth)
        with open(os.path.join(OUT, stem + ".svg"), "w") as f:
            f.write(svg_doc(body, f"Layer {lvl} - {note} - paint {color}"
                           ,
                            W, H))
        preview.append((stem, color, d, z, thick))
        pieces = len(geom.geoms) if isinstance(geom, MultiPolygon) else 1
        rows.append(f"| {lvl} | `svg/{stem}.svg` | {color} | {thick}\" | {pieces} | {note} |")

    mouth_d = " ".join(line_d(m, ox, oy) for m in mouth)
    body = "\n".join(f'<path d="{d}" fill="{COLORS[c]}" fill-rule="evenodd"/>' for _, c, d, _, _ in preview)
    with open(os.path.join(OUT, "preview_flat.svg"), "w") as f:
        f.write(svg_doc(body, "Flat colour preview", W, H))

    tcols = ["#000", "#06c", "#0a0", "#00c", "#c90", "#c60", "#888", "#a00", "#f80", "#808", "#0cc", "#c0c"]
    body = "\n".join(f'<path d="{d}" fill="none" stroke="{tcols[k % len(tcols)]}" stroke-width="0.015" fill-rule="evenodd"/>'
                     for k, (_, _, d, _, _) in enumerate(preview))
    with open(os.path.join(OUT, "placement_template.svg"), "w") as f:
        f.write(svg_doc(body, "Glue-up placement template (print 1:1)", W, H))

    # base / stand
    top, bottom = base_parts(layers[0][2], layers[0][3])
    bx0, by0, bx1, by1 = bottom.bounds
    bw, bh = bx1 - bx0 + 2 * MARGIN, by1 - by0 + 2 * MARGIN
    for stem, g, note in [("base_top_slot", top, "base top plate with slot - 1/4\" stock"),
                          ("base_bottom", bottom, "base bottom plate - 1/4\" stock")]:
        with open(os.path.join(OUT, stem + ".svg"), "w") as f:
            f.write(svg_doc(cut_path(path_d(g, bx0 - MARGIN, by1 + MARGIN)), note, bw, bh))

    with open(os.path.join(OUT, "layers.json"), "w") as f:
        json.dump({"w": W, "h": H, "mouth": mouth_d, "base_cx": (bx0 + bx1) / 2 - ox, "base_y": oy,
                   "base": {"d": path_d(top, ox, oy), "w": bx1 - bx0, "d_bottom": path_d(bottom, ox, oy)},
                   "layers": [{"stem": s, "color": COLORS[c], "d": d, "z": z, "t": t}
                              for s, c, d, z, t in preview]}, f)
    print("\n".join(rows))
    z = max(p[3] + p[4] for p in preview)
    print(f"figure: {maxx - minx:.2f}\" wide x {maxy - miny:.2f}\" tall (incl. tab); "
          f"stack {z:.3f}\"; base {bx1 - bx0:.2f}\" x {by1 - by0:.2f}\"")


if __name__ == "__main__":
    main()
