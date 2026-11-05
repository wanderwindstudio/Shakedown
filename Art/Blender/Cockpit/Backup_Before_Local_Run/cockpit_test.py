"""
SHAKEDOWN - Blender look test: Explorer cockpit module
=======================================================

What this script does
---------------------
Builds a complete cockpit room module (8 m long x 4 m wide x 3.5 m tall) out of
simple, flat-shaded low-poly shapes, then (optionally) saves the .blend, exports an
FBX for Unity, and renders three PNG images.

How to use it
-------------
1. Open Blender (4.2 or newer; written and tested with Blender 5.2).
2. File > New > General. (The script CLEARS the scene it runs in!)
3. Switch to the "Scripting" workspace tab, click "New", paste this file, press
   "Run Script" (the play button).
4. Building takes a second or two. Rendering the three images takes a few
   minutes and Blender will look frozen while it renders. If you only want the
   model, set DO_RENDER = False below.

Conventions (the module grid)
-----------------------------
* 1 Blender unit = 1 metre.
* The module box: X from -2 to +2 (width), Y from -4 to +4 (length), Z from 0 to 3.5.
* +Y is the FRONT (nose / canopy). -Y is the REAR (doorway to the rest of the ship).
* Every object's origin (pivot) is (0, 0, 0) = the centre of the module's floor.

How the shapes are made (worth knowing as a Blender learner)
--------------------------------------------------------------
The hull is built like a ship's frame: we define ONE cross-section (a 2D outline
of the hull seen from the front) and copy it along the Y axis at several
"stations", making it smaller towards the nose. Joining neighbouring copies with
quads gives a "loft". The inside walls are the same loft, shrunk inwards by the
wall thickness. Faces we leave out of both lofts become the window openings,
and glass panes fill them.
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix, Euler

# ---------------------------------------------------------------------------
# 0. SETTINGS - change these freely
# ---------------------------------------------------------------------------
OUTPUT_DIR = os.environ.get(
    "COCKPIT_OUT", os.path.expanduser("~/Shakedown/Art/Blender/Cockpit"))
DO_SAVE_BLEND = True      # save cockpit_test.blend
DO_EXPORT_FBX = True      # export cockpit_test.fbx for Unity
DO_RENDER = os.environ.get("COCKPIT_RENDER", "1") == "1"   # render 3 PNGs
RENDER_SAMPLES = int(os.environ.get("COCKPIT_SAMPLES", "64"))
RENDER_SCALE = int(os.environ.get("COCKPIT_RES", "100"))   # % of 1920x1080

WALL = 0.12          # wall thickness (m)
FLOOR_TOP = 0.15     # floor surface height above the pivot
DOOR_W, DOOR_H = 1.4, 2.2


# ---------------------------------------------------------------------------
# 1. CLEAR THE SCENE
# ---------------------------------------------------------------------------
def clear_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)
    for datablocks in (bpy.data.meshes, bpy.data.materials,
                       bpy.data.lights, bpy.data.cameras, bpy.data.worlds):
        for block in list(datablocks):
            datablocks.remove(block)


clear_scene()
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0


def make_collection(name):
    col = bpy.data.collections.new(name)
    scene.collection.children.link(col)
    return col


COL_MODULE = make_collection("Cockpit")   # everything Unity gets
COL_COLLIDERS = make_collection("COL")    # simple box colliders
COL_RENDER = make_collection("RENDER")    # cameras, lights, backdrop (not exported)


# ---------------------------------------------------------------------------
# 2. MATERIALS
#    Colours are written as normal sRGB values (like a colour picker shows)
#    and converted to Blender's internal "linear" colour space.
# ---------------------------------------------------------------------------
def srgb(r, g, b):
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (lin(r), lin(g), lin(b))


def make_mat(name, rgb, rough=0.75, metal=0.0, emit_strength=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True        # always on in Blender 5, needed in 4.x
    except Exception:
        pass
    col = srgb(*rgb)
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*col, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit_strength > 0:
        bsdf.inputs["Emission Color"].default_value = (*col, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
        m.use_backface_culling = False
    m.diffuse_color = (*col, alpha)   # colour in Solid viewport mode + FBX
    return m


MAT = {
    "hull":        make_mat("M_Hull_Beige",      (0.78, 0.72, 0.63), rough=0.8),
    "hull_dark":   make_mat("M_Hull_Trim",       (0.52, 0.48, 0.44), rough=0.7),
    "interior":    make_mat("M_Interior_BlueGrey", (0.56, 0.62, 0.67), rough=0.85),
    "int_dark":    make_mat("M_Interior_Dark",   (0.34, 0.38, 0.44), rough=0.7),
    "floor":       make_mat("M_Floor_Slate",     (0.23, 0.25, 0.29), rough=0.9),
    "floor_plate": make_mat("M_Floor_Plate",     (0.29, 0.31, 0.35), rough=0.8),
    "accent":      make_mat("M_Accent_Orange",   (0.90, 0.48, 0.20), rough=0.6),
    "glow":        make_mat("M_Glow_Teal",       (0.40, 0.88, 0.82), emit_strength=4.0),
    "glow_soft":   make_mat("M_Glow_TealDim",    (0.18, 0.45, 0.48), emit_strength=1.2),
    "map":         make_mat("M_Glow_StarMap",    (0.14, 0.40, 0.44), emit_strength=1.6),
    "star":        make_mat("M_Glow_Star",       (1.00, 0.86, 0.62), emit_strength=6.0),
    "metal":       make_mat("M_Metal",           (0.62, 0.62, 0.64), rough=0.4, metal=0.7),
    "glass":       make_mat("M_Canopy_Glass",    (0.62, 0.80, 0.84), rough=0.05, alpha=0.22),
    "collider":    make_mat("M_Collider",        (0.9, 0.2, 0.9), alpha=0.3),
}


# ---------------------------------------------------------------------------
# 3. A SMALL MESH-BUILDING TOOLKIT
#    MeshBuilder collects faces in a "bmesh" (Blender's editable mesh) and
#    turns it into one object at the end. Each object gets a list of material
#    slots; every face says which slot (0, 1, 2...) it uses.
# ---------------------------------------------------------------------------
def rot_matrix(rx=0.0, ry=0.0, rz=0.0):
    """Rotation from angles in degrees."""
    return Euler((math.radians(rx), math.radians(ry), math.radians(rz))).to_matrix().to_4x4()


class MeshBuilder:
    def __init__(self, materials):
        self.bm = bmesh.new()
        self.mats = materials                # list of material keys
    def slot(self, key):
        return self.mats.index(key)

    def face(self, points, mat, want_normal=None):
        verts = [self.bm.verts.new(p) for p in points]
        f = self.bm.faces.new(verts)
        f.material_index = self.slot(mat)
        if want_normal is not None:
            f.normal_update()
            if f.normal.dot(Vector(want_normal)) < 0:
                f.normal_flip()
        return f

    def box(self, mn, mx, mat):
        """Axis-aligned box from min corner to max corner."""
        self.box_m(Vector(((mn[0]+mx[0])/2, (mn[1]+mx[1])/2, (mn[2]+mx[2])/2)),
                   (mx[0]-mn[0], mx[1]-mn[1], mx[2]-mn[2]), mat)

    def box_m(self, center, size, mat, rot=None):
        """Box by centre + size, optionally rotated (a 4x4 rotation matrix)."""
        sx, sy, sz = size[0]/2, size[1]/2, size[2]/2
        corners = [(-sx,-sy,-sz),(sx,-sy,-sz),(sx,sy,-sz),(-sx,sy,-sz),
                   (-sx,-sy,sz),(sx,-sy,sz),(sx,sy,sz),(-sx,sy,sz)]
        M = Matrix.Translation(Vector(center)) @ (rot if rot else Matrix.Identity(4))
        v = [self.bm.verts.new(M @ Vector(c)) for c in corners]
        for idx in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
            f = self.bm.faces.new([v[i] for i in idx])
            f.material_index = self.slot(mat)

    def beam(self, a, b, radius, mat, sides=6):
        """A faceted rod (pipe, handle, mullion) from point a to point b."""
        a, b = Vector(a), Vector(b)
        d = (b - a).normalized()
        u = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))).normalized()
        w = d.cross(u)
        ra, rb = [], []
        for i in range(sides):
            ang = 2 * math.pi * i / sides
            off = (u * math.cos(ang) + w * math.sin(ang)) * radius
            ra.append(self.bm.verts.new(a + off))
            rb.append(self.bm.verts.new(b + off))
        faces = [self.bm.faces.new(ra[::-1]), self.bm.faces.new(rb)]
        for i in range(sides):
            j = (i + 1) % sides
            faces.append(self.bm.faces.new([ra[i], ra[j], rb[j], rb[i]]))
        for f in faces:
            f.material_index = self.slot(mat)
        bmesh.ops.recalc_face_normals(self.bm, faces=faces)

    def prism(self, profile, offset, mat):
        """Take a flat outline (list of 3D points) and extrude it by 'offset'
        into a closed solid - used for consoles, the floor and the rear wall."""
        off = Vector(offset)
        va = [self.bm.verts.new(Vector(p)) for p in profile]
        vb = [self.bm.verts.new(Vector(p) + off) for p in profile]
        faces = [self.bm.faces.new(va), self.bm.faces.new(vb[::-1])]
        n = len(profile)
        for i in range(n):
            j = (i + 1) % n
            faces.append(self.bm.faces.new([va[i], va[j], vb[j], vb[i]]))
        for f in faces:
            f.material_index = self.slot(mat)
        bmesh.ops.recalc_face_normals(self.bm, faces=faces)
        return faces

    def finish(self, name, collection):
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=0.0005)
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        for key in self.mats:
            me.materials.append(MAT[key])
        for p in me.polygons:
            p.use_smooth = False           # flat shading = faceted low-poly look
        ob = bpy.data.objects.new(name, me)
        collection.objects.link(ob)
        return ob


# ---------------------------------------------------------------------------
# 4. THE HULL CROSS-SECTION AND STATIONS
# ---------------------------------------------------------------------------
# Right half of the hull outline seen from the front, (x, z), from the bottom
# up to the roof centre. Each point is a facet corner. Max width 1.95 and roof
# 3.45 leave 5 cm inside the 4 x 3.5 box for exterior trim.
R_HALF = [(1.55, 0.00), (1.83, 0.12), (1.95, 0.42), (1.95, 0.80), (1.95, 1.10),
          (1.95, 1.45), (1.95, 1.80), (1.92, 2.12), (1.88, 2.40), (1.81, 2.66),
          (1.72, 2.88), (1.58, 3.06), (1.42, 3.22), (1.21, 3.34), (0.98, 3.42),
          (0.66, 3.44), (0.34, 3.45)]
# Full outline, counter-clockwise: up the right side, across the roof, down the
# left side. 34 points -> 34 edges. Edge i joins point i and point i+1;
# the last edge is the flat bottom.
BASE = R_HALF + [(-x, z) for (x, z) in reversed(R_HALF)]
N = len(BASE)
TOP_Z = 3.45

# Stations along the length: (y, width scale, bottom z, roof z).
# Full size for the back 5.5 m, then tapering into the nose.
STATIONS = [(-4.00, 1.00, 0.0, 3.45), (-2.50, 1.00, 0.0, 3.45),
            (-1.00, 1.00, 0.0, 3.45), (0.50, 1.00, 0.0, 3.45),
            (1.50, 1.00, 0.0, 3.45), (2.20, 0.95, 0.0, 3.25),
            (2.60, 0.91, 0.0, 3.10), (3.00, 0.84, 0.0, 2.88),
            (3.35, 0.75, 0.0, 2.62), (3.62, 0.66, 0.0, 2.38),
            (3.80, 0.57, 0.0, 2.18), (3.95, 0.42, 0.3, 1.80)]   # last = nose cap


def station_index(y):
    return min(range(len(STATIONS)), key=lambda k: abs(STATIONS[k][0] - y))


def edge_z(i):
    """Lowest and highest point of base-outline edge i (used to pick edges by height)."""
    za, zb = BASE[i][1], BASE[(i + 1) % N][1]
    return min(za, zb), max(za, zb)


def section(sx, zb, zt):
    """The base outline scaled to a station's width and height."""
    return [(x * sx, zb + z / TOP_Z * (zt - zb)) for (x, z) in BASE]


