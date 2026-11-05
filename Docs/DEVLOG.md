# Shakedown devlog

Running log of **decisions**, **ideas** and **to-dos**. Newest entries first within each section. Claude maintains this file; anyone may add to it.

- **Decisions** are settled. Change one only by adding a new decision that supersedes it.
- **Ideas** are parked: worth keeping, not scheduled.
- **To-dos** name an owner: Lars, Claude (design, prompts, reviews), Sol (Unity code), Opus (Blender assets).

Related files: `Docs/Specs/section-standard.md` (to be rewritten for blocks), `Docs/Prompts/`, `Art/Concepts/`.

---

## Decisions

### 2026-11-04: Planets and landing

- **D-42 Shape language: low poly, but never blocky.** The grid is logic, not looks: furniture snaps to blocks for gameplay, its shapes must not read as blocks, and small items don't snap at all. Rules for every asset: bevel every hard edge (2–5 cm); add secondary shapes (inset fronts, raised/recessed panels, handles, lips, brackets, trims); round things get 12–16 sides and pipes bend; soft goods drape and sag (sculpted low poly, no simulation); in dressed rooms, small items are slightly rotated, crooked, leaning and overlapping; vary thickness (thin shelves, chunky counters, slim brackets). Budget up to 2,500 triangles for larger pieces.
- **D-41 Main look target: `Art/Concepts/AI-mockups/look_target_cabin.png`** (Lars: "This is it."). Takes precedence over `look_target_quarters.png`, which stays as a secondary reference. Small, tight but not cramped: essentials on the floor (bed, kitchenette, stool), everything else on the walls (high shelves, jars, fold-down desk, lantern, pinned pictures), one clear 1-block walkway, every piece has a use. Light: several small warm sources against the cool window view. Open: the room looks about 3 blocks wide × 4 long; test in a Gangway or rotated Cabin, or add a seventh compartment "Berth" (3 × 3 × 4, H × W × L). Kit additions to make after the current kit: high wall shelves, storage jars, moka pot, lantern, stool, tea towel.
- **D-40 Official look target: `Art/Concepts/AI-mockups/look_target_quarters.png`.** The mood comes from light and colour, not the models: strong contrast with most of the room in shadow, a low sun through the window throwing a warm shaft across the floor, lamps as small warm pools, cool blue-grey shadows against warm orange-gold light, muted grey painted-metal walls with wear, a dark foreground frame. Consequence: the look is built and judged **in Unity** (lighting, shadows, colour grading, bloom, vignette, a fake light shaft), not in Blender renders. Blender assets are judged on shapes, proportions and furniture only.
- **D-39 Three placement layers inside the ship:** (1) floor furniture on the block grid (bed, smelter, lockers), (2) wall panels, one per wall slot (cabinets, fold-out table, porthole, terminal), (3) small items placed freely on counters, tables and walls without using a block or slot (coffee machine, light switch, mug, lamp, pictures). Placement rules: the smelter stands against an outer wall (vents heat through the hull); the suit station stands next to the entrance.
- **D-38 Spacing between compartments:** a compartment's footprint is its interior plus 0.5 m on every side. Touching compartments therefore have exactly 1 m between their interiors, and the block grid stays aligned across the ship. A doorway fills that 1 m with a door frame 1.0 m deep; a joint collar closes the gap on the outside. One deck only for now.
- **First Explorer furniture list:** bed, two chairs with a fold-out wall table, wet cell (toilet/shower, 1 × 1 × 2), overhead wall cabinets, kitchenette (1 × 1 × 1), bookshelf, light switch panel, coffee machine, smelter, compactor, suit station, storage lockers, fabricator, ship terminal, sample analyser. A Cabin's 12 floor blocks can't fit the smelter and compactor as well, so the first ship already wants a second compartment (D-24 working as intended).
- **D-37 Order of work: ship first, planets later.** The planet spike proved the pipeline (handoff, hidden load, detail switching), not that planets can look good or match their landing site. So: (1) interior prefabs in Blender (furniture kit with merge variants and wall panels; grounded material pass on the six compartments), (2) building and furnishing in Unity (compartment placement, door cutting, furniture on the block grid, wall-slot swaps, merging), (3) a rudimentary space to fly in (open: piloted from the command chair, or star-map travel?), (4) only then planets. The site-size spike waits until step 4.

