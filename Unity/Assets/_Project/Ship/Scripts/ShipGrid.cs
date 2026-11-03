using System.Collections.Generic;
using UnityEngine;

namespace Shakedown.Ship
{
    [System.Serializable]
    public struct ShipCell
    {
        public string partId;
        public int rotation, paint;
        public bool locked;
        public ShipCell(string id, int orientation = 0, int colour = 0, bool shapeLocked = false)
        { partId = id; rotation = orientation; paint = colour; locked = shapeLocked; }
    }

    public sealed class ShipGrid
    {
        public const float CellSize = 2.5f;
        public const int AxisLimit = 128;
        readonly Dictionary<Vector3Int, ShipCell> cells = new Dictionary<Vector3Int, ShipCell>();
        public IEnumerable<KeyValuePair<Vector3Int, ShipCell>> Cells => cells;
        public int Count => cells.Count;
        public bool TryGet(Vector3Int position, out ShipCell cell) => cells.TryGetValue(position, out cell);
        public bool Contains(Vector3Int position) => cells.ContainsKey(position);
        // A fixed address space makes the limit independent of placement order.
        public static bool InBounds(Vector3Int p) => p.x >= -64 && p.x < 64 && p.y >= 0 && p.y < 128 && p.z >= -64 && p.z < 64;
        public bool CanPlace(Vector3Int p, out string reason)
        {
            if (!InBounds(p)) { reason = "Outside the 128-cell grid."; return false; }
            if (Contains(p)) { reason = "Cell occupied."; return false; }
            foreach (var face in CubeRotations.Faces)
                if (Contains(p + face)) { reason = ""; return true; }
            reason = "A block must share a face with the ship.";
            return false;
        }
        public bool CanRemove(Vector3Int p, out string reason)
        {
            if (!Contains(p)) { reason = "No block here."; return false; }
            if (Count == 1) { reason = "The last block must stay."; return false; }
            if (!IsConnected(p)) { reason = "Removal would split the ship."; return false; }
            reason = "";
            return true;
        }
        public bool IsConnected(Vector3Int? excluded = null)
        {
            var seen = new HashSet<Vector3Int>();
            var queue = new Queue<Vector3Int>();
            foreach (var p in cells.Keys)
                if (!excluded.HasValue || p != excluded.Value) { queue.Enqueue(p); seen.Add(p); break; }
            while (queue.Count > 0)
            {
                var p = queue.Dequeue();
                foreach (var face in CubeRotations.Faces)
                {
                    var next = p + face;
                    if ((!excluded.HasValue || next != excluded.Value) && Contains(next) && seen.Add(next)) queue.Enqueue(next);
                }
            }
            return seen.Count == Count - (excluded.HasValue ? 1 : 0);
        }
        // Commands and validated loading own mutations; visual objects never own ship data.
        internal void Set(Vector3Int p, ShipCell cell) => cells[p] = cell;
        internal void Remove(Vector3Int p) => cells.Remove(p);
        public float Mass(PartCatalog catalog)
        {
            float total = 0;
            foreach (var cell in cells.Values) total += catalog.Find(cell.partId).massKg;
            return total;
        }
    }
}
