#!/usr/bin/env python3
"""Generate laser-cut SVG files for a stacked 1/8" MDF railroad crossing signal
with working (battery powered) flashing lights.

Units are inches. Design origin = centre of the crossbuck, +y up (SVG output flips y).
Every part sits on a numbered 1/8" layer ("z"), 0 = against the wall.

    pip install shapely numpy fonttools
    python3 generate.py          # writes svg/ (cut files), preview/, layers.json
"""
import json
import math
import os

from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from shapely import affinity
from shapely.geometry import Point, Polygon, MultiPolygon, box as rect, LineString
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "svg")
PREVIEW = os.path.join(HERE, "preview")

T = 0.125                  # stock thickness (1/8" MDF); only used for previews / notes

# ------------------------------------------------------------- main sizes
BLADE_L, BLADE_W = 18.0, 3.4      # crossbuck blades (real ones are 48 x 9)
BLADE_R = 0.08                    # blade corner radius
CROSS_CAP = 1.65                  # letter cap height on the blades
POLE_W, POLE_FRONT_W = 1.25, 0.85 # pole: back two layers / narrower front layer
POLE_TOP, POLE_BOTTOM = 3.6, -24.0
TRACKS_TOP = -4.8                 # top of the "2" tab
TAB_W, TAB_H = 2.8, 2.5
PLATE_W, PLATE_H = 9.0, 3.0
TRACKS_NUMBER = "2"
LAMP_X, LAMP_Y = 6.5, -14.4       # lamp centres (x = +/-LAMP_X)
DISC_D = 7.0                      # black background disc
ARM_H, ARM_FRONT_H = 0.9, 0.65
ARM_END = LAMP_X + 1.0            # arms run this far out (hidden behind the discs)
BOX_W, BOX_H, BOX_R = 4.2, 2.9, 0.2  # junction box = battery compartment
BOX_WALL = 0.25
BOX_CORNER = 0.5                  # solid corner blocks that hold the lid magnets
MAGNET_D = 0.255                  # 1/4" x 1/8" disc magnets
BUTTON_SLOT = (1.2, 0.30)         # x position and width of the push-button slot (bottom wall)
PLAQUE_W, PLAQUE_H, PLAQUE_R = 4.3, 3.0, 0.22
PLAQUE_GAP = 0.35                 # gap between box and plaque
PLAQUE_LINES = ["REPORT PROBLEM", "OR EMERGENCY", "1-800-555-5555"]
PLAQUE_XING = ("X-ING", "836 597 H")

# lamp housing (all centred on the lamp)
LENS_D = 2.40                     # red acrylic lens
HOUSING_OD = 3.3
CAVITY_ID = 2.2                   # LED chamber, also the lip that holds the lens
LENS_POCKET = LENS_D + 0.02
LED_HOLE = 0.205                  # 5 mm LED body
LED_FLANGE_HOLE = 0.30            # LED rim sits in the disc layer behind
WIRE_HOLE = 0.30
HOOD_ID, HOOD_OD = 2.70, HOUSING_OD
HOOD_SPAN = 210                   # degrees, centred on the top
HOOD_LAYERS = 4
CAVITY_LAYERS = 3

CENTRE_BOLT = 0.17                # hole for a #6 bolt through the crossbuck centre
KEYHOLE = (0.40, 0.19, 0.55)      # head hole dia, slot width, slide length
KEYHOLE_Y = [1.4, -22.0]

# Spine joints, staggered per layer; all hidden behind the TRACKS plate / blue plaque
JOINTS = {0: (-8.2, -17.0), 1: (-9.5, -18.4), 2: (-8.85, -17.7)}

FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
if not os.path.exists(FONT):
    FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

COLORS = {
    "grey": "#B9BEC2", "white": "#F4F4F0", "black": "#1A1A1A", "blue": "#1C4DA1",
    "red": "#C8102E", "darkgrey": "#3a3a3a",
}
CUT, SCORE = "#FF0000", "#0000FF"


