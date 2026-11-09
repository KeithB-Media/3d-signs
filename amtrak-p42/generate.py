#!/usr/bin/env python3
"""Generate laser-cut SVG layers for a stacked 1/8" MDF sign of the front of a
GE Genesis P42DC locomotive, with working LED headlights and ditch lights.

Units are inches. Design origin is the bottom centre of the sign (top of rail),
+x to the right, +y up; the SVG output flips y. Run:
    python3 generate.py          (needs: pip install shapely numpy)

Every layer is cut from 1/8" MDF. Layers 1-5 are the hidden "core": they give
the sign its thickness, and hold the battery pocket, the wire channels and the
hanging keyholes. Layers 6-9 are the visible relief.
"""
import json
import math
import os

from shapely import affinity
from shapely.geometry import Polygon, Point, MultiPolygon, LineString, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "svg")

T = 0.125                     # MDF thickness
HALF_W = 8.0                  # sign is 16" wide ...
TOP = 23.0                    # ... and 23" tall (about 1:7.5 scale)
MARGIN = 0.25                 # border around the drawing in the SVG files

# ---- livery (Phase V style: platinum body, dark blue skirt, red pinstripe).
# Change these to repaint the previews; the cut files don't depend on them.
COLORS = {
    "core": "#1d1d1f",        # hidden layers: paint the edges black
    "glass": "#2c3640",       # top of layer 5, seen through the windshield
    "silver": "#b9bec4",
    "nose": "#c9cdd2",
    "blue": "#1f3a63",
    "red": "#c0272d",
    "black": "#161616",
    "gray": "#4a4d52",
    "chrome": "#e6e8ea",
}

# ---- electronics
LED_HOLE = 0.25               # 5 mm LEDs push in from the front (loose fit, dab of glue)
LED_RING_ID = 0.36            # chrome lens ring: the LED flange sits inside it
CHANNEL_W = 0.32              # wire channel width (in layers 4 and 5)
POCKET = (2.50, 1.95)         # battery holder pocket, through layers 1-5 (0.625" deep)
POCKET_C = (0.0, 9.1)         # pocket centre: behind the nose, under the headlight
HEADLIGHTS = [(-0.45, 11.85), (0.45, 11.85)]
DITCHLIGHTS = [(-5.55, 5.15), (5.55, 5.15)]
KEYHOLES = [(-4.6, 19.2), (4.6, 19.2)]


def mirror(pts):
    """Close a half outline (x >= 0, listed bottom-to-top) into a symmetric polygon."""
    return Polygon(pts + [(-x, y) for x, y in reversed(pts)])


def both(geom):
    return unary_union([geom, affinity.scale(geom, -1, 1, origin=(0, 0))])


def rounded(geom, r):
    return geom.buffer(-r, join_style=1).buffer(r, join_style=1)


# ------------------------------------------------------------------ the shapes
def body():
    """Carbody from the sill (y=3.4) to the roof: straight lower sides, upper
    sides leaning in (Genesis 'tumblehome'), rounded roof corners."""
    half = [(0, 3.4), (8.0, 3.4), (8.0, 14.4), (6.85, 21.75), (6.55, 22.55),
            (6.05, 22.92), (5.4, 23.0), (0, 23.0)]
    return rounded(mirror(half), 0.05)


def plow():
    half = [(0, 0.0), (4.3, 0.0), (6.45, 1.85), (6.45, 3.5), (0, 3.5)]
    return mirror(half)


def plow_face():
    """Raised plow plate with three horizontal ribs cut out as grooves."""
    face = plow().buffer(-0.18, join_style=2)
    face = face.intersection(box(-9, 0, 9, 3.15))
    for y, half in ((0.9, 4.0), (1.65, 4.7), (2.4, 5.4)):   # grooves stop short of the ends
        face = face.difference(box(-half, y, half, y + 0.12))
    return face


