"""
SHAKEDOWN - Crew quarters section (comparison build v2, suffix "Opus")
=====================================================================

Builds a 2 x 1 unit ship section (8 m along Y, 4 m wide, 3.5 m tall) that follows
Docs/Specs/section-standard.md, furnished after mockup_quarters_v2.png:

  rear doorway (camera) -> looking +Y
  left wall  (-X): bunk beds in chamfered niches, ladder, drawers, low storage
  far end    (+Y): sage lockers | centred doorway | wash niche, jacket, pictures
  right wall (+X): dinette (two benches + wall table), round porthole, plant
  upper walls    : overhead cabinets; warm light strip under the right ones
  ceiling        : one warm light panel, two ochre pipes on the upper right chamfer

HOW TO RUN
  New Blender file > Scripting tab > New > paste > Run Script.
  The script CLEARS the scene. It saves quarters_Opus.blend, exports
  quarters_Opus.fbx and renders four PNGs into OUTPUT_DIR. Rendering takes
  several minutes and Blender looks frozen meanwhile; set DO_RENDER = False to
  just build.

CONVENTIONS (from the section standard)
  1 unit = 1 m. Box: X -2..2, Y -4..4, Z 0..3.5. +Y = front. Pivot (0,0,0).
  Floor surface Z 0.2, ceiling underside Z 3.2. Walls 0.25 m. Rib frames at
  both ends and every 2 m. Doorways 1.4 x 2.2 m, top corners chamfered 0.25 m.
  Props have their origin at the centre of their base.
  Textures: Box projection, no UVs (only the two little taped pictures use UVs,
  because they are photos on a flat card).
"""

import bpy
import bmesh
import math
import os
import random
from mathutils import Vector, Matrix, Euler

# ---------------------------------------------------------------------------
# 0. SETTINGS
# ---------------------------------------------------------------------------
SUFFIX = "Opus"
OUTPUT_DIR = os.environ.get(
    "QUARTERS_OUT", os.path.expanduser("~/Shakedown/Art/Blender/Quarters_Opus"))
TEX_DIR = os.path.normpath(os.path.join(OUTPUT_DIR, "..", "..", "Textures", "WatercolourTest"))
DO_EXPORT = True
DO_RENDER = os.environ.get("QUARTERS_RENDER", "1") == "1"
SAMPLES = int(os.environ.get("QUARTERS_SAMPLES", "64"))
RES = int(os.environ.get("QUARTERS_RES", "100"))          # % of 1920 x 1080
ONLY = os.environ.get("QUARTERS_ONLY", "")                # e.g. "mockup" for tests

FLOOR_Z, CEIL_Z = 0.2, 3.2
DOOR_W, DOOR_H, DOOR_CH = 1.4, 2.2, 0.25
END_WALL = 0.10            # end wall thickness (Y)
RIB_W, RIB_D = 0.20, 0.10  # rib frame width along Y, depth into the room
RIB_YS = (-2.0, 0.0, 2.0)  # inner ribs every 2 m (end ribs added separately)


# ---------------------------------------------------------------------------
# 1. CLEAR SCENE + COLLECTIONS
# ---------------------------------------------------------------------------
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for col in list(bpy.data.collections):
    bpy.data.collections.remove(col)
for blocks in (bpy.data.meshes, bpy.data.materials, bpy.data.lights,
               bpy.data.cameras, bpy.data.worlds, bpy.data.images):
    for b in list(blocks):
        blocks.remove(b)

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0


def new_collection(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c


C_SECTION = new_collection(f"Quarters_{SUFFIX}")
C_PROPS = new_collection(f"Props_{SUFFIX}")
C_COL = new_collection(f"COL_{SUFFIX}")
C_RENDER = new_collection(f"RENDER_ONLY_{SUFFIX}")
C_TMP = new_collection("TMP")


# ---------------------------------------------------------------------------
# 2. MATERIALS: section-standard palette + watercolour texture chain
# ---------------------------------------------------------------------------
def srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexcol(h):
    h = h.lstrip("#")
    return tuple(srgb_to_lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))


_images = {}


def tex_image(name):
    if name not in _images:
        _images[name] = bpy.data.images.load(os.path.join(TEX_DIR, name), check_existing=True)
    return _images[name]


def add_watercolour(mat, tex_name, scale):
    """Texture Coordinate (Object) -> Mapping -> Image (Box, 0.2)
       -> Mix (Multiply) with base colour -> Principled Base Color."""
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    base = tuple(bsdf.inputs["Base Color"].default_value)
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-1100, 300)
    mp = nt.nodes.new("ShaderNodeMapping"); mp.location = (-900, 300)
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    im = nt.nodes.new("ShaderNodeTexImage"); im.location = (-700, 300)
    im.image = tex_image(tex_name)
    im.projection = 'BOX'
    im.projection_blend = 0.2
    mx = nt.nodes.new("ShaderNodeMix"); mx.location = (-350, 300)
    mx.data_type = 'RGBA'
    mx.blend_type = 'MULTIPLY'
    mx.inputs["Factor"].default_value = 1.0
    mx.inputs[6].default_value = base
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], im.inputs["Vector"])
    nt.links.new(im.outputs["Color"], mx.inputs[7])
    nt.links.new(mx.outputs[2], bsdf.inputs["Base Color"])


def make_mat(name, hx, rough=0.8, metal=0.0, emit=0.0, alpha=1.0, tex=None, scale=0.5):
    m = bpy.data.materials.new(f"{name}_{SUFFIX}")
    try:
        m.use_nodes = True
    except Exception:
        pass
    col = hexcol(hx)
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*col, 1)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
    m.diffuse_color = (*col, alpha)
    if tex:
        add_watercolour(m, tex, scale)
    return m


T_HULL, T_WALL, T_FLOOR = "tex_hull_plating.png", "tex_interior_wall.png", "tex_floor.png"
T_METAL, T_FABRIC = "tex_console_metal.png", "tex_upholstery.png"

MAT = {
    # surfaces of the section
    "hull":        make_mat("M_Hull_Cream",     "#E8DDD2", tex=T_HULL, scale=0.5),
    "hull_teal":   make_mat("M_Hull_TealPanel", "#5E857F", tex=T_HULL, scale=0.5),
    "wall":        make_mat("M_Wall_Beige",     "#E3D3C6", tex=T_WALL, scale=0.5),
    "cream":       make_mat("M_Panel_Cream",    "#E8DDD2", tex=T_WALL, scale=0.5),
    "floor":       make_mat("M_Floor_Plates",   "#5A5560", rough=0.7, tex=T_FLOOR, scale=0.5),
    "slate":       make_mat("M_Frame_Slate",    "#4A4650", rough=0.6, metal=0.2, tex=T_METAL, scale=1.0),
    "slot":        make_mat("M_Slot_Dark",      "#2E2B33", rough=0.7),
    "sage_metal":  make_mat("M_Locker_Sage",    "#7FA39A", rough=0.6, metal=0.15, tex=T_METAL, scale=1.0),
    "teal":        make_mat("M_Accent_Teal",    "#5E857F", rough=0.6, tex=T_METAL, scale=1.0),
    "ochre":       make_mat("M_Accent_Ochre",   "#C9973A", rough=0.5, metal=0.3, tex=T_METAL, scale=1.0),
    "steel":       make_mat("M_Porthole_Steel", "#9C979E", rough=0.45, metal=0.6, tex=T_METAL, scale=1.0),
    "basin":       make_mat("M_Basin",          "#D9DEDC", rough=0.3),
    # fabrics (0.5 m repeat)
    "sage_fabric": make_mat("M_Fabric_Sage",    "#7FA39A", rough=0.95, tex=T_FABRIC, scale=2.0),
    "cream_fabric": make_mat("M_Fabric_Cream",  "#EFE6DA", rough=0.95, tex=T_FABRIC, scale=2.0),
    "ochre_fabric": make_mat("M_Fabric_Ochre",  "#C9973A", rough=0.95, tex=T_FABRIC, scale=2.0),
    "olive_fabric": make_mat("M_Fabric_Olive",  "#6E7A52", rough=0.95, tex=T_FABRIC, scale=2.0),
    # small props
    "leaf":        make_mat("M_Plant_Leaf",     "#6F9A5B", rough=0.7),
    "leaf_dark":   make_mat("M_Plant_LeafDark", "#557E48", rough=0.7),
    "pot":         make_mat("M_Pot_Cream",      "#EADFCF", rough=0.8, tex=T_WALL, scale=2.0),
    "coffee":      make_mat("M_Coffee",         "#3B2A22", rough=0.2),
    "book_cover":  make_mat("M_Book_Teal",      "#5E857F", rough=0.8, tex=T_FABRIC, scale=2.0),
    "paper":       make_mat("M_Paper",          "#F2EBDD", rough=0.9),
    "tape":        make_mat("M_Tape",           "#F1E7CF", rough=0.6, alpha=0.85),
    # light and glass
    "amber":       make_mat("M_Light_Amber",    "#FFD9A3", emit=6.0),
    "amber_soft":  make_mat("M_Light_AmberSoft", "#FFD9A3", emit=2.5),
    "glass":       make_mat("M_Porthole_Glass", "#A9C7D3", rough=0.03, alpha=0.12),
    "collider":    make_mat("M_Collider",       "#FF00FF", alpha=0.25),
}


