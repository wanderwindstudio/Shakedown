using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace TestPlanet
{
    public sealed class PlanetAtmosphere : MonoBehaviour, IPlanetFeature
    {
        [SerializeField, Tooltip("Custom gradient sky material.")]
        Material surfaceMaterial;
        [SerializeField, Tooltip("Unlit vertex-colour material for the distant celestial meshes.")]
        Material celestialMaterial;
        [SerializeField, Tooltip("Horizon and distance fog share this colour.")]
        Color horizon = new Color(.57f, .51f, .64f);
        [SerializeField, Tooltip("Deep overhead blue.")]
        Color zenith = new Color(.09f, .20f, .34f);
        [SerializeField, Tooltip("Warm amber sky glow.")]
        Color sunColour = new Color(1, .65f, .28f);
        [SerializeField, Tooltip("Fog density. Keep low enough to see the volcano across the island.")]
        float fogDensity = .00065f;
        [SerializeField, Tooltip("Gas giant fixed world position. Thousands of metres away makes walking parallax tiny.")]
        Vector3 giantPosition = new Vector3(1000, 1150, 3300);
        [SerializeField, Tooltip("Gas giant radius in metres.")]
        float giantRadius = 670;
        [SerializeField, Tooltip("Rotation of the gas giant and its rings.")]
        Vector3 ringTilt = new Vector3(-8, 0, -20);
        [SerializeField, Tooltip("Ring outer radius relative to the planet.")]
        float ringExtent = 1.85f;
        [SerializeField, Tooltip("Moon fixed world position.")]
        Vector3 moonPosition = new Vector3(3500, 1600, 400);
        [SerializeField, Tooltip("Small moon radius.")]
        float moonRadius = 125;
        [SerializeField, Tooltip("Subtle bloom intensity.")]
        float bloom = .18f;
        [SerializeField, Tooltip("Very light edge darkening.")]
        float vignette = .12f;
        [SerializeField, Tooltip("Post exposure in stops.")]
        float exposure = .1f;
        [SerializeField, Tooltip("Sun angle and orientation.")]
        Vector3 sunRotation = new Vector3(22, -38, 0);
        [SerializeField, Tooltip("Afternoon directional light energy.")]
        float sunIntensity = 2.1f;
        [SerializeField, Tooltip("Warm sunlight tint.")]
        Color lightColour = new Color(1, .81f, .61f);
        [SerializeField, Tooltip("Colour grading saturation adjustment.")]
        float saturation = -7;
        [SerializeField, Tooltip("Colour grading contrast adjustment.")]
        float contrast = 7;
        public void Generate(PlanetWorld world)
        {
            Light sun = RenderSettings.sun;
            sun.transform.rotation = Quaternion.Euler(sunRotation);
            sun.color = lightColour;
            sun.intensity = sunIntensity;
            sun.shadows = LightShadows.Soft;
            surfaceMaterial.SetColor("_Horizon", horizon);
            surfaceMaterial.SetColor("_Zenith", zenith);
            surfaceMaterial.SetColor("_SunColor", sunColour);
            surfaceMaterial.SetVector("_SunDirection", -sun.transform.forward);
            RenderSettings.skybox = surfaceMaterial;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.33f, .40f, .52f);
            RenderSettings.ambientEquatorColor = new Color(.30f, .34f, .38f);
            RenderSettings.ambientGroundColor = new Color(.18f, .22f, .24f);
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogColor = horizon;
            RenderSettings.fogDensity = fogDensity;
            Camera.main.clearFlags = CameraClearFlags.Skybox;
            var volume = new GameObject("Atmosphere · ACES / bloom / grade").AddComponent<Volume>();
            volume.transform.SetParent(transform);
            volume.isGlobal = true;
            var profile = ScriptableObject.CreateInstance<VolumeProfile>();
            volume.sharedProfile = profile;
            profile.Add<Tonemapping>().mode.Override(TonemappingMode.ACES);
            var b = profile.Add<Bloom>();
            b.intensity.Override(bloom);
            b.threshold.Override(1.1f);
            var colour = profile.Add<ColorAdjustments>();
            colour.postExposure.Override(exposure);
            colour.saturation.Override(saturation);
            colour.contrast.Override(contrast);
            profile.Add<Vignette>().intensity.Override(vignette);
            Celestial("Aster · ringed gas giant", giantPosition, giantRadius, true);
            Celestial("Small companion moon", moonPosition, moonRadius, false);
        }

        void Celestial(string name, Vector3 position, float radius, bool ringed)
        {
            var mesh = new FacetMesh();
            const int slices = 64, rows = 32;
            Vector3 Sphere(int row, int slice)
            {
                float latitude = Mathf.PI * row / rows, longitude = 2 * Mathf.PI * slice / slices;
                return radius * new Vector3(Mathf.Sin(latitude) * Mathf.Cos(longitude), Mathf.Cos(latitude), Mathf.Sin(latitude) * Mathf.Sin(longitude));
            }

            for (int row = 0; row < rows; row++)
                for (int slice = 0; slice < slices; slice++)
                {
                    Vector3 a = Sphere(row, slice), b = Sphere(row + 1, slice), c = Sphere(row + 1, slice + 1), d = Sphere(row, slice + 1);
                    float stripe = .5f + .5f * Mathf.Sin(row * 1.8f + Mathf.Sin(row * .7f));
                    Color colour = ringed ? Color.Lerp(new Color(.33f, .36f, .45f), new Color(.81f, .65f, .47f), stripe) : new Color(.64f, .65f, .70f);
                    // Baked light keeps the celestial bodies unlit yet readable, independent of local fog and shadows.
                    float light = .32f + .68f * Mathf.Clamp01(Vector3.Dot(((a + b + c) / 3).normalized, new Vector3(.6f, .3f, -1).normalized));
                    mesh.Quad(a, b, c, d, colour * light);
                }

            var body = mesh.Create(name, transform, celestialMaterial);
            body.transform.position = position;
            body.transform.rotation = Quaternion.Euler(ringTilt);
            body.GetComponent<MeshRenderer>().shadowCastingMode = ShadowCastingMode.Off;
            if (!ringed)
                return;
            var rings = new FacetMesh();
            for (int band = 0; band < 12; band++)
            {
                if (band == 7)
                    continue; // One narrow gap makes the ring read clearly from the shore.
                float r0 = radius * Mathf.Lerp(1.18f, ringExtent, band / 12f), r1 = radius * Mathf.Lerp(1.18f, ringExtent, (band + 1) / 12f);
                Color colour = Color.Lerp(new Color(.32f, .35f, .43f), new Color(.65f, .57f, .49f), (.5f + .5f * Mathf.Sin(band * 2)));
                for (int i = 0; i < 128; i++)
                {
                    float a = 2 * Mathf.PI * i / 128, b = 2 * Mathf.PI * (i + 1) / 128;
                    Vector3 P(float r, float t) => new Vector3(Mathf.Cos(t) * r, 0, Mathf.Sin(t) * r);
                    rings.Quad(P(r0, a), P(r0, b), P(r1, b), P(r1, a), colour);
                }
            }

            var ring = rings.Create("Layered ring with gap", body.transform, celestialMaterial);
            ring.GetComponent<MeshRenderer>().shadowCastingMode = ShadowCastingMode.Off;
        }
    }
}