def inset(poly, d):
    """Shrink a convex outline inwards by distance d (negative d grows it).
    Each edge moves inward along its normal; new corners = where moved edges meet."""
    n = len(poly)
    lines = []
    for i in range(n):
        p, q = Vector(poly[i]), Vector(poly[(i + 1) % n])
        e = (q - p).normalized()
        lines.append((p + Vector((-e.y, e.x)) * d, e))
    out = []
    for i in range(n):
        (p1, e1), (p2, e2) = lines[i - 1], lines[i]
        den = e1.x * e2.y - e1.y * e2.x
        if abs(den) < 1e-6:
            out.append(p2)
        else:
            t = ((p2.x - p1.x) * e2.y - (p2.y - p1.y) * e2.x) / den
            out.append(p1 + e1 * t)
    return [(v.x, v.y) for v in out]


def ring3d(poly2d, y):
    return [Vector((x, y, z)) for (x, z) in poly2d]


outer_rings = [ring3d(section(sx, zb, zt), y) for (y, sx, zb, zt) in STATIONS]
inner_y = [s[0] for s in STATIONS]
inner_y[0] += WALL          # inner walls start behind the rear wall
inner_y[-1] -= WALL         # and stop behind the nose cap
inner_rings = [ring3d(inset(section(sx, zb, zt), WALL), y)
               for (y, sx, zb, zt), y in zip(STATIONS, inner_y)]

