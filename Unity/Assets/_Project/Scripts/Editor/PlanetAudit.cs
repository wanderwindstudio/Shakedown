using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using Unity.Profiling;
using UnityEditor;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;

namespace TestPlanet.Editor
{
    /// <summary>Review evidence is generated from Play mode, rather than inferred from source code.</summary>
    public static class PlanetAudit
    {
        public static IEnumerator Run(Camera camera, PlanetPlayer player, PlanetTerrain terrain)
        {
            Vector3 summitPosition = player.Position;
            var notes = new StringBuilder();
            var positions = new Dictionary<Vector2, float>();
            int chunks = 0, cracks = 0, flatFailures = 0, oversized = 0;
            float highest = float.MinValue;
            foreach (var filter in terrain.GetComponentsInChildren<MeshFilter>())
            {
                if (!filter.name.StartsWith("Terrain "))
                    continue;
                chunks++;
                var mesh = filter.sharedMesh;
                if (mesh.vertexCount > 65535)
                    oversized++;
                Vector3[] vertices = mesh.vertices, normals = mesh.normals;
                for (int i = 0; i < vertices.Length; i++)
                {
                    Vector3 v = vertices[i];
                    highest = Mathf.Max(highest, v.y);
                    var key = new Vector2(v.x, v.z);
                    if (positions.TryGetValue(key, out float previous) && Mathf.Abs(previous - v.y) > .0001f)
                        cracks++;
                    else
                        positions[key] = v.y;
                    if (i % 3 == 0 && (Vector3.Dot(normals[i], normals[i + 1]) < .9999f || Vector3.Dot(normals[i], normals[i + 2]) < .9999f))
                        flatFailures++;
                }
            }

            bool geometry = chunks == 16 && cracks == 0 && flatFailures == 0 && oversized == 0 && highest > 110 && highest < 125;
            notes.AppendLine($"Geometry pass: {geometry}. Chunks={chunks}; inconsistent shared heights={cracks}; non-flat faces={flatFailures}; oversized chunks={oversized}; summit={highest:F2}m.");
            notes.AppendLine(FindFirst<PlanetProps>().ValidatePlacements(terrain));
            Debug.Log("GEOMETRY_REVIEW " + notes);
            if (!geometry)
                Debug.LogError("GEOMETRY_REVIEW_FAIL");
            // Feed the real Input System devices, then let the player's ordinary Update read them.
            player.Respawn();
            player.InputLocked = false;
            PlanetPlayer.LockCursor(true);
            Vector3 before = player.Position;
            Quaternion lookBefore = player.Eyes.transform.rotation;
            InputSystem.QueueStateEvent(Keyboard.current, new KeyboardState(Key.W, Key.LeftShift));
            InputSystem.QueueDeltaStateEvent(Mouse.current.delta, new Vector2(30, -12));
            yield return new WaitForSeconds(.3f);
            bool moved = Vector3.Distance(before, player.Position) > 1;
            bool looked = Quaternion.Angle(lookBefore, player.Eyes.transform.rotation) > .5f;
            InputSystem.QueueStateEvent(Keyboard.current, new KeyboardState(Key.Escape));
            yield return null;
            yield return null;
            bool escaped = Cursor.lockState == CursorLockMode.None;
            InputSystem.QueueStateEvent(Keyboard.current, new KeyboardState());
            player.InputLocked = true;
            PlanetPlayer.LockCursor(false);
            player.Respawn();
            notes.AppendLine($"Input pass: movement={moved}; mouse look={looked}; Escape releases cursor={escaped}.");
            Debug.Log($"INPUT_REVIEW moved={moved} mouseLook={looked} escape={escaped}");
            if (!moved || !looked || !escaped)
                Debug.LogError("INPUT_REVIEW_FAIL");
            File.WriteAllText("Assets/_Project/Screenshots/stage7_validation.txt", notes.ToString());
            yield return Benchmark(camera, "calm");
            player.Teleport(summitPosition);
        }

