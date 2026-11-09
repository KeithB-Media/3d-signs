#!/usr/bin/env python3
"""Generate laser-cut SVG layers for a stacked 1/8" MDF sign of the front of a
GE Genesis P42DC locomotive in Amtrak Phase V, with working LED headlights,
ditch lights and red rear (marker) lights.

Units are inches. Design origin is the bottom centre of the sign (top of rail),
+x to the right, +y up; the SVG output flips y. Run:
    python3 generate.py          (needs: pip install shapely numpy fonttools)

Every layer is cut from 1/8" MDF. Layers 1-5 are the hidden "core": they give
the sign its thickness and hold the battery pocket, the wire channels and the
hanging keyholes. Layers 6-10 are the visible relief.

The front layout follows a head-on photo of a Phase V P42: number board above
the windshield, dark plate and Travelmark under it, twin round headlights with a
red light either side, blue/silver split just under the headlights, ditch lights
and dark lamp boxes on the silver, anticlimber, pilot with jumpers and hoses,
and a big stepped plow.
"""
import json
import os
import sys

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "svg")

T = 0.125                     # MDF thickness
HALF_W = 8.0                  # sign is 16" wide ...
TOP = 23.0                    # ... and 23" tall incl. roof horns (about 1:7.5 scale)
ROOF = 22.4                   # top of the carbody
MARGIN = 0.25                 # border around the drawing in the SVG files

ROAD_NUMBER = "82"            # cut in white for the number board ("" for a blank board)
WORDMARK = "AMTRAK"
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

# ---- Phase V colours (Amtrak livery guide): edit to repaint the previews.
COLORS = {
    "core": "#1d1d1f",        # hidden layers: paint the edges black
    "glass": "#26313b",       # top of layer 5, seen through the windshield
    "blue": "#1f4e79",        # Amtrak Blue: roof and nose "wave"
    "silver": "#cdd1d4",      # Platinum Mist
    "plow": "#26292d",        # plow: near-black so it stands out from the silver body
    "under": "#4a4f52",       # Anthracite Gray: pilot face, steps, underbody
    "red": "#d9442f",         # Amtrak Red
    "black": "#161616",
    "white": "#f4f4f2",
    "gray": "#7d838a",        # coupler, horns, glad hands
    "plug": "#d8d5c8",        # jumper plug heads (light grey)
    "lens": "#5d7690",        # lens of the lower lamp boxes
    "chrome": "#e6e8ea",
}

# ---- lights (LED positions)
HEADLIGHTS = [(-0.55, 12.9), (0.55, 12.9)]
REDLIGHTS = [(-4.3, 12.9), (4.3, 12.9)]
DITCHLIGHTS = [(-5.6, 10.1), (5.6, 10.1)]
LAMP_BOXES = [(-5.6, 8.4), (5.6, 8.4)]       # dark boxes under the ditch lights (not lit)

WIN_BOTTOM, WIN_TOP = 17.0, 19.65             # windshield: wide and short, as on the P42

# ---- electronics
LED_HOLE = 0.25               # 5 mm LEDs push in from the front (loose fit, dab of glue)
LED_RING_ID = 0.36            # chrome lens ring: the LED flange sits inside it
CHANNEL_W = 0.32              # wire channel width (in layers 4 and 5)
POCKET = (2.50, 1.95)         # battery holder pocket, through layers 1-5 (0.625" deep)
POCKET_C = (0.0, 8.9)         # pocket centre: behind the nose
KEYHOLES = [(-4.6, 19.2), (4.6, 19.2)]


def mirror(pts):
    """Close a half outline (x >= 0, listed bottom-to-top) into a symmetric polygon."""
    return Polygon(pts + [(-x, y) for x, y in reversed(pts)])


def both(geom):
    return unary_union([geom, affinity.scale(geom, -1, 1, origin=(0, 0))])


def rounded(geom, r):
    return geom.buffer(-r, join_style=1).buffer(r, join_style=1)


def stroke(pts, w, cap=1):
    return LineString(pts).buffer(w / 2, cap_style=cap, join_style=1)


