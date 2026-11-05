# Blender: Crew quarters section (comparison build, v2)

You are one of two AI agents building this same room independently from this exact prompt. Lars compares both results and picks a winner, so **follow the spec closely** and **name everything with your own suffix**: Claude Opus → `Opus`, GPT Sol → `Sol`.

Work **only** in `~/Shakedown/Art/Blender/Quarters_<Suffix>/`. Don't read, change or delete anything in the other agent's folder or elsewhere in the project.

## Read first

1. `~/Shakedown/Docs/Specs/section-standard.md`: **binding rules** for dimensions, cross-section, rib frames, pipes, doorways, naming, style, palette, textures and export.
2. `~/Shakedown/Art/Concepts/AI-mockups/mockup_quarters_v2.png`: **the target picture.** Match its layout, shapes, palette and mood as closely as 3D allows.
3. `~/Shakedown/Art/Concepts/AI-mockups/mockup_exterior.png`: hull style for the outside.

## How to work

With a live Blender connection, build directly and check your own renders. Without one, write one commented `bpy` script that Lars runs in Blender's Scripting tab. One solid build plus one round of fixes.

## This section

- **Size: 2 × 1 units (8 m along Y × 4 m × 3.5 m).** Doorways at **both** short ends.
- Viewed from the rear doorway, looking toward +Y (this is the mockup's camera):
  - **Left wall:** **bunk beds**, two berths, each in a chamfered niche with a small reading light, sage mattress, cream pillow, ochre blanket. An ochre ladder at the foot end. Storage drawers under the lower bunk.
  - **Far end, left of centre:** two tall **sage lockers** with vent slots.
  - **Far end, right of centre:** a small **wash niche** (sink, tap, soap dispenser) with a light above, a wall hook with a hanging jacket, two small pictures taped to the wall.
  - **Right wall:** a **dinette**: two benches with sage cushions facing each other and a wall-mounted table between them. A large **round porthole** with a bolted ring above the table. On the table: a mug on a coaster and a closed book. A potted trailing plant in a wall holder next to the porthole.
  - **Upper walls, both sides:** overhead cabinets with inset handles; a warm light strip under the right-hand cabinets.
  - **Ceiling:** one central warm light panel. Pipes along the upper right chamfer.
- The far doorway may sit behind the lockers and wash niche only if the 1 m walkway stays clear. If the mockup's arrangement conflicts with the doorway standard, **the standard wins**: keep the doorway centred and arrange lockers and wash niche on either side of it.

## Built in vs props

- **Built in** (`Quarters_<Suffix>_...`): everything in the section standard, plus the bunk niches, overhead cabinets, wash niche, porthole and lights.
- **Props:** `Prop_Lockers_<Suffix>`, `Prop_Dinette_<Suffix>` (benches and table), `Prop_Plant_<Suffix>`, `Prop_Mug_<Suffix>`, `Prop_Book_<Suffix>`, `Prop_Jacket_<Suffix>`, `Prop_Pictures_<Suffix>`. Bedding (mattress, pillow, blanket) may stay with the built-in bunks.

## Deliverables (all in your folder)

1. `quarters_<Suffix>.blend`
2. `quarters_<Suffix>.fbx`
3. Renders, PNG, 1920 × 1080:
   - `quarters_<Suffix>_mockup_view.png`: **the mockup's camera**, from inside the rear doorway at eye height, looking down the room. The main comparison image.
   - `quarters_<Suffix>_topdown.png`: top-down cutaway, ceiling hidden.
   - `quarters_<Suffix>_exterior.png`: three-quarter view of the outside.
   - `quarters_<Suffix>_closeup.png`: dinette and porthole at eye height.
4. `notes_<Suffix>.md`: triangle counts (shell and per prop), what you couldn't match from the mockup and why, and what you'd improve next.
