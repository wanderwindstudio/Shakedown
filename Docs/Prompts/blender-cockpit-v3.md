# Blender: Cockpit (v3, grounded watercolour)

Build the ship's cockpit: the room the player looks out of most, and the ship's nose from outside. Work **only** in `~/Shakedown/Art/Blender/Cockpit_v3_Opus/`. Don't change anything elsewhere in the project.

## Read first

1. `~/Shakedown/Docs/DEVLOG.md`, especially **D-32** (the art direction) and D-17 to D-27 (blocks, slots, walls).
2. `~/Shakedown/Art/Concepts/AI-mockups/mockup_cockpit_v3.png`: **the interior target.** Match its layout, proportions, materials and mood.
3. `~/Shakedown/Art/Concepts/AI-mockups/concept_sheet_deltawing.png`: **the exterior target.** The cockpit is the pointed nose of that ship.
4. `~/Shakedown/Art/Concepts/cockpit_sketch_01.png`: Lars' own sketch of the same cockpit (canopy shape, console, chair).
5. `~/Shakedown/Art/Blender/Compartments_Opus/compartments_Opus.py`: your compartment generator. Reuse its wall construction, slot naming and texture setup for the rear wall.

## Art direction: grounded, not cute

The look is **low poly with watercolour textures, but realistic**: real proportions, real materials, grounded light. Avoid the "cutesy" look: no oversized rounded toy shapes, no candy pastels, no chunky cartoon props. Warmth comes from lamps, plants, books and a rug, not from saturated colours.

- **Real-world sizes:** console top about 0.85–0.9 m high, desk surfaces 0.75 m, chair seat 0.48 m, screens like real monitors, door frames sized for a 1.8 m person.
- **Materials read as what they are:** painted metal panels, darker gunmetal frames and ribs, worn edges, floor plates with grates, a fabric rug, leather on the chair. Wear, scratches and paint chips come from the watercolour textures, not geometry.
- **Crisp chamfers, flat-shaded facets.** Big clear shapes plus a few hero details (switch banks, throttle levers, screens). No clutter for its own sake.
- **Palette** (approximate, match the mockup):
  - Warm white panels `#DDD6CC`, light grey panels `#B9B5AE`
  - Gunmetal frames, ribs, canopy struts `#3E3D42`
  - Orange accent and safety stripes `#D9772B`
  - Chair leather `#B4683A`
  - Floor steel `#4B4A4F`, grates darker
  - Lamp light warm amber `#FFC07A`; screens soft green-teal glow
- **Textures:** the watercolour PNGs in `~/Shakedown/Art/Textures/WatercolourTest/`, Box projection, no UV unwrapping, multiplied with the base colours, exactly as in your compartments.

## Size and shape

- **Interior bounding box in blocks (H × W × L): 3 × 3 × 5** (3 m high, 3 m wide, 5 m long). Origin at the centre of the interior floor; the interior spans X −1.5…1.5, Y −2.5…2.5, Z 0…3. Front is +Y.
- **The blocks only measure size.** The cockpit itself does **not** have to be boxy: the front tapers into a faceted nose, and the canopy follows the nose, as in the mockup and the delta-wing sheet. Only the **rear end** must match the compartment system.
- **Rear wall (−Y):** built exactly like a compartment end wall: 0.35 m thick, split into **1 × 1 m slot objects** spanning the full thickness, named `Cockpit_Back_<column>_<row>`, with the same 0.5 m chamfers at the top edges as the compartments. No doorway: Unity cuts it later by removing slots.
- Walls, floor and ceiling elsewhere: 0.35 m thick as in the compartments. They don't need to be slots.
- Keep a clear 1 m walkway from the rear wall to the chair.

## Layout (from the mockup, seen from the rear)

- **Canopy:** a wide centre window flanked by two angled side windows, plus smaller roof windows above, all in gunmetal struts. Glass slightly tinted.
- **Console:** a horseshoe console wrapping from both side walls toward the chair. Three screens below the window line (left: radar rings, centre and largest: ship diagram, right: data readout), switch banks under each, a throttle quadrant with levers on the right.
- **Command chair** centred on a pedestal, orange-brown leather, facing +Y.
- **Left wall:** shelf with books and a trailing plant, a warm table lamp on the counter, a small framed landscape picture, a mug.
- **Right wall:** a cork pinboard with a ship blueprint, notes and photos; a book on the counter.
- **Under the counters:** drawers and cabinets; hard storage cases on the floor, left and right.
- **Floor:** steel plates, grates along both sides, a striped rug down the middle.
- **Ceiling:** central light panel, smaller panels at the sides, pipes along the upper edges.
- **Rear wall:** an orange safety stripe on the frame edges, as in the mockup's foreground.

## Exterior

The pointed nose of the delta-wing ship: faceted, warm-white and light-grey panels, orange accent stripes, small amber running lights, the canopy frames visible from outside. The rear end matches the compartments' outer hull so it joins them.

## Built in vs props

- **Built in** (`Cockpit_...`): shell, canopy, console with screens and switches, counters, shelves, pinboard, ceiling lights, pipes, rear-wall slots.
- **Props** (separate, origin at the centre of the base, keep a 0.05 m gap to walls): `Prop_CommandChair`, `Prop_Rug`, `Prop_StorageCase` (one model, placed several times), `Prop_TableLamp`, `Prop_Plant`, `Prop_Books`, `Prop_Mug`.
- Colliders: simple boxes in `COL_Cockpit`.

## Budget

Built-in cockpit ≤ 12,000 triangles, each prop ≤ 1,500.

## Render setup

Dark space outside the canopy: black-blue sky with sharp stars, a large grey moon and a few asteroids (put these in `RENDER_ONLY`, excluded from export). Warm lamp light inside against cool screen glow, soft bloom, no harsh shadows.

## Deliverables (all in your folder)

1. `cockpit_v3.blend`, `cockpit_v3.fbx` (scale applied, forward −Z, up Y, no cameras, lights or render-only objects)
2. Renders, PNG, 1920 × 1080:
   - `cockpit_v3_mockup_view.png`: **the mockup's camera**, from the rear at eye height (1.7 m), looking at the canopy
   - `cockpit_v3_exterior.png`: three-quarter front view of the nose
   - `cockpit_v3_topdown.png`: top-down cutaway, ceiling hidden
   - `cockpit_v3_closeup.png`: console, screens and throttle at eye height
3. `cockpit_v3.py`: the build script, commented
4. `notes.md`: triangle counts, what you couldn't match and why, what you'd improve next
