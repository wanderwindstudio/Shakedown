# Blender test: Explorer cockpit module

I'm making **Shakedown**, a first-person space exploration game in Unity 6 (URP). The player is a freshly graduated space cadet who lives in their own ship. I'm considering a **modular ship builder like Starfield's**: ships are assembled from prefab room modules on a grid, and doorways open automatically where two modules meet.

Before committing, I want to see what one module could look like. **Please build the cockpit module in Blender.** It's a look test, not a final asset.

## How to work

- If you have a Blender connection (MCP), build it directly. If not, write a Blender Python script (`bpy`) that I paste into Blender's **Scripting** tab and run. Keep the script in one file, with comments that explain each section; I'm learning Blender and want to follow along.
- My project folder is `~/Shakedown/`. Save everything to `~/Shakedown/Art/Blender/Cockpit/`.
- Keep it to one solid attempt plus one round of fixes. I'd rather see a clear result quickly than a perfect one slowly.

## The module grid (fixed)

- One grid unit: **4 m × 4 m footprint, 3.5 m tall** (one deck).
- The cockpit occupies **2 × 1 units: 8 m long × 4 m wide × 3.5 m tall**. Nothing may extend outside that box.
- **Pivot:** centre of the module's floor (bottom centre of the box). Blender units = metres.
- **Rear face = door socket:** a doorway centred on the rear wall, **1.4 m wide × 2.2 m tall**, leading to the rest of the ship. All other faces are closed.
- Player scale: 1.8 m tall, eye height 1.75 m. The interior must feel walkable: at least 2.5 m clear headroom, and at least 1 m clear walkway around the chair.

## What's inside

- **Command chair** roughly in the middle, facing forward (the front is the module's +Y side in Blender).
- **Main console** in front of the chair, with a **star map display** (a glowing flat panel is fine).
- **Large front canopy / window** so the player sees the planet ahead. The nose may taper inside the box, but the floor footprint stays usable.
- A side console or two, a ceiling light strip, a few small details (handles, vents, panel seams) so it reads as a lived-in ship, not an empty box.

## Style guide

- **Low to medium poly, flat shaded** (no smoothing): faceted, like low-poly rocks. Target **5,000–15,000 triangles** in total.
- Calm, slightly retro-futuristic, cosy rather than military. Think "small research vessel", not "warship".
- Colours as plain materials for now (watercolour textures come later and will be projected in Unity, so **no UV unwrapping needed**):
  - Exterior hull: warm grey-beige
  - Interior walls: muted dusty blue-grey
  - Floor: darker slate
  - Accents: one warm orange
  - Screens and lights: soft teal glow (emission)
  - Canopy glass: slightly tinted, transparent
- Lighting in renders: soft dusk light, purple-tinted sky, to match the game's mood.

## Object structure

Keep parts as separate, clearly named objects, so Unity can use them individually:
`Cockpit_HullExterior`, `Cockpit_Interior`, `Cockpit_Floor`, `Cockpit_Canopy`, `Cockpit_Chair`, `Cockpit_Console`, `Cockpit_Details`.
Also add simple box colliders in a separate collection named `COL`, with objects named `COL_...` (floor, walls, chair, console).

## Deliverables

1. `cockpit_test.blend`
2. `cockpit_test.fbx`, exported for Unity: scale applied (FBX All), forward −Z, up Y, only the module objects (not the camera or lights).
3. Three renders (PNG, 1920 × 1080):
   - exterior, three-quarter view from the front
   - interior at eye height (1.75 m) from the doorway, looking at the chair and canopy
   - a top-down cutaway with the ceiling hidden, to show the layout
4. A short note: triangle count, anything you couldn't do, and what you'd change in a second version.
