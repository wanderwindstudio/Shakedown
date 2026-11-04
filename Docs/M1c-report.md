# M1c — Ship assembly

Built `Unity/Assets/_Project/Assembly/ShipAssembly.unity` in `Shakedown.Assembly`: seven compartment definitions, frozen FBX copies, URP Lit base-colour materials, 1 m grid placement with 90° rotation, footprint checks, an immutable cockpit root, connectivity-safe removal, octagonal joint collars, paired wall-slot cuts, automatic sliding doors, one ramp entrance, command history and readable JSON save/load. The scene loads the actual ShipYard additively to reuse its pad, lighting, player and drone; the old block-builder scripts remain untouched. No packages or later-stage features were added.

**Keys:** B build/drop in; 1 Nook, 2 Skylight, 3 Cabin, 4 Bay, 5 Hall, 6 Gangway; R rotate; left click place; right click remove; F add/remove door; Z/Y undo/redo; F5/F9 save/load; WASD move, Shift faster, Space jump/drone up, C drone down, Esc release cursor.

**Light Play-mode check:** built Cockpit → Gangway → Cabin → Bay → rotated Nook, with four connecting doors and one entrance. Walked from the pad up the ramp through all five doors to the cockpit chair. The observed joins were closed from outside. Removing the Gangway was refused with a connectivity message. Placement, removal and door undo/redo restored the rooms and cuts. Saving, leaving Play, entering again and loading preserved the JSON exactly. M0 played with movement/jump, and OrbitTest played its orbit view. These are smoke checks; Lars’s comfort and visual acceptance remain his playtest.

**Decisions:** grid positions address the lower corner of each rotated footprint; the common interior floor is 0.5 m above the pad. Connection needs a shared footprint edge, rather than a corner-only touch. Assembly saves go to `Application.persistentDataPath/assemblies/test_assembly.json`, separate from block saves; loading clears undo history. The assembly scene reduces the reused controller’s step lift to 8 cm so its capsule passes 2 m headers. In 2 m-high rooms, chamfered end-wall corner columns are refused as door sites; use a long-wall slot for Nook doors. Building across the existing entrance requires removing it first.

**Known issues:** Unity discards four self-intersecting polygons in the frozen cockpit hull plates; the supplied collision proxies are separate. Materials, collars and doors are placeholders. The source `Art/` files were never edited; all seven imported copies still match their initial snapshot hashes.

Screenshots: [assembled ship outside](Screenshots/m1c-outside.png) · [inside through a doorway](Screenshots/m1c-inside.png).