# Which loft faces are WINDOWS? A face is (segment s, edge i); segment s runs
# from station s to station s+1. We choose them by position:
#   y 1.5 -> 2.2 : overhead skylight (edges higher than 3.2 m)
#   y 2.2 -> 3.8 : the big wrap-around canopy (edges higher than 1.1 m)
CANOPY = set()
for s in range(len(STATIONS) - 1):
    y0, y1 = STATIONS[s][0], STATIONS[s + 1][0]
    for i in range(N):
        lo_z, hi_z = edge_z(i)
        if y0 >= 1.49 and y1 <= 2.21 and lo_z >= 3.2:
            CANOPY.add((s, i))
        if y0 >= 2.19 and y1 <= 3.81 and lo_z >= 1.1:
            CANOPY.add((s, i))


def ring_center(ring):
    c = Vector((0, 0, 0))
    for p in ring:
        c += p
    return c / len(ring)


def loft(builder, rings, mat, facing_out, skip=()):
    """Join neighbouring rings with quads. facing_out=True for the outside hull,
    False for the inside walls (their faces must point into the room)."""
    grid = [[builder.bm.verts.new(p) for p in ring] for ring in rings]
    for s in range(len(rings) - 1):
        axis = (ring_center(rings[s]) + ring_center(rings[s + 1])) / 2
        for i in range(N):
            if (s, i) in skip:
                continue
            j = (i + 1) % N
            f = builder.bm.faces.new([grid[s][i], grid[s][j], grid[s + 1][j], grid[s + 1][i]])
            f.material_index = builder.slot(mat)
            f.normal_update()
            c = f.calc_center_median()
            out = Vector((0, c.y, axis.z))
            if (f.normal.dot(c - out) > 0) != facing_out:
                f.normal_flip()
    return grid


# ---------------------------------------------------------------------------
# 5. EXTERIOR HULL  (Cockpit_HullExterior)
# ---------------------------------------------------------------------------
hull = MeshBuilder(["hull", "hull_dark"])
outer_grid = loft(hull, outer_rings, "hull", facing_out=True, skip=CANOPY)
# Nose cap: one flat face closing the front.
hull.face(outer_rings[-1], "hull", want_normal=(0, 1, 0))

# Window reveals: where a window face meets a solid face, bridge the gap
# between outer skin and inner skin so you can't see into the wall.
def neighbours(s, i):
    j = (i + 1) % N
    return [((s - 1, i), (s, i), (s, j)),          # edge on station s
            ((s + 1, i), (s + 1, i), (s + 1, j)),  # edge on station s+1
            ((s, (i - 1) % N), (s, i), (s + 1, i)),  # side edge at point i
            ((s, j), (s, j), (s + 1, j))]          # side edge at point j

for (s, i) in CANOPY:
    glass_c = sum([outer_rings[s][i], outer_rings[s + 1][(i + 1) % N]], Vector()) / 2
    for nb, (sa, ia), (sb, ib) in neighbours(s, i):
        if nb in CANOPY:
            continue
        pts = [outer_rings[sa][ia], outer_rings[sb][ib], inner_rings[sb][ib], inner_rings[sa][ia]]
        c = sum(pts, Vector()) / 4
        f = hull.face(pts, "hull_dark")
        f.normal_update()
        # point the reveal towards the window opening
        to_glass = glass_c - c
        if f.normal.dot(to_glass) < 0:
            f.normal_flip()

# Exterior frame bands: slightly raised hoops at some stations (also act as
# the canopy frame seen from outside). 4 cm proud - still inside the box.
def band(builder, y, sx, zb, zt, d_from, d_to, width, mat, skip_edges, facing_out):
    poly = section(sx, zb, zt)
    a = ring3d(inset(poly, d_from), 0)
    b = ring3d(inset(poly, d_to), 0)
    y0, y1 = y - width / 2, y + width / 2
    for i in range(N):
        if i in skip_edges:
            continue
        j = (i + 1) % N
        pa, pb, qa, qb = a[i], a[j], b[i], b[j]
        def at(p, yy):
            return Vector((p.x, yy, p.z))
        builder.face([at(pa, y0), at(pb, y0), at(qb, y0), at(qa, y0)], mat, want_normal=(0, -1, 0))
        builder.face([at(pa, y1), at(pb, y1), at(qb, y1), at(qa, y1)], mat, want_normal=(0, 1, 0))
        top = [at(qa, y0), at(qb, y0), at(qb, y1), at(qa, y1)]
        mid = (qa + qb) / 2
        centre = Vector((0, 0, (zb + zt) / 2))
        n_out = Vector((mid.x, 0, mid.z)) - Vector((0, 0, centre.z))
        builder.face(top, mat, want_normal=n_out if facing_out else -n_out)

