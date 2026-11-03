# M1a — Ship Builder: Grid basics

## Context

**Shakedown** is a first-person space exploration and ship-building game. The player is a freshly graduated space cadet who builds and lives in their own ship. Milestone **M1** tests one question: *is building a ship fun, for a tiny scout and a capital ship alike?* Everything in M1 is grey-box.

M1 has five stages (M1a–M1e). **This session is M1a only.** Finish it, report, and stop.

- Repository root: `Shakedown/`. The Unity project is `Shakedown/Unity/` (Unity 6000.3.26f1, URP 17.3.0, Input System 1.20.0).
- M0 (the Pelagic test planet) lives in `Unity/Assets/_Project/`. It must keep working. Only change it where this prompt says so.

## Working rules

1. **One stage per session.** Build M1a, report, stop. Don't build features from later stages.
2. **Light verification.** One or two screenshots at the end. No profiling, CSVs, automated review tools or performance reports. Lars playtests himself.
3. **Short report** (one page at most): what was built, keys to test it, known issues, and anything you had to decide that this prompt didn't cover.
4. **Git:** commit when the stage works and tag it `m1a`. Git LFS is installed and `.gitattributes` exists at the repo root.
5. **Readable code for a learner.** Lars is learning C# and is starting on classes. Small classes with one job each, clear names, comments that explain *why*, not *what*.
6. **No new packages or Asset Store content** without asking.
7. Don't add new editor automation (command-file pollers, review runners).

## Fixed foundations (apply to all of M1)

These decisions are final. Later stages (auto-shaping, sealing, blueprints, Blender models) depend on them.

- **Grid cell size: 2.5 m.** Cells are addressed by `Vector3Int`. Maximum ship size: 128 cells per axis.
- **Rotations:** all 24 cube orientations, stored as an index 0–23.
- **Parts are data.** A `PartDefinition` ScriptableObject per part type: stable string `id`, display name, size in cells (1×1×1 for everything in M1a), mass in kg, `autoShapes` flag (false for now), which faces are airtight (all six by default), and a reference to its visual mesh or prefab. A `PartCatalog` asset lists all parts.
- **The grid stores only:** part ID, rotation index, paint colour index, and a shape-lock flag per occupied cell. Keep `ShipGrid` a plain C# class (not a MonoBehaviour), so it can be saved, tested and reasoned about on its own.
- **Logic reads the grid, never the meshes.** Connectivity, mass and (later) sealing are calculated from `ShipGrid`. The visual layer is rebuilt from the grid and is "paint on top". Later, auto-shaping will change how blocks *look* without changing what the grid says.
- **Visuals must scale.** Big ships in M1c will have several thousand blocks. Build visuals as combined meshes per chunk (8×8×8 cells), rebuilding only the chunk(s) a change touches. Colliders per chunk as well.
- **Code location:** `Unity/Assets/_Project/Ship/` (Scripts, Scenes, Parts), namespace `Shakedown.Ship`.

## What to build

### 1. Reusable first-person controller
`PlanetPlayer` is currently tied to `PlanetWorld` (`IPlanetFeature`). Extract the movement, look, jump and sprint logic into a reusable `FirstPersonController` that both scenes can use. The M0 `TestPlanet` scene must play exactly as before afterwards.

### 2. ShipYard scene
New scene `Ship/Scenes/ShipYard.unity`: a large flat landing pad, a simple sky, and lighting similar in mood to M0 (purple-dusk tones, soft shadows). Keep it simple; it's a workshop, not a showcase. The ship starts as **one hull block** at the grid origin, resting on the pad.

### 3. Two modes, toggled with **B**
- **Walk mode** (default): the first-person controller. The player can walk on and inside what they built; gravity is world-down (the ship is landed).
- **Build mode:** a free-flying construction drone camera. WASD move, Space up, C down, mouse look, Shift faster. Switching back to Walk returns control to the player body where it was left.

### 4. Placing and removing (Build mode)
- Raycast from the screen centre against the ship, reach about 30 m.
- **Ghost preview** of the selected part in the cell next to the face you're looking at. Green when placement is valid, red when not.
- **Left click** places. **Right click** removes the block you're looking at (outline it while aimed at).
- **Valid placement:** the target cell is empty, inside the 128-cell limit, and shares a face with an existing block. The ship stays one connected structure.
- **Removal** that would split the ship into two pieces is refused, with a short on-screen message. The last block can't be removed.
- **Rotation:** R = yaw 90°, T = pitch 90°, G = roll 90° (covers all 24 orientations). The placeholder cube needs one visibly marked face (for example a darker stripe), so rotation is visible on the ghost and on placed blocks.
- **Part selection:** 1 = Hull cube (grey), 2 = Window placeholder (translucent cube). Two parts are enough to prove the catalog works.
- **Creative mode:** no costs or inventory in M1.

### 5. Undo and redo
**Z** = undo, **Y** = redo (no modifier keys, so Unity's editor shortcuts don't interfere in Play mode). Command pattern, at least 200 steps. Undoing a removal restores the block exactly, including rotation, paint and lock flag.

### 6. Save and load
**F5** saves, **F9** loads. JSON file in `Application.persistentDataPath/ships/<name>.json`, default name `test_ship`. Human-readable: a format version number, then one entry per block (x, y, z, part ID, rotation, paint, locked). Loading rebuilds the ship exactly.

### 7. Minimal HUD
Current mode, selected part, block count, total mass, a one-line message area (for refusals and "Saved"), and key hints. Plain and small; style like the M0 HUD.

## Done when

- [ ] Lars builds a closed room (4 × 4 cells inside, one cell high inside, with floor, walls and ceiling), removes one wall block as a doorway, and walks inside.
- [ ] He saves, leaves Play mode, enters it again, loads, and the ship is identical.
- [ ] Undo and redo work through a mix of placements, removals and rotations.
- [ ] A removal that would split the ship is refused with a message.
- [ ] The M0 `TestPlanet` scene still plays as before.

## Not in M1a

Auto-shaping, paint, drag-fill, mirror, copy/paste, rooms and sealing, doors, blueprints, machines, building costs, real art, flight.

## Playtest questions Lars will answer

- Does placing feel snappy and precise?
- Is the drone camera comfortable?
- Did I ever place or remove a block I didn't mean to?
