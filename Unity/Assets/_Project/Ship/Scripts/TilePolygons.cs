using System.Collections.Generic;
using UnityEngine;

namespace Shakedown.Ship
{
    // Convex clipping keeps each placeholder inside its occupied octant.
    public static class TilePolygons
    {
        const float Epsilon = .00001f;
        public static List<Vector3> Clip(List<Vector3> polygon, Vector3 normal, float distance)
        {
            var result = new List<Vector3>();
            if (polygon.Count == 0) return result;
            Vector3 previous = polygon[polygon.Count - 1];
            float before = Vector3.Dot(normal, previous) - distance;
            foreach (var point in polygon)
            {
                float after = Vector3.Dot(normal, point) - distance;
                if ((before > Epsilon) != (after > Epsilon)) result.Add(Vector3.Lerp(previous, point, before / (before - after)));
                if (after <= Epsilon) result.Add(point);
                previous = point; before = after;
            }
            return result;
        }
        public static List<Vector3> Ordered(List<Vector3> points, Vector3 normal)
        {
            var unique = new List<Vector3>();
            foreach (var p in points)
                if (!unique.Exists(q => (q - p).sqrMagnitude < Epsilon * Epsilon)) unique.Add(p);
            if (unique.Count < 3) return new List<Vector3>();
            Vector3 centre = Vector3.zero;
            foreach (var p in unique) centre += p;
            centre /= unique.Count;
            Vector3 u = Vector3.Cross(normal, Mathf.Abs(normal.y) < .9f ? Vector3.up : Vector3.right).normalized;
            Vector3 v = Vector3.Cross(normal, u);
            unique.Sort((a,b) => Mathf.Atan2(Vector3.Dot(a-centre,v),Vector3.Dot(a-centre,u)).CompareTo(Mathf.Atan2(Vector3.Dot(b-centre,v),Vector3.Dot(b-centre,u))));
            return unique;
        }
        public static List<List<Vector3>> Subtract(List<Vector3> face, List<Vector3> covering, Vector3 faceNormal)
        {
            var result = new List<List<Vector3>>();
            if (covering == null || covering.Count < 3) { result.Add(face); return result; }
            covering = Ordered(covering, faceNormal);
            var inside = face;
            for (int i = 0; i < covering.Count && inside.Count >= 3; i++)
            {
                Vector3 a = covering[i], b = covering[(i + 1) % covering.Count];
                Vector3 outward = Vector3.Cross(b - a, faceNormal).normalized;
                float distance = Vector3.Dot(outward, a);
                var outside = Clip(inside, -outward, -distance);
                if (outside.Count >= 3) result.Add(outside);
                inside = Clip(inside, outward, distance);
            }
            return result;
        }
    }
}
