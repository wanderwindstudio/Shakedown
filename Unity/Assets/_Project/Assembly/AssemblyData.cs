using System;
using System.Collections.Generic;
using UnityEngine;

namespace Shakedown.Assembly
{
    public enum Wall
    {
        Front, Back, Left, Right
    }
    [Serializable] public sealed class PlacedCompartment
    {
        public int id;
        public string type;
        public int x, z, rotation;
    }
    [Serializable] public sealed class DoorData
    {
        public int id, a, b = -1, columnA, columnB;
        public Wall wallA, wallB;
    }
    [Serializable] public sealed class AssemblyData
    {
        public int formatVersion = 1;
        public List<PlacedCompartment> compartments = new List<PlacedCompartment>();
        public List<DoorData> doors = new List<DoorData>();
        public AssemblyData Copy() => JsonUtility.FromJson<AssemblyData>(JsonUtility.ToJson(this));
    }
}
