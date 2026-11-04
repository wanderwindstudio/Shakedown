using System.Collections.Generic;
using UnityEngine;

namespace Shakedown.Assembly
{
    // All placement and doorway decisions use metre-grid data, never renderer bounds.
    public sealed class AssemblyLayout
    {
        public const float Floor = .5f;
        public AssemblyData Data
        {
            get;
            private set;
        }
        public readonly CompartmentDefinition[] definitions;
        public AssemblyLayout(CompartmentDefinition[] definitions)
        {
            this.definitions = definitions;
            Reset();
        }
        public void Reset()
        {
            Data = new AssemblyData();
            Data.compartments.Add(new PlacedCompartment
            {
                id = 0, type = "Cockpit"
            });
        }
        public void Replace(AssemblyData data) => Data = data;
        public CompartmentDefinition Definition(PlacedCompartment c) => System.Array.Find(definitions, d => d.id == c.type);
        public PlacedCompartment Find(int id) => Data.compartments.Find(c => c.id == id);
        public Vector2 Size(PlacedCompartment c)
        {
            var d = Definition(c);
            return c.rotation%2 == 0?new Vector2(d.width+1, d.length+1):new Vector2(d.length+1, d.width+1);
        }
        public Rect Footprint(PlacedCompartment c)
        {
            var s = Size(c);
            return new Rect(c.x, c.z, s.x, s.y);
        }
        public Vector3 Centre(PlacedCompartment c)
        {
            var r = Footprint(c);
            return new Vector3(r.center.x, Floor, r.center.y);
        }
        public Quaternion Rotation(PlacedCompartment c) => Quaternion.Euler(0, c.rotation*90, 0);
        public Vector3 Normal(PlacedCompartment c, Wall wall) => Rotation(c)*(wall == Wall.Front?Vector3.forward:wall == Wall.Back?Vector3.back:wall == Wall.Left?Vector3.left:Vector3.right);
        public int Columns(PlacedCompartment c, Wall wall) => wall == Wall.Front || wall == Wall.Back?Definition(c).width:Definition(c).length;
        public Vector3 Slot(PlacedCompartment c, Wall wall, int column)
        {
            var d = Definition(c);
            float x = 0, z = 0;
            if (wall == Wall.Front)
            {
                x = -d.width/2f+column+.5f;
                z = d.length/2f;
            }
            if (wall == Wall.Back)
            {
                x = d.width/2f-column-.5f;
                z = -d.length/2f;
            }
            if (wall == Wall.Left)
            {
                x = -d.width/2f;
                z = -d.length/2f+column+.5f;
            }
            if (wall == Wall.Right)
            {
                x = d.width/2f;
                z = d.length/2f-column-.5f;
            }
            return Centre(c)+Rotation(c)*new Vector3(x, 0, z);
        }
        public bool AllowedWall(PlacedCompartment c, Wall wall) => !Definition(c).cockpit || wall == Wall.Back;
        public bool Touch(PlacedCompartment a, PlacedCompartment b, out Wall wa, out Wall wb)
        {
            foreach (Wall aa in System.Enum.GetValues(typeof(Wall))) foreach (Wall bb in System.Enum.GetValues(typeof(Wall)))
            {
                Vector3 n = Normal(a, aa);
                if (Vector3.Dot(n, Normal(b, bb))>-.99f)continue;
                Vector3 pa = Slot(a, aa, 0), pb = Slot(b, bb, 0);
                if (Mathf.Abs(Vector3.Dot(pb-pa, n)-1)>.01f)continue;
                var ra = Footprint(a);
                var rb = Footprint(b);
                float overlap = Mathf.Abs(n.x)>.5f?Mathf.Min(ra.yMax, rb.yMax)-Mathf.Max(ra.yMin, rb.yMin):Mathf.Min(ra.xMax, rb.xMax)-Mathf.Max(ra.xMin, rb.xMin);
                // At least one metre of shared footprint edge; a corner touch alone is not a connection.
                if (overlap >= .99f)
                {
                    wa = aa;
                    wb = bb;
                    return true;
                }
            }
            wa = wb = Wall.Front;
            return false;
        }
        public bool CanPlace(PlacedCompartment candidate, out string reason)
        {
            if (candidate.rotation<0 || candidate.rotation>3 || Definition(candidate) == null)
            {
                reason = "Invalid compartment.";
                return false;
            }
            bool touching = false;
            var r = Footprint(candidate);
            foreach (var other in Data.compartments)
            {
                var q = Footprint(other);
                if (r.xMin<q.xMax-.01f && r.xMax>q.xMin+.01f && r.yMin<q.yMax-.01f && r.yMax>q.yMin+.01f)
                {
                    reason = "Footprints overlap.";
                    return false;
                }
                if (Touch(candidate, other, out var a, out var b))
                {
                    if (!AllowedWall(candidate, a) || !AllowedWall(other, b))
                    {
                        reason = "Only the cockpit rear can connect.";
                        return false;
                    }
                    foreach (var entrance in Data.doors) if (entrance.b<0 && entrance.a == other.id && entrance.wallA == b)
                    {
                        reason = "Remove the entrance before building across it.";
                        return false;
                    }
                    touching = true;
                }
            }
            reason = touching?"":"Touch an existing compartment.";
            return touching;
        }
        public bool CanRemove(int id, out string reason)
        {
            if (id == 0)
            {
                reason = "The cockpit is the ship root.";
                return false;
            }
            var seen = new HashSet<int>
            {
                0
            };
            var queue = new Queue<int>();
            queue.Enqueue(0);
            while (queue.Count>0)
            {
                var current = Find(queue.Dequeue());
                foreach (var next in Data.compartments) if (next.id != id && !seen.Contains(next.id) && Touch(current, next, out _, out _))
                {
                    seen.Add(next.id);
                    queue.Enqueue(next.id);
                }
            }
            bool valid = seen.Count == Data.compartments.Count-1;
            reason = valid?"":"Removal would cut compartments off from the cockpit.";
            return valid;
        }
        public bool TryDoor(int compartment, Wall wall, int column, out DoorData door, out string reason)
        {
            door = null;
            var a = Find(compartment);
            if (!AllowedWall(a, wall) || column<0 || column >= Columns(a, wall))
            {
                reason = "This wall cannot have a doorway.";
                return false;
            }
            Vector3 point = Slot(a, wall, column), normal = Normal(a, wall);
            foreach (var b in Data.compartments)
            {
                if (b.id == a.id || !Touch(a, b, out var aw, out var bw) || aw != wall)continue;
                for (int c = 0;c<Columns(b, bw);c++) if (Vector3.Distance(Slot(b, bw, c), point+normal)<.01f)
                {
                    if (!DoorHeightFits(a, wall, column) || !DoorHeightFits(b, bw, c))
                    {
                        reason = "The upper chamfer leaves too little door height here.";
                        return false;
                    }
                    door = new DoorData
                    {
                        a = a.id, b = b.id, wallA = wall, wallB = bw, columnA = column, columnB = c
                    };
                    reason = "";
                    return true;
                }
            }
            // A touching neighbour without a matching column is not an outside wall.
            foreach (var b in Data.compartments) if (b.id != a.id && Touch(a, b, out var aw, out _) && aw == wall)
            {
                Vector3 delta = point+normal-Centre(b);
                var local = Quaternion.Inverse(Rotation(b))*delta;
                var d = Definition(b);
                if (Mathf.Abs(local.x) <= d.width/2f+.01f && Mathf.Abs(local.z) <= d.length/2f+.01f)
                {
                    reason = "No matching opposite wall slot.";
                    return false;
                }
            }
            if (Data.doors.Exists(d => d.b<0))
            {
                reason = "The ship already has an entrance.";
                return false;
            }
            if (!DoorHeightFits(a, wall, column))
            {
                reason = "Not enough clearance for a 2 m doorway.";
                return false;
            }
            door = new DoorData
            {
                a = a.id, b = -1, wallA = wall, columnA = column
            };
            reason = "";
            return true;
        }
        bool DoorHeightFits(PlacedCompartment c, Wall wall, int column)
        {
            var d = Definition(c);
            return d.height >= 2 && (d.height>2 || wall == Wall.Left || wall == Wall.Right || (column>0 && column<d.width-1));
        }
        public bool IsCut(int id, Wall wall, int column, int row) => row<2 && Data.doors.Exists(d => (d.a == id && d.wallA == wall && d.columnA == column) || (d.b == id && d.wallB == wall && d.columnB == column));
        public bool Validate(AssemblyData data, out string reason)
        {
            var previous = Data;
            Data = new AssemblyData();
            bool valid = true;
            reason = "Invalid assembly file.";
            var ids = new HashSet<int>();
            if (data == null || data.formatVersion != 1 || data.compartments == null || data.doors == null)valid = false;
            if (valid)foreach (var c in data.compartments) if (c == null || !ids.Add(c.id) || c.id<0 || Definition(c) == null || c.rotation<0 || c.rotation>3 || Mathf.Abs(c.x)>10000 || Mathf.Abs(c.z)>10000)
            {
                valid = false;
                break;
            }
            if (valid)
            {
                var root = data.compartments.Find(c => c.id == 0);
                if (root == null || root.type != "Cockpit" || root.x != 0 || root.z != 0 || root.rotation != 0)valid = false;
                else Data.compartments.Add(root);
                var pending = new List<PlacedCompartment>(data.compartments);
                pending.Remove(root);
                // A legal removal can change list order relative to the surviving connection path.
                while (valid && pending.Count>0)
                {
                    var next = pending.Find(c => !Definition(c).cockpit && CanPlace(c, out _));
                    if (next == null)
                    {
                        valid = false;
                        break;
                    }
                    Data.compartments.Add(next);
                    pending.Remove(next);
                }
            }
            var doorIds = new HashSet<int>();
            if (valid)foreach (var d in data.doors)
            {
                if (d == null || d.b < -1 || !ids.Contains(d.a) || (d.b >= 0 && !ids.Contains(d.b)) || d.id<0 || !doorIds.Add(d.id) || !System.Enum.IsDefined(typeof(Wall), d.wallA) || !System.Enum.IsDefined(typeof(Wall), d.wallB) || IsCut(d.a, d.wallA, d.columnA, 0) || !TryDoor(d.a, d.wallA, d.columnA, out var expected, out reason) || expected.b != d.b || (d.b >= 0 && (expected.wallB != d.wallB || expected.columnB != d.columnB)))
                {
                    valid = false;
                    break;
                }
                Data.doors.Add(d);
            }
            Data = previous;
            return valid;
        }
    }
}
