"""Milwaukee logo stacked laser-cut sign (personal gift, not for sale).

Uses the logo traced from source/logo.png by trace_logo.py (logo_trace.json) and writes one
cut SVG per layer. All units are inches; y points up internally and is flipped on output.
"""
import json
import os
import sys

from shapely import affinity
from shapely.geometry import MultiPolygon, Polygon, box
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ settings
STYLE = "contour"         # "contour": cut to the logo's shape; "panel": rounded rectangle
LOGO_W = 22.0             # logo width (wordmark + bolt), inches
WHITE = 0.35              # white border around the logo (contour style)
RIM = 0.30                # black rim outside the white
CLOSE = 2.2               # contour style: dips narrower than ~2x this are filled in
PANEL_PAD = (0.9, 0.9)    # panel style: white space left/right and top/bottom of the logo
PANEL_CORNER = 0.6
# Bambu R1 laser without the material feeder: 600 x 300 mm. Each layer must fit the bed with a
# little clearance, so the backer is kept within these sizes ("r1" versions).
R1_MAX_MM = (590.0, 290.0)
MIN_HALF = 0.04           # red pieces: features thinner than 0.08" (bolt tips) are blunted

COLORS = {"black": "#141414", "red": "#c8282a", "white": "#f7f7f5"}


# ------------------------------------------------------------------ logo
def logo(logo_w=None):
    data = json.load(open(os.path.join(HERE, "logo_trace.json")))
    pieces = [Polygon(p[0], p[1:]).buffer(0) for p in data["pieces"]]
    u = unary_union(pieces)
    minx, miny, maxx, maxy = u.bounds
    k = (logo_w or LOGO_W) / (maxx - minx)
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    out = []
    for p in pieces:          # image y points down -> flip; centre on the origin
        p = affinity.affine_transform(p, [k, 0, 0, -k, -cx * k, cy * k])
        p = p.buffer(-MIN_HALF, join_style="mitre").buffer(MIN_HALF, join_style="mitre", mitre_limit=10)
        out.append(p)
    return unary_union(out)


def smooth_hull(g, d, close):
    """Offset by d, fill gaps/notches narrower than ~2*close, round the outer corners."""
    g = g.buffer(d + close, quad_segs=24).buffer(-close, quad_segs=24)
    return Polygon(g.exterior) if isinstance(g, Polygon) else unary_union([Polygon(p.exterior) for p in g.geoms])


def rrect(w, h, r):
    return box(-w / 2 + r, -h / 2 + r, w / 2 - r, h / 2 - r).buffer(r, quad_segs=24)


def build(style, logo_w=None):
    red = logo(logo_w)
    minx, miny, maxx, maxy = red.bounds
    if style == "contour":
        white = smooth_hull(red, WHITE, CLOSE)
        base = smooth_hull(red, WHITE + RIM, CLOSE)
        what = "cut to the logo's shape"
    else:
        pw, ph = (maxx - minx) + 2 * PANEL_PAD[0], (maxy - miny) + 2 * PANEL_PAD[1]
        white = rrect(pw, ph, PANEL_CORNER)
        base = rrect(pw + 2 * RIM, ph + 2 * RIM, PANEL_CORNER + RIM)
        what = "rounded rectangle"
    bx = base.bounds
    size = (bx[2] - bx[0], bx[3] - bx[1])
    n = len(red.geoms) if isinstance(red, MultiPolygon) else 1
    return size, [
        ("layer1_base_black", "black", base, 0.25, f"backer, {what}; shows as a {RIM}\" black rim"),
        ("layer2_white_field", "white", white, 0.125, "white field"),
        ("layer3_red_logo", "red", red, 0.25, f"red logo ({n} pieces)"),
    ]


# ------------------------------------------------------------------ SVG out
def fit_logo_w(style, max_w, max_h):
    """Largest logo width whose backer fits within max_w x max_h inches."""
    lo, hi = 5.0, 40.0
    for _ in range(30):
        mid = (lo + hi) / 2
        (bw, bh), _ = build(style, mid)
        lo, hi = (mid, hi) if bw <= max_w and bh <= max_h else (lo, mid)
    return lo


def main(style=STYLE, r1=False):
    name = "svg" + ("_r1" if r1 else "") + ("" if style == "contour" else "_panel")
    out = os.path.join(HERE, name)
    os.makedirs(out, exist_ok=True)
    logo_w = fit_logo_w(style, R1_MAX_MM[0] / 25.4, R1_MAX_MM[1] / 25.4) if r1 else None
    (W, H), layers = build(style, logo_w)
    if r1:                               # bed-sized sheet so it drops onto the bed origin as-is
        W, H = 600 / 25.4, 300 / 25.4
    else:
        W, H = round(W + 0.2, 2), round(H + 0.2, 2)      # 0.1" margin around the backer

    def path_d(geom):
        polys = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
        res = []
        for p in polys:
            for ring in [p.exterior, *p.interiors]:
                pts = list(ring.coords)[:-1]
                res.append("M" + " L".join(f"{x + W / 2:.4f},{H / 2 - y:.4f}" for x, y in pts) + " Z")
        return " ".join(res)

    def svg_doc(body, title):
        return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{W * 25.4:.2f}mm" height="{H * 25.4:.2f}mm" '
                f'viewBox="0 0 {W} {H}">\n<title>{title}</title>\n{body}\n</svg>\n')

    preview, z, rows = [], 0.0, []
    for i, (stem, color, geom, thick, note) in enumerate(layers, 1):
        d = path_d(geom)
        cut = f'<path d="{d}" fill="none" stroke="#FF0000" stroke-width="0.01" fill-rule="evenodd"/>'
        with open(os.path.join(out, stem + ".svg"), "w") as f:
            f.write(svg_doc(cut, f"Layer {i} - {note} - paint {color}"))
        preview.append((stem, color, d, z, thick))
        rows.append(f"| {i} | `{os.path.basename(out)}/{stem}.svg` | {color} | {thick}\" | {note} |")
        z += thick

    body = "\n".join(f'<path d="{d}" fill="{COLORS[c]}" fill-rule="evenodd"/>' for _, c, d, _, _ in preview)
    with open(os.path.join(out, "preview_flat.svg"), "w") as f:
        f.write(svg_doc(body, "Flat colour preview"))
    tcols = ["#000", "#08c", "#c00"]
    body = "\n".join(f'<path d="{d}" fill="none" stroke="{tcols[k]}" stroke-width="0.015" fill-rule="evenodd"/>'
                     for k, (_, _, d, _, _) in enumerate(preview))
    with open(os.path.join(out, "placement_template.svg"), "w") as f:
        f.write(svg_doc(body, "Glue-up placement template (print 1:1)"))
    with open(os.path.join(out, "layers.json"), "w") as f:
        json.dump({"w": W, "h": H, "layers": [{"stem": s, "color": COLORS[c], "d": d, "z": z, "t": t}
                                              for s, c, d, z, t in preview]}, f)
    bx = layers[0][2].bounds
    bw, bh = bx[2] - bx[0], bx[3] - bx[1]
    lb = layers[2][2].bounds
    print(f"{name}: sheet {W * 25.4:.0f} x {H * 25.4:.0f} mm, backer {bw * 25.4:.1f} x {bh * 25.4:.1f} mm "
          f"({bw:.2f}\" x {bh:.2f}\"), logo {(lb[2] - lb[0]) * 25.4:.0f} mm wide, stack {z:.3f}\"")
    print("\n".join(rows))


if __name__ == "__main__":
    args = sys.argv[1:]
    main(next((a for a in args if a in ("contour", "panel")), STYLE), r1="r1" in args)