        public static IEnumerator Benchmark(Camera camera, string label)
        {
            // Count completed camera render callbacks, rather than simulation Updates (which can outrun Editor repaints).
            var target = new RenderTexture(1920, 1080, 24);
            var previousTarget = camera.targetTexture;
            camera.targetTexture = target;
            camera.aspect = 1920f / 1080;
            if (label == "calm")
            {
                var terrain = FindFirst<PlanetTerrain>();
                camera.transform.position = new Vector3(-135, terrain.Height(-135, -105) + 1.8f, -105);
                camera.transform.LookAt(new Vector3(65, 65, 52));
            }

            int previousRate = Application.targetFrameRate, previousVsync = QualitySettings.vSyncCount;
            Application.targetFrameRate = -1;
            QualitySettings.vSyncCount = 0;
            yield return new WaitForSecondsRealtime(.5f);
            var samples = new List<float>();
            var csv = new StringBuilder("render,elapsed_ms,main_thread_ms,draw_calls,triangles\n");
            double mainTotal = 0, last = 0;
            long drawTotal = 0, triangleTotal = 0;
            var main = ProfilerRecorder.StartNew(ProfilerCategory.Internal, "Main Thread", 1);
            void Rendered(UnityEngine.Rendering.ScriptableRenderContext context, Camera rendered)
            {
                if (rendered != camera)
                    return;
                double now = Time.realtimeSinceStartupAsDouble;
                if (last > 0)
                {
                    float ms = (float)((now - last) * 1000);
                    samples.Add(ms);
                    double cpu = main.Valid ? main.LastValue / 1000000.0 : 0;
                    mainTotal += cpu;
                    drawTotal += UnityStats.drawCalls;
                    triangleTotal += UnityStats.triangles;
                    csv.AppendLine(string.Format(CultureInfo.InvariantCulture, "{0},{1:F4},{2:F4},{3},{4}", samples.Count, ms, cpu, UnityStats.drawCalls, UnityStats.triangles));
                }

                last = now;
            }

            UnityEngine.Rendering.RenderPipelineManager.endCameraRendering += Rendered;
            double timeout = Time.realtimeSinceStartupAsDouble + 30;
            while (samples.Count < 300 && Time.realtimeSinceStartupAsDouble < timeout)
                yield return null;
            UnityEngine.Rendering.RenderPipelineManager.endCameraRendering -= Rendered;
            main.Dispose();
            Application.targetFrameRate = previousRate;
            QualitySettings.vSyncCount = previousVsync;
            camera.targetTexture = previousTarget;
            target.Release();
            UnityEngine.Object.Destroy(target);
            if (samples.Count == 0)
            {
                Debug.LogError("PERFORMANCE_REVIEW_FAIL: no rendered frames");
                yield break;
            }

            float sum = 0;
            foreach (float sample in samples)
                sum += sample;
            samples.Sort();
            float average = sum / samples.Count, p95 = samples[(int)(samples.Count * .95f)];
            string performance = $"1080p Editor camera renders ({label}), {samples.Count} uncapped samples: mean={average:F2}ms ({1000 / average:F1} renders/s), p95={p95:F2}ms, main-thread mean={mainTotal / samples.Count:F2}ms, mean draw calls={drawTotal / samples.Count}, mean triangles={triangleTotal / samples.Count}. GPU: {SystemInfo.graphicsDeviceName}.";
            File.WriteAllText($"Assets/_Project/Screenshots/stage7_performance_{label}.csv", csv.ToString());
            File.AppendAllText("Assets/_Project/Screenshots/stage7_validation.txt", performance + "\nCamera callback timing includes Editor overhead and submission, not a GPU-completion measurement or standalone-build guarantee. Wave render sampling freezes game time to hold the crest in view.\n");
            Debug.Log("PERFORMANCE_REVIEW " + performance);
        }

        static T FindFirst<T>()
            where T : UnityEngine.Object => UnityEngine.Object.FindFirstObjectByType<T>();
    }
}
