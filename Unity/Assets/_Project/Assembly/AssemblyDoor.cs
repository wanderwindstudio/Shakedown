using UnityEngine;
using Shakedown.Player;

namespace Shakedown.Assembly
{
    public sealed class AssemblyDoor : MonoBehaviour
    {
        public int id;
        public Transform leaf;
        public FirstPersonController player;
        float openness;
        void Update()
        {
            Vector3 offset = player.Position-transform.position;
            bool nearby = new Vector2(offset.x, offset.z).magnitude<1.5f && Mathf.Abs(offset.y)<2;
            openness = Mathf.MoveTowards(openness, nearby?1:0, Time.deltaTime*6);
            leaf.localPosition = new Vector3(openness*1.06f, 1, 0);
            leaf.GetComponent<Collider>().enabled = openness<.9f;
        }
    }
}