# ================================================================== helpers
def circle(r, x=0.0, y=0.0, n=180):
    return Point(x, y).buffer(r, quad_segs=max(8, n // 4))


def rrect(w, h, r=0.0, cx=0.0, cy=0.0):
    b = rect(cx - w / 2 + r, cy - h / 2 + r, cx + w / 2 - r, cy + h / 2 - r)
    return b.buffer(r, quad_segs=16) if r > 0 else b


def ring(od, id_, x=0.0, y=0.0):
    return circle(od / 2, x, y).difference(circle(id_ / 2, x, y))


def slot(x0, y0, x1, y1, w):
    return LineString([(x0, y0), (x1, y1)]).buffer(w / 2, quad_segs=16)


def polys(g):
    if g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    return [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon)]


# ------------------------------------------------------------------ text
class FlatPen(BasePen):
    def __init__(self, gs):
        super().__init__(gs)
        self.contours, self.cur = [], []

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, 9):
            t = i / 8
            self.cur.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, 11):
            t = i / 10
            a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
            self.cur.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                             a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))

    def _closePath(self):
        if len(self.cur) > 2:
            self.contours.append(self.cur)
        self.cur = []

    _endPath = _closePath


_FONT = TTFont(FONT)
_GS = _FONT.getGlyphSet()
_CMAP = _FONT.getBestCmap()
_CAP = _FONT["OS/2"].sCapHeight or 0.7 * _FONT["head"].unitsPerEm


def glyph(ch, cap):
    """Glyph outline scaled to cap height `cap`, baseline y=0, origin x=0."""
    pen = FlatPen(_GS)
    name = _CMAP[ord(ch)]
    _GS[name].draw(pen)
    g = Polygon()
    for c in pen.contours:
        g = g.symmetric_difference(Polygon(c).buffer(0))
    s = cap / _CAP
    return affinity.scale(g, s, s, origin=(0, 0)), _GS[name].width * s


def text_line(text, cap, gap=None):
    """A line of text. gap=None: font spacing; else equal ink gaps of `gap` between letters
    (spaces count as 0.45 cap). Returns (list of letter shapes, ink width), ink from x=0."""
    out, x = [], 0.0
    for ch in text:
        if ch == " ":
            x += 0.45 * cap if gap is not None else _GS[_CMAP[32]].width * cap / _CAP
            continue
        g, adv = glyph(ch, cap)
        if gap is None:
            out.append(affinity.translate(g, x, 0))
            x += adv
        else:
            b = g.bounds
            out.append(affinity.translate(g, x - b[0], 0))
            x += (b[2] - b[0]) + gap
    u = unary_union(out).bounds
    out = [affinity.translate(g, -u[0], 0) for g in out]
    return out, u[2] - u[0]


def fit_line(text, cap, width, gmin, gmax):
    """Equal-gap letters stretched to `width` (gap clamped); shrinks the cap if needed."""
    ink = sum((glyph(c, cap)[0].bounds[2] - glyph(c, cap)[0].bounds[0]) for c in text if c != " ")
    n = len(text.replace(" ", "")) - 1
    sp = 0.45 * cap * text.count(" ")
    gap = (width - ink - sp) / max(n, 1)
    if gap < gmin * cap:
        return fit_line(text, cap * 0.97, width, gmin, gmax)
    return text_line(text, cap, min(gap, gmax * cap)), cap


def place(letters, x, y):
    """Centre a list of letter shapes (their union's bbox) on (x, y)."""
    b = unary_union(letters).bounds
    dx, dy = x - (b[0] + b[2]) / 2, y - (b[1] + b[3]) / 2
    return [affinity.translate(g, dx, dy) for g in letters]


def centred_text(text, cap, x, y, width=None):
    letters, w = text_line(text, cap)
    if width and w > width:
        s = width / w
        letters = [affinity.scale(g, s, s, origin=(0, 0)) for g in letters]
    return place(letters, x, y)


# ================================================================ geometry
def blade(angle):
    return affinity.rotate(rrect(BLADE_L, BLADE_W, BLADE_R), angle, origin=(0, 0))


BLADE_RR = blade(-45)   # RAILROAD: upper-left to lower-right (behind)
BLADE_CX = blade(45)    # CROSSING: lower-left to upper-right (in front)
HALF_FREE = BLADE_W / 2  # the other blade covers |t| < BLADE_W/2 along a blade


