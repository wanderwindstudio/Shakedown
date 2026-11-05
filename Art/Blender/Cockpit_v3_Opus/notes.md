# Cockpit v3: notes (Opus)

I built the cockpit with `cockpit_v3.py`, one commented script, run headless in Blender 5.2.3 and rendered with Cycles (40 samples, denoised, soft bloom). To re-run it: open a new Blender file, go to the Scripting tab, paste the script and press Run. It clears the scene and writes everything into this folder.

## Triangle counts (after the correction round)

| Built in | Tris |
|---|---|
| Cockpit_Hull (outer base shell; dark seams between plates) | 218 |
| Cockpit_HullPlates (114 plates, 38 bolt heads, orange bands, running lights) | 2,074 |
| Cockpit_CanopyFrames (raised, chamfered gunmetal struts) | 156 |
| Cockpit_Nose (hood, bumper with recessed headlights, side intakes, sensor plate) | 384 |
| Cockpit_Interior (inner walls, window jambs) | 116 |
| Cockpit_Floor / Cockpit_Ceiling | 4 / 2 |
| Cockpit_Canopy (5 glass panes) | 16 |
| Cockpit_Ribs (rear frame with safety stripes, rib where the roof starts sloping) | 108 |
| Cockpit_Pipes | 216 |
| Cockpit_CeilingLights | 120 |
| Cockpit_Counters (both walls, drawers, cabinets) | 432 |
| Cockpit_Console (horseshoe, 3 screens, switch banks, throttle) | 914 |
| Cockpit_WallFittings (shelf, picture, pinboard) | 132 |
| Cockpit_FloorGrates | 1,104 |
| Cockpit_Back_00_00 … 02_02 (9 rear-wall slots, unchanged) | 132 |
| **Built-in total** | **6,144** (budget 18,000) |

The props are unchanged (counts below).

| Prop | Tris (budget 1,500 each) |
|---|---|
| Prop_CommandChair | 284 |
| Prop_Rug | 108 |
| Prop_StorageCase (3 placements share one mesh) | 96 each |
| Prop_TableLamp | 100 |
| Prop_Books (shelf row) | 108 |
| Prop_Books_Counter (book on the right counter) | 48 |
| Prop_Plant | 308 |
| Prop_Mug | 108 |

## Correction round: what changed

The first exterior read as a van: a tall upright cab with a short stubby hood. The shell is now a long, low wedge after `reference_nose_exterior.png`. The rear-wall slots, interior layout, props, materials and textures are the same.

- **Profile.**
  - From Y −2.5 to −1.0 the room is full height (3.0 m) and still matches the compartments.
  - From Y −1.0 to +0.6 the roof slopes down to 2.2 m. The two roof windows sit on this slope.
  - The windscreen is raked about 42° from horizontal, from Y +0.6, Z 2.2 down to Y +2.0, Z 0.95.
  - A low hood follows: its top is at 0.9 m behind and slopes to 0.64 m. The bumper tip reaches Y +3.47, within the allowed Y +3.5.
- **Cross-section.** The canopy sides are flat "lean" facets. They start at full width at shoulder height and lean inward to a roof 2.2 m wide at the windscreen. At Y −1.0 they only touch the top corner of the compartment wall, so the rear 1.5 m stays exactly compartment-shaped. Below that there's a gunmetal skirt and underside.
- **Surface.**
  - The outer base shell now sits 3.5 cm under the 0.35 m wall line. On top of it are **114 plates** (0.5–1.2 m) with 2 cm seams and bevelled top edges (2.2 cm). About a third of them stand 3.2 cm proud; the rest are 1.6 cm. The tallest plates end exactly at the 0.35 m wall line, so the bounds don't grow.
  - **38 six-sided bolt heads** sit sparsely at plate corners.
  - The **orange livery** is three diagonal bands per side (one on the hood flanks) and chevrons on the roof and the hood top. It's painted over the plate tops, so the bands run across several plates.
  - The **canopy struts** are raised (3 cm), chamfered gunmetal frames around every window, and the window jambs widen toward the outside.
  - The **nose tip** has a gunmetal bumper housing with two amber headlights in 8 cm deep recesses. There are side air intakes (grille in a frame) just behind it and a small sensor plate on top of the hood.
- **Console under the lower windscreen.** The front desk now ends at Y 1.95, under the glass. The three screens are a little smaller, sit lower and lean back 55°. With the chair at Y 0.55 and a seated eye height of about 1.2 m, the screen tops (about 1.14 m) stay below eye level, so the pilot looks over them through the windscreen. The switch banks sit in front of the screens.
- **Other things moved so they stay under the lower roof and lean facets.**
  - The ceiling lights moved to the full-height rear part (Y −2.2 to −1.2).
  - The pipes end before the slope, at Y −1.2.
  - The mid rib now marks where the slope starts, at Y −1.0.
  - The canopy rib was removed; the struts take over its job.
  - The shelf, plant and pinboard moved back by about 0.4 m.
  - The colliders follow the new shape, plus a new `COL_Hood`.
