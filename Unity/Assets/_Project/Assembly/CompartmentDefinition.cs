using UnityEngine;

namespace Shakedown.Assembly
{
    [CreateAssetMenu(menuName = "Shakedown/Compartment")] public sealed class CompartmentDefinition : ScriptableObject
    {
        public string id;
        public int height, width, length;
        public GameObject model;
        public bool cockpit;
    }
}
