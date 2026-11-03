# M1a.1 — Drop-in and cleanup

Small follow-up to M1a. Same working rules as `M1a-grid-basics.md`: light verification, short report, readable code. Commit and tag `m1a.1` when done. Don't start M1b.

## 1. Drop in where the drone is (replaces the 3 m jump)

- Remove the ShipYard jump override (`player.JumpHeight = 3`). Jump height goes back to the controller default (1.5 m).
- When leaving Build mode with **B**, move the player body to the drone's position and settle it onto the first walkable surface directly below (ship blocks or the landing pad), facing the drone's yaw.
- If the capsule doesn't fit there (inside a block, or the gap is too low), keep looking downward for the next spot that fits. If none is found, leave the body where it was and show a short message, for example "No room to stand here."
- Update the HUD key hint: Space = jump in Walk, up in Build; B = "build / drop in here".

## 2. Shared player code

- Move `FirstPersonController` out of the ship code into `Assets/_Project/Shared/Player/`, namespace `Shakedown.Player`. Both scenes use it; it isn't ship-specific.
- Rename `ReviewControl` to `InputLocked` everywhere it's used, including M0 (`PlanetTide`, `PlanetPlayer`, the review scripts). The behaviour doesn't change.
- Move files together with their `.meta` files, so scene references survive. Both `ShipYard` and M0 `TestPlanet` must still work.

## 3. Commit the re-serialized materials

Unity rewrote five `.mat` files in `Ship/Parts/` when it opened them. Include those changes in the commit.

## Done when

- [ ] In ShipYard: fly the drone into a closed room, press B, and you're standing inside it.
- [ ] Pressing B with the drone inside a solid block shows the message and keeps the body where it was.
- [ ] Normal jump is 1.5 m again.
- [ ] M0 TestPlanet plays as before (movement, jump, wave sweep).
- [ ] `git status` is clean after the commit.
