using System.Collections;
using UnityEngine;

namespace TestPlanet
{
    public sealed class PlanetTide : MonoBehaviour, IPlanetFeature
    {
        public enum TidePhase
        {
            Calm,
            Drawdown,
            Wave,
            Recovery
        }

        [SerializeField, Tooltip("Seconds between wave launches. First launch uses the same interval.")]
        float waveInterval = 90;
        [SerializeField, Tooltip("Seconds of visible drawdown and HUD warning before launch.")]
        float warningDuration = 15;
        [SerializeField, Tooltip("Wave crest height above the resting sea. The 120m rim stays safe.")]
        float crestHeight = 60;
        [SerializeField, Tooltip("Water level drop during warning, in metres.")]
        float drawdownDepth = 8;
        [SerializeField, Tooltip("Wave travel speed in metres per second.")]
        float travelSpeed = 38;
        [SerializeField, Tooltip("Wave travel direction in X/Z world space.")]
        Vector2 direction = new Vector2(1, .18f);
        [SerializeField, Tooltip("Distance beyond each terrain edge where the wave starts and finishes.")]
        float offshoreMargin = 180;
        [SerializeField, Tooltip("Total wave width, including both sides of the island.")]
        float waveWidth = 1100;
        [SerializeField, Range(20, 100), Tooltip("Triangular facets across the curved wave wall.")]
        int waveSegments = 72;
        [SerializeField, Tooltip("Time to restore sea level after the wave passes.")]
        float recoveryDuration = 6;
        [SerializeField, Tooltip("Time to fade back in after respawn.")]
        float fadeInDuration = .65f;
        [SerializeField, Tooltip("Duration of the violent push, shake and fade before respawn.")]
        float sweepDuration = 1.6f;
        [SerializeField, Tooltip("Push speed in metres per second.")]
        float pushSpeed = 32;
        [SerializeField, Tooltip("Maximum camera shake offset in metres.")]
        float shakeAmount = .28f;
        [SerializeField, Tooltip("Low-poly water wall shader material.")]
        Material surfaceMaterial;
        [SerializeField, Tooltip("Wave cross-section. X is forward distance; Y is height for a 60m reference crest.")]
        Vector2[] profile = {new Vector2(-100, -8), new Vector2(-80, 12), new Vector2(-45, 40), new Vector2(-15, 60), new Vector2(3, 59), new Vector2(17, 51), new Vector2(19, 36), new Vector2(13, 13), new Vector2(18, -8)};
        PlanetOcean ocean;
        PlanetPlayer player;
        PlanetHud hud;
        Transform wall;
        Vector3 travelDirection;
        float clock, nextLaunch, launchedAt, distance, lastFront;
        bool hitThisWave, sweeping;
        public TidePhase Phase { get; private set; }

        public float Countdown => Mathf.Max(0, nextLaunch - clock);
        public int WavesLaunched { get; private set; }

        public int Sweeps { get; private set; }

        public float WaveCoordinate => -distance / 2 + (clock - launchedAt) * travelSpeed;
        public float Crest => ocean.RestLevel + crestHeight;
        public void Generate(PlanetWorld world)
        {
            ocean = world.GetComponent<PlanetOcean>();
            player = world.GetComponent<PlanetPlayer>();
            hud = world.GetComponent<PlanetHud>();
            travelDirection = new Vector3(direction.x, 0, direction.y).normalized;
            if (travelDirection.sqrMagnitude < .5f)
                travelDirection = Vector3.right;
            distance = world.Terrain.Size * Mathf.Sqrt(2) + offshoreMargin * 2;
            // Leave room for transit and recovery even if an Inspector interval is set too short.
            waveInterval = Mathf.Max(waveInterval, distance / travelSpeed + recoveryDuration + warningDuration + 1);
            nextLaunch = waveInterval;
            Phase = TidePhase.Calm;
            wall = BuildWall();
            wall.gameObject.SetActive(false);
            hud.Initialize(this, player);
        }

        Transform BuildWall()
        {
            var mesh = new FacetMesh();
            // Cross-section is a curling lip, rather than a vertical box. Z points in the direction of travel.
            for (int x = 0; x < waveSegments; x++)
                for (int p = 0; p < profile.Length - 1; p++)
                {
                    Vector3 Point(int column, int row)
                    {
                        float u = (float)column / waveSegments;
                        float bend = Mathf.Sin(u * Mathf.PI * 2) * 5;
                        float y = profile[row].y / 60 * crestHeight;
                        return new Vector3((u - .5f) * waveWidth, y, profile[row].x + bend);
                    }

                    float foam = Mathf.InverseLerp(crestHeight * .74f, crestHeight, (profile[p].y + profile[p + 1].y) / 120 * crestHeight);
                    Color colour = Color.Lerp(new Color(.045f, .32f, .34f), new Color(.72f, .87f, .79f), foam);
                    mesh.Quad(Point(x, p), Point(x + 1, p), Point(x + 1, p + 1), Point(x, p + 1), colour);
                }

            var go = mesh.Create("Tidal wall · curved crest", transform, surfaceMaterial);
            go.transform.rotation = Quaternion.LookRotation(travelDirection);
            return go.transform;
        }

