# Blender: the six base compartments

Build the six base compartments of the ship builder. Work **only** in `~/Shakedown/Art/Blender/Compartments_Opus/`. Don't change anything elsewhere in the project.

## Read first

1. `~/Shakedown/Docs/DEVLOG.md`: decisions D-17 to D-26 explain the block system this prompt follows.
2. `~/Shakedown/Art/Blender/Quarters_Opus/`: your own quarters build. **Keep its look**: octagon cross-section, dark rib frames, ochre pipes, cream/sage/slate palette, watercolour textures, warm light strips. Reuse your materials and texture setup from `quarters_Opus.py`.
3. `~/Shakedown/Docs/Specs/section-standard.md`: still valid for **palette, textures, render lighting and FBX export**. Its dimensions and doorway rules are **outdated**; this prompt replaces them.
4. `~/Shakedown/Art/Concepts/AI-mockups/mockup_quarters_v2.png` and `mockup_exterior.png`: style targets.

## What changed since the quarters

- Compartments are now **empty shells**. The player furnishes them later on a block grid. No furniture, no props.
- **No doors and no doorway openings.** Doors are cut in Unity later.
- Sizes are measured in **blocks**: 1 × 1 × 1 m of **usable interior space**. Walls, ribs and pipes sit **outside** the block volume.

## The six compartments

Interior size in blocks, **H × W × L** (height Z, width X, length Y):

| Name | H × W × L | Notes |
|---|---|---|
| `Nook` | 2 × 2 × 2 | Storage nook |
| `Skylight` | 2 × 4 × 3 | All ceiling slots are **glass** (framed skylight panes) |
| `Cabin` | 3 × 4 × 3 | |
| `Bay` | 4 × 5 × 4 | |
| `Hall` | 5 × 6 × 5 | |
| `Gangway` | 3 × 2 × 4 | Corridor piece |

Write **one parametric function** that builds a compartment from (name, H, W, L) and call it six times, so all six share exactly the same construction and style.

## Geometry rules

**Origin and axes.** Each compartment's origin is the **centre of its interior floor surface**. The interior spans X from −W/2 to +W/2, Y from −L/2 to +L/2, Z from 0 to H. Blender units = metres. "Front" is +Y.

**Wall layer.** Walls, floor and ceiling are **0.35 m thick**, entirely outside the interior volume: 0.05 m inner panel, 0.3 m of recess depth (reserved for wall cabinets later), outer hull skin. The floor plate sits below Z = 0, the ceiling above Z = H.

**Cross-section.** The interior keeps the octagon character: a **0.5 m × 0.5 m chamfer** along both upper long edges (where the long walls meet the ceiling). The end walls follow that outline. The lower interior edges stay square, so floor furniture fits flush. The **outer hull** adds 0.5 m chamfers on the lower long edges as well, like your quarters.

**Slots: the most important rule.** Build every surface as a grid of **separate 1 × 1 m slot objects**, each spanning the **full wall thickness** (inner panel, recess, outer skin and the edges between them). Deleting one slot must leave a clean, closed-edged 1 × 1 m hole through the wall. That's how Unity will cut doors (a doorway = two slots stacked) and swap in wall furniture later.

- Wall slots: one per block face along each wall, rows counted from the floor.
- Chamfer slots: the top row of each long wall becomes chamfered slot pieces (`Chamfer` variant).
- Floor slots and ceiling slots: one per block.
- Naming: `<Compartment>_<Face>_<column>_<row>`, faces `Front` (+Y), `Back` (−Y), `Left` (−X), `Right` (+X), `Floor`, `Ceiling`. Columns count from left to right as seen **from inside**, rows from the floor up, both starting at 0, two digits: `Cabin_Right_02_00`. Chamfer slots: `Cabin_Right_02_Chamfer`.
- Each compartment's slots go in their own collection, `<Compartment>_Slots`.

**Ribs.** Dark slate rib frames around the full interior outline at **both ends and at every 2nd block boundary** along Y. 0.2 m wide; they may protrude **at most 0.05 m** into the interior (furniture will keep a 0.05 m gap to walls). Ribs are separate objects (`<Compartment>_Rib_<index>`), **not** part of the slots, so removing slots never cuts a rib. On the outside, ribs show as matching hull rings.

**Pipes.** Two ochre pipes along the upper right chamfer, brackets at each rib, running the full length, at the same position relative to the chamfer in every compartment so they continue from compartment to compartment. Use your quarters values relative to the chamfer.

**Light.** A warm emissive light strip along the ceiling centre line (separate object, `<Compartment>_Light`), plus a soft area light for renders. In the Skylight, put the light strips along the upper chamfers instead.

**Exterior.** Cream hull with recessed sage panels on the upper chamfers and an amber light strip low on each long side, like your quarters exterior. Flat end walls for now: rounded end caps come later in Unity, where a compartment has no neighbour.

## Budget and style

- Flat-shaded, low poly. Per compartment ≤ 6,000 triangles (Hall ≤ 10,000). Slots are simple boxes; keep their edges clean, not detailed.
- Palette, watercolour textures with Box projection, and lighting exactly as in your quarters.

## Deliverables (all in your folder)

1. `compartments_Opus.blend`: all six, each in its own collection, placed side by side.
2. One FBX per compartment: `compartment_Nook.fbx`, `compartment_Skylight.fbx`, ... (scale applied, forward −Z, up Y, no cameras or lights).
3. Renders, PNG, 1920 × 1080:
   - `lineup.png`: all six side by side from a three-quarter view, with a simple 1.8 m human silhouette for scale.
   - `<Name>_interior.png` for each: eye height (1.7 m) from one end, looking along the length.
   - `slot_test.png`: the Cabin with two stacked slots on one long wall deleted (a doorway-sized hole), seen from outside. This proves the cut works.
4. `compartments_Opus.py`: the generator script, commented.
5. `notes_Opus.md`: triangle counts per compartment, slot counts, anything you had to decide that this prompt didn't cover.
