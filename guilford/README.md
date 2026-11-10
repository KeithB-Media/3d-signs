# Guilford "G" – 14" round stacked laser-cut sign

Eight-layer 3-D sign in Guilford Rail System gray, orange and white, built the same way
as the Susquehanna S sign. Each layer is cut and painted one colour, then the layers are
stacked and glued from bottom (1) to top (8).

> **Draft letterform.** The G is a parametric geometric letter. It was not traced from a
> photo. To match the locomotive herald exactly, add a head-on photo and the G can be traced
> the same way as the S (see `../susquehanna-s/trace_s.py`). Until then, change the `G_*`
> settings in `generate.py`.

![front](renders/render_front.png)

| Angle | Exploded |
|---|---|
| ![angle](renders/render_angle.png) | ![exploded](renders/render_exploded.png) |

![layers](renders/layer_sheet.png)

## Cut files (`svg/`)

All files are 14 in × 14 in on the same centre, so every layer lines up. They contain
cut lines only: red hairlines with no fill.

| # | File | Paint | Suggested stock | What it is |
|---|------|-------|-----------------|------------|
| 1 | `layer1_base_gray.svg` | Gray | 1/4" | 14.00" disc – outer gray rim and backer |
| 2 | `layer2_white_ring.svg` | White | 1/8" | 13.60" disc – white pinstripe ring |
| 3 | `layer3_orange_ring.svg` | Orange | 1/8" | 13.24" disc – orange ring |
| 4 | `layer4_gray_field.svg` | Gray | 1/8" | 12.90" disc – gray field |
| 5 | `layer5_white_stripe.svg` | White | 1/8" | white stripe band (with hidden G support) |
| 6 | `layer6_orange_stripe.svg` | Orange | 1/8" | orange stripe (with hidden G support) |
| 7 | `layer7_gray_g_outline.svg` | Gray | 1/8" | gray outline of the G (0.22" border) |
| 8 | `layer8_white_g.svg` | White | 1/8" | white G |

With this stock the sign is about 1-1/8" thick in total. A different stock thickness doesn't change the cut files.

Other files:
* `preview_flat.svg` – full-colour flat preview.
* `placement_template.svg` – every layer's outline in a different colour. Print it at 1:1
  (actual size, tiled) to place the stripe pieces and the G during glue-up.

## Build notes
* Every layer is a single piece. Layers 5 and 6 each include a G-shaped support that sits
  under the G, inset 0.06" so it stays hidden. The support keeps the G flat where it crosses the
  stripes, and it locks the stripe band to the G, so the band lines up without
  measuring.
* The gray outline (layer 7) separates the white G from the white and orange stripes. Over the
  gray field it shows only as a raised step and a shadow line.
* Paint each layer before glue-up, including the edges.
* Kerf is not compensated, which is fine for stacked art.
* Glue order: 1 → 2 → 3 → 4 (concentric discs), then 5 and 6 using the template, then 7, 8.

## Regenerating
```
pip install shapely numpy
python3 generate.py        # writes svg/
node render.js             # writes renders/ (needs Playwright + Chromium)
```
Settings in `generate.py`:
* `G_*` – size, stroke, opening, crossbar and outline of the G.
* `STRIPE_*` / `PIN` – stripe band position and pinstripe width.
* `COLORS` – preview colours only. The cut files carry no colour.