# ---------------------------------------------------------------------------
# 3. MESH TOOLKIT
# ---------------------------------------------------------------------------
def rot(rx=0.0, ry=0.0, rz=0.0):
    return Euler((math.radians(rx), math.radians(ry), math.radians(rz))).to_matrix().to_4x4()


class MB:
    """Mesh builder: collects faces in a bmesh; each face has a material key."""

    def __init__(self):
        self.bm = bmesh.new()
        self.keys = []

    def slot(self, key):
        if key not in self.keys:
            self.keys.append(key)
        return self.keys.index(key)

    def _faces(self, faces, key, fix=True):
        for f in faces:
            f.material_index = self.slot(key)
        if fix:
            bmesh.ops.recalc_face_normals(self.bm, faces=faces)
        return faces

    def face(self, pts, key, normal=None):
        f = self.bm.faces.new([self.bm.verts.new(Vector(p)) for p in pts])
        f.material_index = self.slot(key)
        if normal is not None:
            f.normal_update()
            if f.normal.dot(Vector(normal)) < 0:
                f.normal_flip()
        return f

    def box(self, mn, mx, key, M=None):
        x0, y0, z0 = mn
        x1, y1, z1 = mx
        c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        if M is not None:
            c = [M @ Vector(p) for p in c]
        v = [self.bm.verts.new(Vector(p)) for p in c]
        fs = [self.bm.faces.new([v[i] for i in idx]) for idx in
              [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]]
        return self._faces(fs, key, fix=False)

    def box_c(self, centre, size, key, R=None):
        """Box by centre and size, optionally rotated (4x4 matrix) about its centre."""
        h = Vector(size) / 2
        M = Matrix.Translation(Vector(centre)) @ (R if R is not None else Matrix.Identity(4))
        return self.box(-h, h, key, M)

    def prism(self, profile, offset, key):
        """Extrude a flat convex outline (3D points) by 'offset' into a solid."""
        off = Vector(offset)
        a = [self.bm.verts.new(Vector(p)) for p in profile]
        b = [self.bm.verts.new(Vector(p) + off) for p in profile]
        fs = [self.bm.faces.new(a), self.bm.faces.new(b[::-1])]
        n = len(a)
        for i in range(n):
            j = (i + 1) % n
            fs.append(self.bm.faces.new([a[i], a[j], b[j], b[i]]))
        return self._faces(fs, key)

    def cyl(self, a, b, r, key, sides=8, r2=None):
        """Faceted cylinder / cone from a to b."""
        a, b = Vector(a), Vector(b)
        d = (b - a).normalized()
        u = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))).normalized()
        w = d.cross(u)
        r2 = r if r2 is None else r2
        ra, rb = [], []
        for i in range(sides):
            ang = 2 * math.pi * (i + 0.5) / sides
            o = u * math.cos(ang) + w * math.sin(ang)
            ra.append(self.bm.verts.new(a + o * r))
            rb.append(self.bm.verts.new(b + o * r2))
        fs = [self.bm.faces.new(ra[::-1]), self.bm.faces.new(rb)]
        for i in range(sides):
            j = (i + 1) % sides
            fs.append(self.bm.faces.new([ra[i], ra[j], rb[j], rb[i]]))
        return self._faces(fs, key)

    def ring(self, centre, axis, r_in, r_out, depth, key, sides=24):
        """Flat annulus (washer) of given depth along 'axis' (unit vector)."""
        c, ax = Vector(centre), Vector(axis).normalized()
        u = ax.cross(Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0))).normalized()
        w = ax.cross(u)
        fs = []
        for i in range(sides):
            a0 = 2 * math.pi * i / sides
            a1 = 2 * math.pi * (i + 1) / sides
            pts = []
            for (ang, r) in ((a0, r_in), (a1, r_in), (a1, r_out), (a0, r_out)):
                pts.append(c + (u * math.cos(ang) + w * math.sin(ang)) * r)
            q0 = [self.bm.verts.new(p) for p in pts]
            q1 = [self.bm.verts.new(p + ax * depth) for p in pts]
            fs.append(self.bm.faces.new(q0[::-1]))
            fs.append(self.bm.faces.new(q1))
            fs.append(self.bm.faces.new([q0[2], q0[3], q1[3], q1[2]]))   # outer rim
            fs.append(self.bm.faces.new([q0[0], q0[1], q1[1], q1[0]]))   # inner rim
        for f in fs:
            f.material_index = self.slot(key)
        for f in fs:
            f.normal_update()
        return fs

    def append_mesh(self, me, key_for_name):
        """Append an existing mesh (e.g. a boolean result); material names map to keys."""
        names = [m.name if m else "" for m in me.materials]
        start = len(self.bm.faces)
        self.bm.from_mesh(me)
        self.bm.faces.ensure_lookup_table()
        for f in list(self.bm.faces)[start:]:
            idx = f.material_index
            nm = names[idx] if idx < len(names) else ""
            f.material_index = self.slot(key_for_name(nm))

    def finish(self, name, coll, origin=None):
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=0.0004)
        if origin is not None:
            bmesh.ops.translate(self.bm, verts=self.bm.verts, vec=-Vector(origin))
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        for k in self.keys:
            me.materials.append(MAT[k])
        for p in me.polygons:
            p.use_smooth = False
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        if origin is not None:
            ob.location = Vector(origin)
        return ob


def base_centre(builder):
    """Centre of the bounding-box base of everything in a builder (prop origin)."""
    vs = [v.co for v in builder.bm.verts]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))


def chamfer_rect(x0, x1, z0, z1, c, bottom=True):
    """Outline (u, v) of a rectangle with chamfered corners, counter-clockwise."""
    if bottom:
        return [(x0 + c, z0), (x1 - c, z0), (x1, z0 + c), (x1, z1 - c),
                (x1 - c, z1), (x0 + c, z1), (x0, z1 - c), (x0, z0 + c)]
    return [(x0, z0), (x1, z0), (x1, z1 - c), (x1 - c, z1), (x0 + c, z1), (x0, z1 - c)]


