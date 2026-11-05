# Spike: landing site size

A **spike** answers one question; its code is throwaway and lives in its own scene. This one: **how big should a planet's landing site be so that it stays interesting to walk, and the game stays finishable?** One session, then report and stop. Commit and tag `spike-size`.

Read `~/Shakedown/Docs/DEVLOG.md` first, especially **D-33 and D-35** (circular landing sites with natural borders). Working rules as in `Docs/Prompts/M1a-grid-basics.md`: light verification, short report, readable code, no new packages.

## Build

New scene `Unity/Assets/_Project/Spikes/SiteSizeTest.unity`, code in `Unity/Assets/_Project/Spikes/`. Reuse the M0 Pelagic code (terrain, ocean, props, player); don't change the M0 scene itself.

1. **Site diameter is a single parameter.** Presets on keys **1 / 2 / 3: 1,000 m, 2,000 m, 3,000 m.** Pressing a key regenerates the site with the same seed and respawns the player at the landing spot in the centre.
2. **Terrain: a sunken crater**, as planned for Pelagic: a ring-shaped crater rim as the natural border, with islands, shallows and a lagoon inside. **Keep facet size constant** across sizes (about 7.5 m), so larger sites get more terrain chunks rather than coarser terrain. Gentle swell on the water; the tidal wave stays off.
3. **Border:** the crater rim is too steep to climb. If the player still reaches the edge, show a ship-computer line ("Signal weak. Return to the landing zone.") and push them back gently.
4. **Backdrop:** beyond the rim, a ring of simple low-poly distant mountains fading into haze.
5. **Points of interest, placed by density, so every size has the same density:**
   - **Resource nodes:** one per 150 × 150 m cell on average (about 35 / 140 / 315). Small, clearly visible crystal clusters. Walking into one collects it.
   - **Landmarks:** one per 400 × 400 m cell on average (about 5 / 20 / 45). Placeholder: a tall coloured pillar with a name, visible from far away. It counts as discovered within 15 m.
   - **Safe high points:** at least one within 300 m of anywhere on the site (keeps a future tidal wave fair).
6. **Player:** the M0 controller unchanged: walk 7 m/s, sprint 12 m/s, jump.
7. **HUD:** site size, time since landing, distance walked, nodes collected / total, landmarks found / total.

## Report

- For each size: time to walk from the centre to the rim and across the whole site; frame rate in the Editor; terrain triangle count; number of chunks.
- Screenshots for each size: from the landing spot, and from the highest point looking across the site.
- Anything that broke or got slow at 3,000 m.
