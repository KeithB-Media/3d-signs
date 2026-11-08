# Workbench: Bambu Lab R1 laser + Automatic Conveyor Feeder

![drawing](workbench.png)

(`workbench.svg` holds the same drawing at full scale. Run `python3 drawing.py` to regenerate it.)

## Design basis

| Item | Spec used | Source |
|---|---|---|
| R1 footprint (standalone or with Riser Base) | 940 W × 660 D mm (37 × 26 in), lid open | Bambu Lab |
| Recommended clearance | 100 mm (4 in) left, right, rear and top → 1140 × 860 mm | Bambu Lab |
| Height with Riser Base, lid open | 850 mm (33.5 in); 950 mm with top clearance | Bambu Lab |
| Conveyor room | Riser Base footprint plus **(stock − 400 mm) in front** and **(stock − 550 mm) behind** | Bambu Lab |
| Conveyor Feeder | ~117 × 1234 × 756 mm, 9.2 kg. Needs the Riser Base. Rail runs 450–1500 mm, extensions reach 3000 mm | Swing Design listing |
| Feed direction | Long stock comes out the **front and back** of the machine | MatterHackers |

What follows from these specs:

* **Top height is 28 in**, which is lower than a normal 36 in bench. The riser adds about 8 in and the open lid stands about 33.5 in, so the lid top lands around 61 in. A lower bench keeps the bed easy to reach and the lid easy to see over.
* **Open front and back.** The bench has no back panel or rear stretchers above the shelf, so stock and conveyor rails can pass straight through.
* **No wings.** Bambu only asks for open space in front and behind for the stock to hang out into. The conveyor's guide rails carry the stock, and their supports sit close to the machine, so they land on the 36 in top. The machine is 26 in deep, which leaves about 5 in of top in front and 5 in behind.
* **Top is 45 × 36 in, the narrowest that works.** That is the 37 in machine plus Bambu's 4 in (100 mm) side clearance on each side. The R1's crossflow ventilation pulls air in one side and exhausts out the other, so don't block those 4 in. The exhaust hose can hang past the edge of the bench.
* **The lower shelf** holds sheet stock flat (24 × 12 in / 600 × 300 mm sheets fit with room to spare).
* **Leveling feet, not casters.** The laser wants to stay level and still. If you need to move the bench, use locking casters rated at least 150 lb each and subtract their height from the leg length.

## Lumber to buy

| Qty | Material | Notes |
|---|---|---|
| 1 | 4×4 × 10 ft (or 2 × 8 ft) | legs |
| 5 | 2×4 × 8 ft | frame and joists (most of the last board is spare) |
| 1 | 3/4 in plywood, 4×8, sanded/cabinet grade (birch or similar) | top and lower shelf |

## Cut list

Actual sizes: 4×4 = 3½ × 3½, 2×4 = 1½ × 3½, ply = ¾.

| Part | Qty | Material | Length / size | Where |
|---|---|---|---|---|
| Legs | 4 | 4×4 | 26¼ in | corners |
| Top long aprons (front/back) | 2 | 2×4 | 42 in | top frame, on edge |
| Top short aprons (sides) | 2 | 2×4 | 27 in | between the long aprons |
| Top joists | 2 | 2×4 | 27 in | inside the top frame, ~14 in on center |
| Lower long aprons | 2 | 2×4 | 42 in | shelf frame, bottom edge 5 in off the floor |
| Lower short aprons | 2 | 2×4 | 27 in | shelf frame |
| Lower joist | 1 | 2×4 | 27 in | center of the shelf frame |
| A — Top | 1 | ¾ ply | 45 × 36 in | overhangs the frame 1½ in at the sides, 3 in front and back |
| B — Lower shelf | 1 | ¾ ply | 42 × 30 in | notch 3½ × 3½ at each corner for the legs |

**How the 2×4s come out of 8 ft boards (96 in):**

* Boards 1–2: 42 + 42 each (the 4 long aprons)
* Boards 3–4: 27 + 27 + 27 each (6 short pieces)
* Board 5: 27 (the last short piece), the rest is spare

**Legs:** cut 4 × 26¼ from the 10 ft 4×4. With two 8 ft posts, cut 2 legs from each.

**Plywood:** the layout is in the drawing. One sheet gives both the top and the shelf, plus offcuts of 45 × 12 and 42 × 18 in.

## Hardware

| Qty | Item |
|---|---|
| 4 | Leveling feet, 3/8-16 thread, with 4 tee nuts or threaded inserts |
| ~32 | Structural wood screws, ¼ × 3⅛ in (GRK RSS / Spax PowerLag): aprons to legs |
| ~25 | 3 in construction screws: joists |
| ~40 | 1⅝ in wood screws: plywood to frame, every 8 in |
| — | Wood glue, sandpaper, finish (2–3 coats water-based poly, or paint) |

## Assembly

1. **Legs.** Drill the bottom of each leg for the tee nut or insert and install the leveling feet. Set each foot to stick out about 1 in.
2. **Top frame.** Screw the two 42 in aprons over the outside faces of the legs, flush with the leg tops, using 2 structural screws per leg. Fit the 27 in side aprons between them, also screwed into the legs. Add the 2 joists at about 14 in spacing, 2 × 3 in screws through each end.
3. **Shelf frame.** Repeat step 2 with the lower aprons and the center joist. Put the bottom edge of the aprons 4 in above the leg bottoms, which is 5 in off the floor with the feet set.
4. **Check square.** Measure the diagonals before the plywood goes on. Then glue and screw shelf B onto the lower frame. The plywood stops the frame from racking.
5. **Top.** Center top A with a 1½ in overhang at each side and 3 in front and back. Glue it and screw it down every 8 in. Countersink the screws so the R1 feet and stock slide smoothly.
6. **Finish.** Ease the edges, then apply finish (2–3 coats of water-based poly, or paint).
7. **Level.** Put the bench in place, level it with the feet, then set the R1 on its riser centered on the top.

## Placement and use

* **Floor footprint** is just the bench: 45 × 36 in. Leave 4 in on the sides for airflow, as Bambu specifies.
* **Room depth for long stock**, front to back, kept clear at feed height (Bambu's formula):

  | Stock length | In front | Behind | Total incl. 660 mm machine |
  |---|---|---|---|
  | 1500 mm (59 in) | 1100 mm | 950 mm | ~2.7 m (107 in) |
  | 2000 mm (79 in) | 1600 mm | 1450 mm | ~3.7 m (146 in) |
  | 3000 mm (118 in) | 2600 mm | 2450 mm | ~5.7 m (225 in) |

  The stock hangs out at feed height, which is above the 28 in bench top, so it clears chairs and low furniture. Walls, doors and shelves count, though.
* Don't put the back of the bench against a wall if you use the conveyor. Turning the bench sideways along a wall works.
* Run the exhaust hose to the side and out a window or wall vent. Keep the hose short, with few bends.
* With the Riser Base or conveyor installed, the R1 is **no longer fully enclosed (Class 4)**. Wear CO2-rated laser eyewear and keep people away from the open front and back slots.

## Verify before cutting

* **Where the guide-rail supports stand.** The design assumes they land within the 36 in top. If they reach farther out, make the top deeper. The plywood sheet allows up to 48 in deep: lengthen the 27 in side aprons and joists by the same amount, and the top and shelf too.
* **Actual R1 and riser weights.** The frame is good for several hundred pounds.
