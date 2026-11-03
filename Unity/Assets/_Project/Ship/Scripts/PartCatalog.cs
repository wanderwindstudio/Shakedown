using UnityEngine;

namespace Shakedown.Ship
{
    [CreateAssetMenu(menuName = "Shakedown/Part catalog")]
    public sealed class PartCatalog : ScriptableObject
    {
        public PartDefinition[] parts;
        public PartDefinition Find(string id)
        {
            foreach (var part in parts)
                if (part != null && part.id == id) return part;
            return null;
        }
    }
}