def crossbuck_letters():
    margin, gmin, gmax = 0.30, 0.12, 0.45
    # CROSSING: the gap between the two S's sits on the centre, as on the real sign
    left, right = "CROS", "SING"
    end = BLADE_L / 2 - margin
    cap = CROSS_CAP
    while True:
        L, wl = text_line(left, cap, 0.2 * cap)
        R, wr = text_line(right, cap, 0.2 * cap)
        # solve one gap g so that the longer half reaches `end`
        inkl = sum(g.bounds[2] - g.bounds[0] for g in text_line(left, cap, 0)[0])
        inkr = sum(g.bounds[2] - g.bounds[0] for g in text_line(right, cap, 0)[0])
        g = min((end - inkl) / 3.5, (end - inkr) / 3.5)
        if g >= gmin * cap:
            break
        cap *= 0.97
    g = min(g, gmax * cap)
    L, wl = text_line(left, cap, g)
    R, wr = text_line(right, cap, g)
    dy = -cap / 2
    cross = [affinity.translate(s, -g / 2 - wl, dy) for s in L] + \
            [affinity.translate(s, g / 2, dy) for s in R]
    cross = [affinity.rotate(s, 45, origin=(0, 0)) for s in cross]
    # RAIL / ROAD on the free halves of the back blade
    avail = BLADE_L / 2 - HALF_FREE - 2 * margin - 0.15
    tc = (BLADE_L / 2 + HALF_FREE) / 2 + 0.05
    words = []
    (ra, _), c1 = fit_line("RAIL", cap, avail, gmin, gmax)
    (ro, _), c2 = fit_line("ROAD", cap, avail, gmin, gmax)
    for w, t in ((ra, -tc), (ro, tc)):
        w = place(w, t, 0)
        b = unary_union(w).bounds
        w = [affinity.translate(s, 0, -(b[1] + b[3]) / 2) for s in w]
        words += [affinity.rotate(s, -45, origin=(0, 0)) for s in w]
    return words, cross, cap


def tracks_plate():
    tab = rrect(TAB_W, TAB_H + 0.3, 0.1, 0, TRACKS_TOP - (TAB_H + 0.3) / 2)
    plate = rrect(PLATE_W, PLATE_H, 0.12, 0, TRACKS_TOP - TAB_H - PLATE_H / 2)
    return unary_union([tab, plate])


def tracks_letters():
    num = centred_text(TRACKS_NUMBER, 1.4, 0, TRACKS_TOP - TAB_H / 2 - 0.05)
    (tr, _), cap = fit_line("TRACKS", 1.15, PLATE_W - 2.4, 0.10, 0.22)
    tr = place(tr, 0, TRACKS_TOP - TAB_H - PLATE_H / 2)
    return num + tr


def box_centre():
    return 0.0, LAMP_Y


def box_outline():
    return rrect(BOX_W, BOX_H, BOX_R, *box_centre())


def box_cavity():
    cx, cy = box_centre()
    w, h = BOX_W - 2 * BOX_WALL, BOX_H - 2 * BOX_WALL
    cav = rect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0 = cx + sx * (BOX_W / 2 - BOX_CORNER)
            y0 = cy + sy * (BOX_H / 2 - BOX_CORNER)
            corner = rect(min(x0, x0 + sx * 1), min(y0, y0 + sy * 1), max(x0, x0 + sx * 1), max(y0, y0 + sy * 1))
            cav = cav.difference(corner)
    return cav


def magnet_holes():
    cx, cy = box_centre()
    d = BOX_CORNER / 2
    return unary_union([circle(MAGNET_D / 2, cx + sx * (BOX_W / 2 - d), cy + sy * (BOX_H / 2 - d), 48)
                        for sx in (-1, 1) for sy in (-1, 1)])


def plaque_centre():
    return 0.0, LAMP_Y - BOX_H / 2 - PLAQUE_GAP - PLAQUE_H / 2


def plaque():
    return rrect(PLAQUE_W, PLAQUE_H, PLAQUE_R, *plaque_centre())


def plaque_engrave():
    """White parts of the blue plaque (engrave through a paint mask, see README)."""
    cx, cy = plaque_centre()
    o = rrect(PLAQUE_W - 0.16, PLAQUE_H - 0.16, PLAQUE_R - 0.08, cx, cy)
    border = o.difference(o.buffer(-0.07))
    parts = [border, circle(0.07, cx, cy + PLAQUE_H / 2 - 0.25), circle(0.07, cx, cy - PLAQUE_H / 2 + 0.25)]
    cap, lh = 0.27, 0.43
    y0 = cy + 0.80
    for i, line in enumerate(PLAQUE_LINES):
        parts += centred_text(line, cap, cx, y0 - i * lh, PLAQUE_W - 0.55)
    # last line: "X-ING" in white, number in blue inside a white box
    y = y0 - len(PLAQUE_LINES) * lh - 0.02
    a = text_line(PLAQUE_XING[0], cap)[0]
    b = text_line(PLAQUE_XING[1], cap)[0]
    wa = unary_union(a).bounds[2]
    wb = unary_union(b).bounds[2]
    pad, gap = 0.06, 0.14
    total = wa + gap + wb + 2 * pad
    x0 = cx - total / 2
    parts += place(a, x0 + wa / 2, y)
    bx = x0 + wa + gap
    boxr = rect(bx, y - cap / 2 - pad, bx + wb + 2 * pad, y + cap / 2 + pad)
    parts.append(boxr.difference(unary_union(place(b, bx + pad + wb / 2, y))))
    return unary_union(parts)