def boolean_difference(base, cutters, name):
    """Apply Boolean DIFFERENCE (Exact) with each cutter; returns a new Mesh."""
    bob = base.finish("TMP_" + name, C_TMP)
    cobs = [c.finish(f"TMP_{name}_cut{i}", C_TMP) for i, c in enumerate(cutters)]
    for co in cobs:
        mod = bob.modifiers.new(co.name, 'BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.object = co
        mod.solver = 'EXACT'
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(bob.evaluated_get(dg))
    for o in [bob] + cobs:
        bpy.data.objects.remove(o, do_unlink=True)
    return me


# ---------------------------------------------------------------------------
# 4. THE CROSS-SECTION (chamfered octagon)
# ---------------------------------------------------------------------------
# Outer hull, seen from the front, counter-clockwise (x, z).
# Edges: 0 bottom, 1 lower-right chamfer (0.5), 2 right wall, 3 upper-right
# chamfer (0.8), 4 roof, 5 upper-left chamfer, 6 left wall, 7 lower-left chamfer.
OUTER = [(-1.5, 0.0), (1.5, 0.0), (2.0, 0.5), (2.0, 2.7),
         (1.2, 3.5), (-1.2, 3.5), (-2.0, 2.7), (-2.0, 0.5)]


def offset_poly(poly, dists):
    """Move every edge i inwards by dists[i]; new corners = where moved edges meet."""
    n = len(poly)
    lines = []
    for i in range(n):
        p, q = Vector(poly[i]), Vector(poly[(i + 1) % n])
        e = (q - p).normalized()
        lines.append((p + Vector((-e.y, e.x)) * dists[i], e))
    out = []
    for i in range(n):
        (p1, e1), (p2, e2) = lines[i - 1], lines[i]
        den = e1.x * e2.y - e1.y * e2.x
        t = ((p2.x - p1.x) * e2.y - (p2.y - p1.y) * e2.x) / den
        v = p1 + e1 * t
        out.append((v.x, v.y))
    return out


# Interior: walls 0.25 m thick, floor plate 0.2 m (surface Z 0.2), ceiling at Z 3.2.
INNER = offset_poly(OUTER, [FLOOR_Z, 0.25, 0.25, 0.25, 3.5 - CEIL_Z, 0.25, 0.25, 0.25])
WALL_X = INNER[2][0]                         # +1.75 (inner face of the side walls)
# Rib frames: 0.1 m proud of the inner shell (bottom edge stays on the floor).
RIB_IN = offset_poly(INNER, [0.0] + [RIB_D] * 7)


def ring_at(poly, y):
    return [Vector((x, y, z)) for (x, z) in poly]


def dist_to_poly(px, pz, poly):
    best = 1e9
    p = Vector((px, pz))
    for i in range(len(poly)):
        a, b = Vector(poly[i]), Vector(poly[(i + 1) % len(poly)])
        ab = b - a
        t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
        best = min(best, (a + ab * t - p).length)
    return best


# ---------------------------------------------------------------------------
# 5. SHELL: one solid, cut by booleans, then split into hull / walls / floor / ceiling
# ---------------------------------------------------------------------------
shell = MB()
stations = [-4.0, -2.0, 0.0, 2.0, 4.0]
grid = [[shell.bm.verts.new(p) for p in ring_at(OUTER, y)] for y in stations]
side_faces = {}
for s in range(len(stations) - 1):
    for i in range(8):
        j = (i + 1) % 8
        f = shell.bm.faces.new([grid[s][i], grid[s][j], grid[s + 1][j], grid[s + 1][i]])
        f.material_index = shell.slot("hull")
        side_faces[(s, i)] = f
shell.bm.faces.new(grid[0][::-1]).material_index = shell.slot("hull")
shell.bm.faces.new(grid[-1]).material_index = shell.slot("hull")
bmesh.ops.recalc_face_normals(shell.bm, faces=shell.bm.faces[:])

# Recessed exterior panels (they sink 3 cm, so nothing leaves the grid box):
# teal-grey panels on both upper chamfers, amber light strips on the lower ones.
teal_faces = [side_faces[(s, i)] for s in range(4) for i in (3, 5)]
amber_faces = [side_faces[(s, i)] for s in (1, 2) for i in (1, 7)]
for f in teal_faces:
    f.material_index = shell.slot("hull_teal")
for f in amber_faces:
    f.material_index = shell.slot("amber_soft")
r1 = bmesh.ops.inset_individual(shell.bm, faces=teal_faces, thickness=0.10, depth=-0.03,
                                use_even_offset=True)
r2 = bmesh.ops.inset_individual(shell.bm, faces=amber_faces, thickness=0.25, depth=-0.02,
                                use_even_offset=True)
# shallow panel lines on the side walls (not the porthole bay)
side_panels = [side_faces[(s, i)] for s in range(4) for i in (2, 6) if not (i == 2 and s == 1)]
r3 = bmesh.ops.inset_individual(shell.bm, faces=side_panels, thickness=0.08, depth=-0.012,
                                use_even_offset=True)
for f in r1["faces"] + r2["faces"] + r3["faces"]:
    f.material_index = shell.slot("hull")

# Cutters: the room cavity, two doorways, the porthole.
cavity = MB()
cavity.prism([Vector((x, -4.0 + END_WALL, z)) for (x, z) in INNER], (0, 8.0 - 2 * END_WALL, 0), "wall")
DOOR = chamfer_rect(-DOOR_W / 2, DOOR_W / 2, FLOOR_Z, FLOOR_Z + DOOR_H, DOOR_CH, bottom=False)
door_rear = MB()
door_rear.prism([Vector((x, -4.2, z)) for (x, z) in DOOR], (0, 0.4, 0), "wall")
door_front = MB()
door_front.prism([Vector((x, 3.8, z)) for (x, z) in DOOR], (0, 0.4, 0), "wall")
PORT_Y, PORT_Z, PORT_R = -1.0, 1.6, 0.36
port_cut = MB()
port_cut.cyl((1.55, PORT_Y, PORT_Z), (2.3, PORT_Y, PORT_Z), 0.46, "wall", sides=24)

shell_mesh = boolean_difference(shell, [cavity, door_rear, door_front, port_cut], "Shell")

# Classify every face by where it sits.
src = bmesh.new()
src.from_mesh(shell_mesh)
mat_names = [m.name for m in shell_mesh.materials]
classes = {"Hull": [], "InteriorShell": [], "Floor": [], "Ceiling": []}
face_key = {}
for f in src.faces:
    c = f.calc_center_median()
    n = f.normal
    name = mat_names[f.material_index] if f.material_index < len(mat_names) else ""
    on_outer = abs(c.y) > 3.999 or dist_to_poly(c.x, c.z, OUTER) < 0.04
    if on_outer and abs(c.y) <= 4.0 and not (abs(c.x) > 1.6 and abs(c.y - PORT_Y) < 0.47
                                            and abs(c.z - PORT_Z) < 0.47 and abs(n.x) < 0.95):
        classes["Hull"].append(f.index)
        if "TealPanel" in name:
            face_key[f.index] = "hull_teal"
        elif "AmberSoft" in name:
            face_key[f.index] = "amber_soft"
        else:
            face_key[f.index] = "hull"
    elif n.z > 0.9 and abs(c.z - FLOOR_Z) < 0.01:
        classes["Floor"].append(f.index); face_key[f.index] = "floor"
    elif n.z < -0.9 and abs(c.z - CEIL_Z) < 0.01:
        classes["Ceiling"].append(f.index); face_key[f.index] = "cream"
    else:
        classes["InteriorShell"].append(f.index); face_key[f.index] = "wall"

section_objects = []


def split_object(cls, name):
    keep = set(classes[cls])
    bm = src.copy()
    bm.faces.ensure_lookup_table()
    mb = MB()
    keys = {}
    for f in bm.faces:
        if f.index in keep:
            f.material_index = mb.slot(face_key[f.index])
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
    mb.bm.free()
    mb.bm = bm
    ob = mb.finish(name, C_SECTION)
    section_objects.append(ob)
    return ob


ob_hull = split_object("Hull", f"Quarters_{SUFFIX}_Hull")
ob_inner = split_object("InteriorShell", f"Quarters_{SUFFIX}_InteriorShell")
ob_floor = split_object("Floor", f"Quarters_{SUFFIX}_Floor")
ob_ceiling = split_object("Ceiling", f"Quarters_{SUFFIX}_Ceiling")
src.free()
bpy.data.meshes.remove(shell_mesh)


# ---------------------------------------------------------------------------
# 6. RIB FRAMES (both ends + every 2 m) AND DOOR SURROUNDS
# ---------------------------------------------------------------------------
def rib_band(mb, y0, y1, key="slate"):
    a, b = INNER, RIB_IN
    centre = Vector((0, 0, 1.7))
    for i in range(1, 8):                 # edge 0 is the floor: no frame there
        j = (i + 1) % 8
        A0, A1, B0, B1 = Vector(a[i]), Vector(a[j]), Vector(b[i]), Vector(b[j])

        def P(v, y):
            return Vector((v.x, y, v.y))
        mb.face([P(A0, y0), P(A1, y0), P(B1, y0), P(B0, y0)], key, normal=(0, -1, 0))
        mb.face([P(A0, y1), P(A1, y1), P(B1, y1), P(B0, y1)], key, normal=(0, 1, 0))
        mid = (B0 + B1) / 2
        mb.face([P(B0, y0), P(B1, y0), P(B1, y1), P(B0, y1)], key,
                normal=(-(mid.x), 0, -(mid.y - centre.z)))


ribs = MB()
inner_end = 4.0 - END_WALL
rib_band(ribs, -inner_end, -inner_end + RIB_W)
rib_band(ribs, inner_end - RIB_W, inner_end)
for y in RIB_YS:
    rib_band(ribs, y - RIB_W / 2, y + RIB_W / 2)
section_objects.append(ribs.finish(f"Quarters_{SUFFIX}_Ribs", C_SECTION))

# Door surrounds: dark frames 0.15 m wide, 0.1 m proud of each end wall.
frames = MB()
DOOR_OUT = offset_poly(DOOR, [0.0] + [-0.15] * 5)
for sgn in (-1, 1):
    y_wall = sgn * inner_end               # inner face of the end wall
    y_in = y_wall - sgn * 0.10             # frame face inside the room
    for i in range(1, 6):
        j = (i + 1) % 6
        a0, a1 = Vector(DOOR[i]), Vector(DOOR[j])
        b0, b1 = Vector(DOOR_OUT[i]), Vector(DOOR_OUT[j])

        def P(v, y):
            return Vector((v.x, y, v.y))
        frames.face([P(a0, y_in), P(a1, y_in), P(b1, y_in), P(b0, y_in)], "slate",
                    normal=(0, -sgn, 0))
        mid_a = (a0 + a1) / 2
        frames.face([P(a0, y_wall), P(a1, y_wall), P(a1, y_in), P(a0, y_in)], "slate",
                    normal=(-mid_a.x, 0, -(mid_a.y - 1.2)))
        mid_b = (b0 + b1) / 2
        frames.face([P(b0, y_wall), P(b1, y_wall), P(b1, y_in), P(b0, y_in)], "slate",
                    normal=(mid_b.x, 0, mid_b.y - 1.2))
    # small amber "door ready" light above each doorway
    frames.box((-0.12, y_in - sgn * 0.01 - 0.01, 2.5), (0.12, y_in - sgn * 0.01 + 0.01, 2.56), "amber")
section_objects.append(frames.finish(f"Quarters_{SUFFIX}_DoorFrames", C_SECTION))

# Sliding door panels (closed), one object each.
for sgn, nm in ((-1, "Door_Back"), (1, "Door_Front")):
    d = MB()
    shrink = offset_poly(DOOR, [0.0] + [0.01] * 5)
    y0 = sgn * (4.0 - END_WALL / 2) - 0.02
    d.prism([Vector((x, y0, z)) for (x, z) in shrink], (0, 0.04, 0), "cream")
    yf = y0 if sgn > 0 else y0 + 0.04        # room-facing side
    out = -0.012 if sgn > 0 else 0.012
    d.box((-0.04, min(yf, yf + out), 0.95), (0.04, max(yf, yf + out), 1.45), "teal")   # handle slot
    d.box((-0.66, min(yf, yf + out), 1.55), (0.66, max(yf, yf + out), 1.60), "slate")  # seam band
    section_objects.append(d.finish(f"{nm}_{SUFFIX}", C_SECTION))


# ---------------------------------------------------------------------------
# 7. PIPES along the upper RIGHT chamfer, with brackets at every rib
#    Fixed position (same in every section): offset 0.2 m from the chamfer,
#    0.13 m either side of its middle, radius 0.06 m.
# ---------------------------------------------------------------------------
pipes = MB()
ca, cb = Vector(INNER[3]), Vector(INNER[4])           # upper-right chamfer (x, z)
mid = (ca + cb) / 2
t = (cb - ca).normalized()
nrm = Vector((-t.y, t.x))                              # points into the room
PIPE_POS = [mid + nrm * 0.20 + t * 0.13, mid + nrm * 0.20 - t * 0.13]
for p in PIPE_POS:
    pipes.cyl((p.x, -inner_end, p.y), (p.x, inner_end, p.y), 0.06, "ochre", sides=10)
for y in (-inner_end + RIB_W / 2, -2.0, 0.0, 2.0, inner_end - RIB_W / 2):
    bc = mid + nrm * 0.17
    pipes.box_c((bc.x, y, bc.y), (0.46, 0.08, 0.10), "slate",
                Matrix.Rotation(-math.atan2(t.y, t.x), 4, 'Y'))
    for p in PIPE_POS:
        pipes.ring((p.x, y - 0.035, p.y), (0, 1, 0), 0.062, 0.085, 0.07, "slate", sides=10)
section_objects.append(pipes.finish(f"Quarters_{SUFFIX}_Pipes", C_SECTION))


# ---------------------------------------------------------------------------
# 8. BUNK BEDS (left wall, built in, bedding included)
# ---------------------------------------------------------------------------
BY0, BY1 = -3.0, -0.8           # bunk length along Y
BXF = -0.85                     # front face of the bunk fascia
LOW_OPEN = (0.62, 1.18)         # z range of lower niche opening
UP_OPEN = (1.40, 1.96)
bunk = MB()

# Fascia with two chamfered niche openings (Boolean cut).
fascia = MB()
fascia.box((BXF - 0.06, BY0, FLOOR_Z), (BXF, BY1, 2.10), "cream")
cutters = []
for (z0, z1) in (LOW_OPEN, UP_OPEN):
    c = MB()
    outline = chamfer_rect(BY0 + 0.12, BY1 - 0.12, z0, z1, 0.16)
    c.prism([Vector((BXF - 0.2, y, z)) for (y, z) in outline], (0.4, 0, 0), "cream")
    cutters.append(c)
fascia_mesh = boolean_difference(fascia, cutters, "Fascia")
bunk.append_mesh(fascia_mesh, lambda nm: "cream")
bpy.data.meshes.remove(fascia_mesh)

inner_x0 = -WALL_X + 0.0         # -1.75
bunk.box((inner_x0, BY0, FLOOR_Z), (BXF - 0.06, BY1, LOW_OPEN[0] - 0.07), "cream")   # drawer block
bunk.box((inner_x0, BY0, 1.18), (BXF - 0.06, BY1, UP_OPEN[0] - 0.04), "cream")       # middle shelf
bunk.box((inner_x0, BY0, UP_OPEN[1]), (BXF - 0.06, BY1, 2.10), "cream")              # top
for (ya, yb) in ((BY0, BY0 + 0.06), (BY1 - 0.06, BY1)):                              # end boards
    bunk.box((inner_x0, ya, FLOOR_Z), (BXF - 0.06, yb, 2.10), "cream")
# Drawers under the lower bunk.
n_dr = 3
w_dr = (BY1 - BY0 - 0.16) / n_dr
for k in range(n_dr):
    ya = BY0 + 0.08 + k * w_dr + 0.02
    yb = ya + w_dr - 0.04
    bunk.box((BXF, ya, 0.25), (BXF + 0.02, yb, 0.52), "cream")
    ym = (ya + yb) / 2
    bunk.box((BXF + 0.02, ym - 0.12, 0.40), (BXF + 0.024, ym + 0.12, 0.44), "slot")

# Bedding: mattress (sage), pillow (cream) at the far end, blanket (ochre) at the foot.
for (z0, z1) in (LOW_OPEN, UP_OPEN):
    mz0 = z0 - 0.07
    mz1 = mz0 + 0.17
    bunk.box((-1.62, BY0 + 0.08, mz0), (-0.94, BY1 - 0.08, mz1), "sage_fabric")
    # pillow: a chamfered cushion
    prof = chamfer_rect(-1.55, -1.02, mz1, mz1 + 0.13, 0.05)
    bunk.prism([Vector((x, BY1 - 0.48, z)) for (x, z) in prof], (0, 0.36, 0), "cream_fabric")
    # folded blanket on the mattress + a fold hanging over the fascia lip
    bunk.box((-1.60, BY0 + 0.10, mz1), (-0.92, BY0 + 0.78, mz1 + 0.05), "ochre_fabric")
    bunk.box((-0.93, BY0 + 0.14, z0 - 0.005), (BXF + 0.03, BY0 + 0.74, z0 + 0.035), "ochre_fabric")
    bunk.box((BXF, BY0 + 0.14, z0 - 0.20), (BXF + 0.03, BY0 + 0.74, z0 + 0.03), "ochre_fabric")
    # reading light on the back wall near the pillow
    rz = z1 - 0.10
    bunk.box((inner_x0, BY1 - 0.82, rz - 0.04), (inner_x0 + 0.03, BY1 - 0.52, rz + 0.04), "slate")
    bunk.box((inner_x0 + 0.03, BY1 - 0.80, rz - 0.025), (inner_x0 + 0.04, BY1 - 0.54, rz + 0.025), "amber")

# Ochre ladder at the foot end (near the door).
LY = BY0 + 0.38
LX = BXF + 0.08
for dy in (-0.21, 0.21):
    bunk.box((LX - 0.025, LY + dy - 0.025, FLOOR_Z), (LX + 0.025, LY + dy + 0.025, 1.70), "slate")
    bunk.box((BXF, LY + dy - 0.025, 1.66), (LX + 0.025, LY + dy + 0.025, 1.71), "slate")   # hook
for z in (0.50, 0.85, 1.20, 1.55):
    bunk.cyl((LX, LY - 0.19, z), (LX, LY + 0.19, z), 0.026, "ochre", sides=6)
section_objects.append(bunk.finish(f"Quarters_{SUFFIX}_Bunks", C_SECTION))


# ---------------------------------------------------------------------------
# 9. OVERHEAD CABINETS (both sides), LOW STORAGE (left), LIGHT STRIP (right)
# ---------------------------------------------------------------------------
cab = MB()
SEGMENTS = [(-inner_end + RIB_W + 0.02, -2.12), (-1.88, -0.12), (0.12, 1.88), (2.12, inner_end - RIB_W - 0.02)]
CHAMFER_Z = INNER[2][1]                      # where the vertical wall meets the upper chamfer
for (ya, yb) in SEGMENTS:
    # Left: follows the upper chamfer, front face at x = -1.25.
    x_top = INNER[5][0] + (INNER[6][0] - INNER[5][0]) * (2.92 - INNER[5][1]) / (INNER[6][1] - INNER[5][1])
    profL = [(-WALL_X, 2.15), (-1.25, 2.15), (-1.25, 2.92), (x_top, 2.92), (-WALL_X, CHAMFER_Z)]
    cab.prism([Vector((x, ya, z)) for (x, z) in profL], (0, yb - ya, 0), "cream")
    # Right: below the pipes, front face at x = 1.25.
    cab.box((1.25, ya, 2.20), (WALL_X, yb, 2.58), "cream")
    # Doors with inset handles.
    n = 2
    w = (yb - ya) / n
    for k in range(n):
        da, db = ya + k * w + 0.015, ya + (k + 1) * w - 0.015
        cab.box((-1.25, da, 2.19), (-1.23, db, 2.88), "cream")
        cab.box((-1.232, (da + db) / 2 - 0.13, 2.30), (-1.226, (da + db) / 2 + 0.13, 2.35), "slot")
        cab.box((1.23, da, 2.23), (1.25, db, 2.55), "cream")
        cab.box((1.226, (da + db) / 2 - 0.13, 2.44), (1.232, (da + db) / 2 + 0.13, 2.49), "slot")
    # Warm light strip under the right-hand cabinets.
    cab.box((1.28, ya + 0.08, 2.185), (1.36, yb - 0.08, 2.20), "amber")

# Low storage bench on the left between the ribs at 0 and 2 m.
cab.box((-WALL_X, 0.12, FLOOR_Z), (-1.30, 1.88, 0.70), "cream")
cab.box((-WALL_X, 0.10, 0.70), (-1.28, 1.90, 0.75), "teal")
for (ya, yb) in ((0.16, 0.99), (1.01, 1.84)):
    cab.box((-1.30, ya, 0.24), (-1.28, yb, 0.66), "cream")
    cab.box((-1.28, (ya + yb) / 2 - 0.12, 0.55), (-1.276, (ya + yb) / 2 + 0.12, 0.59), "slot")
section_objects.append(cab.finish(f"Quarters_{SUFFIX}_Cabinets", C_SECTION))


# ---------------------------------------------------------------------------
# 10. WASH NICHE (far end, right of the doorway)
# ---------------------------------------------------------------------------
wn = MB()
NX0, NX1 = 0.86, WALL_X
NY0, NY1 = 3.12, inner_end - RIB_W
wn.box((0.92, NY0 + 0.03, FLOOR_Z), (1.69, NY1, 0.86), "cream")                       # vanity
wn.box((0.97, NY0 + 0.01, 0.25), (1.64, NY0 + 0.03, 0.81), "cream")                    # vanity door
wn.box((1.55, NY0 - 0.004, 0.42), (1.58, NY0 + 0.01, 0.62), "slot")                    # handle
wn.box((0.94, NY0 - 0.06, 0.86), (1.67, NY1, 1.0), "cream")                            # counter
wn.box((1.02, NY0 + 0.0, 0.985), (1.55, NY1 - 0.12, 1.002), "basin")                   # basin
wn.cyl((1.30, NY1 - 0.06, 1.0), (1.30, NY1 - 0.06, 1.20), 0.018, "steel", sides=6)    # tap
wn.cyl((1.30, NY1 - 0.06, 1.19), (1.30, NY1 - 0.24, 1.17), 0.016, "steel", sides=6)
wn.box((1.26, NY1 - 0.09, 1.08), (1.34, NY1 - 0.03, 1.10), "steel")                    # knob
wn.box((1.55, NY1 - 0.16, 1.0), (1.63, NY1 - 0.08, 1.14), "sage_metal")                # soap
wn.cyl((1.59, NY1 - 0.12, 1.14), (1.59, NY1 - 0.12, 1.19), 0.008, "steel", sides=6)
wn.box((1.59 - 0.008, NY1 - 0.18, 1.18), (1.59 + 0.008, NY1 - 0.12, 1.19), "steel")
for (xa, xb) in ((NX0, 0.94), (1.67, NX1)):                                             # sides
    wn.box((xa, NY0 - 0.06, 0.86), (xb, NY1, 2.20), "cream")
wn.box((NX0, NY0 - 0.06, 2.05), (NX1, NY1, 2.20), "cream")                              # top
wn.box((0.94, NY1 - 0.03, 1.0), (1.67, NY1, 2.05), "wall")                              # back
for sx, x in ((1, 0.94), (-1, 1.67)):                                                   # chamfers
    pts = [(x, 2.05), (x + sx * 0.14, 2.05), (x, 1.91)]
    wn.prism([Vector((px, NY0 - 0.06, pz)) for (px, pz) in pts], (0, NY1 - NY0 + 0.06, 0), "cream")
wn.box((1.10, NY0 + 0.08, 2.035), (1.51, NY0 + 0.26, 2.05), "amber")                    # light
section_objects.append(wn.finish(f"Quarters_{SUFFIX}_WashNiche", C_SECTION))


# ---------------------------------------------------------------------------
# 11. PORTHOLE (right wall, above the table): bolted ring, tube, glass
# ---------------------------------------------------------------------------
ph = MB()
ph.ring((WALL_X, PORT_Y, PORT_Z), (-1, 0, 0), PORT_R, 0.52, 0.06, "steel", sides=24)
ph.ring((WALL_X - 0.06, PORT_Y, PORT_Z), (-1, 0, 0), PORT_R, 0.40, 0.02, "slate", sides=24)
for k in range(12):
    a = 2 * math.pi * k / 12
    by, bz = PORT_Y + 0.46 * math.cos(a), PORT_Z + 0.46 * math.sin(a)
    ph.cyl((WALL_X - 0.06, by, bz), (WALL_X - 0.08, by, bz), 0.02, "steel", sides=6)
# tube lining through the wall and the outer ring (flush, inside the box)
ph.ring((WALL_X - 0.06, PORT_Y, PORT_Z), (1, 0, 0), PORT_R, 0.46, 2.0 - WALL_X + 0.06, "steel", sides=24)
section_objects.append(ph.finish(f"Quarters_{SUFFIX}_Porthole", C_SECTION))

glass = MB()
pts = [Vector((1.90, PORT_Y + PORT_R * math.cos(2 * math.pi * k / 24),
               PORT_Z + PORT_R * math.sin(2 * math.pi * k / 24))) for k in range(24)]
glass.face(pts, "glass", normal=(-1, 0, 0))
section_objects.append(glass.finish(f"Quarters_{SUFFIX}_PortholeGlass", C_SECTION))


# ---------------------------------------------------------------------------
# 12. CEILING LIGHT PANEL (one, central)
# ---------------------------------------------------------------------------
lights = MB()
LP_Y = -1.0
lights.box((-0.62, LP_Y - 0.32, CEIL_Z - 0.06), (0.62, LP_Y + 0.32, CEIL_Z), "slate")
lights.box((-0.54, LP_Y - 0.24, CEIL_Z - 0.07), (0.54, LP_Y + 0.24, CEIL_Z - 0.06), "amber")
section_objects.append(lights.finish(f"Quarters_{SUFFIX}_CeilingLight", C_SECTION))


# ---------------------------------------------------------------------------
# 13. PROPS (placeable). Origin = centre of each prop's base.
# ---------------------------------------------------------------------------
prop_objects = []


def finish_prop(mb, name):
    ob = mb.finish(f"Prop_{name}_{SUFFIX}", C_PROPS, origin=base_centre(mb))
    prop_objects.append(ob)
    return ob


# Lockers: two tall sage lockers left of the far doorway.
lk = MB()
LKX0, LKX1, LKY0, LKY1 = -1.72, -0.90, 3.10, inner_end - RIB_W - 0.02
lk.box((LKX0 + 0.03, LKY0 + 0.05, FLOOR_Z), (LKX1 - 0.03, LKY1, 0.27), "slate")       # plinth
lk.box((LKX0, LKY0 + 0.02, 0.27), (LKX1, LKY1, 2.15), "sage_metal")                   # body
wl = (LKX1 - LKX0) / 2
for k in range(2):
    xa, xb = LKX0 + k * wl + 0.012, LKX0 + (k + 1) * wl - 0.012
    lk.box((xa, LKY0, 0.30), (xb, LKY0 + 0.02, 2.12), "sage_metal")                   # door
    for v in range(3):                                                                 # vents
        z = 1.80 + v * 0.07
        lk.box((xa + 0.08, LKY0 - 0.004, z), (xb - 0.08, LKY0 + 0.005, z + 0.03), "slot")
    hx = xb - 0.06 if k == 0 else xa + 0.04
    lk.box((hx, LKY0 - 0.004, 1.05), (hx + 0.02, LKY0 + 0.005, 1.30), "slot")         # handle
finish_prop(lk, "Lockers")

# Dinette: two benches facing each other, wall-mounted table between.
dn = MB()
DX0, DX1 = 0.86, 1.72
for (ya, yb, sgn) in ((-1.90, -1.44, 1), (-0.56, -0.10, -1)):
    back_y = ya if sgn > 0 else yb                    # backrest against the far side
    dn.box((DX0, ya, FLOOR_Z), (DX1, yb, 0.48), "cream")                           # base
    seat = chamfer_rect(ya + (0.12 if sgn > 0 else 0.0), yb - (0.0 if sgn > 0 else 0.12), 0.48, 0.61, 0.04)
    dn.prism([Vector((DX0 + 0.02, y, z)) for (y, z) in seat], (DX1 - DX0 - 0.04, 0, 0), "sage_fabric")
    by0, by1 = (ya, ya + 0.12) if sgn > 0 else (yb - 0.12, yb)
    dn.box((DX0, by0, 0.48), (DX1, by1, 1.28), "cream")                            # back frame
    cy0, cy1 = (by1, by1 + 0.10) if sgn > 0 else (by0 - 0.10, by0)
    back = chamfer_rect(cy0, cy1, 0.64, 1.22, 0.035)
    dn.prism([Vector((DX0 + 0.04, y, z)) for (y, z) in back], (DX1 - DX0 - 0.08, 0, 0), "sage_fabric")
# table top with chamfered aisle corners
top = [(DX0 + 0.10, -1.38), (DX1, -1.38), (DX1, -0.62), (DX0 + 0.10, -0.62), (DX0 - 0.02, -0.74), (DX0 - 0.02, -1.26)]
dn.prism([Vector((x, y, 0.93)) for (x, y) in reversed(top)], (0, 0, 0.05), "cream")
dn.box((DX1 - 0.02, -1.08, 0.50), (DX1, -0.92, 0.95), "slate")                     # wall plate
Rs = Matrix.Rotation(math.radians(-50), 4, 'Y')
dn.box_c(((DX1 + 1.20) / 2 - 0.02, -1.0, 0.74), (0.62, 0.05, 0.05), "slate", Rs)  # strut
finish_prop(dn, "Dinette")

# Mug on a coaster.
mg = MB()
MX, MY, MZ = 1.48, -0.80, 0.98
mg.cyl((MX, MY, MZ), (MX, MY, MZ + 0.007), 0.06, "ochre", sides=10)
mg.cyl((MX, MY, MZ + 0.007), (MX, MY, MZ + 0.105), 0.042, "cream", sides=10)
mg.cyl((MX, MY, MZ + 0.090), (MX, MY, MZ + 0.0955), 0.036, "coffee", sides=10)
mg.box((MX - 0.008, MY + 0.040, MZ + 0.03), (MX + 0.008, MY + 0.075, MZ + 0.042), "cream")
mg.box((MX - 0.008, MY + 0.040, MZ + 0.075), (MX + 0.008, MY + 0.075, MZ + 0.087), "cream")
mg.box((MX - 0.008, MY + 0.063, MZ + 0.03), (MX + 0.008, MY + 0.075, MZ + 0.087), "cream")
finish_prop(mg, "Mug")

# Closed book.
bk = MB()
Rb = Matrix.Translation((1.25, -1.12, 0.98)) @ rot(rz=14)
bk.box((-0.085, -0.115, 0.0), (0.085, 0.115, 0.006), "book_cover", Rb)
bk.box((-0.085, -0.115, 0.030), (0.085, 0.115, 0.036), "book_cover", Rb)
bk.box((-0.085, -0.115, 0.0), (-0.072, 0.115, 0.036), "book_cover", Rb)          # spine
bk.box((-0.072, -0.110, 0.006), (0.080, 0.110, 0.030), "paper", Rb)
finish_prop(bk, "Book")

# Potted trailing plant in a wall holder next to the porthole.
pl = MB()
PX, PY, PZ = 1.62, -0.33, 1.42
pl.box((WALL_X - 0.02, PY - 0.05, PZ - 0.02), (WALL_X, PY + 0.05, PZ + 0.10), "slate")   # wall plate
pl.box((PX + 0.06, PY - 0.015, PZ + 0.02), (WALL_X - 0.02, PY + 0.015, PZ + 0.05), "slate")
pl.cyl((PX, PY, PZ), (PX, PY, PZ + 0.15), 0.075, "pot", sides=8, r2=0.09)
pl.ring((PX, PY, PZ + 0.05), (0, 0, 1), 0.085, 0.10, 0.05, "ochre", sides=8)
rnd = random.Random(11)


def leaf(mb, base, direction, length, width, key):
    d = Vector(direction).normalized()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 0.1:
        side = Vector((1, 0, 0))
    side.normalize()
    up = side.cross(d)
    tip = base + d * length
    mid = base + d * (length * 0.45) + up * (length * 0.12)
    mb.face([base, mid + side * width, tip], key, normal=up)
    mb.face([base, tip, mid - side * width], key, normal=up)


top_c = Vector((PX, PY, PZ + 0.15))
for k in range(16):                      # bushy top
    a = 2 * math.pi * k / 16 + rnd.uniform(-0.2, 0.2)
    el = rnd.uniform(0.25, 0.9)
    d = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)))
    leaf(pl, top_c + Vector((rnd.uniform(-0.03, 0.03), rnd.uniform(-0.03, 0.03), 0)), d,
         rnd.uniform(0.10, 0.15), 0.035, "leaf" if k % 3 else "leaf_dark")
