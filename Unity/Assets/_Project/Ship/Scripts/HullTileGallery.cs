using UnityEngine;
using System.Collections.Generic;
using Shakedown.Player;

namespace Shakedown.Ship
{
    // A static modelling reference scene, using the same tiles as the yard; no editor callbacks.
    public sealed class HullTileGallery : MonoBehaviour
    {
        public PartCatalog catalog;
        HullTiles tiles;
        readonly List<Mesh> ownedMeshes = new List<Mesh>();
        Camera view;
        readonly Vector3[] centres = new Vector3[22];
        void Start()
        {
            FirstPersonController.LockCursor(false);
            RenderSettings.fog = false;
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(.55f,.55f,.62f);
            view = new GameObject("Tile reference camera").AddComponent<Camera>();
            view.transform.position = new Vector3(0,0,-40);
            view.orthographic = true; view.orthographicSize = 9;
            view.clearFlags = CameraClearFlags.SolidColor; view.backgroundColor = new Color(.075f,.08f,.11f);
            var light = new GameObject("Reference light").AddComponent<Light>();
            light.type = LightType.Directional; light.intensity = 1.4f;
            light.transform.rotation = Quaternion.Euler(35,-145,0); RenderSettings.sun = light;
            tiles = new HullTiles(.5f);
            for (int tile = 0; tile < 22; tile++)
            {
                centres[tile] = new Vector3((tile%6-2.5f)*4.7f, (1.5f-tile/6)*4.1f, 0);
                Quaternion rotation = Quaternion.Euler(-25,135,0);
                var mesh = new FlatMesh();
                for (int bit = 0; bit < 8; bit++) mesh.Add(tiles.Octants[tile,bit], Matrix4x4.Rotate(rotation), new Color(.63f,.68f,.76f).linear);
                Draw("HullTile_" + tile.ToString("D2"), mesh, catalog.parts[0].material, centres[tile]);
                // The tile's outer cube is only a guide, never part of its shipped surface.
                var guide = new FlatMesh();
                for (int axis = 0; axis < 3; axis++) for (int a = -1; a <= 1; a += 2) for (int b = -1; b <= 1; b += 2)
                {
                    var size = Vector3.one * .018f; size[axis] = 2.5f;
                    var p = Vector3.zero; p[(axis+1)%3] = a*1.25f; p[(axis+2)%3] = b*1.25f;
                    guide.Add(catalog.parts[0].visualMesh, Matrix4x4.Rotate(rotation) * Matrix4x4.TRS(p,Quaternion.identity,size), new Color(.24f,.3f,.4f).linear);
                }
                Draw("2.5 m guide", guide, catalog.parts[0].material, centres[tile]);
            }
        }
        void Draw(string name, FlatMesh mesh, Material material, Vector3 position)
        {
            var root = new GameObject(name); root.transform.position = position;
            var created = mesh.Create(name); ownedMeshes.Add(created);
            root.AddComponent<MeshFilter>().sharedMesh = created;
            root.AddComponent<MeshRenderer>().sharedMaterial = material;
        }
        void OnGUI()
        {
            if (view == null) return;
            GUI.color = new Color(.85f,.89f,.96f);
            GUI.Label(new Rect(20,12,900,24), "M1b · 22 canonical hull tiles · 0.5 m chamfer · wire cubes show tile boundaries");
            for (int tile = 0; tile < 22; tile++)
            {
                Vector3 point = view.WorldToScreenPoint(centres[tile] + Vector3.down * 1.7f);
                GUI.Label(new Rect(point.x-110, Screen.height-point.y,220,24), $"HullTile_{tile:D2}  /  0x{HullTileLookup.BasePatterns[tile]:X2}");
            }
            GUI.Label(new Rect(20,Screen.height-28,1400,24), "00: empty · 21: full interior (both have no exposed surface). Surfaces are split by occupied octant for cell paint and fixed-piece replacement.");
        }
        void OnDestroy()
        {
            tiles?.Dispose();
            foreach (var mesh in ownedMeshes) Destroy(mesh);
        }
    }
}
