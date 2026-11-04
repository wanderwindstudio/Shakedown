using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;
using Shakedown.Player;
using TestPlanet;

namespace Shakedown.Spikes
{
    public sealed class OrbitFlight : MonoBehaviour
    {
        const string OrbitScene = "Assets/_Project/Spikes/OrbitTest.unity";
        const string SurfaceScene = "Assets/_Project/Scenes/TestPlanet.unity";
        enum Phase { Orbit, Approach, Clouds, Arrival, Landed, Restarting }
        public static OrbitFlight Instance { get; private set; }
        OrbitWorld orbit;
        PlanetPlayer player;
        PlanetTide tide;
        readonly List<Canvas> hiddenCanvases = new List<Canvas>();
        Coroutine journey;
        Phase phase;
        bool loading, restartQueued;
        Vector3 landing, arrivalStart;
        float yaw, cloudAlpha, fps;
        Texture2D cloudTexture;
        Stopwatch journeyClock, loadClock;
        double loadSeconds;

        void Awake()
        {
            Instance = this; DontDestroyOnLoad(gameObject);
            SceneManager.sceneLoaded += SceneLoaded;
            cloudTexture = new Texture2D(128,128,TextureFormat.RGBA32,false);
            cloudTexture.wrapMode = TextureWrapMode.Repeat; cloudTexture.filterMode = FilterMode.Bilinear;
            var pixels = new Color[128*128];
            for (int y = 0; y < 128; y++) for (int x = 0; x < 128; x++)
            {
                float density = Mathf.PerlinNoise(x/28f,y/28f)*.18f+.78f;
                pixels[y*128+x] = new Color(density,density,density,1);
            }
            cloudTexture.SetPixels(pixels); cloudTexture.Apply();
        }
        public void Attach(OrbitWorld world)
        {
            orbit = world; phase = Phase.Orbit; cloudAlpha = 0; restartQueued = false; loading = false;
            FirstPersonController.LockCursor(false); PlacePlanet(1150);
        }
        void Update()
        {
            fps = Mathf.Lerp(fps,1/Mathf.Max(.001f,Time.unscaledDeltaTime),.04f);
            var keyboard = Keyboard.current;
            if (keyboard == null) return;
            if (keyboard.rKey.wasPressedThisFrame)
            {
                if (loading) { restartQueued = true; return; }
                if (journey != null) StopCoroutine(journey);
                if (orbit != null) { Attach(orbit); journey = StartCoroutine(Approach()); }
                else journey = StartCoroutine(RestartOrbit());
            }
            if (phase == Phase.Orbit && keyboard.lKey.wasPressedThisFrame) journey = StartCoroutine(Approach());
        }
        void PlacePlanet(float siteDistance)
        {
            if (orbit == null) return;
            // The pilot stays still. Only the small orbit representation moves past the windscreen.
            orbit.Planet.transform.position = orbit.Pilot.transform.position + orbit.Pilot.transform.forward*siteDistance - OrbitPlanet.LandingDirection*OrbitPlanet.Radius;
        }
        IEnumerator Approach()
        {
            phase = Phase.Approach; journeyClock = Stopwatch.StartNew();
            while (journeyClock.Elapsed.TotalSeconds < 20)
            {
                float t = Mathf.SmoothStep(0,1,(float)journeyClock.Elapsed.TotalSeconds/20);
                PlacePlanet(Mathf.Exp(Mathf.Lerp(Mathf.Log(1150),Mathf.Log(30),t)));
                yield return null;
            }
            phase = Phase.Clouds;
            var cloudClock = Stopwatch.StartNew();
            AsyncOperation load = null;
            while (cloudClock.Elapsed.TotalSeconds < 5 || load == null || !load.isDone)
            {
                float t = (float)cloudClock.Elapsed.TotalSeconds;
                PlacePlanet(Mathf.Lerp(30,.5f,Mathf.SmoothStep(0,1,t/5)));
                cloudAlpha = Mathf.SmoothStep(0,1,t/2);
                if (t >= 2.4f && load == null)
                {
                    // The outgoing camera must not be Camera.main while Pelagic creates its own player.
                    orbit.Pilot.tag = "Untagged";
                    loading = true; loadClock = Stopwatch.StartNew();
                    load = SceneManager.LoadSceneAsync(SurfaceScene,LoadSceneMode.Single);
                }
                yield return null;
            }
            loading = false;
            if (restartQueued) { yield return RestartOrbit(); yield break; }
            phase = Phase.Arrival;
            var descentClock = Stopwatch.StartNew();
            while (descentClock.Elapsed.TotalSeconds < 8)
            {
                float seconds = (float)descentClock.Elapsed.TotalSeconds;
                float t = Mathf.SmoothStep(0,1,seconds/8);
                player.SetStandingPose(Vector3.Lerp(arrivalStart,landing,t),yaw);
                player.Eyes.transform.localRotation = Quaternion.Euler(Mathf.Lerp(24,0,t),0,0);
                cloudAlpha = 1-Mathf.SmoothStep(0,1,seconds/1.2f);
                yield return null;
            }
            cloudAlpha = 0;
            player.SetStandingPose(landing,yaw);
            player.InputLocked = false; tide.enabled = true;
            foreach (var canvas in hiddenCanvases) if (canvas != null) canvas.enabled = true;
            hiddenCanvases.Clear();
            // Let ordinary gravity settle the final few centimetres before timing 'standing'.
            float settling = 0;
            while (!player.Grounded && settling < .7f) { settling += Time.unscaledDeltaTime; yield return null; }
            phase = Phase.Landed;
            UnityEngine.Debug.Log($"PLANET_SPIKE landed: total={journeyClock.Elapsed.TotalSeconds:F2}s, hidden surface load={loadSeconds:F3}s, grounded={player.Grounded}");
            journey = null;
        }
        void SceneLoaded(Scene scene, LoadSceneMode mode)
        {
            if (scene.name != "TestPlanet" || !loading) return;
            loadClock.Stop(); loadSeconds = loadClock.Elapsed.TotalSeconds;
            player = FindFirstObjectByType<PlanetPlayer>(); tide = FindFirstObjectByType<PlanetTide>();
            player.InputLocked = true; tide.enabled = false;
            foreach (var canvas in FindObjectsByType<Canvas>(FindObjectsSortMode.None))
                if (canvas.enabled) { hiddenCanvases.Add(canvas); canvas.enabled = false; }
            landing = FindLandingSpot(player);
            var terrain = FindFirstObjectByType<PlanetTerrain>();
            Vector3 facing = new Vector3(terrain.VolcanoCentre.x,landing.y,terrain.VolcanoCentre.y)-landing;
            yaw = Quaternion.LookRotation(facing).eulerAngles.y;
            arrivalStart = landing - facing.normalized*70 + Vector3.up*200;
            player.SetStandingPose(arrivalStart,yaw);
            player.Eyes.transform.localRotation = Quaternion.Euler(24,0,0);
            UnityEngine.Debug.Log($"PLANET_SPIKE surface ready behind opaque cloud: {loadSeconds:F3}s; landing={landing}");
        }
        static Vector3 FindLandingSpot(PlanetPlayer explorer)
        {
            // Reuse Pelagic's shore area; choose a clear, gently sloping patch using real colliders.
            for (int ring = 0; ring <= 5; ring++)
                for (int x = -ring; x <= ring; x++) for (int z = -ring; z <= ring; z++)
                {
                    if (Mathf.Max(Mathf.Abs(x),Mathf.Abs(z)) != ring) continue;
                    Vector3 from = explorer.Spawn + new Vector3(x*6,250,z*6);
                    if (!Physics.Raycast(from,Vector3.down,out var hit,400,Physics.DefaultRaycastLayers,QueryTriggerInteraction.Ignore)) continue;
                    if (explorer.OwnsCollider(hit.collider) || hit.normal.y < .97f || hit.point.y < 2 || hit.point.y > 14) continue;
                    Vector3 feet = hit.point + Vector3.up*.12f;
                    if (explorer.CanStandAt(feet)) return feet;
                }
            return explorer.Spawn;
        }
        IEnumerator RestartOrbit()
        {
            phase = Phase.Restarting; cloudAlpha = 1; loading = true;
            if (player != null) player.InputLocked = true;
            hiddenCanvases.Clear();
            yield return SceneManager.LoadSceneAsync(OrbitScene,LoadSceneMode.Single);
            journey = StartCoroutine(Approach());
        }
        void OnGUI()
        {
            GUI.depth = -10000;
            if (phase != Phase.Landed)
            {
                GUI.color = new Color(.72f,.78f,.83f);
                GUI.Label(new Rect(28,25,700,26), "PELAGIC  /  " + (phase == Phase.Orbit ? "L approach  ·  R replay approach" : "Computer flying  ·  R replay approach"));
                GUI.Label(new Rect(Screen.width-150,25,140,26), "~" + Mathf.RoundToInt(fps) + " fps");
            }
            else { GUI.color = new Color(.85f,.9f,.9f); GUI.Label(new Rect(Screen.width/2-95,20,260,25),"R replay approach"); }
            if (cloudAlpha <= 0) return;
            GUI.color = new Color(.77f,.79f,.80f,cloudAlpha);
            GUI.DrawTexture(new Rect(0,0,Screen.width,Screen.height),Texture2D.whiteTexture);
            GUI.color = new Color(1,1,1,cloudAlpha*.36f);
            float drift = Time.unscaledTime*.018f;
            GUI.DrawTextureWithTexCoords(new Rect(0,0,Screen.width,Screen.height),cloudTexture,new Rect(drift,drift*.4f,2.7f,1.7f));
            GUI.color = Color.white;
        }
        void OnDestroy()
        {
            SceneManager.sceneLoaded -= SceneLoaded;
            if (Instance == this) Instance = null;
            if (cloudTexture != null) Destroy(cloudTexture);
        }
    }
}
