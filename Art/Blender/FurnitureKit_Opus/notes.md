# Furniture kit: notes (Opus)

`furniture_kit.py` builds the whole kit. I ran it headless in Blender 5.2.3 and rendered with Cycles. It runs `../Compartments_Opus/compartments_Opus.py` as a library, so the wall panels are cut from real slots of the compartment generator and use the same materials. To re-run it: open a new Blender file, go to the Scripting tab, paste the script and press Run. It clears the scene.

## What's in the folder

- `furniture_kit.blend`: every piece, the catalogue layout and the furnished test Cabin.
- **40 FBX files**, one per family or piece. Each family file holds all its variants, and the wall-panel files hold their edge forms. ACCESS empties are included. Scale is applied, −Z forward, Y up.
- `kit_manifest.csv`: 103 rows (name, footprint, merge family, variant, access marker, triangles).
- `kit_catalogue.png`, `kit_room_test.png`.

Triangles: the largest piece is `Wall_Porthole` at 942, and most are 50–500. Budget is ≤ 1,500 per piece; nothing is over. The script also checks that every floor piece stays inside its footprint with the 5 cm margin.

## Decisions the brief didn't cover

1. **Which side is which.** Seen from the front, the viewer's left is the piece's +X. `EndL` is closed on that side and open to the right. `EndR` is the same piece mirrored (separate meshes, so no negative scales in Unity).
2. **No margin on the joining sides.** Merging pieces run to the block edge on the sides where they join a neighbour, so the tops are continuous. Everywhere else there's the 5 cm margin. In `Mid` the body runs to both side edges.
3. **CornerIn and CornerOut**, as I modelled them (both orientations are rotations of the same piece):
   - **CornerIn:** an inside corner. There's a wall behind and on the viewer's left. The run continues to the viewer's right and, rotated 90°, toward the front.
   - **CornerOut:** an outside corner. The run comes from the viewer's right and continues behind. It has fronts on two sides and a chamfered top corner.
4. **Kitchenette** is a counter end piece. It has the same body, top height (0.90 m) and front style as `Counter`, is open on the viewer's left and closed on the right. A run is `Counter_EndL` + `Counter_Mid` (repeated) + `Kitchenette`. The manifest lists it as family `Counter`, variant `EndOfRun`.
5. **Wall panels and wall corners.** A slot at either end of a long wall carries the 45° mitre to the end wall. So each wall panel comes in three forms:
   - plain, for inner columns;
   - `_EdgeL`, for the column at the viewer's left end of a wall;
   - `_EdgeR`, for the right end.

   All three are cut from the matching plain slot of the generator, so the outer shape, hull skin and seams are identical. Only the inner side differs, and no panel goes deeper than 0.30 m. Panel origin: the bottom centre of the slot's inner face, with +Y pointing into the room and the hull skin at Y −0.35.
6. **Chamfer cabinets** follow the vertical top row (0.5 m) and the 45° chamfer, with one flush door on each part. They come in `Single/EndL/Mid/EndR`, plus the edge forms.
7. **FoldTable.**
   - `Wall_FoldTable_Folded` and `_Open` are complete panels.
   - `Wall_FoldTable_Top` is the leaf alone, modelled hanging (folded), with its origin on the hinge axis (Y 0, Z 0.75). Unity opens it by rotating it +90° about X.
   - It replaces a **floor-row** slot (row 00), because the table top sits at 0.75 m.
8. **Door_Frame and Door_Leaf.**
   - **Frame:** origin at the centre of the opening at floor level, halfway through the 1 m gap; you walk through along Y. It lines the 1 × 2 m opening for the full 1 m depth. A threshold piece fills the mitred floor edges of both walls and the gap under the opening. Orange safety edges sit at both ends.
   - **Leaf:** sits closed in the middle of the frame and slides along X.
   - **Door height:** D-22 says doors are 2 blocks high, so the frame is a true 1 × 2 m opening and the leaf is about 1.9 m tall. That's a tight fit for a 1.8 m player.
