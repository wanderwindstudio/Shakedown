# Base compartments: notes (Opus)

`compartments_Opus.py` is the generator. It has one function, `build_compartment(name, H, W, L)`, and calls it six times. I ran it headless in Blender 5.2.3 and rendered with Cycles (32 samples, denoised, gentle bloom). The materials, palette, watercolour chain and lighting are the same as in `quarters_Opus.py`.

To re-run it: open a new Blender file, go to the Scripting tab, paste the script and press Run. It clears the scene and writes everything into this folder.

## Numbers

| Compartment | H × W × L | Slots | of which Chamfer | Ribs | Triangles | Budget |
|---|---|---|---|---|---|---|
| Nook | 2 × 2 × 2 | 24 | 4 | 2 | 1,080 | 6,000 |
| Skylight | 2 × 4 × 3 | 52 | 6 | 3 | 2,084 | 6,000 |
| Cabin | 3 × 4 × 3 | 66 | 6 | 3 | 1,940 | 6,000 |
| Bay | 4 × 5 × 4 | 112 | 8 | 3 | 2,556 | 6,000 |
| Hall | 5 × 6 × 5 | 170 | 10 | 4 | 3,608 | 10,000 |
| Gangway | 3 × 2 × 4 | 52 | 8 | 3 | 1,836 | 6,000 |

The triangle counts include slots, ribs, pipes and the light strip.

Slots per face, using the Cabin as an example:
- **Left and Right walls:** 9 each (3 columns × 2 rows, plus 3 Chamfer slots).
- **Front and Back walls:** 12 each.
- **Floor and Ceiling:** 12 each.

In general, each long wall has L × (H − 1) plain slots plus L Chamfer slots. Each end wall has W × H, and the floor and ceiling have W × L each.

## How I checked the slots

- **Every slot is a closed solid.** The script tests each one for open edges and found none. In the Skylight I left out the glass pane, which is a single loose face by design.
- **The slots fill the shell exactly, with no gaps or overlaps.** In a test run without the exterior recesses, the slot volumes add up to the shell volume (outer hull minus interior) to four decimal places for all six compartments. The exterior recesses take a few litres off the outside on purpose.
- **Removing slots works:** `slot_test.png` shows the Cabin with `Cabin_Right_01_00` and `Cabin_Right_01_01` hidden. That leaves a clean 1 × 2 m doorway hole through the full 0.35 m wall, edged with the dark recess colour.

## Decisions this prompt didn't cover

1. **Corners are mitred.** Every point of the 0.35 m shell belongs to the interior surface it sits straight out from. Where two surfaces meet, the split is the 45° line between them, like a picture frame. Each slot's inner face is exactly its 1 × 1 m block face, the hole through the wall is clean, and the corners need no extra pieces.
2. **A Chamfer slot is the top wall row plus the chamfer face.** It covers 0.5 m of vertical wall and the 0.5 × 0.5 m chamfer above it, welded along the line between them into one closed piece. As a result, the **outermost ceiling slots are only 0.5 m wide** (the flat ceiling stops where the chamfer begins). I kept one ceiling slot per block anyway. Unity can treat them as "narrow ceiling" slots.
3. **End-wall corner slots.** The top corner slots of the front and back walls have the chamfer corner cut off (a pentagon-shaped inner face). They use the normal names (`Cabin_Front_00_02`), not `Chamfer`.
4. **How columns and rows are counted:**
   - Long and end walls follow the prompt: columns count left to right as seen from inside, facing that wall.
   - **Floor and ceiling:** columns run along X from −X to +X (left to right when facing the front), and rows run along Y from the back to the front.
5. **Ribs:**
   - **No rib on the floor.** A 5 cm ridge would sit under the furniture grid. The ribs cover both walls, both chamfers and the ceiling.
   - **Each rib object has an inner frame and an outer ring.** The inner frame stands 0.05 m out from the walls into the room. The outer hull ring stands 0.05 m out from the hull and has no bottom section.
   - **Where the ribs sit:** end ribs sit just inside each end (the last 0.2 m), so two joined compartments show a 0.4 m double frame at the joint. Inner ribs are centred on the block boundary, so they overlap each neighbouring slot by 0.1 m. A doorway cut next to a rib therefore has a 5 cm deep frame lip along one side. The full 1 m opening stays open behind it.
6. **Pipes reach into the room.** They use the quarters values relative to the chamfer: centres 0.20 m out from the chamfer surface and 0.13 m either side of its middle, radius 0.06 m. That puts them up to 0.26 m into the chamfered top-row block. DEVLOG D-20 reserves that block for overhead things such as pipes. Because they're fixed relative to the chamfer, the pipes only line up between two compartments whose right-hand chamfers line up, meaning the same height and the same right wall position.
7. **The exterior details belong to the slots.** Each Chamfer slot has its own recessed sage panel, and each bottom-row wall slot has a short recessed amber strip on its half of the lower outer chamfer. The result is a "dashed" rhythm of one panel per block, and the detail disappears cleanly with its slot.
8. **Skylight ceiling slots** keep a 0.08 m slate frame through the full thickness, with a glass pane at mid-thickness. The light strips run along both upper chamfers, just below the pipes on the right.
9. **Each slot's side faces are dark slate.** These are the faces between slots, so they only show inside a hole. Inner faces use the wall, floor or ceiling colours, and outer faces the cream hull.
10. **Origins.** Every object of a compartment (slots, ribs, pipes, light) has its origin at that compartment's floor centre. For each FBX export the script moves the compartment to the world origin, so all six FBX files start at (0, 0, 0).
11. **No colliders and no doors,** as the prompt asks.

## Not done / to check in Unity

- **The Unity import is untested.** Things to check: −Z forward, slot names surviving the import, and whether 170 separate objects in the Hall are acceptable for draw calls. Static batching or combining at runtime should handle them.
- **There are no rounded end caps.** The end walls are flat, as the prompt asks.

## Material pass (2026-11-04)

The six compartments now use the corrected cockpit's materials and level of detail (warm white and light-grey painted metal with 2 cm bevelled seams around every slot, gunmetal ribs with orange safety edges at the joints, a gunmetal hull skirt with amber running lights, copper pipes), with all dimensions, slot names and slot structure unchanged.