def circles(pts, r):
    return unary_union([Point(p).buffer(r) for p in pts])


def rings(pts, r_out, r_in):
    return unary_union([Point(p).buffer(r_out).difference(Point(p).buffer(r_in)) for p in pts])


def bezier(p0, p1, p2, p3, n=40):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                    a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


# ------------------------------------------------------------------ text
class _FlatPen(BasePen):
    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.rings, self.cur = [], []

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        self.cur += bezier(self.cur[-1], p1, p2, p3, 12)[1:]

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, 9):
            t = i / 8
            self.cur.append(((1 - t) ** 2 * p0[0] + 2 * t * (1 - t) * p1[0] + t * t * p2[0],
                             (1 - t) ** 2 * p0[1] + 2 * t * (1 - t) * p1[1] + t * t * p2[1]))

    def _closePath(self):
        if len(self.cur) > 2:
            self.rings.append(self.cur)
        self.cur = []

    _endPath = _closePath


def text(s, cap_height, cx, cy, tracking=0.06):
    """Text as polygons, centred on (cx, cy). Letters with holes keep them."""
    font = TTFont(FONT)
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    cap = font["OS/2"].sCapHeight or 1409
    k = cap_height / cap
    x, letters = 0.0, []
    for ch in s:
        name = cmap[ord(ch)]
        pen = _FlatPen(gs)
        gs[name].draw(pen)
        g = Polygon()
        for ring in pen.rings:
            g = g.symmetric_difference(Polygon(ring).buffer(0))
        letters.append(affinity.translate(affinity.scale(g, k, k, origin=(0, 0)), x, 0))
        x += gs[name].width * k + tracking
    t = unary_union(letters)
    minx, miny, maxx, maxy = t.bounds
    return affinity.translate(t, cx - (minx + maxx) / 2, cy - cap_height / 2)


def travelmark(cx, cy, cap=0.5):
    """Phase V Travelmark: the AMTRAK wordmark over three sweeping stripes that
    fan out to the right. Stripes are at least 0.1" wide so they can be cut.
    Approximate - swap in the official artwork if you have it."""
    word = text(WORDMARK, cap, 0.0, 0.0, tracking=0.06)
    minx, _, maxx, _ = word.bounds
    w = maxx - minx
    bands = []
    for k in range(3):
        x0 = minx + 0.12 * w + 0.07 * w * k                      # left tips step in
        y_top = -cap / 2 - 0.3 - 0.2 * k
        pts = bezier((x0, y_top - 0.28), (x0 + 0.3 * w, y_top - 0.09),
                     (maxx - 0.35 * w, y_top + 0.02), (maxx + 0.08 * w, y_top + 0.1), 50)
        n = len(pts) - 1
        half = [0.05 + 0.04 * (i / n) for i in range(n + 1)]    # widen to the right
        upper = [(x, y + h) for (x, y), h in zip(pts, half)]
        lower = [(x, y - h) for (x, y), h in zip(pts, half)]
        bands.append(Polygon(upper + lower[::-1]))
    mark = unary_union(bands)
    bx0, by0, bx1, by1 = unary_union([word, mark]).bounds
    dx, dy = cx - (bx0 + bx1) / 2, cy - (by0 + by1) / 2
    return affinity.translate(mark, dx, dy), affinity.translate(word, dx, dy)


# ------------------------------------------------------------------ carbody
def body():
    """Carbody from the sill (y=3.4) to the roof: straight lower sides, upper
    sides leaning in (Genesis 'tumblehome'), rounded roof corners."""
    half = [(0, 3.4), (8.0, 3.4), (8.0, 14.4), (6.9, 21.2), (6.6, 21.95),
            (6.1, 22.32), (5.45, ROOF), (0, ROOF)]
    return rounded(mirror(half), 0.05)


def wave():
    """Everything above this line is Amtrak Blue. It forms a shallow V across the
    front, lowest just under the headlights, and sweeps up at the cab corners."""
    pts = []
    for i in range(-90, 91):
        x = i / 10
        y = 11.8 + 0.75 * abs(x) / 7 + 2.2 * max(0.0, abs(x) - 6.7)
        pts.append((x, y))
    return Polygon(pts + [(9, TOP + 1), (-9, TOP + 1)])


