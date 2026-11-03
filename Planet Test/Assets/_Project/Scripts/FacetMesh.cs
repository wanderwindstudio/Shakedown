using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace TestPlanet
{
    /// <summary>Duplicating triangle vertices is deliberate: RecalculateNormals then gives flat faces.</summary>
    public sealed class FacetMesh
    {
        readonly List<Vector3> vertices = new List<Vector3>();
        readonly List<Color> colours = new List<Color>();
        readonly List<int> indices = new List<int>();
        public void Triangle(Vector3 a, Vector3 b, Vector3 c, Color colour)
        {
            // Vertex colours bypass Unity's material colour conversion. Convert artist-friendly sRGB to linear for URP.
            int start = vertices.Count;
            vertices.Add(a);
            vertices.Add(b);
            vertices.Add(c);
            for (int i = 0; i < 3; i++)
            {
                indices.Add(start + i);
                colours.Add(colour.linear);
            }
        }

        public void Quad(Vector3 a, Vector3 b, Vector3 c, Vector3 d, Color colour)
        {
            Triangle(a, b, c, colour);
            Triangle(a, c, d, colour);
        }

        public Mesh Build(string name)
        {
            var mesh = new Mesh{name = name};
            if (vertices.Count > 65535)
                mesh.indexFormat = IndexFormat.UInt32;
            mesh.SetVertices(vertices);
            mesh.SetColors(colours);
            mesh.SetTriangles(indices, 0);
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            return mesh;
        }

        public GameObject Create(string name, Transform parent, Material material)
        {
            var go = new GameObject(name, typeof(MeshFilter), typeof(MeshRenderer));
            go.transform.SetParent(parent, false);
            go.GetComponent<MeshFilter>().sharedMesh = Build(name);
            go.GetComponent<MeshRenderer>().sharedMaterial = material;
            return go;
        }
    }
}
