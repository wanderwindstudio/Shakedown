using System.Collections.Generic;
using UnityEngine;
using TestPlanet;

namespace Shakedown.Spikes
{
    public static class OrbitSphere
    {
        public struct Triangle
        {
            public int a, b, c;
            public Triangle(int a, int b, int c) { this.a = a; this.b = b; this.c = c; }
        }
        public static void Icosphere(int subdivisions, out List<Vector3> points, out List<Triangle> faces)
        {
            float t = (1 + Mathf.Sqrt(5)) / 2;
            points = new List<Vector3> {
                new Vector3(-1,t,0), new Vector3(1,t,0), new Vector3(-1,-t,0), new Vector3(1,-t,0),
                new Vector3(0,-1,t), new Vector3(0,1,t), new Vector3(0,-1,-t), new Vector3(0,1,-t),
                new Vector3(t,0,-1), new Vector3(t,0,1), new Vector3(-t,0,-1), new Vector3(-t,0,1) };
            for (int i = 0; i < points.Count; i++) points[i] = points[i].normalized;
            int[] indices = {0,11,5, 0,5,1, 0,1,7, 0,7,10, 0,10,11, 1,5,9, 5,11,4, 11,10,2, 10,7,6, 7,1,8, 3,9,4, 3,4,2, 3,2,6, 3,6,8, 3,8,9, 4,9,5, 2,4,11, 6,2,10, 8,6,7, 9,8,1};
            faces = new List<Triangle>();
            for (int i = 0; i < indices.Length; i += 3) faces.Add(new Triangle(indices[i],indices[i+1],indices[i+2]));
            var vertices = points;
            for (int level = 0; level < subdivisions; level++)
            {
                var midpoints = new Dictionary<long,int>();
                int Midpoint(int a, int b)
                {
                    long key = ((long)Mathf.Min(a,b) << 32) | (uint)Mathf.Max(a,b);
                    if (midpoints.TryGetValue(key, out int found)) return found;
                    int index = vertices.Count;
                    vertices.Add((vertices[a]+vertices[b]).normalized); midpoints.Add(key,index); return index;
                }
                var next = new List<Triangle>(faces.Count*4);
                foreach (var f in faces)
                {
                    int a = Midpoint(f.a,f.b), b = Midpoint(f.b,f.c), c = Midpoint(f.c,f.a);
                    next.Add(new Triangle(f.a,a,c)); next.Add(new Triangle(f.b,b,a));
                    next.Add(new Triangle(f.c,c,b)); next.Add(new Triangle(a,b,c));
                }
                faces = next;
            }
        }
        public static float Noise(Vector3 p)
        {
            return (Mathf.PerlinNoise(p.x,p.y)+Mathf.PerlinNoise(p.y,p.z)+Mathf.PerlinNoise(p.z,p.x))/3;
        }
    }
}
