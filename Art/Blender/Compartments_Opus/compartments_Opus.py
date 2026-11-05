"""
SHAKEDOWN - the six base compartments (generator, suffix "Opus")
================================================================

One parametric function, build_compartment(name, H, W, L), builds an EMPTY
compartment shell whose usable interior is H x W x L blocks of 1 m
(height Z x width X x length Y). It is called six times (Nook, Skylight, Cabin,
Bay, Hall, Gangway), so all six share exactly the same construction and style.
The look follows the corrected cockpit (Cockpit_v3_Opus): warm white and light-grey
painted metal with bevelled seams, gunmetal ribs and frames, copper pipes, orange
safety edges, watercolour textures, warm amber light strips.

LIBRARY USE: the furniture kit runs this file up to section 6 to reuse
compartment_geometry(), slot_list() and slot_object(), so wall panels have
exactly the slot shape and skin.

HOW TO RUN
  New Blender file > Scripting tab > New > paste > Run Script. The scene is
  cleared. Output goes to OUTPUT_DIR: compartments_Opus.blend, one FBX per
  compartment and the PNG renders. Rendering takes a while (Blender looks
  frozen); set DO_RENDER = False to only build and export.

GEOMETRY RULES (from Prompts / DEVLOG D-17..D-26)
  * Origin of a compartment = centre of its interior floor surface.
    Interior: X -W/2..W/2, Y -L/2..L/2, Z 0..H.  +Y = front.
  * Interior cross-section: square bottom edges, 0.5 x 0.5 m chamfer along both
    upper long edges. Walls/floor/ceiling 0.35 m thick, entirely outside.
  * The outer hull is the interior grown by 0.35 m, plus 0.5 m chamfers on the
    lower long edges.

HOW THE SLOTS ARE MADE (the important part)
  The 0.35 m shell is cut into pieces like a picture frame: every point of the
  shell belongs to the interior surface it is closest to "straight out from"
  (for a convex room that is the surface with the largest outward distance).
  Where two surfaces meet, the split is the 45-degree mitre between them.
  Each surface is then cut into 1 m cells along the block grid by planes at
  right angles to it. Every slot is therefore a closed convex block (or, for
  a Chamfer slot, two convex blocks welded together), clipped from a big box by
  a list of flat planes. Deleting a slot leaves a clean 1 x 1 m hole with
  closed edges, because each neighbour has its own closed side face there.
"""

import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix, Euler

# ---------------------------------------------------------------------------
# 0. SETTINGS
# ---------------------------------------------------------------------------
SUFFIX = "Opus"
OUTPUT_DIR = os.environ.get(
    "COMP_OUT", os.path.expanduser("~/Shakedown/Art/Blender/Compartments_Opus"))
TEX_DIR = os.path.normpath(os.path.join(OUTPUT_DIR, "..", "..", "Textures", "WatercolourTest"))
DO_EXPORT = True
DO_RENDER = os.environ.get("COMP_RENDER", "1") == "1"
SAMPLES = int(os.environ.get("COMP_SAMPLES", "48"))
RES = int(os.environ.get("COMP_RES", "100"))
ONLY = os.environ.get("COMP_ONLY", "")           # e.g. "lineup,slot_test" for test runs

T = 0.35            # wall / floor / ceiling thickness (outside the blocks)
CH_IN = 0.5         # interior upper chamfer (0.5 x 0.5 m)
CH_LOW = 0.5        # outer lower chamfer
RIB_W = 0.20        # rib width along Y
RIB_IN = 0.05       # rib protrusion into the room (max allowed 0.05)
RIB_OUT = 0.05      # hull ring protrusion outside
GAP = 1.6           # space between compartments in the line-up

COMPARTMENTS = [    # name, H, W, L  (blocks)
    ("Nook", 2, 2, 2),
    ("Skylight", 2, 4, 3),
    ("Cabin", 3, 4, 3),
    ("Bay", 4, 5, 4),
    ("Hall", 5, 6, 5),
    ("Gangway", 3, 2, 4),
]


# ---------------------------------------------------------------------------
# 1. CLEAR SCENE
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


def new_collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent.children if parent else scene.collection.children).link(c)
    return c


C_RENDER = new_collection(f"RENDER_ONLY_{SUFFIX}")
C_TMP = new_collection("TMP")


# ---------------------------------------------------------------------------
# 2. MATERIALS - same palette and watercolour chain as quarters_Opus.py
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
T_METAL = "tex_console_metal.png"
# Palette and materials of the corrected cockpit (Cockpit_v3_Opus, D-32): warm
# white and light-grey painted metal, gunmetal frames, orange accents, steel floor.
# The keys keep their old names so the construction code stays the same.
MAT = {
    "hull":       make_mat("M_Hull_WarmWhite",  "#DDD6CC", rough=0.7, tex=T_HULL, scale=0.5),
    "hull_sage":  make_mat("M_Hull_LightGrey",  "#B9B5AE", rough=0.7, tex=T_HULL, scale=0.5),
    "skirt":      make_mat("M_Hull_Gunmetal",   "#3E3D42", rough=0.55, metal=0.5, tex=T_METAL, scale=1.0),
    "wall":       make_mat("M_Panel_WarmWhite", "#DDD6CC", tex=T_WALL, scale=0.5),
    "wall_low":   make_mat("M_Panel_LightGrey", "#B9B5AE", tex=T_WALL, scale=0.5),
    "ceiling":    make_mat("M_Ceiling_LightGrey", "#B9B5AE", tex=T_WALL, scale=0.5),
    "floor":      make_mat("M_Floor_Steel",     "#4B4A4F", rough=0.6, metal=0.4, tex=T_FLOOR, scale=0.5),
    "recess":     make_mat("M_Gunmetal_Dark",   "#2B2A2E", rough=0.6, metal=0.4, tex=T_METAL, scale=1.0),
    "slate":      make_mat("M_Gunmetal",        "#3E3D42", rough=0.55, metal=0.5, tex=T_METAL, scale=1.0),
    "orange":     make_mat("M_Accent_Orange",   "#D9772B", rough=0.6, tex=T_METAL, scale=1.0),
    "ochre":      make_mat("M_Pipe_Copper",     "#8A4A30", rough=0.45, metal=0.6, tex=T_METAL, scale=1.0),
    "amber":      make_mat("M_Light_Amber",     "#FFC07A", emit=7.0),
    "amber_soft": make_mat("M_Light_AmberSoft", "#FFC07A", emit=3.0),
    "glass":      make_mat("M_Skylight_Glass",  "#7F9CA6", rough=0.03, alpha=0.10),
    "human":      make_mat("M_ScaleFigure",     "#3B3846", rough=0.9),
}