def lid_label():
    cx, cy = box_centre()
    p = []
    p += centred_text("Railroad", 0.20, cx, cy + 0.42)
    p += centred_text("Crossing Signal", 0.20, cx, cy + 0.08)
    p += centred_text("MADE IN U.S.A.", 0.15, cx, cy - 0.30)
    return unary_union(p)


def pole_strip(width, y0, y1, finial=False):
    shape = rect(-width / 2, y1, width / 2, y0)
    if finial:   # cap band + cone on the top of the pole
        k = width / POLE_W
        band = rrect(1.45 * k, 0.55, 0.06, 0, y0 - 0.95)
        cone = Polygon([(-0.66 * k, y0 - 0.68), (0.66 * k, y0 - 0.68), (0.12 * k, y0 - 0.06), (0, y0), (-0.12 * k, y0 - 0.06)])
        shape = unary_union([rect(-width / 2, y1, width / 2, y0 - 0.9), band, cone])
    return shape


def spine_layer(z):
    """Spine (pole + arms + box back) for layer z in 0..2, split into 3 pieces."""
    j1, j2 = JOINTS[z]
    w = POLE_W if z < 2 else POLE_FRONT_W
    ah = ARM_H if z < 2 else ARM_FRONT_H
    upper = pole_strip(w, POLE_TOP, j1, finial=True)
    arms = rect(-ARM_END, LAMP_Y - ah / 2, ARM_END, LAMP_Y + ah / 2)
    for x in (-ARM_END, ARM_END):   # round arm ends
        arms = arms.union(circle(ah / 2, x, LAMP_Y))
    cross = unary_union([rect(-w / 2, j2, w / 2, j1), arms, box_outline()])
    lower = rect(-w / 2, POLE_BOTTOM, w / 2, j2)
    holes = []
    if z < 2:
        holes.append(circle(CENTRE_BOLT / 2))
    else:
        holes.append(circle(CENTRE_BOLT / 2))
    cav = box_cavity().bounds
    feed_x = (cav[2] - cav[0]) / 2 - 0.2
    if z == 0:   # keyhole
        for ky in KEYHOLE_Y:
            holes += [circle(KEYHOLE[0] / 2, 0, ky), slot(0, ky, 0, ky + KEYHOLE[2], KEYHOLE[1])]
    if z == 1:   # screw-head relief + wire channels
        for ky in KEYHOLE_Y:
            holes.append(slot(0, ky - 0.05, 0, ky + KEYHOLE[2] + 0.12, KEYHOLE[0] + 0.08))
        for s in (-1, 1):
            holes.append(slot(s * feed_x, LAMP_Y, s * LAMP_X, LAMP_Y, WIRE_HOLE))
    if z == 2:   # wire feed-throughs into the box and behind each lamp
        for s in (-1, 1):
            holes += [circle(WIRE_HOLE / 2, s * feed_x, LAMP_Y), circle(WIRE_HOLE / 2, s * LAMP_X, LAMP_Y)]
    h = unary_union(holes)
    return {"upper": upper.difference(h), "cross": cross.difference(h), "lower": lower.difference(h)}


def hood(x, y):
    a0, a1 = 90 - HOOD_SPAN / 2, 90 + HOOD_SPAN / 2
    pts = [(x, y)] + [(x + 3 * math.cos(math.radians(a)), y + 3 * math.sin(math.radians(a)))
                      for a in [a0 + (a1 - a0) * i / 60 for i in range(61)]]
    h = ring(HOOD_OD, HOOD_ID, x, y).intersection(Polygon(pts))
    return h.buffer(0.04).buffer(-0.04)   # soften the ends


