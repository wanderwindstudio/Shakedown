using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace Shakedown.Ship
{
    public sealed class ShipVisuals : MonoBehaviour
    {
        public const int ChunkSize = 8;
        readonly Dictionary<Vector3Int, GameObject> chunks = new Dictionary<Vector3Int, GameObject>();
        ShipGrid grid;
        PartCatalog catalog;
        Material stripeMaterial;
        Mesh stripe;
        public void Initialize(ShipGrid data, PartCatalog parts, Material marking)
        {
            grid = data; catalog = parts; stripeMaterial = marking;
            stripe = new Mesh { name = "Orientation stripe" };
            stripe.vertices = new[] { new Vector3(-.3f,.14f,.501f), new Vector3(.38f,.14f,.501f), new Vector3(.38f,.38f,.501f), new Vector3(-.3f,.38f,.501f) };
            stripe.triangles = new[] { 0, 1, 2, 0, 2, 3 };
            stripe.RecalculateNormals();
            RebuildAll();
        }
        public static Vector3Int ChunkFor(Vector3Int p) => new Vector3Int(Mathf.FloorToInt(p.x / 8f), Mathf.FloorToInt(p.y / 8f), Mathf.FloorToInt(p.z / 8f));
        public static Vector3 Centre(Vector3Int p) => (Vector3)p * ShipGrid.CellSize + Vector3.up * (ShipGrid.CellSize / 2);
        public void ReplaceGrid(ShipGrid data) { grid = data; RebuildAll(); }
        public void RebuildAll()
        {
            foreach (var chunk in chunks.Values) DisposeChunk(chunk);
            chunks.Clear();
            var keys = new HashSet<Vector3Int>();
            foreach (var pair in grid.Cells) keys.Add(ChunkFor(pair.Key));
            foreach (var key in keys) Rebuild(key);
        }
        public void Changed(Vector3Int position) => Rebuild(ChunkFor(position));
        void Rebuild(Vector3Int key)
        {
            if (chunks.TryGetValue(key, out var previous)) { DisposeChunk(previous); chunks.Remove(key); }
            var groups = new List<CombineInstance>[catalog.parts.Length + 1];
            for (int i = 0; i < groups.Length; i++) groups[i] = new List<CombineInstance>();
            var collision = new List<CombineInstance>();
            Vector3 origin = (Vector3)(key * ChunkSize) * ShipGrid.CellSize;
            foreach (var pair in grid.Cells)
            {
                if (ChunkFor(pair.Key) != key) continue;
                var definition = catalog.Find(pair.Value.partId);
                int partIndex = System.Array.IndexOf(catalog.parts, definition);
                var matrix = Matrix4x4.TRS(Centre(pair.Key) - origin, CubeRotations.Get(pair.Value.rotation), Vector3.one * ShipGrid.CellSize);
                var instance = new CombineInstance { mesh = definition.visualMesh, transform = matrix };
                groups[partIndex].Add(instance);
                groups[groups.Length - 1].Add(new CombineInstance { mesh = stripe, transform = matrix });
                collision.Add(instance);
            }
            if (collision.Count == 0) return;
            var root = new GameObject("Chunk " + key);
            root.transform.SetParent(transform, false);
            root.transform.localPosition = origin;
            root.AddComponent<ShipChunk>();
            var sections = new List<CombineInstance>();
            var materials = new List<Material>();
            var temporary = new List<Mesh>();
            for (int i = 0; i < groups.Length; i++)
            {
                if (groups[i].Count == 0) continue;
                var section = new Mesh { indexFormat = IndexFormat.UInt32 };
                section.CombineMeshes(groups[i].ToArray());
                temporary.Add(section);
                sections.Add(new CombineInstance { mesh = section, transform = Matrix4x4.identity });
                materials.Add(i == catalog.parts.Length ? stripeMaterial : catalog.parts[i].material);
            }
            var visual = new Mesh { name = "Chunk visual", indexFormat = IndexFormat.UInt32 };
            visual.CombineMeshes(sections.ToArray(), false);
            root.AddComponent<MeshFilter>().sharedMesh = visual;
            root.AddComponent<MeshRenderer>().sharedMaterials = materials.ToArray();
            var collider = new Mesh { name = "Chunk collision", indexFormat = IndexFormat.UInt32 };
            collider.CombineMeshes(collision.ToArray());
            root.AddComponent<MeshCollider>().sharedMesh = collider;
            foreach (var mesh in temporary) Destroy(mesh);
            chunks.Add(key, root);
            Physics.SyncTransforms();
        }
        void DisposeChunk(GameObject chunk)
        {
            // Disable immediately so a replaced collider cannot catch a second click this frame.
            chunk.SetActive(false);
            Destroy(chunk.GetComponent<MeshFilter>().sharedMesh);
            Destroy(chunk.GetComponent<MeshCollider>().sharedMesh);
            Destroy(chunk);
        }
        void OnDestroy()
        {
            foreach (var chunk in chunks.Values) if (chunk != null) DisposeChunk(chunk);
            if (stripe != null) Destroy(stripe);
        }
    }
}