# ---------------------------------------------------------------------------
# 3. CONVEX POLYHEDRON CLIPPING (the slot maker)
#    A polyhedron is a list of faces; each face is a list of Vectors in
#    counter-clockwise order seen from outside. clip() keeps the part where
#    n . p <= d and closes the cut with a new face.
# ---------------------------------------------------------------------------
EPS = 1e-7


def box_poly(lo, hi):
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    c = [Vector(v) for v in [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]]
    idx = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return [[c[i] for i in f] for f in idx]


def _dedupe(pts, tol=1e-6):
    out = []
    for p in pts:
        if all((p - q).length > tol for q in out):
            out.append(p)
    return out


def _ring_clean(ring, tol=1e-6):
    out = []
    for p in ring:
        if not out or (p - out[-1]).length > tol:
            out.append(p)
    if len(out) > 1 and (out[0] - out[-1]).length <= tol:
        out.pop()
    return out


def _area(poly):
    a = Vector((0, 0, 0))
    for i in range(len(poly)):
        a += poly[i].cross(poly[(i + 1) % len(poly)])
    return a.length / 2


def clip(faces, n, d):
    n = Vector(n)
    ln = n.length
    n, d = n / ln, d / ln
    out, cut, coplanar = [], [], False
    for poly in faces:
        ds = [n.dot(p) - d for p in poly]
        if all(abs(x) < 1e-6 for x in ds):
            coplanar = True
            out.append(poly)
            continue
        res = []
        m = len(poly)
        for i in range(m):
            a, b = poly[i], poly[(i + 1) % m]
            da, db = ds[i], ds[(i + 1) % m]
            if da <= EPS:
                res.append(a)
                if abs(da) <= 1e-6:
                    cut.append(a)
            if (da < -EPS and db > EPS) or (da > EPS and db < -EPS):
                p = a.lerp(b, da / (da - db))
                res.append(p)
                cut.append(p)
        res = _ring_clean(res)
        if len(res) >= 3 and _area(res) > 1e-9:
            out.append(res)
    if not coplanar:
        pts = _dedupe(cut)
        if len(pts) >= 3:
            c = sum(pts, Vector()) / len(pts)
            u = (pts[0] - c).normalized()
            w = n.cross(u)
            pts.sort(key=lambda p: math.atan2((p - c).dot(w), (p - c).dot(u)))
            if _area(pts) > 1e-9:
                out.append(pts)
    return out


def polyhedron(planes, big):
    faces = box_poly(*big)
    for (n, d) in planes:
        faces = clip(faces, n, d)
        if not faces:
            break
    return faces


def on_plane(poly, n, d, tol=1e-5):
    n = Vector(n)
    ln = n.length
    return all(abs(n.dot(p) / ln - d / ln) < tol for p in poly)


# ---------------------------------------------------------------------------
# 4. SMALL MESH HELPERS
# ---------------------------------------------------------------------------
class MB:
    def __init__(self):
        self.bm = bmesh.new()
        self.keys = []

    def slot(self, key):
        if key not in self.keys:
            self.keys.append(key)
        return self.keys.index(key)

    def face(self, pts, key, normal=None):
        f = self.bm.faces.new([self.bm.verts.new(Vector(p)) for p in pts])
        f.material_index = self.slot(key)
        if normal is not None:
            f.normal_update()
            if f.normal.dot(Vector(normal)) < 0:
                f.normal_flip()
        return f

    def box(self, lo, hi, key, M=None):
        for poly in box_poly(lo, hi):
            pts = [M @ p for p in poly] if M is not None else poly
            self.face(pts, key)

    def box_c(self, centre, size, key, R=None):
        h = Vector(size) / 2
        M = Matrix.Translation(Vector(centre)) @ (R if R is not None else Matrix.Identity(4))
        self.box(-h, h, key, M)

    def cyl(self, a, b, r, key, sides=8):
        a, b = Vector(a), Vector(b)
        dv = (b - a).normalized()
        u = dv.cross(Vector((0, 0, 1)) if abs(dv.z) < 0.9 else Vector((1, 0, 0))).normalized()
        w = dv.cross(u)
        ra, rb = [], []
        for i in range(sides):
            ang = 2 * math.pi * (i + 0.5) / sides
            o = (u * math.cos(ang) + w * math.sin(ang)) * r
            ra.append(self.bm.verts.new(a + o))
            rb.append(self.bm.verts.new(b + o))
        fs = [self.bm.faces.new(ra[::-1]), self.bm.faces.new(rb)]
        for i in range(sides):
            j = (i + 1) % sides
            fs.append(self.bm.faces.new([ra[i], ra[j], rb[j], rb[i]]))
        for f in fs:
            f.material_index = self.slot(key)
        bmesh.ops.recalc_face_normals(self.bm, faces=fs)

    def ring(self, centre, axis, r_in, r_out, depth, key, sides=10):
        c, ax = Vector(centre), Vector(axis).normalized()
        u = ax.cross(Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0))).normalized()
        w = ax.cross(u)
        for i in range(sides):
            a0, a1 = 2 * math.pi * i / sides, 2 * math.pi * (i + 1) / sides
            pts = [c + (u * math.cos(a) + w * math.sin(a)) * r
                   for (a, r) in ((a0, r_in), (a1, r_in), (a1, r_out), (a0, r_out))]
            q0 = [self.bm.verts.new(p) for p in pts]
            q1 = [self.bm.verts.new(p + ax * depth) for p in pts]
            for f in (self.bm.faces.new(q0[::-1]), self.bm.faces.new(q1),
                      self.bm.faces.new([q0[2], q0[3], q1[3], q1[2]]),
                      self.bm.faces.new([q0[0], q0[1], q1[1], q1[0]])):
                f.material_index = self.slot(key)

    def finish(self, name, coll, location=(0, 0, 0)):
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-5)
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        for k in self.keys:
            me.materials.append(MAT[k])
        for p in me.polygons:
            p.use_smooth = False
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        ob.location = location
        return ob


