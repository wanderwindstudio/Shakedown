using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace Shakedown.Ship
{
    public sealed class FlatMesh
    {
        readonly List<Vector3> vertices = new List<Vector3>();
        readonly List<Vector3> normals = new List<Vector3>();
        readonly List<Color> colours = new List<Color>();
        readonly List<int> triangles = new List<int>();
        public int Count => vertices.Count;
        public void Triangle(Vector3 a, Vector3 b, Vector3 c, Color colour)
        {
            Vector3 normal = Vector3.Cross(b - a, c - a);
            if (normal.sqrMagnitude < .00000001f) return;
            normal.Normalize();
            int start = vertices.Count;
            vertices.Add(a); vertices.Add(b); vertices.Add(c);
            for (int i = 0; i < 3; i++) { normals.Add(normal); colours.Add(colour); triangles.Add(start + i); }
        }
        public void Polygon(List<Vector3> polygon, Color colour)
        {
            for (int i = 1; i < polygon.Count - 1; i++) Triangle(polygon[0], polygon[i], polygon[i + 1], colour);
        }
        public void Add(Mesh mesh, Matrix4x4 matrix, Color colour)
        {
            if (mesh == null || mesh.vertexCount == 0) return;
            var points = mesh.vertices;
            var indices = mesh.triangles;
            bool mirrored = matrix.determinant < 0;
            for (int i = 0; i < indices.Length; i += 3)
                Triangle(matrix.MultiplyPoint3x4(points[indices[i]]), matrix.MultiplyPoint3x4(points[indices[i + (mirrored ? 2 : 1)]]), matrix.MultiplyPoint3x4(points[indices[i + (mirrored ? 1 : 2)]]), colour);
        }
        public Mesh Create(string name)
        {
            var mesh = new Mesh { name = name, indexFormat = IndexFormat.UInt32 };
            mesh.SetVertices(vertices); mesh.SetNormals(normals); mesh.SetColors(colours); mesh.SetTriangles(triangles, 0);
            mesh.RecalculateBounds();
            return mesh;
        }
    }
}