def roof_gear():
    """Horn cluster and radio antenna, seen over the roof line."""
    horn = unary_union([box(2.3, ROOF - 0.05, 4.3, ROOF + 0.12),
                        box(3.2, ROOF + 0.05, 3.4, ROOF + 0.32),
                        rounded(box(2.35, ROOF + 0.28, 4.25, ROOF + 0.52), 0.08)] +
                       [Polygon([(x - 0.12, ROOF + 0.5), (x + 0.12, ROOF + 0.5),
                                 (x + 0.22, TOP), (x - 0.22, TOP)]) for x in (2.65, 3.3, 3.95)])
    antenna = unary_union([box(-3.9, ROOF - 0.05, -3.1, ROOF + 0.14),
                           Polygon([(-3.62, ROOF + 0.1), (-3.38, ROOF + 0.1), (-3.44, ROOF + 0.55),
                                    (-3.56, ROOF + 0.55)])])
    return horn.difference(body()), antenna.difference(body())


def windows():
    """Windshield openings (each pane leans in with the cab side)."""
    lean = 0.157 * (WIN_TOP - WIN_BOTTOM)             # follows the cab side
    pane = Polygon([(0.38, WIN_BOTTOM), (5.85, WIN_BOTTOM), (5.85 - lean, WIN_TOP), (0.38, WIN_TOP)])
    return both(rounded(pane, 0.3))


def gaskets():
    return windows().buffer(0.24, join_style=1).difference(windows())


def wipers():
    """Parked wipers, joined to the gasket at both ends so they're strong."""
    b = WIN_BOTTOM
    arm = stroke([(4.8, b - 0.12), (0.26, b + 1.0)], 0.18, cap=2)
    pivot = Point(4.65, b - 0.15).buffer(0.16)
    return both(unary_union([arm, pivot]))


def number_board():
    """Number board above the windshield, between the panes."""
    return rounded(box(-0.95, 20.15, 0.95, 21.05), 0.12)


def nose_plate():
    """Dark plate on the nose just under the windshield."""
    return rounded(box(-1.0, 15.75, 1.0, 16.45), 0.1)


def nose():
    """Forward-sloping nose under the windshield, raised one layer over the
    cab 'cheeks'. It stops at the anticlimber."""
    half = [(0, 7.0), (7.5, 7.0), (6.35, 16.6), (0, 16.6)]
    return rounded(mirror(half), 0.08)


def pilot_face():
    """Anthracite pilot face behind the coupler, jumpers and hoses."""
    return box(-6.6, 3.4, 6.6, 7.0).difference(PLOW_TOP).difference(COUPLER_POCKET)


def grab_irons_low():
    return both(box(7.3, 3.95, 7.5, 6.9))


def grab_irons_nose():
    return both(stroke([(6.1, 13.6), (5.92, 14.9)], 0.18))


# ------------------------------------------------------------------ plow (4 steps)
PLOW_TOP = mirror([(0, -1), (9, -1), (9, 2.95), (6.25, 3.05), (1.15, 4.2), (0, 4.2)])
COUPLER_POCKET = box(-1.15, 1.55, 1.15, 4.2)    # opening in the plow the coupler sits in


def plow():
    """Step 1 (layer 6): the plow base."""
    half = [(0, 0.0), (4.3, 0.0), (6.45, 1.85), (6.45, 3.5), (0, 3.5)]
    return mirror(half)


def plow_wings():
    """Step 2 (layer 7): one plate with two wings. The top edge slopes down to the
    outer corners, and the middle is cut away for the coupler pocket."""
    outline = mirror([(0, 0.0), (4.3, 0.0), (6.45, 1.85), (6.45, 4.3), (0, 4.3)])
    return outline.buffer(-0.16, join_style=2).intersection(PLOW_TOP).difference(COUPLER_POCKET)


