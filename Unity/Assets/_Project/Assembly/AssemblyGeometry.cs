using UnityEngine;
using Shakedown.Ship;

namespace Shakedown.Assembly
{
    public static class AssemblyGeometry
    {
        public static GameObject Box(string name, Transform parent, Vector3 p, Vector3 size, Material material, bool collision = true)
        {
            var box = GameObject.CreatePrimitive(PrimitiveType.Cube);
            box.name = name;
            box.transform.SetParent(parent, false);
            box.transform.localPosition = p;
            box.transform.localScale = size;
            box.GetComponent<Renderer>().sharedMaterial = material;
            if (!collision)
            {
                box.GetComponent<Collider>().enabled = false;
                Object.Destroy(box.GetComponent<Collider>());
            }
            return box;
        }
        public static GameObject Mesh(string name, Transform parent, Mesh mesh, Material material, bool collision = false)
        {
            var root = new GameObject(name);
            root.transform.SetParent(parent, false);
            root.AddComponent<MeshFilter>().sharedMesh = mesh;
            root.AddComponent<MeshRenderer>().sharedMaterial = material;
            if (collision)root.AddComponent<MeshCollider>().sharedMesh = mesh;
            return root;
        }
        public static Mesh Collar(float width, float height, float length)
        {
            var mesh = new FlatMesh();
            Vector2[] Ring(float w, float h, float bottom)
            {
                float c = Mathf.Min(.5f, w/4, h/4);
                return new[]
                {
                    new Vector2(-w/2+c, bottom), new Vector2(w/2-c, bottom), new Vector2(w/2, bottom+c), new Vector2(w/2, bottom+h-c), new Vector2(w/2-c, bottom+h), new Vector2(-w/2+c, bottom+h), new Vector2(-w/2, bottom+h-c), new Vector2(-w/2, bottom+c)
                };
            }
            var inner = Ring(width, height, 0);
            var outer = Ring(width+.7f, height+.7f, -.35f);
            Vector3 P(Vector2 p, float z) => new Vector3(p.x, p.y, z);
            void Quad(Vector3 a, Vector3 b, Vector3 c, Vector3 d)
            {
                mesh.Triangle(a, c, b, Color.white);
                mesh.Triangle(a, d, c, Color.white);
            }
            for (int i = 0;i<8;i++)
            {
                int j = (i+1)%8;
                Quad(P(outer[i], 0), P(outer[i], length), P(outer[j], length), P(outer[j], 0));
                Quad(P(inner[j], 0), P(inner[j], length), P(inner[i], length), P(inner[i], 0));
                Quad(P(outer[j], 0), P(inner[j], 0), P(inner[i], 0), P(outer[i], 0));
                Quad(P(outer[i], length), P(inner[i], length), P(inner[j], length), P(outer[j], length));
            }
            return mesh.Create("Octagonal joint collar");
        }
        public static Mesh Ramp(float height, float length)
        {
            var m = new FlatMesh();
            Vector3 a = new Vector3(-.65f, 0, 0), b = new Vector3(.65f, 0, 0), c = new Vector3(-.65f, -height, length), d = new Vector3(.65f, -height, length), e = new Vector3(-.65f, -height, 0), f = new Vector3(.65f, -height, 0);
            void Q(Vector3 x, Vector3 y, Vector3 z, Vector3 w)
            {
                m.Triangle(x, y, z, Color.white);
                m.Triangle(x, z, w, Color.white);
            }
            Q(a, c, d, b);
            Q(e, f, d, c);
            Q(a, b, f, e);
            m.Triangle(a, e, c, Color.white);
            m.Triangle(b, d, f, Color.white);
            return m.Create("Entrance ramp");
        }
    }
}