def lens_pattern(x, y):
    """Diamond 'reflector' facets, engraved on the back of the lens."""
    lines = []
    for ang in (60, -60, 0):
        for k in range(-14, 15):
            c = k * 0.20
            dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            nx, ny = -dy, dx
            lines.append(slot(x + nx * c - dx * 2, y + ny * c - dy * 2, x + nx * c + dx * 2, y + ny * c + dy * 2, 0.022))
    return unary_union(lines).intersection(circle(LENS_D / 2 - 0.12, x, y))


# ============================================================ part catalogue
def build():
    """Returns the list of parts: dict(name, z, color, geom(in place), qty_note, ...)."""
    parts = []

    def add(name, z, color, geom, material="1/8in MDF", engrave=None, score=None, note="", file=None):
        parts.append(dict(name=name, z=z, color=color, geom=geom, material=material,
                          engrave=engrave, score=score, note=note, file=file or name))

    for z, lbl in ((0, "back"), (1, "mid"), (2, "front")):
        for k, g in spine_layer(z).items():
            add(f"spine_{z + 1}_{lbl}_{k}", z, "grey", g)

    add("blade_railroad", 3, "white", BLADE_RR.difference(circle(CENTRE_BOLT / 2)))
    add("blade_crossing", 4, "white", BLADE_CX.difference(circle(CENTRE_BOLT / 2)))
    rr, cx, cap = crossbuck_letters()
    add("letters_railroad", 4, "black", unary_union(rr), file="letters_railroad")
    add("letters_crossing", 5, "black", unary_union(cx), file="letters_crossing")
    tp = tracks_plate()
    tc = (0, TRACKS_TOP - 0.35)
    bolts = unary_union([circle(0.08, 0, TRACKS_TOP - 0.3), circle(0.08, 0, TRACKS_TOP - TAB_H - PLATE_H + 0.25)])
    add("tracks_plate", 3, "white", tp, score=bolts.boundary)
    add("letters_tracks", 4, "black", unary_union(tracks_letters()))
    add("plaque", 3, "blue", plaque(), engrave=plaque_engrave())

    # lamps (one entry per lamp so the preview is complete; files merge the pair)
    for s, side in ((-1, "L"), (1, "R")):
        x, y = s * LAMP_X, LAMP_Y
        add(f"lamp_disc_{side}", 3, "black", circle(DISC_D / 2, x, y).difference(circle(LED_FLANGE_HOLE / 2, x, y)), file="lamp_disc")
        add(f"lamp_housing_back_{side}", 4, "black", circle(HOUSING_OD / 2, x, y).difference(circle(LED_HOLE / 2, x, y)), file="lamp_housing_back")
        for i in range(CAVITY_LAYERS):
            add(f"lamp_cavity_ring_{side}{i}", 5 + i, "black", ring(HOUSING_OD, CAVITY_ID, x, y), file="lamp_cavity_ring")
        zl = 5 + CAVITY_LAYERS
        add(f"lamp_lens_pocket_{side}", zl, "black", ring(HOUSING_OD, LENS_POCKET, x, y), file="lamp_lens_pocket")
        add(f"lens_{side}", zl, "red", circle(LENS_D / 2, x, y), material="1/8in red acrylic",
            engrave=lens_pattern(x, y), file="lens")
        add(f"lamp_bezel_{side}", zl + 1, "black", ring(HOUSING_OD, CAVITY_ID, x, y), file="lamp_bezel")
        for i in range(HOOD_LAYERS):
            add(f"lamp_hood_{side}{i}", zl + 2 + i, "black", hood(x, y), file="lamp_hood")

    # junction box / battery compartment
    out, cav = box_outline(), box_cavity()
    frame = out.difference(cav)
    bx, bw = BUTTON_SLOT
    cyb = box_centre()[1] - BOX_H / 2
    bslot = rect(bx - bw / 2, cyb - 0.1, bx + bw / 2, cyb + BOX_WALL + 0.05)
    nail = rrect(0.8, 0.24, 0.08, 0, cyb)  # fingernail notch under the lid
    for i in range(6):
        g, f = frame, "box_frame"
        if i in (1, 2, 3):
            g, f = frame.difference(bslot), "box_frame_button"
        if i == 5:
            g, f = frame.difference(magnet_holes()).difference(nail), "box_frame_magnets"
        add(f"{f}_{i}", 3 + i, "grey", g, file=f)
    add("box_lid_1_magnets", 9, "grey", out.difference(magnet_holes()))
    add("box_lid_2_cover", 10, "grey", out)
    cx_, cy_ = box_centre()
    add("box_lid_3_label", 11, "grey", rrect(BOX_W - 0.6, BOX_H - 0.6, 0.15, cx_, cy_), engrave=lid_label())
    return parts


