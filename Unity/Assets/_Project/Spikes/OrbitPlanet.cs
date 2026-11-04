using System.Collections.Generic;
using UnityEngine;
using TestPlanet;

namespace Shakedown.Spikes
{
    public sealed class OrbitPlanet : MonoBehaviour
    {
        public const float Radius = 80;
        public static readonly Vector3 LandingDirection = new Vector3(-.30f,.18f,-.937f).normalized;
        readonly List<Vector3> islands = new List<Vector3>();
        readonly List<Mesh> meshes = new List<Mesh>();
        Transform clouds;
        public void Generate(Material surface, Material cloud, Material atmosphere, int seed)
        {
            var random = new System.Random(seed);
            islands.Add(LandingDirection);
            for (int i = 0; i < 9; i++)
                islands.Add(Quaternion.Euler((float)random.NextDouble()*360,(float)random.NextDouble()*360,0)*Vector3.forward);
            var lods = new LOD[3];
            for (int level = 0; level < 3; level++)
            {
                int subdivisions = 4-level;
                var root = Make("Pelagic sphere · " + (20 * (1 << (subdivisions*2))) + " faces", SurfaceMesh(subdivisions), surface);
                lods[level] = new LOD(level == 0 ? .55f : level == 1 ? .22f : .0001f, new[] {root.GetComponent<Renderer>()});
            }
            var group = gameObject.AddComponent<LODGroup>();
            group.fadeMode = LODFadeMode.CrossFade;
            group.animateCrossFading = true;
            LODGroup.crossFadeAnimationDuration = .8f;
            group.SetLODs(lods); group.RecalculateBounds();
            clouds = Make("Faceted moving cloud deck", CloudMesh(seed), cloud).transform;
            OrbitSphere.Icosphere(3,out var points,out var faces);
            var rim = new FacetMesh();
            foreach (var f in faces) rim.Triangle(points[f.a]*Radius*1.055f,points[f.b]*Radius*1.055f,points[f.c]*Radius*1.055f,Color.white);
            Make("Lit-side atmosphere",rim.Build("Thin atmosphere shell"),atmosphere);
        }
        float Height(Vector3 direction)
        {
            float island = 0;
            foreach (var centre in islands)
            {
                float angle = Mathf.Acos(Mathf.Clamp(Vector3.Dot(centre,direction),-1,1));
                island = Mathf.Max(island,Mathf.SmoothStep(0,1,1-angle/.31f));
            }
            float noise = OrbitSphere.Noise(direction*11 + new Vector3(42.7f,17.1f,63.2f));
            return island*.025f + (noise-.5f)*.01f - .008f;
        }
        Mesh SurfaceMesh(int subdivisions)
        {
            OrbitSphere.Icosphere(subdivisions,out var points,out var faces);
            var mesh = new FacetMesh();
            foreach (var f in faces)
            {
                Vector3 a = points[f.a], b = points[f.b], c = points[f.c];
                float ha = Height(a), hb = Height(b), hc = Height(c);
                float h = Height((a+b+c).normalized);
                Color colour;
                if (h < -.003f) colour = Color.Lerp(new Color(.018f,.075f,.13f),new Color(.035f,.22f,.27f),Mathf.InverseLerp(-.009f,-.003f,h));
                else if (h < 0) colour = Color.Lerp(new Color(.035f,.22f,.27f),new Color(.12f,.40f,.40f),Mathf.InverseLerp(-.003f,0,h));
                else if (h < .0025f) colour = Color.Lerp(new Color(.65f,.61f,.45f),new Color(.25f,.35f,.23f),h/.0025f);
                else colour = Color.Lerp(new Color(.25f,.35f,.23f),new Color(.37f,.36f,.32f),Mathf.InverseLerp(.006f,.017f,h));
                mesh.Triangle(a*Radius*(1+Mathf.Max(0,ha)),b*Radius*(1+Mathf.Max(0,hb)),c*Radius*(1+Mathf.Max(0,hc)),colour);
            }
            return mesh.Build("Flat-shaded ocean world");
        }
        Mesh CloudMesh(int seed)
        {
            OrbitSphere.Icosphere(3,out var points,out var faces);
            var mesh = new FacetMesh();
            foreach (var f in faces)
            {
                Vector3 centre = (points[f.a]+points[f.b]+points[f.c]).normalized;
                float density = OrbitSphere.Noise(centre*5 + Vector3.one*(seed*.017f));
                float alpha = Mathf.SmoothStep(0,.65f,Mathf.InverseLerp(.44f,.68f,density));
                if (alpha < .015f) continue;
                var colour = new Color(.85f,.87f,.88f,alpha);
                mesh.Triangle(points[f.a]*Radius*1.035f,points[f.b]*Radius*1.035f,points[f.c]*Radius*1.035f,colour);
            }
            return mesh.Build("Faceted cloud patches");
        }
        GameObject Make(string name, Mesh mesh, Material material)
        {
            meshes.Add(mesh);
            var root = new GameObject(name); root.transform.SetParent(transform,false);
            root.AddComponent<MeshFilter>().sharedMesh = mesh;
            root.AddComponent<MeshRenderer>().sharedMaterial = material;
            return root;
        }
        void Update() { if (clouds != null) clouds.Rotate(Vector3.up,.18f*Time.deltaTime,Space.World); }
        void OnDestroy() { foreach (var mesh in meshes) Destroy(mesh); }
    }
}
