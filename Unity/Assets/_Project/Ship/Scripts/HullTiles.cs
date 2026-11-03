using System.Collections.Generic;
using UnityEngine;

namespace Shakedown.Ship
{
    public sealed class HullTiles : System.IDisposable
    {
        public readonly Mesh[,] Octants = new Mesh[22,8];
        sealed class Face
        {
            public Vector3 normal;
            public List<Vector3> points;
            public int axis = -1;
            public bool tileBoundary;
        }
        public HullTiles(float chamfer)
        {
            for (int tile = 0; tile < 22; tile++) Generate(tile, HullTileLookup.BasePatterns[tile], Mathf.Clamp(chamfer, 0, 1));
        }
        static Vector3 Axis(int axis) { var v = Vector3.zero; v[axis] = 1; return v; }
        void Generate(int tile, int pattern, float chamfer)
        {
            var solids = new List<Face>[8];
            for (int bit = 0; bit < 8; bit++)
            {
                if ((pattern & (1 << bit)) == 0) continue;
                solids[bit] = Octant(bit);
                Vector3 sign = HullTileLookup.Sign(bit);
                for (int a = 0; a < 3; a++)
                    for (int b = a + 1; b < 3; b++)
                        if ((pattern & (1 << (bit ^ (1 << a)))) == 0 && (pattern & (1 << (bit ^ (1 << b)))) == 0)
                            Cut(solids[bit], -sign[a] * Axis(a) - sign[b] * Axis(b), -chamfer);
                if ((pattern & (1 << (bit ^ 1))) == 0 && (pattern & (1 << (bit ^ 2))) == 0 && (pattern & (1 << (bit ^ 4))) == 0)
                    Cut(solids[bit], -sign, -Mathf.Min(chamfer * 2, 1.25f));
            }
            for (int bit = 0; bit < 8; bit++)
            {
                var mesh = new FlatMesh();
                if (solids[bit] != null)
                    foreach (var face in solids[bit])
                    {
                        if (face.tileBoundary) continue;
                        List<Vector3> cover = null;
                        if (face.axis >= 0)
                        {
                            var neighbour = solids[bit ^ (1 << face.axis)];
                            if (neighbour != null) cover = neighbour.Find(f => f.axis == face.axis && !f.tileBoundary)?.points;
                        }
                        foreach (var polygon in TilePolygons.Subtract(face.points, cover, face.normal)) mesh.Polygon(polygon, Color.white);
                    }
                Octants[tile,bit] = mesh.Create($"HullTile_{tile:D2}_o{bit}");
            }
        }
        static List<Face> Octant(int bit)
        {
            var faces = new List<Face>();
            Vector3 sign = HullTileLookup.Sign(bit);
            for (int axis = 0; axis < 3; axis++)
                for (int side = 0; side < 2; side++)
                {
                    var points = new List<Vector3>();
                    for (int a = 0; a < 2; a++)
                        for (int b = 0; b < 2; b++)
                        {
                            var p = Vector3.zero;
                            p[axis] = side * sign[axis] * 1.25f;
                            p[(axis+1)%3] = a * sign[(axis+1)%3] * 1.25f;
                            p[(axis+2)%3] = b * sign[(axis+2)%3] * 1.25f;
                            points.Add(p);
                        }
                    var normal = Axis(axis) * sign[axis] * (side == 0 ? -1 : 1);
                    faces.Add(new Face { normal = normal, points = TilePolygons.Ordered(points, normal), axis = axis, tileBoundary = side == 1 });
                }
            return faces;
        }
        static void Cut(List<Face> faces, Vector3 normal, float distance)
        {
            if (Mathf.Abs(distance) < .00001f) return;
            var cap = new List<Vector3>();
            foreach (var face in faces)
            {
                face.points = TilePolygons.Clip(face.points, normal, distance);
                foreach (var point in face.points)
                    if (Mathf.Abs(Vector3.Dot(normal, point) - distance) < .0001f) cap.Add(point);
            }
            faces.RemoveAll(f => f.points.Count < 3);
            cap = TilePolygons.Ordered(cap, normal.normalized);
            if (cap.Count >= 3) faces.Add(new Face { normal = normal.normalized, points = cap });
        }
        public void Dispose()
        {
            foreach (var mesh in Octants) Object.Destroy(mesh);
        }
    }
}