9. **ACCESS markers.** These are empties named `ACCESS_<piece>`, because Blender needs unique names. Each is parented to its piece, 0.5 m in front of the front face. Unity can find them as the child whose name starts with `ACCESS`. Wall panels that are used (cabinets, shelf niche, fold table, terminal) have one too, 0.5 m into the room.
10. **Desk (1 × 2).** The desk itself stands in the back block and the front block is the chair space. That's where the access marker sits.
11. **Dinette (2 × 3).** It's a booth with two benches along the long sides and the table between them, open at the front where you slide in.
12. **Smelter.** The heat duct is on the back, with a wall flange. The smelter therefore has to stand with its back against an outer wall (D-39). Unity could check that by testing whether the slot behind the duct is a hull slot.
13. **Small items and decor.** Their origin is at the base. Wall-mounted items (`Decor_LightSwitch`, `Decor_PictureFrame`, `Decor_Clock`) have the origin at the back, with +Y facing out of the wall.
14. **Images on screens, the picture and pinboard prints** are small images the script generates and packs into the `.blend`, on flat cards with simple UVs. Everything else uses Box projection with no UVs.

## Part 2 (compartments)

The six compartments were re-run with the cockpit's materials and detail: 2 cm bevelled seams round every slot, gunmetal ribs with orange safety edges at the joints, a gunmetal skirt and amber running lights outside, copper pipes. Dimensions, slot names and slot structure are unchanged. The generator was also split into reusable functions (`compartment_geometry`, `slot_list`, `slot_object`) so the kit can use them.

## What I'd improve next

1. **Mirrored pieces.** Mirror `EndR`, the CornerIn/CornerOut orientations and the edge forms in Unity instead of shipping separate meshes. That would halve the file count, but it needs a check that negative scale doesn't break lighting or colliders.
2. **Door frames.** Give `Door_Frame` a version for the cockpit's rear wall, and an end cap for a doorway without a neighbour.
3. **Variety.** Add two or three variants of the boring pieces (counter fronts, locker doors), so long runs don't repeat exactly.
4. **Colliders.** There are no collision boxes yet for furniture. The footprint boxes would do for the block grid, but pieces such as the bed and chairs need lower boxes.
5. **Hero detail.** The machines (Smelter, Fabricator, Compactor) could use one more hero detail each, such as a gauge, a cable loom or a hazard placard. They're readable but a little plain next to the cockpit console.

## Look pass after `mockup_quarters_v3.png` (one line per change)

- **Lighting:** the room has several warm local lights instead of one bright strip. There's a desk lamp (spot light), strips under the wall cabinets, the wall shelf, the shelf niche and the bed (emission plus a small area light each), a bed reading light, a dimmed ceiling panel, and cool planet light through the window. Ambient light is lower.
- **Walls:** the panels are now a darker warm grey-beige (`#968B80`, lower row `#857B71`, ceiling `#9E958B`). Lighter panels (`M_Panel_Accent`) appear only on furniture fronts and as accents.
- **Wear:** the watercolour textures get more contrast, plus grime patches, vertical rust streaks and edge or corner dirt (Object-space noise and ambient occlusion). The floor gets scuffed patches. The noise and AO layers only work in Blender (Cycles): Unity needs the same wear painted into the textures (see "Next").
- **Orange band** at hip height (0.9–1.1 m) runs across the walls of the room test. On the back wall it stops at 1.0 m and acts as a backsplash under the cabinets.
- **Rivet rows** run along the top and bottom edges of every plain wall slot in the room test, as 364 six-sided heads.
- **Ceiling beams:** two heavier beams with bolt rows and angled brackets down the chamfers. They hang 10 cm below the ceiling, in the room test only.
- **Bed:** `Furn_Bed` is now a built-in berth. It has a chamfered wall-side panel, headboard and foot rail; a reading-light strip, status screen and buttons in the headboard; drawers with recessed handles; a light strip under the frame; a thin mattress, a chamfered pillow, a striped blanket with a soft low-poly fold and a turned-back edge; and a folded safety strap. 1,396 triangles.
- **Desk:** `Furn_Desk` is restyled with a chamfered top, gunmetal frame, a drawer unit with recessed handles, a status light, a label and a cable run down the back.
- **Chair:** `Furn_Chair` is now a padded swivel chair on a five-star base with casters and armrests. Seat height is still 0.45 m.
- **Chest:** `Furn_StorageCase` is now a hard chest with a chamfered lid, seal band, latches, side handles, a stencil plate and orange bands.
- **Lockers:** every locker front gets a label plate and a status light, in addition to the vent slots.
- **New small items:** `Decor_DeskLamp`, `Decor_Radio`, `Decor_TapedPhotos`, `Decor_WallShelf` (with a light strip) and `Decor_PlantPotted` are new. In the room test the mug steams (render-only wisps).
- **New wall panel:** `Wall_WindowHex` is a chamfered-hexagon window through the slot, with bolted gunmetal frames inside and out and a chamfered liner. It comes in plain, `_EdgeL` and `_EdgeR` forms, like the other panels. The room test uses it instead of the porthole; `Wall_Porthole` stays in the kit.
- **New room layout:**
  - left wall: the berth under the window, the high shelf and the chest at the foot of the bed;
  - back wall: the counter run of 3 ending in the kitchenette, with the wall-cabinet run above;
  - right wall: the desk and shelf niche, with the wet cell in the corner;
  - front wall: the fold table with two chairs;
  - middle: a striped rug.
