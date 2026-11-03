using UnityEngine;

namespace TestPlanet
{
    /// <summary>One height function serves every chunk: borders can never disagree.</summary>
    public sealed class PlanetTerrain : MonoBehaviour
    {
        [SerializeField, Tooltip("Same seed produces the same coast, ridges and biome colours.")]
        int seed = 7429;
        [SerializeField, Tooltip("Square terrain width in metres.")]
        float islandSize = 600;
        [SerializeField, Range(2, 8), Tooltip("Chunks along each axis; keeps individual meshes below 65k vertices.")]
        int chunks = 4;
        [SerializeField, Range(12, 64), Tooltip("Grid cells per chunk. More cells give smaller triangular facets.")]
        int cellsPerChunk = 40;
        [SerializeField, Tooltip("Sea reference height. Match the Ocean component.")]
        float seaLevel = 0;
        [SerializeField, Tooltip("How quickly the seabed deepens beyond the shore; prevents a square shallow-water patch during drawdown.")]
        float seabedSlope = .65f;
        [SerializeField, Tooltip("Volcano position in island coordinates.")]
        Vector2 volcanoCentre = new Vector2(65, 52);
        [SerializeField, Tooltip("Crater rim height above sea level.")]
        float volcanoHeight = 120;
        [SerializeField, Tooltip("Radius of the volcano's broad walkable base.")]
        float volcanoRadius = 185;
        [SerializeField, Range(1, 2), Tooltip("Higher values give gentler outer shoulders and a more distinct upper peak.")]
        float coneShape = 1.55f;
        [SerializeField, Tooltip("Radius of the sunken bowl inside the rim.")]
        float craterRadius = 24;
        [SerializeField, Tooltip("Depth of the bowl below its rim.")]
        float craterDepth = 30;
        [SerializeField, Tooltip("Height of layered Perlin lowland hills.")]
        float lowlandHeight = 18;
        [SerializeField, Tooltip("Largest noise wavelength in metres.")]
        float noiseScale = 110;
        [SerializeField, Tooltip("Pale exposed shoreline.")]
        Color sand = new Color(.75f, .69f, .49f);
        [SerializeField, Tooltip("Muted alien ground cover.")]
        Color ground = new Color(.26f, .39f, .33f);
        [SerializeField, Tooltip("Slate exposed on steep slopes.")]
        Color rock = new Color(.29f, .34f, .40f);
        [SerializeField, Tooltip("Dark basalt above the volcano's shoulder.")]
        Color basalt = new Color(.075f, .085f, .10f);
        [SerializeField, Tooltip("URP Lit Shader Graph driven by Vertex Color → Base Color.")]
        Material terrainMaterial;
        public Material Surface => terrainMaterial;
        public Vector2 VolcanoCentre => volcanoCentre;
        public float Size => islandSize;
        public float SeaLevel => seaLevel;
        public Material Material { set => terrainMaterial = value; }

        public int TriangleCount => chunks * chunks * cellsPerChunk * cellsPerChunk * 2;
        public float Height(float x, float z)
        {
            float offset = seed * .137f;
            float n = Mathf.PerlinNoise(x / noiseScale + offset, z / noiseScale + offset);
            float detail = Mathf.PerlinNoise(x / (noiseScale * .37f) + offset, z / (noiseScale * .37f) - offset);
            // A noisy ellipse leaves a wide shelf; the square mesh edge is always underwater.
            float radius = new Vector2(x / .97f, z / .86f).magnitude;
            float coast = 246 + (n - .5f) * 40;
            float shelf = Mathf.SmoothStep(0, 1, Mathf.InverseLerp(coast + 28, coast - 46, radius));
            float lowlands = -9 + shelf * (15 + n * lowlandHeight + detail * 4);
            Vector2 relative = new Vector2(x, z) - volcanoCentre;
            float r = relative.magnitude;
            float angle = Mathf.Atan2(relative.y, relative.x);
            float warped = r * (1 + .035f * Mathf.Sin(angle * 7) + .02f * Mathf.Sin(angle * 13));
            // A shallow cone lets a CharacterController climb to the rim without a hidden staircase.
            float cone = volcanoHeight * Mathf.Pow(Mathf.Clamp01((volcanoRadius - warped) / (volcanoRadius - craterRadius)), coneShape);
            float bowl = craterDepth * (1 - Mathf.SmoothStep(0, 1, r / craterRadius));
            float hill = Mathf.Max(lowlands, cone - bowl + (detail - .5f) * 3);
            float seabed = -9 - Mathf.Max(0, radius - coast) * seabedSlope;
            return seaLevel + Mathf.Lerp(seabed, hill, shelf);
        }

        public void Generate()
        {
            float step = islandSize / (chunks * cellsPerChunk);
            for (int cz = 0; cz < chunks; cz++)
                for (int cx = 0; cx < chunks; cx++)
                {
                    var mesh = new FacetMesh();
                    for (int z = 0; z < cellsPerChunk; z++)
                        for (int x = 0; x < cellsPerChunk; x++)
                        {
                            // Compute global integer coordinates first: floating point border positions match exactly.
                            int gx = cx * cellsPerChunk + x, gz = cz * cellsPerChunk + z;
                            Vector3 a = Point(gx, gz, step), b = Point(gx, gz + 1, step);
                            Vector3 c = Point(gx + 1, gz, step), d = Point(gx + 1, gz + 1, step);
                            AddFace(mesh, a, b, c);
                            AddFace(mesh, c, b, d);
                        }

                    GameObject chunk = mesh.Create($"Terrain {cx},{cz}", transform, terrainMaterial);
                    chunk.AddComponent<MeshCollider>().sharedMesh = chunk.GetComponent<MeshFilter>().sharedMesh;
                }
        }

        Vector3 Point(int x, int z, float step)
        {
            float wx = x * step - islandSize / 2, wz = z * step - islandSize / 2;
            return new Vector3(wx, Height(wx, wz), wz);
        }

        void AddFace(FacetMesh mesh, Vector3 a, Vector3 b, Vector3 c)
        {
            Vector3 normal = Vector3.Cross(b - a, c - a).normalized;
            float height = (a.y + b.y + c.y) / 3 - seaLevel;
            Color colour = height < 5 ? sand : Color.Lerp(ground, rock, Mathf.InverseLerp(12, 65, height));
            colour = Color.Lerp(colour, rock, Mathf.InverseLerp(.25f, .7f, 1 - normal.y));
            if (height > 70)
                colour = Color.Lerp(rock, basalt, Mathf.InverseLerp(70, 96, height));
            // One colour per face, plus tiny deterministic variation, reinforces the low-poly shape.
            colour *= .94f + .12f * Mathf.PerlinNoise(a.x * .8f + seed, a.z * .8f);
            mesh.Triangle(a, b, c, colour);
        }
    }
}
