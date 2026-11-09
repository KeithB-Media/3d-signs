#!/usr/bin/env python3
"""Generate laser-cut SVG layers for a stacked 1/8" MDF sign of the front of a
GE Genesis P42DC locomotive in Amtrak Phase VI colours, with working LED
headlights and ditch lights.

Units are inches. Design origin is the bottom centre of the sign (top of rail),
+x to the right, +y up; the SVG output flips y. Run:
    python3 generate.py          (needs: pip install shapely numpy fonttools)

Every layer is cut from 1/8" MDF. Layers 1-5 are the hidden "core": they give
the sign its thickness and hold the battery pocket, the wire channels and the
hanging keyholes. Layers 6-9 are the visible relief.
"""
import json
import math
import os

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))

T = 0.125                     # MDF thickness
HALF_W = 8.0                  # sign is 16" wide ...
TOP = 23.0                    # ... and 23" tall incl. roof horns (about 1:7.5 scale)
ROOF = 22.4                   # top of the carbody
MARGIN = 0.25                 # border around the drawing in the SVG files

WORDMARK = "AMTRAK"
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

# ---- liveries. Each one is written to its own folder (phase5/, phase6/).
# Colours only change the previews and the paint list; ROAD_NUMBER is cut.
_COMMON = {
    "core": "#1d1d1f",        # hidden layers: paint the edges black
    "glass": "#26313b",       # top of layer 5, seen through the windshield
    "black": "#161616",
    "white": "#f4f4f2",
    "under": "#3b4046",       # undercarriage grey: plow, steps
    "gray": "#7d838a",        # coupler, horns, glad hands, receptacle lids
    "chrome": "#e6e8ea",
}
LIVERIES = {
    # Phase V (1999 on): Platinum Mist body, Amtrak Blue nose and roof "wave",
    # Anthracite Gray underbody, Amtrak Red sill stripe, Travelmark logo.
    "phase5": {"number": "82",
               "colors": {**_COMMON, "silver": "#cdd1d4", "blue": "#1f4e79", "red": "#d9442f",
                          "under": "#4a4f52"}},
    # Phase VI (P42 #108, 2021): blue body, black and red around the windshield.
    "phase6": {"number": "108",
               "colors": {**_COMMON, "blue": "#0b4a7a", "red": "#c8202f"}},
}
COLORS = LIVERIES["phase5"]["colors"]

# ---- electronics
LED_HOLE = 0.25               # 5 mm LEDs push in from the front (loose fit, dab of glue)
LED_RING_ID = 0.36            # chrome lens ring: the LED flange sits inside it
CHANNEL_W = 0.32              # wire channel width (in layers 4 and 5)
POCKET = (2.50, 1.95)         # battery holder pocket, through layers 1-5 (0.625" deep)
POCKET_C = (0.0, 8.9)         # pocket centre: behind the nose, under the headlight
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


def stroke(pts, w, cap=1):
    return LineString(pts).buffer(w / 2, cap_style=cap, join_style=1)


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


def travel_mark(cx, cy, w=1.55, h=0.82):
    """Three sweeping stripes in the spirit of Amtrak's Travel Mark: they rise
    from the left and fan out toward the right. Each stripe is a separate piece
    at least 0.1" wide so it survives cutting. Approximate - swap in the
    official artwork if you have it."""
    bands = []
    for k in range(3):
        y0 = -h / 2 + 0.06 + k * 0.2
        rise = 0.18 + 0.16 * k
        pts = bezier((-w / 2, y0), (-w / 6, y0 - 0.02), (w / 6, y0 + rise * 0.55), (w / 2, y0 + rise), 40)
        upper = [(x, y + 0.055 + 0.02 * i / 40) for i, (x, y) in enumerate(pts)]
        lower = [(x, y - 0.055 - 0.02 * i / 40) for i, (x, y) in enumerate(pts)]
        bands.append(Polygon(upper + lower[::-1]))
    return affinity.translate(unary_union(bands), cx, cy)


# ------------------------------------------------------------------ carbody
def body():
    """Carbody from the sill (y=3.4) to the roof: straight lower sides, upper
    sides leaning in (Genesis 'tumblehome'), rounded roof corners."""
    half = [(0, 3.4), (8.0, 3.4), (8.0, 14.4), (6.9, 21.2), (6.6, 21.95),
            (6.1, 22.32), (5.45, ROOF), (0, ROOF)]
    return rounded(mirror(half), 0.05)


