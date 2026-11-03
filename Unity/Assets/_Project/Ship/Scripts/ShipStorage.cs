using System;
using System.IO;
using System.Collections.Generic;
using UnityEngine;

namespace Shakedown.Ship
{
    public static class ShipStorage
    {
        [Serializable] sealed class FileData { public int formatVersion = 1; public List<BlockData> blocks = new List<BlockData>(); }
        [Serializable] sealed class BlockData { public int x, y, z; public string partId; public int rotation, paint; public bool locked; }
        public static string PathFor(string name) => Path.Combine(Application.persistentDataPath, "ships", name + ".json");
        public static void Save(ShipGrid grid, string name)
        {
            var data = new FileData();
            foreach (var pair in grid.Cells)
                data.blocks.Add(new BlockData { x = pair.Key.x, y = pair.Key.y, z = pair.Key.z, partId = pair.Value.partId, rotation = pair.Value.rotation, paint = pair.Value.paint, locked = pair.Value.locked });
            data.blocks.Sort((a, b) => a.x != b.x ? a.x.CompareTo(b.x) : a.y != b.y ? a.y.CompareTo(b.y) : a.z.CompareTo(b.z));
            string path = PathFor(name);
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            File.WriteAllText(path + ".tmp", JsonUtility.ToJson(data, true));
            if (File.Exists(path)) File.Replace(path + ".tmp", path, null);
            else File.Move(path + ".tmp", path);
        }
        public static ShipGrid Load(string name, PartCatalog catalog)
        {
            var data = JsonUtility.FromJson<FileData>(File.ReadAllText(PathFor(name)));
            if (data == null || data.formatVersion != 1 || data.blocks == null || data.blocks.Count == 0) throw new InvalidDataException("Unsupported or empty ship file.");
            var grid = new ShipGrid();
            foreach (var block in data.blocks)
            {
                var p = new Vector3Int(block.x, block.y, block.z);
                if (!ShipGrid.InBounds(p) || grid.Contains(p) || catalog.Find(block.partId) == null || block.rotation < 0 || block.rotation > 23 || block.paint < 0)
                    throw new InvalidDataException("Invalid block data.");
                grid.Set(p, new ShipCell(block.partId, block.rotation, block.paint, block.locked));
            }
            if (!grid.IsConnected()) throw new InvalidDataException("Ship is disconnected.");
            return grid;
        }
    }
}
