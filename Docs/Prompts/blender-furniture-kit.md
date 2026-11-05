# Blender: furniture kit and compartment material pass

Two parts, in this order. Work **only** in `~/Shakedown/Art/Blender/FurnitureKit_Opus/` (Part 1) and `~/Shakedown/Art/Blender/Compartments_Opus/` (Part 2). Don't change anything else.

## Read first

1. `~/Shakedown/Docs/DEVLOG.md`: **D-32** (art direction: grounded low poly with watercolour textures, not cute), **D-17 to D-27** (blocks, slots, wall panels, merging, access rule).
2. `~/Shakedown/Art/Blender/Cockpit_v3_Opus/`: your corrected cockpit. **Its materials and level of detail are the standard** for everything in this brief: warm white and light-grey painted metal, gunmetal frames, orange accents, worn edges from the watercolour textures, bevelled edges, panel seams.
3. `~/Shakedown/Art/Blender/Compartments_Opus/`: your compartments and generator. The wall panels in Part 1 must fit their slots exactly.
4. `~/Shakedown/Art/Concepts/AI-mockups/mockup_cockpit_v3.png`, `mockup_quarters_v2.png`, `concept_sheet_deltawing.png`: style references for furniture (proportions, materials, lived-in props).

## Rules for every piece

- **Blocks:** 1 × 1 × 1 m. Each piece has a footprint **W × L × H** in whole blocks. Origin at the **centre of the footprint, on the floor** (Z = 0). The front faces **+Y**.
- **Fit:** the model stays inside its footprint with a **0.05 m margin** on all sides, so pieces never touch walls or each other at the bounding box.
- **Access side:** every piece that is used (bed, locker, machine, desk...) gets an empty object `ACCESS` placed 0.5 m in front of its front face. Unity reads it for the access rule (D-21).
- **Real-world proportions** (D-32): bed 0.55 m high, counter top 0.9 m, desk 0.75 m, seat 0.45 m, lockers 2.0 m, door handles at 1.0 m.
- **Budget:** ≤ 1,500 triangles per piece; most should be far less.
- **Textures and materials:** exactly as in the cockpit (Box projection, no UVs, watercolour multiply).

## Part 1: the furniture kit

### A. Floor furniture that merges (D-18)

Each family comes in **six variants**: `Single`, `EndL`, `Mid`, `EndR`, `CornerIn`, `CornerOut`. `EndL` is seen from the front with the open side to the right; `EndR` may be a mirror of `EndL`. Shared side panels disappear in `Mid`; continuous tops run through.

| Family | Footprint per piece | Notes |
|---|---|---|
| `Counter` | 1 × 1 × 1 | Workbench/counter, cabinets below, continuous top |
| `LowCabinet` | 1 × 1 × 1 | Drawers, lower than the counter, for under windows |
| `Locker` | 1 × 1 × 2 | Tall, vent slots; in a row they read as one locker bank |
| `Shelf` | 1 × 1 × 2 | Open shelving with a back panel |

### B. Floor furniture that doesn't merge

| Piece | Footprint | Notes |
|---|---|---|
| `Bed` | 1 × 2 × 1 | Storage drawers under it |
| `Bunk` | 1 × 2 × 2 | Two berths, ladder at the foot end |
| `Wardrobe` | 2 × 1 × 2 | Two doors |
| `Desk` | 1 × 2 × 1 | With a small drawer unit |
| `Dinette` | 2 × 3 × 1 | Two benches and a table between them |
| `StorageCase` | 1 × 1 × 1 | Hard case, like the cockpit's |
| `Smelter` | 2 × 2 × 2 | Machine: hopper on top, glowing inspection window. It vents heat through the hull, so put a vent duct on its **back** (it will stand against an outer wall) |
| `Fabricator` | 1 × 2 × 2 | Machine: enclosed print bay with a window, control panel |
| `Hydroponics` | 1 × 3 × 2 | Machine: two lit grow shelves, water tank below |
| `Chair` | 1 × 1 × 1 | Simple padded chair, real proportions |
| `WetCell` | 1 × 1 × 2 | Camper-van toilet/shower combo: enclosed cubicle with a door, shower head, fold-down toilet seat |
| `Kitchenette` | 1 × 1 × 1 | Cooktop on top, oven below. Same height, top and front style as `Counter`, so it lines up at the end of a counter run |
| `Compactor` | 1 × 1 × 2 | Machine: hopper on top, press inside, compressed cubes come out of a front tray |
| `SuitStation` | 1 × 1 × 2 | Upright frame holding a spacesuit and helmet, small control panel |
| `Analyzer` | 1 × 1 × 1 | Counter-height bench device with a sample chamber, for the Survey Logbook |
| `Locker_Storage` | 1 × 1 × 1 | Small storage crate/locker for inventory, stackable look |