# ================================================================== output
def path_d(g, dx=0.0, dy=0.0, prec=4):
    out = []
    for p in polys(g):
        for ring_ in [p.exterior] + list(p.interiors):
            c = list(ring_.coords)[:-1]
            out.append("M" + " L".join(f"{x + dx:.{prec}f} {-y + dy:.{prec}f}" for x, y in c) + " Z")
    return " ".join(out)


def line_d(g, dx=0.0, dy=0.0):
    out = []
    for ls in getattr(g, "geoms", [g]):
        if ls.is_empty:
            continue
        c = list(ls.coords)
        out.append("M" + " L".join(f"{x + dx:.4f} {-y + dy:.4f}" for x, y in c))
    return " ".join(out)


def svg_doc(w, h, body):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}in" height="{h:.3f}in" '
            f'viewBox="0 0 {w:.4f} {h:.4f}">\n{body}\n</svg>\n')


def cut_path(g, dx, dy):
    return f'<path d="{path_d(g, dx, dy)}" fill="none" stroke="{CUT}" stroke-width="0.001"/>'


def engrave_path(g, dx, dy):
    return f'<path d="{path_d(g, dx, dy)}" fill="#000000" fill-rule="evenodd" stroke="none"/>'


def score_path(g, dx, dy):
    return f'<path d="{line_d(g, dx, dy)}" fill="none" stroke="{SCORE}" stroke-width="0.001"/>'


def write_sheet(fname, items, margin=0.25, gap=0.2, max_w=19.0):
    """items: list of (cut geom, engrave geom|None, score geom|None). Shelf-packs copies."""
    x, y, row_h, W = margin, margin, 0.0, 0.0
    body = []
    for cut, eng, sc in items:
        b = cut.bounds
        w, h = b[2] - b[0], b[3] - b[1]
        if x > margin and x + w > max_w - margin:
            x, y, row_h = margin, y + row_h + gap, 0.0
        dx, dy = x - b[0], y + b[3]
        if eng is not None and not eng.is_empty:
            body.append(engrave_path(eng, dx, dy))
        if sc is not None and not sc.is_empty:
            body.append(score_path(sc, dx, dy))
        body.append(cut_path(cut, dx, dy))
        x += w + gap
        row_h = max(row_h, h)
        W = max(W, x - gap + margin)
    H = y + row_h + margin
    with open(os.path.join(OUT, fname), "w") as f:
        f.write(svg_doc(W, H, "\n".join(body)))
    return W, H