def plow_plates():
    """Step 3 (layer 8): a lower centre plate and a raised plate on each wing."""
    centre = mirror([(0, 0.24), (3.75, 0.24), (2.75, 1.32), (0, 1.32)])
    wing = plow_wings().buffer(-0.24, join_style=2).intersection(
        mirror([(0, 0.95), (9, 0.95), (9, 9), (0, 9)])).difference(box(-2.35, -1, 2.35, 9))
    return unary_union([rounded(centre, 0.06), wing])


def plow_brackets():
    """Step 4 (layer 9): bolted brackets on the wing plates and a rib on the centre plate."""
    brk = [rounded(box(x - 0.22, 1.55, x + 0.22, 2.25), 0.05) for x in (3.0, 4.6)]
    rib = rounded(box(-1.9, 0.62, 1.9, 0.86), 0.06)
    return unary_union([both(unary_union(brk)), rib])


STEP_WELL = box(6.62, 0.9, 7.9, 3.4)          # corner step well, under the sill


def step_wells():
    """Back of each corner step well (layer 6): painted black, it reads as the
    dark recess the steps are tucked into."""
    return both(STEP_WELL)


def step_treads():
    """Steps inside the well (layer 7): two side stringers and three treads, one piece a side."""
    x0, y0, x1, y1 = STEP_WELL.bounds
    parts = [box(x0, y0, x0 + 0.16, y1), box(x1 - 0.16, y0, x1, y1)]
    parts += [box(x0, y, x1, y + 0.2) for y in (y0, 1.85, 2.75)]
    return both(unary_union(parts))


def sill_stripe():
    """Amtrak Red sill stripe, seen at the front corners either side of the pilot."""
    return both(box(6.62, 3.45, 8.0, 3.72))


# ------------------------------------------------------------------ lights
def headlight_recess():
    """Pocket the twin headlights sit in: cut out of the nose (layer 7), so
    the lamps sit one layer below the nose surface."""
    (x0, y), (x1, _) = HEADLIGHTS
    return rounded(box(x0 - 0.62, y - 0.55, x1 + 0.62, y + 0.55), 0.3)


def light_housings():
    return unary_union([circles(REDLIGHTS, 0.4), circles(DITCHLIGHTS, 0.5)])


def red_rings():
    """Red lights: a red ring round the LED (paint it red, or use a red LED with a chrome ring)."""
    return rings(REDLIGHTS, 0.31, LED_RING_ID / 2)


def lamp_boxes():
    return unary_union([rounded(box(x - 0.6, y - 0.5, x + 0.6, y + 0.5), 0.08) for x, y in LAMP_BOXES])


def lamp_box_lenses():
    return unary_union([rounded(box(x - 0.42, y - 0.32, x + 0.42, y + 0.32), 0.06) for x, y in LAMP_BOXES])


# ------------------------------------------------------------------ front end
def anticlimber():
    a = box(-6.4, 6.35, 6.4, 6.95)
    return a.difference(box(-0.5, 6.35, 0.5, 6.42))      # notch over the coupler shank


def coupler_shank():
    return box(-0.42, 3.62, 0.42, 6.32)


def coupler_head():
    """E-type coupler head with the knuckle gap and lock-lift hole. It sits in
    the coupler pocket (layer 7), on the plow base."""
    head = rounded(Polygon([(-1.0, 2.3), (0.55, 2.3), (1.0, 2.6), (1.0, 3.5), (-1.0, 3.5)]), 0.12)
    return head.difference(box(0.05, 2.3, 0.22, 3.0)).difference(Point(-0.55, 3.05).buffer(0.1))


MU_X = (2.2, 2.75)           # MU receptacles each side of the coupler
HEP_X = (3.8, 4.8)            # HEP receptacle and its dummy (stowage) socket
HOSE_X = (1.35, 1.65)         # air hoses: brake pipe and main reservoir
REC_Y = 4.75                  # receptacle centre height