Small decor (separate, no footprint rule, origin at the base): `Plant`, `Mug`, `Books`, `TableLamp`, `Rug_2x3`.

### C. Wall panels (D-17)

A wall panel **replaces one 1 × 1 m wall slot.** It must have **exactly the slot's outer shape**: same 1 × 1 m face, same 0.35 m thickness, same mitred edges and the **same outer hull skin** as a plain slot from your generator. Only the inner side differs, using up to 0.3 m of recess depth. Build them from your generator's plain long-wall slot so the fit is exact.

| Panel | Variants | Notes |
|---|---|---|
| `WallCabinet` | `Single`, `EndL`, `Mid`, `EndR` | Flush doors, inset handles; merges in rows |
| `ShelfNiche` | single | Recessed shelf with a light strip |
| `WallLight` | single | Recessed warm light panel |
| `Vent` | single | Grille |
| `Screen` | single | Wall monitor, teal glow |
| `Porthole` | single | Round window **through** the slot (glass, bolted ring inside and out) |
| `Pinboard` | single | Cork board, a few notes |
| `FoldTable` | two states: `Folded`, `Open` | A table that folds out of the wall. `Folded`: flush with the wall. `Open`: the table top projects 0.8 m into the room at 0.75 m height. Make both states as separate objects, plus the hinged top as its own object so Unity can animate it |
| `Terminal` | single | Ship terminal: a wall screen with a small keyboard ledge. Opens build mode, star map and logbook in the game |

Also make the **chamfer-row** versions of `WallCabinet` (`Single`, `EndL`, `Mid`, `EndR`) that replace a `Chamfer` slot: overhead cabinets that follow the 45° chamfer.

### D. Doorway between compartments

Adjacent compartments are placed with **exactly 1 m between their interiors** (both walls plus a small gap). A doorway removes two stacked slots in both walls and fills the 1 m with:
- `Door_Frame`: a 1 × 2 m opening, **1.0 m deep**, gunmetal frame with an orange safety edge. It closes off the gap between the two walls completely.
- `Door_Leaf`: the sliding door panel, a separate object, closed position, so Unity can slide it open sideways.

### E. Small items (third placement layer)

Placed freely on counters, tables and walls; they **don't use a block or a wall slot**. Origin at the base (or at the back for wall-mounted items).

`Decor_CoffeeMachine`, `Decor_LightSwitch` (a small flat wall screen, about 0.15 × 0.25 m, for lighting controls), `Decor_PictureFrame`, `Decor_Clock`, plus the decor from section B (`Plant`, `Mug`, `Books`, `TableLamp`, `Rug_2x3`).

### Naming

`Furn_<Family>_<Variant>` (e.g. `Furn_Counter_Mid`), `Furn_<Piece>` (e.g. `Furn_Bed`), `Wall_<Panel>_<Variant>` (e.g. `Wall_WallCabinet_EndL`), `WallChamfer_WallCabinet_<Variant>`, `Decor_<Name>`.

### Deliverables (Part 1)

1. `furniture_kit.blend`, and one FBX per family or piece (scale applied, forward −Z, up Y).
2. `kit_manifest.csv`: one row per piece: name, footprint W × L × H, merge family (or none), variant, has access marker (yes/no), triangle count.
3. Renders, PNG, 1920 × 1080:
   - `kit_catalogue.png`: all pieces in a labelled grid, with a 1.8 m human silhouette for scale.
   - `kit_room_test.png`: a **Cabin** from your compartments, furnished with kit pieces, including a **merged counter run of 3 ending in the `Kitchenette`**, the `WetCell`, a `FoldTable` (open) with two chairs, a `Decor_CoffeeMachine` on the counter, a **merged wall-cabinet run of 3**, a porthole panel swapped into a wall slot and a bed. Eye-height view. This proves the merging and the slot swap work.

## Part 2: material pass on the six compartments

Re-run your compartment generator with the **cockpit's materials and detail level** instead of the earlier cream/watercolour look: panel seams, bevelled edges, gunmetal ribs, orange accents where they make sense (door-frame edges, rib bands), worn painted metal. Keep all dimensions, slot names and slot structure **exactly** as they are. Overwrite the FBX files and renders in `Compartments_Opus/`, and add one sentence to `notes_Opus.md` describing the change.

## Notes

Write `notes.md` in `FurnitureKit_Opus/`: anything this brief didn't cover, and what you'd improve next.
