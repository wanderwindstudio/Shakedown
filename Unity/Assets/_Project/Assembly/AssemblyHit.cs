using UnityEngine;

namespace Shakedown.Assembly
{
    public class AssemblyHit : MonoBehaviour
    {
        public int compartment;
    }
    public sealed class AssemblySlot : AssemblyHit
    {
        public Wall wall;
        public int column, row;
    }
}
