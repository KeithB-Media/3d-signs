# Milwaukee-style tool sign – 24" × 7" stacked laser-cut sign

A Christmas gift sign: heavy, slanted white block letters on a red panel, with a black outline
and the "NOTHING BUT HEAVY DUTY" tagline. **For personal use only.** The Milwaukee name is a
trademark of Milwaukee Electric Tool, so don't sell signs made from these files.

The lettering is drawn in `generate.py` in a similar heavy, slanted style. It is not a copy of
Milwaukee's official logo artwork.

![front](renders/render_front.png)

| Angle | Exploded |
|---|---|
| ![angle](renders/render_angle.png) | ![exploded](renders/render_exploded.png) |

![layers](renders/layer_sheet.png)

## Cut files (`svg/`)

All files are 24 in × 7 in on the same origin, so every layer lines up. They contain cut lines only
(red hairline, no fill).

| # | File | Paint | Stock | Pieces | What it is |
|---|------|-------|-------|--------|------------|
| 1 | `layer1_base_black.svg` | Black | 1/4" | 1 | 24" × 7" backer, 1/2" corner radius; shows as a 0.3" black rim |
| 2 | `layer2_red_panel.svg` | Red | 1/8" | 1 | red panel |
| 3 | `layer3_black_outline.svg` | Black | 1/8" | 1 | black outline behind MILWAUKEE (0.16" all round, one piece) |
| 4 | `layer4_white_letters.svg` | White | 1/8" | 9 | the MILWAUKEE letters (2.6" tall) |
| 5 | `layer5_white_tagline.svg` | White | 1/8" | 19 | tagline letters (0.62" tall), glued straight onto the red |

Total thickness is about 5/8".

Other files:
* `preview_flat.svg`: full-colour flat preview.
* `placement_template.svg`: every layer's outline in a different colour. Print it at actual size
  (tiled) to place the letters during glue-up.

## Build notes
* Paint each layer, edges included, before glue-up.
* Glue order: 1 → 2 (centred, even black rim), then 3. The outline is one piece, so it's easy to
  place. Then drop each white letter into its outline. Glue the tagline letters onto the red under
  the wordmark, using the template.
* The tagline is the fiddly part: 19 small letters. Use hold-downs or tabs when cutting it. To skip
  it, set `TAGLINE = False` in `generate.py`.
* Kerf is not compensated. That's fine for stacked art.
* Add a keyhole hanger or a French cleat on the back of layer 1.

## Changing it
Everything is set at the top of `generate.py`: sign size (`W`, `H`), slant, outline width,
tagline text and size. The wordmark scales itself to fit the width. To personalise it, change
`TAG_TEXT`, for example to `"DAD'S GARAGE"`.

```
pip install shapely fonttools
python3 generate.py   # writes svg/
node render.js        # writes renders/ (needs Playwright + Chromium)
```
The tagline uses Inter Black Italic (`TAG_FONT`). Point it at any .otf/.ttf you have.
