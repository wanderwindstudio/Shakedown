# M1b — Ship Builder: Auto-shaping

## Context

Read `M1a-grid-basics.md` first: the context, working rules and fixed foundations there still apply. M1a and M1a.1 are done and playtested (placing feels precise, the drone is comfortable).

M1b is the riskiest stage of M1. It is followed by the **fun gate**: Lars builds a small ship and decides whether auto-shaping helps more than it fights him. If it doesn't, we fall back to manual slopes. So the goal is not perfection; it is a fair, playable test of the idea.

**This session is M1b only.** Finish, report, stop. Commit and tag `m1b`.

## The idea

Hull blocks fuse with their neighbours and change shape automatically, like Townscaper. A rough pile of hull blocks should look like an intentional ship: convex edges and corners are chamfered, flat runs stay flat, and the hull reads as one surface instead of separate cubes.

## Rules that must hold

1. **Visual only.** Auto-shaping changes how the hull *looks*. `ShipGrid` is unchanged: an occupied cell is solid, airtight and one block of mass, whatever it looks like. Connectivity, mass and (in M1d) sealing never read the shaped mesh.
2. **Colliders stay boxes** built from the grid, as in M1a. Walking and aiming must behave exactly as before.
3. **Never intrude into empty cells by more than 0.25 m.** Interiors must stay walkable. Chamfers cut into occupied cells (convex edges); concave edges (inside room corners) stay sharp or get at most a small fillet.
4. **Flat-shaded, faceted look**, consistent with the M0 rocks. Grey placeholder geometry generated in code is fine; real tiles come from Lars' Blender work later.
5. **Rebuild only what changed.** One placement or removal must not rebuild the whole ship.

## Method: corner-based tiles (dual grid)

Use the corner-based method Townscaper is known for, unless you find a concrete problem with it. In that case, explain the problem and your alternative in the report before building it.

- Each tile sits at a **grid corner**, where 8 cells meet. Its shape is chosen from which of those 8 cells are solid (an 8-bit pattern, 256 cases).
- Under the cube's rotations and mirroring, the 256 cases reduce to **22 unique shapes** (including empty and full). Generate those 22 base tiles plus a lookup table that maps every pattern to a base tile and an orientation.
- **What counts as solid** for the pattern: hull blocks, and fixed pieces (window, door frame, ramp). Fixed pieces are drawn as their own mesh, but the hull around them reacts to them.
- Only parts with `autoShapes = true` are drawn by the tile system. Their rotation index is ignored visually.

## What to build

### 1. Auto-shaping hull
- The existing hull part gets `autoShapes = true` and is drawn by the tile system.
- Chamfer size is a single Inspector value (start around 0.5 m), so Lars can try sharper or softer hulls without code changes.
- **H toggles auto-shaping on and off** (plain cubes vs shaped), so Lars can compare the same ship both ways during the fun gate.

### 2. Lock shape
- **L** while aiming at a hull block toggles its lock flag (undoable, saved). A locked block is drawn as a plain cube. Its neighbours still treat it as solid.
- Locked blocks get a subtle visual hint in Build mode only (for example, a small corner mark), so Lars can find them again.

### 3. Fixed pieces (placeholders)
Fixed pieces never change shape, can be rotated, and count as solid for neighbouring hull tiles.
- **Window** (exists): keep it.
- **Door frame**: a 1-cell frame with a walkable opening. No opening or closing yet; that's M1d. Its front and back faces are not airtight.
- **Ramp**: a 1-cell wedge rising the full 2.5 m, with a matching sloped collider. The player must be able to walk up it, so check the controller's slope limit. This is how the cadet gets into a ship from the pad.
- Part keys: 1 = Hull, 2 = Window, 3 = Door frame, 4 = Ramp.

### 4. Paint
- A palette of 8 muted colours that fit the M0 dusk mood.
- **[ and ]** cycle the current colour. New blocks are placed in the current colour.
- **Middle click** paints the aimed block with the current colour (undoable, saved).
- Shaped tiles take their colour from the cells they belong to; where colours meet, pick the simplest rule that looks clean and describe it in the report.

### 5. Tile spec for Lars (Blender brief)
Write `Docs/Specs/hull-tiles.md`. Lars will model the real tiles in Blender from it. It must contain:
- One entry per base tile: an ID, a one-line description, and a screenshot of the placeholder tile.
- Exact dimensions and the pivot point (tiles are 2.5 m cubes centred on a grid corner).
- Where the surface must meet each tile edge, so neighbouring tiles join without gaps.
- Which orientations the lookup applies, so Lars knows which way each tile must face in Blender.
- Export settings for FBX from Blender into this project (axes, scale), and the naming scheme the code expects.

## Done when

- [ ] A rough block pile visibly fuses into one chamfered hull; H shows the plain-cube version for comparison.
- [ ] Walking inside a 1-cell-high room is unaffected by chamfers.
- [ ] Lock, paint, window, door frame and ramp work, and all are undoable and saved.
- [ ] The player walks up the ramp from the pad into a ship through the door frame.
- [ ] Placing or removing one block on a ship of about 500 blocks updates without a visible hitch.
- [ ] `Docs/Specs/hull-tiles.md` exists with all 22 tiles.
- [ ] M0 TestPlanet still plays.

## Not in M1b

Drag-fill, mirror, copy/paste, rooms and sealing, opening doors, blueprints, machines, building costs, real art, flight.

## Playtest questions (the fun gate)

Lars builds a small ship (under 60 blocks) from scratch and answers:
- Does auto-shaping make my rough build look intentional?
- Did it ever do something I didn't want? How often did I reach for L?
- With H: do I prefer the shaped version or the plain cubes?
