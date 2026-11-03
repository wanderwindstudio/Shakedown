# M1a — Grid basics

Implemented 3 November 2026. Open `Unity/Assets/_Project/Ship/Scenes/ShipYard.unity` and press Play. The scene starts in Walk mode beside one hull block.

Built: a reusable first-person controller with the M0 planet adapter retained; a dusk landing pad; a free-flying build drone; a plain C# 2.5 m ship grid; Hull and Window ScriptableObject definitions and catalog; 24 stable cube orientations with an asymmetric face stripe; green/red placement ghosts and aimed-block outlines; connected placement/removal rules; 256-command undo/redo; versioned, readable JSON saving/loading; and a small mode/part/count/mass/message HUD. Visual meshes and colliders are combined per 8×8×8 chunk; edits rebuild only their own chunk.

**Keys:** B switches Walk/Build. WASD moves, mouse looks, Shift moves faster. Space jumps in Walk or rises in Build; C descends in Build. 1/2 selects Hull/Window. R/T/G rotates the next placement in world yaw/pitch/roll. Left click places; right click removes. Z/Y undoes/redoes. F5 saves and F9 loads `test_ship`. Escape releases the cursor; click recaptures it. Returning to Walk restores the player body where it was left.

**Light verification:** Unity compiled without script errors. Both scenes entered Play mode. ShipYard checks exercised rotated hull/window placements, placement/removal undo/redo, split-removal refusal, and F5 → exit Play → enter Play → F9 restoring the four-block test ship (two hulls, two differently rotated windows, 320 kg). M0 received a brief movement/jump smoke check; no new review runners, profiling or packages were added. Two screenshots are in `Docs/Screenshots/`.

**Decisions:** X/Z addresses are −64…63; Y is 0…127 above the pad. Hull mass is 100 kg and Window mass 60 kg. ShipYard jump height is 3 m so the player can jump onto a 2.5 m floor block; M0 retains its original 1.5 m jump and movement settings. Loading clears undo/redo history. Save location is `Application.persistentDataPath/ships/test_ship.json` (this project's current macOS path is `~/Library/Application Support/DefaultCompany/Planet Test/ships/test_ship.json`).

**Known limits / acceptance:** Window transparency is a placeholder and can show sorting artifacts within a combined chunk. The yard is generated on entering Play. The closed-room/doorway/walk-inside acceptance test and the three feel/precision questions remain for Lars's hands-on playtest; the brief M0 smoke check does not replace a full tidal-cycle regression. No M1b–M1e features were built.