# edges that touch the floor get no bands/ribs
BOTTOM_EDGES = {i for i in range(N) if edge_z(i)[1] < 0.45}
for y in (-3.95, -1.0, 1.5, 3.0):
    _, sx, zb, zt = STATIONS[station_index(y)]
    band(hull, y, sx, zb, zt, 0.0, -0.04, 0.10, "hull_dark", BOTTOM_EDGES, facing_out=True)

# Exterior canopy mullions running front-to-back between window panes.
MULLION_Z = (1.80, 2.66, 3.22, 3.44)     # base-outline heights that get a mullion
for (s, i) in CANOPY:
    if (s, (i - 1) % N) in CANOPY and any(abs(BASE[i][1] - z) < 1e-3 for z in MULLION_Z):
        a = outer_rings[s][i]
        b = outer_rings[s + 1][i]
        ax = Vector((0, 0, 1.6))
        pa = a + (Vector((a.x, 0, a.z)) - ax).normalized() * 0.015
        pb = b + (Vector((b.x, 0, b.z)) - ax).normalized() * 0.015
        hull.beam(pa, pb, 0.03, "hull_dark", sides=4)

ob_hull = hull.finish("Cockpit_HullExterior", COL_MODULE)


# ---------------------------------------------------------------------------
# 6. CANOPY GLASS  (Cockpit_Canopy)
#    One pane per window face, halfway through the wall thickness.
# ---------------------------------------------------------------------------
glass = MeshBuilder(["glass"])
for (s, i) in CANOPY:
    j = (i + 1) % N
    pts = [outer_rings[s][i].lerp(inner_rings[s][i], 0.5),
           outer_rings[s][j].lerp(inner_rings[s][j], 0.5),
           outer_rings[s + 1][j].lerp(inner_rings[s + 1][j], 0.5),
           outer_rings[s + 1][i].lerp(inner_rings[s + 1][i], 0.5)]
    c = sum(pts, Vector()) / 4
    glass.face(pts, "glass", want_normal=(c.x, 0.3, c.z - 1.6))
ob_glass = glass.finish("Cockpit_Canopy", COL_MODULE)


# ---------------------------------------------------------------------------
# 7. INTERIOR WALLS  (Cockpit_Interior)
#    Inner loft + structural ribs + the rear wall with the doorway.
# ---------------------------------------------------------------------------
inter = MeshBuilder(["interior", "hull", "accent", "int_dark"])
loft(inter, inner_rings, "interior", facing_out=False, skip=CANOPY)
inter.face(inner_rings[-1], "int_dark", want_normal=(0, -1, 0))   # inside of nose

# Ribs: hoops on the inside every 1.5 m (panel seams / frames). At the canopy
# stations they double as the inner window frames.
for y in (-2.5, -1.0, 0.5, 1.5, 2.2, 3.0):
    _, sx, zb, zt = STATIONS[station_index(y)]
    band(inter, y, sx, zb, zt, WALL - 0.01, WALL + 0.07, 0.08, "int_dark",
         BOTTOM_EDGES, facing_out=False)

# Rear wall with the door socket. We make a solid slab in the shape of the
# hull outline, then cut the doorway out with a Boolean (difference).
slab_bm = MeshBuilder(["interior", "hull", "accent", "int_dark"])
slab_bm.prism([Vector((x, -4.0, z)) for (x, z) in BASE], (0, WALL, 0), "interior")
slab = slab_bm.finish("TMP_RearWall", COL_MODULE)

cutter_bm = MeshBuilder(["interior"])
cutter_bm.box((-DOOR_W / 2, -4.5, FLOOR_TOP), (DOOR_W / 2, -3.5, FLOOR_TOP + DOOR_H), "interior")
cutter = cutter_bm.finish("TMP_DoorCutter", COL_MODULE)

mod = slab.modifiers.new("Door", 'BOOLEAN')
mod.operation = 'DIFFERENCE'
mod.object = cutter
mod.solver = 'EXACT'
depsgraph = bpy.context.evaluated_depsgraph_get()
cut_mesh = bpy.data.meshes.new_from_object(slab.evaluated_get(depsgraph))

# Colour the slab by which way each face points:
# rear face = hull beige, inner face = interior blue-grey, door jambs = orange.
tmp = bmesh.new()
tmp.from_mesh(cut_mesh)
for f in tmp.faces:
    if f.normal.y < -0.5:
        f.material_index = inter.slot("hull")
    elif f.normal.y > 0.5:
        f.material_index = inter.slot("interior")
    else:
        f.material_index = inter.slot("accent")
tmp.to_mesh(cut_mesh)
tmp.free()
inter.bm.from_mesh(cut_mesh)            # append the cut slab to the interior
for ob in (slab, cutter):
    bpy.data.objects.remove(ob, do_unlink=True)
bpy.data.meshes.remove(cut_mesh)

ob_inter = inter.finish("Cockpit_Interior", COL_MODULE)


# ---------------------------------------------------------------------------
# 8. FLOOR  (Cockpit_Floor)
#    A slab following the inside of the hull, plus raised deck plates whose
#    gaps read as panel seams.
# ---------------------------------------------------------------------------
floor = MeshBuilder(["floor", "floor_plate", "accent"])
right = []
for k in range(len(STATIONS) - 1):           # all stations except the nose cap
    y = -4.0 if k == 0 else inner_y[k]
    right.append((inner_rings[k][0].x + 0.06, y))
