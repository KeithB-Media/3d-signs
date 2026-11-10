# Guilford Rail System – stacked laser-cut signs

Two 14" signs in Guilford gray, orange and white, built the same way as the Susquehanna S
sign. Each layer is cut and painted one colour, then the layers are stacked and glued from
the bottom up.

* **Round** (this page, `svg/`): an 8-layer disc with the G over an orange-and-white stripe.
* **Square** (`square/`): a 5-layer square with the G, "Guilford Rail System" and the orange
  bar, adapted from the wide logo. See [Square version](#square-version-square).

The G with its arrow is traced from the logo in `reference/guilford_logo.jpg` by
`trace_g.py`, so its shape matches the logo exactly. Both signs use the logo's colours.

## Round version

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
| 7 | `layer7_gray_g_outline.svg` | Gray | 1/8" | gray outline of the G (0.22" border, sharp arrow corners) |
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

## Square version (`square/`)

![square](square/renders/render_front.png)

| Angle | Exploded |
|---|---|
| ![angle](square/renders/render_angle.png) | ![exploded](square/renders/render_exploded.png) |

All files are 14 in × 14 in on the same centre.

| # | File | Paint | Suggested stock | What it is |
|---|------|-------|-----------------|------------|
| 1 | `square/svg/layer1_base_gray.svg` | Gray | 1/4" | 14.00" square (0.3" corners) – gray border and backer |
| 2 | `square/svg/layer2_white_pinstripe.svg` | White | 1/8" | 13.60" square – white pinstripe |
| 3 | `square/svg/layer3_gray_field.svg` | Gray | 1/8" | 13.20" square – gray field |
| 4 | `square/svg/layer4_orange_bar.svg` | Orange | 1/8" | orange bar, edge to edge across the field |
| 5 | `square/svg/layer5_white_g_lettering.svg` | White | 1/8" | the G and "Guilford Rail System" (21 pieces) |

* With this stock the sign is about 3/4" thick in total.
* The lettering is Liberation Sans Bold, which has the same letter widths as the Helvetica
  Bold in the logo. The capitals are 0.78" tall, and the strokes are about 0.13" wide.
* Layer 5 is the G plus 20 separate pieces: the letters, and the dots of the i's
  as their own pieces. Glue it last, using `square/svg/placement_template.svg` printed at 1:1.
  Mark the baseline on the field with a light pencil line, or lay the cut-out
  sheet of layer 5 over the sign as a stencil. The pieces drop back into the holes they were cut from.

## Regenerating
```
pip install shapely numpy fonttools
python3 generate.py          # round  -> svg/
python3 generate_square.py   # square -> square/svg/
node render.js               # round renders  -> renders/
node render.js square        # square renders -> square/renders/
```
* `G_HEIGHT` / `G_CENTER` (round) and `G_HEIGHT`, the gaps and `BAR_H` (square) set the layout.
  `STRIPE_*` / `PIN` set the round sign's stripes.
* `COLORS` in `common.py` is used for the previews only. The cut files carry no colour.
* To re-trace the G from another image, run
  `pip install pillow scikit-image scipy`, then `python3 trace_g.py image.jpg`.
