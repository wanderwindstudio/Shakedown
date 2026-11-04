using UnityEngine;
using UnityEngine.Rendering;
using TestPlanet;

namespace Shakedown.Spikes
{
    public sealed class OrbitWorld : MonoBehaviour
    {
        public Shader surfaceShader, cloudShader, atmosphereShader, starShader, sunShader;
        public Material cockpitMaterial;
        public Camera Pilot { get; private set; }
        public OrbitPlanet Planet { get; private set; }
        readonly System.Collections.Generic.List<Material> materials = new System.Collections.Generic.List<Material>();
        Mesh starMesh, sunMesh;
        void Start()
        {
            Application.targetFrameRate = 60;
            RenderSettings.skybox = null; RenderSettings.fog = false;
            RenderSettings.ambientMode = AmbientMode.Flat; RenderSettings.ambientLight = Color.black;
            var camera = new GameObject("Pilot view"); camera.transform.SetParent(transform,false);
            Pilot = camera.AddComponent<Camera>(); Pilot.tag = "MainCamera";
            Pilot.fieldOfView = 62; Pilot.nearClipPlane = .05f; Pilot.farClipPlane = 4000;
            Pilot.clearFlags = CameraClearFlags.SolidColor; Pilot.backgroundColor = new Color(.0015f,.0025f,.006f);
            Vector3 toSun = new Vector3(-.86f,.22f,-.46f).normalized;
            var sun = new GameObject("Single warm-white sun").AddComponent<Light>(); sun.transform.SetParent(transform,false);
            sun.type = LightType.Directional; sun.intensity = 1.8f; sun.color = new Color(1,.94f,.84f);
            sun.transform.rotation = Quaternion.LookRotation(-toSun); RenderSettings.sun = sun;
            var planet = new GameObject("Pelagic · orbit representation"); planet.transform.SetParent(transform,false);
            Planet = planet.AddComponent<OrbitPlanet>(); Planet.Generate(Material(surfaceShader),Material(cloudShader),Material(atmosphereShader),7429);
            Stars(Material(starShader)); Sun(toSun,Material(sunShader)); Cockpit();
            OrbitFlight flight = OrbitFlight.Instance;
            if (flight == null) flight = new GameObject("Orbit approach · persistent handoff").AddComponent<OrbitFlight>();
            flight.Attach(this);
        }
        Material Material(Shader shader) { var material = new Material(shader); materials.Add(material); return material; }
        void Stars(Material material)
        {
            var mesh = new FacetMesh(); var random = new System.Random(82241);
            Color[] colours = {new Color(.65f,.77f,1),new Color(.92f,.95f,1),new Color(1,.94f,.74f),new Color(1,.69f,.40f)};
            for (int i = 0; i < 3600; i++)
            {
                float z = (float)random.NextDouble()*2-1, angle = (float)random.NextDouble()*Mathf.PI*2;
                Vector3 direction = new Vector3(Mathf.Sqrt(1-z*z)*Mathf.Cos(angle),z,Mathf.Sqrt(1-z*z)*Mathf.Sin(angle));
                Vector3 centre = direction*1800;
                Vector3 u = Vector3.Cross(direction,Vector3.up).normalized, v = Vector3.Cross(direction,u);
                float size = Mathf.Lerp(.25f,1.05f,Mathf.Pow((float)random.NextDouble(),3));
                Color colour = colours[random.Next(10) < 1 ? 0 : random.Next(10) < 6 ? 1 : random.Next(10) < 8 ? 2 : 3] * Mathf.Lerp(.22f,1,(float)random.NextDouble());
                mesh.Quad(centre-u*size-v*size,centre-u*size+v*size,centre+u*size+v*size,centre+u*size-v*size,colour);
            }
            starMesh = mesh.Build("3600 sharp star quads"); Draw("Sharp natural-colour stars",starMesh,material);
        }
        void Sun(Vector3 direction, Material material)
        {
            var root = new GameObject("Sun glow sprite"); root.transform.SetParent(transform,false);
            root.transform.position = direction*1400; root.transform.rotation = Quaternion.LookRotation(-direction);
            sunMesh = new Mesh {name="Sun glow quad"};
            sunMesh.vertices = new[] {new Vector3(-15,-15,0),new Vector3(15,-15,0),new Vector3(15,15,0),new Vector3(-15,15,0)};
            sunMesh.uv = new[] {Vector2.zero,Vector2.right,Vector2.one,Vector2.up}; sunMesh.triangles = new[] {0,1,2,0,2,3};
            root.AddComponent<MeshFilter>().sharedMesh = sunMesh; root.AddComponent<MeshRenderer>().sharedMaterial = material;
        }
        void Draw(string name, Mesh mesh, Material material)
        {
            var root = new GameObject(name); root.transform.SetParent(transform,false);
            root.AddComponent<MeshFilter>().sharedMesh = mesh; root.AddComponent<MeshRenderer>().sharedMaterial = material;
        }
        void Cockpit()
        {
            void Bar(string name, Vector3 position, Vector3 size, float roll = 0)
            {
                var bar = GameObject.CreatePrimitive(PrimitiveType.Cube); bar.name = name; Destroy(bar.GetComponent<Collider>());
                bar.transform.SetParent(Pilot.transform,false); bar.transform.localPosition = position;
                bar.transform.localScale = size; bar.transform.localRotation = Quaternion.Euler(0,0,roll);
                bar.GetComponent<Renderer>().sharedMaterial = cockpitMaterial;
            }
            Bar("Low instrument coaming",new Vector3(0,-.53f,.8f),new Vector3(2.2f,.16f,.32f));
            Bar("Port windscreen frame",new Vector3(-.83f,0,.78f),new Vector3(.045f,1.5f,.045f),-12);
            Bar("Starboard windscreen frame",new Vector3(.83f,0,.78f),new Vector3(.045f,1.5f,.045f),12);
        }
        void OnDestroy()
        {
            foreach (var material in materials) Destroy(material);
            if (starMesh != null) Destroy(starMesh); if (sunMesh != null) Destroy(sunMesh);
        }
    }
}