def receptacles():
    """Receptacle boxes on the pilot face (layer 8)."""
    mu = [rounded(box(x - 0.27, REC_Y - 0.33, x + 0.27, REC_Y + 0.33), 0.06) for x in MU_X]
    hep = [rounded(box(x - 0.36, REC_Y - 0.4, x + 0.36, REC_Y + 0.4), 0.08) for x in HEP_X]
    return both(unary_union(mu + hep))


def socket_faces():
    """Round socket face with a centre hole on the outer (empty) MU receptacles."""
    return both(rings([(MU_X[1], REC_Y)], 0.2, 0.07))


def air_hoses():
    """Hoses hang from the anticlimber, curve out and end at glad hands."""
    return both(unary_union([stroke(bezier((x, 6.35), (x, 4.6), (x + 0.25, 3.2), (x + 0.2, 1.62), 30), 0.17)
                             for x in HOSE_X]))


def glad_hands():
    hands = []
    for x in HOSE_X:
        cx, cy = x + 0.2, 1.75
        hands.append(unary_union([rounded(box(cx - 0.13, cy - 0.28, cx + 0.13, cy + 0.12), 0.05),
                                  box(cx - 0.13, cy - 0.28, cx + 0.32, cy - 0.12)]))
    return both(unary_union(hands))


def mu_jumper():
    """MU jumper cable draped under the coupler shank, plug heads on the inner receptacles."""
    x = MU_X[0]
    cable = stroke(bezier((-x, REC_Y - 0.2), (-x + 0.3, 3.65), (x - 0.3, 3.65), (x, REC_Y - 0.2), 60), 0.22)
    return cable.difference(plugs_mu())


def plugs_mu():
    x = MU_X[0]
    return unary_union([rounded(box(s * x - 0.23, REC_Y - 0.28, s * x + 0.23, REC_Y + 0.22), 0.07)
                        for s in (-1, 1)])


def hep_jumpers():
    """HEP jumpers stowed in a loop between receptacle and dummy socket."""
    a, b = HEP_X
    loop = stroke(bezier((a, REC_Y - 0.25), (a + 0.05, 3.75), (b - 0.05, 3.75), (b, REC_Y - 0.25), 40), 0.24)
    return both(loop).difference(plugs_hep())


def plugs_hep():
    return both(unary_union([rounded(box(x - 0.28, REC_Y - 0.33, x + 0.28, REC_Y + 0.25), 0.08)
                             for x in HEP_X]))


def cut_lever():
    """Uncoupling lever across the left plow wing to the coupler, handle at the
    left. It rests on the wing plate and the air hoses (layer 8)."""
    bar = stroke([(-5.1, 2.4), (-1.3, 2.4), (-1.08, 2.7)], 0.16)
    handle = stroke([(-5.1, 2.4), (-5.3, 2.0), (-5.02, 1.9)], 0.15)
    return unary_union([bar, handle])


def cut_lever_brackets():
    return unary_union([rounded(box(-4.7, 3.05, -4.3, 3.5), 0.05),
                        rounded(box(-3.0, 3.05, -2.6, 3.5), 0.05)])


def silhouette():
    horn, antenna = roof_gear()
    return unary_union([body(), plow(), both(STEP_WELL), horn, antenna])


# ------------------------------------------------------------------ electronics
def all_leds():
    return HEADLIGHTS + REDLIGHTS + DITCHLIGHTS


def led_holes():
    return circles(all_leds(), LED_HOLE / 2)


def pocket():
    w, h = POCKET
    return rounded(box(POCKET_C[0] - w / 2, POCKET_C[1] - h / 2,
                       POCKET_C[0] + w / 2, POCKET_C[1] + h / 2), 0.06)


def channels():
    """Pocket -> straight up to the light bar (headlights + red lights), and
    pocket -> sideways to each ditch light."""
    cx, cy = POCKET_C
    y_bar = HEADLIGHTS[0][1]
    runs = [LineString([(cx, cy), (cx, y_bar)]),
            LineString([REDLIGHTS[0], REDLIGHTS[1]])]
    for x, y in DITCHLIGHTS:
        runs.append(LineString([(cx, y), (x, y)]))
    lines = unary_union([r.buffer(CHANNEL_W / 2, cap_style=1, join_style=1) for r in runs])
    return unary_union([lines, circles(all_leds(), 0.2)])