def nest_letters(geom):
    """Split a letter union into single letters (piece + its counters), sorted for packing."""
    return [(p, None, None) for p in sorted(polys(geom), key=lambda p: -(p.bounds[3] - p.bounds[1]))]


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PREVIEW, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".svg"):
            os.remove(os.path.join(OUT, f))
    parts = build()

    # sanity: nothing on the same layer may overlap
    byz = {}
    for p in parts:
        for q in byz.get(p["z"], []):
            a = p["geom"].intersection(q["geom"]).area
            if a > 1e-4:
                raise SystemExit(f"overlap on layer {p['z']}: {p['name']} / {q['name']} ({a:.3f} sq in)")
        byz.setdefault(p["z"], []).append(p)

    # ---- cut files: one file per part type, all copies laid out
    files = {}
    for p in parts:
        files.setdefault(p["file"], []).append(p)
    rotate_upright = {"blade_railroad": 45, "blade_crossing": -45}
    summary = []
    for fname, ps in files.items():
        items = []
        for p in ps:
            g, e, s = p["geom"], p["engrave"], p["score"]
            ang = rotate_upright.get(fname.replace("letters_", "blade_"), 0)
            if fname.startswith("letters_"):
                items += nest_letters(affinity.rotate(g, ang, origin=(0, 0)))
                continue
            if ang:
                g = affinity.rotate(g, ang, origin=(0, 0))
            if fname == "lens":   # engrave on the back face: mirror the facets
                e = affinity.scale(e, -1, 1, origin=g.centroid)
            items.append((g, e, s))
        W, H = write_sheet(fname + ".svg", items)
        zs = sorted({p["z"] + 1 for p in ps})
        summary.append(dict(file=fname + ".svg", qty=len(ps) if not fname.startswith("letters_") else len(items),
                            layers=zs, color=ps[0]["color"], material=ps[0]["material"], w=round(W, 2), h=round(H, 2)))

    # ---- letter placement jigs (cut from card): blank outline with the letters' holes
    for fname, outline, ang in (("letters_railroad", BLADE_RR, 45), ("letters_crossing", BLADE_CX, -45),
                                ("letters_tracks", tracks_plate(), 0)):
        letters = files[fname][0]["geom"]
        jig = outline.difference(letters.buffer(0.01))
        jig = affinity.rotate(jig, ang, origin=(0, 0))
        b = jig.bounds
        with open(os.path.join(OUT, f"jig_{fname}.svg"), "w") as f:
            f.write(svg_doc(b[2] - b[0] + 0.5, b[3] - b[1] + 0.5, cut_path(jig, 0.25 - b[0], 0.25 + b[3])))

    # ---- full-size assembly template, preview data, flat preview
    allg = unary_union([p["geom"] for p in parts])
    B = allg.bounds
    pad = 0.5
    W, H = B[2] - B[0] + 2 * pad, B[3] - B[1] + 2 * pad
    dx, dy = pad - B[0], pad + B[3]
    tcol = ["#888", "#888", "#666", "#e4572e", "#2e86ab", "#3bb273", "#a23b72", "#f18f01", "#6c5ce7", "#00a8a8"]
    body = [f'<path d="{path_d(p["geom"], dx, dy)}" fill="none" stroke="{tcol[min(p["z"], 9)]}" stroke-width="0.02"/>'
            for p in sorted(parts, key=lambda p: p["z"]) if p["z"] <= 5]
    body.append(f'<path d="M{dx - 0.5} {dy} H{dx + 0.5} M{dx} {dy - 0.5} V{dy + 0.5}" stroke="#000" stroke-width="0.02"/>')
    with open(os.path.join(PREVIEW, "assembly_template.svg"), "w") as f:
        f.write(svg_doc(W, H, "\n".join(body)))

    layers = []
    for p in sorted(parts, key=lambda p: p["z"]):
        L = dict(name=p["name"], z=p["z"], t=T, color=COLORS[p["color"]], d=path_d(p["geom"], dx, dy, 3))
        if p["engrave"] is not None:
            L["engrave"] = path_d(p["engrave"], dx, dy, 3)
            L["engrave_color"] = {"blue": "#F4F4F0", "grey": "#8d8f8f", "red": "#8d0a1e"}[p["color"]]
        if p["score"] is not None:
            L["score"] = line_d(p["score"], dx, dy)
        layers.append(L)
    lamps = [dict(x=s * LAMP_X + dx, y=-LAMP_Y + dy, r=LENS_D / 2) for s in (-1, 1)]
    with open(os.path.join(PREVIEW, "layers.json"), "w") as f:
        json.dump(dict(w=W, h=H, layers=layers, lamps=lamps), f)
    with open(os.path.join(OUT, "cut_list.json"), "w") as f:
        json.dump(summary, f, indent=1)

    flat = []
    for L in layers:
        flat.append(f'<path d="{L["d"]}" fill="{L["color"]}" fill-rule="evenodd" stroke="#0004" stroke-width="0.01"/>')
        if "engrave" in L:
            flat.append(f'<path d="{L["engrave"]}" fill="{L["engrave_color"]}" fill-rule="evenodd"/>')
    with open(os.path.join(PREVIEW, "preview_flat.svg"), "w") as f:
        f.write(svg_doc(W, H, "\n".join(flat)))

    print(f"overall size: {B[2] - B[0]:.2f} in wide x {B[3] - B[1]:.2f} in tall; "
          f"depth {(max(p['z'] for p in parts) + 1) * T:.3f} in ({max(p['z'] for p in parts) + 1} layers of {T} in)")
    print(f"crossbuck letter cap height: {crossbuck_letters()[2]:.2f} in")
    for s in sorted(summary, key=lambda s: s["layers"][0]):
        print(f"  {s['file']:32s} x{s['qty']:<3d} layer {','.join(map(str, s['layers'])):10s} "
              f"{s['color']:6s} {s['material']:18s} sheet {s['w']:.1f} x {s['h']:.1f} in")


if __name__ == "__main__":
    main()