for vine in range(3):                    # trailing vines
    a = -0.6 + vine * 0.9
    p = top_c + Vector((math.cos(a) * 0.07 - 0.03, math.sin(a) * 0.07, -0.02))
    for s in range(6):
        q = p + Vector((-0.015, rnd.uniform(-0.02, 0.02), -0.075))
        pl.cyl(p, q, 0.004, "leaf_dark", sides=3)
        for sd in (-1, 1):
            leaf(pl, q, Vector((-0.4, sd * 0.8, -0.3)), 0.06, 0.022, "leaf")
        p = q
finish_prop(pl, "Plant")

# Jacket on a wall hook (right wall, near the far end).
jk = MB()
JY, JX = 2.80, WALL_X
jk.box((JX - 0.015, JY - 0.03, 1.86), (JX, JY + 0.03, 1.96), "slate")                    # hook plate
jk.cyl((JX - 0.015, JY, 1.91), (JX - 0.08, JY, 1.91), 0.012, "slate", sides=6)
jk.cyl((JX - 0.08, JY, 1.91), (JX - 0.085, JY, 1.96), 0.012, "slate", sides=6)
torso = [(JY - 0.21, 1.10), (JY + 0.21, 1.10), (JY + 0.17, 1.80), (JY + 0.06, 1.88),
         (JY - 0.06, 1.88), (JY - 0.17, 1.80)]
