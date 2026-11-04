using System;
using System.IO;
using UnityEngine;
using UnityEngine.InputSystem;
using Shakedown.Player;
using Shakedown.Ship;

namespace Shakedown.Assembly
{
    public sealed class AssemblyBuilder : MonoBehaviour
    {
        public CompartmentDefinition[] definitions;
        public Material[] palette;
        public Material jointMaterial, doorMaterial, ghostMaterial;
        public FirstPersonController player;
        public Camera walkCamera, droneCamera;
        public ConstructionDrone drone;
        public AssemblyLayout Layout
        {
            get;
            private set;
        }
        public bool Building
        {
            get;
            private set;
        }
        public string Selected => definitions[selected].id;
        public string Message => Time.time<messageUntil?message:"";
        readonly ShipHistory history = new ShipHistory();
        // Reuse M1a.1's physics drop search. There are no legacy block cells in this scene.
        readonly ShipGrid noBlocks = new ShipGrid();
        AssemblyView view;
        GameObject ghost;
        Renderer[] ghostRenderers;
        int selected, rotation, ghostType = -1;
        PlacedCompartment candidate;
        AssemblySlot aimedSlot;
        AssemblyDoor aimedDoor;
        AssemblyHit aimedRoom;
        string message = "B build / drop in here", refusal;
        float messageUntil = 7;
        bool valid;
        static string SavePath => Path.Combine(Application.persistentDataPath, "assemblies", "test_assembly.json");
        public void Initialize()
        {
            Layout = new AssemblyLayout(definitions);
            var root = new GameObject("Placed compartments and joints");
            view = root.AddComponent<AssemblyView>();
            view.palette = palette;
            view.jointMaterial = jointMaterial;
            view.doorMaterial = doorMaterial;
            view.player = player;
            view.Initialize(Layout);
            // A level deck needs only small steps; the planet controller's 45 cm step lift hits 2 m headers.
            player.GetComponent<CharacterController>().stepOffset = .08f;
            player.Teleport(new Vector3(2, .15f, -6));
        }
        void Apply(AssemblyData data)
        {
            Layout.Replace(data);
            view.Rebuild();
        }
        void Change(Action<AssemblyData> edit)
        {
            var before = Layout.Data.Copy();
            var after = before.Copy();
            edit(after);
            history.Execute(new AssemblyCommand(before, after, Apply));
        }
        void Update()
        {
            if (Layout == null)return;
            var k = Keyboard.current;
            var m = Mouse.current;
            if (k == null || m == null)return;
            bool captured = Cursor.lockState == CursorLockMode.Locked;
            if (k.escapeKey.wasPressedThisFrame)FirstPersonController.LockCursor(false);
            if (!captured && m.leftButton.wasPressedThisFrame)FirstPersonController.LockCursor(true);
            if (k.bKey.wasPressedThisFrame)ToggleMode();
            if (k.f5Key.wasPressedThisFrame)Save();
            if (k.f9Key.wasPressedThisFrame)Load();
            if (!Building || !captured)
            {
                if (ghost != null)ghost.SetActive(false);
                return;
            }
            for (int i = 0;i<6;i++)if (k[(Key)((int)Key.Digit1+i)].wasPressedThisFrame)selected = i;
            if (k.rKey.wasPressedThisFrame)rotation = (rotation+1)%4;
            if (k.zKey.wasPressedThisFrame)Say(history.Undo()?"Undone.":"Nothing to undo.");
            if (k.yKey.wasPressedThisFrame)Say(history.Redo()?"Redone.":"Nothing to redo.");
            Aim();
            if (k.fKey.wasPressedThisFrame)ToggleDoor();
            if (m.leftButton.wasPressedThisFrame && candidate != null)
            {
                if (valid)
                {
                    var placed = candidate;
                    Change(d => d.compartments.Add(placed));
                    Say("Placed "+Selected+".");
                }
                else Say(refusal);
            }
            if (m.rightButton.wasPressedThisFrame && aimedRoom != null)
            {
                int id = aimedRoom.compartment;
                if (Layout.CanRemove(id, out var reason))Change(d =>
                {
                    d.compartments.RemoveAll(c => c.id == id);d.doors.RemoveAll(door => door.a == id || door.b == id);
                });
                else Say(reason);
            }
        }
        void Aim()
        {
            aimedRoom = null;
            aimedSlot = null;
            aimedDoor = null;
            candidate = null;
            if (!Physics.Raycast(droneCamera.ViewportPointToRay(new Vector3(.5f, .5f)), out var hit, 60))
            {
                if (ghost != null)ghost.SetActive(false);
                return;
            }
            aimedDoor = hit.collider.GetComponentInParent<AssemblyDoor>();
            aimedSlot = hit.collider.GetComponentInParent<AssemblySlot>();
            aimedRoom = hit.collider.GetComponentInParent<AssemblyHit>();
            if (aimedRoom == null)
            {
                if (ghost != null)ghost.SetActive(false);
                return;
            }
            var target = Layout.Find(aimedRoom.compartment);
            Wall wall = Wall.Back;
            if (aimedSlot != null)wall = aimedSlot.wall;
            else
            {
                Vector3 direction = hit.point-Layout.Centre(target);
                direction.y = 0;
                float closest = -999;
                foreach (Wall w in Enum.GetValues(typeof(Wall)))
                {
                    float dot = Vector3.Dot(Layout.Normal(target, w), direction.normalized);
                    if (dot>closest)
                    {
                        closest = dot;
                        wall = w;
                    }
                }
            }
            candidate = new PlacedCompartment
            {
                id = NextRoomId(), type = Selected, rotation = rotation
            };
            var size = Layout.Size(candidate);
            var rect = Layout.Footprint(target);
            var normal = Layout.Normal(target, wall);
            if (Mathf.Abs(normal.x)>.5f)
            {
                candidate.x = Mathf.RoundToInt(normal.x>0?rect.xMax:rect.xMin-size.x);
                candidate.z = Mathf.RoundToInt(hit.point.z-size.y/2);
            }
            else
            {
                candidate.z = Mathf.RoundToInt(normal.z>0?rect.yMax:rect.yMin-size.y);
                candidate.x = Mathf.RoundToInt(hit.point.x-size.x/2);
            }
            valid = Layout.AllowedWall(target, wall) && Layout.CanPlace(candidate, out refusal);
            if (!Layout.AllowedWall(target, wall))refusal = "Only the cockpit rear can connect.";
            if (ghost == null || ghostType != selected)
            {
                if (ghost != null)Destroy(ghost);
                ghost = view.Model(candidate, transform, true);
                ghostType = selected;
                ghostRenderers = ghost.GetComponentsInChildren<Renderer>();
                foreach (var renderer in ghostRenderers)
                {
                    if (renderer.gameObject.name.StartsWith("COL_"))
                    {
                        renderer.enabled = false;
                        continue;
                    }
                    var materials = new Material[renderer.sharedMaterials.Length];
                    for (int i = 0;i<materials.Length;i++)materials[i] = ghostMaterial;
                    renderer.sharedMaterials = materials;
                }
            }
            ghost.SetActive(true);
            ghost.transform.SetPositionAndRotation(Layout.Centre(candidate), Layout.Rotation(candidate));
            ghostMaterial.color = valid?new Color(.2f, .9f, .4f, .25f):new Color(1, .15f, .12f, .25f);
        }
        int NextRoomId()
        {
            int id = 0;
            foreach (var c in Layout.Data.compartments)id = Mathf.Max(id, c.id+1);
            return id;
        }
        void ToggleDoor()
        {
            DoorData existing = null;
            if (aimedDoor != null)existing = Layout.Data.doors.Find(d => d.id == aimedDoor.id);
            else if (aimedSlot != null)existing = Layout.Data.doors.Find(d => (d.a == aimedSlot.compartment && d.wallA == aimedSlot.wall && d.columnA == aimedSlot.column) || (d.b == aimedSlot.compartment && d.wallB == aimedSlot.wall && d.columnB == aimedSlot.column));
            if (existing != null)
            {
                Change(d => d.doors.RemoveAll(door => door.id == existing.id));
                Say("Door removed; wall slots restored.");
                return;
            }
            if (aimedSlot == null || aimedSlot.row>1)
            {
                Say("Aim at a wall slot in the bottom two rows.");
                return;
            }
            if (!Layout.TryDoor(aimedSlot.compartment, aimedSlot.wall, aimedSlot.column, out var door, out var reason))
            {
                Say(reason);
                return;
            }
            int next = 0;
            foreach (var d in Layout.Data.doors)next = Mathf.Max(next, d.id+1);
            door.id = next;
            Change(d => d.doors.Add(door));
            Say(door.b<0?"Entrance and ramp added.":"Connected doorway added.");
        }
        void ToggleMode()
        {
            Building = !Building;
            if (Building)drone.SetPose(walkCamera.transform);
            else if (ShipDropIn.TryFindPosition(drone.transform.position, player, noBlocks, null, out var feet))
            {
                player.SetStandingPose(feet, drone.transform.eulerAngles.y);
                Say("Dropped in here.");
            }
            else Say("No room to stand here.");
            player.InputLocked = Building;
            walkCamera.gameObject.SetActive(!Building);
            droneCamera.gameObject.SetActive(Building);
            FirstPersonController.LockCursor(true);
        }
        public void Say(string value)
        {
            message = value;
            messageUntil = Time.time+4;
        }
        void Save()
        {
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(SavePath));
                File.WriteAllText(SavePath+".tmp", JsonUtility.ToJson(Layout.Data, true));
                if (File.Exists(SavePath))File.Replace(SavePath+".tmp", SavePath, null);
                else File.Move(SavePath+".tmp", SavePath);
                Say("Saved test_assembly.");
            }
            catch (Exception e)
            {
                Say("Save failed: "+e.Message);
            }
        }
        void Load()
        {
            try
            {
                var data = JsonUtility.FromJson<AssemblyData>(File.ReadAllText(SavePath));
                if (!Layout.Validate(data, out var reason))throw new InvalidDataException(reason);
                Apply(data);
                history.Clear();
                Say("Loaded test_assembly.");
            }
            catch (Exception e)
            {
                Say("Load failed: "+e.Message);
            }
        }
        void OnGUI()
        {
            if (Layout == null)return;
            GUI.color = new Color(.07f, .07f, .1f, .86f);
            GUI.DrawTexture(new Rect(15, 15, 700, 145), Texture2D.whiteTexture);
            GUI.color = new Color(.9f, .9f, .94f);
            GUI.Label(new Rect(28, 24, 670, 24), "SHAKEDOWN / "+(Building?"ASSEMBLE":"WALK")+" / "+Selected);
            GUI.Label(new Rect(28, 47, 670, 24), Layout.Data.compartments.Count+" compartments · "+Layout.Data.doors.Count+" doors");
            GUI.Label(new Rect(28, 70, 670, 24), "1 Nook · 2 Skylight · 3 Cabin · 4 Bay · 5 Hall · 6 Gangway · R rotate");
            GUI.Label(new Rect(28, 93, 670, 24), "B build/drop in · LMB place · RMB remove · F door · Z/Y undo/redo");
            GUI.Label(new Rect(28, 116, 670, 24), "WASD move · Shift faster · Space jump/up · C down · F5/F9 save/load · Esc cursor");
            GUI.Label(new Rect(28, 177, 1000, 24), Message);
            GUI.Label(new Rect(Screen.width/2f-5, Screen.height/2f-12, 20, 24), "+");
        }
        void OnDestroy()
        {
            if (ghost != null)Destroy(ghost);
            if (view != null)Destroy(view.gameObject);
            Destroy(ghostMaterial);
            FirstPersonController.LockCursor(false);
        }
    }
}
