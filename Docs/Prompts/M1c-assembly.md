# M1c — Ship assembly: placing compartments and cutting doors

## Context

Shakedown's ships are assembled from pre-built **compartments** (empty rooms) that the player furnishes later. This stage builds the **assembly**: placing compartments next to each other, cutting doors between them, and walking through the result. Furniture comes in the next stage.

Read first:
- `~/Shakedown/Docs/DEVLOG.md`: especially **D-22 to D-27** (blocks, doorways, shared floor level, the six compartments, slots), **D-37** (order of work) and **D-38** (spacing between compartments).
- `~/Shakedown/Art/Blender/Compartments_Opus/notes_Opus.md`: how the compartments are built, the slot naming scheme and axes.
- `~/Shakedown/Docs/Prompts/M1a-grid-basics.md`: the working rules, which still apply (one stage per session, light verification, short report, readable code for a learner, no new packages).

**This session is M1c only.** Finish, report, stop. Tag `m1c`.

## Working in parallel with another agent (important)

Another agent (Claude Opus) is working in `~/Shakedown/Art/` at the same time and will **overwrite the compartment FBX files** during your session.
- **At the very start**, copy these FBX files **once** into `Unity/Assets/_Project/Assembly/Imported/` and work only with your copies: the six `compartment_*.fbx` from `Art/Blender/Compartments_Opus/`, and `cockpit_v3.fbx` from `Art/Blender/Cockpit_v3_Opus/`.
- Never write to `Art/`.
- **Git:** stage only the files you created or changed under `Unity/` and your report under `Docs/`. **Never use `git add -A` or `git add .`**, which would commit the other agent's unfinished work.

## Reuse from M1a

New scene `Unity/Assets/_Project/Assembly/ShipAssembly.unity`, code in `Unity/Assets/_Project/Assembly/`, namespace `Shakedown.Assembly`. Reuse (don't copy) what exists: `FirstPersonController`, the `ConstructionDrone`, drop-in (B), undo/redo history (the command pattern), the landing pad and lighting from `ShipYard`. Leave the old block-builder code untouched.

## Fixed rules

- **Block grid:** 1 m. All compartments stand on the same floor level (D-23). One deck only for now: no stacking.
- **Rotation:** 90° steps around the vertical axis.
- **Spacing (D-38):** a compartment's footprint is its interior **plus a 0.5 m border on every side**. Footprints may touch but never overlap. So two touching compartments have **exactly 1 m between their interiors**, and the block grid stays aligned across the whole ship.
- **Compartment data:** a `CompartmentDefinition` ScriptableObject per type: id, interior size H × W × L in blocks, the imported model. Types: `Nook`, `Skylight`, `Cabin`, `Bay`, `Hall`, `Gangway`, `Cockpit`.
- **The ship's save data:** a list of placed compartments (type, grid position, rotation) and a list of doors (which two compartments, which wall slots). Readable JSON, like M1a.
- **Logic never reads meshes.** Adjacency, doors and connectivity are calculated from the save data, not from the models.
- **Materials:** Blender's procedural materials don't survive FBX export. Create simple URP Lit materials matching the base colours (per material name). Watercolour textures come later.

## What to build

1. **Start:** the `Cockpit` stands on the pad, facing forward. It's the ship's root and can't be removed. Only its rear wall can connect.
2. **Placing compartments** (in Build mode, with the drone): keys **1–6** select a compartment type. A ghost preview snaps next to the compartment you're aiming at; green when valid, red when not. **R** rotates. Left click places, right click removes. Valid means no footprint overlap and touching at least one existing compartment. Removal is refused if it would cut compartments off from the cockpit, or if it's the cockpit.
3. **Closing the gap:** where two compartments touch, the 1 m gap between them must not show from outside. Fill it with a simple **joint collar** following the octagonal outline (generated in code is fine).
4. **Cutting doors:** aim at a wall slot at floor level and press **F**.
   - If a touching compartment's wall lies directly opposite, remove the two stacked slots (rows 0 and 1) in **both** walls, and fill the 1 m between them with a placeholder door frame plus a sliding door leaf (simple boxes are fine; Opus is modelling the real `Door_Frame` and `Door_Leaf` right now).
   - If the wall faces outside, allow it only once per ship, as the **entrance**, with a simple ramp down to the pad.
   - Otherwise refuse with a short message.
   - **F** again on a door removes it and restores the slots.
   - Doors slide open automatically when the player comes within 1.5 m.
5. **Walking:** drop-in (B) puts the player inside, and every door is walkable. Colliders: walls from the slots, so a removed slot is a real opening.
6. **Undo/redo** (Z/Y) for placing, removing, and doors. **Save/load** (F5/F9).
7. **HUD:** mode, selected compartment, compartment count, door count, a message line, key hints.

## Done when

- [ ] Starting from the cockpit, Lars builds a ship from a Gangway, a Cabin, a Bay and a Nook, with doors between them and one entrance with a ramp.
- [ ] He walks from the pad up the ramp, through every door, to the cockpit chair.
- [ ] No gaps between compartments are visible from outside.
- [ ] Removing a compartment that holds others to the cockpit is refused.
- [ ] Save, quit Play mode, load: identical ship. Undo and redo work for every action.
- [ ] The M0 planet and the orbit spike scenes still play.

## Not in M1c

Furniture, wall-panel swapping, merging, end caps and exterior dressing, stacking compartments, building costs, flight.

## Report

What was built, the keys, known issues, anything you had to decide that this prompt didn't cover, two or three screenshots (outside view of the assembled ship, inside view looking through a door).