- **Second view:** a second eye-height view, `kit_room_test_b.png`, shows the front half (fold table and chairs, wet cell, desk), which one camera in a 4 × 3 m room can't fit alongside the bed wall.
- **Budget:** everything stays within the raised budget. The largest pieces are the bed (1,396) and `Wall_Porthole` (942); nothing goes over 1,500.
- **Fixed:** the room was moved from X −60 to X −100. Parked edge-form panels were overlapping it.

### Next, from this pass

1. **Wear in textures.** The grime, rust and AO wear exist only in the Blender material. For Unity, bake it into a second watercolour layer (a grime/rust texture in Box projection) or into vertex colours.
2. **Compartments.** The compartment generator still uses the lighter Part 2 palette. The darker walls, hip band, rivet rows and beams could move into the generator, so every compartment gets them by default.

## Second look pass: a maintained ship, not an abandoned one

Layout, furniture, bed, hex window, kitchenette, cabinets and all small items are unchanged. Only surfaces and light changed:

- **Walls:** the panels are light again: `#D2C9BB` (lower row `#CBC2B4`, ceiling `#CEC5B7`, furniture bodies `#CFC7BA`), with `#DDD6CC` accent panels and fronts. There are no dark brown walls anymore.
- **Floor:** steel `#5A5652`, medium-dark. Frames and beams stay dark gunmetal (`#3E3D42`), and the orange stays saturated (`#D9772B`).
- **Watercolour texture:** it's blended toward white before the multiply. 42 % of the texture remains on walls, cabinets and furniture, so it darkens by at most about 15 %. On floors and frames 60–70 % remains.
- **Local wear only:**
  - The overall grime layer is gone.
  - Dirt and short rust streaks appear only near panel edges, seams, bolts and corners (ambient-occlusion mask, 12 cm, broken up by noise).
  - The floor wears most along the walkway, with dark scuffs and lighter polished patches.
  - Two soft grime decals sit in front of and under the kitchenette and at the fold table.
- **Light:**
  - A soft warm fill area light (32 W, `#FFD2A0`) and exposure +0.05 with AgX Medium High Contrast.
  - The desk lamp gets an extra 9 W point light so it throws a warm pool on the wall behind it.
  - Stronger strips under the wall cabinets (30 W) and the wall shelf (14 W).
  - The bed reading light gets an extra 7 W point light for its pool on the side wall.
  - The cool planet light through the hex window stays as the contrast.
- **Process:** I rendered both views twice and compared each with `mockup_quarters_v3.png`. The first pass was too bright and washed out (salmon orange), so I lowered the fill and exposure and made the edge wear stronger.