def steps():
    """Corner step ladders (treads cut out)."""
    ladder = box(6.72, 0.85, 7.88, 3.4)
    for y0 in (1.15, 2.15):
        ladder = ladder.difference(box(6.88, y0, 7.72, y0 + 0.62))
    return both(ladder)


def windows():
    """Windshield openings (each pane leans in with the cab side)."""
    pane = Polygon([(0.38, 15.75), (5.95, 15.75), (5.35, 19.65), (0.38, 19.65)])
    return both(rounded(pane, 0.35))


def gaskets():
    return windows().buffer(0.24, join_style=1).difference(windows())


def wipers():
    """Parked wipers, joined to the gasket at both ends so they're strong."""
    arms = []
    for x0, y0, x1, y1 in [(4.9, 15.63, 0.26, 16.9)]:
        arm = LineString([(x0, y0), (x1, y1)]).buffer(0.09, cap_style=2)
        arms.append(arm)
    return both(unary_union(arms))


def nose():
    """Forward-sloping nose under the windshield; the triangles left over at
    each side are the cab 'cheeks', one layer lower."""
    half = [(0, 7.8), (7.45, 7.8), (6.45, 15.3), (0, 15.3)]
    return rounded(mirror(half), 0.12)


def blue_skirt():
    return box(-HALF_W, 3.4, HALF_W, 7.8)


def red_stripe():
    return box(-HALF_W + 0.05, 7.42, HALF_W - 0.05, 7.8)


def anticlimber():
    return box(-6.1, 5.85, 6.1, 6.45)


def headlight_bezel():
    """'Home plate' headlight housing, point down."""
    cx, cy = 0.0, 11.65
    pts = [(-1.15, 0.75), (1.15, 0.75), (1.15, -0.25), (0, -0.95), (-1.15, -0.25)]
    return rounded(Polygon([(cx + x, cy + y) for x, y in pts]), 0.12)


def ditch_housings():
    return unary_union([rounded(box(x - 0.48, y - 0.42, x + 0.48, y + 0.42), 0.12)
                        for x, y in DITCHLIGHTS])


def lens_rings():
    return unary_union([Point(x, y).buffer(0.32).difference(Point(x, y).buffer(LED_RING_ID / 2))
                        for x, y in HEADLIGHTS + DITCHLIGHTS])


def coupler():
    shank = box(-0.42, 3.2, 0.42, 6.0)
    head = rounded(box(-0.95, 2.35, 0.95, 3.55), 0.18)
    knuckle_gap = box(-0.12, 2.35, 0.12, 2.95)
    return unary_union([shank, head]).difference(knuckle_gap)


def hoses():
    """MU and air hoses hanging either side of the coupler."""
    pcs = []
    for x, y_top, y_bot in [(1.55, 3.9, 1.35), (2.05, 3.9, 1.55), (2.55, 3.9, 1.35)]:
        pcs.append(LineString([(x, y_top), (x + 0.12, y_bot)]).buffer(0.1, cap_style=1))
    return both(unary_union(pcs))


def grab_irons():
    pcs = [box(7.3, 3.95, 7.5, 7.15),                          # beside the steps
           LineString([(6.0, 13.0), (5.75, 14.6)]).buffer(0.09, cap_style=1)]  # on the cheeks
    return both(unary_union(pcs))


def silhouette():
    return unary_union([body(), plow(), both(box(6.72, 0.85, 7.88, 3.6))])


# ------------------------------------------------------------------ electronics
def led_holes():
    return unary_union([Point(p).buffer(LED_HOLE / 2) for p in HEADLIGHTS + DITCHLIGHTS])


def pocket():
    w, h = POCKET
    return rounded(box(POCKET_C[0] - w / 2, POCKET_C[1] - h / 2,
                       POCKET_C[0] + w / 2, POCKET_C[1] + h / 2), 0.06)