def roof_gear():
    """Horn cluster and radio antenna, seen over the roof line."""
    horn = unary_union([box(2.3, ROOF - 0.05, 4.3, ROOF + 0.12),          # mounting bar
                        box(3.2, ROOF + 0.05, 3.4, ROOF + 0.32),          # post
                        rounded(box(2.35, ROOF + 0.28, 4.25, ROOF + 0.52), 0.08)] +  # manifold
                       [Polygon([(x - 0.12, ROOF + 0.5), (x + 0.12, ROOF + 0.5),
                                 (x + 0.22, TOP), (x - 0.22, TOP)]) for x in (2.65, 3.3, 3.95)])
    antenna = unary_union([box(-3.9, ROOF - 0.05, -3.1, ROOF + 0.14),
                           Polygon([(-3.62, ROOF + 0.1), (-3.38, ROOF + 0.1), (-3.44, ROOF + 0.55),
                                    (-3.56, ROOF + 0.55)])])
    return horn, antenna


def plow():
    half = [(0, 0.0), (4.3, 0.0), (6.45, 1.85), (6.45, 3.5), (0, 3.5)]
    return mirror(half)


def plow_face():
    """Raised plow plate with three horizontal ribs cut as grooves."""
    face = plow().buffer(-0.18, join_style=2).intersection(box(-9, 0, 9, 3.1))
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


def window_mask():
    """Black surround: one piece around both panes, the centre post included."""
    return windows().convex_hull.buffer(0.42, join_style=1).difference(windows())


def red_band():
    """Red band hugging the black mask: under the windshield and up the sides."""
    inner = windows().convex_hull.buffer(0.42, join_style=1)
    outer = windows().convex_hull.buffer(0.95, join_style=1)
    return outer.difference(inner).intersection(box(-9, 0, 9, 17.7))


def wipers():
    """Parked wipers, joined to the mask at both ends so they're strong."""
    arm = stroke([(4.9, 15.63), (0.26, 16.9)], 0.18, cap=2)
    pivot = Point(4.75, 15.6).buffer(0.16)
    return both(unary_union([arm, pivot]))


def nose_and_skirt():
    """Forward-sloping nose under the windshield plus the skirt below it, one
    piece. The triangles left over at each side are the cab 'cheeks', one layer lower."""
    nose_top = red_band().bounds[1]
    half = [(0, 3.4), (8.0, 3.4), (8.0, 7.8), (7.45, 7.8), (6.5, nose_top), (0, nose_top)]
    return rounded(mirror(half), 0.08)


def gaskets():
    """Phase V: separate black rubber gaskets around each pane."""
    return windows().buffer(0.24, join_style=1).difference(windows())


def wave_p5():
    """Phase V: everything above this curve is Amtrak Blue (the "wave" over the
    roof and nose); below it is Platinum Mist. It dips toward the centre of the nose."""
    pts = [(x / 10, 10.35 + 0.9 * (x / 80) ** 2) for x in range(-90, 91)]
    return Polygon(pts + [(9, TOP + 1), (-9, TOP + 1)])


def nose_p5():
    """Phase V nose + lower front, from the red sill stripe up to just under the gaskets."""
    half = [(0, 3.75), (8.0, 3.75), (8.0, 7.8), (7.45, 7.8), (6.45, 15.3), (0, 15.3)]
    return rounded(mirror(half), 0.08)


def sill_stripe_p5():
    """Phase V: Amtrak Red sill stripe across the bottom of the carbody."""
    return box(-HALF_W, 3.4, HALF_W, 3.75)


def travelmark_p5(cx, cy, cap=0.56):
    """Phase V style Travelmark: the AMTRAK wordmark over three sweeping stripes
    that fan out to the right. Stripes are at least 0.1" wide so they can be cut.
    Approximate - swap in the official artwork if you have it."""
    word = text(WORDMARK, cap, 0.0, 0.0, tracking=0.06)
    minx, _, maxx, _ = word.bounds
    w = maxx - minx
    bands = []
    for k in range(3):
        x0 = minx + 0.12 * w + 0.07 * w * k                      # left tips step in
        y_top = -cap / 2 - 0.32 - 0.22 * k
        pts = bezier((x0, y_top - 0.32), (x0 + 0.3 * w, y_top - 0.1),
                     (maxx - 0.35 * w, y_top + 0.02), (maxx + 0.08 * w, y_top + 0.12), 50)
        n = len(pts) - 1
        half = [0.05 + 0.045 * (i / n) for i in range(n + 1)]   # widen to the right
        upper = [(x, y + h) for (x, y), h in zip(pts, half)]
        lower = [(x, y - h) for (x, y), h in zip(pts, half)]
        bands.append(Polygon(upper + lower[::-1]))
    mark = unary_union(bands)
    both_ = unary_union([word, mark])
    bx0, by0, bx1, by1 = both_.bounds
    dx, dy = cx - (bx0 + bx1) / 2, cy - (by0 + by1) / 2
    return affinity.translate(mark, dx, dy), affinity.translate(word, dx, dy)