outline = [Vector((x, y, 0)) for (x, y) in right] + \
          [Vector((-x, y, 0)) for (x, y) in reversed(right)]
floor.prism(outline, (0, 0, FLOOR_TOP), "floor")

# Deck plates: 1.2 m x 0.9 m tiles with 3 cm gaps, 1 cm proud.
xs = [(-1.33, -0.47), (-0.43, 0.43), (0.47, 1.33)]
y = -3.85
while y + 1.2 <= 1.6:
    for (x0, x1) in xs:
        floor.box((x0, y, FLOOR_TOP), (x1, y + 1.17, FLOOR_TOP + 0.01), "floor_plate")
    y += 1.2
# Orange threshold strip at the doorway.
floor.box((-DOOR_W / 2, -4.0, FLOOR_TOP), (DOOR_W / 2, -3.88, FLOOR_TOP + 0.012), "accent")
ob_floor = floor.finish("Cockpit_Floor", COL_MODULE)


# ---------------------------------------------------------------------------
# 9. COMMAND CHAIR  (Cockpit_Chair)
#    Centre of the chair at y = 0.2, facing +Y (the canopy).
# ---------------------------------------------------------------------------
CHAIR_Y = 0.2
chair = MeshBuilder(["int_dark", "accent", "glow", "metal"])
chair.beam((0, CHAIR_Y, FLOOR_TOP), (0, CHAIR_Y, FLOOR_TOP + 0.04), 0.32, "metal", sides=8)  # foot
chair.beam((0, CHAIR_Y, FLOOR_TOP), (0, CHAIR_Y, 0.48), 0.10, "metal", sides=8)             # column
chair.box((-0.30, CHAIR_Y - 0.25, 0.48), (0.30, CHAIR_Y + 0.30, 0.60), "int_dark")          # seat base
chair.box((-0.27, CHAIR_Y - 0.22, 0.60), (0.27, CHAIR_Y + 0.28, 0.68), "accent")            # cushion
# Backrest, tilted back 12 degrees.
tilt = rot_matrix(rx=12)
back_c = Vector((0, CHAIR_Y - 0.30, 1.02))
chair.box_m(back_c, (0.56, 0.10, 0.80), "int_dark", tilt)
chair.box_m(back_c + tilt.to_3x3() @ Vector((0, 0.07, 0.0)), (0.48, 0.05, 0.68), "accent", tilt)
chair.box_m(back_c + tilt.to_3x3() @ Vector((0, 0.02, 0.52)), (0.34, 0.12, 0.20), "int_dark", tilt)
# Armrests with small glowing control pads.
for sgn in (-1, 1):
    x = sgn * 0.36
    chair.box((x - 0.05, CHAIR_Y - 0.20, 0.76), (x + 0.05, CHAIR_Y + 0.28, 0.82), "int_dark")
    chair.beam((x, CHAIR_Y - 0.12, 0.60), (x, CHAIR_Y - 0.12, 0.76), 0.025, "metal")
    chair.beam((x, CHAIR_Y + 0.20, 0.60), (x, CHAIR_Y + 0.20, 0.76), 0.025, "metal")
    chair.box((x - 0.04, CHAIR_Y + 0.12, 0.82), (x + 0.04, CHAIR_Y + 0.26, 0.83), "glow")
    chair.box((-0.02 + x, CHAIR_Y + 0.02, 0.82), (0.02 + x, CHAIR_Y + 0.08, 0.835), "accent")
ob_chair = chair.finish("Cockpit_Chair", COL_MODULE)


# ---------------------------------------------------------------------------
# 10. CONSOLES  (Cockpit_Console)
#     Main console + star map in front of the chair, two side consoles.
# ---------------------------------------------------------------------------
con = MeshBuilder(["int_dark", "interior", "glow", "glow_soft", "star", "accent", "map"])

# Main console: a side profile (y, z) extruded 2 m across the room.
profile_yz = [(1.60, FLOOR_TOP), (2.70, FLOOR_TOP), (2.70, 0.95),
              (2.30, 1.05), (1.75, 0.90), (1.60, 0.80)]
con.prism([Vector((-1.0, y, z)) for (y, z) in profile_yz], (2.0, 0, 0), "int_dark")
# Kick plate in a lighter tone.
con.box((-0.95, 1.57, FLOOR_TOP), (0.95, 1.61, 0.45), "interior")

# Two flat screens lying on the sloped desk top (slope is about 15 degrees).
slope = math.degrees(math.atan2(1.05 - 0.90, 2.30 - 1.75))
desk = rot_matrix(rx=slope)
for x in (-0.62, 0.62):
    con.box_m((x, 2.02, 0.985), (0.46, 0.30, 0.02), "glow_soft", desk)
# Row of buttons in the middle.
for k in range(5):
    con.box_m((-0.16 + k * 0.08, 1.92, 0.955), (0.05, 0.05, 0.02),
              "accent" if k == 2 else "glow", desk)

# Star map: a tilted panel at the back of the console, leaning back 15 degrees.
lean = rot_matrix(rx=-15)
map_c = Vector((0, 2.48, 1.36))
con.box_m(map_c, (1.20, 0.06, 0.52), "int_dark", lean)                   # frame
con.box_m(map_c + lean.to_3x3() @ Vector((0, -0.032, 0)), (1.10, 0.01, 0.44), "map", lean)
con.beam((0, 2.50, 1.0), (0, 2.52, 1.16), 0.05, "int_dark", sides=6)     # stand
# "Stars" and an orbit ring as tiny bright tiles in front of the screen.
import random
rnd = random.Random(7)
for _ in range(26):
    px, pz = rnd.uniform(-0.5, 0.5), rnd.uniform(-0.19, 0.19)
    s = rnd.choice((0.012, 0.018, 0.026))
    con.box_m(map_c + lean.to_3x3() @ Vector((px, -0.040, pz)), (s, 0.004, s), "star", lean)
for k in range(16):
    ang = 2 * math.pi * k / 16
    px, pz = 0.18 + 0.16 * math.cos(ang), 0.02 + 0.10 * math.sin(ang)
    con.box_m(map_c + lean.to_3x3() @ Vector((px, -0.040, pz)), (0.03, 0.004, 0.008), "accent", lean)

