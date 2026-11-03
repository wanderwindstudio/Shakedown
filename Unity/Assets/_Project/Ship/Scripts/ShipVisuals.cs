using System.Collections.Generic;
using UnityEngine;

namespace Shakedown.Ship
{
    public sealed class ShipVisuals : MonoBehaviour
    {
        public const int ChunkSize = 8;
        readonly Dictionary<Vector3Int, GameObject> chunks = new Dictionary<Vector3Int, GameObject>();
        readonly List<Material> windowPaints = new List<Material>();
        ShipGrid grid;
        PartCatalog catalog;
        Material stripeMaterial;
        Mesh stripe;
        HullTiles tiles;
        float chamfer;
        bool shaping = true, buildMode;
        public bool Shaping => shaping;
        public void Initialize(ShipGrid data, PartCatalog parts, Material marking, float chamferSize)
        {
            grid = data; catalog = parts; stripeMaterial = marking; chamfer = chamferSize;
            tiles = new HullTiles(chamfer);
            var markingMesh = new FlatMesh();
            markingMesh.Polygon(new List<Vector3> { new Vector3(-.3f,.14f,.501f), new Vector3(.38f,.14f,.501f), new Vector3(.38f,.38f,.501f), new Vector3(-.3f,.38f,.501f) }, Color.white);
            stripe = markingMesh.Create("Orientation stripe");
            for (int i = 0; i < 8; i++)
            {
                var material = new Material(catalog.parts[1].material);
                Color tint = Color.Lerp(ShipPalette.Get(i), new Color(.4f,.75f,.85f), .35f); tint.a = .32f;
                material.color = tint;
                windowPaints.Add(material);
            }
            RebuildAll();
        }
        public static Vector3Int ChunkFor(Vector3Int p) => new Vector3Int(Mathf.FloorToInt(p.x / 8f), Mathf.FloorToInt(p.y / 8f), Mathf.FloorToInt(p.z / 8f));
        public static Vector3 Centre(Vector3Int p) => (Vector3)p * ShipGrid.CellSize + Vector3.up * (ShipGrid.CellSize / 2);
        public static Vector3 Corner(Vector3Int p) => ((Vector3)p + new Vector3(-.5f,0,-.5f)) * ShipGrid.CellSize;
        public void ReplaceGrid(ShipGrid data) { grid = data; RebuildAll(); }
        public void ToggleShaping() { shaping = !shaping; RebuildAll(); }
        public void SetChamfer(float size)
        {
            if (Mathf.Approximately(size, chamfer)) return;
            chamfer = size; tiles.Dispose(); tiles = new HullTiles(chamfer); RebuildAll();
        }
        public void SetBuildMode(bool value)
        {
            buildMode = value;
            foreach (var chunk in chunks.Values) chunk.transform.Find("Lock hints")?.gameObject.SetActive(value);
        }
        static IEnumerable<Vector3Int> CornersOf(Vector3Int p)
        {
            for (int x = 0; x < 2; x++) for (int y = 0; y < 2; y++) for (int z = 0; z < 2; z++) yield return p + new Vector3Int(x,y,z);
        }
        public void RebuildAll()
        {
            foreach (var chunk in chunks.Values) DisposeChunk(chunk);
            chunks.Clear();
            var keys = new HashSet<Vector3Int>();
            foreach (var pair in grid.Cells)
            {
                keys.Add(ChunkFor(pair.Key));
                foreach (var corner in CornersOf(pair.Key)) keys.Add(ChunkFor(corner));
            }
            foreach (var key in keys) Rebuild(key, true);
            Physics.SyncTransforms();
        }
        public void Changed(Vector3Int position)
        {
            var keys = new HashSet<Vector3Int>();
            foreach (var corner in CornersOf(position)) keys.Add(ChunkFor(corner));
            keys.Add(ChunkFor(position));
            foreach (var face in CubeRotations.Faces) keys.Add(ChunkFor(position + face));
            foreach (var key in keys) Rebuild(key, key == ChunkFor(position));
            Physics.SyncTransforms();
        }
        void Rebuild(Vector3Int key, bool rebuildCollision)
        {
            if (!chunks.TryGetValue(key, out var root))
            {
                root = new GameObject("Chunk " + key);
                root.transform.SetParent(transform, false);
                root.transform.localPosition = (Vector3)(key * ChunkSize) * ShipGrid.CellSize;
                root.AddComponent<ShipChunk>();
                chunks.Add(key, root);
                rebuildCollision = true;
            }
            Vector3 origin = root.transform.position;
            var opaque = new FlatMesh(); var marks = new FlatMesh(); var hints = new FlatMesh();
            var windows = new FlatMesh[8]; for (int i = 0; i < 8; i++) windows[i] = new FlatMesh();
            var collision = new FlatMesh();
            if (rebuildCollision)
            {
                var old = root.transform.Find("Fixed collisions");
                if (old != null) { old.gameObject.SetActive(false); Destroy(old.gameObject); }
            }
            var start = key * ChunkSize;
            // A chunk reads a bounded neighbourhood, never scans every block in the ship.
            for (int x = 0; x < ChunkSize; x++) for (int y = 0; y < ChunkSize; y++) for (int z = 0; z < ChunkSize; z++)
            {
                var p = start + new Vector3Int(x,y,z);
                if (grid.TryGet(p, out var cell))
                {
                    var definition = catalog.Find(cell.partId);
                    var matrix = Matrix4x4.TRS(Centre(p)-origin, CubeRotations.Get(cell.rotation), Vector3.one * ShipGrid.CellSize);
                    bool useTiles = shaping && definition.autoShapes && !cell.locked;
                    if (!useTiles)
                    {
                        var destination = definition.collisionKind == PartCollision.Box && !definition.autoShapes ? windows[Mathf.Clamp(cell.paint,0,7)] : opaque;
                        destination.Add(definition.visualMesh, matrix, ShipPalette.Get(cell.paint).linear);
                        if (definition.collisionKind == PartCollision.Box) marks.Add(stripe, matrix, Color.white);
                    }
                    if (useTiles) AddFixedInterfaces(opaque, p, origin, cell.paint);
                    if (cell.locked && definition.autoShapes) AddLockHint(hints, Centre(p)-origin);
                    if (rebuildCollision)
                    {
                        if (definition.collisionKind == PartCollision.Box) collision.Add(definition.visualMesh, matrix, Color.white);
                        else AddFixedCollision(root, p, cell, definition);
                    }
                }
                if (shaping) AddTile(opaque, p, origin);
            }
            SetMesh(root, "Opaque hull", opaque, catalog.parts[0].material);
            SetMesh(root, "Stripes", marks, stripeMaterial);
            for (int i = 0; i < 8; i++) SetMesh(root, "Window paint " + i, windows[i], windowPaints[i]);
            SetMesh(root, "Lock hints", hints, stripeMaterial);
            root.transform.Find("Lock hints")?.gameObject.SetActive(buildMode);
            if (rebuildCollision)
            {
                var collider = root.GetComponent<MeshCollider>();
                if (collider == null) collider = root.AddComponent<MeshCollider>();
                var previous = collider.sharedMesh;
                collider.sharedMesh = collision.Count == 0 ? null : collision.Create("Grid box collision");
                if (previous != null) Destroy(previous);
            }
        }
        void AddTile(FlatMesh output, Vector3Int corner, Vector3 origin)
        {
            int pattern = 0;
            for (int bit = 0; bit < 8; bit++) if (grid.Contains(corner + HullTileLookup.CellOffset(bit))) pattern |= 1 << bit;
            var entry = HullTileLookup.Cases[pattern];
            var symmetry = HullTileLookup.Symmetries[entry.symmetry];
            var matrix = Matrix4x4.Translate(Corner(corner)-origin) * symmetry;
            for (int bit = 0; bit < 8; bit++)
            {
                var mesh = tiles.Octants[entry.tile,bit];
                if (mesh.vertexCount == 0) continue;
                int actual = HullTileLookup.Bit(symmetry.MultiplyVector(HullTileLookup.Sign(bit)));
                if (!grid.TryGet(corner + HullTileLookup.CellOffset(actual), out var cell)) continue;
                if (!catalog.Find(cell.partId).autoShapes || cell.locked) continue;
                output.Add(mesh, matrix, ShipPalette.Get(cell.paint).linear);
            }
        }
        void AddFixedInterfaces(FlatMesh output, Vector3Int p, Vector3 origin, int paint)
        {
            // Fixed pieces count as solid for bevels, but a hollow frame still needs a visible floor.
            foreach (var normal in CubeRotations.Faces)
            {
                if (!grid.TryGet(p + normal, out var neighbour)) continue;
                if (catalog.Find(neighbour.partId).collisionKind == PartCollision.Box) continue;
                Vector3 centre = Centre(p)-origin + (Vector3)normal * (ShipGrid.CellSize / 2);
                Vector3 u = Vector3.Cross(normal, normal.y == 0 ? Vector3.up : Vector3.right) * (ShipGrid.CellSize / 2);
                Vector3 v = Vector3.Cross(normal, u);
                output.Polygon(new List<Vector3> { centre-u-v, centre+u-v, centre+u+v, centre-u+v }, ShipPalette.Get(paint).linear);
            }
        }
        void AddFixedCollision(GameObject chunk, Vector3Int p, ShipCell cell, PartDefinition definition)
        {
            var parent = chunk.transform.Find("Fixed collisions");
            if (parent == null) { parent = new GameObject("Fixed collisions").transform; parent.SetParent(chunk.transform, false); }
            var root = new GameObject(definition.displayName + " collision");
            root.transform.SetParent(parent, false);
            root.transform.position = Centre(p); root.transform.rotation = CubeRotations.Get(cell.rotation);
            root.transform.localScale = Vector3.one * ShipGrid.CellSize;
            var marker = root.AddComponent<ShipChunk>(); marker.fixedPiece = true; marker.cell = p;
            if (definition.collisionKind == PartCollision.Ramp)
            {
                var collider = root.AddComponent<MeshCollider>(); collider.sharedMesh = definition.visualMesh; collider.convex = true;
            }
            else
            {
                AddBox(root, new Vector3(-.45f,-.05f,0), new Vector3(.1f,.9f,1));
                AddBox(root, new Vector3(.45f,-.05f,0), new Vector3(.1f,.9f,1));
                AddBox(root, new Vector3(0,.45f,0), new Vector3(1,.1f,1));
            }
        }
        static void AddBox(GameObject root, Vector3 centre, Vector3 size) { var box = root.AddComponent<BoxCollider>(); box.center = centre; box.size = size; }
        void AddLockHint(FlatMesh output, Vector3 centre)
        {
            var cube = catalog.parts[0].visualMesh;
            output.Add(cube, Matrix4x4.TRS(centre + new Vector3(.9f,1.27f,-1), Quaternion.identity, new Vector3(.4f,.025f,.06f)), Color.white);
            output.Add(cube, Matrix4x4.TRS(centre + new Vector3(1.07f,1.27f,-.83f), Quaternion.identity, new Vector3(.06f,.025f,.4f)), Color.white);
        }
        void SetMesh(GameObject root, string name, FlatMesh data, Material material)
        {
            var existing = root.transform.Find(name);
            if (existing != null) { Destroy(existing.GetComponent<MeshFilter>().sharedMesh); existing.gameObject.SetActive(false); Destroy(existing.gameObject); }
            var child = new GameObject(name); child.transform.SetParent(root.transform, false);
            child.AddComponent<MeshFilter>().sharedMesh = data.Create(name);
            child.AddComponent<MeshRenderer>().sharedMaterial = material;
        }
        void DisposeChunk(GameObject chunk)
        {
            chunk.SetActive(false);
            foreach (var filter in chunk.GetComponentsInChildren<MeshFilter>(true)) Destroy(filter.sharedMesh);
            var collider = chunk.GetComponent<MeshCollider>(); if (collider != null && collider.sharedMesh != null) Destroy(collider.sharedMesh);
            Destroy(chunk);
        }
        void OnDestroy()
        {
            foreach (var chunk in chunks.Values) if (chunk != null) DisposeChunk(chunk);
            tiles?.Dispose(); if (stripe != null) Destroy(stripe);
            foreach (var material in windowPaints) Destroy(material);
        }
    }
}