def offset_poly(poly, dists):
    """Move edge i of a counter-clockwise (x, z) outline inwards by dists[i]."""
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
        if abs(den) < 1e-9:
            out.append((p2.x, p2.y))
            continue
        t = ((p2.x - p1.x) * e2.y - (p2.y - p1.y) * e2.x) / den
        v = p1 + e1 * t
        out.append((v.x, v.y))
    return out


def band(mb, poly, poly_in, y0, y1, key, skip=(0,), centre_z=1.0, key_for_edge=None):
    """A frame strip between two outlines (x, z), from y0 to y1 (a rib).
    key_for_edge(i) may colour single edges differently (orange safety edges)."""
    base_key = key
    for i in range(len(poly)):
        if i in skip:
            continue
        key = key_for_edge(i) if key_for_edge else base_key
        j = (i + 1) % len(poly)
        A0, A1, B0, B1 = (Vector(v) for v in (poly[i], poly[j], poly_in[i], poly_in[j]))

        def P(v, y):
            return Vector((v.x, y, v.y))
        mb.face([P(A0, y0), P(A1, y0), P(B1, y0), P(B0, y0)], key, normal=(0, -1, 0))
        mb.face([P(A0, y1), P(A1, y1), P(B1, y1), P(B0, y1)], key, normal=(0, 1, 0))
        mid_a, mid_b = (A0 + A1) / 2, (B0 + B1) / 2
        out_dir = mid_b - mid_a                # from poly towards poly_in
        mb.face([P(B0, y0), P(B1, y0), P(B1, y1), P(B0, y1)], key,
                normal=(out_dir.x, 0, out_dir.y))
        mb.face([P(A0, y0), P(A1, y0), P(A1, y1), P(A0, y1)], key,
                normal=(-out_dir.x, 0, -out_dir.y))


# ---------------------------------------------------------------------------
# 5. THE GENERATOR
# ---------------------------------------------------------------------------
# The slot construction is split into three reusable functions so that other
# scripts (the furniture kit) can build a slot of exactly the same shape:
#   compartment_geometry(H, W, L) -> the planes of one compartment
#   slot_list(name, H, W, L, ...)  -> every slot as (name, faces, owners, tags)
#   slot_object(...)               -> one finished slot object (materials, seams)
REPORT = {}
X, Y, Z = 0, 1, 2
s2 = math.sqrt(2)


class Geo:
    """All planes of one compartment of H x W x L blocks."""

    def __init__(self, H, W, L):
        self.H, self.W, self.L = H, W, L
        hw, hl = W / 2, L / 2
        self.hw, self.hl = hw, hl
        # Interior surfaces as planes: outward distance d_k(p) = n_k . p - c_k
        self.F = {
            "Right":   (Vector((1, 0, 0)), hw),
            "Left":    (Vector((-1, 0, 0)), hw),
            "Floor":   (Vector((0, 0, -1)), 0.0),
            "Ceiling": (Vector((0, 0, 1)), float(H)),
            "ChamR":   (Vector((1, 0, 1)) / s2, (hw + H - CH_IN) / s2),
            "ChamL":   (Vector((-1, 0, 1)) / s2, (hw + H - CH_IN) / s2),
            "Front":   (Vector((0, 1, 0)), hl),
            "Back":    (Vector((0, -1, 0)), hl),
        }
        # Outer hull (convex): interior grown by T, lower chamfers added.
        xo, zb, zt, yo = hw + T, -T, H + T, hl + T
        self.xo, self.zb, self.zt, self.yo = xo, zb, zt, yo
        self.OUTER = [
            ((1, 0, 0), xo), ((-1, 0, 0), xo), ((0, 0, 1), zt), ((0, 0, -1), T),
            ((0, 1, 0), yo), ((0, -1, 0), yo),
            ((1, 0, -1), xo - zb - CH_LOW), ((-1, 0, -1), xo - zb - CH_LOW),           # lower chamfers
            ((1, 0, 1), hw + H - CH_IN + T * s2), ((-1, 0, 1), hw + H - CH_IN + T * s2),  # upper
        ]
        self.LOWER_CH = self.OUTER[6:8]
        self.UPPER_CH = self.OUTER[8:10]
        self.BIG = ((-xo - 1, -yo - 1, zb - 1), (xo + 1, yo + 1, zt + 1))

    def owner_planes(self, k):
        """Half-spaces where surface k owns the shell: outside it, and further out
        from it than from any other surface (this gives the 45-degree mitres)."""
        nk, ck = self.F[k]
        pl = [(-nk, -ck)]                               # d_k >= 0
        for j, (nj, cj) in self.F.items():
            if j != k:
                pl.append((nj - nk, cj - ck))           # d_j <= d_k
        return pl

    def piece(self, k, cell):
        return polyhedron(self.OUTER + self.owner_planes(k) + cell, self.BIG)


