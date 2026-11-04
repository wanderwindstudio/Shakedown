using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;
using Shakedown.Ship;

namespace Shakedown.Assembly
{
    public sealed class AssemblyBootstrap : MonoBehaviour
    {
        public CompartmentDefinition[] definitions;
        public Material[] palette;
        public Material jointMaterial, doorMaterial, ghostMaterial;
        IEnumerator Start()
        {
            // Reuse the actual M1a yard, player, drone and lighting without editing its builder scripts.
            yield return SceneManager.LoadSceneAsync("Assets/_Project/Ship/Scenes/ShipYard.unity", LoadSceneMode.Additive);
            var old = FindFirstObjectByType<ShipBuilder>();
            var builder = gameObject.AddComponent<AssemblyBuilder>();
            builder.definitions = definitions;
            builder.palette = palette;
            builder.jointMaterial = jointMaterial;
            builder.doorMaterial = doorMaterial;
            builder.ghostMaterial = new Material(ghostMaterial);
            builder.player = old.player;
            builder.drone = old.drone;
            builder.walkCamera = old.walkCamera;
            builder.droneCamera = old.droneCamera;
            FindFirstObjectByType<ShipYard>().enabled = false;
            old.gameObject.SetActive(false);
            Destroy(old.gameObject);
            builder.Initialize();
        }
    }
}