- **Renders.** There's a new `cockpit_v3_side.png` (orthographic side view, to check the silhouette). The exterior is now a three-quarter view from slightly above, with the nose pointing toward the lower left, like the reference.
- **How I checked it.** I rendered, compared the result with the reference and fixed the biggest difference, three times:
  1. Long sliver plates stuck out of the hull (duplicate clip points caused mitre spikes). I fixed them, and the canopy sides got plates instead of bare gunmetal.
  2. The orange looked like a checkerboard, then like hazard stripes with black gaps. Now it's painted as bands over whole plates.
  3. The dark skirt was too tall; it now covers only the lower chamfer and the underside.

## How it's built

- **The room.** The room is one convex shape made of flat planes (see the correction round above for the profile).
- **Outer hull.** Every room surface is pushed 0.35 m outward, plus the compartments' 0.5 m lower chamfers. The walls are therefore 0.35 m everywhere, and the rear end is exactly a compartment's outer hull.
- **Rear wall.** It uses the same mitred construction as `compartments_Opus.py`. It's made of nine closed 1 × 1 m slots named `Cockpit_Back_<column>_<row>`. Columns count from the left as seen from inside, facing the rear wall. The top corner slots have the 0.5 m chamfer cut off. The script checked all nine for open edges and found none.
- **Canopy.** Five window openings are cut through the wall: the windscreen, two side windows on the lean facets and two roof windows on the sloping roof, split by a centre strut.
- **Exterior.** Plated hull, livery, nose and struts: see the correction round above.
- **Walkway.** It's 1.9 m wide between the counters and 1.62 m between the storage cases. From the rear wall to the chair back is 2.65 m.
- **Real-world heights.** Counter and console tops are at 0.90 m, the chair seat at 0.48 m. The main screen is about 0.70 × 0.44 m (a 32″ monitor), the side screens about 0.46 × 0.34 m.
- **Textures.** The watercolour PNGs use Box projection, multiplied with the brief's palette. The screens, the landscape picture and the pinboard prints are small images the script generates, packed into the `.blend`, on flat cards with simple UVs.
- **Export.** The FBX contains everything built in, the props and the 12 `COL_Cockpit` boxes. It has no cameras, lights or `RENDER_ONLY` objects (moon, asteroids). The space background is part of the world shader, so it never reaches the FBX.

## What I couldn't match, and why

- **No D-32 in the devlog.** `DEVLOG.md` stops at D-31, so I followed the art direction written in the prompt.
- **Room depth.** The mockup's camera looks into a deeper, wider room than 3 × 5 m. In our 5 m room the console and canopy sit close to the chair, so the canopy fills less of the frame and the side walls dominate.
- **Canopy shape.** The interior mockup shows a near-upright centre window under a 3 m roof. The corrected profile has a sloping roof and a windscreen raked about 42°. From the rear doorway the canopy now reads as a low, slanted glass roof over the console, and the struts look heavier than in the mockup.
- **Hood length.** The reference hood is longer than ours. The windscreen has to come down to Y +2.0 just above the console, and the nose may only reach Y +3.5, so the hood is about 0.9 m long plus the bumper.
- **Exterior detail.** The reference's weathering, rust streaks and small hatches aren't modelled. The wear comes only from the watercolour texture. The bolts are sparse, as asked.
- **Detail density.** Mockup details such as cables, hoses, cable trays and stickers aren't modelled. The brief says "no clutter for its own sake", and wear should live in the textures.
- **Moon and asteroids.** They're smaller in frame than in the mockup, and the Milky Way band is very faint. D-30 asks for realistic, desaturated space, so I kept it subtle.
- **The look.** Multiplying the watercolour textures mutes the palette slightly. The worn edges and scratches of the mockup show only as soft texture variation.

## What I'd improve next

1. **Longer hood.** If the nose may grow beyond Y +3.5 (or the windscreen may start lower), a 1.5–2 m hood would get much closer to the reference's long wedge.
2. **Hero details.** Add a cable tray along the console underside, a small overhead switch panel above the centre window, and grab handles at the canopy frames.
3. **Exterior.** Line the plate seams up with the compartments' 1 m slot rhythm at the rear joint, and add a few hatches and small antennas on the hood.
4. **Chair.** Add a swivel indication and seat belts. Make the armrests slimmer.
5. **Unity check.** Test the import: −Z forward, glass transparency, removing the rear-wall slots, and turning the `COL_` boxes into BoxColliders.