def compartment_geometry(H, W, L):
    return Geo(H, W, L)


def _lo(axis, v):   # keep coordinate >= v
    n = [0, 0, 0]; n[axis] = -1
    return (tuple(n), -v)


def _hi(axis, v):   # keep coordinate <= v
    n = [0, 0, 0]; n[axis] = 1
    return (tuple(n), v)


def slot_list(name, g, skylight=False):
    """Every slot of a compartment as (slot name, faces, owner surfaces, tags)."""
    H, W, L, hw, hl = g.H, g.W, g.L, g.hw, g.hl
    slots = []
    # Long walls: columns along Y, rows along Z; top row = Chamfer slot.
    for side, cham in (("Right", "ChamR"), ("Left", "ChamL")):
        for c in range(L):
            if side == "Right":      # facing +X from inside, "left" is +Y
                ya, yb = hl - c - 1, hl - c
            else:                    # facing -X, "left" is -Y
                ya, yb = -hl + c, -hl + c + 1
            ycell = []
            if ya > -hl + 1e-9:
                ycell.append(_lo(Y, ya))
            if yb < hl - 1e-9:
                ycell.append(_hi(Y, yb))
            for r in range(H - 1):
                cell = list(ycell)
                if r > 0:
                    cell.append(_lo(Z, r))
                cell.append(_hi(Z, r + 1))
                slots.append((f"{name}_{side}_{c:02d}_{r:02d}", g.piece(side, cell), [side], {"row": r}))
            # Chamfer slot: top wall row + the chamfer face, welded along their mitre.
            wall_part = g.piece(side, ycell + [_lo(Z, H - 1)])
            cham_part = g.piece(cham, ycell)
            nk, ck = g.F[side]
            nj, cj = g.F[cham]
            mitre_n, mitre_d = nj - nk, cj - ck
            faces = [f for f in wall_part if not on_plane(f, mitre_n, mitre_d)] + \
                    [f for f in cham_part if not on_plane(f, mitre_n, mitre_d)]
            slots.append((f"{name}_{side}_{c:02d}_Chamfer", faces, [side, cham],
                          {"chamfer": True, "row": H - 1}))
    # End walls: columns along X, rows along Z.
    for side in ("Front", "Back"):
        for c in range(W):
            if side == "Front":      # facing +Y, "left" is -X
                xa, xb = -hw + c, -hw + c + 1
            else:                    # facing -Y, "left" is +X
                xa, xb = hw - c - 1, hw - c
            for r in range(H):
                cell = []
                if xa > -hw + 1e-9:
                    cell.append(_lo(X, xa))
                if xb < hw - 1e-9:
                    cell.append(_hi(X, xb))
                if r > 0:
                    cell.append(_lo(Z, r))
                if r < H - 1:
                    cell.append(_hi(Z, r + 1))
                slots.append((f"{name}_{side}_{c:02d}_{r:02d}", g.piece(side, cell), [side], {"row": r}))
    # Floor and ceiling: columns along X (left to right facing the front),
    # rows along Y (back to front).
    for side in ("Floor", "Ceiling"):
        for c in range(W):
            xa, xb = -hw + c, -hw + c + 1
            for r in range(L):
                ya, yb = -hl + r, -hl + r + 1
                cell = []
                if xa > -hw + 1e-9:
                    cell.append(_lo(X, xa))
                if xb < hw - 1e-9:
                    cell.append(_hi(X, xb))
                if ya > -hl + 1e-9:
                    cell.append(_lo(Y, ya))
                if yb < hl - 1e-9:
                    cell.append(_hi(Y, yb))
                slots.append((f"{name}_{side}_{c:02d}_{r:02d}", g.piece(side, cell), [side],
                              {"glass": skylight and side == "Ceiling"}))
    return slots


SEAM = 0.02          # bevel on the inner and outer edges of every slot = panel seams


