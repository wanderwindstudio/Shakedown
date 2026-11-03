using UnityEngine;

namespace TestPlanet
{
    public sealed class PlanetOcean : MonoBehaviour, IPlanetFeature
    {
        [SerializeField, Tooltip("Water surface shader. Material is kept as an asset for build inclusion.")]
        Material surfaceMaterial;
        [SerializeField, Tooltip("Resting water height; match Terrain's sea reference.")]
        float seaLevel = 0;
        [SerializeField, Tooltip("Detailed inner ocean width, in metres.")]
        float width = 1800;
        [SerializeField, Range(40, 180), Tooltip("Number of low-poly wave cells along the detailed ocean.")]
        int cells = 140;
        [SerializeField, Tooltip("Outer ocean edge; far enough to meet the haze.")]
        float horizonDistance = 10000;
        [SerializeField, Tooltip("Small wave amplitude; kept low to avoid shoreline flicker.")]
        float waveHeight = .24f;
        [SerializeField, Tooltip("Gentle wave travel speed.")]
        float waveSpeed = .65f;
        [SerializeField, Tooltip("Wave spatial frequency.")]
        float waveFrequency = .075f;
        [SerializeField, Tooltip("Deep teal water colour.")]
        Color deepWater = new Color(.035f, .29f, .29f, .96f);
        [SerializeField, Tooltip("Lighter turquoise over the shelf.")]
        Color shallowWater = new Color(.30f, .63f, .53f, .96f);
        Transform water;
        public float Level => water == null ? seaLevel : water.position.y;
        public float RestLevel => seaLevel;
        public void SetDrawdown(float drop)
        {
            if (water != null)
                water.position = Vector3.up * (seaLevel - drop);
        }

        public void Generate(PlanetWorld world)
        {
            var mesh = new FacetMesh();
            float step = width / cells;
            Vector3 P(int x, int z) => new Vector3(x * step - width / 2, 0, z * step - width / 2);
            Color Depth(Vector3 p)
            {
                // Alpha stores seabed height, rather than opacity, so drawdown also moves the pale shelf band.
                return new Color(1, 1, 1, world.Terrain.Height(p.x, p.z));
            }

            for (int z = 0; z < cells; z++)
                for (int x = 0; x < cells; x++)
                {
                    Vector3 a = P(x, z), b = P(x, z + 1), c = P(x + 1, z), d = P(x + 1, z + 1);
                    mesh.Triangle(a, b, c, Depth((a + b + c) / 3));
                    mesh.Triangle(c, b, d, Depth((c + b + d) / 3));
                }

            // A cheap four-sided skirt extends the horizon without spending triangles far from the player.
            float inner = width / 2, outer = horizonDistance;
            for (int i = 0; i < 4; i++)
                for (int segment = 0; segment < cells; segment++)
                {
                    Quaternion rotation = Quaternion.Euler(0, 90 * i, 0);
                    float a = -inner + segment * step, b = a + step;
                    mesh.Quad(rotation * new Vector3(a, 0, inner), rotation * new Vector3(a * outer / inner, 0, outer), rotation * new Vector3(b * outer / inner, 0, outer), rotation * new Vector3(b, 0, inner), new Color(1, 1, 1, -100));
                }

            water = mesh.Create("Ocean · faceted swell", transform, surfaceMaterial).transform;
            water.position = Vector3.up * seaLevel;
            surfaceMaterial.SetColor("_Deep", deepWater);
            surfaceMaterial.SetColor("_Shallow", shallowWater);
            surfaceMaterial.SetVector("_Wave", new Vector4(waveHeight, waveSpeed, waveFrequency, 0));
        }
    }
}
