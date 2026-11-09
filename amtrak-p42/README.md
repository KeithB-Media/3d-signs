# Amtrak P42 (GE Genesis) in Phase V – 16" × 21" stacked MDF sign with working lights

A head-on relief of GE Genesis P42DC #82 in Amtrak Phase V, cut from nine layers of 1/8"
MDF and stacked. It's built the same way as the IAIS 510 sign: every layer is cut,
painted, then glued from 1 (back) to 9 (front). The headlights, ditch lights and red
rear lights are 5 mm LEDs that run on a battery holder hidden in a pocket in the back.

| Unlit | Lit |
|---|---|
| ![front](renders/render_front.png) | ![lit](renders/render_lit.png) |

| Angle | Exploded |
|---|---|
| ![angle](renders/render_angle.png) | ![exploded](renders/render_exploded.png) |

![layers](renders/layer_sheet.png)

## What's on the front
The layout follows a head-on photo of a Phase V P42, top to bottom:

* **Roof**: domed, curving from the cab sides up to the crown, with the horn cluster
  and radio antenna on top.
* **Windshield**: two wide, short panes with black gaskets and pantograph wipers parked
  **standing up along the outer edge** of each pane, leaning in with the cab side. Each
  wiper has a blade (layer 7, joined to the gasket at the bottom and the top), and on
  layer 8 a pivot hub at the bottom outer corner, a tapered arm, a thinner pantograph link
  with its own pivot, a clip where the arm grabs the blade and a cap on the blade tip. A
  grey nut sits on each hub (layer 9). Close-up: `renders/detail_wipers.png`.
* **Number board** on the nose just under the windshield: black board (layer 8) with
  white digits on it (layer 9). `ROAD_NUMBER`, default 82, or `""` for a blank board.
* **Travelmark**: AMTRAK wordmark over three sweeping stripes, in white on the blue.
* **Light bar**: twin round **headlights** set into a recess in the nose that comes to a
  point at the bottom (the recess is cut out of layer 7, so the lamps sit one layer in, with a black floor). A **red light**
  either side.
* **Blue/silver line**: a shallow V across the nose, lowest just under the headlights,
  sweeping up at the cab corners.
* **Ditch lights** on the silver. Below each one is a **connector box**: a recess cut
  out of the nose (black floor on layer 6) holding two covered connectors. Each connector
  is a square plate (layer 7) with a round cap (layer 8): **blue on the outside, black on
  the inside**. Under the box, a small slot holds a **yellow plug** with a **black cable**
  that runs down and disappears behind the plow tip.
* **Pilot opening**: a cut-out in the bottom middle of the silver body (black floor on
  layer 6) over the coupler, with the dark underframe showing above the plow.
  * **Coupler**: an E-type head seen end-on, in rusty brown: the head with its guard arm,
    the knuckle beside it and the slot between them, with a knuckle pin cap. It sits in
    the plow notch with **its top level with the plow tips**. A lock-lift rod stands on top,
    and the **uncoupling lever** runs from it out to the left and down behind the plow wing.
  * **MU receptacle** each side of the coupler head. The **MU jumper** droops across the
    coupler face between them, with light-grey plug heads.
  * **Air hoses**, three each side, further out: they hang from the top of the opening and
    run down **behind the plow wings**, so only the part above each wing shows.
* **Skirt** (anthracite, layer 6) behind the plow, running out to both edges of the
  body with chamfered bottom corners.
* **Plow**, near-black, in front of everything: 15" wide across the tips, 10" across the
  bottom, 4.65" tall:
  1. base (layer 6)
  2. the plow plate (layer 7): wide bottom, angled lower corners, **tall outer tips that
     reach up to the bottom of the body**, top edge sloping down to a notch in the middle
     for the coupler
  3. a **closed door on each wing** and a reinforcing plate across the bottom centre
     (layer 8)
  4. a latch and two hinges on each door (layer 9)

  The **white grab handles** are mounted on top of each wing: a rail standing above the
  wing's top edge with its legs down onto it (layer 7, beside the plow plate).
* **Red sill stripe** at the front corners, either side of the plow.

