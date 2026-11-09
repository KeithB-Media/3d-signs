# Amtrak P42 (GE Genesis) in Phase VI – 16" × 23" stacked MDF sign with working lights

A head-on relief of GE Genesis P42DC #108 in Amtrak's Phase VI colours (blue body,
black window mask with a red band around it, white logo), cut from nine layers of 1/8" MDF and stacked.
It's built the same way as the IAIS 510 sign: every layer is cut, painted, then glued
from 1 (back) to 9 (front). The two headlights and two ditch lights are 5 mm LEDs that
run on a battery holder hidden in a pocket in the back.

| Unlit | Lit |
|---|---|
| ![front](renders/render_front.png) | ![lit](renders/render_lit.png) |

| Angle | Exploded |
|---|---|
| ![angle](renders/render_angle.png) | ![exploded](renders/render_exploded.png) |

![layers](renders/layer_sheet.png)

## Cut files (`svg/`)

All files are 16.5" × 23.5" (the sign plus a 1/4" margin) and share the same origin, so
every layer lines up. They contain cut lines only (red hairline, no fill). The sign is
16" wide × 23" tall (about 1:7.5 scale). It fits a 24" × 18" laser bed if you rotate it.

| # | File | Paint | Pieces | What it is |
|---|------|-------|--------|------------|
| 1 | `layer1_backer.svg` | black | 1 | backer: battery pocket + 2 keyhole hangers |
| 2 | `layer2_core.svg` | black | 1 | core: room for the hanging-screw heads |
| 3 | `layer3_core.svg` | black | 1 | same as layer 2 |
| 4 | `layer4_core_wiring.svg` | black | 1 | core: wire channels |
| 5 | `layer5_glass_wiring.svg` | dark glass (top), black edges | 1 | wire channels; its top shows through the windshield |
| 6 | `layer6_body.svg` | blue body; dark grey plow + steps; grey horns + antenna | 6 | carbody with windshield cut out, plow backing, corner steps, roof horns, antenna |
| 7 | `layer7_nose_mask.svg` | blue, red, black, dark grey | 4 | nose + skirt, red band, black window mask with wipers, ribbed plow face |
| 8 | `layer8_details.svg` | black, white, grey | 35 | headlight bezel, ditch light housings, logo, road number, anticlimber, coupler, MU + HEP receptacles, air hoses, lever brackets, grab irons |
| 9 | `layer9_front_gear.svg` | black, grey, chrome | 18 | lens rings, MU jumper cable, HEP jumper cables, receptacle lids, glad hands, uncoupling lever |
| – | `back_cover.svg` | black | 1 | battery pocket cover (screws to the back, with a slot to reach the switch) |

The stack is 1-1/8" thick. Each piece in a layer is cut separately, so pieces with different
paints (for example the blue body and the grey plow on layer 6) come apart.

Other files:
* `preview_flat.svg` – full-colour flat preview.
* `placement_template.svg` – every layer's outline in its own colour. Print it at 1:1
  (actual size, tiled) to position the small layer 8 and 9 parts (logo letters, hoses, cables) during glue-up.

## Lights and battery

* **Battery pocket**: 2.50" × 1.95", cut through layers 1–5 (0.625" deep), behind the nose.
  It's sized for a 3×AAA holder with an on/off switch. **Measure your holder** and change
  `POCKET` in `generate.py` if it differs.
* **Wire channels**: 0.32" wide, cut through layers 4 and 5. They run from the pocket to
  each light. Layers 1–3 close them from the back, and layer 6 covers them from the front.
* **LEDs**: four 5 mm warm-white LEDs. The holes in layers 6–8 are 0.25", so each LED goes
  in from the front after glue-up. Its rim sits inside the chrome ring on layer 9.
* **Wiring**: wire all four LEDs in parallel, each with its own 100 Ω resistor
  (4.5 V, about 14 mA each). Solder the leads and resistor to two thin wires first
  (heat-shrink the joints). Then feed the wires down the LED hole and along the channel
  to the pocket. Do this before you glue the LED in, and fit the wires before gluing
  layer 6 if you want to avoid fishing them through later.
* **Hanging**: layer 1 has two keyhole slots. Layers 2 and 3 leave room behind them for
  the screw heads. Drive two screws 9.2" apart into the wall, leaving the heads 1/8" out.

## Build notes
* Paint each piece before glue-up, including the edges: the edges of the raised layers show
  from an angle. Layers 1–5 only show their edges, so paint those black. Paint the top of
  layer 5 dark glass grey: it shows through the windshield.
* Glue order: 1 → 5 (all the same outline), check the wire channels are clear, then 6,
  7, 8 and 9. Use the placement template for the small layer 8 parts.
* The wipers are part of the black window mask and joined at both ends, so they don't snap.

## Front-end detail
Everything between the anticlimber and the plow, as on the real locomotive:
* **Coupler**: draft gear and an E-type head with the knuckle gap and lock-lift hole.
* **MU receptacles** (two each side of the coupler) with a **MU jumper cable** draped
  across the coupler between the inner pair, plug heads on the receptacles.
* **HEP (head-end power) receptacles** further out, each with its jumper stowed in a loop
  to the dummy socket beside it.
* **Air hoses** (brake pipe and main reservoir, two each side) hanging from the
  anticlimber, ending in **glad hands**.
* **Uncoupling lever** across the top of the plow on the left, on two brackets.
* Receptacle lids, grab irons beside the steps and on the nose, and a ribbed plow.

Layer 9 parts sit on layer 8 parts: the cables end on the receptacles and the lever rests
on its brackets and on the air hoses where it crosses them. Glue the receptacles and hoses
first, then lay the cables and lever on top using the placement template.

## Phase VI livery and logo
* Body, nose and skirt: Amtrak blue. Window surround: black. A red band wraps around the
  bottom and lower sides of the black surround. Plow, steps and undercarriage: dark grey.
* Sources describe P42 #108's Phase VI front as "a mostly blue body with red and black
  around the windshield". They don't give the exact shapes, so the red band and mask are
  my interpretation. Check a photo of #108 and adjust `window_mask()` and `red_band()`
  in `generate.py` if needed.
* The logo is cut from MDF and painted white: three sweeping stripes for the Travel Mark,
  then the AMTRAK wordmark (set in Liberation Sans Bold), centred on the nose above the
  headlight. The Travel Mark is an **approximation** drawn to be cuttable (no stripe narrower
  than 0.1"). If you have the official artwork, swap it in `travel_mark()`.
  The Amtrak logo is a trademark: fine for a personal sign, but get permission before
  selling these (the IAIS sign was made with the railroad's permission).
* The road number (`ROAD_NUMBER`, default 108) is cut in white below the headlight.
  Change it to any number and rerun.
* Change `COLORS` to preview other schemes. The cut files stay the same.
* Kerf is not compensated. Pieces come out a few thousandths undersize, which is fine for
  stacked art. If your LEDs fit loosely, a dab of hot glue holds them.
* The shape was drawn from general P42 references, not from factory drawings: the
  "home plate" headlight on the nose, ditch lights low on the front, a plow,
  corner steps, and cab sides that lean inward. Compare it with a photo of the unit
  you want, and adjust the coordinates in `generate.py` if needed.

## Regenerating
```
pip install shapely numpy fonttools
python3 generate.py        # writes svg/
node render.js             # writes renders/ (needs Playwright + Chromium)
```
