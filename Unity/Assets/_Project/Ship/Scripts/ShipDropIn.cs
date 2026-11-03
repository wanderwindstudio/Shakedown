using UnityEngine;
using Shakedown.Player;

namespace Shakedown.Ship
{
    public static class ShipDropIn
    {
        public static bool TryFindPosition(Vector3 origin, FirstPersonController player, ShipGrid grid, PartCatalog catalog, out Vector3 feet)
        {
            Physics.SyncTransforms();
            feet = default;
            // The pad is at zero. Continue below rejected surfaces, including floors in the same chunk.
            while (origin.y >= 0)
            {
                RaycastHit? nearest = null;
                foreach (var hit in Physics.RaycastAll(origin, Vector3.down, origin.y + .1f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore))
                {
                    if (player.OwnsCollider(hit.collider)) continue;
                    if (!nearest.HasValue || hit.distance < nearest.Value.distance) nearest = hit;
                }
                if (!nearest.HasValue) return false;
                var surface = nearest.Value;
                bool walkable = surface.normal.y >= Mathf.Cos(player.SlopeLimit * Mathf.Deg2Rad);
                // A capsule touches a slope off-centre; its feet need more clearance than on a flat pad.
                float slopeClearance = walkable ? player.BodyRadius * (1 / surface.normal.y - 1) : 0;
                var candidate = surface.point + Vector3.up * (.05f + slopeClearance);
                if (walkable && !IntersectsShip(candidate, player.BodyHeight, player.BodyRadius, grid, catalog) && player.CanStandAt(candidate))
                {
                    feet = candidate;
                    return true;
                }
                origin.y = surface.point.y - .02f;
            }
            return false;
        }

        static bool IntersectsShip(Vector3 feet, float height, float radius, ShipGrid grid, PartCatalog catalog)
        {
            // Non-convex mesh colliders are surfaces: a capsule fully inside a block can miss them.
            // Check the actual occupied cells as well, so solid blocks never become standing space.
            Vector3 bottom = feet + Vector3.up * radius;
            Vector3 top = feet + Vector3.up * (height - radius);
            int minX = Mathf.FloorToInt((feet.x - radius) / ShipGrid.CellSize + .5f);
            int maxX = Mathf.FloorToInt((feet.x + radius) / ShipGrid.CellSize + .5f);
            int minY = Mathf.FloorToInt(feet.y / ShipGrid.CellSize);
            int maxY = Mathf.FloorToInt((feet.y + height) / ShipGrid.CellSize);
            int minZ = Mathf.FloorToInt((feet.z - radius) / ShipGrid.CellSize + .5f);
            int maxZ = Mathf.FloorToInt((feet.z + radius) / ShipGrid.CellSize + .5f);
            for (int x = minX; x <= maxX; x++)
                for (int y = minY; y <= maxY; y++)
                    for (int z = minZ; z <= maxZ; z++)
                    {
                        var cell = new Vector3Int(x, y, z);
                        if (!grid.TryGet(cell, out var data)) continue;
                        // Convex ramps and frame bars are solid physics volumes, but not solid cell boxes.
                        if (catalog.Find(data.partId).collisionKind != PartCollision.Box) continue;
                        var bounds = new Bounds(ShipVisuals.Centre(cell), Vector3.one * ShipGrid.CellSize);
                        float dx = feet.x - Mathf.Clamp(feet.x, bounds.min.x, bounds.max.x);
                        float dz = feet.z - Mathf.Clamp(feet.z, bounds.min.z, bounds.max.z);
                        float dy = Mathf.Max(0, bounds.min.y - top.y, bottom.y - bounds.max.y);
                        if (dx * dx + dy * dy + dz * dz < radius * radius) return true;
                    }
            return false;
        }
    }
}
