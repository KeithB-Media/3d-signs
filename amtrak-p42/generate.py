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
and connector boxes (blue + black covers) on the silver, a cut-out in the bottom of
the body over the coupler, and a tall plow with doors whose tips reach the body.
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
SILL = 6.3                    # bottom of the silver carbody (the plow tips reach up to it)
Y0 = 1.9                      # bottom edge of the plow = bottom of the sign

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
    "conn_blue": "#2f7fd0",   # outer connector cover in the boxes under the ditch lights
    "yellow": "#e3b53c",      # plug on the cable hanging from under each connector box
    "chrome": "#e6e8ea",
}

# ---- lights (LED positions)
HEADLIGHTS = [(-0.68, 12.9), (0.68, 12.9)]
REDLIGHTS = [(-4.3, 12.9), (4.3, 12.9)]
DITCHLIGHTS = [(-5.6, 10.1), (5.6, 10.1)]
CONN_BOXES = [(-5.6, 8.4), (5.6, 8.4)]       # connector recesses under the ditch lights

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
    """Carbody from the sill (y=SILL) to the roof: straight lower sides, upper
    sides leaning in (Genesis 'tumblehome'), rounded roof corners."""
    half = [(0, SILL), (8.0, SILL), (8.0, 14.4), (6.9, 21.2), (6.6, 21.95),
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


NUMBER_Y = 16.05


def number_board():
    """Number board on the nose, just under the windshield (layer 8); the
    digits sit on it (layer 9)."""
    return rounded(box(-1.15, NUMBER_Y - 0.45, 1.15, NUMBER_Y + 0.45), 0.1)


def nose():
    """Forward-sloping nose under the windshield, raised one layer over the
    cab 'cheeks'. It stops just above the bottom of the carbody."""
    half = [(0, 7.0), (7.5, 7.0), (6.35, 16.6), (0, 16.6)]
    return rounded(mirror(half), 0.08)


def grab_irons_nose():
    return both(stroke([(6.1, 13.6), (5.92, 14.9)], 0.18))


def sill_stripe():
    """Amtrak Red sill stripe, seen at the front corners either side of the plow."""
    return both(box(6.62, SILL + 0.05, 8.0, SILL + 0.32))


# ------------------------------------------------------------------ lights
def headlight_recess():
    """Pocket the twin headlights sit in: cut out of the nose (layer 7), so
    the lamps sit one layer below the nose surface."""
    (x0, y), (x1, _) = HEADLIGHTS
    return rounded(box(x0 - 0.72, y - 0.66, x1 + 0.72, y + 0.66), 0.4)


def light_housings():
    return unary_union([circles(REDLIGHTS, 0.4), circles(DITCHLIGHTS, 0.66)])


def red_rings():
    """Red lights: a red ring round the LED (paint it red, or use a red LED with a chrome ring)."""
    return rings(REDLIGHTS, 0.31, LED_RING_ID / 2)


def conn_recesses():
    """Recesses cut out of the nose (layer 7) with a black floor (layer 6): the
    connector box under each ditch light, and a small cable opening below it."""
    boxes = [rounded(box(x - 0.62, y - 0.45, x + 0.62, y + 0.45), 0.08) for x, y in CONN_BOXES]
    holes = [rounded(box(cx - 0.24, 6.9, cx + 0.24, 7.72), 0.06) for cx, _ in cable_tops()]   # open at the bottom
    return unary_union(boxes + holes)


def cable_tops():
    return [(x * 0.93, 7.46) for x, _ in CONN_BOXES]


def hanging_cables():
    """Yellow plug in each small opening (layer 7, on the black floor) with a black
    cable (layer 7) running down from it and disappearing behind the plow tip.
    Returns (cables, plugs)."""
    cables, plugs = [], []
    for cx, cy in cable_tops():
        s = 1 if cx > 0 else -1
        plugs.append(rounded(box(cx - 0.15, 7.24, cx + 0.15, 7.62), 0.06))
        pts = bezier((cx, 7.3), (cx, 6.8), (cx + s * 0.2, 6.5), (cx + s * 0.25, 5.6), 30)
        cables.append(stroke(pts, 0.18))
    plugs = unary_union(plugs)
    return unary_union(cables).difference(plugs).difference(plow()), plugs


def _conn_centres():
    """(outer, inner) connector centres: blue on the outside, black on the inside."""
    outer, inner = [], []
    for x, y in CONN_BOXES:
        s = 1 if x > 0 else -1
        outer.append((x + s * 0.29, y))
        inner.append((x - s * 0.29, y))
    return outer, inner


def conn_plates():
    """Square base plate of each covered connector (layer 7, flush with the nose).
    Returns (outer - blue, inner - black)."""
    sq = lambda pts: unary_union([rounded(box(x - 0.24, y - 0.24, x + 0.24, y + 0.24), 0.05) for x, y in pts])
    outer, inner = _conn_centres()
    return sq(outer), sq(inner)


def conn_caps():
    """Round cap on each plate (layer 8). Returns (outer - blue, inner - black)."""
    outer, inner = _conn_centres()
    return circles(outer, 0.17), circles(inner, 0.17)


# ------------------------------------------------------------------ pilot opening + coupler
B = Y0                                            # bottom of the plow (= bottom of the sign)
PILOT_OPENING = box(-3.0, SILL, 3.0, 6.95)        # cut-out in the bottom of the silver body over the coupler
NOTCH = box(-1.7, B + 1.7, 1.7, SILL)             # opening in the plow top the coupler sits in
UNDERFRAME = box(-6.4, B + 3.0, 6.4, SILL)        # dark underframe seen above the plow


def coupler_head():
    """E-type coupler head with the knuckle gap and lock-lift hole. It sits down in
    the plow notch (layer 7), its top about level with the plow tips; the hoses pass behind it."""
    head = rounded(Polygon([(-1.0, 0.0), (0.55, 0.0), (1.0, 0.3), (1.0, 1.25), (-1.0, 1.25)]), 0.12)
    head = head.difference(box(0.05, 0.0, 0.22, 0.7)).difference(Point(-0.55, 0.75).buffer(0.1))
    return affinity.translate(head, 0, B + 3.2)


def coupler_shank():
    return box(-0.42, B + 4.5, 0.42, 6.95)


MU_X = (1.85, 2.65)           # MU receptacles, in the dark gap between the plow wings
REC_Y = 5.88                  # receptacle centre height
HOSE_X = (1.0, 1.3)           # air hoses: brake pipe and main reservoir


def receptacles():
    return both(unary_union([rounded(box(x - 0.27, REC_Y - 0.33, x + 0.27, REC_Y + 0.33), 0.06)
                             for x in MU_X]))


def socket_faces():
    """Round socket face with a centre hole on the outer (empty) MU receptacles."""
    return both(rings([(MU_X[1], REC_Y)], 0.2, 0.07))


def air_hoses():
    """Hoses hang from the top of the pilot opening behind the plow; they show in
    the opening and the plow notch, passing behind the coupler head (layer 7)."""
    return both(unary_union([stroke(bezier((x, 6.95), (x, 5.6), (x - 0.15, 4.8), (x - 0.2, B + 2.05), 30), 0.17)
                             for x in HOSE_X]))


def glad_hands():
    hands = []
    for x in HOSE_X:
        cx, cy = x - 0.2, B + 2.05
        hands.append(unary_union([rounded(box(cx - 0.12, cy - 0.26, cx + 0.12, cy + 0.12), 0.05),
                                  box(cx - 0.3, cy - 0.26, cx + 0.12, cy - 0.12)]))
    return both(unary_union(hands))


def mu_jumper():
    """MU jumper cable draped across the coupler between the inner receptacles."""
    x = MU_X[0]
    cable = stroke(bezier((-x, REC_Y - 0.2), (-x + 0.3, 5.0), (x - 0.3, 5.0), (x, REC_Y - 0.2), 60), 0.22)
    return cable.difference(plugs_mu())


def plugs_mu():
    x = MU_X[0]
    return unary_union([rounded(box(s * x - 0.23, REC_Y - 0.28, s * x + 0.23, REC_Y + 0.22), 0.07)
                        for s in (-1, 1)])


# ------------------------------------------------------------------ plow
def _plow_top(x):
    """Height of the plow's top edge: low beside the notch, rising to the outer
    tips, which reach up to the bottom of the carbody."""
    x = min(max(abs(x), 1.7), 5.95)
    return B + 3.2 + 1.45 * (x - 1.7) / (5.95 - 1.7)


def plow():
    """Plow outline (front plate, layer 7): wide bottom, angled lower corners,
    tall outer tips up at the carbody, top edge sloping down to the coupler notch."""
    half = [(0, B), (4.1, B), (5.9, B + 0.95), (6.4, B + 1.6), (6.4, B + 4.6), (5.95, B + 4.65),
            (1.7, B + 3.2), (1.7, B + 1.7), (0, B + 1.7)]
    return rounded(mirror(half), 0.06)


def plow_doors():
    """Closed door on each wing (layer 8), inset from the plow edges."""
    xs = [2.15 + i * (6.05 - 2.15) / 40 for i in range(41)]
    top = [(x, _plow_top(x) - 0.3) for x in xs]
    door = Polygon([(2.15, B + 0.8), (5.7, B + 0.8), (6.05, B + 1.35)] + top[::-1])
    return both(rounded(door.intersection(plow().buffer(-0.25, join_style=2)), 0.06))


def plow_bar():
    """Reinforcing plate across the bottom centre, under the notch (layer 8)."""
    return rounded(box(-1.95, B + 0.3, 1.95, B + 1.2), 0.06)


def plow_handles():
    """White grab handles (layer 9): they come forward from the engine over the
    top of each wing, a rail along the wing with its ends turned down."""
    xs = [2.6 + i * (5.6 - 2.6) / 30 for i in range(31)]
    rail = [(x, _plow_top(x) - 0.32) for x in xs]
    pts = [(2.6, rail[0][1] - 0.4)] + rail + [(5.6, rail[-1][1] - 0.4)]
    return both(stroke(pts, 0.14))


def door_hardware():
    """Latch at the inner edge and two hinges at the outer edge of each door (layer 9)."""
    parts = [rounded(box(2.35, B + 1.4, 2.55, B + 2.1), 0.05),
             rounded(box(5.55, B + 1.3, 5.8, B + 1.55), 0.04),
             rounded(box(5.55, B + 3.0, 5.8, B + 3.25), 0.04)]
    return both(unary_union(parts))


def cut_lever():
    """Uncoupling lever from the coupler head out onto the left plow door (layer 8)."""
    return stroke([(-1.0, B + 3.3), (-1.9, B + 3.3), (-2.35, B + 2.8)], 0.15)


def silhouette():
    horn, antenna = roof_gear()
    return unary_union([body(), plow(), NOTCH, UNDERFRAME, horn, antenna])


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
    mark, word = travelmark(0.0, 14.62, cap=0.56)
    digits = text(ROAD_NUMBER, 0.52, 0.0, NUMBER_Y, tracking=0.06) if ROAD_NUMBER else None

    layers = [
        # (stem, [(paint, geometry)], note)
        ("layer01_backer", [("core", core.difference(keyholes()))],
         "backer: battery pocket + 2 keyhole hangers"),
        ("layer02_core", [("core", core.difference(keyhole_reliefs()))], "core: room for the screw heads"),
        ("layer03_core", [("core", core.difference(keyhole_reliefs()))], "core: room for the screw heads"),
        ("layer04_core_wiring", [("core", core.difference(channels()))], "core: wire channels"),
        ("layer05_glass_wiring", [("glass", core.difference(channels()))],
         "core: wire channels; top shows through the windshield"),
        ("layer06_body", [("silver", cab.difference(blue).difference(conn_recesses()).difference(PILOT_OPENING)),
                          ("black", cab.intersection(conn_recesses())),          # connector recess floors
                          ("black", cab.intersection(PILOT_OPENING).union(
                              NOTCH.union(UNDERFRAME).difference(body()).difference(plow()))),  # opening + underframe
                          ("blue", cab.intersection(blue).difference(headlight_recess())),
                          ("black", cab.intersection(headlight_recess())),      # headlight recess floor
                          ("plow", plow().difference(body())),
                          ("gray", horn), ("gray", antenna)],
         "carbody (blue wave + silver, windshield cut out, pilot opening), recess floors, underframe, plow base, horns, antenna"),
        ("layer07_nose", [("silver", nose_.difference(blue).difference(conn_recesses())),
                          ("conn_blue", conn_plates()[0]), ("black", conn_plates()[1]),
                          ("blue", nose_.intersection(blue).difference(headlight_recess())),
                          ("chrome", rings(HEADLIGHTS, 0.5, LED_RING_ID / 2)),  # lamps in the recess
                          ("black", gaskets().union(wipers())),
                          ("gray", coupler_shank().difference(coupler_head())),
                          ("gray", coupler_head()),                        # sits down in the plow notch
                          ("black", receptacles().difference(plow())),
                          ("black", air_hoses().difference(plow()).difference(nose()).difference(coupler_head().buffer(0.03))
                                    .difference(coupler_shank().buffer(0.03))),
                          ("black", hanging_cables()[0]), ("yellow", hanging_cables()[1]),
                          ("red", sill_stripe()),
                          ("plow", plow())],
         "raised nose with headlight + connector recesses, headlight rings, connector plates, gaskets "
         "with wipers, coupler, MU receptacles, air hoses, corner cables + plugs, sill stripe, plow"),
        ("layer08_lights_logo", [("black", light_housings().difference(leds)),
                                 ("black", number_board()),
                                 ("white", mark), ("white", word),
                                 ("conn_blue", conn_caps()[0]), ("black", conn_caps()[1]),
                                 ("gray", socket_faces()),
                                 ("black", mu_jumper()), ("plug", plugs_mu()),
                                 ("plug", glad_hands()),
                                 ("black", grab_irons_nose()),
                                 ("gray", cut_lever().difference(mu_jumper().buffer(0.04))),
                                 ("plow", plow_doors().difference(cut_lever().buffer(0.03))), ("plow", plow_bar())],
         "red + ditch light housings, number board, Travelmark, connector caps, MU jumper, socket faces, "
         "glad hands, uncoupling lever, plow doors + centre plate"),
        ("layer09_front_gear", [("chrome", rings(DITCHLIGHTS, 0.5, LED_RING_ID / 2)),
                                ("red", red_rings())] +
                               ([("white", digits)] if digits else []) +
                               [("white", plow_handles()),
                                ("gray", door_hardware())],
         "ditch light rings, red light rings, number digits, white plow handles, door latches + hinges"),
    ]
    return layers


# ------------------------------------------------------------------ SVG out
W_SVG = 2 * HALF_W + 2 * MARGIN
H_SVG = TOP - Y0 + 2 * MARGIN          # the sign runs from the plow bottom (Y0) to TOP


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