jk.prism([Vector((JX - 0.13, y, z)) for (y, z) in torso], (0.10, 0, 0), "olive_fabric")
for sd in (-1, 1):                                                                       # sleeves
    sl = [(JY + sd * 0.15, 1.20), (JY + sd * 0.25, 1.22), (JY + sd * 0.20, 1.80), (JY + sd * 0.12, 1.78)]
    if sd < 0:
        sl = sl[::-1]
    jk.prism([Vector((JX - 0.16, y, z)) for (y, z) in sl], (0.07, 0, 0), "olive_fabric")
    jk.box((JX - 0.145, JY + sd * 0.09 - 0.05, 1.32), (JX - 0.135, JY + sd * 0.09 + 0.05, 1.42), "olive_fabric")
collar = [(JY - 0.09, 1.80), (JY + 0.09, 1.80), (JY + 0.05, 1.90), (JY - 0.05, 1.90)]
jk.prism([Vector((JX - 0.15, y, z)) for (y, z) in collar], (0.05, 0, 0), "olive_fabric")
finish_prop(jk, "Jacket")


# Two small pictures taped to the wall (simple painted images made here).
def make_picture(name, w, h, kind):
    import numpy as np
    W, H = 256, int(256 * h / w)
    yy, xx = np.mgrid[0:H, 0:W]
    v = yy / (H - 1)                      # 0 bottom .. 1 top (image rows go up in Blender)
    u = xx / (W - 1)
    if kind == "mountains":
        sky = np.stack([0.95 - 0.5 * v, 0.62 - 0.25 * v, 0.55 + 0.05 * v], -1)
        img = sky.copy()
        sun = ((u - 0.66) ** 2 + ((v - 0.52) * H / W) ** 2) < 0.012
        img[sun] = [1.0, 0.82, 0.55]
        for (amp, base, col, ph) in ((0.10, 0.42, (0.50, 0.40, 0.58), 1.0),
                                     (0.08, 0.28, (0.33, 0.27, 0.42), 2.6)):
            ridge = base + amp * np.abs(np.sin(u * 7 + ph)) + 0.03 * np.sin(u * 23)
            img[v < ridge] = col
    else:
        sky = np.stack([0.30 + 0.1 * v, 0.33 + 0.12 * v, 0.55 + 0.15 * v], -1)
        img = sky.copy()
        moon = ((u - 0.5) ** 2 + ((v - 0.62) * H / W) ** 2) < 0.025
        img[moon] = [0.93, 0.90, 0.80]
        ridge = 0.30 + 0.07 * np.sin(u * 5 + 0.5)
        img[v < ridge] = (0.25, 0.27, 0.38)
    img = img + np.random.default_rng(3).normal(0, 0.02, img.shape)   # paper grain
    img = np.clip(img, 0, 1)
    rgba = np.concatenate([img, np.ones((H, W, 1))], -1).astype(np.float32)
    im = bpy.data.images.new(name, W, H)
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = os.path.join(OUTPUT_DIR, name + ".png")
    im.file_format = 'PNG'
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    im.save()
    m = bpy.data.materials.new(f"M_{name}_{SUFFIX}")
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = im
    nt.links.new(t.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6
    MAT[name] = m
    return m


make_picture("pic_mountains", 0.24, 0.18, "mountains")
make_picture("pic_moon", 0.18, 0.18, "moon")
pc = MB()
uv_quads = []
for (cy, cz, w, h, tilt, key) in ((2.30, 1.74, 0.24, 0.18, 3, "pic_mountains"),
                                  (2.46, 1.47, 0.18, 0.18, -4, "pic_moon")):
    x = WALL_X - 0.004
    R = Matrix.Rotation(math.radians(tilt), 3, 'X')
    corners = [Vector((0, -w / 2, -h / 2)), Vector((0, w / 2, -h / 2)),
               Vector((0, w / 2, h / 2)), Vector((0, -w / 2, h / 2))]
    pts = [Vector((x, cy, cz)) + R @ c for c in corners]
    f = pc.face(pts, key, normal=(-1, 0, 0))
    uv_quads.append(f)
    for c in corners:                                            # tape at the corners
        tp = Vector((x - 0.002, cy, cz)) + R @ (c * 0.92)
        pc.box_c(tp, (0.002, 0.05, 0.022), "tape", rot(rx=tilt + (35 if c.y * c.z > 0 else -35)))
uvl = pc.bm.loops.layers.uv.new("UVMap")
for f in uv_quads:
    vs = [l.vert.co for l in f.loops]
    ys = [v.y for v in vs]
    zs = [v.z for v in vs]
    for l in f.loops:
        l[uvl].uv = ((l.vert.co.y - min(ys)) / (max(ys) - min(ys)),
                     (l.vert.co.z - min(zs)) / (max(zs) - min(zs)))
finish_prop(pc, "Pictures")


# ---------------------------------------------------------------------------
# 14. COLLIDERS (boxes, collection COL_Opus)
# ---------------------------------------------------------------------------
def collider(name, mn, mx):
    b = MB()
    b.box(mn, mx, "collider")
    ob = b.finish(f"COL_{name}", C_COL)
    ob.display_type = 'WIRE'
    ob.hide_render = True


collider("Floor", (-2, -4, 0), (2, 4, FLOOR_Z))
collider("Ceiling", (-2, -4, CEIL_Z), (2, 4, 3.5))
collider("Wall_L", (-2, -4, 0), (-WALL_X, 4, 3.5))
collider("Wall_R", (WALL_X, -4, 0), (2, 4, 3.5))
for sgn, nm in ((-1, "Back"), (1, "Front")):
    y0, y1 = sorted((sgn * 4.0, sgn * inner_end))
    collider(f"End{nm}_L", (-2, y0, 0), (-DOOR_W / 2, y1, 3.5))
    collider(f"End{nm}_R", (DOOR_W / 2, y0, 0), (2, y1, 3.5))
    collider(f"End{nm}_Top", (-DOOR_W / 2, y0, FLOOR_Z + DOOR_H), (DOOR_W / 2, y1, 3.5))
    collider(f"Door_{nm}", (-DOOR_W / 2, y0, FLOOR_Z), (DOOR_W / 2, y1, FLOOR_Z + DOOR_H))
collider("Bunks", (-WALL_X, BY0, FLOOR_Z), (BXF, BY1, 2.10))
collider("Cabinets_L", (-WALL_X, -inner_end, 2.15), (-1.25, inner_end, 3.2))
collider("Cabinets_R", (1.25, -inner_end, 2.20), (WALL_X, inner_end, 2.6))
collider("Storage", (-WALL_X, 0.12, FLOOR_Z), (-1.28, 1.88, 0.75))
collider("WashNiche", (NX0, NY0 - 0.06, FLOOR_Z), (NX1, inner_end, 2.2))
collider("Lockers", (LKX0, LKY0, FLOOR_Z), (LKX1, LKY1, 2.15))
collider("Dinette_BenchNear", (DX0, -1.90, FLOOR_Z), (DX1, -1.44, 1.28))
collider("Dinette_BenchFar", (DX0, -0.56, FLOOR_Z), (DX1, -0.10, 1.28))
collider("Dinette_Table", (DX0 - 0.02, -1.38, 0.5), (DX1, -0.62, 0.98))


# ---------------------------------------------------------------------------
# 15. REPORT: triangles, bounds, walkway
# ---------------------------------------------------------------------------
def tris(ob):
    ob.data.calc_loop_triangles()
    return len(ob.data.loop_triangles)


report = {"section": {}, "props": {}}
lo = Vector((1e9,) * 3)
hi = Vector((-1e9,) * 3)
for ob in section_objects + prop_objects:
    for v in ob.data.vertices:
        w = ob.matrix_world @ v.co
        lo = Vector((min(lo.x, w.x), min(lo.y, w.y), min(lo.z, w.z)))
        hi = Vector((max(hi.x, w.x), max(hi.y, w.y), max(hi.z, w.z)))
for ob in section_objects:
    report["section"][ob.name] = tris(ob)
for ob in prop_objects:
    report["props"][ob.name] = tris(ob)
shell_total = sum(report["section"].values())
prop_total = sum(report["props"].values())
print("\n--- Quarters report ---")
for k, v in report["section"].items():
    print(f"  {k:34s} {v:6d}")
print(f"  SECTION TOTAL                      {shell_total:6d}  (budget 8000)")
for k, v in report["props"].items():
    print(f"  {k:34s} {v:6d}  (budget 1500)")
print(f"  ALL                                {shell_total + prop_total:6d}  (budget 25000)")
print("  bounds", tuple(round(c, 3) for c in lo), tuple(round(c, 3) for c in hi))
print("  fits box:", lo.x >= -2.0001 and lo.y >= -4.0001 and lo.z >= -0.0001 and
      hi.x <= 2.0001 and hi.y <= 4.0001 and hi.z <= 3.5001)
print(f"  walkway width between bunk ladder and dinette: {DX0 - 0.02 - (LX + 0.025):.2f} m")


# ---------------------------------------------------------------------------
# 16. RENDER STAGING (collection RENDER_ONLY_Opus, never exported)
# ---------------------------------------------------------------------------
world = bpy.data.worlds.new(f"Dusk_{SUFFIX}")
scene.world = world
try:
    world.use_nodes = True
except Exception:
    pass
wn_ = world.node_tree.nodes
wl_ = world.node_tree.links
bg = wn_["Background"]
tc = wn_.new("ShaderNodeTexCoord")
sep = wn_.new("ShaderNodeSeparateXYZ")
mr = wn_.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = -0.1
mr.inputs["From Max"].default_value = 0.8
ramp = wn_.new("ShaderNodeValToRGB")
wl_.new(tc.outputs["Generated"], sep.inputs[0])
wl_.new(sep.outputs["Z"], mr.inputs["Value"])
wl_.new(mr.outputs["Result"], ramp.inputs["Fac"])
cr = ramp.color_ramp
cr.elements[0].color = (*hexcol("#4B3F5E"), 1)
cr.elements[1].color = (*hexcol("#1E1A3A"), 1)
for pos, hx in ((0.12, "#F2B79A"), (0.28, "#C99AB8"), (0.55, "#7C6AA6")):
    e = cr.elements.new(pos)
    e.color = (*hexcol(hx), 1)
# stars
vor = wn_.new("ShaderNodeTexVoronoi")
vor.inputs["Scale"].default_value = 260
wl_.new(tc.outputs["Generated"], vor.inputs["Vector"])
star_r = wn_.new("ShaderNodeMapRange")
star_r.inputs["From Min"].default_value = 0.035
star_r.inputs["From Max"].default_value = 0.0
star_r.inputs["To Max"].default_value = 3.0
wl_.new(vor.outputs["Distance"], star_r.inputs["Value"])
starmix = wn_.new("ShaderNodeMix")
starmix.data_type = 'RGBA'
starmix.blend_type = 'ADD'
wl_.new(star_r.outputs["Result"], starmix.inputs["Factor"])
wl_.new(ramp.outputs["Color"], starmix.inputs[6])
starmix.inputs[7].default_value = (1.0, 0.95, 0.85, 1)
wl_.new(starmix.outputs[2], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 0.6
world_dusk = world

# A second world for the interior shots: dark space with stars, seen through the porthole.
world_space = bpy.data.worlds.new(f"Space_{SUFFIX}")
try:
    world_space.use_nodes = True
except Exception:
    pass
sn = world_space.node_tree.nodes
sl = world_space.node_tree.links
sbg = sn["Background"]
stc = sn.new("ShaderNodeTexCoord")
svor = sn.new("ShaderNodeTexVoronoi")
svor.inputs["Scale"].default_value = 150
sl.new(stc.outputs["Generated"], svor.inputs["Vector"])
srng = sn.new("ShaderNodeMapRange")
srng.inputs["From Min"].default_value = 0.05
srng.inputs["From Max"].default_value = 0.0
srng.inputs["To Max"].default_value = 1.0
sl.new(svor.outputs["Distance"], srng.inputs["Value"])
smix = sn.new("ShaderNodeMix")
smix.data_type = 'RGBA'
sl.new(srng.outputs["Result"], smix.inputs["Factor"])
smix.inputs[6].default_value = (*hexcol("#111433"), 1)
smix.inputs[7].default_value = (6.0, 5.6, 5.0, 1)
sl.new(smix.outputs[2], sbg.inputs["Color"])
sbg.inputs["Strength"].default_value = 1.0


def stage(ob):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    C_RENDER.objects.link(ob)
    return ob


def look(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat('-Z', 'Y').to_euler()


def light(name, kind, loc, power, hx, size=None, target=None, size_y=None):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = power
    ld.color = hexcol(hx)
    if kind == 'AREA':
        ld.shape = 'RECTANGLE'
        ld.size = size
        ld.size_y = size_y if size_y else size
    elif kind == 'SUN':
        ld.angle = math.radians(size or 2)
    elif size:
        ld.shadow_soft_size = size
    ob = bpy.data.objects.new(name, ld)
    C_RENDER.objects.link(ob)
    ob.location = loc
    if target is not None:
        look(ob, target)
    return ob


INTERIOR_LIGHTS = [
    light("L_CeilingPanel", 'AREA', (0, LP_Y, CEIL_Z - 0.09), 120, "#FFD9A3", 1.0, (0, LP_Y, 0), 0.45),
    light("L_FarFill", 'AREA', (0, 2.2, CEIL_Z - 0.12), 50, "#FFE2BD", 1.4, (0, 2.6, 0), 1.0),
    light("L_RearFill", 'AREA', (0, -3.3, CEIL_Z - 0.12), 35, "#FFE2BD", 1.0, (0, -2.4, 0), 1.0),
    light("L_StripRight", 'AREA', (1.32, -1.0, 2.17), 45, "#FFD9A3", 0.12, (1.32, -1.0, 0), 3.2),
    light("L_StripRight2", 'AREA', (1.32, 2.0, 2.17), 25, "#FFD9A3", 0.12, (1.32, 2.0, 0), 1.6),
    light("L_BunkLow", 'POINT', (-1.62, BY1 - 0.67, LOW_OPEN[1] - 0.14), 9, "#FFD9A3", 0.05),
    light("L_BunkUp", 'POINT', (-1.62, BY1 - 0.67, UP_OPEN[1] - 0.14), 9, "#FFD9A3", 0.05),
    light("L_Wash", 'POINT', (1.30, NY0 + 0.17, 1.95), 12, "#FFD9A3", 0.05),
]
EXT_LIGHTS = [
    light("L_SunDusk", 'SUN', (-20, 30, 8), 2.4, "#FFD8BE", 4, (0, 0, 0)),
    light("L_SkyFill", 'SUN', (20, -10, 25), 0.6, "#B7A6E0", 20, (0, 0, 0)),
]
TOP_LIGHT = light("L_TopSoftbox", 'AREA', (0, 0, 9), 1600, "#FFF0DD", 6, (0, 0, 0), 10)

bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=480, location=(636, 635, -500))
planet = stage(bpy.context.object)
planet.name = f"RENDER_Planet_{SUFFIX}"
pm = bpy.data.materials.new("M_Planet")
try:
    pm.use_nodes = True
except Exception:
    pass
pnt = pm.node_tree
pb = pnt.nodes["Principled BSDF"]
pnz = pnt.nodes.new("ShaderNodeTexNoise")
pnz.inputs["Scale"].default_value = 4
pnz.inputs["Detail"].default_value = 6
prr = pnt.nodes.new("ShaderNodeValToRGB")
prr.color_ramp.elements[0].color = (*hexcol("#2C4E86"), 1)
prr.color_ramp.elements[1].color = (*hexcol("#9FB7D6"), 1)
pnt.links.new(pnz.outputs["Fac"], prr.inputs[0])
pnt.links.new(prr.outputs["Color"], pb.inputs["Base Color"])
pnt.links.new(prr.outputs["Color"], pb.inputs["Emission Color"])
pb.inputs["Emission Strength"].default_value = 0.35
planet.data.materials.append(pm)
for p in planet.data.polygons:
    p.use_smooth = True

bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -0.002))
ground = stage(bpy.context.object)
ground.name = f"RENDER_Ground_{SUFFIX}"
gm = bpy.data.materials.new("M_Ground")
try:
    gm.use_nodes = True