# Side consoles along both walls, behind the chair, tops angled into the room.
for sgn in (-1, 1):
    prof = [(1.38, FLOOR_TOP), (1.80, FLOOR_TOP), (1.80, 1.20), (1.38, 0.95)]
    pts = [Vector((sgn * x, -2.70, z)) for (x, z) in prof]
    con.prism(pts, (0, 1.6, 0), "int_dark")
    ang = math.degrees(math.atan2(1.20 - 0.95, 1.80 - 1.38))
    top = rot_matrix(ry=-sgn * ang)
    con.box_m((sgn * 1.59, -1.90, 1.085), (0.36, 1.3, 0.02), "glow_soft", top)
    for k in range(4):
        con.box_m((sgn * 1.52, -2.45 + k * 0.12, 1.06), (0.05, 0.05, 0.02), "accent", top)
    con.box((sgn * 1.36 - 0.02, -2.6, 0.25), (sgn * 1.36 + 0.02, -1.2, 0.8), "interior")
ob_con = con.finish("Cockpit_Console", COL_MODULE)


# ---------------------------------------------------------------------------
# 11. DETAILS  (Cockpit_Details)
#     Ceiling light, handles, vents, pipes, stripes, locker, exterior lights.
# ---------------------------------------------------------------------------
det = MeshBuilder(["metal", "accent", "glow", "int_dark", "interior", "hull_dark"])

# Ceiling light strip, hanging just under the ribs (headroom stays > 3 m).
det.box((-0.14, -3.6, 3.22), (0.14, 1.35, 3.26), "int_dark")      # housing
det.box((-0.10, -3.55, 3.20), (0.10, 1.30, 3.22), "glow")         # light
for y in (-3.3, -1.75, -0.25, 1.1):
    det.box((-0.04, y - 0.04, 3.26), (0.04, y + 0.04, 3.36), "metal")

# Orange door frame on the inside face of the rear wall.
y0, y1 = -3.88, -3.85
det.box((-DOOR_W/2 - 0.12, y0, FLOOR_TOP), (-DOOR_W/2, y1, FLOOR_TOP + DOOR_H + 0.12), "accent")
det.box((DOOR_W/2, y0, FLOOR_TOP), (DOOR_W/2 + 0.12, y1, FLOOR_TOP + DOOR_H + 0.12), "accent")
det.box((-DOOR_W/2, y0, FLOOR_TOP + DOOR_H), (DOOR_W/2, y1, FLOOR_TOP + DOOR_H + 0.12), "accent")

# Grab handles either side of the door and on the walls beside the chair.
for sgn in (-1, 1):
    x = sgn * 1.05
    det.beam((x, -3.80, 0.95), (x, -3.80, 1.65), 0.02, "metal")
    for z in (0.95, 1.65):
        det.box((x - 0.02, -3.85, z - 0.02), (x + 0.02, -3.79, z + 0.02), "metal")
    xw = sgn * 1.76
    det.beam((xw, -0.45, 1.70), (xw, 0.45, 1.70), 0.02, "metal")
    for yy in (-0.45, 0.45):
        det.box((xw - 0.02 if sgn > 0 else xw - 0.05, yy - 0.02, 1.68),
                (xw + 0.05 if sgn > 0 else xw + 0.02, yy + 0.02, 1.72), "metal")

# Vent grilles low on the right wall near the door.
for yc in (-3.35, -2.95):
    det.box((1.80, yc - 0.16, 0.48), (1.83, yc + 0.16, 0.88), "int_dark")
    for k in range(5):
        z = 0.53 + k * 0.075
        det.box((1.775, yc - 0.13, z), (1.80, yc + 0.13, z + 0.03), "metal")

# Storage locker on the left wall near the door: two doors with handles.
det.box((-1.83, -3.80, 0.45), (-1.80, -2.85, 2.10), "int_dark")
for (ya, yb) in ((-3.77, -3.34), (-3.31, -2.88)):
    det.box((-1.80, ya, 0.48), (-1.77, yb, 2.07), "interior")
    yh = yb - 0.06 if ya < -3.5 else ya + 0.06
    det.beam((-1.75, yh, 1.15), (-1.75, yh, 1.40), 0.015, "metal", sides=4)

# Orange accent stripe along both inner walls.
for sgn in (-1, 1):
    det.box((sgn * 1.83 - (0.02 if sgn > 0 else 0), -3.86, 1.36),
            (sgn * 1.83 + (0 if sgn > 0 else 0.02), 1.45, 1.42), "accent")

# Pipes running along the upper wall corners.
corner_i = min(range(N), key=lambda i: abs(BASE[i][1] - 2.88) + abs(BASE[i][0] - 1.72))
cx, cz = inset(section(1, 0, TOP_Z), WALL + 0.06)[corner_i]
for sgn in (-1, 1):
    det.beam((sgn * cx, -3.86, cz), (sgn * cx, 1.45, cz), 0.035, "metal", sides=6)
    det.beam((sgn * (cx - 0.05), -3.86, cz - 0.09), (sgn * (cx - 0.05), 1.45, cz - 0.09),
             0.022, "accent", sides=6)

# Exterior: orange stripe and panels on the hull sides, nav lights, roof sensor.
for sgn in (-1, 1):
    det.box((sgn * 1.955 - (0 if sgn > 0 else 0.02), -3.85, 1.02),
            (sgn * 1.955 + (0.02 if sgn > 0 else 0), 1.45, 1.12), "accent")
    for (ya, yb) in ((-3.4, -2.7), (-2.2, -1.2), (-0.6, 0.2)):
        det.box((sgn * 1.955 - (0 if sgn > 0 else 0.015), ya, 1.4),
                (sgn * 1.955 + (0.015 if sgn > 0 else 0), yb, 2.05), "hull_dark")
    # nav light near the nose (teal glow)
    ny = 3.2
    nx = 1.95 * 0.78 + 0.005
    det.box_m((sgn * nx, ny, 0.55), (0.03, 0.18, 0.08), "glow")