def channels():
    cx, cy = POCKET_C
    w = CHANNEL_W / 2
    runs = [LineString([(cx, cy), (0, HEADLIGHTS[0][1])]),
            LineString(HEADLIGHTS)]
    for x, y in DITCHLIGHTS:
        s = 1 if x > 0 else -1
        runs.append(LineString([(cx, cy), (s * 1.6, 6.9), (x, y)]))
    lines = unary_union([r.buffer(w, cap_style=1, join_style=1) for r in runs])
    led_seats = unary_union([Point(p).buffer(0.2) for p in HEADLIGHTS + DITCHLIGHTS])
    return unary_union([lines, led_seats])


def keyholes():
    """Keyhole slot cut in the backer: the screw head goes in the big hole and
    the sign drops 0.5" so the shank sits at the top of the slot."""
    return unary_union([unary_union([Point(x, y).buffer(0.2),
                                     box(x - 0.09, y, x + 0.09, y + 0.5),
                                     Point(x, y + 0.5).buffer(0.09)]) for x, y in KEYHOLES])


def keyhole_reliefs():
    """Room behind the keyhole for the screw head (layers 2 and 3)."""
    return unary_union([rounded(box(x - 0.26, y - 0.26, x + 0.26, y + 0.78), 0.2) for x, y in KEYHOLES])


def back_cover():
    """Cover plate for the battery pocket, screwed onto the back."""
    w, h = POCKET[0] + 0.8, POCKET[1] + 0.8
    cx, cy = POCKET_C
    plate = rounded(box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), 0.15)
    screws = unary_union([Point(cx + sx * (w / 2 - 0.2), cy + sy * (h / 2 - 0.2)).buffer(0.07)
                          for sx in (-1, 1) for sy in (-1, 1)])
    switch_slot = rounded(box(cx - 0.55, cy - 0.25, cx + 0.55, cy + 0.25), 0.1)
    return plate.difference(screws).difference(switch_slot)


# ------------------------------------------------------------------ layers
def build():
    sil = silhouette()
    core = sil.difference(pocket())
    windows_cut = windows()
    leds = led_holes()
    plow_region = plow()
    body_l6 = body().difference(windows_cut).difference(leds)

    layers = [
        # (stem, [(paint, geometry)], note)
        ("layer1_backer", [("core", core.difference(keyholes()))],
         "backer: battery pocket + 2 keyhole hangers"),
        ("layer2_core", [("core", core.difference(keyhole_reliefs()))], "core: screw-head room behind keyholes"),
        ("layer3_core", [("core", core.difference(keyhole_reliefs()))], "core: screw-head room behind keyholes"),
        ("layer4_core_wiring", [("core", core.difference(channels()))], "core: wire channels"),
        ("layer5_glass_wiring", [("glass", core.difference(channels()))],
         "core: wire channels; top shows through the windshield"),
        ("layer6_body", [("silver", body_l6),
                         ("black", plow_region.difference(body()).difference(leds)),
                         ("black", steps())],
         "carbody (windshield cut out), plow backing, corner steps"),
        ("layer7_nose_skirt", [("nose", nose().difference(leds)),
                               ("blue", blue_skirt().difference(leds)),
                               ("black", gaskets().union(wipers())),
                               ("black", plow_face())],
         "nose, blue skirt, windshield gaskets + wipers, plow face"),
        ("layer8_details", [("black", headlight_bezel().difference(leds)),
                            ("black", ditch_housings().difference(leds)),
                            ("red", red_stripe()),
                            ("black", anticlimber().difference(coupler().buffer(0.03))),
                            ("gray", coupler()),
                            ("black", hoses()),
                            ("black", grab_irons())],
         "headlight bezel, ditch light housings, red stripe, anticlimber, coupler, hoses, grab irons"),
        ("layer9_lens_rings", [("chrome", lens_rings())], "chrome lens rings (4)"),
    ]
    return layers


# ------------------------------------------------------------------ SVG out
W_SVG = 2 * HALF_W + 2 * MARGIN
H_SVG = TOP + 2 * MARGIN


