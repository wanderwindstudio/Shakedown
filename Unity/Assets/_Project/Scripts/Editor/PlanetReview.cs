using System.Collections;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace TestPlanet.Editor
{
    // This runner lives only in the Editor. A shipped game never teleports or auto-exits.
    [InitializeOnLoad]
    public static class PlanetReview
    {
        static PlanetReview()
        {
            EditorApplication.playModeStateChanged += Changed;
        }

        static void Changed(PlayModeStateChange state)
        {
            if (state == PlayModeStateChange.EnteredEditMode)
            {
                AssetDatabase.Refresh();
                return;
            }

            if (state != PlayModeStateChange.EnteredPlayMode || SessionState.GetInt("PlanetReviewStage", 0) == 0)
                return;
            new GameObject("Temporary screenshot review").AddComponent<ReviewRunner>();
        }
    }

    public sealed class ReviewRunner : MonoBehaviour
    {
        IEnumerator Start()
        {
            int stage = SessionState.GetInt("PlanetReviewStage", 1);
            yield return new WaitForSeconds(4);
            var camera = Camera.main;
            var player = FindFirstObjectByType<PlanetPlayer>();
            if (player != null)
            {
                player.InputLocked = true;
                camera.transform.SetParent(null);
                PlanetPlayer.LockCursor(false);
            }

            camera.transform.position = new Vector3(-350, 450, -350);
            camera.transform.LookAt(Vector3.zero);
            yield return new WaitForSeconds(1);
            yield return Capture(camera, $"stage{stage}_aerial");
            if (stage >= 2)
            {
                yield return new WaitForSeconds(1);
                yield return Capture(camera, $"stage{stage}_ocean_motion");
            }

            var terrain = FindFirstObjectByType<PlanetTerrain>();
            camera.enabled = false;
            var fresh = new GameObject("Shore review camera").AddComponent<Camera>();
            fresh.CopyFrom(camera);
            camera = fresh;
            camera.enabled = true;
            camera.GetUniversalAdditionalCameraData().renderPostProcessing = true;
            camera.transform.position = new Vector3(-135, terrain.Height(-135, -105) + 1.8f, -105);
            if (Physics.Raycast(new Vector3(-135, 250, -105), Vector3.down, out RaycastHit shore, 400))
                camera.transform.position = shore.point + Vector3.up * 1.8f;
            camera.transform.LookAt(new Vector3(65, 65, 52));
            Debug.Log($"REVIEW CAMERA {camera.transform.position} forward={camera.transform.forward} summit={terrain.Height(65, 52)}");
            yield return new WaitForSeconds(1);
            yield return Capture(camera, $"stage{stage}_shoreline");
            if (stage >= 5)
                Debug.Log("PROP_VALIDATION " + FindFirstObjectByType<PlanetProps>().ValidatePlacements(terrain));
            if (stage >= 4)
            {
                yield return WalkReview(player, terrain);
                camera.transform.position = player.Position + Vector3.up * 1.8f;
                camera.transform.LookAt(new Vector3(-80, 35, -140));
                yield return Capture(camera, $"stage{stage}_summit");
            }

            if (stage >= 7)
            {
                yield return PlanetAudit.Run(camera, player, terrain);
                Vector3 coast = new Vector3(100, 250, -155);
                if (Physics.Raycast(coast, Vector3.down, out RaycastHit hit, 400))
                    coast = hit.point + Vector3.up * 1.8f;
                camera.transform.position = coast;
                camera.transform.LookAt(new Vector3(240, 40, -40));
                yield return Capture(camera, "stage7_coast");
            }

            if (stage >= 6)
                yield return TideReview(camera, player, terrain, stage);
            Debug.Log($"PLANET_REVIEW_PASS stage={stage} triangles={terrain.TriangleCount} colliders={FindObjectsByType<MeshCollider>(FindObjectsSortMode.None).Length}");
            SessionState.SetInt("PlanetReviewStage", 0);
            EditorApplication.ExitPlaymode();
        }

        static IEnumerator TideReview(Camera camera, PlanetPlayer player, PlanetTerrain terrain, int stage)
        {
            var tide = FindFirstObjectByType<PlanetTide>();
            var ocean = FindFirstObjectByType<PlanetOcean>();
            Vector3 summit = player.Position;
            int before = player.Respawns;
            player.Respawn();
            before = player.Respawns;
            Time.timeScale = 4;
            float timeout = Time.time + 240;
            while (tide.Phase != PlanetTide.TidePhase.Drawdown && Time.time < timeout)
                yield return null;
            while (tide.Countdown > 2 && Time.time < timeout)
                yield return null;
            camera.transform.position = new Vector3(0, 18, -215);
            camera.transform.LookAt(new Vector3(120, 8, -120));
            yield return Capture(camera, $"stage{stage}_drawdown");
            bool lowered = ocean.Level < ocean.RestLevel - 5;
            while ((tide.Phase != PlanetTide.TidePhase.Wave || tide.WaveCoordinate < 0) && Time.time < timeout)
                yield return null;
            camera.transform.position = new Vector3(-350, 450, -350);
            camera.transform.LookAt(new Vector3(0, 12, 0));
            yield return Capture(camera, $"stage{stage}_mid_wave");
            if (stage >= 7)
            {
                Time.timeScale = 0;
                yield return PlanetAudit.Benchmark(camera, "wave");
                Time.timeScale = 4;
            }

            while (tide.Phase != PlanetTide.TidePhase.Calm && Time.time < timeout)
                yield return null;
            bool swept = tide.Sweeps == 1 && player.Respawns == before + 1;
            bool restored = Mathf.Abs(ocean.Level - ocean.RestLevel) < .01f;
            player.Teleport(summit);
            int summitRespawns = player.Respawns;
            int firstWave = tide.WavesLaunched;
            while (tide.WavesLaunched == firstWave && Time.time < timeout)
                yield return null;
            while (tide.Phase != PlanetTide.TidePhase.Calm && Time.time < timeout)
                yield return null;
            bool survived = player.Respawns == summitRespawns && player.Position.y > tide.Crest && tide.WavesLaunched == firstWave + 1;
            Time.timeScale = 1;
            camera.transform.position = summit + Vector3.up * 1.8f;
            camera.transform.LookAt(new Vector3(-100, 10, -130));
            yield return Capture(camera, $"stage{stage}_safe_summit");
            Debug.Log($"TIDE_REVIEW drawdown={lowered} sweptRespawn={swept} seaRestored={restored} summitSurvived={survived} launches={tide.WavesLaunched}");
            File.WriteAllText("Assets/_Project/Screenshots/tide_review.txt", $"Drawdown: {lowered}\nLowland sweep and respawn: {swept}\nSea restored: {restored}\nSummit survival: {survived}\nWaves observed: {tide.WavesLaunched}\nDefault interval: 90s. Review ran at 4x game time after the climb.\n");
            if (!lowered || !swept || !restored || !survived)
                Debug.LogError("TIDE_REVIEW_FAIL");
        }

        static IEnumerator WalkReview(PlanetPlayer player, PlanetTerrain terrain)
        {
            player.Respawn();
            for (int i = 0; i < 20; i++)
            {
                player.Move(Vector3.zero, false, false, .02f);
                yield return null;
            }

            float startY = player.Position.y;
            bool jumped = false;
            for (int i = 0; i < 35; i++)
            {
                player.Move(Vector3.zero, false, i == 0, .02f);
                if (player.Position.y > startY + .5f)
                    jumped = true;
                yield return null;
            }

            Vector3 target = new Vector3(terrain.VolcanoCentre.x - 24, 0, terrain.VolcanoCentre.y - 12);
            float elapsed = 0;
            int rescues = player.Respawns;
            while (elapsed < 65)
            {
                Vector3 delta = target - player.Position;
                delta.y = 0;
                if (delta.magnitude < 4)
                    break;
                player.Move(delta.normalized, true, false, .02f);
                elapsed += .02f;
                yield return null;
            }

            bool climbed = player.Position.y > 100 && player.Respawns == rescues;
            Debug.Log($"PLAYER_REVIEW jump={jumped} craterReached={climbed} position={player.Position} simulatedSeconds={elapsed:F1}");
            if (!jumped || !climbed)
                Debug.LogError("PLAYER_REVIEW_FAIL: jump or shore-to-crater climb");
        }

        public static IEnumerator Capture(Camera camera, string name)
        {
            // Render explicitly at 1080p; the editor's docked Game view size does not change the evidence.
            var hud = Object.FindFirstObjectByType<PlanetHud>();
            if (hud != null)
                hud.SetReviewCamera(camera);
            var target = new RenderTexture(1920, 1080, 24);
            var previous = camera.targetTexture;
            camera.targetTexture = target;
            camera.aspect = 1920f / 1080f;
            camera.ResetWorldToCameraMatrix();
            camera.ResetProjectionMatrix();
            // Let URP render normal frames; manually calling Camera.Render can reuse stale view data.
            yield return null;
            yield return new WaitForEndOfFrame();
            var old = RenderTexture.active;
            RenderTexture.active = target;
            var image = new Texture2D(1920, 1080, TextureFormat.RGB24, false);
            image.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0);
            image.Apply();
            File.WriteAllBytes($"Assets/_Project/Screenshots/{name}.png", image.EncodeToPNG());
            camera.targetTexture = previous;
            RenderTexture.active = old;
            Destroy(image);
            target.Release();
            Destroy(target);
        }
    }
}
