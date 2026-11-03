using UnityEngine;
using UnityEngine.InputSystem;

namespace TestPlanet
{
    public sealed class PlanetPlayer : MonoBehaviour, IPlanetFeature
    {
        [SerializeField, Tooltip("Shore spawn in terrain X/Z coordinates; snapped to the real triangle collider.")]
        Vector2 spawnXZ = new Vector2(-155, -130);
        [SerializeField, Tooltip("Walking speed in metres per second.")]
        float walkSpeed = 7;
        [SerializeField, Tooltip("Sprint speed while Shift is held.")]
        float sprintSpeed = 12;
        [SerializeField, Tooltip("Jump height in metres.")]
        float jumpHeight = 1.5f;
        [SerializeField, Tooltip("Downward acceleration in metres per second squared.")]
        float gravity = 22;
        [SerializeField, Tooltip("Mouse sensitivity in degrees per pixel. Mouse delta already represents one frame.")]
        float sensitivity = .11f;
        [SerializeField, Tooltip("Eye height measured from the player's feet.")]
        float eyeHeight = 1.75f;
        [SerializeField, Tooltip("Capsule height.")]
        float bodyHeight = 1.9f;
        [SerializeField, Tooltip("Capsule radius; narrow enough for gaps between boulders.")]
        float bodyRadius = .35f;
        [SerializeField, Range(30, 65), Tooltip("Maximum climbable incline. The crater approach is below this angle.")]
        float slopeLimit = 58;
        [SerializeField, Tooltip("Largest ledge the capsule automatically steps over.")]
        float stepHeight = .45f;
        [SerializeField, Tooltip("Rescue height below the seabed if the player leaves the terrain.")]
        float rescueDepth = -25;
        CharacterController body;
        Camera eyes;
        Vector3 spawn;
        Quaternion spawnRotation;
        float verticalSpeed, pitch;
        public bool ReviewControl { get; set; }

        public Vector3 Position => body.transform.position;
        public Vector3 Spawn => spawn;
        public Camera Eyes => eyes;
        public bool Grounded => body.isGrounded;
        public int Respawns { get; private set; }

        public void Generate(PlanetWorld world)
        {
            var root = new GameObject("Explorer · CharacterController");
            root.transform.SetParent(transform);
            body = root.AddComponent<CharacterController>();
            body.height = bodyHeight;
            body.radius = bodyRadius;
            body.center = Vector3.up * (bodyHeight / 2);
            body.slopeLimit = slopeLimit;
            body.stepOffset = stepHeight;
            body.minMoveDistance = 0;
            Physics.SyncTransforms();
            if (Physics.Raycast(new Vector3(spawnXZ.x, 250, spawnXZ.y), Vector3.down, out RaycastHit hit, 400))
                spawn = hit.point + Vector3.up * .15f;
            else
                spawn = new Vector3(spawnXZ.x, world.Terrain.Height(spawnXZ.x, spawnXZ.y) + .2f, spawnXZ.y);
            Vector3 facing = new Vector3(world.Terrain.VolcanoCentre.x, spawn.y, world.Terrain.VolcanoCentre.y) - spawn;
            spawnRotation = Quaternion.LookRotation(facing);
            Teleport(spawn);
            root.transform.rotation = spawnRotation;
            eyes = Camera.main;
            eyes.transform.SetParent(root.transform, false);
            eyes.transform.localPosition = Vector3.up * eyeHeight;
            pitch = -9;
            eyes.transform.localRotation = Quaternion.Euler(pitch, 0, 0);
            LockCursor(true);
        }

        void Update()
        {
            if (body == null || ReviewControl)
                return;
            var keyboard = Keyboard.current;
            var mouse = Mouse.current;
            if (keyboard != null && keyboard.escapeKey.wasPressedThisFrame)
                LockCursor(false);
            if (mouse != null && mouse.leftButton.wasPressedThisFrame)
                LockCursor(true);
            if (Cursor.lockState != CursorLockMode.Locked)
            {
                // Releasing the mouse stops walking, but gravity must still bring a jumping player back down.
                Move(Vector3.zero, false, false, Time.deltaTime);
                return;
            }

            Vector2 move = Vector2.zero;
            if (keyboard != null)
            {
                move.x = (keyboard.dKey.isPressed ? 1 : 0) - (keyboard.aKey.isPressed ? 1 : 0);
                move.y = (keyboard.wKey.isPressed ? 1 : 0) - (keyboard.sKey.isPressed ? 1 : 0);
            }

            if (mouse != null)
            {
                Vector2 look = mouse.delta.ReadValue() * sensitivity;
                body.transform.Rotate(0, look.x, 0);
                pitch = Mathf.Clamp(pitch - look.y, -85, 85);
                eyes.transform.localRotation = Quaternion.Euler(pitch, 0, 0);
            }

            Vector3 direction = body.transform.TransformDirection(new Vector3(move.x, 0, move.y));
            Move(direction, keyboard != null && keyboard.leftShiftKey.isPressed, keyboard != null && keyboard.spaceKey.wasPressedThisFrame, Time.deltaTime);
        }

        public void Move(Vector3 direction, bool sprint, bool jump, float deltaTime)
        {
            // The same movement method is used by keyboard play and the automated climb review.
            if (body.isGrounded && verticalSpeed < 0)
                verticalSpeed = -2;
            if (jump && body.isGrounded)
                verticalSpeed = Mathf.Sqrt(2 * gravity * jumpHeight);
            verticalSpeed -= gravity * deltaTime;
            body.Move((Vector3.ClampMagnitude(direction, 1) * (sprint ? sprintSpeed : walkSpeed) + Vector3.up * verticalSpeed) * deltaTime);
            if (Position.y < rescueDepth)
                Respawn();
        }

        public void Push(Vector3 direction, float distance)
        {
            body.Move(direction * distance);
        }

        public void Teleport(Vector3 position)
        {
            body.enabled = false;
            body.transform.position = position;
            body.enabled = true;
            verticalSpeed = 0;
        }

        public void Respawn()
        {
            Teleport(spawn);
            body.transform.rotation = spawnRotation;
            pitch = -9;
            if (eyes != null)
            {
                eyes.transform.localPosition = Vector3.up * eyeHeight;
                eyes.transform.localRotation = Quaternion.Euler(pitch, 0, 0);
            }

            Respawns++;
        }

        public static void LockCursor(bool locked)
        {
            Cursor.lockState = locked ? CursorLockMode.Locked : CursorLockMode.None;
            Cursor.visible = !locked;
        }

        void OnDestroy()
        {
            LockCursor(false);
        }
    }
}