det.box((-0.45, 3.95, 0.75), (0.45, 3.98, 1.35), "hull_dark")    # nose sensor plate
det.box((-0.35, -2.8, 3.45), (0.35, -1.6, 3.49), "hull_dark")    # roof sensor plate
det.box((-0.15, -2.6, 3.45), (0.15, -2.2, 3.5), "metal")
det.box((-0.25, 0.0, 3.45), (0.25, 0.4, 3.48), "glow")            # roof beacon
ob_det = det.finish("Cockpit_Details", COL_MODULE)


# ---------------------------------------------------------------------------
# 12. COLLIDERS  (collection "COL")
#     Plain boxes. In Unity, give each COL_ object a Box Collider (or Mesh
#     Collider) and switch off its Mesh Renderer.
# ---------------------------------------------------------------------------
def collider(name, mn, mx):
    b = MeshBuilder(["collider"])
    b.box(mn, mx, "collider")
    ob = b.finish(name, COL_COLLIDERS)
    ob.display_type = 'WIRE'
    ob.hide_render = True
    return ob

collider("COL_Floor",        (-1.9, -4.0, 0.0), (1.9, 3.8, FLOOR_TOP))
collider("COL_Ceiling",      (-1.9, -4.0, 3.3), (1.9, 1.5, 3.5))
collider("COL_Wall_Left",    (-2.0, -4.0, 0.0), (-1.83, 2.2, 3.5))
collider("COL_Wall_Right",   (1.83, -4.0, 0.0), (2.0, 2.2, 3.5))
collider("COL_Wall_Rear_L",  (-2.0, -4.0, 0.0), (-DOOR_W / 2, -3.88, 3.5))
collider("COL_Wall_Rear_R",  (DOOR_W / 2, -4.0, 0.0), (2.0, -3.88, 3.5))
collider("COL_Wall_Rear_Top", (-DOOR_W / 2, -4.0, FLOOR_TOP + DOOR_H), (DOOR_W / 2, -3.88, 3.5))
collider("COL_Nose",         (-1.7, 2.7, 0.0), (1.7, 3.95, 2.9))
collider("COL_Chair",        (-0.42, CHAIR_Y - 0.45, FLOOR_TOP), (0.42, CHAIR_Y + 0.30, 1.45))
collider("COL_Console",      (-1.0, 1.6, FLOOR_TOP), (1.0, 2.7, 1.6))
collider("COL_SideConsole_L", (-1.83, -2.7, FLOOR_TOP), (-1.38, -1.1, 1.2))
collider("COL_SideConsole_R", (1.38, -2.7, FLOOR_TOP), (1.83, -1.1, 1.2))


# ---------------------------------------------------------------------------
# 13. CHECKS  - triangle count and "does it fit in the box?"
# ---------------------------------------------------------------------------
module_objects = [ob_hull, ob_inter, ob_floor, ob_glass, ob_chair, ob_con, ob_det]
total_tris = 0
lo = Vector((1e9, 1e9, 1e9))
hi = Vector((-1e9, -1e9, -1e9))
print("\n--- Cockpit module report ---")
for ob in module_objects:
    me = ob.data
    me.calc_loop_triangles()
    tris = len(me.loop_triangles)
    total_tris += tris
    for v in me.vertices:
        lo = Vector((min(lo.x, v.co.x), min(lo.y, v.co.y), min(lo.z, v.co.z)))
        hi = Vector((max(hi.x, v.co.x), max(hi.y, v.co.y), max(hi.z, v.co.z)))
    print(f"{ob.name:24s} {tris:6d} tris")
print(f"TOTAL                    {total_tris:6d} tris")
print(f"Bounds min {tuple(round(c, 3) for c in lo)}  max {tuple(round(c, 3) for c in hi)}")
inside = lo.x >= -2.0001 and lo.y >= -4.0001 and lo.z >= -0.0001 and \
         hi.x <= 2.0001 and hi.y <= 4.0001 and hi.z <= 3.5001
print("Fits in 4 x 8 x 3.5 m box:", inside)


# ---------------------------------------------------------------------------
# 14. RENDER SET-UP: dusk sky, sun, planet, cameras (collection RENDER)
# ---------------------------------------------------------------------------
world = bpy.data.worlds.new("Dusk")
scene.world = world
try:
    world.use_nodes = True
except Exception:
    pass
wn = world.node_tree.nodes
wl = world.node_tree.links
bg = wn.get("Background")
coord = wn.new("ShaderNodeTexCoord")
sep = wn.new("ShaderNodeSeparateXYZ")
ramp = wn.new("ShaderNodeValToRGB")
mapr = wn.new("ShaderNodeMapRange")
mapr.inputs["From Min"].default_value = -0.15
mapr.inputs["From Max"].default_value = 0.75
wl.new(coord.outputs["Generated"], sep.inputs[0])
wl.new(sep.outputs["Z"], mapr.inputs["Value"])
wl.new(mapr.outputs["Result"], ramp.inputs["Fac"])
wl.new(ramp.outputs["Color"], bg.inputs["Color"])
cr = ramp.color_ramp
cr.elements[0].position = 0.0
cr.elements[0].color = (*srgb(0.20, 0.15, 0.28), 1)    # below horizon
cr.elements[1].position = 1.0
cr.elements[1].color = (*srgb(0.10, 0.08, 0.24), 1)    # zenith, deep indigo
for pos, col in ((0.17, (0.98, 0.66, 0.52)),            # warm horizon glow
                 (0.30, (0.80, 0.50, 0.62)),            # mauve
                 (0.55, (0.42, 0.30, 0.58))):           # purple
    e = cr.elements.new(pos)
    e.color = (*srgb(*col), 1)
