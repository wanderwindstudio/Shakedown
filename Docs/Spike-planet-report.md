# Spike — orbit to surface

4 November 2026. Open `Unity/Assets/_Project/Spikes/OrbitTest.unity` and press Play. **L** starts the approach; **R** replays it from orbit, including after arrival. The experiment is isolated in `Assets/_Project/Spikes/`; Pelagic's scene and scripts were reused without edits. The orbit scene was added to the build-scene list for runtime loading. No packages were added.

**Result:** the orbit → cloud cover → existing surface-scene approach works. Five completed Editor runs reached a grounded player in **33.05–33.06 s**, below the 40 s limit. The sequence uses 20 s approaching the day-side island, 5 s passing through cloud cover, then 8 s descending from about 200 m above the island. The landing search found a clear shore patch near **(−155, 4.95, −130)**. Pelagic's tide waits during arrival and resumes at handover.

**Space and planet:** 3,600 sharp star points, natural star colours, one warm-white sun and glow, a simple pilot windscreen, seeded island clusters and height colours, raised land with sea-level ocean vertices, rotating faceted translucent clouds, a lit-side atmosphere rim and dark night side. A Unity LOD Group selects **320 / 1,280 / 5,120** flat-shaded surface faces with **0.8 s dither cross-fades**.

**LOD popping:** no hard whole-sphere jump was evident in the sampled views/frame sequence. There is still mild facet/coastline reshaping as detail increases, most noticeable on the first refinement while the planet is small; dither softens the change rather than preserving the exact coast silhouette. The second refinement is less conspicuous. This is a light visual check; Lars should judge how distracting it feels in motion.

**Landing or loading screen?** The expanding planet and final island descent communicate landing, but the opaque grey/white interval still reads as an edited cloud transition. The scene change did not expose a black frame or unfinished terrain in the checks. The measured load-to-scene-ready callback was **0.193–0.252 s**, fully behind opaque cloud cover. A load-frame pause can be masked there; it is not a seamless-streaming result. R replay from the surface passed repeatedly.

**Rough Editor frame rate:** the spike's live frame-time estimate showed about **60 fps** (roughly 60–61 rounded) during approach in the **1920×1080 Game view**, with the normal 60 fps cap. No profiling reports or automated review runners were added. This is an Editor observation on this Mac, not a standalone hardware claim.

**Change first for a real system:** make the orbit island's coastline/volcano agree with the surface destination, coordinate the orbit and Pelagic lighting, and replace the obvious white plateau with a more directional moving cloud deck/reveal. The current orbit representation and M0 island are deliberately separate scales; there is no region layer or free flight. The small cockpit is only a framing proxy. Final subjective acceptance remains Lars's playtest.

**Screenshots:** [far](Screenshots/spike-planet/far.png), [mid / about half the view](Screenshots/spike-planet/mid.png), [near / clouds and rim](Screenshots/spike-planet/near.png), [opaque cloud fade](Screenshots/spike-planet/cloud-fade.png), [arrival above the island](Screenshots/spike-planet/arrival.png).

**Final input check after unlocking:** completed another full landing (33.05 s; hidden load 0.240 s), then verified walking and Space jump after handover. The readout rose from about 5 m at the landing spot to 8 m after moving uphill, then 9 m during the jump. Unity was left out of Play mode. The earlier lock-screen interruption is resolved. Pre-existing untracked art and planning files were left untouched.
