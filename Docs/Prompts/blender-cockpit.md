# Blender: Cockpit section (comparison build)

You are one of two AI agents building this same room independently from this exact prompt. Lars compares both results and picks a winner, so **follow the spec closely** and **name everything with your own suffix**: Claude Opus → `Opus`, GPT Sol → `Sol`.

Work **only** in `~/Shakedown/Art/Blender/Cockpit_<Suffix>/`. Don't read, change or delete anything in the other agent's folder or elsewhere in the project (older cockpit tests in `Cockpit/` and `Cockpit_New/` are not yours to touch).

## Read first

1. `~/Shakedown/Docs/Specs/section-standard.md`: **binding rules** for dimensions, cross-section, rib frames, pipes, doorways, naming, style, palette, textures and export.
2. `~/Shakedown/Art/Concepts/AI-mockups/mockup_cockpit_v2.png`: **the target picture.** Match its layout, shapes, palette and mood as closely as 3D allows.
3. `~/Shakedown/Art/Concepts/cockpit_sketch_01.png`: Lars' own sketch of the same cockpit; the mockup is based on it.
4. `~/Shakedown/Art/Concepts/AI-mockups/mockup_exterior.png`: the outside of the ship. The cockpit is its nose.

## How to work

With a live Blender connection, build directly and check your own renders. Without one, write one commented `bpy` script that Lars runs in Blender's Scripting tab. One solid build plus one round of fixes.

## This section

- **Size: 2 × 1 units (8 m along Y × 4 m × 3.5 m).** It's the ship's nose: **one doorway at the rear only** (−Y). The front (+Y) is the canopy.
- **Canopy:** three faceted windows as in the sketch and mockup: a wide trapezoid in the middle and two angled side windows, framed by dark slate frames. The nose may taper toward the front inside the bounding box, but the octagonal cross-section must be complete at the rear end, so the cockpit joins other sections.
- **Console:** a horseshoe console wrapping from both side walls around the chair, sage top, cream cabinet fronts below, small warm light strips under the edge. **Three screens** below the window line: ship diagram (left), star map (centre, the largest), planet view (right). Teal glowing screens; simple shapes on them are enough. A few switch groups and one small joystick, not more.
- **Command chair** on a chamfered pedestal, centred, facing +Y, with two ochre guard rails beside it.
- **Walls:** an ochre handrail on the left wall near the entrance, shelves with books, a plant and a small box on the left; a shelf with a box, a clipboard with a map and a cup holder with a mug on the right. Vent grilles low on both sides.
- **Ceiling:** a warm light strip, pipes running along the upper chamfers toward the canopy.

## Built in vs props

- **Built in** (`Cockpit_<Suffix>_...`): everything in the section standard, plus canopy, console with screens, shelves, handrail, vents and lights.
- **Props:** `Prop_CommandChair_<Suffix>` (with pedestal and guard rails), `Prop_Plant_<Suffix>`, `Prop_Books_<Suffix>`, `Prop_Box_<Suffix>`, `Prop_Clipboard_<Suffix>`, `Prop_Mug_<Suffix>`.

## Deliverables (all in your folder)

1. `cockpit_<Suffix>.blend`
2. `cockpit_<Suffix>.fbx`
3. Renders, PNG, 1920 × 1080:
   - `cockpit_<Suffix>_mockup_view.png`: **the mockup's camera**, from inside the rear doorway at eye height, looking toward the canopy. The main comparison image. Put a large lavender planet and stars outside the canopy (render-only).
   - `cockpit_<Suffix>_topdown.png`: top-down cutaway, ceiling hidden.
   - `cockpit_<Suffix>_exterior.png`: three-quarter front view of the outside.
   - `cockpit_<Suffix>_closeup.png`: console and screens at eye height.
4. `notes_<Suffix>.md`: triangle counts (shell and per prop), what you couldn't match from the mockup and why, and what you'd improve next.
