using UnityEngine;

namespace TestPlanet
{
    public interface IPlanetFeature
    {
        void Generate(PlanetWorld world);
    }

    [DefaultExecutionOrder(-100)]
    public sealed class PlanetWorld : MonoBehaviour
    {
        [SerializeField, Tooltip("Completed feature stage (1–7). Also used for staged screenshot review.")]
        int stage = 1;
        [SerializeField, Tooltip("Frame rate limit during normal play. The review temporarily unlocks this for measurement.")]
        int targetFrameRate = 60;
        [SerializeField, Tooltip("Procedural terrain settings.")]
        PlanetTerrain terrain;
        public PlanetTerrain Terrain => terrain;
        public int Stage { get => stage; set => stage = value; }

        public void Configure(PlanetTerrain value)
        {
            terrain = value;
        }

        void Awake()
        {
            Application.targetFrameRate = targetFrameRate;
            Application.runInBackground = true;
            terrain.Generate();
            // Terrain comes first because spawning and scattering use its real triangle colliders.
            foreach (var feature in GetComponents<IPlanetFeature>())
                feature.Generate(this);
        }
    }
}
