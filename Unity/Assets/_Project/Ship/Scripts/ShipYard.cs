using UnityEngine;
using Shakedown.Player;
using UnityEngine.Rendering;

namespace Shakedown.Ship
{
    public sealed class ShipYard : MonoBehaviour
    {
        public PartCatalog catalog;
        public Material padMaterial, stripeMaterial, ghostMaterial, outlineMaterial, skyMaterial;
        [Range(0, 1), Tooltip("Convex hull chamfer in metres. Zero keeps hard edges. Live in Play mode.")]
        public float chamferSize = .5f;
        ShipBuilder builder;
        void Awake()
        {
            Application.targetFrameRate = 60;
            var pad = GameObject.CreatePrimitive(PrimitiveType.Cube);
            pad.name = "Landing pad · 400 m";
            pad.transform.position = new Vector3(0, -1, 0);
            pad.transform.localScale = new Vector3(400, 2, 400);
            pad.GetComponent<Renderer>().sharedMaterial = padMaterial;
            var sun = new GameObject("Dusk sun").AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.transform.rotation = Quaternion.Euler(26, -38, 0);
            sun.color = new Color(1, .81f, .67f);
            sun.intensity = 1.6f;
            sun.shadows = LightShadows.Soft;
            RenderSettings.sun = sun;
            RenderSettings.skybox = new Material(skyMaterial);
            RenderSettings.skybox.SetVector("_SunDirection", -sun.transform.forward);
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(.43f, .38f, .54f);
            RenderSettings.ambientEquatorColor = new Color(.37f, .32f, .42f);
            RenderSettings.ambientGroundColor = new Color(.23f, .20f, .28f);
            RenderSettings.fog = true;
            RenderSettings.fogColor = new Color(.57f, .51f, .64f);
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogDensity = .002f;
            var walk = MakeCamera("Player eyes");
            walk.tag = "MainCamera";
            var player = new GameObject("Cadet body").AddComponent<FirstPersonController>();
            player.Initialize(new Vector3(0, .15f, -9), Quaternion.identity, walk, 0);
            var droneCamera = MakeCamera("Construction drone");
            var drone = droneCamera.gameObject.AddComponent<ConstructionDrone>();
            droneCamera.gameObject.SetActive(false);
            var ship = new GameObject("Ship · grid visuals");
            builder = ship.AddComponent<ShipBuilder>();
            builder.catalog = catalog;
            builder.stripeMaterial = stripeMaterial;
            // Preview tint is mutable; keep the authored asset untouched in the editor.
            builder.ghostMaterial = new Material(ghostMaterial);
            builder.outlineMaterial = outlineMaterial;
            builder.player = player;
            builder.walkCamera = walk;
            builder.droneCamera = droneCamera;
            builder.drone = drone;
            builder.Initialize(chamferSize);
        }
        void Update() { if (builder != null) builder.SetChamfer(chamferSize); }
        Camera MakeCamera(string name)
        {
            var camera = new GameObject(name).AddComponent<Camera>();
            camera.nearClipPlane = .05f;
            camera.farClipPlane = 600;
            camera.fieldOfView = 70;
            camera.clearFlags = CameraClearFlags.Skybox;
            return camera;
        }
        void OnGUI()
        {
            if (builder == null) return;
            GUI.color = new Color(.08f, .07f, .13f, .85f);
            GUI.DrawTexture(new Rect(15, 15, 720, 187), Texture2D.whiteTexture);
            GUI.color = new Color(.9f, .88f, .97f);
            GUI.Label(new Rect(28, 23, 690, 24), "SHAKEDOWN   /   " + (builder.Building ? "BUILD DRONE" : "WALK") + "   /   " + builder.SelectedName);
            GUI.Label(new Rect(28, 47, 690, 24), builder.Grid.Count + " blocks    ·    " + builder.Grid.Mass(catalog).ToString("N0") + " kg");
            GUI.Label(new Rect(28, 71, 690, 24), "B build / drop in here  ·  WASD move  ·  Shift faster");
            GUI.Label(new Rect(28, 92, 690, 24), "Space: jump in Walk / up in Build  ·  C: down in Build");
            GUI.Label(new Rect(28, 113, 690, 24), "1/2/3/4 part  ·  R/T/G rotate  ·  LMB place  ·  RMB remove  ·  Z/Y undo/redo");
            GUI.Label(new Rect(28, 134, 690, 24), "F5 save  ·  F9 load  ·  Esc release cursor  ·  click recapture");
            GUI.Label(new Rect(28, 155, 690, 24), "H shape: " + (builder.Shaping ? "on" : "off") + "  ·  L lock hull  ·  [ / ] colour  ·  MMB paint");
            GUI.Label(new Rect(28, 176, 690, 24), "Paint: " + builder.PaintName);
            GUI.Label(new Rect(28, 219, 900, 30), builder.Message);
            GUI.Label(new Rect(Screen.width / 2f - 5, Screen.height / 2f - 12, 20, 24), "+");
        }
        void OnDestroy() { FirstPersonController.LockCursor(false); }
    }
}
