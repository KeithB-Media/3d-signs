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
MIN_HALF = 0.04           # red pieces: features thinner than 0.08" (bolt tips) are blunted

COLORS = {"black": "#141414", "red": "#c8282a", "white": "#f7f7f5"}


# ------------------------------------------------------------------ logo
def logo():
    data = json.load(open(os.path.join(HERE, "logo_trace.json")))
    pieces = [Polygon(p[0], p[1:]).buffer(0) for p in data["pieces"]]
    u = unary_union(pieces)
    minx, miny, maxx, maxy = u.bounds
    k = LOGO_W / (maxx - minx)
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


def build(style):
    red = logo()
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
def main(style=STYLE):
    out = os.path.join(HERE, "svg" if style == "contour" else "svg_panel")
    os.makedirs(out, exist_ok=True)
    (W, H), layers = build(style)
    W, H = round(W + 0.2, 2), round(H + 0.2, 2)          # 0.1" margin around the backer

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
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}in" height="{H}in" '
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
    print(f"{style}: sheet {W}\" x {H}\" (backer {W - 0.2:.2f}\" x {H - 0.2:.2f}\"), stack {z:.3f}\"")
    print("\n".join(rows))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else STYLE)
