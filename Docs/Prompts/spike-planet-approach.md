# Spike: from orbit to surface

A **spike** is a short experiment that answers one question. This one: **does approaching and landing on a planet work and feel good in Shakedown?** It's throwaway-quality code in its own scene; nothing here is final. One session, then report and stop. Commit and tag `spike-planet`.

## Context

Read `~/Shakedown/Docs/DEVLOG.md` first, especially:
- **D-3 / D-4:** no seamless space-to-planet flight; the ship computer flies.
- **D-28:** planet level of detail stays minimal (far, near, arrival).
- **D-30:** space is realistic low poly: near-black sky, sharp stars, faceted planets with natural colours, one strong sun.
- **D-32:** grounded art direction (watercolour textures come later; plain colours are fine here).

The M0 planet (`Unity/Assets/_Project/Scenes/TestPlanet.unity`, "Pelagic") is the landing destination. Reuse it; don't rewrite it.

Working rules as in `Docs/Prompts/M1a-grid-basics.md`: light verification (a few screenshots, no profiling reports), short report, readable code, no new packages.

## Build

New scene `Unity/Assets/_Project/Spikes/OrbitTest.unity`, code in `Unity/Assets/_Project/Spikes/`.

1. **Space:** near-black, very slightly blue sky. A generated star field: a few thousand sharp points of varying brightness in real star colours (blue-white, white, yellow, orange). One directional "sun" light, warm white, plus a simple sun glow sprite.
2. **The planet, an ocean world like Pelagic:**
   - A faceted, flat-shaded icosphere with **three LOD levels: about 320, 1,280 and 5,120 faces**, switched by distance with a Unity LOD Group. Use cross-fade or dithered transitions so switches don't pop.
   - Colours from a height ramp per face: deep ocean → shallows → beach → land → rock, from seeded noise, with a few island clusters. Ocean faces stay at sea level (flat ocean, raised land).
   - A **faceted cloud shell** slightly above the surface, turning slowly, partly transparent.
   - A thin **atmosphere rim** glow on the lit side (a simple fresnel shader).
   - Hard day/night side from the sun, with a clear terminator line.
3. **The view:** a camera placed like a pilot looking out of a cockpit, starting far enough away that the planet is small.
4. **The approach (press L):**
   - About **20 seconds** from far away until the planet fills the view. The camera eases in, aiming at a landing site on an island on the day side.
   - Then about **5 seconds of descent into the clouds**: the view fades through cloud grey/white.
   - Behind the cloud fade, **load `TestPlanet`** and arrive about 200 m above the Pelagic island, descending smoothly onto a flat spot near the shore, then hand control to the player. The load must stay hidden behind the clouds.
   - Total, from pressing L to standing on the ground: **under 40 seconds.**
5. **R** restarts the approach from orbit.

## Report

- Screenshots: far, mid (planet half filling the view), near (filling the view, clouds and rim visible), one frame from the cloud fade, the arrival above the island.
- **Did the LOD switches pop?** Where and how badly.
- **Did the handoff to the surface feel like a landing or like a loading screen?** Any visible hitch while `TestPlanet` loads, and how long it took.
- A rough frame rate in the Editor during the approach.
- What you'd change first if this became the real system.