def grab_irons():
    pcs = [box(7.3, 3.95, 7.5, 7.15),                         # beside the steps
           stroke([(6.05, 12.6), (5.82, 14.1)], 0.18)]       # on the nose
    return both(unary_union(pcs))


# ------------------------------------------------------------------ front end
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
    """Draft gear/shank plus the E-type coupler head with its knuckle gap."""
    shank = box(-0.42, 3.4, 0.42, 5.82)
    head = rounded(Polygon([(-1.0, 2.3), (0.55, 2.3), (1.0, 2.6), (1.0, 3.55), (-1.0, 3.55)]), 0.12)
    knuckle_gap = box(0.05, 2.3, 0.22, 3.0)
    pin = Point(-0.55, 3.0).buffer(0.1)                      # lock-lift hole
    return unary_union([shank, head]).difference(knuckle_gap).difference(pin)


MU_X = (1.95, 2.5)            # MU receptacles each side of the coupler
HEP_X = (3.45, 4.45)          # HEP receptacle and its dummy (stowage) socket
HOSE_X = (1.2, 1.5)           # air hoses: brake pipe and main reservoir


def receptacles():
    mu = [rounded(box(x - 0.24, 4.3, x + 0.24, 4.85), 0.06) for x in MU_X]
    hep = [rounded(box(x - 0.3, 4.15, x + 0.3, 4.85), 0.08) for x in HEP_X]
    return both(unary_union(mu + hep))


def receptacle_lids():
    """Hinged spring lids on top of each receptacle (layer 9)."""
    mu = [rounded(box(x - 0.2, 4.68, x + 0.2, 4.95), 0.05) for x in MU_X]
    hep = [rounded(box(x - 0.26, 4.68, x + 0.26, 4.98), 0.06) for x in HEP_X]
    return both(unary_union(mu + hep))


def air_hoses():
    """Hoses hang from the anticlimber, curve out and end in glad hands."""
    hoses = [stroke(bezier((x, 5.85), (x, 4.4), (x + 0.25, 3.2), (x + 0.2, 1.95), 30), 0.17)
             for x in HOSE_X]
    return both(unary_union(hoses))


def glad_hands():
    hands = []
    for x in HOSE_X:
        cx, cy = x + 0.2, 1.75
        hands.append(unary_union([rounded(box(cx - 0.13, cy - 0.28, cx + 0.13, cy + 0.12), 0.05),
                                  box(cx - 0.13, cy - 0.28, cx + 0.32, cy - 0.12)]))
    return both(unary_union(hands))


def cut_lever():
    """Uncoupling lever across the top of the plow: handle at the left end,
    bracket half-way, crank at the coupler."""
    bar = stroke([(-5.1, 3.18), (-1.05, 3.18)], 0.16)
    handle = stroke([(-5.1, 3.18), (-5.25, 2.75), (-4.85, 2.65)], 0.15)
    crank = stroke([(-1.05, 3.18), (-1.05, 3.48)], 0.15)
    return unary_union([bar, handle, crank])


def cut_lever_brackets():
    """Brackets the lever rests on (layer 8)."""
    return unary_union([rounded(box(-4.7, 2.95, -4.3, 3.4), 0.05),
                        rounded(box(-2.9, 2.95, -2.5, 3.4), 0.05)])


def mu_cable():
    """MU jumper cable draped across the coupler between the inner receptacles,
    with a plug head at each end."""
    x = MU_X[0]
    cable = stroke(bezier((-x, 4.4), (-x + 0.2, 3.2), (x - 0.2, 3.2), (x, 4.4), 60), 0.2)
    plugs = unary_union([rounded(box(s * x - 0.2, 4.3, s * x + 0.2, 4.68), 0.06) for s in (-1, 1)])
    return unary_union([cable, plugs])


def hep_cables():
    """HEP jumper stowed in a loop between its receptacle and dummy socket."""
    a, b = HEP_X
    loop = stroke(bezier((a, 4.25), (a + 0.05, 3.55), (b - 0.05, 3.55), (b, 4.25), 40), 0.22)
    plugs = unary_union([rounded(box(x - 0.24, 4.15, x + 0.24, 4.6), 0.06) for x in HEP_X])
    return both(unary_union([loop, plugs]))


