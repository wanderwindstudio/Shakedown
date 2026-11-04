using System.Collections.Generic;
using System.Text.RegularExpressions;
using UnityEngine;
using Shakedown.Player;

namespace Shakedown.Assembly
{
    public sealed class AssemblyView : MonoBehaviour
    {
        public Material[] palette;
        public Material jointMaterial, doorMaterial;
        public FirstPersonController player;
        AssemblyLayout layout;
        readonly List<Mesh> owned = new List<Mesh>();
        readonly Dictionary<string, Material> colours = new Dictionary<string, Material>();
        static readonly Regex slotName = new Regex(@"_(Front|Back|Left|Right)_(\d+)_(\d+|Chamfer)$");
        static string Clean(string name) => Regex.Replace(name.Replace(" (Instance)", ""), @"\.\d{3}$", "");
        public void Initialize(AssemblyLayout data)
        {
            layout = data;
            foreach (var m in palette)colours[Clean(m.name)] = m;
            Rebuild();
        }
        public void Rebuild()
        {
            foreach (Transform child in transform)
            {
                child.gameObject.SetActive(false);
                Destroy(child.gameObject);
            }
            foreach (var mesh in owned)Destroy(mesh);
            owned.Clear();
            foreach (var c in layout.Data.compartments)BuildCompartment(c);
            for (int i = 0;i<layout.Data.compartments.Count;i++)for (int j = i+1;j<layout.Data.compartments.Count;j++)
            {
                var a = layout.Data.compartments[i];
                var b = layout.Data.compartments[j];
                if (layout.Touch(a, b, out var wa, out _))BuildJoint(a, b, wa);
            }
            foreach (var door in layout.Data.doors)BuildDoor(door);
            Physics.SyncTransforms();
        }
        public GameObject Model(PlacedCompartment c, Transform parent, bool ghost = false)
        {
            var d = layout.Definition(c);
            var root = new GameObject(d.id+" "+c.id);
            root.transform.SetParent(parent, false);
            root.transform.position = layout.Centre(c);
            root.transform.rotation = layout.Rotation(c);
            var model = Instantiate(d.model, root.transform);
            model.transform.localPosition = Vector3.zero;
            model.transform.localRotation = Quaternion.identity;
            model.transform.localScale = Vector3.one;
            foreach (var collider in model.GetComponentsInChildren<Collider>())
            {
                collider.enabled = false;
                Destroy(collider);
            }
            return root;
        }
        void BuildCompartment(PlacedCompartment c)
        {
            var root = Model(c, transform);
            root.AddComponent<AssemblyHit>().compartment = c.id;
            var definition = layout.Definition(c);
            foreach (var filter in root.GetComponentsInChildren<MeshFilter>())
            {
                var go = filter.gameObject;
                string name = go.name;
                var renderer = go.GetComponent<Renderer>();
                if (renderer != null)
                {
                    var mapped = renderer.sharedMaterials;
                    for (int i = 0;i<mapped.Length;i++)if (mapped[i] != null && colours.TryGetValue(Clean(mapped[i].name), out var material))mapped[i] = material;
                    renderer.sharedMaterials = mapped;
                }
                var match = slotName.Match(name);
                if (match.Success)
                {
                    Wall wall = (Wall)System.Enum.Parse(typeof(Wall), match.Groups[1].Value);
                    int column = int.Parse(match.Groups[2].Value), row = match.Groups[3].Value == "Chamfer"?definition.height-1:int.Parse(match.Groups[3].Value);
                    if (layout.IsCut(c.id, wall, column, row))
                    {
                        go.SetActive(false);
                        continue;
                    }
                    var marker = go.AddComponent<AssemblySlot>();
                    marker.compartment = c.id;
                    marker.wall = wall;
                    marker.column = column;
                    marker.row = row;
                    go.AddComponent<MeshCollider>().sharedMesh = filter.sharedMesh;
                }
                else if (name.StartsWith("COL_"))
                {
                    if (renderer != null)renderer.enabled = false;
                    if (name.Contains("RearWall"))continue;
                    var collider = go.AddComponent<MeshCollider>();
                    collider.sharedMesh = filter.sharedMesh;
                    collider.convex = true;
                }
                else if (!definition.cockpit && (name.Contains("_Floor_") || name.Contains("_Ceiling_")))go.AddComponent<MeshCollider>().sharedMesh = filter.sharedMesh;
            }
            // Gentle fill makes the empty shells usable without replacing the yard's dusk lighting.
            var lamp = new GameObject("Workshop fill").AddComponent<Light>();
            lamp.transform.SetParent(root.transform, false);
            lamp.type = LightType.Point;
            lamp.transform.localPosition = new Vector3(0, definition.height-.3f, 0);
            lamp.range = Mathf.Max(definition.width, definition.length)+2;
            lamp.intensity = 1.2f;
            lamp.color = new Color(1, .87f, .71f);
        }
        void BuildJoint(PlacedCompartment a, PlacedCompartment b, Wall wall)
        {
            Vector3 normal = layout.Normal(a, wall);
            var ra = layout.Footprint(a);
            var rb = layout.Footprint(b);
            bool alongX = Mathf.Abs(normal.x)>.5f;
            float min = Mathf.Max(alongX?ra.yMin:ra.xMin, alongX?rb.yMin:rb.xMin)+.5f;
            float max = Mathf.Min(alongX?ra.yMax:ra.xMax, alongX?rb.yMax:rb.xMax)-.5f;
            Vector3 start = layout.Slot(a, wall, 0);
            if (alongX)start.z = (min+max)/2;
            else start.x = (min+max)/2;
            var mesh = AssemblyGeometry.Collar(Mathf.Max(.01f, max-min), Mathf.Min(layout.Definition(a).height, layout.Definition(b).height), 1);
            owned.Add(mesh);
            var root = AssemblyGeometry.Mesh("Joint "+a.id+"–"+b.id, transform, mesh, jointMaterial);
            root.transform.SetPositionAndRotation(start, Quaternion.LookRotation(normal));
            AssemblyGeometry.Box("Joint floor", root.transform, new Vector3(0, -.08f, .5f), new Vector3(max-min, .16f, 1), jointMaterial);
        }
        void BuildDoor(DoorData data)
        {
            var c = layout.Find(data.a);
            Vector3 normal = layout.Normal(c, data.wallA);
            var root = new GameObject(data.b<0?"Entrance "+data.id:"Door "+data.id);
            root.transform.SetParent(transform, false);
            root.transform.SetPositionAndRotation(layout.Slot(c, data.wallA, data.columnA), Quaternion.LookRotation(normal));
            float depth = data.b<0?.8f:1;
            AssemblyGeometry.Box("Left jamb", root.transform, new Vector3(-.54f, 1, depth/2), new Vector3(.08f, 2, depth), jointMaterial);
            AssemblyGeometry.Box("Right jamb", root.transform, new Vector3(.54f, 1, depth/2), new Vector3(.08f, 2, depth), jointMaterial);
            AssemblyGeometry.Box("Header", root.transform, new Vector3(0, 2.04f, depth/2), new Vector3(1.16f, .08f, depth), jointMaterial);
            AssemblyGeometry.Box("Threshold", root.transform, new Vector3(0, -.04f, depth/2), new Vector3(1, .08f, depth), jointMaterial);
            var slide = new GameObject("Sliding assembly");
            slide.transform.SetParent(root.transform, false);
            slide.transform.localPosition = new Vector3(0, 0, depth/2);
            var leaf = AssemblyGeometry.Box("Sliding door leaf", slide.transform, new Vector3(0, 1, 0), new Vector3(.98f, 1.98f, .08f), doorMaterial);
            var door = slide.AddComponent<AssemblyDoor>();
            door.id = data.id;
            door.leaf = leaf.transform;
            door.player = player;
            // Mark the whole frame too, so F remains easy to aim at while its leaf is open.
            var hit = root.AddComponent<AssemblyDoor>();
            hit.id = data.id;
            hit.enabled = false;
            if (data.b<0)
            {
                var mesh = AssemblyGeometry.Ramp(AssemblyLayout.Floor, 1.8f);
                owned.Add(mesh);
                var ramp = AssemblyGeometry.Mesh("Pad entrance ramp", root.transform, mesh, jointMaterial, true);
                ramp.transform.localPosition = new Vector3(0, 0, depth);
            }
        }
        void OnDestroy()
        {
            foreach (var mesh in owned)Destroy(mesh);
        }
    }
}
