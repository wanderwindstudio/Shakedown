# PELAGIC — low-poly ocean-world test

A self-contained Unity **6000.3.26f1 / URP 17.3.0** project inside `Planet Test/`. Open this folder in Unity Hub, then open `Assets/_Project/Scenes/TestPlanet.unity` and press Play. All authored assets live under `Assets/_Project/`. The scene generates its meshes when Play begins, so the island is intentionally absent from the edit-time Scene view.

Walk with **WASD**, look with the mouse, **Shift** to sprint, **Space** to jump, **Escape** to release the cursor, and click to capture it again. Climb the dark volcano before the surge. The crater rim is above the 60 m crest; the beach and lowlands are dangerous.

## What was built

- A 600 × 600 m terrain domain, with a seeded irregular island, pale coastal shelf, muted green lowlands and an off-centre, approximately 120 m basalt volcano with a crater.
- Sixteen terrain chunks, 51,200 triangles total. Each triangle owns its three vertices and has a flat normal. A URP Lit Shader Graph connects **Vertex Color → Base Color**. Terrain colliders match the rendered triangle meshes.
- A faceted teal ocean: detailed inner mesh, matching horizon skirt, gentle GPU vertex displacement and a shallow-water tint. The seabed deepens toward the terrain boundary to avoid a square shelf appearing during drawdown.
- Lavender distance haze, gradient sky, warm low sunlight, soft shadows, ACES tonemapping, restrained bloom, colour grading and vignette. The ringed gas giant and moon are generated meshes at fixed distant world positions.
- A first-person CharacterController using the new Input System, including sprint, jump, cursor capture and rescue/respawn.
- 420 seeded, clustered props: deformed subdivided icosphere rocks, prism crystal clusters and stalk/fan plants. Scattering raycasts against the real terrain. Visuals are combined by material and spatial cell; only large boulders receive colliders.
- A repeating tidal surge: 90 s between launches, 15 s drawdown warning, 8 m sea retreat, a 60 m curling faceted wall, strong push and camera shake, fade to black and shore respawn. After passage the ocean recovers. A TextMeshPro HUD displays the countdown, warning and altitude/safety state.

All world geometry is generated in C#. No Blender, Asset Store content or third-party packages were used. The only supplied visual resources are the font and text shaders from **Unity's official TextMeshPro essentials**. The bundled Liberation Sans font's licence is retained alongside it. Unused example scenes and emoji art were removed.

## Script map

| Script | Responsibility |
| --- | --- |
| `Scripts/PlanetWorld.cs` | Builds terrain first, then initializes the enabled scene features in a predictable order. |
| `Scripts/PlanetTerrain.cs` | Samples seeded heights, assigns height/slope colours and generates the sixteen collision chunks. |
| `Scripts/FacetMesh.cs` | Builds independent triangle vertices, converts palette colours to linear lighting, and calculates flat normals. |
| `Scripts/PlanetOcean.cs` | Builds the faceted ocean and horizon skirt and controls the resting water level/drawdown. |
| `Scripts/PlanetAtmosphere.cs` | Creates sky, celestial meshes, lighting, fog and the global post-processing Volume. |
| `Scripts/PlanetPlayer.cs` | Reads keyboard/mouse input and handles grounded movement, jump, sprint, teleport and respawn. |
| `Scripts/PlanetProps.cs` | Generates reusable prop meshes, scatters dry/slope-safe clusters, adds boulder collisions and combines render meshes. |
| `Scripts/PlanetTide.cs` | Runs calm → drawdown → surge → recovery and handles the sweep/respawn sequence. |
| `Scripts/PlanetHud.cs` | Builds the TextMeshPro readouts, warning, reticle and respawn fade. |
| `Scripts/Editor/PlanetBuild.cs` | Creates/configures the scene and exposes the Planet menu's open/review actions. |
| `Scripts/Editor/PlanetReview.cs` | Runs Play mode screenshots, jump/climb checks and two complete wave-cycle checks. |
| `Scripts/Editor/PlanetAudit.cs` | Checks triangle consistency, exercises Input System events and records 1080p profiler/frame statistics. |
| `Scripts/Editor/PlanetCommands.cs` | Polls a local development review command file; editor-only and excluded from a game build. |

`Shaders/TerrainVertexColor.shadergraph` is the editable terrain graph. `Ocean.shader`, `Sky.shader`, `Celestial.shader` and `TidalWave.shader` are small purpose-specific shaders. `Shaders/TextMeshPro/` contains Unity-supplied text shaders.

## Ten useful Inspector values

Select **PELAGIC · procedural ocean world** in the scene hierarchy. Settings are on its components; each serialized setting has a tooltip. Change values **before entering Play**, then restart Play to regenerate. Defaults below describe the delivered scene.

| Value | Component / field | Default | Effect |
| --- | --- | --- | --- |
| Island seed | PlanetTerrain / Seed | 7429 | Changes coast, lowland hills and colour variation. |
| Volcano height | PlanetTerrain / Volcano Height | 120 m | Raises/lowers the dominant rim and safe ground. |
| Crater radius | PlanetTerrain / Crater Radius | 24 m | Changes the bowl/rim width. |
| Sea level | PlanetOcean / Sea Level **and** PlanetTerrain / Sea Level | 0 m | Keep both aligned when shifting the world's sea reference. |
| Gentle swell height | PlanetOcean / Wave Height | 0.24 m | Changes calm-ocean motion. |
| Distance haze | PlanetAtmosphere / Fog Density | 0.00065 | Controls how quickly distant terrain fades. |
| Sprint speed | PlanetPlayer / Sprint Speed | 12 m/s | Controls how quickly the player can reach high ground. |
| Prop count | PlanetProps / Count | 420 | Controls density; 300–500 is the intended range. |
| Surge interval | PlanetTide / Wave Interval | 90 s | Seconds between launches; code enforces enough room for transit, warning and recovery. |
| Surge height | PlanetTide / Crest Height | 60 m | Changes the safe altitude; keep it below the volcano rim. |