def path_d(geom):
    polys = geom.geoms if hasattr(geom, "geoms") else [geom]
    out = []
    for p in polys:
        if p.is_empty:
            continue
        for ring in [p.exterior, *p.interiors]:
            pts = list(ring.coords)
            out.append("M" + " L".join(f"{x + HALF_W + MARGIN:.4f},{TOP + MARGIN - y:.4f}"
                                       for x, y in pts[:-1]) + " Z")
    return " ".join(out)


def svg_doc(body_, title, w=W_SVG, h=H_SVG):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}in" height="{h:.3f}in" '
            f'viewBox="0 0 {w:.3f} {h:.3f}">\n<title>{title}</title>\n{body_}\n</svg>\n')


def count(geom):
    return len(geom.geoms) if hasattr(geom, "geoms") else 1


def check(stem, geom):
    """Warn about slivers that won't survive the laser."""
    thin = geom.difference(geom.buffer(-0.05).buffer(0.05))
    if thin.area > 0.002:
        print(f"  note: {stem} has {thin.area:.3f} sq in narrower than 0.10\"")


def main():
    os.makedirs(OUT, exist_ok=True)
    layers = build()
    data, rows, z = [], [], 0.0
    for i, (stem, pieces, note) in enumerate(layers, 1):
        allgeom = unary_union([g for _, g in pieces])
        check(stem, allgeom)
        # each piece is cut on its own, so edges between paints are cut too
        cut = "\n".join(f'<path d="{path_d(g)}" fill="none" stroke="#FF0000" stroke-width="0.01"/>'
                        for _, g in pieces)
        with open(os.path.join(OUT, stem + ".svg"), "w") as f:
            f.write(svg_doc(cut, f"Layer {i} - {note}"))
        paints = sorted({c for c, _ in pieces}, key=list(COLORS).index)
        rows.append(f"| {i} | `svg/{stem}.svg` | {', '.join(paints)} | {sum(count(g) for _, g in pieces)} | {note} |")
        data.append({"stem": stem, "z": z, "t": T,
                     "pieces": [{"color": COLORS[c], "d": path_d(g)} for c, g in pieces]})
        z += T

    # back cover plate (not part of the stack)
    cover = back_cover()
    with open(os.path.join(OUT, "back_cover.svg"), "w") as f:
        f.write(svg_doc(f'<path d="{path_d(cover)}" fill="none" stroke="#FF0000" stroke-width="0.01"/>',
                        "Battery pocket cover - screws to the back"))

    # flat colour preview
    body_ = "\n".join(f'<path d="{p["d"]}" fill="{p["color"]}" fill-rule="evenodd"/>'
                      for L in data for p in L["pieces"])
    with open(os.path.join(OUT, "preview_flat.svg"), "w") as f:
        f.write(svg_doc(body_, "Flat colour preview"))

    # placement template: every layer's outline in its own colour (print 1:1)
    tcols = ["#000", "#888", "#888", "#0a0", "#0a0", "#00c", "#c90", "#c00", "#808"]
    body_ = "\n".join(f'<path d="{" ".join(p["d"] for p in L["pieces"])}" fill="none" '
                      f'stroke="{tcols[k]}" stroke-width="0.015"/>' for k, L in enumerate(data))
    with open(os.path.join(OUT, "placement_template.svg"), "w") as f:
        f.write(svg_doc(body_, "Glue-up placement template (print 1:1)"))

    meta = {"w": W_SVG, "h": H_SVG, "lights": [[x + HALF_W + MARGIN, TOP + MARGIN - y]
                                                 for x, y in HEADLIGHTS + DITCHLIGHTS],
            "layers": data}
    with open(os.path.join(OUT, "layers.json"), "w") as f:
        json.dump(meta, f)
    print("\n".join(rows))
    print(f"total stack height: {z:.3f}\"  |  sheet size {W_SVG:.2f}\" x {H_SVG:.2f}\"")


if __name__ == "__main__":
    main()