except Exception:
    pass
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*hexcol("#8C7F99"), 1)
gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0
ground.data.materials.append(gm)


def camera(name, loc, target, lens, ortho=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.03
    cd.clip_end = 3000
    if ortho:
        cd.type = 'ORTHO'
        cd.ortho_scale = ortho
    ob = bpy.data.objects.new(name, cd)
    C_RENDER.objects.link(ob)
    ob.location = loc
    look(ob, target)
    return ob


CAM_MOCKUP = camera(f"CAM_MockupView_{SUFFIX}", (0.0, -3.86, 1.70), (0.05, 3.7, 1.32), 18)
CAM_CLOSE = camera(f"CAM_Closeup_{SUFFIX}", (-0.35, -2.75, 1.70), (1.45, -0.95, 1.30), 24)
CAM_EXT = camera(f"CAM_Exterior_{SUFFIX}", (8.6, 9.8, 4.6), (0, 0.2, 1.4), 30)
CAM_TOP = camera(f"CAM_TopDown_{SUFFIX}", (0, 0, 20), (0, 0, 0), 35, ortho=8.9)
CAM_TOP.rotation_euler = (0, 0, math.radians(90))
bpy.data.collections.remove(C_TMP)


# ---------------------------------------------------------------------------
# 17. SAVE + EXPORT
# ---------------------------------------------------------------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)
if DO_EXPORT:
    for ob in scene.objects:
        ob.select_set(False)
    for ob in list(C_SECTION.objects) + list(C_PROPS.objects) + list(C_COL.objects):
        ob.select_set(True)
    bpy.context.view_layer.objects.active = ob_hull
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(OUTPUT_DIR, f"quarters_{SUFFIX}.fbx"),
        use_selection=True, object_types={'MESH'},
        apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
        axis_forward='-Z', axis_up='Y', bake_space_transform=True,
        mesh_smooth_type='FACE', use_mesh_modifiers=True,
        add_leaf_bones=False, bake_anim=False)

