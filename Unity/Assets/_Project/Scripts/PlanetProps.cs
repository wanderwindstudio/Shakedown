using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace TestPlanet
{
    public sealed class PlanetProps : MonoBehaviour, IPlanetFeature
    {
        [SerializeField, Tooltip("Seed for all prop meshes, cluster centres and placements.")]
        int seed = 1917;
        [SerializeField, Range(300, 500), Tooltip("Number of props to place, after water and slope rejection.")]
        int count = 420;
        [SerializeField, Tooltip("Number of loose natural clusters.")]
        int clusterCount = 32;
        [SerializeField, Tooltip("Typical cluster spread in metres.")]
        float clusterRadius = 24;
        [SerializeField, Tooltip("Reject slopes steeper than this angle.")]
        float maximumSlope = 37;
        [SerializeField, Tooltip("Plants prefer terrain below this height above sea.")]
        float lowlandCeiling = 32;
        [SerializeField, Tooltip("Crystals become common above this elevation.")]
        float crystalFloor = 34;
        [SerializeField, Tooltip("Minimum dry-ground clearance above the normal sea.")]
        float shoreClearance = 2;
        [SerializeField, Tooltip("Boulders taller than this receive collision. Smaller props do not.")]
        float colliderHeight = 1.9f;
        [SerializeField, Tooltip("Boulder size range, measured as approximate radius.")]
        Vector2 rockSizes = new Vector2(.65f, 3.8f);
        [SerializeField, Tooltip("Crystal and plant size multiplier range.")]
        Vector2 organicSizes = new Vector2(.65f, 1.6f);
        [SerializeField, Tooltip("Crystal emission; small values preserve the calm atmosphere.")]
        Color crystalEmission = new Color(.12f, .55f, .49f);
        [SerializeField, Tooltip("Material used for crystals; faint emission is set during generation.")]
        Material crystalMaterial;
        [SerializeField, Tooltip("Dark slate in rock faces.")]
        Color rockDark = new Color(.21f, .27f, .33f);
        [SerializeField, Tooltip("Light grey in rock faces.")]
        Color rockLight = new Color(.42f, .44f, .47f);
        [SerializeField, Tooltip("Alien stalk colour.")]
        Color stalkColour = new Color(.30f, .35f, .38f);
        [SerializeField, Tooltip("Teal fan colour.")]
        Color fanTeal = new Color(.36f, .58f, .51f);
        [SerializeField, Tooltip("Mauve fan colour.")]
        Color fanMauve = new Color(.58f, .39f, .51f);
        System.Random random;
        readonly List<Placement> placements = new List<Placement>();
        public int PlacedCount => placements.Count;
        public string ValidatePlacements(PlanetTerrain terrain)
        {
            int dry = 0, steep = 0, rocks = 0, crystals = 0, plants = 0;
            foreach (var p in placements)
            {
                if (p.point.y < terrain.SeaLevel + shoreClearance - .01f)
                    dry++;
                if (Vector3.Angle(p.normal, Vector3.up) > maximumSlope + .01f)
                    steep++;
                if (p.kind == 0)
                    rocks++;
                else if (p.kind == 1)
                    crystals++;
                else
                    plants++;
            }

            return $"count={PlacedCount} rocks={rocks} crystals={crystals} plants={plants} underwater={dry} steep={steep} hash={PlacementHash}";
        }

        public int PlacementHash { get; private set; }

        public int LargeRockColliders { get; private set; }

        struct Placement
        {
            public Vector3 point, normal;
            public int kind, variant;
            public float scale, yaw;
        }

        float Next(float min, float max) => Mathf.Lerp(min, max, (float)random.NextDouble());
        public void Generate(PlanetWorld world)
        {
            random = new System.Random(seed);
            placements.Clear();
            PlacementHash = 17;
            var meshes = new Mesh[3, 4];
            for (int i = 0; i < 4; i++)
            {
                meshes[0, i] = Rock(i);
                meshes[1, i] = Crystal(i);
                meshes[2, i] = Plant(i);
            }

            var centres = new Vector2[clusterCount];
            for (int i = 0; i < centres.Length; i++)
                centres[i] = new Vector2(Next(-230, 230), Next(-200, 200));
            Physics.SyncTransforms();
            for (int attempt = 0; placements.Count < count && attempt < count * 80; attempt++)
            {
                Vector2 centre = centres[random.Next(centres.Length)];
                // Summing three uniform samples makes soft dense centres instead of an even sprinkle.
                Vector2 offset = new Vector2(Next(-1, 1) + Next(-1, 1) + Next(-1, 1), Next(-1, 1) + Next(-1, 1) + Next(-1, 1)) * clusterRadius;
                Vector2 p = centre + offset;
                if (Mathf.Abs(p.x) > world.Terrain.Size * .48f || Mathf.Abs(p.y) > world.Terrain.Size * .48f)
                    continue;
                if (!Physics.Raycast(new Vector3(p.x, 250, p.y), Vector3.down, out RaycastHit hit, 400))
                    continue;
                float altitude = hit.point.y - world.Terrain.SeaLevel;
                if (altitude < shoreClearance || Vector3.Angle(hit.normal, Vector3.up) > maximumSlope)
                    continue;
                var player = world.GetComponent<PlanetPlayer>();
                if (player != null && Vector3.Distance(hit.point, player.Spawn) < 9)
                    continue;
                int kind = altitude > crystalFloor ? (random.NextDouble() < .68 ? 1 : 0) : (altitude < lowlandCeiling && random.NextDouble() < .7 ? 2 : 0);
                float scale = kind == 0 ? Next(rockSizes.x, rockSizes.y) : Next(organicSizes.x, organicSizes.y);
                placements.Add(new Placement{point = hit.point, normal = hit.normal, kind = kind, variant = random.Next(4), scale = scale, yaw = Next(0, 360)});
                unchecked
                {
                    PlacementHash = PlacementHash * 31 + Mathf.RoundToInt(p.x * 100);
                    PlacementHash = PlacementHash * 31 + Mathf.RoundToInt(p.y * 100);
                }
            }

            crystalMaterial.SetColor("_EmissionColor", crystalEmission * 1.6f);
            crystalMaterial.EnableKeyword("_EMISSION");
            // Batch by material and spatial cell: 420 props use at most 48 renderers, with useful local culling.
            var batches = new Dictionary<int, List<CombineInstance>>();
            foreach (var p in placements)
            {
                int cellX = Mathf.Clamp((int)((p.point.x + 300) / 150), 0, 3), cellZ = Mathf.Clamp((int)((p.point.z + 300) / 150), 0, 3);
                int key = (cellZ * 4 + cellX) * 3 + p.kind;
                if (!batches.ContainsKey(key))
                    batches[key] = new List<CombineInstance>();
                Quaternion rotation = Quaternion.FromToRotation(Vector3.up, Vector3.Lerp(Vector3.up, p.normal, .5f)) * Quaternion.Euler(0, p.yaw, 0);
                var matrix = Matrix4x4.TRS(p.point, rotation, Vector3.one * p.scale);
                batches[key].Add(new CombineInstance{mesh = meshes[p.kind, p.variant], transform = matrix});
                if (p.kind == 0 && meshes[0, p.variant].bounds.size.y * p.scale > colliderHeight)
                {
                    var collider = new GameObject("Boulder collision");
                    collider.transform.SetParent(transform, false);
                    collider.transform.SetPositionAndRotation(p.point, rotation);
                    collider.transform.localScale = Vector3.one * p.scale;
                    collider.AddComponent<MeshCollider>().sharedMesh = meshes[0, p.variant];
                    LargeRockColliders++;
                }
            }

            foreach (var batch in batches)
            {
                var go = new GameObject($"Prop cluster batch {batch.Key}", typeof(MeshFilter), typeof(MeshRenderer));
                go.transform.SetParent(transform, false);
                var mesh = new Mesh{name = go.name, indexFormat = IndexFormat.UInt32};
                mesh.CombineMeshes(batch.Value.ToArray());
                go.GetComponent<MeshFilter>().sharedMesh = mesh;
                go.GetComponent<MeshRenderer>().sharedMaterial = batch.Key % 3 == 1 ? crystalMaterial : world.Terrain.Surface;
            }

            Debug.Log($"PROPS: placed={PlacedCount} hash={PlacementHash} batches={batches.Count} largeColliders={LargeRockColliders}");
        }

        Mesh Rock(int variant)
        {
            float t = (1 + Mathf.Sqrt(5)) / 2;
            Vector3[] v = {new Vector3(-1, t, 0), new Vector3(1, t, 0), new Vector3(-1, -t, 0), new Vector3(1, -t, 0), new Vector3(0, -1, t), new Vector3(0, 1, t), new Vector3(0, -1, -t), new Vector3(0, 1, -t), new Vector3(t, 0, -1), new Vector3(t, 0, 1), new Vector3(-t, 0, -1), new Vector3(-t, 0, 1)};
            int[] faces = {0, 11, 5, 0, 5, 1, 0, 1, 7, 0, 7, 10, 0, 10, 11, 1, 5, 9, 5, 11, 4, 11, 10, 2, 10, 7, 6, 7, 1, 8, 3, 9, 4, 3, 4, 2, 3, 2, 6, 3, 6, 8, 3, 8, 9, 4, 9, 5, 2, 4, 11, 6, 2, 10, 8, 6, 7, 9, 8, 1};
            var mesh = new FacetMesh();
            Vector3 Deform(Vector3 p)
            {
                p = p.normalized;
                float deform = .8f + .3f * Mathf.PerlinNoise(p.x * 3 + variant * 11, p.z * 3 + p.y * 2 + seed);
                p *= deform;
                p.x *= 1.2f;
                p.y = p.y * .8f + .52f;
                return p;
            }

            for (int i = 0; i < faces.Length; i += 3)
            {
                Vector3 a = v[faces[i]].normalized, b = v[faces[i + 1]].normalized, c = v[faces[i + 2]].normalized;
                Vector3 ab = (a + b).normalized, bc = (b + c).normalized, ca = (c + a).normalized;
                Color colour = Color.Lerp(rockDark, rockLight, Next(0, 1));
                mesh.Triangle(Deform(a), Deform(ab), Deform(ca), colour);
                mesh.Triangle(Deform(b), Deform(bc), Deform(ab), colour);
                mesh.Triangle(Deform(c), Deform(ca), Deform(bc), colour);
                mesh.Triangle(Deform(ab), Deform(bc), Deform(ca), colour);
            }

            return mesh.Build("Deformed icosphere " + variant);
        }

        Mesh Crystal(int variant)
        {
            var mesh = new FacetMesh();
            for (int i = 0; i < 4; i++)
            {
                float a = i * 2.4f;
                Vector3 basePoint = new Vector3(Mathf.Cos(a) * .55f, 0, Mathf.Sin(a) * .55f);
                Prism(mesh, basePoint, Next(.16f, .28f), Next(1.8f, 4.8f), 6, new Color(.2f, .72f, .67f), true);
            }

            return mesh.Build("Crystal cluster " + variant);
        }

        Mesh Plant(int variant)
        {
            var mesh = new FacetMesh();
            float height = Next(1.5f, 3.6f);
            Prism(mesh, Vector3.zero, .075f, height, 5, stalkColour, false);
            for (int i = 0; i < 7; i++)
            {
                float a = i * 2 * Mathf.PI / 7;
                Vector3 centre = Vector3.up * height;
                Vector3 tip = centre + new Vector3(Mathf.Cos(a) * .95f, .3f, Mathf.Sin(a) * .95f);
                Vector3 side = new Vector3(-Mathf.Sin(a), 0, Mathf.Cos(a)) * .32f;
                Color c = Color.Lerp(fanTeal, fanMauve, variant / 3f);
                mesh.Triangle(centre, tip + side, tip - side, c);
                mesh.Triangle(centre, tip - side, tip + side, c);
            }

            return mesh.Build("Fan plant " + variant);
        }

        static void Prism(FacetMesh mesh, Vector3 p, float radius, float height, int sides, Color colour, bool pointed)
        {
            for (int i = 0; i < sides; i++)
            {
                float a = i * 2 * Mathf.PI / sides, b = (i + 1) * 2 * Mathf.PI / sides;
                Vector3 v0 = p + new Vector3(Mathf.Cos(a) * radius, 0, Mathf.Sin(a) * radius), v1 = p + new Vector3(Mathf.Cos(b) * radius, 0, Mathf.Sin(b) * radius);
                Vector3 top = Vector3.up * height;
                mesh.Quad(v0, v0 + top, v1 + top, v1, colour);
                mesh.Triangle(v0 + top, p + top + Vector3.up * (pointed ? radius * 2 : 0), v1 + top, colour);
            }
        }
    }
}