def slot_object(sname, faces, owners, tags, g, coll, loc=(0, 0, 0)):
    """Turn one slot polyhedron into a finished object: painted-metal inner panel
    (warm white, light grey on the lowest row), gunmetal sides, warm white hull
    plate outside, 2 cm bevelled seams round the inner and outer faces, a gunmetal
    skirt low on the hull, a recessed light-grey panel on the upper chamfers and a
    short amber running light low on each long side."""
    mb = MB()
    kind = mb.bm.faces.layers.int.new("kind")       # 1 inner, 2 outer, 0 side
    inner_key_for = {"Floor": "floor", "Ceiling": "ceiling"}
    low_row = tags.get("row") == 0
    grey_panels, amber_faces = [], []
    for poly in faces:
        key, kd = "recess", 0
        for k in owners:
            nk, ck = g.F[k]
            if on_plane(poly, nk, ck):
                key, kd = inner_key_for.get(k, "wall_low" if low_row else "wall"), 1
        if kd == 0:
            for (n, d) in g.OUTER:
                if on_plane(poly, n, d):
                    key, kd = "hull", 2
        f = mb.face(poly, key)
        f[kind] = kd
        if kd == 2:
            if any(on_plane(poly, n, d) for (n, d) in g.LOWER_CH) or \
                    on_plane(poly, (0, 0, -1), T):
                f.material_index = mb.slot("skirt")
                if low_row and any(on_plane(poly, n, d) for (n, d) in g.LOWER_CH):
                    amber_faces.append(f)
            elif tags.get("chamfer") and any(on_plane(poly, n, d) for (n, d) in g.UPPER_CH):
                grey_panels.append(f)
    bmesh.ops.remove_doubles(mb.bm, verts=mb.bm.verts, dist=1e-5)
    # Seams: bevel only the rim of the inner and outer surfaces (edges between
    # an inner/outer face and a side face), never the folds inside a surface.
    edges = []
    for e in mb.bm.edges:
        ks = sorted(fc[kind] for fc in e.link_faces)
        if len(ks) == 2 and ks[0] == 0 and ks[1] in (1, 2):
            edges.append(e)
    if edges:
        bmesh.ops.bevel(mb.bm, geom=edges, offset=SEAM, segments=1, affect='EDGES',
                        material=mb.slot("recess"), clamp_overlap=True)
    if grey_panels:
        grey_panels = [f for f in grey_panels if f.is_valid]
        for f in grey_panels:
            f.material_index = mb.slot("hull_sage")
        r = bmesh.ops.inset_individual(mb.bm, faces=grey_panels, thickness=0.09, depth=-0.02,
                                       use_even_offset=True)
        for f in r["faces"]:
            f.material_index = mb.slot("hull")
    if amber_faces:
        amber_faces = [f for f in amber_faces if f.is_valid]
        for f in amber_faces:
            f.material_index = mb.slot("amber_soft")
        r = bmesh.ops.inset_individual(mb.bm, faces=amber_faces, thickness=0.12, depth=-0.012,
                                       use_even_offset=True)
        for f in r["faces"]:
            f.material_index = mb.slot("skirt")
    ob = mb.finish(sname, coll, loc)
    if tags.get("glass"):
        ob = make_glass_slot(ob, g.H)
    return ob


