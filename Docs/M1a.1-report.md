# M1a.1 — Drop-in and cleanup

Completed 3 November 2026. This replaces M1a's return-to-body behaviour and 3 m ShipYard jump workaround.

**Changed:** B now leaves Build mode by finding a walkable surface directly below the drone, checking that the player capsule fits, and placing the player there facing the drone's yaw. Rejected surfaces are skipped so lower floors can be considered, including floors within the same combined chunk. Occupied grid cells are checked as well as physics overlaps, preventing a capsule fully enclosed in a mesh block from being accepted. If no spot fits, Walk mode resumes at the previous body position with “No room to stand here.” The normal 1.5 m jump is restored.

`FirstPersonController` and its original `.meta` moved to `Assets/_Project/Shared/Player/`, namespace `Shakedown.Player`. Both scenes use it. `ReviewControl` was renamed to `InputLocked` throughout runtime and existing review scripts. The five re-serialized Hull, Outline, Pad, Stripe and Window materials are included.

**Keys to test:** Open `Ship/Scenes/ShipYard.unity` and press Play. B enters Build; fly with WASD, Space up and C down, then B drops in at that location. Space jumps in Walk. The HUD now explicitly says “B build / drop in here” and distinguishes Space's two uses. All other M1a keys remain unchanged.

**Light verification:** Unity compiled without script errors. Loaded a temporary, fully closed 92-block room (4×4 cells inside, one cell high), flew inside and pressed B: the player stood inside on the ship floor and could move. Flew inside the solid starter hull and pressed B: refusal appeared and the body stayed at its previous pad position. M0 TestPlanet movement/jump worked, its normal 90-second wave launched, swept and respawned the player, and movement/jump worked afterward. The original ship save was restored byte-for-byte after loading the temporary room. No new packages or editor automation were added.

**Decisions / limits:** Successful drop-in levels the view and uses 5 cm initial floor clearance before gravity settles the capsule. Failed drop-in still exits Build mode, at the old body. Existing placeholder window transparency can show sorting artifacts. No new known issues were observed in these checks. No M1b work was started.

Screenshots: `Screenshots/m1a1-room-drop-in.png` and `Screenshots/m1a1-no-room.png`.
