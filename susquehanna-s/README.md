# Susquehanna "S" – 14" round stacked laser-cut sign

Eight-layer 3-D sign of the Susquehanna flag "S" logo (made with the railroad's permission).
Each layer is cut, painted one colour, then stacked and glued, bottom (1) to top (8).

![front](renders/render_front.png)

| Angle | Exploded |
|---|---|
| ![angle](renders/render_angle.png) | ![exploded](renders/render_exploded.png) |

![layers](renders/layer_sheet.png)

Compared with the locomotive (left: head-on photo, right: faded photo):

![compare](renders/compare_to_photo.png)

Swoosh passing behind the serif:

![detail](renders/detail_swoosh.png)

## Cut files (`svg/`)

All files are 14 in × 14 in on the same centre, so every layer lines up. They contain
cut lines only (red hairline, no fill).

| # | File | Paint | Suggested stock | What it is |
|---|------|-------|-----------------|------------|
| 1 | `layer1_base_black.svg` | Black | 1/4" | 14.00" disc – outer black rim and backer |
| 2 | `layer2_yellow_ring.svg` | Yellow | 1/8" | 13.60" disc – yellow pinstripe ring |
| 3 | `layer3_black_ring.svg` | Black | 1/8" | 13.24" disc – inner black ring |
| 4 | `layer4_blue_field.svg` | Blue | 1/8" | 12.90" disc – blue field |
| 5 | `layer5_white_stripes_stars.svg` | White | 1/8" | white stripe panel, swoosh and 10 stars |
| 6 | `layer6_red_stripes.svg` | Red | 1/8" | red stripes |
| 7 | `layer7_yellow_s_outline.svg` | Yellow | 1/8" | yellow outline of the S (0.17" border) |
| 8 | `layer8_black_s.svg` | Black | 1/8" | black S |

Total thickness with this stock is about 1-1/8". The stock thickness doesn't change the cut files.

Other files:
* `preview_flat.svg` – full-colour flat preview.
* `placement_template.svg` – every layer's outline in a different colour. Print it at 1:1
  (actual size, tiled) to position the stars, swoosh, red stripes and S pieces during glue-up.

### Hidden S support
Layers 5 and 6 each include an S-shaped piece that sits directly under the S
(inset 0.06" so it stays out of sight). It holds the S outline flat on top of the
stripes, so the S doesn't rock or leave gaps. It also joins the red stripes into
one piece, which makes layer 6 easy to align. Paint it with its layer; it is
covered by layers 7 and 8.

## Build notes
* Paint each layer before glue-up. Paint the edges too: the edges of the raised
  pieces show from an angle.
* Kerf is not compensated. With a typical 0.004–0.008" kerf, the pieces come out
  a few thousandths undersize, which is fine for stacked art.
* Stars keep one shape, but each has its own size (1.3–1.9" across), tilt and position,
  fitted to the matching star in the photo. As on the locomotive, the two stars at the
  left edge run under the ring and are clipped by it. Three stars next to the S are cut
  at 90% so they clear its outline. Smallest pieces: Swoosh tips are blunted to 0.07", and
  stripe points at the rim are trimmed, so no part of the stripe layers is thinner than
  about 0.09". Use hold-downs or tabs for the stars.
* The stripe edges, swoosh and star positions were measured from a head-on photo of the logo
  (pixel scans, fitted with smooth curves): six bands under the blue, white-red-white-red-white,
  then a wide red band at the bottom.
* The white swoosh passes behind the S's lower serif, as on the locomotive. It is
  cut as part of the white stripe piece and joined to it through the hidden S support,
  so both visible ends line up on their own.
* Glue order: 1 → 2 → 3 → 4 (all concentric discs), then 5 using the template,
  then 6, 7, 8.

## Regenerating
The geometry is fully parametric (sizes, S position, stars, stripe waves) in `generate.py`.

```
pip install shapely numpy
python3 generate.py        # writes svg/
node render.js             # writes renders/ (needs Playwright + Chromium)
```
The S letterform (`s_logo_trace.json`) was traced from a head-on photo of the
locomotive logo with `trace_s.py`. The script reads the black letter inside the
yellow outline, smooths the curves, and keeps the serif corners and spurs sharp.
It also repairs a glare dent on the top-left curve. To re-trace from a photo:
`pip install opencv-python-headless scipy`, then `python3 trace_s.py photo.jpg`.
The yellow outline is 0.21" wide, as measured from the photo, and the thinnest
stroke of the S is wider than 0.3".