def silhouette():
    horn, antenna = roof_gear()
    return unary_union([body(), plow(), both(box(6.72, 0.85, 7.88, 3.6)), horn, antenna])


# ------------------------------------------------------------------ electronics
def led_holes():
    return unary_union([Point(p).buffer(LED_HOLE / 2) for p in HEADLIGHTS + DITCHLIGHTS])


def pocket():
    w, h = POCKET
    return rounded(box(POCKET_C[0] - w / 2, POCKET_C[1] - h / 2,
                       POCKET_C[0] + w / 2, POCKET_C[1] + h / 2), 0.06)


def channels():
    cx, cy = POCKET_C
    runs = [LineString([(cx, cy), (0, HEADLIGHTS[0][1])]), LineString(HEADLIGHTS)]
    for x, y in DITCHLIGHTS:
        s = 1 if x > 0 else -1
        runs.append(LineString([(cx, cy), (s * 1.6, 6.9), (x, y)]))
    lines = unary_union([r.buffer(CHANNEL_W / 2, cap_style=1, join_style=1) for r in runs])
    led_seats = unary_union([Point(p).buffer(0.2) for p in HEADLIGHTS + DITCHLIGHTS])
    return unary_union([lines, led_seats])


def keyholes():
    """Keyhole slot in the backer: the screw head goes in the big hole and the
    sign drops 0.5" so the shank sits at the top of the slot."""
    return unary_union([unary_union([Point(x, y).buffer(0.2), box(x - 0.09, y, x + 0.09, y + 0.5),
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
def logo(cap=0.62, cy=13.45):
    """Travel Mark + wordmark, centred on the nose between headlight and windshield."""
    k = cap / 0.62
    word = text(WORDMARK, cap, 0.0, 0.0, tracking=0.07 * k)
    ww = word.bounds[2] - word.bounds[0]
    mark = travel_mark(0, 0, w=1.55 * max(k, 0.9), h=0.82)
    mw = mark.bounds[2] - mark.bounds[0]
    gap = 0.22 * k
    total = mw + gap + ww
    mark = affinity.translate(mark, -total / 2 + mw / 2, cy + 0.04)
    word = affinity.translate(word, -total / 2 + mw + gap + ww / 2, cy)
    return mark, word


def build(livery):
    number_text = LIVERIES[livery]["number"]
    sil = silhouette()
    core = sil.difference(pocket())
    leds = led_holes()
    horn, antenna = roof_gear()
    plow_back = plow().difference(body())
    if livery == "phase5":
        mark, word = travelmark_p5(0.0, 8.85)
        logo_paint = "blue"
        wave = wave_p5()
        cab = body().difference(windows()).difference(leds)
        nose = nose_p5().difference(leds)
        number = text(number_text, 0.75, 0.0, 21.05, tracking=0.08) if number_text else None
        layer6 = [("silver", cab.difference(wave)), ("blue", cab.intersection(wave))]
        layer7 = [("silver", nose.difference(wave)), ("blue", nose.intersection(wave)),
                  ("red", sill_stripe_p5()),
                  ("black", gaskets().union(wipers())),
                  ("under", plow_face())]
        layer7 += [("white", number)] if number else []
        note7 = "nose (blue wave + silver), red sill stripe, gaskets with wipers, plow face, road number"
        numbers = []
    else:
        mark, word = logo()
        logo_paint = "white"
        layer6 = [("blue", body().difference(windows()).difference(leds))]
        layer7 = [("blue", nose_and_skirt().difference(leds)),
                  ("red", red_band()),
                  ("black", window_mask().union(wipers())),
                  ("under", plow_face())]
        note7 = "nose + skirt, red band, black window mask with wipers, plow face"
        number = text(number_text, 0.7, 0.0, 9.55, tracking=0.08) if number_text else None
        numbers = [(logo_paint, number)] if number else []

    layers = [
        # (stem, [(paint, geometry)], note)
        ("layer1_backer", [("core", core.difference(keyholes()))],
         "backer: battery pocket + 2 keyhole hangers"),
        ("layer2_core", [("core", core.difference(keyhole_reliefs()))], "core: room for the screw heads"),
        ("layer3_core", [("core", core.difference(keyhole_reliefs()))], "core: room for the screw heads"),
        ("layer4_core_wiring", [("core", core.difference(channels()))], "core: wire channels"),
        ("layer5_glass_wiring", [("glass", core.difference(channels()))],
         "core: wire channels; top shows through the windshield"),
        ("layer6_body", layer6 + [("under", plow_back.difference(leds)),
                         ("under", steps()),
                         ("gray", horn.difference(body())), ("gray", antenna.difference(body()))],
         "carbody (windshield cut out), plow backing, steps, horns, antenna"),
        ("layer7_nose", layer7, note7),
        ("layer8_details", [("black", headlight_bezel().difference(leds)),
                            ("black", ditch_housings().difference(leds)),
                            (logo_paint, mark), (logo_paint, word)] + numbers + [
                            ("black", anticlimber().difference(coupler().buffer(0.03))),
                            ("gray", coupler()),
                            ("black", receptacles()),
                            ("black", air_hoses().difference(anticlimber())),
                            ("black", cut_lever_brackets()),
                            ("black", grab_irons())],
         "headlight + ditch housings, logo, number, anticlimber, coupler, receptacles, hoses, grab irons"),
        ("layer9_front_gear", [("chrome", lens_rings()),
                               ("black", mu_cable()),
                               ("black", hep_cables()),
                               ("gray", receptacle_lids().difference(mu_cable()).difference(hep_cables())),
                               ("gray", glad_hands()),
                               ("black", cut_lever().difference(mu_cable().buffer(0.04)))],
         "lens rings, MU jumper, HEP jumpers, receptacle lids, glad hands, cut lever"),
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


def check(stem, pieces):
    """Warn about overlapping pieces in a layer, and slivers that won't survive the laser."""
    for i in range(len(pieces)):
        for j in range(i + 1, len(pieces)):
            a = pieces[i][1].intersection(pieces[j][1]).area
            if a > 1e-4:
                print(f"  WARNING: {stem}: pieces {i} and {j} overlap ({a:.4f} sq in)")
    for c, g in pieces:
        thin = g.difference(g.buffer(-0.045).buffer(0.045))
        if thin.area > 0.01:
            print(f"  note: {stem} ({c}) has {thin.area:.3f} sq in narrower than 0.09\"")


def write(livery):
    global COLORS
    COLORS = LIVERIES[livery]["colors"]
    OUT = os.path.join(HERE, livery, "svg")
    print(f"== {livery} -> {os.path.relpath(OUT, HERE)}")
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):                       # clear out files from older versions
        if f.endswith(".svg") or f.endswith(".json"):
            os.remove(os.path.join(OUT, f))
    layers = build(livery)
    data, rows, z = [], [], 0.0
    for i, (stem, pieces, note) in enumerate(layers, 1):
        check(stem, pieces)
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

    cover = back_cover()
    with open(os.path.join(OUT, "back_cover.svg"), "w") as f:
        f.write(svg_doc(f'<path d="{path_d(cover)}" fill="none" stroke="#FF0000" stroke-width="0.01"/>',
                        "Battery pocket cover - screws to the back"))

    body_ = "\n".join(f'<path d="{p["d"]}" fill="{p["color"]}" fill-rule="evenodd"/>'
                      for L in data for p in L["pieces"])
    with open(os.path.join(OUT, "preview_flat.svg"), "w") as f:
        f.write(svg_doc(body_, "Flat colour preview"))

    tcols = ["#000", "#888", "#888", "#0a0", "#0a0", "#00c", "#c90", "#c00", "#808"]
    body_ = "\n".join(f'<path d="{" ".join(p["d"] for p in L["pieces"])}" fill="none" '
                      f'stroke="{tcols[k]}" stroke-width="0.015"/>' for k, L in enumerate(data))
    with open(os.path.join(OUT, "placement_template.svg"), "w") as f:
        f.write(svg_doc(body_, "Glue-up placement template (print 1:1)"))

    meta = {"w": W_SVG, "h": H_SVG, "top": TOP, "margin": MARGIN,
            "lights": [[x + HALF_W + MARGIN, TOP + MARGIN - y] for x, y in HEADLIGHTS + DITCHLIGHTS],
            "layers": data}
    with open(os.path.join(OUT, "layers.json"), "w") as f:
        json.dump(meta, f)
    print("\n".join(rows))
    print(f"total stack height: {z:.3f}\"  |  sheet size {W_SVG:.2f}\" x {H_SVG:.2f}\"")


def main():
    import sys
    for livery in sys.argv[1:] or LIVERIES:
        write(livery)


if __name__ == "__main__":
    main()