scene.camera = CAM_MOCKUP
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTPUT_DIR, f"quarters_{SUFFIX}.blend"))
try:
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_mainfile()
except Exception as e:
    print("relative paths:", e)


# ---------------------------------------------------------------------------
# 18. RENDERS (Cycles, gentle bloom in the compositor)
# ---------------------------------------------------------------------------
def setup_render():
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 8
    scene.cycles.transparent_max_bounces = 8
    scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
    scene.render.resolution_percentage = RES
    scene.render.image_settings.file_format = 'PNG'
    try:
        scene.view_settings.view_transform = 'AgX'
        scene.view_settings.look = 'AgX - Base Contrast'
    except Exception:
        pass
    try:   # Blender 5: compositor is a node group
        tree = bpy.data.node_groups.new("Bloom", "CompositorNodeTree")
        tree.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
        rl = tree.nodes.new("CompositorNodeRLayers")
        gl = tree.nodes.new("CompositorNodeGlare")
        gl.inputs["Type"].default_value = 'Bloom'
        gl.inputs["Threshold"].default_value = 1.0
        gl.inputs["Strength"].default_value = 0.35
        gl.inputs["Size"].default_value = 0.6
        out = tree.nodes.new("NodeGroupOutput")
        tree.links.new(rl.outputs["Image"], gl.inputs["Image"])
        tree.links.new(gl.outputs["Image"], out.inputs[0])
        scene.compositing_node_group = tree
    except Exception as e:
        print("bloom skipped:", e)