## Cut files (`svg/`)
All files are 16.5" × 21.6" (the sign plus a 1/4" margin) and share the same origin, so
every layer lines up. They contain cut lines only (red hairline, no fill). The sign is
16" wide × 21.1" tall from the bottom of the plow to the top of the horns (about 1:7.5
scale), 1-1/8" thick. It fits a 24" × 18" laser bed if you rotate it.

| # | File | What it is |
|---|------|------------|
| 1 | `layer01_backer.svg` | backer: battery pocket + 2 keyhole hangers |
| 2 | `layer02_core.svg` | core: room for the hanging-screw heads |
| 3 | `layer03_core.svg` | same as layer 2 |
| 4 | `layer04_core_wiring.svg` | core: wire channels |
| 5 | `layer05_glass_wiring.svg` | wire channels; its top shows through the windshield |
| 6 | `layer06_body.svg` | carbody (blue + silver, windshield and pilot opening cut out), headlight + connector recess floors, pilot opening + underframe floor, plow base, skirt, horns, antenna |
| 7 | `layer07_nose.svg` | raised nose (blue + silver) with headlight and connector recesses, headlight rings, connector plates, gaskets with wipers, coupler head, uncoupling lever, MU receptacles, air hoses, corner cables + yellow plugs, sill stripe, white plow handles, plow plate |
| 8 | `layer08_lights_logo.svg` | red light + ditch light housings, number board, Travelmark, connector caps, MU plug heads, jumper spacer, knuckle pin, lift rod, nose grab irons, plow doors + centre plate |
| 9 | `layer09_front_gear.svg` | ditch light rings, red light rings, number digits, MU jumper, door latches + hinges |
| – | `back_cover.svg` | battery pocket cover (screws to the back, slot for the switch) |

The stack is 1-1/8" thick. Each piece is cut on its own, so where two paint colours meet
(for example blue and silver on layers 6 and 7) the piece is cut in two.
`generate.py` checks every layer: no pieces overlap, and every part has at least a
quarter of its area glued to the layer below.

Other files:
* `preview_flat.svg` – full-colour flat preview.
* `placement_template.svg` – every layer's outline in its own colour. Print it at 1:1
  (actual size, tiled) to place the small parts (logo, digits, hoses, jumpers, handles) during glue-up.

## Paint (Phase V, from Amtrak's livery guide)
| Colour | Preview hex | Pieces |
|---|---|---|
| Amtrak Blue | `#1f4e79` | top of the carbody and nose (above the wave line) |
| Platinum Mist | `#cdd1d4` | lower carbody and nose |
| Near-black | `#26292d` | the four plow layers (darker than the real one so the plow stands out) |
| Anthracite Gray | `#4a4f52` | skirt behind the plow |
| Amtrak Red | `#d9442f` | red light rings, sill stripe at the corners |
| Black | | gaskets, wipers, number board, headlight and connector recess floors, pilot opening + underframe, light housings, inner connector covers, corner cables, receptacles, hoses, jumper, nose grab irons |
| White | | Travelmark, number digits, plow grab handles |
| Grey | | uncoupling lever, lift rod, door latches + hinges, horns, antenna |
| Rusty brown | `#6e5a4c` | coupler head, knuckle pin |
| Light grey | | MU plug heads |
| Chrome/silver | | headlight and ditch light rings |
| Bright blue | `#2f7fd0` | outer connector covers |
| Yellow | `#e3b53c` | plugs on the corner cables |

## Lights and battery
* **Six 5 mm LEDs**: two warm-white headlights, two warm-white ditch lights and two red
  rear lights. The holes are 0.25", so each LED goes in from the front after glue-up.
  Headlight and ditch light rings are 1" across; the headlight rings sit in the recess on
  layer 7, the ditch light rings on layer 9.
* **Battery pocket**: 2.50" × 1.95", cut through layers 1–5 (0.625" deep), behind the nose.
  It's sized for a 3×AAA holder with an on/off switch. **Measure your holder** and change
  `POCKET` in `generate.py` if it differs.
* **Wire channels** (0.32" wide, through layers 4 and 5): one runs straight up from the
  pocket to the light bar, then across to the headlights and red lights. Two more run
  sideways to the ditch lights. Layers 1–3 close them from the back, layer 6 from the front.
* **Wiring**: each LED gets its own resistor: 100 Ω for white, 150 Ω for red (4.5 V,
  about 15 mA each). On a real locomotive the red lights are on at the rear end and the
  white lights at the front. To copy that, put a small slide switch (SPDT) in the cover's
  slot: one side feeds the four white LEDs, the other the two red ones. Run a common
  negative wire to all six. Solder each LED and its resistor to thin wire before you feed
  it down the LED hole and along the channel, and fit the wires before you glue on layer 6.
* **Hanging**: layer 1 has two keyhole slots. Layers 2 and 3 leave room behind them for
  the screw heads. Drive two screws 9.2" apart into the wall, leaving the heads 1/8" out.

## Build notes
* Paint each piece before glue-up, including the edges: the edges of the raised layers show
  from an angle. Layers 1–5 only show their edges, so paint those black. Paint the top of
  layer 5 dark glass grey: it shows through the windshield.
* Glue order: 1 → 5 (all the same outline), check the wire channels are clear, then 6, 7,
  8 and 9. On layer 7, glue the coupler, lever, receptacles and hoses before the plow
  plate. The MU jumper (layer 9) rests on its plug heads and a small hidden spacer on
  the coupler (layer 8).
* The headlight and connector recess floors and the pilot opening floor (layer 6) are cut
  as separate pieces: paint them black before gluing layer 7 over them.
* The wipers are joined to the gaskets at both ends, so they don't snap.
* The smallest parts are the Travelmark stripes and letters (about 0.1" strokes). Cut them
  from good MDF, or from 1/8" hardboard or birch ply, for clean edges.
* Kerf is not compensated. Pieces come out a few thousandths undersize, which is fine for
  stacked art. If your LEDs fit loosely, a dab of hot glue holds them.
* The Travelmark is an approximation drawn to be cuttable. Swap in the official artwork
  in `travelmark()` if you have it. The Amtrak name and logo are trademarks; this sign is
  for personal use.
* The shape was drawn from a head-on photo and general P42 references, not from factory
  drawings. Every part is a set of coordinates in `generate.py`, so it's easy to adjust.

## Regenerating
```
pip install shapely numpy fonttools
python3 generate.py        # writes svg/
node render.js             # writes renders/ (needs Playwright + Chromium)
```
