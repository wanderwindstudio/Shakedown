# Crew quarters: notes (Opus)

Built without a live Blender connection. `quarters_Opus.py` is a single commented script, run headless with Blender 5.2.3 and rendered with Cycles (40 samples, denoised, gentle bloom in the compositor). To re-run it: open a new Blender file, go to the Scripting tab, paste the script and press Run. It clears the scene and writes everything into this folder. Textures are loaded from `../../Textures/WatercolourTest/` and stored as relative paths.

## Triangle counts

| Section (built in) | Tris |
|---|---|
| Quarters_Opus_Hull | 270 |
| Quarters_Opus_InteriorShell | 132 |
| Quarters_Opus_Floor | 14 |
| Quarters_Opus_Ceiling | 2 |
| Quarters_Opus_Ribs | 210 |
| Quarters_Opus_DoorFrames | 84 |
| Door_Back_Opus / Door_Front_Opus | 44 + 44 |
| Quarters_Opus_Pipes | 932 |
| Quarters_Opus_Bunks (incl. bedding, ladder, reading lights) | 544 |
| Quarters_Opus_Cabinets (overhead both sides, light strip, low storage) | 616 |
| Quarters_Opus_WashNiche | 232 |
| Quarters_Opus_Porthole + PortholeGlass | 816 + 22 |
| Quarters_Opus_CeilingLight | 24 |
| **Section total** | **3,986** (budget 8,000) |

| Prop | Tris (budget 1,500 each) |
|---|---|
| Prop_Lockers_Opus | 144 |
| Prop_Dinette_Opus | 204 |
| Prop_Plant_Opus | 359 |
| Prop_Mug_Opus | 144 |
| Prop_Book_Opus | 48 |
| Prop_Jacket_Opus | 132 |
| Prop_Pictures_Opus | 100 |
| **Everything** | **5,117** (budget 25,000) |

## Checks against the section standard

- **Bounds:** everything stays inside X −2…2, Y −4…4, Z 0…3.5. The script prints this check.
- **Pivot:** the section's pivot is (0, 0, 0). Each prop's origin is at the centre of its base.
- **Shell:** floor surface at Z 0.2 and ceiling underside at Z 3.2. Walls are 0.25 m thick and the interior follows the octagon (0.8 m upper and 0.5 m lower chamfers outside).
- **Rib frames:** at both ends and at Y −2, 0 and 2. Each is 0.2 m wide and stands 0.1 m out from the wall.
- **Doorways:** 1.4 × 2.2 m, centred on both end walls, starting at floor level, top corners chamfered 0.25 m, with a dark surround. The closed sliding doors are `Door_Back_Opus` and `Door_Front_Opus`.
- **Walkway:** 1.58 m clear between the ladder and the dinette. The straight line from door to door is clear.
- **Pipes:** two ochre pipes on the upper right chamfer, held by brackets at every rib and running from end wall to end wall. Their centres sit at (x, z) = **(1.215, 2.849)** and **(1.399, 2.665)**, radius 0.06. Every other section should use these values so the pipes line up.
- **Colliders:** 21 boxes in `COL_Opus`. These cover the shell, the end-wall pieces around each door, a closed-door box per doorway, the bunks, both rows of overhead cabinets, the storage bench, the wash niche, the lockers, the two benches and the table.
- **Textures:** every material uses the standard chain: Texture Coordinate (Object) → Mapping → Box-projected image (blend 0.2) → Multiply with the base colour.
  - Walls, floor and hull repeat every 2 m.
  - Metal parts (ribs, pipes, lockers, porthole ring, ladder) repeat every 1 m.
  - Fabrics (mattresses, pillows, blankets, cushions, jacket, book cover) repeat every 0.5 m.
  - The only UVs are on the two taped pictures. They're small painted images that the script generates and saves next to the `.blend`.
- **Export:** FBX with FBX All scale, −Z forward, Y up, Apply Transform. It contains the section, the props and the colliders, and no cameras, lights or `RENDER_ONLY_Opus` objects.
- **Not tested:** the Unity import.

## What I couldn't match from the mockup, and why

- **Room depth.** The mockup room looks about 4–5 m deep, but the standard makes this section 8 m. From the rear doorway the far wall (lockers, door, wash niche) is about 7.5 m away, so it looks smaller and the room looks more like a corridor than in the mockup. I kept the bunks and dinette in the near half as the mockup shows. The left wall between the bunks and the lockers would have been bare, so I added a low storage bench between the ribs at 0 and 2 m (`Quarters_Opus_Cabinets`). It isn't in the brief.
- **Far doorway.** Following the standard, the doorway is centred, with the lockers on its left and the wash niche on its right. In the mockup the lockers and sink sit side by side with no door between them.
- **Ribs and furniture.** With ribs every 2 m, the 2 m bunks have to cross the rib at Y −2. The rib runs behind the mattresses, which stop 13 cm short of the wall so they clear it. The dinette sits exactly between two ribs, which gives a 0.9 m table and benches 0.46 m deep. That's a little tighter than in the mockup.
- **Painterly look.** The mockup's soft edges, grain and wear come from painting. Here they come only from the watercolour textures. Multiplying the textures darkens every palette colour slightly, and the floor most of all.
- **Clutter.** I left out the mockup's extra cabinet details, the fold-over pillow shapes and the fabric draping. The bedding is made of chamfered blocks.
- **Exterior.** The section is the standard octagon box: teal recessed panels on the upper chamfers, amber light strips low down and the porthole on the right. The mockup ship's nose, legs and fins belong to other sections.
- **Two different backgrounds.** For the interior shots the porthole looks out on space with a blue planet. The exterior shot uses a dusk sky and a ground plane. These are separate render-only worlds, chosen per shot.

## What I'd improve next

1. **Pictures and jacket position.** Move them onto the far wall, as in the mockup. Here they're on the right wall near the far end, and the doorway leaves little room beside it.
2. **Bedding.** Shape the pillows and blankets as low-poly folded forms instead of boxes, and make the near benches a little softer.
3. **Exterior.** Add a few more details that stay inside the box: an exterior porthole collar, small amber lights at the doorway joints, and panel seams that match the rib rhythm.
4. **Lighting.** Make the ceiling light and the strip under the cabinets a little warmer and dimmer, so the room is less evenly lit and closer to the mockup's cosy pools of light.
5. **Unity check.** Test the import in Unity: the pivot, which way the room faces with −Z forward, transparency on the porthole glass, and turning the `COL_` boxes into BoxColliders.
