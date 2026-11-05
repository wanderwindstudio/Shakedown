> **Partly outdated (2026-11-04):** the grid, dimensions and doorway rules below describe the old 4 m section model. Compartments now use 1 m interior blocks; see `Docs/DEVLOG.md` (D-17 to D-27) and `Docs/Prompts/blender-compartments.md`. Palette, textures, render lighting and export settings still apply.

# Shakedown section standard (v1)

Every ship section follows these rules, so any section fits any other. Dimensions and connectors are **frozen**: never change them for a single section.

## Game context

**Shakedown** is a calm, cosy first-person space exploration game (Unity 6, URP). The player lives in a ship assembled from hand-designed **sections** that snap together on a grid; doorways open where sections meet. Furniture and machines are placed freely inside by the player.

## Grid and dimensions

- **One grid unit:** 4 m × 4 m footprint, 3.5 m tall (one deck). Sections are whole units: 1×1, 2×1, 2×2.
- **Axes:** a section's long axis is **Y**. "Front" is +Y. Z is up. Blender units = metres.
- **Pivot:** bottom centre of the section's bounding box (0, 0, 0). Nothing may extend outside the box.
- **Floor surface at Z = 0.2 m** (floor plate fills 0–0.2 m). **Ceiling underside at Z = 3.2 m.**

## Cross-section: the chamfered octagon

- Outer hull: **0.8 m chamfers** on the two upper long edges, **0.5 m** on the two lower long edges, running the full length.
- Walls **0.25 m** thick; the interior follows the same octagonal shape.
- **Rib frames:** dark structural frames following the octagon, **at both ends and every 2 m** along Y. 0.2 m wide, protruding 0.1 m into the room. Every section joint therefore shows a frame; that rhythm is the ship's signature.
- **Pipes:** one or two pipe runs along an upper chamfer, held by brackets at the rib frames. They must line up at section ends (same position in every section), so pipes continue from section to section.

## Connectors

- **Doorway:** 1.4 m wide × 2.2 m tall, centred on a short end wall, starting at floor level, corners chamfered 0.25 m. Framed by the end rib frame.
- Each doorway has a **closed sliding door panel** as its own object (`Door_Front`, `Door_Back`).
- Player: 1.8 m tall, eye height 1.7 m. Keep a clear walkway of at least 1 m through every doorway path.

## Built in vs placeable

- **Section (built in):** hull, interior shell, floor, ceiling, rib frames, pipes, built-in cabinets, doors and frames, windows, ceiling lights.
- **Props (placeable by the player):** furniture, machines, small items. Separate objects named `Prop_<Name>_<Suffix>`, origin at the centre of the base, footprint in whole metres where possible (furniture grid 1 × 1 m).
- **Colliders:** simple boxes in a collection `COL_<Suffix>`, objects named `COL_...`.

## Style

- **Low to medium poly, flat-shaded facets.** Big, clean chamfered shapes; no smoothing. Budget per section: shell ≤ 8,000 triangles, each prop ≤ 1,500, total ≤ 25,000.
- **Wear, stains, rivets and paint chips live in the textures**, not the geometry. Bolts only where they define a shape (a porthole ring).
- **Palette** (approximate):
  - Cream panels `#E8DDD2`, warm beige walls `#E3D3C6`
  - Dark slate rib frames and beams `#4A4650`
  - Sage-green upholstery, lockers, console tops `#7FA39A`; deep teal accents `#5E857F`
  - Ochre accents (handrails, ladders, pipes, blankets) `#C9973A`
  - Floor: dark grey-violet metal plates `#5A5560`
  - Light: warm amber `#FFD9A3` (emission). Screens: soft teal glow.
- **Watercolour textures** from `~/Shakedown/Art/Textures/WatercolourTest/`, applied with **Box projection, no UV unwrapping**: Texture Coordinate (Object) → Mapping → Image Texture (Box, blend about 0.2) → Mix (Multiply) with the base colour → Principled BSDF Base Color. Walls, floor, hull: 2 m repeat (Mapping scale 0.5). Metal props and console: 1 m (scale 1). Fabric: `tex_upholstery.png`, 0.5 m (scale 2).
- **Render lighting:** warm, soft, cosy, like the mockups. Light panels as emission plus a few soft area lights, gentle bloom, no harsh shadows. Anything seen through windows (stars, planets) goes in a collection `RENDER_ONLY_<Suffix>`, excluded from export.

## Export

FBX with scale applied (FBX All), forward −Z, up Y. Export the section, props and colliders only: no cameras, lights or render-only objects.