def build_compartment(name, H, W, L, x_offset=0.0, skylight=False):
    """Build one compartment. Returns its root collection."""
    root = new_collection(name)
    slots_col = new_collection(f"{name}_Slots", root)
    loc = Vector((x_offset, 0, 0))
    g = compartment_geometry(H, W, L)
    hw, hl, xo, zb, zt, yo = g.hw, g.hl, g.xo, g.zb, g.zt, g.yo

    tri_total = 0
    slot_objects = []
    for (sname, faces, owners, tags) in slot_list(name, g, skylight):
        ob = slot_object(sname, faces, owners, tags, g, slots_col, loc)
        ob.data.calc_loop_triangles()
        tri_total += len(ob.data.loop_triangles)
        slot_objects.append(ob)

    # --- Ribs: both ends and every 2nd block boundary along Y. Gunmetal; the end
    #     ribs carry orange safety edges on the lower legs (inside) and orange
    #     bands on the hull sides (outside), where compartments meet.
    inner_outline = [(-hw, 0.0), (hw, 0.0), (hw, 1.2), (hw, H - CH_IN), (hw - CH_IN, H),
                     (-hw + CH_IN, H), (-hw, H - CH_IN), (-hw, 1.2)]
    inner_rib = offset_poly(inner_outline, [0.0] + [RIB_IN] * 7)
    outer_outline = [(-(xo - CH_LOW), zb), (xo - CH_LOW, zb), (xo, zb + CH_LOW),
                     (xo, H - CH_IN + T * s2 - T), (hw - CH_IN + T * s2 - T, zt),
                     (-(hw - CH_IN + T * s2 - T), zt), (-xo, H - CH_IN + T * s2 - T),
                     (-xo, zb + CH_LOW)]
    outer_rib = offset_poly(outer_outline, [0.0] + [-RIB_OUT] * 7)
    rib_ys = sorted(set([-hl + k for k in range(0, L + 1, 2)] + [hl]))
    rib_objects = []
    for i, yb in enumerate(rib_ys):
        end = yb <= -hl + 1e-9 or yb >= hl - 1e-9
        if yb <= -hl + 1e-9:
            y0, y1 = -hl, -hl + RIB_W            # end rib sits inside the compartment
        elif yb >= hl - 1e-9:
            y0, y1 = hl - RIB_W, hl
        else:
            y0, y1 = yb - RIB_W / 2, yb + RIB_W / 2
        mb = MB()
        band(mb, inner_outline, inner_rib, y0, y1, "slate", skip=(0,),
             key_for_edge=(lambda e: "orange" if e in (1, 7) else "slate") if end else None)
        oy0 = -yo if yb <= -hl + 1e-9 else (yo - RIB_W if yb >= hl - 1e-9 else y0)
        oy1 = oy0 + RIB_W
        band(mb, outer_outline, outer_rib, oy0, oy1, "slate", skip=(0,),
             key_for_edge=(lambda e: "orange" if e in (2, 6) else "slate") if end else None)
        ob = mb.finish(f"{name}_Rib_{i:02d}", root, loc)
        rib_objects.append(ob)

    # --- Pipes along the upper RIGHT chamfer (quarters values relative to the chamfer):
    #     0.20 m out from the chamfer surface, 0.13 m either side of its middle, r 0.06.
    A, B = Vector((hw, H - CH_IN)), Vector((hw - CH_IN, H))
    mid, t = (A + B) / 2, (B - A).normalized()
    nrm = Vector((-t.y, t.x))                     # into the room
    pipe_pos = [mid + nrm * 0.20 + t * 0.13, mid + nrm * 0.20 - t * 0.13]
    mb = MB()
    for p in pipe_pos:
        mb.cyl((p.x, -hl, p.y), (p.x, hl, p.y), 0.06, "ochre", sides=10)
    ang = math.atan2(t.y, t.x)
    for yb in rib_ys:
        yc = (-hl + RIB_W / 2) if yb <= -hl + 1e-9 else ((hl - RIB_W / 2) if yb >= hl - 1e-9 else yb)
        bc = mid + nrm * 0.14
        mb.box_c((bc.x, yc, bc.y), (0.42, 0.08, 0.18), "slate", Matrix.Rotation(-ang, 4, 'Y'))
        for p in pipe_pos:
            mb.ring((p.x, yc - 0.035, p.y), (0, 1, 0), 0.062, 0.085, 0.07, "slate")
    pipes = mb.finish(f"{name}_Pipes", root, loc)

    # --- Light: warm strip along the ceiling centre line (Skylight: along the chamfers).
    mb = MB()
    seg_edges = [-hl + 0.15] + [y for y in rib_ys if -hl + 1e-9 < y < hl - 1e-9] + [hl - 0.15]
    for a_, b_ in zip(seg_edges[:-1], seg_edges[1:]):
        ya, yb = a_ + 0.15, b_ - 0.15
        if yb - ya < 0.2:
            continue
        if not skylight:
            mb.box((-0.10, ya, H - 0.035), (0.10, yb, H), "slate")
            mb.box((-0.07, ya + 0.02, H - 0.045), (0.07, yb - 0.02, H - 0.035), "amber")
        else:
            for sx in (1, -1):
                pa = Vector((hw, H - CH_IN)) + Vector((-0.707, 0.707)) * 0.14
                c = Vector((sx * pa.x, 0, pa.y))
                n_in = Vector((-sx * 0.707, 0, -0.707))
                R = Matrix.Rotation(sx * math.radians(45), 4, 'Y')
                mb.box_c(c + n_in * 0.015 + Vector((0, (ya + yb) / 2, 0)), (0.16, yb - ya, 0.03), "slate", R)
                mb.box_c(c + n_in * 0.032 + Vector((0, (ya + yb) / 2, 0)), (0.11, yb - ya - 0.04, 0.006), "amber", R)
    light = mb.finish(f"{name}_Light", root, loc)

    # --- Report
    tris = tri_total
    for ob in rib_objects + [pipes, light]:
        ob.data.calc_loop_triangles()
        tris += len(ob.data.loop_triangles)
    REPORT[name] = {"H": H, "W": W, "L": L, "slots": len(slot_objects),
                    "slots_by_face": {}, "tris": tris, "tris_slots": tri_total,
                    "ribs": len(rib_objects), "x_offset": x_offset}
    for ob in slot_objects:
        face = ob.name.split("_")[1]
        REPORT[name]["slots_by_face"][face] = REPORT[name]["slots_by_face"].get(face, 0) + 1
    return root


