using System.Collections.Generic;
using UnityEngine;

namespace Shakedown.Ship
{
    public static class CubeRotations
    {
        // This order is part of the save format. Never reorder these axes.
        public static readonly Vector3Int[] Faces = { Vector3Int.right, Vector3Int.left, Vector3Int.up, Vector3Int.down, Vector3Int.forward, Vector3Int.back };
        static readonly List<Quaternion> rotations = Create();
        static List<Quaternion> Create()
        {
            var result = new List<Quaternion>();
            foreach (var forward in new[] { Vector3Int.forward, Vector3Int.back, Vector3Int.right, Vector3Int.left, Vector3Int.up, Vector3Int.down })
                foreach (var up in new[] { Vector3Int.up, Vector3Int.down, Vector3Int.forward, Vector3Int.back, Vector3Int.right, Vector3Int.left })
                    if (Vector3.Dot(forward, up) == 0) result.Add(Quaternion.LookRotation(forward, up));
            return result;
        }
        public static Quaternion Get(int index) => rotations[index];
        public static int Turn(int index, Vector3 axis)
        {
            Quaternion target = Quaternion.AngleAxis(90, axis) * Get(index);
            for (int i = 0; i < rotations.Count; i++)
                if (Quaternion.Angle(target, rotations[i]) < .1f) return i;
            return index;
        }
    }
}
