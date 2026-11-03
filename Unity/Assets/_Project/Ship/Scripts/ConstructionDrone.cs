using UnityEngine;
using UnityEngine.InputSystem;

namespace Shakedown.Ship
{
    public sealed class ConstructionDrone : MonoBehaviour
    {
        float pitch, yaw;
        public void SetPose(Transform source)
        {
            transform.SetPositionAndRotation(source.position, source.rotation);
            pitch = source.eulerAngles.x;
            if (pitch > 180) pitch -= 360;
            yaw = source.eulerAngles.y;
        }
        void Update()
        {
            if (Cursor.lockState != CursorLockMode.Locked) return;
            var k = Keyboard.current;
            var m = Mouse.current;
            if (m != null)
            {
                Vector2 look = m.delta.ReadValue() * .11f;
                yaw += look.x;
                pitch = Mathf.Clamp(pitch - look.y, -85, 85);
                transform.rotation = Quaternion.Euler(pitch, yaw, 0);
            }
            if (k == null) return;
            Vector3 move = transform.forward * ((k.wKey.isPressed ? 1 : 0) - (k.sKey.isPressed ? 1 : 0))
                + transform.right * ((k.dKey.isPressed ? 1 : 0) - (k.aKey.isPressed ? 1 : 0))
                + Vector3.up * ((k.spaceKey.isPressed ? 1 : 0) - (k.cKey.isPressed ? 1 : 0));
            transform.position += Vector3.ClampMagnitude(move, 1) * (k.leftShiftKey.isPressed ? 24 : 8) * Time.deltaTime;
        }
    }
}
