using System.Collections.Generic;
using UnityEngine;

namespace Shakedown.Ship
{
    public readonly struct HullTileCase
    {
        public readonly int tile, symmetry;
        public HullTileCase(int tile, int symmetry) { this.tile = tile; this.symmetry = symmetry; }
    }

    public static class HullTileLookup
    {
        public static readonly Matrix4x4[] Symmetries = MakeSymmetries();
        public static readonly int[] BasePatterns = MakeBasePatterns();
        public static readonly HullTileCase[] Cases = MakeCases();
        public static Vector3 Sign(int bit) => new Vector3((bit & 1) == 0 ? -1 : 1, (bit & 2) == 0 ? -1 : 1, (bit & 4) == 0 ? -1 : 1);
        public static int Bit(Vector3 sign) => (sign.x > 0 ? 1 : 0) + (sign.y > 0 ? 2 : 0) + (sign.z > 0 ? 4 : 0);
        public static Vector3Int CellOffset(int bit) => new Vector3Int((bit & 1) == 0 ? -1 : 0, (bit & 2) == 0 ? -1 : 0, (bit & 4) == 0 ? -1 : 0);
        public static int TransformPattern(int pattern, Matrix4x4 symmetry)
        {
            int result = 0;
            for (int bit = 0; bit < 8; bit++)
                if ((pattern & (1 << bit)) != 0) result |= 1 << Bit(symmetry.MultiplyVector(Sign(bit)));
            return result;
        }
        static Matrix4x4[] MakeSymmetries()
        {
            var result = new List<Matrix4x4>();
            // Column axes, then signs: this order is also documented in the Blender brief.
            int[][] permutations = { new[] {0,1,2}, new[] {0,2,1}, new[] {1,0,2}, new[] {1,2,0}, new[] {2,0,1}, new[] {2,1,0} };
            foreach (var axes in permutations)
                for (int signs = 0; signs < 8; signs++)
                {
                    var matrix = Matrix4x4.identity;
                    for (int column = 0; column < 3; column++)
                    {
                        Vector4 axis = Vector4.zero;
                        axis[axes[column]] = (signs & (1 << column)) == 0 ? 1 : -1;
                        matrix.SetColumn(column, axis);
                    }
                    result.Add(matrix);
                }
            return result.ToArray();
        }
        static int Canonical(int pattern)
        {
            int minimum = pattern;
            foreach (var symmetry in Symmetries) minimum = Mathf.Min(minimum, TransformPattern(pattern, symmetry));
            return minimum;
        }
        static int[] MakeBasePatterns()
        {
            var patterns = new List<int>();
            for (int pattern = 0; pattern < 256; pattern++)
                if (Canonical(pattern) == pattern) patterns.Add(pattern);
            return patterns.ToArray();
        }
        static HullTileCase[] MakeCases()
        {
            var cases = new HullTileCase[256];
            for (int pattern = 0; pattern < 256; pattern++)
            {
                int tile = System.Array.IndexOf(BasePatterns, Canonical(pattern));
                for (int orientation = 0; orientation < Symmetries.Length; orientation++)
                    if (TransformPattern(BasePatterns[tile], Symmetries[orientation]) == pattern)
                    { cases[pattern] = new HullTileCase(tile, orientation); break; }
            }
            return cases;
        }
    }
}