bg.inputs["Strength"].default_value = 0.7


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def add_light(name, kind, loc, energy, color, size=None, target=None):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = energy
    ld.color = srgb(*color)
    if size is not None:
        if kind == 'AREA':
            ld.shape = 'RECTANGLE'
            ld.size, ld.size_y = size
        elif kind == 'SUN':
            ld.angle = math.radians(size)
        else:
            ld.shadow_soft_size = size
    ob = bpy.data.objects.new(name, ld)
    COL_RENDER.objects.link(ob)
    ob.location = loc
    if target is not None:
        look_at(ob, target)
    return ob


sun = add_light("Sun_Dusk", 'SUN', (-30, 35, 9), 2.4, (1.0, 0.82, 0.70), size=3, target=(0, 0, 0))
fill = add_light("Fill_Sky", 'SUN', (25, -20, 30), 0.7, (0.62, 0.55, 0.95), size=20, target=(0, 0, 0))
ceiling = add_light("Interior_Ceiling", 'AREA', (0, -1.1, 3.15), 70, (0.92, 0.95, 0.90),
                    size=(0.4, 4.8), target=(0, -1.1, 0))
console_glow = add_light("Interior_Console", 'POINT', (0, 2.2, 1.6), 25, (0.4, 0.9, 0.85), size=0.3)
top_light = add_light("Cutaway_Top", 'AREA', (0, 0, 12), 1400, (1.0, 0.92, 0.85),
                      size=(6, 10), target=(0, 0, 0))

# The planet ahead (an ocean world, like Pelagic), far in front of the nose.
bm_tmp = bmesh.new()
bmesh.ops.create_icosphere(bm_tmp, subdivisions=4, radius=220)
planet_me = bpy.data.meshes.new("Planet")
bm_tmp.to_mesh(planet_me)
bm_tmp.free()
planet = bpy.data.objects.new("RENDER_Planet", planet_me)
COL_RENDER.objects.link(planet)
planet.location = (60, 760, -60)
pmat = make_mat("M_Planet_Ocean", (0.20, 0.42, 0.55), rough=0.6, emit_strength=0.25)
planet_me.materials.append(pmat)
for p in planet_me.polygons:
    p.use_smooth = True


def add_camera(name, loc, target=None, lens=35, ortho=None, rot=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.05
    cd.clip_end = 3000
    if ortho:
        cd.type = 'ORTHO'
        cd.ortho_scale = ortho
    ob = bpy.data.objects.new(name, cd)
    COL_RENDER.objects.link(ob)
    ob.location = loc
    if target is not None:
        look_at(ob, target)
    if rot is not None:
        ob.rotation_euler = rot
    return ob


cam_ext = add_camera("CAM_Exterior", (-8.2, 10.5, 4.6), target=(0, 0.6, 1.4), lens=35)
cam_int = add_camera("CAM_Interior", (0.0, -3.92, 1.75), target=(0, 3.5, 1.45), lens=18)
cam_top = add_camera("CAM_TopDown", (0, 0, 30), ortho=9.0, rot=(0, 0, math.radians(90)))


# ---------------------------------------------------------------------------
# 15. SAVE + EXPORT
# ---------------------------------------------------------------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)
blend_path = os.path.join(OUTPUT_DIR, "cockpit_test.blend")
fbx_path = os.path.join(OUTPUT_DIR, "cockpit_test.fbx")

if DO_EXPORT_FBX:
    for ob in scene.objects:
        ob.select_set(False)
    for ob in list(COL_MODULE.objects) + list(COL_COLLIDERS.objects):
        ob.select_set(True)
    bpy.context.view_layer.objects.active = ob_hull
    bpy.ops.export_scene.fbx(
        filepath=fbx_path,
        use_selection=True,
        object_types={'MESH'},
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',
        axis_forward='-Z',
        axis_up='Y',
        bake_space_transform=True,     # no -90 degree rotation on import
        mesh_smooth_type='FACE',
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        bake_anim=False,
    )
    print("FBX written:", fbx_path)

if DO_SAVE_BLEND:
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("Blend saved:", blend_path)


# ---------------------------------------------------------------------------
# 16. RENDERS (Cycles). Each shot switches its own lights on.
# ---------------------------------------------------------------------------
def cutaway_copies(objects, z_cut):
    """Make temporary copies with everything above z_cut sliced off, so the
    top-down view can look into the room. Originals are hidden meanwhile."""
    temps = []
    for ob in objects:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                               plane_co=(0, 0, z_cut), plane_no=(0, 0, 1), clear_outer=True)
        me = bpy.data.meshes.new(ob.name + "_cut")
        bm.to_mesh(me)
        bm.free()
        for m in ob.data.materials:
            me.materials.append(m)
        t = bpy.data.objects.new(ob.name + "_cut", me)
        COL_RENDER.objects.link(t)
        ob.hide_render = True
        temps.append(t)
    return temps


def render_shot(cam, filename, lights_on, exposure=0.0):
    scene.camera = cam
    for L in (sun, fill, ceiling, console_glow, top_light):
        L.hide_render = L not in lights_on
    scene.view_settings.exposure = exposure
    scene.render.filepath = os.path.join(OUTPUT_DIR, filename)
    bpy.ops.render.render(write_still=True)
    print("Rendered:", scene.render.filepath)


if DO_RENDER:
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = RENDER_SAMPLES
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.cycles.transparent_max_bounces = 8
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = RENDER_SCALE
    scene.render.image_settings.file_format = 'PNG'

    render_shot(cam_ext, "cockpit_exterior.png", {sun, fill, ceiling, console_glow}, exposure=0.0)
    render_shot(cam_int, "cockpit_interior.png", {sun, fill, ceiling, console_glow}, exposure=0.25)

    cut = cutaway_copies([ob_hull, ob_inter, ob_glass, ob_det], z_cut=2.6)
    planet.hide_render = True
    render_shot(cam_top, "cockpit_topdown.png", {top_light, fill, ceiling, console_glow}, exposure=0.0)
    for t in cut:
        bpy.data.objects.remove(t, do_unlink=True)
    for ob in (ob_hull, ob_inter, ob_glass, ob_det):
        ob.hide_render = False
    planet.hide_render = False
    scene.camera = cam_int

print("Done.")