def make_glass_slot(ob, H):
    """Skylight ceiling slot: keep a 0.08 m frame through the whole thickness and
    put a glass pane in the middle. Same object, same name."""
    me = ob.data
    vs = [v.co.copy() for v in me.vertices]
    inner = [p for p in me.polygons if p.normal.z < -0.99 and
             all(abs(me.vertices[i].co.z - H) < 1e-5 for i in p.vertices)][0]
    ring = [me.vertices[i].co.copy() for i in inner.vertices]
    # inset outline (x, y) by 0.08 m
    c = sum(ring, Vector()) / len(ring)
    xs = [p.x for p in ring]
    ys = [p.y for p in ring]
    x0, x1, y0, y1 = min(xs) + 0.08, max(xs) - 0.08, min(ys) + 0.08, max(ys) - 0.08
    cut = MB()
    cut.box((x0, y0, H - 0.5), (x1, y1, H + 1.0), "glass")
    cob = cut.finish("TMP_glasscut", C_TMP, ob.location)
    mod = ob.modifiers.new("hole", 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cob
    mod.solver = 'EXACT'
    dg = bpy.context.evaluated_depsgraph_get()
    new_me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob.modifiers.clear()
    bpy.data.objects.remove(cob, do_unlink=True)
    bm = bmesh.new()
    bm.from_mesh(new_me)
    mats = [m for m in new_me.materials]
    # recolour the new opening's sides as frame (slate)
    if MAT["slate"] not in mats:
        new_me.materials.append(MAT["slate"])
        mats.append(MAT["slate"])
    si = mats.index(MAT["slate"])
    for f in bm.faces:
        cc = f.calc_center_median()
        if (abs(cc.x - x0) < 1e-4 or abs(cc.x - x1) < 1e-4 or abs(cc.y - y0) < 1e-4 or
                abs(cc.y - y1) < 1e-4) and abs(f.normal.z) < 0.1:
            f.material_index = si
    if MAT["glass"] not in mats:
        new_me.materials.append(MAT["glass"])
        mats.append(MAT["glass"])
    gi = mats.index(MAT["glass"])
    zg = H + T / 2
    vv = [bm.verts.new((x, y, zg)) for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    gf = bm.faces.new(vv)
    gf.material_index = gi
    bm.to_mesh(new_me)
    bm.free()
    old = ob.data
    ob.data = new_me
    new_me.name = ob.name
    for p in new_me.polygons:
        p.use_smooth = False
    bpy.data.meshes.remove(old)
    return ob


# ---------------------------------------------------------------------------
# 6. BUILD ALL SIX, SIDE BY SIDE ALONG X
# ---------------------------------------------------------------------------
roots = {}
x = 0.0
prev_half = None
for (nm, H, W, L) in COMPARTMENTS:
    half = W / 2 + T + RIB_OUT
    if prev_half is not None:
        x += prev_half + GAP + half
    roots[nm] = build_compartment(nm, H, W, L, x_offset=x, skylight=(nm == "Skylight"))
    prev_half = half
LINE_CENTRE = x / 2


# ---------------------------------------------------------------------------
# 7. SLOT CHECK: every slot must be a closed solid (no open edges)
# ---------------------------------------------------------------------------
open_slots = []
for nm in roots:
    for ob in bpy.data.collections[f"{nm}_Slots"].objects:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        if nm == "Skylight" and "_Ceiling_" in ob.name:
            # the glass pane is a single loose face by design; check the frame only
            glass_faces = [f for f in bm.faces if ob.data.materials[f.material_index] == MAT["glass"]]
            bmesh.ops.delete(bm, geom=glass_faces, context='FACES')
        if any(not e.is_manifold for e in bm.edges):
            open_slots.append(ob.name)
        bm.free()

print("\n--- Compartment report ---")
for nm, r in REPORT.items():
    print(f"{nm:9s} {r['H']}x{r['W']}x{r['L']}  slots {r['slots']:4d}  tris {r['tris']:6d} "
          f"(slots {r['tris_slots']})  ribs {r['ribs']}  {r['slots_by_face']}")
print("Open (non-closed) slots:", open_slots if open_slots else "none")


# ---------------------------------------------------------------------------
# 8. RENDER STAGING (RENDER_ONLY_Opus; never exported)
# ---------------------------------------------------------------------------
world = bpy.data.worlds.new(f"Dusk_{SUFFIX}")
scene.world = world
try:
    world.use_nodes = True
except Exception:
    pass
wn, wl = world.node_tree.nodes, world.node_tree.links
bg = wn["Background"]
tc = wn.new("ShaderNodeTexCoord")
sep = wn.new("ShaderNodeSeparateXYZ")
mr = wn.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = -0.1
mr.inputs["From Max"].default_value = 0.8
ramp = wn.new("ShaderNodeValToRGB")
wl.new(tc.outputs["Generated"], sep.inputs[0])
wl.new(sep.outputs["Z"], mr.inputs["Value"])
wl.new(mr.outputs["Result"], ramp.inputs["Fac"])
cr = ramp.color_ramp
cr.elements[0].color = (*hexcol("#4B3F5E"), 1)
cr.elements[1].color = (*hexcol("#1E1A3A"), 1)
for pos, hx in ((0.12, "#F2B79A"), (0.28, "#C99AB8"), (0.55, "#7C6AA6")):
    e = cr.elements.new(pos)
    e.color = (*hexcol(hx), 1)
vor = wn.new("ShaderNodeTexVoronoi")
vor.inputs["Scale"].default_value = 260
wl.new(tc.outputs["Generated"], vor.inputs["Vector"])
star_r = wn.new("ShaderNodeMapRange")
star_r.inputs["From Min"].default_value = 0.035
star_r.inputs["From Max"].default_value = 0.0
star_r.inputs["To Max"].default_value = 3.0
wl.new(vor.outputs["Distance"], star_r.inputs["Value"])
starmix = wn.new("ShaderNodeMix")
starmix.data_type = 'RGBA'
starmix.blend_type = 'ADD'
wl.new(star_r.outputs["Result"], starmix.inputs["Factor"])
wl.new(ramp.outputs["Color"], starmix.inputs[6])
starmix.inputs[7].default_value = (1.0, 0.95, 0.85, 1)
wl.new(starmix.outputs[2], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 0.6


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


ROOM_LIGHTS = {}
for (nm, H, W, L) in COMPARTMENTS:
    ox = REPORT[nm]["x_offset"]
    area = W * L
    ROOM_LIGHTS[nm] = [
        light(f"L_{nm}_Soft", 'AREA', (ox, 0, H - 0.12), 16 * area, "#FFD9A3",
              max(0.6, W - 1.0), (ox, 0, 0), max(0.6, L - 0.8)),
        light(f"L_{nm}_Fill", 'POINT', (ox, -L / 2 + 0.6, min(1.6, H - 0.4)), 6 * H, "#FFE6C8", 0.4),
    ]
SUN = light("L_SunDusk", 'SUN', (-25, 30, 10), 2.4, "#FFD8BE", 4, (0, 0, 0))
FILL = light("L_SkyFill", 'SUN', (20, -15, 25), 0.6, "#B7A6E0", 20, (0, 0, 0))

bpy.ops.mesh.primitive_plane_add(size=400, location=(LINE_CENTRE, 0, -T - 0.002))
ground = bpy.context.object
ground.name = f"RENDER_Ground_{SUFFIX}"
for c in list(ground.users_collection):
    c.objects.unlink(ground)
C_RENDER.objects.link(ground)
gm = bpy.data.materials.new("M_Ground")
try:
    gm.use_nodes = True
except Exception:
    pass
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*hexcol("#8C7F99"), 1)
gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0
ground.data.materials.append(gm)

# 1.8 m scale figure (simple faceted silhouette), standing in front of the Cabin.
fig = MB()
hx = REPORT["Cabin"]["x_offset"]
fy = REPORT["Cabin"]["L"] / 2 + T + 1.4
gz = -T
for sx in (-0.11, 0.11):                                  # legs
    fig.box((hx + sx - 0.07, fy - 0.08, gz), (hx + sx + 0.07, fy + 0.08, gz + 0.86), "human")
fig.box((hx - 0.21, fy - 0.12, gz + 0.84), (hx + 0.21, fy + 0.12, gz + 1.48), "human")   # torso
for sx in (-0.27, 0.27):                                  # arms
    fig.box((hx + sx - 0.055, fy - 0.06, gz + 0.80), (hx + sx + 0.055, fy + 0.06, gz + 1.45), "human")
fig.box((hx - 0.06, fy - 0.06, gz + 1.48), (hx + 0.06, fy + 0.06, gz + 1.56), "human")   # neck
fig.cyl((hx, fy, gz + 1.56), (hx, fy, gz + 1.80), 0.11, "human", sides=8)              # head
figure = fig.finish(f"RENDER_ScaleFigure_1p8m_{SUFFIX}", C_RENDER)


def camera(name, loc, target, lens, ortho=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.03
    cd.clip_end = 3000
    ob = bpy.data.objects.new(name, cd)
    C_RENDER.objects.link(ob)
    ob.location = loc
    look(ob, target)
    return ob


cams = {}
for (nm, H, W, L) in COMPARTMENTS:
    ox = REPORT[nm]["x_offset"]
    eye = min(1.7, H - 0.15)
    cams[nm] = camera(f"CAM_{nm}_Interior", (ox, -L / 2 + 0.12, eye),
                      (ox, L / 2, max(eye - 0.25, H * 0.5)), 14)
cams["lineup"] = camera("CAM_Lineup", (LINE_CENTRE - 11, 25, 8.5), (LINE_CENTRE + 1.0, 0, 1.0), 30)
cx = REPORT["Cabin"]["x_offset"]
cams["slot_test"] = camera("CAM_SlotTest", (cx + 5.2, -3.6, 2.2), (cx + 2.0, 0.0, 1.0), 30)
bpy.data.collections.remove(C_TMP)


# ---------------------------------------------------------------------------
# 9. SAVE + EXPORT (one FBX per compartment, origin = its floor centre)
# ---------------------------------------------------------------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)


def all_objects(col):
    obs = list(col.objects)
    for ch in col.children:
        obs += all_objects(ch)
    return obs


if DO_EXPORT:
    for nm, root in roots.items():
        obs = all_objects(root)
        for o in scene.objects:
            o.select_set(False)
        saved = [o.location.copy() for o in obs]
        for o in obs:
            o.location = (0, 0, 0)
            o.select_set(True)
        bpy.context.view_layer.objects.active = obs[0]
        bpy.ops.export_scene.fbx(
            filepath=os.path.join(OUTPUT_DIR, f"compartment_{nm}.fbx"),
            use_selection=True, object_types={'MESH'},
            apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL',
            axis_forward='-Z', axis_up='Y', bake_space_transform=True,
            mesh_smooth_type='FACE', use_mesh_modifiers=True,
            add_leaf_bones=False, bake_anim=False)
        for o, l in zip(obs, saved):
            o.location = l

scene.camera = cams["lineup"]
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTPUT_DIR, f"compartments_{SUFFIX}.blend"))
try:
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_mainfile()
except Exception as e:
    print("relative paths:", e)


# ---------------------------------------------------------------------------
# 10. RENDERS
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
    try:
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


def set_visible(only=None, ground_on=False, figure_on=False, sun_on=False, rooms_lit=()):
    for nm, root in roots.items():
        for o in all_objects(root):
            o.hide_render = (only is not None and nm not in only)
    for nm, ls in ROOM_LIGHTS.items():
        for l in ls:
            l.hide_render = nm not in rooms_lit
    ground.hide_render = not ground_on
    figure.hide_render = not figure_on
    SUN.hide_render = not sun_on
    FILL.hide_render = not sun_on


def render(cam, fname, exposure=0.0):
    scene.camera = cam
    scene.view_settings.exposure = exposure
    scene.render.filepath = os.path.join(OUTPUT_DIR, fname)
    bpy.ops.render.render(write_still=True)
    print("Rendered", fname)


def wanted(tag):
    return not ONLY or tag in ONLY.split(",")


if DO_RENDER:
    setup_render()
    if wanted("lineup"):
        set_visible(None, ground_on=True, figure_on=True, sun_on=True, rooms_lit=tuple(roots))
        render(cams["lineup"], "lineup.png")
    if wanted("slot_test"):
        set_visible(["Cabin"], ground_on=True, figure_on=False, sun_on=True, rooms_lit=("Cabin",))
        removed = [bpy.data.objects["Cabin_Right_01_00"], bpy.data.objects["Cabin_Right_01_01"]]
        for o in removed:
            o.hide_render = True
        render(cams["slot_test"], "slot_test.png")
        for o in removed:
            o.hide_render = False
    for (nm, H, W, L) in COMPARTMENTS:
        if wanted(nm):
            set_visible([nm], ground_on=False, figure_on=False, sun_on=(nm == "Skylight"),
                        rooms_lit=(nm,))
            render(cams[nm], f"{nm}_interior.png")
    set_visible(None)
print("Done.")
