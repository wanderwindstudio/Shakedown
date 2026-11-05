# Cockpit look test — notes

Built without a Blender connection. I wrote `cockpit_test.py`, ran it with Blender 5.2 in the cloud and rendered with Cycles. You can re-run it yourself: open a new Blender file, go to the Scripting tab, paste the script and press Run. It clears the scene first. Set `DO_RENDER = False` near the top if you only want the model, because rendering freezes Blender for a few minutes.

## Numbers

| Object | Triangles |
|---|---|
| Cockpit_HullExterior | 1,836 |
| Cockpit_Interior | 1,708 |
| Cockpit_Console | 832 |
| Cockpit_Details | 760 |
| Cockpit_Canopy | 268 |
| Cockpit_Chair | 268 |
| Cockpit_Floor | 240 |
| **Total** | **≈ 5,900** (lower end of the 5–15k target) |

- Bounds: X −1.99…1.99, Y −4.00…3.995, Z 0…3.50, so everything stays inside the 8 × 4 × 3.5 m box (the script checks this and prints it).
- Pivot is at the floor centre (0, 0, 0) on every object. The walkable floor surface is at **z = 0.15 m**.
- Doorway: 1.4 × 2.2 m, centred in the rear wall (Y = −4), with the sill at floor level (0.15 m).
- Headroom: about 3.05 m under the light strip. Clearance around the chair is about 1.1 m in front, 1.4 m at the sides, 3.6 m behind and about 1.25 m to the side consoles diagonally.
- 12 box colliders are in the `COL` collection: floor, ceiling, left and right walls, three rear-wall pieces around the door, nose, chair, console and both side consoles.

## What I couldn't do, and things to check

- **No Blender MCP connection**, so I built it through the script instead of live in your Blender.
- **Which way the nose faces in Unity:** I used the FBX settings you asked for (FBX All, −Z forward, Y up), plus "Apply Transform" so the objects come in without a −90° rotation. I couldn't test the import in Unity. With these settings, Blender's +Y front usually ends up pointing along Unity's **−Z**. If the nose points backwards, rotate the prefab 180° around Y (or re-export with forward = Z).
- **Colliders come in as normal meshes.** In Unity, add a Box Collider to each `COL_` object and turn off its Mesh Renderer (a short editor script can do this on import).
- **Canopy colliders are simplified.** The curved glass has no exact collider. The console and the `COL_Nose` box keep you out of the nose instead.
- **Glass** is a Principled material with alpha 0.22. Unity's FBX importer often brings this in as opaque, so set the material to Transparent by hand.
- The **star map** is an emissive panel with small "star" tiles in front of it, not a texture.
- **Colour under dusk light:** in the exterior render the beige hull looks pinkish-salmon because of the warm sky. Under neutral light it reads as warm grey-beige.

## What I'd change in a second version

1. **Fewer, more deliberate hoops.** Inside, the six ribs make the room feel a bit like a tube or tunnel. Three or four, plus flat wall panels in between, would make it feel more like a room.
2. **A lower chair back, or a chair that swivels to face the door.** From the doorway the backrest hides most of the star map. A low backrest, or a map that hangs higher (as a hologram above the console), would fix that.
3. **A less symmetrical layout.** The side consoles are mirror copies. One console plus a jump seat, locker or plant on the other side would make it feel more lived-in and cosy.
4. **Socket geometry as its own object** (`Cockpit_DoorSocket`), so the builder can swap "doorway" and "closed wall" pieces on each face. The rear wall is currently part of `Cockpit_Interior`.
5. **Room for wear and tear:** the faces are already large and flat, which will suit your projected watercolour textures. Seams could also be marked with a separate vertex colour.