def show(objs, visible):
    for o in objs:
        o.hide_render = not visible


def cutaway_copies(z_cut):
    temps = []
    for ob in section_objects:
        ob.hide_render = True
        if ob.name.endswith("Ceiling") or "CeilingLight" in ob.name or "Pipes" in ob.name:
            continue
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
        C_RENDER.objects.link(t)
        temps.append(t)
    return temps


def render(cam, fname, interior=True, ground_on=False, planet_on=True, top=False, exposure=0.0):
    scene.camera = cam
    scene.world = world_space if (interior and not top) else world_dusk
    show(INTERIOR_LIGHTS, interior)
    show(EXT_LIGHTS, not interior)
    TOP_LIGHT.hide_render = not top
    ground.hide_render = not ground_on
    planet.hide_render = not planet_on
    scene.view_settings.exposure = exposure
    scene.render.filepath = os.path.join(OUTPUT_DIR, fname)
    bpy.ops.render.render(write_still=True)
    print("Rendered", fname)


if DO_RENDER:
    setup_render()
    if ONLY in ("", "mockup"):
        render(CAM_MOCKUP, f"quarters_{SUFFIX}_mockup_view.png", exposure=0.0)
    if ONLY in ("", "closeup"):
        render(CAM_CLOSE, f"quarters_{SUFFIX}_closeup.png", exposure=0.0)
    if ONLY in ("", "exterior"):
        render(CAM_EXT, f"quarters_{SUFFIX}_exterior.png", interior=False, ground_on=True,
               planet_on=False, exposure=0.0)
    if ONLY in ("", "top"):
        cut = cutaway_copies(1.9)
        render(CAM_TOP, f"quarters_{SUFFIX}_topdown.png", interior=True, planet_on=False,
               top=True, exposure=0.0)
        for t in cut:
            bpy.data.objects.remove(t, do_unlink=True)
        show(section_objects, True)
print("Done.")
