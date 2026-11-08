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
rect(X(11.5), H(oy, 28+8), 37, 8, R1C, dash="4 2"); text(X(30), H(oy, 28+4)+0.4, "R1 Riser Base (~8 in)", 10)
rect(X(11.5), H(oy, 28+16), 37, 8, R1C, dash="4 2"); text(X(30), H(oy, 28+12)+0.4, "Bambu R1 (37 in W, ~26 in D)", 10)
rect(X(11.5), H(oy, 28+33.5), 37, 17.5, "none", "#557", dash="2 3"); text(X(30), H(oy, 28+30), "lid-open envelope ~33.5 in w/ riser", 10)
# top
rect(X(0), H(oy, 28), 60, 0.75, PLY)
# aprons
rect(X(1.5), H(oy, 27.25), 57, 3.5, LUM); rect(X(1.5), H(oy, 8.5), 57, 3.5, LUM)
# legs (visible behind aprons -> draw posts)
for lx in (1.5, 55):
    rect(X(lx), H(oy, 27.25), 3.5, 26.25, POST)
    rect(X(lx+1.25), H(oy, 1), 1, 1, "#777")
rect(X(1.5), H(oy, 9.25), 57, 0.75, PLY)  # lower shelf
text(X(30), H(oy, 6.5), "lower shelf: sheet-stock storage (24x12 / 600x300 sheets)", 10)
dim(X(0), oy+2.5, X(60), "60 in top")
dim(X(11.5), H(oy, 47), X(48.5), "37 in R1")
dim(X(0), H(oy, 30), X(11.5), "11.5")
dim(X(48.5), H(oy, 30), X(60), "11.5")
vdim(X(-2.5), oy, H(oy, 28), "28 in top height")
line(X(-4), oy, X(64), oy, "#000", sw=2)

# ---------- SIDE ELEVATION (depth, wings up) ----------
ox2, oy2 = 80, 72
text(ox2+42, 3, "SIDE ELEVATION — wings up (material feeds front ⇄ back)", 13, weight="bold")
Y = lambda v: ox2 + v
rect(Y(24), H(oy2, 28), 36, 0.75, PLY); text(Y(42), H(oy2, 28)+2, "", 9)
rect(Y(0), H(oy2, 28), 24, 0.75, PLY); rect(Y(60), H(oy2, 28), 24, 0.75, PLY)
text(Y(12), H(oy2, 28)-0.8, "FRONT WING 24 in (infeed)", 10); text(Y(72), H(oy2, 28)-0.8, "REAR WING 24 in (outfeed)", 10)
# frame
rect(Y(27), H(oy2, 27.25), 30, 3.5, LUM); rect(Y(27), H(oy2, 8.5), 30, 3.5, LUM)
for lx in (27, 53.5):
    rect(Y(lx), H(oy2, 27.25), 3.5, 26.25, POST); rect(Y(lx+1.25), H(oy2, 1), 1, 1, "#777")
rect(Y(27), H(oy2, 9.25), 30, 0.75, PLY)
# stiles + brackets
for sx, dirn in ((25.5, -1), (57, 1)):
    rect(Y(sx), H(oy2, 27.25), 1.5, 22.25, LUM)
    edge = sx if dirn < 0 else sx + 1.5
    line(Y(edge), H(oy2, 27.25), Y(edge + dirn*20), H(oy2, 27.25), "#555", sw=3)
    line(Y(edge), H(oy2, 27.25-13), Y(edge + dirn*17), H(oy2, 27.25), "#555", sw=3)
text(Y(14), H(oy2, 18), "20 in folding", 10); text(Y(14), H(oy2, 16.5), "shelf brackets", 10)
# R1
rect(Y(29), H(oy2, 36), 26, 8, R1C, dash="4 2"); rect(Y(29), H(oy2, 44), 26, 8, R1C, dash="4 2")
text(Y(42), H(oy2, 32)+0.4, "Riser Base", 10); text(Y(42), H(oy2, 40)+0.4, "R1", 10)
# stock through
line(Y(-6), H(oy2, 37), Y(90), H(oy2, 37), "#a40", dash="8 4", sw=2)
text(Y(42), H(oy2, 47.5), "long stock / conveyor rails pass through (feed height ≈ verify on your unit)", 10)
dim(Y(0), oy2+2.5, Y(84), "84 in overall depth, wings up  (36 in, wings down)")
dim(Y(24), H(oy2, 50), Y(60), "36 in top")
dim(Y(27), oy2+5.5, Y(57), "30 in frame")
line(Y(-8), oy2, Y(92), oy2, "#000", sw=2)

# ---------- PLYWOOD LAYOUT ----------
oy3 = 82
text(6+48, oy3, "3/4 in PLYWOOD LAYOUT (4x8 sheets, 96 x 48)", 13, weight="bold")
def sheet(x0, y0, title, parts):
    rect(x0, y0, 48, 24, "#fafafa")  # half scale: 0.5
    text(x0+24, y0-0.6, title, 11, weight="bold")
    for (px, py, pw, ph, lab) in parts:
        rect(x0+px/2, y0+py/2, pw/2, ph/2, PLY)
        text(x0+(px+pw/2)/2, y0+(py+ph/2)/2+0.4, lab, 10)
sheet(6, oy3+3, "Sheet 1", [(0, 0, 60, 36, "A  Top 60 x 36"), (60.125, 0, 35.875, 36, "offcut 35.9 x 36"), (0, 36.125, 60, 11.875, "offcut 60 x 11.9"), (60.125, 36.125, 35.875, 11.875, "35.9 x 11.9")])
sheet(60, oy3+3, "Sheet 2", [(0, 0, 60, 24, "B  Front wing 60 x 24"), (0, 24.125, 60, 23.875, "B  Rear wing 60 x 24*"), (60.125, 0, 35.875, 48, "offcut 35.9 x 48")])
sheet(114, oy3+3, "Sheet 3", [(0, 0, 57, 30, "C  Lower shelf 57 x 30"), (57.125, 0, 38.875, 48, "offcut 38.9 x 48"), (0, 30.125, 57, 17.875, "offcut 57 x 17.9")])
text(6, oy3+30, "* second wing is 23-7/8 in after the saw kerf — fine. Notch C 3-1/2 x 3-1/2 at all four corners for the legs.", 10, anchor="start")

W, Ht = 170*S, 116*S
svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Ht}" viewBox="0 0 {W} {Ht}"><rect width="100%" height="100%" fill="white"/>' + "".join(out) + "</svg>"
open(__file__.replace("drawing.py", "workbench.svg"), "w").write(svg)
print("wrote workbench.svg")
