using System;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Shakedown.Ship
{
    public sealed class ShipBuilder : MonoBehaviour
    {
        public PartCatalog catalog;
        public Material stripeMaterial, ghostMaterial, outlineMaterial;
        public FirstPersonController player;
        public Camera walkCamera, droneCamera;
        public ConstructionDrone drone;
        public ShipGrid Grid { get; private set; }
        ShipVisuals visuals;
        readonly ShipHistory history = new ShipHistory();
        GameObject ghost, outline;
        int selected, rotation;
        bool building;
        string message = "B opens the construction drone.";
        float messageUntil = 6;
        bool hasTarget, valid;
        Vector3Int aimed, target;
        string refusal;
        public bool Building => building;
        public string SelectedName => catalog.parts[selected].displayName;
        public string Message => Time.time < messageUntil ? message : "";

        public void Initialize()
        {
            Grid = new ShipGrid();
            Grid.Set(Vector3Int.zero, new ShipCell(catalog.parts[0].id));
            visuals = gameObject.AddComponent<ShipVisuals>();
            visuals.Initialize(Grid, catalog, stripeMaterial);
            ghost = CreatePreview("Placement ghost", ghostMaterial);
            var stripe = GameObject.CreatePrimitive(PrimitiveType.Cube);
            Destroy(stripe.GetComponent<Collider>());
            stripe.transform.SetParent(ghost.transform, false);
            stripe.transform.localPosition = new Vector3(.04f, .26f, .504f);
            stripe.transform.localScale = new Vector3(.68f, .24f, .006f);
            stripe.GetComponent<Renderer>().sharedMaterial = stripeMaterial;
            outline = CreateOutline();
            ghost.SetActive(false); outline.SetActive(false);
        }
        GameObject CreatePreview(string name, Material material)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            Destroy(go.GetComponent<Collider>());
            go.GetComponent<Renderer>().sharedMaterial = material;
            go.GetComponent<Renderer>().shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            go.transform.localScale = Vector3.one * (ShipGrid.CellSize * 1.002f);
            return go;
        }
        GameObject CreateOutline()
        {
            var root = new GameObject("Aimed block outline");
            for (int axis = 0; axis < 3; axis++)
                for (int a = -1; a <= 1; a += 2)
                    for (int b = -1; b <= 1; b += 2)
                    {
                        var line = GameObject.CreatePrimitive(PrimitiveType.Cube);
                        Destroy(line.GetComponent<Collider>());
                        line.transform.SetParent(root.transform, false);
                        var size = Vector3.one * .035f; size[axis] = 2.54f;
                        var p = Vector3.zero; p[(axis + 1) % 3] = a * 1.27f; p[(axis + 2) % 3] = b * 1.27f;
                        line.transform.localScale = size; line.transform.localPosition = p;
                        line.GetComponent<Renderer>().sharedMaterial = outlineMaterial;
                    }
            return root;
        }
        void Update()
        {
            var k = Keyboard.current; var m = Mouse.current;
            if (k == null || m == null) return;
            bool captured = Cursor.lockState == CursorLockMode.Locked;
            if (k.escapeKey.wasPressedThisFrame) FirstPersonController.LockCursor(false);
            if (!captured && m.leftButton.wasPressedThisFrame) FirstPersonController.LockCursor(true);
            if (k.bKey.wasPressedThisFrame) ToggleMode();
            if (k.f5Key.wasPressedThisFrame) Save();
            if (k.f9Key.wasPressedThisFrame) Load();
            if (!building || !captured) { ghost.SetActive(false); outline.SetActive(false); return; }
            if (k.digit1Key.wasPressedThisFrame) selected = 0;
            if (k.digit2Key.wasPressedThisFrame) selected = 1;
            if (k.rKey.wasPressedThisFrame) rotation = CubeRotations.Turn(rotation, Vector3.up);
            if (k.tKey.wasPressedThisFrame) rotation = CubeRotations.Turn(rotation, Vector3.right);
            if (k.gKey.wasPressedThisFrame) rotation = CubeRotations.Turn(rotation, Vector3.forward);
            if (k.zKey.wasPressedThisFrame) Say(history.Undo() ? "Undone." : "Nothing to undo.");
            if (k.yKey.wasPressedThisFrame) Say(history.Redo() ? "Redone." : "Nothing to redo.");
            Aim();
            if (m.leftButton.wasPressedThisFrame && hasTarget)
            {
                if (valid) history.Execute(new CellCommand(Grid, target, new ShipCell(catalog.parts[selected].id, rotation), visuals.Changed));
                else Say(refusal);
            }
            if (m.rightButton.wasPressedThisFrame && hasTarget)
            {
                if (Grid.CanRemove(aimed, out var reason)) history.Execute(new CellCommand(Grid, aimed, null, visuals.Changed));
                else Say(reason);
            }
        }
        void Aim()
        {
            hasTarget = Physics.Raycast(droneCamera.ViewportPointToRay(new Vector3(.5f, .5f)), out var hit, 30)
                && hit.collider.GetComponent<ShipChunk>() != null;
            ghost.SetActive(hasTarget); outline.SetActive(hasTarget);
            if (!hasTarget) return;
            // Sample just inside/outside the hit face, independent of the combined mesh triangle order.
            aimed = ToCell(hit.point - hit.normal * .01f);
            target = ToCell(hit.point + hit.normal * .01f);
            valid = Grid.CanPlace(target, out refusal);
            // Below-pad cells remain addressable in the grid, but cannot be built into the landing pad.
            if (target.y < 0) { valid = false; refusal = "The landing pad blocks this cell."; }
            outline.transform.position = ShipVisuals.Centre(aimed);
            ghost.transform.SetPositionAndRotation(ShipVisuals.Centre(target), CubeRotations.Get(rotation));
            ghostMaterial.color = valid ? new Color(.2f, 1, .45f, .4f) : new Color(1, .15f, .2f, .4f);
        }
        static Vector3Int ToCell(Vector3 world)
        {
            world -= Vector3.up * (ShipGrid.CellSize / 2);
            return Vector3Int.RoundToInt(world / ShipGrid.CellSize);
        }
        void ToggleMode()
        {
            building = !building;
            if (building) drone.SetPose(walkCamera.transform);
            player.ReviewControl = building;
            walkCamera.gameObject.SetActive(!building);
            droneCamera.gameObject.SetActive(building);
            FirstPersonController.LockCursor(true);
            Say(building ? "Construction drone active." : "Back at your player body.");
        }
        public void Say(string text) { message = text; messageUntil = Time.time + 4; }
        void Save()
        {
            try { ShipStorage.Save(Grid, "test_ship"); Say("Saved test_ship."); }
            catch (Exception e) { Say("Save failed: " + e.Message); }
        }
        void Load()
        {
            try
            {
                var loaded = ShipStorage.Load("test_ship", catalog);
                Grid = loaded;
                history.Clear();
                visuals.ReplaceGrid(Grid);
                Say("Loaded test_ship.");
            }
            catch (Exception e) { Say("Load failed: " + e.Message); }
        }
        void OnDestroy() { Destroy(ghost); Destroy(outline); }
    }
}