        void Update()
        {
            if (wall == null)
                return;
            clock += Time.deltaTime;
            // State transitions make the warning, transit and recovery independent and easy to tune.
            if (Phase == TidePhase.Calm && clock >= nextLaunch - warningDuration)
                Phase = TidePhase.Drawdown;
            if (Phase == TidePhase.Drawdown)
            {
                ocean.SetDrawdown(drawdownDepth * Mathf.SmoothStep(0, 1, 1 - Countdown / warningDuration));
                if (clock >= nextLaunch)
                {
                    Phase = TidePhase.Wave;
                    launchedAt = clock;
                    nextLaunch += waveInterval;
                    WavesLaunched++;
                    hitThisWave = false;
                    lastFront = -distance / 2 - 30;
                    wall.gameObject.SetActive(true);
                    Debug.Log($"TIDE: launch {WavesLaunched} at {clock:F2}s");
                }
            }

            if (Phase == TidePhase.Wave)
            {
                float coordinate = WaveCoordinate;
                wall.position = travelDirection * coordinate + Vector3.up * ocean.RestLevel;
                float remaining = distance / 2 - coordinate;
                float dissolve = Mathf.SmoothStep(0, 1, Mathf.Clamp01(remaining / offshoreMargin));
                wall.localScale = new Vector3(1, dissolve, 1);
                float playerCoordinate = Vector3.Dot(player.Position, travelDirection);
                Vector3 cross = player.Position - travelDirection * playerCoordinate;
                // Test the swept interval between frames, so even a low frame rate cannot skip the player.
                bool crossed = playerCoordinate >= lastFront - 24 && playerCoordinate <= coordinate + 24;
                if (!hitThisWave && crossed && cross.magnitude < waveWidth / 2 && player.Position.y < ocean.RestLevel + crestHeight * dissolve)
                {
                    hitThisWave = true;
                    StartCoroutine(Sweep());
                }

                lastFront = coordinate;
                if (coordinate > distance / 2)
                {
                    Phase = TidePhase.Recovery;
                    wall.gameObject.SetActive(false);
                }
            }

            if (Phase == TidePhase.Recovery)
            {
                float since = clock - launchedAt - distance / travelSpeed;
                ocean.SetDrawdown(drawdownDepth * (1 - Mathf.SmoothStep(0, 1, since / recoveryDuration)));
                if (since >= recoveryDuration)
                {
                    Phase = TidePhase.Calm;
                    ocean.SetDrawdown(0);
                    Debug.Log("TIDE: calm restored");
                }
            }
        }

        IEnumerator Sweep()
        {
            if (sweeping)
                yield break;
            sweeping = true;
            Sweeps++;
            bool wasReview = player.InputLocked;
            player.InputLocked = true;
            Vector3 eyeBase = player.Eyes.transform.localPosition;
            for (float elapsed = 0; elapsed < sweepDuration; elapsed += Time.deltaTime)
            {
                player.Push(travelDirection, pushSpeed * Time.deltaTime);
                float shake = shakeAmount * (1 - elapsed / sweepDuration);
                player.Eyes.transform.localPosition = eyeBase + new Vector3(Mathf.Sin(elapsed * 83), Mathf.Sin(elapsed * 67), 0) * shake;
                hud.Fade = Mathf.SmoothStep(0, 1, elapsed / sweepDuration);
                yield return null;
            }

            player.Respawn();
            hud.Fade = 1;
            for (float t = 0; t < fadeInDuration; t += Time.deltaTime)
            {
                hud.Fade = 1 - t / fadeInDuration;
                yield return null;
            }

            hud.Fade = 0;
            player.InputLocked = wasReview;
            sweeping = false;
            Debug.Log($"TIDE: swept and respawned ({Sweeps})");
        }

        void OnValidate()
        {
            travelSpeed = Mathf.Max(1, travelSpeed);
            warningDuration = Mathf.Max(1, warningDuration);
            recoveryDuration = Mathf.Max(.1f, recoveryDuration);
        }
    }
}