def keyholes():
    """Keyhole slot in the backer: the screw head goes in the big hole and the
    sign drops 0.5" so the shank sits at the top of the slot."""
    return unary_union([unary_union([Point(x, y).buffer(0.2), box(x - 0.09, y, x + 0.09, y + 0.5),
                                     Point(x, y + 0.5).buffer(0.09)]) for x, y in KEYHOLES])


def keyhole_reliefs():
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
    core = silhouette().difference(pocket())
    leds = led_holes()
    horn, antenna = roof_gear()
    blue = wave()
    cab = body().difference(windows()).difference(leds)
    nose_ = nose().difference(leds)
    mark, word = travelmark(0.0, 14.7, cap=0.56)
    digits = text(ROAD_NUMBER, 0.55, 0.0, 20.6, tracking=0.06) if ROAD_NUMBER else None

    layers = [
        # (stem, [(paint, geometry)], note)
        ("layer01_backer", [("core", core.difference(keyholes()))],
         "backer: battery pocket + 2 keyhole hangers"),
        ("layer02_core", [("core", core.difference(keyhole_reliefs()))], "core: room for the screw heads"),
        ("layer03_core", [("core", core.difference(keyhole_reliefs()))], "core: room for the screw heads"),
        ("layer04_core_wiring", [("core", core.difference(channels()))], "core: wire channels"),
        ("layer05_glass_wiring", [("glass", core.difference(channels()))],
         "core: wire channels; top shows through the windshield"),
        ("layer06_body", [("silver", cab.difference(blue).difference(COUPLER_POCKET)),
                          ("blue", cab.intersection(blue).difference(headlight_recess())),
                          ("black", cab.intersection(headlight_recess())),     # recess floor
                          ("plow", plow().difference(body()).difference(COUPLER_POCKET)),
                          ("black", COUPLER_POCKET.intersection(silhouette())),     # pocket floor
                          ("black", step_wells()), ("gray", horn), ("gray", antenna)],
         "carbody (blue wave + silver, windshield cut out), plow base, steps, horns, antenna"),
        ("layer07_nose", [("silver", nose_.difference(blue)),
                          ("blue", nose_.intersection(blue).difference(headlight_recess())),
                          ("chrome", rings(HEADLIGHTS, 0.38, LED_RING_ID / 2)),  # lamps in the recess
                          ("gray", coupler_head()),
                          ("under", pilot_face()),
                          ("black", gaskets().union(wipers())),
                          ("black", number_board()),
                          ("under", grab_irons_low()),
                          ("gray", step_treads()),
                          ("red", sill_stripe()),
                          ("plow", plow_wings())],
         "raised nose (blue + silver) with headlight recess, headlight rings, coupler head, "
         "pilot face, gaskets with wipers, number board, plow wings"),
        ("layer08_lights_logo", [("black", light_housings().difference(leds)),
                                 ("black", nose_plate()),
                                 ("white", mark), ("white", word)] +
                                ([("white", digits)] if digits else []) +
                                [("black", lamp_boxes()),
                                 ("black", anticlimber()),
                                 ("gray", coupler_shank()),
                                 ("black", receptacles()),
                                 ("black", air_hoses().difference(anticlimber())),
                                 ("black", grab_irons_nose()),
                                 ("plow", plow_plates())],
         "light housings, nose plate, Travelmark, number, lamp boxes, anticlimber, coupler shank, "
         "receptacles, air hoses, lever brackets, grab irons, plow plates"),
        ("layer09_front_gear", [("chrome", rings(DITCHLIGHTS, 0.37, LED_RING_ID / 2)),
                                ("red", red_rings()),
                                ("lens", lamp_box_lenses()),
                                ("gray", socket_faces()),
                                ("black", mu_jumper()),
                                ("plug", plugs_mu()),
                                ("black", hep_jumpers().union(plugs_hep())),  # one piece: glues to the receptacles
                                ("plug", glad_hands()),
                                ("gray", cut_lever().difference(mu_jumper().buffer(0.04))),
                                ("plow", plow_brackets())],
         "ditch light rings, red light rings, lamp box lenses, socket faces, MU + HEP jumpers "
         "with plug heads, glad hands, uncoupling lever, plow brackets"),
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


def check(stem, pieces, below):
    """Warn about overlapping pieces, pieces with nothing under them, and slivers."""
    for i in range(len(pieces)):
        for j in range(i + 1, len(pieces)):
            a = pieces[i][1].intersection(pieces[j][1]).area
            if a > 1e-4:
                print(f"  WARNING: {stem}: pieces {i} and {j} overlap ({a:.4f} sq in)")
    for k, (c, g) in enumerate(pieces):
        if below is not None:
            parts = g.geoms if hasattr(g, "geoms") else [g]
            for p in parts:
                if p.intersection(below).area < 0.25 * p.area:
                    print(f"  WARNING: {stem}: piece {k} ({c}) has under 25% glue area below it")
                    break
        thin = g.difference(g.buffer(-0.045).buffer(0.045))
        if thin.area > 0.01:
            print(f"  note: {stem} ({c}) has {thin.area:.3f} sq in narrower than 0.09\"")


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):                       # clear out files from older versions
        if f.endswith(".svg") or f.endswith(".json"):
            os.remove(os.path.join(OUT, f))
    layers = build()
    data, rows, z, below = [], [], 0.0, None
    for i, (stem, pieces, note) in enumerate(layers, 1):
        check(stem, pieces, below)
        below = unary_union([g for _, g in pieces])
        cut = "\n".join(f'<path d="{path_d(g)}" fill="none" stroke="#FF0000" stroke-width="0.01"/>'
                        for _, g in pieces)
        with open(os.path.join(OUT, stem + ".svg"), "w") as f:
            f.write(svg_doc(cut, f"Layer {i} - {note}"))
        paints = sorted({c for c, _ in pieces}, key=list(COLORS).index)
        rows.append(f"| {i} | `svg/{stem}.svg` | {', '.join(paints)} | "
                    f"{sum(count(g) for _, g in pieces)} | {note} |")
        data.append({"stem": stem, "z": z, "t": T,
                     "pieces": [{"color": COLORS[c], "d": path_d(g)} for c, g in pieces]})
        z += T

    with open(os.path.join(OUT, "back_cover.svg"), "w") as f:
        f.write(svg_doc(f'<path d="{path_d(back_cover())}" fill="none" stroke="#FF0000" stroke-width="0.01"/>',
                        "Battery pocket cover - screws to the back"))

    body_ = "\n".join(f'<path d="{p["d"]}" fill="{p["color"]}" fill-rule="evenodd"/>'
                      for L in data for p in L["pieces"])
    with open(os.path.join(OUT, "preview_flat.svg"), "w") as f:
        f.write(svg_doc(body_, "Flat colour preview"))

    tcols = ["#000", "#888", "#888", "#0a0", "#0a0", "#00c", "#c90", "#c00", "#808", "#088"]
    body_ = "\n".join(f'<path d="{" ".join(p["d"] for p in L["pieces"])}" fill="none" '
                      f'stroke="{tcols[k]}" stroke-width="0.015"/>' for k, L in enumerate(data))
    with open(os.path.join(OUT, "placement_template.svg"), "w") as f:
        f.write(svg_doc(body_, "Glue-up placement template (print 1:1)"))

    to_svg = lambda pts: [[x + HALF_W + MARGIN, TOP + MARGIN - y] for x, y in pts]
    meta = {"w": W_SVG, "h": H_SVG,
            "lights": to_svg(HEADLIGHTS + DITCHLIGHTS), "red_lights": to_svg(REDLIGHTS),
            "layers": data}
    with open(os.path.join(OUT, "layers.json"), "w") as f:
        json.dump(meta, f)
    print("\n".join(rows))
    print(f"total stack height: {z:.3f}\"  |  sheet size {W_SVG:.2f}\" x {H_SVG:.2f}\"")


if __name__ == "__main__":
    main()
