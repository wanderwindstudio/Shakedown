using UnityEngine;
using Shakedown.Ship;

namespace TestPlanet
{
    public sealed class PlanetPlayer : FirstPersonController, IPlanetFeature
    {
        [SerializeField, Tooltip("Shore spawn in terrain X/Z coordinates; snapped to the real triangle collider.")]
        Vector2 spawnXZ = new Vector2(-155, -130);

        public void Generate(PlanetWorld world)
        {
            Physics.SyncTransforms();
            Vector3 position;
            if (Physics.Raycast(new Vector3(spawnXZ.x, 250, spawnXZ.y), Vector3.down, out RaycastHit hit, 400))
                position = hit.point + Vector3.up * .15f;
            else
                position = new Vector3(spawnXZ.x, world.Terrain.Height(spawnXZ.x, spawnXZ.y) + .2f, spawnXZ.y);
            Vector3 facing = new Vector3(world.Terrain.VolcanoCentre.x, position.y, world.Terrain.VolcanoCentre.y) - position;
            // Keep the planet root fixed: its other features generate geometry in world coordinates.
            var explorer = new GameObject("Explorer · CharacterController");
            explorer.transform.SetParent(transform);
            InitializeOn(explorer, position, Quaternion.LookRotation(facing), Camera.main);
        }
    }
}
