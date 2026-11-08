"""Generate r1-workbench/workbench.svg: front + side elevations and plywood layout.
All dimensions in inches. Run: python3 drawing.py"""
S = 7  # px per inch
out = []
def rect(x, y, w, h, fill="#e9d3a8", stroke="#333", dash=None, sw=1):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(f'<rect x="{x*S:.1f}" y="{y*S:.1f}" width="{w*S:.1f}" height="{h*S:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')
def line(x1, y1, x2, y2, stroke="#333", dash=None, sw=1):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    out.append(f'<line x1="{x1*S:.1f}" y1="{y1*S:.1f}" x2="{x2*S:.1f}" y2="{y2*S:.1f}" stroke="{stroke}" stroke-width="{sw}"{d}/>')
def text(x, y, s, size=11, anchor="middle", weight="normal"):
    out.append(f'<text x="{x*S:.1f}" y="{y*S:.1f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" font-family="Arial">{s}</text>')
def dim(x1, y, x2, label):
    line(x1, y, x2, y, "#c00"); line(x1, y-0.6, x1, y+0.6, "#c00"); line(x2, y-0.6, x2, y+0.6, "#c00")
    text((x1+x2)/2, y-0.5, label, 10)
def vdim(x, y1, y2, label):
    line(x, y1, x, y2, "#c00"); line(x-0.6, y1, x+0.6, y1, "#c00"); line(x-0.6, y2, x+0.6, y2, "#c00")
    out.append(f'<text x="{(x-0.8)*S:.1f}" y="{(y1+y2)/2*S:.1f}" font-size="10" text-anchor="middle" font-family="Arial" transform="rotate(-90 {(x-0.8)*S:.1f} {(y1+y2)/2*S:.1f})">{label}</text>')

PLY, LUM, POST, R1C = "#f3e2bf", "#e0bb7a", "#c9995a", "#9fb7d6"
FLOOR = 0  # we draw with y downward; convert height h -> y = OY - h
def H(oy, h): return oy - h

# ---------- FRONT ELEVATION (width) ----------
ox, oy = 6, 72
text(ox+30, 3, "FRONT ELEVATION (looking at the R1's front)", 13, weight="bold")
X = lambda v: ox + v
# R1 + riser (approx)
rect(X(4), H(oy, 28+8), 37, 8, R1C, dash="4 2"); text(X(22.5), H(oy, 28+4)+0.4, "R1 Riser Base (~8 in)", 10)
rect(X(4), H(oy, 28+16), 37, 8, R1C, dash="4 2"); text(X(22.5), H(oy, 28+12)+0.4, "Bambu R1 (37 in W, ~26 in D)", 10)
rect(X(4), H(oy, 28+33.5), 37, 17.5, "none", "#557", dash="2 3"); text(X(22.5), H(oy, 28+30), "lid-open envelope ~33.5 in w/ riser", 10)
# top
rect(X(0), H(oy, 28), 45, 0.75, PLY)
# aprons
rect(X(1.5), H(oy, 27.25), 42, 3.5, LUM); rect(X(1.5), H(oy, 8.5), 42, 3.5, LUM)
# legs (visible behind aprons -> draw posts)
for lx in (1.5, 40):
    rect(X(lx), H(oy, 27.25), 3.5, 26.25, POST)
    rect(X(lx+1.25), H(oy, 1), 1, 1, "#777")
rect(X(1.5), H(oy, 9.25), 42, 0.75, PLY)  # lower shelf
text(X(22.5), H(oy, 6.5), "lower shelf: sheet stock (24x12 / 600x300)", 10)
dim(X(0), oy+2.5, X(45), "45 in top")
dim(X(4), H(oy, 47), X(41), "37 in R1")
dim(X(0), H(oy, 30), X(4), "4")
dim(X(41), H(oy, 30), X(45), "4")
vdim(X(-2.5), oy, H(oy, 28), "28 in top height")
line(X(-4), oy, X(64), oy, "#000", sw=2)
text(X(22.5), oy+5.5, "4 in = Bambu's 100 mm side clearance", 10)

# ---------- SIDE ELEVATION (depth) ----------
ox2, oy2 = 100, 72
text(ox2+18, 3, "SIDE ELEVATION — material feeds front ⇄ back", 13, weight="bold")
Y = lambda v: ox2 + v
rect(Y(0), H(oy2, 28), 36, 0.75, PLY)
rect(Y(3), H(oy2, 27.25), 30, 3.5, LUM); rect(Y(3), H(oy2, 8.5), 30, 3.5, LUM)
for lx in (3, 29.5):
    rect(Y(lx), H(oy2, 27.25), 3.5, 26.25, POST); rect(Y(lx+1.25), H(oy2, 1), 1, 1, "#777")
rect(Y(3), H(oy2, 9.25), 30, 0.75, PLY)
# R1 (26 in deep, centered)
rect(Y(5), H(oy2, 36), 26, 8, R1C, dash="4 2"); rect(Y(5), H(oy2, 44), 26, 8, R1C, dash="4 2")
text(Y(18), H(oy2, 32)+0.4, "Riser Base", 10); text(Y(18), H(oy2, 40)+0.4, "R1", 10)
# stock overhanging both ends, carried by the conveyor rails
line(Y(-14), H(oy2, 37), Y(50), H(oy2, 37), "#a40", dash="8 4", sw=2)
text(Y(-8), H(oy2, 38.5), "← stock overhangs", 10); text(Y(44), H(oy2, 38.5), "overhangs →", 10)
text(Y(18), H(oy2, 50.5), "Bambu: allow (stock − 400 mm) in front,", 10)
text(Y(18), H(oy2, 48.5), "(stock − 550 mm) behind, kept clear at feed height", 10)
text(Y(-10), H(oy2, 30), "FRONT", 11, weight="bold"); text(Y(46), H(oy2, 30), "REAR", 11, weight="bold")
dim(Y(0), oy2+2.5, Y(36), "36 in top")
dim(Y(3), oy2+5.5, Y(33), "30 in frame")
dim(Y(5), H(oy2, 46), Y(31), "26 in (660 mm)")
line(Y(-16), oy2, Y(52), oy2, "#000", sw=2)

# ---------- PLYWOOD LAYOUT ----------
oy3 = 82
text(6+48, oy3, "3/4 in PLYWOOD LAYOUT (one 4x8 sheet)", 13, weight="bold")
def sheet(x0, y0, title, parts):
    rect(x0, y0, 48, 24, "#fafafa")  # half scale: 0.5
    text(x0+24, y0-0.6, title, 11, weight="bold")
    for (px, py, pw, ph, lab) in parts:
        rect(x0+px/2, y0+py/2, pw/2, ph/2, PLY)
        text(x0+(px+pw/2)/2, y0+(py+ph/2)/2+0.4, lab, 10)
sheet(6, oy3+3, "Sheet 1", [(0, 0, 45, 36, "A  Top 45 x 36"), (45.125, 0, 42, 30, "C  Shelf 42 x 30"), (0, 36.125, 45, 11.875, "offcut 45 x 11.9"), (45.125, 30.125, 42, 17.875, "offcut 42 x 17.9")])
text(6, oy3+30, "Notch C 3-1/2 x 3-1/2 at all four corners for the legs.", 10, anchor="start")

W, Ht = 170*S, 116*S
svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Ht}" viewBox="0 0 {W} {Ht}"><rect width="100%" height="100%" fill="white"/>' + "".join(out) + "</svg>"
open(__file__.replace("drawing.py", "workbench.svg"), "w").write(svg)
print("wrote workbench.svg")
