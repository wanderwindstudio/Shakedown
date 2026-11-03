using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using TMPro;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace TestPlanet.Editor
{
    public static class PlanetBuild
    {
        const string Root = "Assets/_Project/";
        [MenuItem("Planet/Build test scene")]
        public static void Build()
        {
            if (File.Exists(Root + "Scenes/TestPlanet.unity"))
            {
                EditorSceneManager.OpenScene(Root + "Scenes/TestPlanet.unity");
                Advance(7);
                return;
            }

            Directory.CreateDirectory(Root + "Materials");
            var renderer = ScriptableObject.CreateInstance<UniversalRendererData>();
            AssetDatabase.CreateAsset(renderer, Root + "Materials/PlanetRenderer.asset");
            var pipeline = UniversalRenderPipelineAsset.Create(renderer);
            pipeline.name = "Planet URP";
            pipeline.supportsHDR = true;
            pipeline.shadowDistance = 450;
            pipeline.msaaSampleCount = 2;
            AssetDatabase.CreateAsset(pipeline, Root + "Materials/PlanetURP.asset");
            GraphicsSettings.defaultRenderPipeline = pipeline;
            QualitySettings.renderPipeline = pipeline;
            var settings = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/ProjectSettings.asset")[0]);
            settings.FindProperty("activeInputHandler").intValue = 1;
            settings.ApplyModifiedProperties();
            PlayerSettings.colorSpace = ColorSpace.Linear;
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var world = new GameObject("PELAGIC · procedural ocean world").AddComponent<PlanetWorld>();
            var terrain = world.gameObject.AddComponent<PlanetTerrain>();
            var material = new Material(AssetDatabase.LoadAssetAtPath<Shader>(Root + "Shaders/TerrainVertexColor.shadergraph"));
            AssetDatabase.CreateAsset(material, Root + "Materials/Terrain.mat");
            terrain.Material = material;
            world.Configure(terrain);
            var sun = new GameObject("Late afternoon sun").AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.intensity = 2.3f;
            sun.color = new Color(1, .82f, .62f);
            sun.transform.rotation = Quaternion.Euler(24, -38, 0);
            sun.shadows = LightShadows.Soft;
            RenderSettings.sun = sun;
            RenderSettings.ambientLight = new Color(.35f, .40f, .49f);
            var camera = new GameObject("Player Camera", typeof(Camera)).GetComponent<Camera>();
            camera.tag = "MainCamera";
            camera.nearClipPlane = .1f;
            camera.farClipPlane = 12000;
            camera.fieldOfView = 68;
            camera.allowHDR = true;
            camera.transform.position = new Vector3(-165, 15, -145);
            camera.transform.LookAt(new Vector3(65, 58, 52));
            camera.GetUniversalAdditionalCameraData().renderPostProcessing = true;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(.48f, .48f, .6f);
            EditorSceneManager.SaveScene(scene, Root + "Scenes/TestPlanet.unity");
            EditorBuildSettings.scenes = new[]{new EditorBuildSettingsScene(Root + "Scenes/TestPlanet.unity", true)};
            AssetDatabase.SaveAssets();
            Debug.Log("PLANET: scene built");
            StartReview(1);
        }

        public static void StartReview(int stage)
        {
            SessionState.SetInt("PlanetReviewStage", stage);
            EditorApplication.EnterPlaymode();
        }

        public static void Advance(int stage)
        {
            foreach (string file in new[]{"DefaultVolumeProfile.asset", "UniversalRenderPipelineGlobalSettings.asset"})
                if (AssetDatabase.LoadMainAssetAtPath("Assets/" + file) != null)
                    AssetDatabase.MoveAsset("Assets/" + file, Root + "Materials/" + file);
            if (Directory.Exists("Assets/TextMesh Pro"))
            {
                AssetDatabase.DeleteAsset(Root + "Shaders/TextMeshPro");
                AssetDatabase.DeleteAsset(Root + "Materials/Fonts");
                AssetDatabase.DeleteAsset("Assets/TextMesh Pro/Examples & Extras");
                AssetDatabase.DeleteAsset("Assets/TextMesh Pro/Documentation");
                AssetDatabase.MoveAsset("Assets/TextMesh Pro/Shaders", Root + "Shaders/TextMeshPro");
                AssetDatabase.MoveAsset("Assets/TextMesh Pro", Root + "Materials/TMP Essentials");
            }

            var world = Object.FindFirstObjectByType<PlanetWorld>();
            world.Stage = stage;
            string[] types = {"PlanetOcean", "PlanetAtmosphere", "PlanetPlayer", "PlanetProps", "PlanetTide"};
            for (int i = 0; i < stage - 1 && i < types.Length; i++)
            {
                var type = typeof(PlanetWorld).Assembly.GetType("TestPlanet." + types[i]);
                if (type != null && world.GetComponent(type) == null)
                    world.gameObject.AddComponent(type);
            }

            if (stage >= 6 && world.GetComponent<PlanetHud>() == null)
                world.gameObject.AddComponent<PlanetHud>();
            if (stage >= 6)
            {
                var hud = world.GetComponent<PlanetHud>();
                var so = new SerializedObject(hud);
                var prop = so.FindProperty("font");
                if (prop.objectReferenceValue == null)
                {
                    // Use the prebuilt font from Unity's official TMP essentials; built-in runtime fonts lack source face data.
                    var font = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(Root + "Materials/TMP Essentials/Resources/Fonts & Materials/LiberationSans SDF.asset");
                    if (font == null)
                        throw new System.InvalidOperationException("Unity TMP Essentials font is missing.");
                    font.material.shader = Shader.Find("TextMeshPro/Distance Field");
                    prop.objectReferenceValue = font;
                    so.ApplyModifiedProperties();
                    EditorUtility.SetDirty(font.material);
                }
            }

            if (stage >= 6)
            {
                var font = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(Root + "Materials/TMP Essentials/Resources/Fonts & Materials/LiberationSans SDF.asset");
                font.material.shader = AssetDatabase.LoadAssetAtPath<Shader>(Root + "Shaders/TextMeshPro/TMP_SDF.shader");
                EditorUtility.SetDirty(font.material);
            }

            // Keep shader references in material assets, so a future player build does not strip them.
            foreach (var feature in world.GetComponents<MonoBehaviour>())
            {
                var so = new SerializedObject(feature);
                var prop = so.FindProperty("surfaceMaterial");
                if (prop == null || prop.objectReferenceValue != null)
                    continue;
                string shaderName = feature.GetType().Name == "PlanetOcean" ? "Planet/Ocean" : feature.GetType().Name == "PlanetAtmosphere" ? "Planet/Sky" : "Planet/TidalWave";
                var shader = Shader.Find(shaderName);
                if (shader == null)
                    continue;
                var mat = new Material(shader);
                AssetDatabase.CreateAsset(mat, Root + "Materials/" + feature.GetType().Name + ".mat");
                prop.objectReferenceValue = mat;
                so.ApplyModifiedProperties();
            }

            var props = world.GetComponent<PlanetProps>();
            if (props != null)
            {
                var so = new SerializedObject(props);
                var prop = so.FindProperty("crystalMaterial");
                if (prop.objectReferenceValue == null)
                {
                    var mat = new Material(Shader.Find("Universal Render Pipeline/Lit"));
                    mat.SetColor("_BaseColor", new Color(.10f, .45f, .40f));
                    mat.SetFloat("_Smoothness", .32f);
                    mat.EnableKeyword("_EMISSION");
                    mat.SetColor("_EmissionColor", new Color(.2f, .8f, .7f));
                    AssetDatabase.CreateAsset(mat, Root + "Materials/Crystal.mat");
                    prop.objectReferenceValue = mat;
                    so.ApplyModifiedProperties();
                }
            }

            var atmosphere = world.GetComponent<PlanetAtmosphere>();
            if (atmosphere != null)
            {
                var so = new SerializedObject(atmosphere);
                var prop = so.FindProperty("celestialMaterial");
                if (prop.objectReferenceValue == null)
                {
                    var mat = new Material(Shader.Find("Planet/Celestial"));
                    AssetDatabase.CreateAsset(mat, Root + "Materials/Celestial.mat");
                    prop.objectReferenceValue = mat;
                    so.ApplyModifiedProperties();
                }
            }

            EditorSceneManager.MarkSceneDirty(world.gameObject.scene);
            EditorSceneManager.SaveOpenScenes();
            AssetDatabase.SaveAssets();
            StartReview(stage);
        }

        [MenuItem("Planet/Run full review")]
        public static void ReviewAll() => Advance(7);
        [MenuItem("Planet/Open test scene")]
        static void OpenScene() => EditorSceneManager.OpenScene(Root + "Scenes/TestPlanet.unity");
        [MenuItem("Planet/Review current scene stage")]
        static void ReviewCurrent() => StartReview(Object.FindFirstObjectByType<PlanetWorld>().Stage);
        [MenuItem("Planet/Review stage 1")]
        static void Review1() => StartReview(1);
    }
}