- **D-33 Landing only in curated landing zones** (Lars' idea): an ocean world's sunken volcano crater with islands and shallows (Subnautica style), a lava plateau, a forest clearing. One landing zone per planet at first; a shuttle or rover from the hangar module can later open more of the region (progression by capability).
- **D-36 Landing-site size is a test variable, not a fixed number** (amends D-35). Content grows with area: doubling the diameter means four times the ground to fill. The question is which size stays interesting to walk and keeps the game finishable. Tested with `Docs/Prompts/spike-site-size.md` at 1, 2 and 3 km, with the same density of resource nodes and landmarks at every size. Lars plays each size for about 10 minutes and notes when it got boring, whether it felt big or small, and whether he'd want to come back.
- **D-35 Each planet is one circular landing site, about 3 km across, with natural borders** (refines D-33; D-34's region layer becomes "later, maybe"). Borders by planet type: crater rim or deep rough water (ocean), lava rivers and cliffs (volcanic), dense woods and ravines (forest), crevasses (ice), a sandstorm wall (desert). Behind them, a ship-computer warning and a soft push back; invisible walls only where nature can't do the job. Beyond the border, a **backdrop ring** of low-poly distant mountains, coastline and forest silhouettes fading into haze makes the planet feel endless. Content: procedural terrain plus hand-placed landmarks (crater, waterfall, wreck, Survey Logbook spots). The first planet may start at 1.5–2 km and grow. Quirks must scale: e.g. several safe high points on Pelagic. Landing itself: the minimal version (D-28): orbit, cloud fade, site loads.
- **D-34 Later, maybe: a three-layer descent that feels continuous.** The ship computer flies the descent, so detail only has to exist along its path:
  1. **Sphere** (orbit to high atmosphere): faceted planet, clouds, atmosphere rim. Rendered small and close to look huge ("scaled space", as in Kerbal Space Program).
  2. **Region** (high atmosphere to about 1 km): one terrain tile of roughly 20 × 20 km around the landing zone: mountains, lakes, rivers, forests in low poly; haze hides its edges.
  3. **Site** (last kilometre, on foot): the detailed landing zone, 1–2 km across, like M0's Pelagic island.
  Handoffs between layers are hidden in cloud decks and haze. One seed generates all three layers, so what you see from orbit is where you land; landmarks are hand-placed. Each planet type is a kit (colour ramp, terrain noise, water level, prop set). Not feasible and not planned: landing anywhere, walking across continents, free flight to any spot. Order: spike 1 (sphere + cloud handoff) → spike 2 (region layer) → full system (about 3–5 Sol stages).

### 2026-11-04: Space and exteriors

- **D-32 Art direction: grounded low poly with watercolour textures** (corrects D-31). Watercolour stays as the medium; the subject becomes realistic: real proportions, real materials (painted metal, gunmetal frames, worn edges, steel floors with grates), grounded light, muted neutral colours with orange accents. Avoid the "cutesy" look: no oversized rounded toy shapes, no candy pastels. Warmth comes from lamps, plants, books and rugs. The warm white interior panels stay. Cockpit reference: `mockup_cockpit_v3.png`. Cockpit size: 3 × 3 × 5 blocks (H × W × L); blocks measure size only, the cockpit's shape is a faceted, tapering nose; only its rear wall follows the compartment slot system. Brief: `Docs/Prompts/blender-cockpit-v3.md`.
- **D-31 Superseded by D-32.** (Was: the whole game moves to realistic low poly without watercolour.) Reference: `Art/Concepts/AI-mockups/concept_sheet_deltawing.png`: grey-white hull panels with orange accents, darker and more worn interiors, natural light, dark space. Next art order: cockpit (interior + nose) → material pass on the six compartments → engine section → exterior hero parts (wings, legs, dish, antennas) → furniture kit. In parallel: Sol builds compartment placement in Unity.

- **D-30 Space is realistic low poly, not pastel watercolour** (supersedes the look in D-29; the layer structure stays). Near-black background, sharp stars in real star colours (generated in code), an optional faint desaturated Milky Way band. Planets are faceted spheres with natural palettes (one small colour ramp per planet), lit by one strong sun with a dark night side, a sharp terminator and a thin atmosphere rim. Rings and clouds are faceted geometry. Colourful nebulas only later, as rare highlights. Planet LOD = more facets when closer (about 300 / 1,300 / 5,000 faces) via a Unity LOD Group. Open: does the ship keep its watercolour look, and does the screen-wide watercolour pass apply to space?
- **D-29 Space is a painted backdrop, not a place you fly through.** Layers: painted skybox panorama, a subtle twinkling star layer, a few transparent nebula cards at different depths (parallax during fake-motion travel), planets and gas giants as spheres with painted equirectangular textures, rings as a painted strip, the sun as a glowing sprite, low-poly asteroids with watercolour textures. The screen-wide watercolour pass unifies space, ships and planets.
- **D-28 Planet level of detail stays minimal**, because there is no seamless space-to-planet flight (D-3): a planet seen from space has 2–3 states (far: small sphere; near: sphere + cloud layer + atmosphere rim glow; arrival: fade into a painted cloud/entry sequence, then the surface scene loads). Texture detail is handled by Unity's automatic mipmaps. Ships only need interiors hidden from outside (occlusion) and at most one simplified exterior level.
- **Exterior direction:** follow the concept sheets in `Art/Concepts/AI-mockups/`. `concept_sheet_deltawing.png` was replaced on 2026-11-04 by a realistic low-poly version (dark space, natural light, grey-white hull with orange accents, hull number "DS-17"); it is now the main reference. `concept_sheet_ships.png` is the older, pastel take: modular sections with dressed exteriors, a nose and engines on every ship, antennas, dishes, solar panels, lit windows. Ship names on the sheets (Explorer, Surveyor, Carrier) are example builds, not classes.

### 2026-11-04: Ship interiors

- **D-27 Blender builds the six compartments without doors; Unity cuts the doors.** Every wall, floor and ceiling is built from separate 1 × 1 m slot objects spanning the full wall thickness. A doorway in Unity = remove two stacked slots and add a door frame. The same slots are swapped for wall furniture (D-17). Walls are 0.35 m thick (0.3 m recess depth), interior chamfers 0.5 m on the upper long edges, ribs protrude at most 0.05 m, furniture keeps a 0.05 m gap to walls. Brief: `Docs/Prompts/blender-compartments.md`.
- **D-26 Compartments are empty shells; the player furnishes them on a 1 m block grid.** A block is 1 × 1 × 1 m of *usable interior space*. Walls, ribs and pipes sit outside the blocks, so they never steal furniture space.
- **D-25 Base compartment set** (interior size in blocks, H × W × L):
  - Nook 2 × 2 × 2 (storage)
  - Skylight 2 × 4 × 3 (low, glass ceiling, cosy)
  - Cabin 3 × 4 × 3
  - Bay 4 × 5 × 4
  - Hall 5 × 6 × 5
  - Gangway 3 × 2 × 4 (corridor piece)
  - Cockpit: hand-built, unique
- **D-24 Furniture has a fixed size in blocks** (bed 1 × 2, wardrobe 2 × 2, ...). Limited space in early ships creates the wish to expand and to build space-efficiently. Motivation without progression numbers.
- **D-23 Shared floor level.** All compartments have their floor at the same height; taller rooms only grow upward.
- **D-22 Doorways are 1 block wide × 2 blocks tall**, on any wall block at floor level. Two compartments connect where both have a doorway in the same place. The player chooses door positions.
- **D-21 Access rule.** Each piece of furniture has one access side that must stay free, and a path of free floor blocks must lead to it from a door.
- **D-20 The chamfered top edge row of blocks is overhead-only** (cabinets, shelves, lights, pipes); no floor furniture there.
- **D-19 Minimum height 3 blocks for rooms you walk through daily.** 2 blocks only for the Skylight and the Nook.
- **D-18 Furniture of the same family merges with its neighbours** (like a Minecraft double chest): single, left end, middle, right end, inner and outer corner variants. Merging is visual only; each piece stays its own item in the game logic.
- **D-17 Wall furniture is built into the wall.** Walls are a grid of swappable 1 × 1 m panels with about 0.3 m of depth behind them. A wall cabinet, shelf niche, light, vent, screen or porthole *replaces* a plain panel instead of sitting in front of it. Wall slots are a separate resource from floor blocks.
- **D-16 Compartments come from one Blender generator script** (input: H, W, L in blocks), so every size has exactly the same style. The cockpit is hand-built.

### 2026-11-03: Art and assets

- **D-15 Opus 5.5 builds the Blender assets.** It won the quarters comparison against Sol (cleaner, closer to the mockup, about 5,100 triangles).
- **D-14 Triangle budget:** section shell ≤ 8,000, prop ≤ 1,500. Explorer-sized ship under 100,000 in total. Performance risks to watch: transparency, real-time lights and shadows, the watercolour screen pass, draw calls.
- **D-13 Model half and mirror; prefer parts that work by rotation**, so no left/right versions are needed. Keep text off mirrored parts.
- **D-12 Style target: the v2 mockups** (`Art/Concepts/AI-mockups/`): chamfered octagon cross-section, dark rib frames, pipes along the upper chamfers, cream/sage/ochre/slate palette, warm light strips, lived-in props.
- **D-11 AI art first, replaced by Lars' own work over time.** Every asset is listed in `Docs/Credits.md` as AI placeholder or made by Lars (also needed for Steam's AI disclosure).
- **D-10 Watercolour look:** low-poly, flat-shaded models with hand-painted watercolour textures. Textures are greyscale and light, tinted by the material colour, seamless, painted at 1024 × 1024 sRGB. They're projected (box/triplanar), so models need no UV unwrapping. A subtle screen-wide watercolour pass (paper grain, edge darkening) comes later in Unity.

### 2026-11-03: Ship building

- **D-9 Ships are assembled from pre-built sections** (Starbound/Starfield middle ground). The ship starts as a fixed starter section built as the cadet's final exam; the player expands it in any direction.
- **D-8 Sections are spaces, not functions.** Machines and crafting stations are placeable objects; any room becomes a workshop by putting machines in it.
- **D-7 Cosmetics** (wings, fins, antennas, panels, paint) give ships their character and are purely cosmetic.
- **D-6 Small ships must be as viable as large ones.** Every essential machine has a compact footprint.
- **D-5 Superseded: free block building.** The block builder with auto-shaping (M1a, M1b; Git tags `m1a`, `m1b`) worked, but felt like a crude Space Engineers, and auto-shaping opened gaps at diagonal joints. Replaced by D-9.

### 2026-11-03: Travel and flight

- **D-4 The ship computer flies.** Travel via a star map with short take-off and landing sequences. During autopilot the ship stands still and the world moves past outside, so the player can walk around freely.
- **D-3 Manual flight, if ever added, only from the command chair** (seated during flight), using simple stats-based arcade handling. No seamless space-to-planet flight.

### 2026-11-03: Project

- **D-2 Working title Shakedown.** Repo `wanderwindstudio/Shakedown`, Unity project in `Unity/`, Git LFS enabled. Agents work one stage per session with light verification.
- **D-1 The three core systems** are ship building, planets and universe, and mining and processing. Each must be fun alone and interlock with the others. Ship building comes first.

### Earlier (from the handoff notes)

- Unity 6 + URP (HDRP is in maintenance mode and aims for photorealism; Unreal is harder to steer as a beginner).
- No ship classes or progression numbers; access is gated by capabilities, never by ship size.
- No enemies at launch. Motivation comes from exploration and the optional Survey Logbook.
- Ship computer: intent matching and pre-written voice lines first; a local LLM maybe later.

---

## Open questions

- **Ship layout:** spine with side rooms (recommended), train, or hub? Affects which walls need doorways.
- **Exterior look:** visible modules with a shared hull language (octagon, outer rib rings, rounded end caps where no neighbour) plus silhouette pieces (nose, tail, legs, fins)? Recommended, not yet confirmed.
- Vertical connections: hatches and ladders between compartments of different heights?
- Machine footprints in blocks, power rules, first recipes.
- Maximum ship size.

---

## Ideas (parked)

- **Drone bay module:** drones gather common resources from orbit (water, iron, ice); rare finds, quirks and wonders still need the player on the ground. An extra capability, never a replacement for landing.
- **Vertical slice "First Voyage":** final exam on Earth, take-off, hyperjump, landing on Pelagic, exploring, mining, upgrading the ship, flying on to a second planet. Proposed as the next big goal after the ship builder.
- Pelagic's drawdown exposes the seabed for 15 seconds: rare finds out there, so players decide how greedy to be.
- Part designer: sculpt a part at 16³ and bake it into one reusable piece.
- Paint brush per face plus a paint bucket; automatic interior/exterior defaults.
- Exterior variants per section (same interior, different hull shell).
- Piloted landings; a fixed-design shuttle with real flight.
- Trophy room for Survey Logbook souvenirs.
- Watercolour treatment for terrain, water (two sliding layers), sky and gas giant.
- Steam Workshop for blueprints and parts.
- M0 polish, if Pelagic is reused: larger terrain facets, calmer colour noise, clean beach edge, flat-shaded moon, haze on sky objects, sky/fog seam.

---

## To-dos

| Owner | Task | Status |
|---|---|---|
| Lars | Space set (realistic low poly, D-30): planet colour ramps (Pelagic, gas giant bands), sun glow, optional faint Milky Way band | Open |
| Lars | Decide whether the ship keeps its watercolour look or moves to realistic low poly too | Done (D-32: grounded low poly, still watercolour) |
| Claude | Rewrite the cockpit brief for the new direction | Done (`blender-cockpit-v3.md`) |
| Opus | Build the cockpit v3 | Done (corrected after one feedback round; long low wedge) |
| Sol | Spike: orbit-to-surface approach (`Docs/Prompts/spike-planet-approach.md`) | Done (`spike-planet`, report `Docs/Spike-planet-report.md`): 33 s orbit to ground, 0.2 s hidden load, 60 fps, soft LOD switches. Planets are feasible. Look not yet: per-face colour noise instead of continents, clouds blur into the surface, white-screen cloud fade, orbit and surface don't match |
| Lars | Play `OrbitTest.unity` once (L approach, R replay) and judge the feel | Open |
| Lars | Commit `Art/` and `Docs/` (add `.DS_Store` to `.gitignore`) and push | Open |
| Sol | Spike: landing-site size at 1 / 2 / 3 km (`Docs/Prompts/spike-site-size.md`) | Parked until planets (D-37) |
| Lars | Play each site size for about 10 minutes and note boredom, sense of size, wish to return | After the size spike |
| Claude | Spike 2 brief: region layer seen through the clouds (D-34) | Deferred (D-35) |
| Lars | Decide ship layout (spine / train / hub) | Open |
| Lars | Draw a top-down floor plan of the cockpit | Open |
| Lars | Redo `tex_interior_wall` (panel lines aligned to tile edges, or none) | Open |
| Lars | Start `Docs/Credits.md` (AI placeholder vs own work) | Open |
| Lars | Push local commits to GitHub (`git push --follow-tags`) | Check |
| Claude | Rewrite `section-standard.md` for blocks, wall panels and merging | Next |
| Opus | Build the six compartments (`Docs/Prompts/blender-compartments.md`) | Done (`Art/Blender/Compartments_Opus/`) |
| Claude | Brief for Opus: compartment generator plus the six compartments | Done |
| Sol | Compartment builder in Unity: place compartments, cut doors by removing slots, swap wall slots | Later |
| Claude | Brief for Opus: cockpit (from Lars' sketch and mockup v2) | Superseded by the v3 brief |
| Claude | Brief for Opus: furniture kit (floor furniture with merge variants, wall panels) | Done (`Docs/Prompts/blender-furniture-kit.md`) |
| Opus | Furniture kit + material pass on the six compartments (`blender-furniture-kit.md`, now incl. wet cell, kitchenette, chairs, fold-out table, compactor, suit station, analyser, terminal, door, small items) | In progress |
| Sol | M1c: ship assembly in Unity: placing compartments, cutting doors, walking through (`Docs/Prompts/M1c-assembly.md`) | Done (`m1c`, report `Docs/M1c-report.md`). Placeholder materials and doors. Notes: interior floor sits 0.5 m above the pad; Nook doors only on long walls; cockpit FBX has 4 self-intersecting polygons (fix in Blender later) |
| Lars | Playtest M1c (`ShipAssembly.unity`): does assembling a ship feel good? | Open |
| Claude | M1d brief: furnishing in Unity with Opus' kit (floor grid, wall-slot swaps, merging, small items) | After the furniture kit |
| Claude | Look-dev brief for Sol: lighting, colour grading and post-processing in Unity, target `look_target_quarters.png` (D-40) | After the furniture kit |
| Lars | Decide step 3: piloted flight from the command chair, or star-map travel? | Open |
| Claude | Update the M1 roadmap v2 and the GDD to the block-based compartments | Next |
| Sol | M1c: compartment placement in Unity | Replaced by `M1c-assembly.md` |