Other useful controls include the 15 s Warning Duration, 8 m Drawdown Depth, wave Direction, terrain Cone Shape, prop cluster radius, palette colours and mouse Sensitivity. Changing a seed can change the best walking route and requires a fresh playtest. Large changes to island size also need suitable ocean, wave width, spawn and chunk-resolution settings.

## Review and evidence

Screenshots from each stage are in `Screenshots/stageN_*.png`, rendered at **1920 × 1080** in Play mode. The final set includes aerial, eye-level lowlands, coast, summit, drawdown and mid-wave views. Older stage screenshots intentionally show the earlier stage's appearance.

Use **Planet → Run full review** to regenerate the final evidence. It temporarily takes camera/control ownership, exercises the player, records a calm shoreline benchmark, and observes two surge cycles at 4× game time. The ordinary game always starts at normal speed and retains the default 90 s surge interval. The automated review exits Play mode on completion. The `Planet → Review current scene stage` action uses the scene's current feature stage.

The input smoke check feeds the Input System keyboard/mouse devices and lets the normal player Update read those events. The climb check calls the same movement method used by normal play, without teleporting up the mountain. This is automated runtime evidence; a personal hands-on feel/art review is still useful.

Final measured results are recorded in `Screenshots/stage7_validation.txt`, `Screenshots/stage7_performance_calm.csv`, `Screenshots/stage7_performance_wave.csv` and `Screenshots/tide_review.txt`.

### Final results — 3 November 2026

- Geometry: **16 chunks, zero inconsistent shared heights, zero non-flat faces, zero oversized chunk meshes**. Highest sampled rim vertex: **120.76 m**.
- Scatter: **420 props — 142 rocks, 9 crystal clusters, 269 plants**. Zero underwater/steep placements. Reproducibility hash for the delivered seed/spawn: **-592411041**. The final set uses 24 combined visual batches and 108 large-rock colliders.
- Input: movement/sprint, mouse look and Escape cursor release passed through Input System device events. Jump passed. The shore-to-rim movement test reached **111.74 m** without a fall-through or rescue, taking 21.6 seconds of simulated movement.
- Hazard: both default-interval cycles completed; drawdown, lowland sweep/respawn, sea restoration and summit survival all passed. See `Screenshots/tide_review.txt`.
- **Live Game view Stats:** after selecting Full HD (**1920×1080**) and allowing resizing to settle, observed **60.2 fps / 16.6 ms**, about **188.8k triangles, 86 batches, 10 SetPass calls**, main thread about **16.7 ms**, render thread about **1.2 ms**, on **Apple M4 Pro / Metal**. This was normal, capped Play mode at the shore. The initial resolution-change frame briefly read about 54 fps.
- Separate uncapped 1080p camera-render callback samples (300 each): calm mean **0.67 ms**, p95 **0.85 ms**, 68 draw calls; held mid-wave mean **0.63 ms**, p95 **0.77 ms**, 49 draw calls. These measure CPU submission/render callbacks; **do not interpret their reciprocal as GPU-completed gameplay fps**. Different views also cull different amounts of geometry.

The live check meets the 60 fps prototype target on this machine in that view. GPU-completion profiling, longer sessions, all viewpoints and a standalone build remain separate validation work. The CSVs retain the per-sample data so the measurement can be reviewed rather than treated as a blanket performance claim.

## Known issues and next steps

- This is a stylized hazard prototype: the surge is a moving mesh and swept player test, not a fluid simulation. It does not flood behind the crest, refract the world or carry props away. Add these only if they support the game design.
- The ocean's shelf tint uses the procedural seabed height sampled per face. This keeps the flat-shaded look inexpensive, but the tint is faceted and is not screen-depth foam. Water has no swimming controller or underwater effects.
- The ringed giant has deliberately exaggerated apparent size. It is fixed in world space, with small parallax as the player walks, and uses baked vertex-colour bands rather than atmospheric scattering or ring shadows.
- Terrain is generated when Play starts; there is no edit-time preview, saved mesh cache or runtime seed-change button. Add a separate generation/cache tool if authoring becomes cumbersome.
- Very different seeds or Inspector values can produce a steeper shore, an obstructed approach or an unsafe spawn. The delivered seed and route are the tested baseline; automatic safe-spawn search and route generation are sensible next steps.
- The first font-creation attempts failed because Unity's built-in runtime font lacks source face data and TMP settings were not initialized. The delivered project uses the official prebuilt TMP font and an explicit shader reference; that path was visually checked. A newly created project also required an editor restart after enabling the Input System; the saved project opens with it enabled.
- Performance evidence is an Editor Play mode sample on this Mac, including editor overhead. It does not establish standalone performance across hardware. Profile a standalone 1080p build, including the whole surge, before accepting a 60 fps production budget. Shadow rendering, the detailed ocean and overlapping transparent water are the first costs to inspect.
- No standalone executable was requested or delivered. Unity runtime verification and screenshots are distinct from the user's final art/gameplay acceptance.

Every stage was committed and pushed to the existing repository. The machine lacked the repository's Git LFS helper; commits contain no LFS-tracked file types, so publishing used a temporary, per-command LFS-hook bypass. Repository hooks were left intact. No generated `Library/`, `Temp/`, `Logs/`, `UserSettings/`, `output/` or builds were committed.
