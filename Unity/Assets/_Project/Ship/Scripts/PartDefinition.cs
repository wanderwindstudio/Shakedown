using UnityEngine;

namespace Shakedown.Ship
{
    [System.Flags]
    public enum AirtightFaces { None = 0, Right = 1, Left = 2, Up = 4, Down = 8, Front = 16, Back = 32, All = 63 }

    [CreateAssetMenu(menuName = "Shakedown/Part")]
    public sealed class PartDefinition : ScriptableObject
    {
        public string id;
        public string displayName;
        public Vector3Int size = Vector3Int.one;
        public float massKg = 100;
        public bool autoShapes;
        public AirtightFaces airtightFaces = AirtightFaces.All;
        public Mesh visualMesh;
        public Material material;
    }
}
