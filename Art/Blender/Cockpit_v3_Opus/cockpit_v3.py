"""
SHAKEDOWN - Cockpit v3 ("grounded watercolour"), suffix Opus
============================================================

Builds the ship's cockpit: the interior after mockup_cockpit_v3.png and
Lars' cockpit_sketch_01.png, and the faceted nose of the delta-wing ship
(concept_sheet_deltawing.png) on the outside.

HOW TO RUN
  New Blender file > Scripting > New > paste > Run Script. Clears the scene,
  writes cockpit_v3.blend, cockpit_v3.fbx and four PNG renders to OUTPUT_DIR.
  Rendering takes several minutes; set DO_RENDER = False to only build.

SIZE AND AXES
  Interior bounding box 3 x 3 x 5 blocks: X -1.5..1.5, Y -2.5..2.5, Z 0..3.
  Origin = centre of the interior floor. Front = +Y. 1 unit = 1 m.

HOW IT IS BUILT
  * The room (cavity) is a convex shape: a compartment-like rear part (square
    floor edges, 0.5 m chamfers at the ceiling) that tapers from y = 0.5 into
    a narrower nose at y = 2.5. All its faces are flat planes.
  * The outer hull = every cavity plane pushed 0.35 m outward, plus the 0.5 m
    lower chamfers of the compartments. So walls are 0.35 m everywhere and
    the rear end is exactly a compartment's outer hull.
  * Shell = outer hull minus cavity minus five window openings minus the rear
    wall region, using Boolean (Exact). The wall left between the openings
    becomes the gunmetal canopy frames.
  * The rear wall is made of 1 x 1 m slot objects, Cockpit_Back_cc_rr, built
    with the same mitred clipping as compartments_Opus.py, so Unity can cut a
    doorway by removing two stacked slots.
  * Textures: watercolour PNGs, Box projection, multiplied with base colours.
    Only the screens, the picture and the pinboard prints use a simple UV
    on a flat card, because they show an image.
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
OUTPUT_DIR = os.environ.get("CP_OUT", os.path.expanduser("~/Shakedown/Art/Blender/Cockpit_v3_Opus"))
TEX_DIR = os.path.normpath(os.path.join(OUTPUT_DIR, "..", "..", "Textures", "WatercolourTest"))
DO_RENDER = os.environ.get("CP_RENDER", "1") == "1"
SAMPLES = int(os.environ.get("CP_SAMPLES", "48"))
RES = int(os.environ.get("CP_RES", "100"))
ONLY = os.environ.get("CP_ONLY", "")

T = 0.35                 # wall thickness everywhere
HW, HL, H = 1.5, 2.5, 3.0
CH = 0.5                 # interior upper chamfer (as the compartments)
SILL = 1.2               # bottom of the canopy windows
Y_CANOPY = 0.6           # where the plan taper of the nose starts (= windscreen top)
FRAME = 0.14             # canopy strut half-width left around each pane
T_BASE = T - 0.035       # outer base surface; hull plates (<= 3.5 cm) bring it back to 0.35 m
RIB_W, RIB_IN = 0.20, 0.05

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


def new_collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent.children if parent else scene.collection.children).link(c)
    return c


C_BUILT = new_collection("Cockpit")
C_SLOTS = new_collection("Cockpit_Slots", C_BUILT)
C_PROPS = new_collection("Props_Cockpit")
C_COL = new_collection("COL_Cockpit")
C_RENDER = new_collection("RENDER_ONLY")
C_TMP = new_collection("TMP")

# ---------------------------------------------------------------------------
# 2. MATERIALS (palette from the brief; watercolour chain as in the compartments)
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
    m = bpy.data.materials.new(name)
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


TW, TH, TF = "tex_interior_wall.png", "tex_hull_plating.png", "tex_floor.png"
TM, TU = "tex_console_metal.png", "tex_upholstery.png"
MAT = {
    "white":    make_mat("M_Panel_WarmWhite", "#DDD6CC", tex=TW, scale=0.5),
    "grey":     make_mat("M_Panel_LightGrey", "#B9B5AE", tex=TW, scale=0.5),
    "hull":     make_mat("M_Hull_WarmWhite",  "#DDD6CC", rough=0.7, tex=TH, scale=0.5),
    "hull_grey": make_mat("M_Hull_LightGrey", "#B9B5AE", rough=0.7, tex=TH, scale=0.5),
    "gun":      make_mat("M_Gunmetal",        "#3E3D42", rough=0.55, metal=0.5, tex=TM, scale=1.0),
    "gun_dark": make_mat("M_Gunmetal_Dark",   "#2B2A2E", rough=0.6, metal=0.4, tex=TM, scale=1.0),
    "orange":   make_mat("M_Accent_Orange",   "#D9772B", rough=0.6, tex=TM, scale=1.0),
    "hull_orange": make_mat("M_Hull_Orange",  "#D9772B", rough=0.65, tex=TH, scale=0.5),
    "steel":    make_mat("M_Floor_Steel",     "#4B4A4F", rough=0.6, metal=0.4, tex=TF, scale=0.5),
    "grate":    make_mat("M_Floor_Grate",     "#2E2D31", rough=0.6, metal=0.5, tex=TM, scale=1.0),
    "counter":  make_mat("M_Counter_Top",     "#9E9A94", rough=0.55, metal=0.2, tex=TM, scale=1.0),
    "copper":   make_mat("M_Pipe_Copper",     "#8A4A30", rough=0.45, metal=0.6, tex=TM, scale=1.0),
    "leather":  make_mat("M_Chair_Leather",   "#B4683A", rough=0.55, tex=TU, scale=2.0),
    "cork":     make_mat("M_Cork",            "#A8834F", rough=0.95, tex=TU, scale=2.0),
    "rug_base": make_mat("M_Rug_Wool",        "#8A4A3A", rough=1.0, tex=TU, scale=2.0),
    "rug_light": make_mat("M_Rug_Cream",      "#CDBFA6", rough=1.0, tex=TU, scale=2.0),
    "rug_dark": make_mat("M_Rug_Dark",        "#5C2A27", rough=1.0, tex=TU, scale=2.0),
    "book_r":   make_mat("M_Book_Red",        "#6E3B34", tex=TU, scale=2.0),
    "book_b":   make_mat("M_Book_Navy",       "#3B4660", tex=TU, scale=2.0),
    "book_g":   make_mat("M_Book_Olive",      "#5E6248", tex=TU, scale=2.0),
    "book_br":  make_mat("M_Book_Brown",      "#6B5040", tex=TU, scale=2.0),
    "paper":    make_mat("M_Paper",           "#E8E1D2", rough=0.9),
    "ceramic":  make_mat("M_Mug_Ceramic",     "#E6E1D8", rough=0.35, tex=TW, scale=2.0),
    "coffee":   make_mat("M_Coffee",          "#3A2A22", rough=0.2),
    "leaf":     make_mat("M_Leaf",            "#5F7F3E", rough=0.6),
    "leaf_dark": make_mat("M_LeafDark",       "#46602E", rough=0.6),
    "pot":      make_mat("M_Pot",             "#8E847A", rough=0.8, tex=TW, scale=2.0),
    "amber":    make_mat("M_Light_Amber",     "#FFC07A", emit=7.0),
    "lamp":     make_mat("M_Lamp_Glow",       "#FFC07A", emit=9.0),
    "headlight": make_mat("M_Headlight",      "#FFC07A", emit=3.5),
    "led_amber": make_mat("M_LED_Amber",      "#FFB060", emit=5.0),
    "led_green": make_mat("M_LED_Green",      "#7FE0B0", emit=4.0),
    "glass":    make_mat("M_Canopy_Glass",    "#7F9CA6", rough=0.03, alpha=0.10),
    "screen_glass": make_mat("M_Screen_Bezel", "#1B1D1F", rough=0.3, metal=0.2),
    "collider": make_mat("M_Collider",        "#FF00FF", alpha=0.25),
}


def image_material(name, img, emit=0.0):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img
    b = nt.nodes["Principled BSDF"]
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.5
    if emit:
        nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = emit
    return m


# ---------------------------------------------------------------------------
# 3. GEOMETRY TOOLKIT (mesh builder + convex clipping from compartments_Opus.py)
# ---------------------------------------------------------------------------
EPS = 1e-7


def rot(rx=0.0, ry=0.0, rz=0.0):
    return Euler((math.radians(rx), math.radians(ry), math.radians(rz))).to_matrix().to_4x4()


def box_poly(lo, hi):
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    c = [Vector(v) for v in [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]]
    return [[c[i] for i in f] for f in
            [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]]


def _dedupe(pts, tol=1e-6):
    out = []
    for p in pts:
        if all((p - q).length > tol for q in out):
            out.append(p)
    return out


def _ring_clean(r, tol=1e-6):
    out = []
    for p in r:
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
    n = Vector(n); ln = n.length; n, d = n / ln, d / ln
    out, cut, coplanar = [], [], False
    for poly in faces:
        ds = [n.dot(p) - d for p in poly]
        if all(abs(x) < 1e-6 for x in ds):
            coplanar = True; out.append(poly); continue
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
                p = a.lerp(b, da / (da - db)); res.append(p); cut.append(p)
        res = _ring_clean(res)
        if len(res) >= 3 and _area(res) > 1e-9:
            out.append(res)
    if not coplanar:
        pts = _dedupe(cut)
        if len(pts) >= 3:
            c = sum(pts, Vector()) / len(pts)
            u = (pts[0] - c).normalized(); w = n.cross(u)
            pts.sort(key=lambda p: math.atan2((p - c).dot(w), (p - c).dot(u)))
            if _area(pts) > 1e-9:
                out.append(pts)
    return out


def polyhedron(planes, big=((-8, -8, -4), (8, 8, 8))):
    faces = box_poly(*big)
    for (n, d) in planes:
        faces = clip(faces, n, d)
    return faces


def on_plane(poly, n, d, tol=1e-4):
    n = Vector(n); ln = n.length
    return all(abs(n.dot(p) / ln - d / ln) < tol for p in poly)


class MB:
    def __init__(self):
        self.bm = bmesh.new()
        self.keys = []
        self.uv_faces = []

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

    def poly(self, faces, key):
        for p in faces:
            self.face(p, key)

    def box(self, lo, hi, key, M=None):
        for p in box_poly(lo, hi):
            self.face([M @ v for v in p] if M is not None else p, key)

    def box_c(self, c, size, key, R=None):
        h = Vector(size) / 2
        M = Matrix.Translation(Vector(c)) @ (R if R is not None else Matrix.Identity(4))
        self.box(-h, h, key, M)

    def prism(self, profile, offset, key):
        off = Vector(offset)
        a = [self.bm.verts.new(Vector(p)) for p in profile]
        b = [self.bm.verts.new(Vector(p) + off) for p in profile]
        fs = [self.bm.faces.new(a), self.bm.faces.new(b[::-1])]
        for i in range(len(a)):
            j = (i + 1) % len(a)
            fs.append(self.bm.faces.new([a[i], a[j], b[j], b[i]]))
        for f in fs:
            f.material_index = self.slot(key)
        bmesh.ops.recalc_face_normals(self.bm, faces=fs)
        return fs

    def cyl(self, a, b, r, key, sides=8, r2=None):
        a, b = Vector(a), Vector(b)
        dv = (b - a).normalized()
        u = dv.cross(Vector((0, 0, 1)) if abs(dv.z) < 0.9 else Vector((1, 0, 0))).normalized()
        w = dv.cross(u)
        r2 = r if r2 is None else r2
        ra, rb = [], []
        for i in range(sides):
            ang = 2 * math.pi * (i + 0.5) / sides
            o = u * math.cos(ang) + w * math.sin(ang)
            ra.append(self.bm.verts.new(a + o * r)); rb.append(self.bm.verts.new(b + o * r2))
        fs = [self.bm.faces.new(ra[::-1]), self.bm.faces.new(rb)]
        for i in range(sides):
            j = (i + 1) % sides
            fs.append(self.bm.faces.new([ra[i], ra[j], rb[j], rb[i]]))
        for f in fs:
            f.material_index = self.slot(key)
        bmesh.ops.recalc_face_normals(self.bm, faces=fs)

    def card(self, centre, right, up, w, h, key):
        """A flat image card with UVs (screens, pictures, prints)."""
        c, r, u = Vector(centre), Vector(right).normalized(), Vector(up).normalized()
        pts = [c - r * w / 2 - u * h / 2, c + r * w / 2 - u * h / 2,
               c + r * w / 2 + u * h / 2, c - r * w / 2 + u * h / 2]
        f = self.face(pts, key, normal=r.cross(u))
        self.uv_faces.append((f, pts, r, u, w, h))
        return f

    def finish(self, name, coll, origin=None):
        if self.uv_faces:
            uvl = self.bm.loops.layers.uv.new("UVMap")
            for (f, pts, r, u, w, h) in self.uv_faces:
                c = sum(pts, Vector()) / 4
                for l in f.loops:
                    d = l.vert.co - c
                    l[uvl].uv = (d.dot(r) / w + 0.5, d.dot(u) / h + 0.5)
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-5)
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


def faces_to_mb(faces, key):
    mb = MB()
    mb.poly(faces, key)
    return mb


def boolean_difference(base_ob, cutter_obs):
    for co in cutter_obs:
        m = base_ob.modifiers.new(co.name, 'BOOLEAN')
        m.operation = 'DIFFERENCE'
        m.object = co
        m.solver = 'EXACT'
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(base_ob.evaluated_get(dg))
    for co in cutter_obs:
        bpy.data.objects.remove(co, do_unlink=True)
    bpy.data.objects.remove(base_ob, do_unlink=True)
    return me


def offset_poly(poly, dists):
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
            out.append((p2.x, p2.y)); continue
        t = ((p2.x - p1.x) * e2.y - (p2.y - p1.y) * e2.x) / den
        v = p1 + e1 * t
        out.append((v.x, v.y))
    return out


def base_centre(mb):
    vs = [v.co for v in mb.bm.verts]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))


# ---------------------------------------------------------------------------
# 4. THE ROOM SHAPE (cavity) AND THE OUTER HULL
# ---------------------------------------------------------------------------
# Side profile (correction round): full 3.0 m height from Y -2.5 to -1.0 (the
# walk-in rear, matching the compartments), then the roof slopes down to 2.2 m
# at Y +0.6, where a windscreen raked about 42 degrees runs down to Y +2.0,
# Z 0.95, just above the console. In front of it a long, low hood (section 8).
# Cross-section: full width up to shoulder height, then the canopy sides lean
# inward ("lean" facets) to a roof about 2.2 m wide. All faces are flat planes,
# the cavity is their intersection (n . p <= d, n pointing out).
s2 = math.sqrt(2)
NOSE_HW = 0.9                     # interior half-width at the front (floor level)
Y_NOSE = HL
Y_ROOF0, Y_WS_TOP, Z_WS_TOP = -1.0, 0.6, 2.2
Y_WS_BOT, Z_WS_BOT = 2.0, 0.95


def plane(n, p):
    n = Vector(n).normalized()
    return (n, n.dot(Vector(p)))


def plane3(a, b, c, outward):
    a, b, c = Vector(a), Vector(b), Vector(c)
    n = (b - a).cross(c - a)
    if n.dot(Vector(outward)) < 0:
        n = -n
    return plane(n, a)


CAV = {
    "floor": plane((0, 0, -1), (0, 0, 0)), "ceil": plane((0, 0, 1), (0, 0, H)),
    "side_R": plane((1, 0, 0), (HW, 0, 0)), "side_L": plane((-1, 0, 0), (-HW, 0, 0)),
    "cham_R": plane((1, 0, 1), (HW, 0, H - CH)), "cham_L": plane((-1, 0, 1), (-HW, 0, H - CH)),
    "back": plane((0, -1, 0), (0, -HL, 0)), "front": plane((0, 1, 0), (0, Y_NOSE, 0)),
    "taper_R": plane((Y_NOSE - Y_CANOPY, HW - NOSE_HW, 0), (HW, Y_CANOPY, 0)),
    "taper_L": plane((-(Y_NOSE - Y_CANOPY), HW - NOSE_HW, 0), (-HW, Y_CANOPY, 0)),
    "roof": plane3((0, Y_ROOF0, H), (1, Y_ROOF0, H), (0, Y_WS_TOP, Z_WS_TOP), (0, 0.3, 1)),
    "ws": plane3((0, Y_WS_TOP, Z_WS_TOP), (1, Y_WS_TOP, Z_WS_TOP), (0, Y_WS_BOT, Z_WS_BOT), (0, 1, 1)),
}
for sx, nm in ((1, "lean_R"), (-1, "lean_L")):
    # touches the compartment profile only at its top wall corner at Y -1.0,
    # reaches the roof edge (x 1.1, z 2.2) at the windscreen top.
    CAV[nm] = plane3((sx * HW, Y_ROOF0, H - CH), (sx * HW, Y_WS_TOP, 1.2),
                     (sx * 1.1, Y_WS_TOP, Z_WS_TOP), (sx, 0, 0.5))
CAV_PLANES = list(CAV.values())
WIN_NAMES = ("lean_R", "lean_L", "roof", "ws")
WS_N = CAV["ws"][0]
cav_faces = polyhedron([(tuple(n), d) for (n, d) in CAV_PLANES])

xo, zb = HW + T_BASE, -T_BASE
OUT = {k: (n, d + T_BASE) for k, (n, d) in CAV.items()}
OUT["lowch_R"] = ((1 / s2, 0, -1 / s2), (xo - zb - 0.5) / s2)
OUT["lowch_L"] = ((-1 / s2, 0, -1 / s2), (xo - zb - 0.5) / s2)
OUTER_PLANES = list(OUT.values())
outer_faces = polyhedron([(tuple(n), d) for (n, d) in OUTER_PLANES])


def plane_name(poly, table):
    for k, (n, d) in table.items():
        if on_plane(poly, n, d):
            return k
    return None


def wall_x(y):
    """Interior half-width at floor level for a given y (walls taper in the nose)."""
    if y <= Y_CANOPY:
        return HW
    return HW + (NOSE_HW - HW) * (y - Y_CANOPY) / (Y_NOSE - Y_CANOPY)


# ---------------------------------------------------------------------------
# 5. WINDOW OPENINGS AND GLASS
#    Side windows on the lean facets (above 1.2 m), two roof windows on the
#    sloping roof (split by a centre strut), one wide raked windscreen.
# ---------------------------------------------------------------------------
def simplify(poly, min_edge=0.03, min_turn=0.02):
    """Drop tiny edges and nearly straight corners left over from clipping."""
    pts = list(poly)
    changed = True
    while changed and len(pts) > 3:
        changed = False
        for i in range(len(pts)):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
            e1, e2 = b - a, c - b
            if e1.length < min_edge or e1.normalized().cross(e2.normalized()).length < min_turn:
                pts.pop(i)
                changed = True
                break
    return pts


def frame2d(poly, n):
    c = sum(poly, Vector()) / len(poly)
    u = (poly[1] - poly[0]).normalized()
    w = n.cross(u)
    flat = [((p - c).dot(u), (p - c).dot(w)) for p in poly]
    area = sum(flat[i][0] * flat[(i + 1) % len(flat)][1] - flat[(i + 1) % len(flat)][0] * flat[i][1]
               for i in range(len(flat)))
    if area < 0:
        flat = flat[::-1]
    return c, u, w, flat


def pane(poly, n):
    poly = simplify(poly)
    c, u, w, flat = frame2d(poly, n)
    ins = offset_poly(flat, [FRAME] * len(flat))
    return [c + u * a + w * b for (a, b) in ins], n


PANES = []
for poly in cav_faces:
    nm = plane_name(poly, CAV)
    if nm not in WIN_NAMES:
        continue
    n, d = CAV[nm]
    parts = [poly]
    if nm.startswith("lean"):
        parts = clip(parts, (0, 0, -1), -1.2)
    if nm == "ws":
        parts = clip(parts, (0, 0, -1), -Z_WS_BOT)
    parts = [q for q in parts if on_plane(q, n, d)]
    if nm == "roof":
        sub = []
        for q in parts:
            for (pn, pd) in (((1, 0, 0), 0.0), ((-1, 0, 0), 0.0)):
                sub += [r for r in clip([q], pn, pd) if on_plane(r, n, d)]
        parts = sub
    for q in parts:
        PANES.append(pane(q, n))
print("window panes:", len(PANES))


# ---------------------------------------------------------------------------
# 6. REAR WALL SLOTS (compartment end-wall construction, H 3 x W 3)
# ---------------------------------------------------------------------------
F = {
    "Right": (Vector((1, 0, 0)), HW), "Left": (Vector((-1, 0, 0)), HW),
    "Floor": (Vector((0, 0, -1)), 0.0), "Ceiling": (Vector((0, 0, 1)), H),
    "ChamR": (Vector((1, 0, 1)) / s2, (HW + H - CH) / s2),
    "ChamL": (Vector((-1, 0, 1)) / s2, (HW + H - CH) / s2),
    "Front": (Vector((0, 1, 0)), HL), "Back": (Vector((0, -1, 0)), HL),
}
COMP_OUTER = [((1, 0, 0), xo), ((-1, 0, 0), xo), ((0, 0, 1), H + T), ((0, 0, -1), T),
              ((0, 1, 0), HL + T), ((0, -1, 0), HL + T),
              ((1, 0, -1), xo - zb - 0.5), ((-1, 0, -1), xo - zb - 0.5),
              ((1, 0, 1), HW + H - CH + T * s2), ((-1, 0, 1), HW + H - CH + T * s2)]


def owner_planes(k):
    nk, ck = F[k]
    pl = [(tuple(-nk), -ck)]
    for j, (nj, cj) in F.items():
        if j != k:
            pl.append((tuple(nj - nk), cj - ck))
    return pl


slot_objects = []
for c in range(3):
    xa, xb = HW - c - 1, HW - c              # facing -Y from inside, "left" is +X
    for r in range(3):
        cell = []
        if xa > -HW + 1e-9:
            cell.append(((-1, 0, 0), -xa))
        if xb < HW - 1e-9:
            cell.append(((1, 0, 0), xb))
        if r > 0:
            cell.append(((0, 0, -1), -r))
        if r < 2:
            cell.append(((0, 0, 1), r + 1))
        faces = polyhedron(COMP_OUTER + owner_planes("Back") + cell)
        mb = MB()
        for p in faces:
            if on_plane(p, (0, -1, 0), HL):
                key = "white"
            elif any(on_plane(p, n, d) for (n, d) in COMP_OUTER):
                key = "hull"
            else:
                key = "gun_dark"
            mb.face(p, key)
        slot_objects.append(mb.finish(f"Cockpit_Back_{c:02d}_{r:02d}", C_SLOTS))

# Cutter for the shell: the whole rear-wall region (slightly larger on the outside
# so the Boolean never meets coplanar faces).
back_region = polyhedron([(n, d + 0.02) for (n, d) in COMP_OUTER] + owner_planes("Back"))

# ---------------------------------------------------------------------------
# 7. THE SHELL: outer minus cavity minus windows minus rear wall, then split
# ---------------------------------------------------------------------------
outer_ob = faces_to_mb(outer_faces, "hull").finish("TMP_outer", C_TMP)
cutters = [faces_to_mb(polyhedron([(tuple(n), d) for (n, d) in CAV_PLANES]), "white").finish("TMP_cav", C_TMP),
           faces_to_mb(back_region, "white").finish("TMP_back", C_TMP)]
def grown(pts, n, d):
    c, u, w, flat = frame2d(pts, n)
    g = offset_poly(flat, [-d] * len(flat))
    return [c + u * a + w * b for (a, b) in g]


for i, (pts, n) in enumerate(PANES):
    # the opening widens toward the outside, so the jambs read as chamfers
    hull_pts = [p - n * 0.15 for p in pts] + [p + n * (T_BASE + 0.2) for p in grown(pts, n, 0.05)]
    bmw = bmesh.new()
    for p in hull_pts:
        bmw.verts.new(p)
    bmesh.ops.convex_hull(bmw, input=bmw.verts[:])
    me = bpy.data.meshes.new(f"TMP_win{i}")
    bmw.to_mesh(me); bmw.free()
    ob = bpy.data.objects.new(f"TMP_win{i}", me)
    C_TMP.objects.link(ob)
    cutters.append(ob)
shell_me = boolean_difference(outer_ob, cutters)

src = bmesh.new()
src.from_mesh(shell_me)
classes = {"Hull": [], "Interior": [], "Floor": [], "Ceiling": []}
fkey = {}
for f in src.faces:
    c = f.calc_center_median()
    pts = [v.co for v in f.verts]
    inner = plane_name(pts, CAV)
    outer = plane_name(pts, OUT)
    if inner:
        n = CAV[inner][0]
        if inner == "floor":
            classes["Floor"].append(f.index); fkey[f.index] = "steel"
        elif inner == "ceil":
            classes["Ceiling"].append(f.index); fkey[f.index] = "grey"
        else:
            classes["Interior"].append(f.index)
            fkey[f.index] = "gun" if inner in WIN_NAMES else ("white" if c.z > 0.95 else "grey")
    elif outer:
        classes["Hull"].append(f.index)
        # window faces = gunmetal canopy struts; plated faces show dark seams
        fkey[f.index] = "gun" if outer in WIN_NAMES else "gun_dark"
    else:                             # window jambs, rear-wall mitre faces
        jamb = c.y > Y_ROOF0 - 0.1 and c.z > 0.9
        classes["Hull" if jamb else "Interior"].append(f.index)
        fkey[f.index] = "gun" if jamb else "gun_dark"

built = []


def split(cls, name):
    keep = set(classes[cls])
    bm = src.copy()
    bm.faces.ensure_lookup_table()
    mb = MB()
    for f in bm.faces:
        if f.index in keep:
            f.material_index = mb.slot(fkey[f.index])
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES')
    mb.bm.free()
    mb.bm = bm
    ob = mb.finish(name, C_BUILT)
    built.append(ob)
    return ob


ob_hull = split("Hull", "Cockpit_Hull")
ob_inner = split("Interior", "Cockpit_Interior")
split("Floor", "Cockpit_Floor")
split("Ceiling", "Cockpit_Ceiling")
src.free()
bpy.data.meshes.remove(shell_me)

# Glass panes in the middle of the wall thickness.
gl = MB()
for (pts, n) in PANES:
    gl.face([p + n * (T / 2) for p in pts], "glass", normal=n)
built.append(gl.finish("Cockpit_Canopy", C_BUILT))

# ---------------------------------------------------------------------------
# 8. EXTERIOR: hood, bumper, intakes, sensor, canopy struts, hull plating
# ---------------------------------------------------------------------------
def convex_faces(points):
    bmh = bmesh.new()
    for p in points:
        bmh.verts.new(Vector(p))
    bmesh.ops.convex_hull(bmh, input=bmh.verts[:])
    bmesh.ops.dissolve_limit(bmh, angle_limit=math.radians(0.5), verts=bmh.verts[:], edges=bmh.edges[:])
    bmh.normal_update()
    out = []
    for f in bmh.faces:
        out.append(([v.co.copy() for v in f.verts], f.normal.copy()))
    bmh.free()
    return out


def mirror_pts(half):
    pts = []
    for (x, y, z) in half:
        pts += [(x, y, z), (-x, y, z)]
    return pts


# Hood: a long, low wedge in front of the windscreen, top 0.9 m sloping to 0.64.
HOOD_Y0, HOOD_Y1 = 2.60, 3.30
HOOD = convex_faces(mirror_pts([
    (1.10, HOOD_Y0, 0.90), (1.22, HOOD_Y0, 0.78), (1.22, HOOD_Y0, 0.05), (0.95, HOOD_Y0, -0.30),
    (0.86, HOOD_Y1, 0.64), (0.96, HOOD_Y1, 0.54), (0.96, HOOD_Y1, 0.02), (0.70, HOOD_Y1, -0.16)]))
nose = MB()
for (poly, n) in HOOD:
    nose.face(poly, "gun_dark", normal=n)

# Bumper housing at the tip with two recessed amber headlights (Boolean recesses).
BUMP = convex_faces(mirror_pts([
    (1.00, 3.24, -0.14), (1.00, 3.24, 0.58),
    (0.94, 3.47, -0.02), (0.88, 3.47, -0.08), (0.88, 3.47, 0.52), (0.94, 3.47, 0.46)]))
bmb = MB()
for (poly, n) in BUMP:
    bmb.face(poly, "gun", normal=n)
bump_ob = bmb.finish("TMP_bumper", C_TMP)
recs = []
for sx in (-1, 1):
    r = MB()
    xa, xb = sorted((sx * 0.14, sx * 0.80))
    r.box((xa, 3.39, 0.13), (xb, 3.60, 0.37), "gun")
    recs.append(r.finish("TMP_rec", C_TMP))
bump_me = boolean_difference(bump_ob, recs)
bmx = bmesh.new()
bmx.from_mesh(bump_me)
for f in bmx.faces:
    f.material_index = nose.slot("gun_dark") if (abs(f.calc_center_median().y - 3.39) < 0.005 or
                                                 (f.calc_center_median().y > 3.39 and f.calc_center_median().y < 3.47 - 0.005)) \
        else nose.slot("gun")
bmx.to_mesh(bump_me)
bmx.free()
start = len(nose.bm.faces)
mats_b = [nose.keys.index("gun_dark"), nose.keys.index("gun")]
nose.bm.from_mesh(bump_me)
bpy.data.meshes.remove(bump_me)
for sx in (-1, 1):                                    # the lamps inside the recesses
    xa, xb = sorted((sx * 0.20, sx * 0.74))
    nose.face([Vector((xa, 3.395, 0.18)), Vector((xb, 3.395, 0.18)),
               Vector((xb, 3.395, 0.32)), Vector((xa, 3.395, 0.32))], "headlight", normal=(0, 1, 0))
    nose.box((min(sx * 0.46, sx * 0.48), 3.39, 0.13), (max(sx * 0.46, sx * 0.48), 3.44, 0.37), "gun_dark")


def side_frame(sx, faces):
    """Local frame on the hood side face: u along the face (forward), v up, n out."""
    poly, n = max(faces, key=lambda f: sx * f[1].x)
    n = n.normalized()
    u = Vector((0, 1, 0)) - n * n.y
    u.normalize()
    v = n.cross(u)
    if v.z < 0:
        v = -v
    return poly, n, u, v


AVOID = []
# Side air intakes just behind the bumper: dark grille in a gunmetal frame.
for sx in (-1, 1):
    poly, n, u, v = side_frame(sx, HOOD)
    o = Vector((sx * 1.0, 2.98, 0.24))
    o = o - n * (n.dot(o) - n.dot(poly[0]))          # onto the side face
    M = Matrix((u, v, n)).transposed().to_4x4()
    M.translation = o
    nose.box(Vector((-0.24, -0.10, 0.0)), Vector((0.24, 0.10, 0.012)), "grate", M)
    for k in range(5):
        z0 = -0.085 + k * 0.038
        nose.box(Vector((-0.22, z0, 0.012)), Vector((0.22, z0 + 0.012, 0.022)), "gun", M)
    for (a, b) in (((-0.28, -0.14), (0.28, -0.10)), ((-0.28, 0.10), (0.28, 0.14)),
                   ((-0.28, -0.10), (-0.24, 0.10)), ((0.24, -0.10), (0.28, 0.10))):
        nose.box(Vector((a[0], a[1], 0.0)), Vector((b[0], b[1], 0.03)), "gun", M)
    AVOID.append((o, 0.36, 0.2, n))

# Sensor plate on top of the hood.
top_poly, top_n = max(HOOD, key=lambda f: f[1].z)
top_n = top_n.normalized()
u = Vector((1, 0, 0))
v = top_n.cross(u)
o = Vector((0, 2.98, 1.0))
o = o - top_n * (top_n.dot(o) - top_n.dot(top_poly[0]))
M = Matrix((u, v, top_n)).transposed().to_4x4()
M.translation = o
nose.box(Vector((-0.20, -0.14, 0.0)), Vector((0.20, 0.14, 0.03)), "gun", M)
nose.box(Vector((-0.16, -0.10, 0.03)), Vector((0.16, 0.10, 0.034)), "gun_dark", M)
nose.box(Vector((-0.05, -0.05, 0.034)), Vector((0.05, 0.05, 0.044)), "led_green", M)
AVOID.append((o, 0.28, 0.2, top_n))
built.append(nose.finish("Cockpit_Nose", C_BUILT))

# Canopy struts: a raised, chamfered gunmetal frame around every window opening.
fr = MB()
WIN_OUTLINES = []          # (normal, outer strut outline) so plates stop at the struts
for (pts, n) in PANES:
    e_out = 0.05 * (T_BASE + 0.15) / (T_BASE + 0.35)
    base = grown(pts, n, e_out)
    off = n * T_BASE
    c, u, w, flat = frame2d(base, n)
    rings = {}
    for key, d in (("A", 0.0), ("TA", 0.02), ("TB", 0.09), ("B", 0.11)):
        g = offset_poly(flat, [-d] * len(flat))
        h = 0.03 if key in ("TA", "TB") else 0.0
        rings[key] = [c + off + u * a + w * b + n * h for (a, b) in g]
    WIN_OUTLINES.append((n.copy(), [q - n * 0.0 for q in rings["B"]]))
    m = len(flat)
    for i in range(m):
        j = (i + 1) % m
        A, TA, TB, B = rings["A"], rings["TA"], rings["TB"], rings["B"]
        e_mid = (B[i] + B[j]) / 2 - (A[i] + A[j]) / 2
        fr.face([A[i], A[j], TA[j], TA[i]], "gun", normal=n - e_mid.normalized())
        fr.face([TA[i], TA[j], TB[j], TB[i]], "gun", normal=n)
        fr.face([TB[i], TB[j], B[j], B[i]], "gun", normal=n + e_mid.normalized())
built.append(fr.finish("Cockpit_CanopyFrames", C_BUILT))


# Hull plating: every non-window outer face is split into plates of 0.5-1.2 m,
# 2 cm seams, bevelled top edges, some plates raised, sparse hex bolts,
# orange diagonal bands, a gunmetal skirt and underside.
def clip2d(subject, clipper):
    """Clip a convex 2D polygon by a convex counter-clockwise clipper."""
    out = subject
    m = len(clipper)
    for i in range(m):
        a, b = Vector(clipper[i]), Vector(clipper[(i + 1) % m])
        e = b - a
        inp, out = out, []
        if not inp:
            break
        for k in range(len(inp)):
            P, Q = Vector(inp[k]), Vector(inp[(k + 1) % len(inp)])
            sp = e.x * (P.y - a.y) - e.y * (P.x - a.x)
            sq = e.x * (Q.y - a.y) - e.y * (Q.x - a.x)
            if sp >= 0:
                out.append((P.x, P.y))
            if (sp >= 0) != (sq >= 0):
                t = sp / (sp - sq)
                out.append((P.x + (Q.x - P.x) * t, P.y + (Q.y - P.y) * t))
    return dedupe2d(out)


def dedupe2d(p, tol=1e-5):
    out = []
    for q in p:
        if not out or math.dist(q, out[-1]) > tol:
            out.append(q)
    if len(out) > 1 and math.dist(out[0], out[-1]) <= tol:
        out.pop()
    return out


def area2d(p):
    return 0.5 * sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1]
                     for i in range(len(p)))


def clip_half(poly, g, c):
    """Keep the part of a convex 2D polygon where g . p <= c (None if empty)."""
    if not poly:
        return None
    out = []
    m = len(poly)
    for k in range(m):
        P, Q = poly[k], poly[(k + 1) % m]
        dp = g[0] * P[0] + g[1] * P[1] - c
        dq = g[0] * Q[0] + g[1] * Q[1] - c
        if dp <= 0:
            out.append(P)
        if (dp < 0 < dq) or (dq < 0 < dp):
            t = dp / (dp - dq)
            out.append((P[0] + (Q[0] - P[0]) * t, P[1] + (Q[1] - P[1]) * t))
    out = dedupe2d(out)
    return out if len(out) >= 3 and abs(area2d(out)) > 1e-4 else None


def cuts(lo, hi, rng, step=(0.6, 1.15), forced=()):
    c = [lo]
    x = lo
    while x < hi:
        x += rng.uniform(*step)
        if hi - x < 0.4:
            x = hi
        c.append(min(x, hi))
    for f in forced:
        if lo + 0.2 < f < hi - 0.2:
            c = [v for v in c if abs(v - f) > 0.25] + [f]
    return sorted(set(c))


def bands_for(n):
    """Orange paint bands (Sx, Sy, Sz, s0, s1): orange where s0 <= S . p <= s1.
    Sx is mirrored on the -X half, so the bands are symmetric chevrons/diagonals."""
    if n.z > 0.6:
        return "top", [(1.1, 1.0, 0.0, -2.25, -1.55), (1.1, 1.0, 0.0, 3.0, 3.6)]
    if abs(n.x) > 0.3 and n.z > -0.3:
        return "side", [(0.0, 1.0, -0.9, -2.75, -1.85), (0.0, 1.0, -0.9, -0.75, 0.05),
                        (0.0, 1.0, -0.9, 2.25, 2.7)]
    return None, []


plates = MB()
rng = random.Random(17)
n_plates = n_bolts = 0


def plate_one(cell, bands, o, u, v, n, z_skirt, lin):
    """One hull plate: 2 cm seam, bevelled top, maybe raised, maybe bolted."""
    global n_plates, n_bolts
    per = sum(math.dist(cell[k], cell[(k + 1) % len(cell)]) for k in range(len(cell)))
    if abs(area2d(cell)) < 0.02 or abs(area2d(cell)) / per < 0.06:      # skip slivers
        return
    raw = cell
    cell = offset_poly(cell, [0.01] * len(cell))                           # 2 cm seams
    rc = (sum(a for a, b in raw) / len(raw), sum(b for a, b in raw) / len(raw))
    rmax = max(math.dist(q, rc) for q in raw)
    cen = o + u * rc[0] + v * rc[1]
    if any((cen - ao).length < r_ and abs(n.dot(an)) > 0.95 for (ao, r_, _, an) in AVOID):
        return
    skirt = n.z < -0.3 or (abs(n.z) < 0.5 and cen.z < z_skirt)
    raised = not skirt and rng.random() < 0.3
    h = 0.006 if skirt else (0.032 if raised else 0.016)
    bev = 0.012 if skirt else 0.022
    key = "gun" if skirt else ("hull_grey" if rng.random() < 0.25 else "hull")
    top = offset_poly(cell, [bev] * len(cell))
    if abs(area2d(top)) < 0.004 or max(math.dist(q, rc) for q in top) > rmax:
        top = offset_poly(cell, [0.004] * len(cell))
    if max(math.dist(q, rc) for q in cell + top) > rmax + 0.01:            # mitre spikes
        return
    B = [o + u * a + v * b - n * 0.002 for (a, b) in cell]
    Tp = [o + u * a + v * b + n * h for (a, b) in top]
    plates.face(Tp, key, normal=n)
    # orange paint: diagonal bands laid over the plate tops like a painted livery
    if not skirt:
        for side in (1, -1):
            gx, cx = lin((side, 0, 0))
            half = clip_half(top, (-gx[0], -gx[1]), cx)          # the part with side * x >= 0
            for (sxv, sy, sz, s0, s1) in bands:
                g, off = lin((sxv * side, sy, sz))
                part = clip_half(clip_half(half, g, s1 - off), (-g[0], -g[1]), -(s0 - off))
                if part:
                    plates.face([o + u * a + v * b + n * (h + 0.0015) for (a, b) in part],
                                "hull_orange", normal=n)
    for k in range(len(cell)):
        l = (k + 1) % len(cell)
        mid = (B[k] + B[l]) / 2 - cen
        plates.face([B[k], B[l], Tp[l], Tp[k]], key, normal=mid.normalized() + n * 0.3)
    n_plates += 1
    if not raised and not skirt and rng.random() < 0.35:                  # sparse bolt pair
        for cp in [Tp[k] for k in rng.sample(range(len(Tp)), min(2, len(Tp)))]:
            pb = cp + (cen + n * h - cp).normalized() * 0.07
            plates.cyl(pb, pb + n * 0.008, 0.013, "gun", sides=6)
            n_bolts += 1


def plate_faces(poly, n, z_skirt=0.18):
    n = Vector(n).normalized()
    u = Vector((0, 1, 0)) - n * n.y
    if u.length < 0.2:
        u = Vector((1, 0, 0)) - n * n.x
    u.normalize()
    v = n.cross(u)
    o = poly[0]

    def to2(P):
        return ((P - o).dot(u), (P - o).dot(v))

    def lin(S):                                   # world linear form S . p -> 2D (g, offset)
        S = Vector(S)
        return (S.dot(u), S.dot(v)), S.dot(o)

    flat = [to2(p) for p in poly]
    if area2d(flat) < 0:
        flat = flat[::-1]
    us = [a for a, b in flat]
    vs = [b for a, b in flat]
    forced_v = [(z_skirt - o.z) / v.z] if abs(v.z) > 0.3 else []
    cu = cuts(min(us), max(us), rng)
    cv = cuts(min(vs), max(vs), rng, (0.55, 1.0), forced_v)
    wins = []
    for (wn, ring) in WIN_OUTLINES:
        if (wn - n).length < 1e-3:
            w2 = [to2(q) for q in ring]
            wins.append(w2 if area2d(w2) > 0 else w2[::-1])
    kind, bands = bands_for(n)
    for i in range(len(cu) - 1):
        for j in range(len(cv) - 1):
            rect = [(cu[i], cv[j]), (cu[i + 1], cv[j]), (cu[i + 1], cv[j + 1]), (cu[i], cv[j + 1])]
            cell = clip2d(rect, flat)
            if len(cell) < 3 or abs(area2d(cell)) < 0.02:
                continue
            pieces = [(cell, False)]
            for wpoly in wins:                    # leave the canopy struts free
                new = []
                for (pc, orx) in pieces:
                    rem = pc
                    for k in range(len(wpoly)):
                        A_, B_ = wpoly[k], wpoly[(k + 1) % len(wpoly)]
                        g = (B_[1] - A_[1], -(B_[0] - A_[0]))      # outward edge normal
                        c0 = g[0] * A_[0] + g[1] * A_[1]
                        out_part = clip_half(rem, (-g[0], -g[1]), -c0)
                        if out_part:
                            new.append((out_part, orx))
                        rem = clip_half(rem, g, c0)
                        if rem is None:
                            break
                pieces = new
            for (pc, orx) in pieces:
                plate_one(pc, bands, o, u, v, n, z_skirt, lin)


for poly in outer_faces:
    nm = plane_name(poly, OUT)
    if nm in ("back", "front"):
        continue
    plate_faces(poly, OUT[nm][0])
for (poly, n) in HOOD:
    if n.y > 0.9 or n.y < -0.9:                       # hood front (behind bumper), hood back (hidden)
        continue
    plate_faces(poly, n, z_skirt=0.06)
# small amber running lights on the skirt
for sx in (-1, 1):
    xa, xb = sorted((sx * (xo + 0.004), sx * (xo + 0.012)))
    plates.box((xa, -0.30, 0.26), (xb, 0.10, 0.31), "led_amber")
    plates.box((xa, -2.55, 0.26), (xb, -2.25, 0.31), "led_amber")
print(f"hull plates: {n_plates}, bolts: {n_bolts}")
built.append(plates.finish("Cockpit_HullPlates", C_BUILT))

# ---------------------------------------------------------------------------
# 9. RIBS (rear end frame with orange safety stripes, a mid rib, canopy rib)
# ---------------------------------------------------------------------------
COMP_IN = [(-HW, 0), (HW, 0), (HW, H - CH), (HW - CH, H), (-HW + CH, H), (-HW, H - CH)]
COMP_IN_RIB = offset_poly(COMP_IN, [0.0] + [RIB_IN] * 5)


def band(mb, poly, poly_in, y0, y1, key, skip=(0,)):
    for i in range(len(poly)):
        if i in skip:
            continue
        j = (i + 1) % len(poly)
        A0, A1, B0, B1 = (Vector(v) for v in (poly[i], poly[j], poly_in[i], poly_in[j]))

        def P(v, y):
            return Vector((v.x, y, v.y))
        mb.face([P(A0, y0), P(A1, y0), P(B1, y0), P(B0, y0)], key, normal=(0, -1, 0))
        mb.face([P(A0, y1), P(A1, y1), P(B1, y1), P(B0, y1)], key, normal=(0, 1, 0))
        d = (B0 + B1) / 2 - (A0 + A1) / 2
        mb.face([P(B0, y0), P(B1, y0), P(B1, y1), P(B0, y1)], key, normal=(d.x, 0, d.y))


ribs = MB()
band(ribs, COMP_IN, COMP_IN_RIB, -HL, -HL + RIB_W, "white")
for sx in (-1, 1):            # orange safety stripes on the rear frame legs
    for z0 in (0.35, 1.25):
        ribs.box((sx * (HW - RIB_IN) - (0.004 if sx > 0 else 0), -HL + 0.02, z0),
                 (sx * (HW - RIB_IN) + (0 if sx > 0 else 0.004), -HL + RIB_W - 0.02, z0 + 0.45), "orange")
band(ribs, COMP_IN, COMP_IN_RIB, Y_ROOF0 - 0.2, Y_ROOF0, "gun")   # where the roof starts to slope
built.append(ribs.finish("Cockpit_Ribs", C_BUILT))

# ---------------------------------------------------------------------------
# 10. PIPES along both upper chamfers (right one at the compartment position)
# ---------------------------------------------------------------------------
pipes = MB()
for sx in (1, -1):
    A, B = Vector((sx * HW, H - CH)), Vector((sx * (HW - CH), H))
    mid, t = (A + B) / 2, (B - A).normalized()
    nrm = Vector((-t.y, t.x)) * (1 if sx > 0 else -1)
    for off in (0.13, -0.13):
        p = mid + nrm * 0.20 + t * off
        pipes.cyl((p.x, -HL, p.y), (p.x, Y_ROOF0 - 0.22, p.y), 0.06 if off > 0 else 0.045,
                  "copper", sides=10)
    for yb in (-HL + 0.1, -1.75, Y_ROOF0 - 0.3):
        bc = mid + nrm * 0.14
        pipes.box_c((bc.x, yb, bc.y), (0.42, 0.06, 0.16), "gun",
                    Matrix.Rotation(-math.atan2(t.y, t.x) * (1 if sx > 0 else 1), 4, 'Y'))
built.append(pipes.finish("Cockpit_Pipes", C_BUILT))

# ---------------------------------------------------------------------------
# 11. CEILING LIGHTS
# ---------------------------------------------------------------------------
li = MB()
li.box((-0.55, -2.20, H - 0.07), (0.55, -1.25, H), "gun")
li.box((-0.47, -2.12, H - 0.08), (0.47, -1.33, H - 0.07), "amber")
for sx in (-1, 1):
    for yc in (-2.05, -1.45):
        li.box((sx * 0.80 - 0.13, yc - 0.20, H - 0.05), (sx * 0.80 + 0.13, yc + 0.20, H), "gun")
        li.box((sx * 0.80 - 0.10, yc - 0.17, H - 0.06), (sx * 0.80 + 0.10, yc + 0.17, H - 0.05), "amber")
built.append(li.finish("Cockpit_CeilingLights", C_BUILT))

# ---------------------------------------------------------------------------
# 12. COUNTERS (both walls), DRAWERS AND CABINETS
# ---------------------------------------------------------------------------
TOP_Z = 0.90                # counter / console top
CY0, CY1 = -0.95, 0.55      # side counters along Y
CX_IN = 0.95                # inner edge of the side counters (walkway 1.9 m)


cn = MB()
for sx in (-1, 1):
    # body
    pts = [(sx * HW, CY0), (sx * CX_IN, CY0), (sx * CX_IN, CY1), (sx * HW, CY1)]
    cn.prism([Vector((x, y, 0.08)) for (x, y) in pts], (0, 0, TOP_Z - 0.04 - 0.08), "grey")
    xa_, xb_ = sorted((sx * (CX_IN + 0.05), sx * HW))
    cn.box((xa_, CY0 + 0.02, 0.0), (xb_, CY1 - 0.02, 0.08), "gun_dark")                 # kick plinth
    # top slab, slight overhang
    cn.box((min(sx * (CX_IN - 0.03), sx * HW), CY0 - 0.02, TOP_Z - 0.04),
           (max(sx * (CX_IN - 0.03), sx * HW), CY1, TOP_Z), "counter")
    # fronts: a drawer stack, a cabinet door, a drawer stack (3 bays of ~0.6 m)
    bw = (CY1 - CY0 - 0.06) / 3
    bays = [(CY0 + 0.03 + k * bw + 0.01, CY0 + 0.03 + (k + 1) * bw - 0.01) for k in range(3)]
    xf = sx * (CX_IN - 0.012)
    for bi, (ya, yb) in enumerate(bays):
        if bi == 1:
            cn.box((min(xf, sx * CX_IN), ya, 0.12), (max(xf, sx * CX_IN), yb, TOP_Z - 0.07), "white")
            cn.box((min(xf, xf - sx * 0.012), (ya + yb) / 2 + 0.18, 0.55),
                   (max(xf, xf - sx * 0.012), (ya + yb) / 2 + 0.21, 0.72), "gun")
        else:
            for k, (za, zb_) in enumerate(((0.12, 0.36), (0.39, 0.60), (0.63, TOP_Z - 0.07))):
                cn.box((min(xf, sx * CX_IN), ya, za), (max(xf, sx * CX_IN), yb, zb_), "white")
                cn.box((min(xf, xf - sx * 0.015), (ya + yb) / 2 - 0.09, (za + zb_) / 2 - 0.012),
                       (max(xf, xf - sx * 0.015), (ya + yb) / 2 + 0.09, (za + zb_) / 2 + 0.012), "gun")
    # backsplash strip on the wall
    xa_, xb_ = sorted((sx * (HW - 0.015), sx * HW))
    cn.box((xa_, CY0, TOP_Z), (xb_, CY1, TOP_Z + 0.12), "gun")
built.append(cn.finish("Cockpit_Counters", C_BUILT))

# ---------------------------------------------------------------------------
# 13. HORSESHOE CONSOLE: angled wings, front desk, screens, switches, throttle
# ---------------------------------------------------------------------------
co = MB()
FY0, FY1 = 1.25, 1.95                    # front desk; ends under the windscreen
front = [(-wall_x(FY0) + 0.01, FY0), (wall_x(FY0) - 0.01, FY0),
         (wall_x(FY1) - 0.01, FY1), (-wall_x(FY1) + 0.01, FY1)]
co.prism([Vector((x, y, 0.08)) for (x, y) in front], (0, 0, TOP_Z - 0.04 - 0.08), "grey")
co.prism([Vector((x, y - 0.03, TOP_Z - 0.04)) for (x, y) in front], (0, 0, 0.04), "counter")
for sx in (-1, 1):
    wing = [(sx * HW, CY1), (sx * CX_IN, CY1), (sx * 0.62, FY0), (sx * wall_x(FY0), FY0)]
    if sx < 0:
        wing = wing[::-1]
    co.prism([Vector((x, y, 0.08)) for (x, y) in wing], (0, 0, TOP_Z - 0.04 - 0.08), "grey")
    co.prism([Vector((x, y, TOP_Z - 0.04)) for (x, y) in wing], (0, 0, 0.04), "counter")
    # wing front panel with a cabinet door (faces the chair diagonally)
    a, b = Vector((sx * CX_IN, CY1, 0)), Vector((sx * 0.62, FY0, 0))
    mid = (a + b) / 2
    d = (b - a).normalized()
    nrm = Vector((-d.y, d.x, 0)) * (-1 if sx > 0 else 1)
    ang = math.degrees(math.atan2(d.y, d.x))
    co.box_c(mid + nrm * 0.01 + Vector((0, 0, 0.48)), ((b - a).length - 0.12, 0.02, 0.62), "white",
             rot(rz=ang))
    co.box_c(mid + nrm * 0.025 + Vector((0, 0, 0.70)), (0.20, 0.012, 0.025), "gun", rot(rz=ang))
# front desk: fascia toward the chair with two cabinet doors and a dark kick
co.box((-0.60, FY0 - 0.012, 0.12), (-0.02, FY0, TOP_Z - 0.07), "white")
co.box((0.02, FY0 - 0.012, 0.12), (0.60, FY0, TOP_Z - 0.07), "white")
co.box((-0.62, FY0 - 0.02, 0.0), (0.62, FY0 + 0.05, 0.08), "gun_dark")
for sx in (-1, 1):
    co.box((sx * 0.08 - 0.012, FY0 - 0.026, 0.40), (sx * 0.08 + 0.012, FY0 - 0.012, 0.62), "gun")

# Screens on the front desk, below the window line, tilted back 12 degrees.
def make_screen_image(kind, W=512, Hh=320):
    import numpy as np
    img = np.zeros((Hh, W, 3), np.float32)
    img[:] = (0.02, 0.06, 0.06)
    yy, xx = np.mgrid[0:Hh, 0:W]
    teal = np.array((0.35, 0.95, 0.75), np.float32)
    dim = teal * 0.35

    def disk(cx, cy, r, w, col):
        dd = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        img[np.abs(dd - r) < w] = col

    def seg(x0, y0, x1, y1, w, col):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for t in np.linspace(0, 1, n):
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            img[max(0, int(y - w)):int(y + w) + 1, max(0, int(x - w)):int(x + w) + 1] = col

    # faint grid everywhere
    img[(yy % 32) == 0] = dim * 0.5
    img[(xx % 32) == 0] = dim * 0.5
    if kind == "radar":
        cx, cy = W / 2, Hh / 2
        for r in (40, 80, 120, 150):
            disk(cx, cy, r, 1.2, teal * (0.6 if r < 150 else 1.0))
        seg(cx - 155, cy, cx + 155, cy, 0.8, dim)
        seg(cx, cy - 155, cx, cy + 155, 0.8, dim)
        a = math.radians(35)
        seg(cx, cy, cx + 150 * math.cos(a), cy - 150 * math.sin(a), 1.5, teal)
        for (bx, by) in ((cx + 60, cy - 40), (cx - 95, cy + 30), (cx + 20, cy + 105)):
            disk(bx, by, 4, 4, np.array((1.0, 0.75, 0.35)))
    elif kind == "ship":
        cx, cy = W * 0.42, Hh * 0.52
        pts = [(cx, cy - 110), (cx + 22, cy - 60), (cx + 22, cy - 10), (cx + 160, cy + 70),
               (cx + 150, cy + 85), (cx + 22, cy + 60), (cx + 22, cy + 100), (cx - 22, cy + 100),
               (cx - 22, cy + 60), (cx - 150, cy + 85), (cx - 160, cy + 70), (cx - 22, cy - 10),
               (cx - 22, cy - 60)]
        for i in range(len(pts)):
            seg(*pts[i], *pts[(i + 1) % len(pts)], 1.4, teal)
        seg(cx, cy - 100, cx, cy + 95, 0.7, dim)
        for k in range(9):
            y0 = 40 + k * 26
            seg(W * 0.80, y0, W * 0.80 + 30 + (k * 37) % 50, y0, 2.0, teal * (0.9 if k % 3 else 0.5))
    else:   # data readout
        for k in range(10):
            y0 = 30 + k * 26
            seg(30, y0, 30 + 60 + (k * 53) % 150, y0, 2.2, teal * (1.0 if k % 4 == 0 else 0.6))
            seg(260, y0, 260 + 40 + (k * 31) % 70, y0, 2.2, dim * 1.8)
        vals = [0.3, 0.5, 0.45, 0.7, 0.6, 0.8, 0.75, 0.9, 0.7, 0.85, 0.95]
        for i in range(len(vals) - 1):
            seg(360 + i * 13, 300 - vals[i] * 120, 360 + (i + 1) * 13, 300 - vals[i + 1] * 120, 1.2, teal)
    img = np.flipud(img)
    rgba = np.concatenate([img, np.ones((Hh, W, 1), np.float32)], -1)
    im = bpy.data.images.new(f"screen_{kind}", W, Hh)
    im.pixels.foreach_set(rgba.ravel())
    im.pack()
    return im


for kind, emit in (("radar", 2.2), ("ship", 2.2), ("data", 2.2)):
    MAT[f"scr_{kind}"] = image_material(f"M_Screen_{kind}", make_screen_image(kind), emit)

tilt = rot(rx=-55)         # screens lean back so the pilot sees over them
SCREENS = [("radar", -0.62, 0.40, 0.30), ("ship", 0.0, 0.62, 0.36), ("data", 0.62, 0.40, 0.30)]
SCR_Y = 1.42               # bottom edge of the screens
up = tilt.to_3x3() @ Vector((0, 0, 1))
for kind, x, w, h in SCREENS:
    c = Vector((x, SCR_Y, TOP_Z + 0.03)) + up * (h / 2 + 0.02)
    co.box_c(c + tilt.to_3x3() @ Vector((0, 0.03, 0)), (w + 0.05, 0.04, h + 0.05), "gun", tilt)
    co.box((x - w * 0.3, SCR_Y + 0.05, TOP_Z), (x + w * 0.3, SCR_Y + 0.25, TOP_Z + 0.06), "gun")
    co.card(c + tilt.to_3x3() @ Vector((0, 0.008, 0)), (1, 0, 0), up, w, h, f"scr_{kind}")
    # switch bank in front of each screen: toggles and lit buttons on a sloped plate
    plate = rot(rx=10)
    pc = Vector((x, FY0 + 0.085, TOP_Z + 0.02))
    co.box_c(pc, (w + 0.04, 0.15, 0.03), "gun_dark", plate)
    cols = 6 if kind != "ship" else 9
    for k in range(cols):
        px = x - (w / 2) + 0.05 + k * (w - 0.1) / (cols - 1)
        co.box_c(pc + plate.to_3x3() @ Vector((px - x, -0.035, 0.022)), (0.018, 0.03, 0.02), "grey", plate)
        led = "led_amber" if (k + len(kind)) % 3 else "led_green"
        co.box_c(pc + plate.to_3x3() @ Vector((px - x, 0.04, 0.018)), (0.03, 0.025, 0.008), led, plate)

# Throttle quadrant on the right wing (three levers).
tq = Vector((0.88, 1.02, TOP_Z))
co.box_c(tq + Vector((0, 0, 0.07)), (0.20, 0.30, 0.14), "gun", rot(rz=-20))
co.box_c(tq + Vector((0, 0, 0.142)), (0.16, 0.26, 0.006), "gun_dark", rot(rz=-20))
for k, (dx, lean) in enumerate(((-0.05, 18), (0.0, 8), (0.05, -4))):
    base = tq + rot(rz=-20).to_3x3() @ Vector((dx, 0.0, 0.145))
    top = base + rot(rz=-20).to_3x3() @ (rot(rx=lean).to_3x3() @ Vector((0, 0, 0.16)))
    co.cyl(base, top, 0.008, "grey", sides=6)
    co.box_c(top, (0.028, 0.045, 0.03), "orange" if k == 1 else "gun_dark", rot(rz=-20))
built.append(co.finish("Cockpit_Console", C_BUILT))

# ---------------------------------------------------------------------------
# 14. WALL FITTINGS: shelf + framed picture (left), cork pinboard (right)
# ---------------------------------------------------------------------------
def painted_image(name, kind, W=320, Hh=220):
    import numpy as np
    yy, xx = np.mgrid[0:Hh, 0:W]
    v = 1 - yy / (Hh - 1)
    u = xx / (W - 1)
    if kind == "blueprint":
        img = np.zeros((Hh, W, 3), np.float32); img[:] = (0.12, 0.20, 0.36)
        img[(yy % 16) == 0] = (0.20, 0.30, 0.48); img[(xx % 16) == 0] = (0.20, 0.30, 0.48)
        line = (0.85, 0.90, 0.95)
        cx, cy = W / 2, Hh / 2
        pts = [(cx, cy - 85), (cx + 15, cy - 40), (cx + 15, cy), (cx + 120, cy + 60),
               (cx + 15, cy + 45), (cx + 15, cy + 80), (cx - 15, cy + 80), (cx - 15, cy + 45),
               (cx - 120, cy + 60), (cx - 15, cy), (cx - 15, cy - 40)]
        for i in range(len(pts)):
            x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % len(pts)]
            for t in np.linspace(0, 1, 300):
                x, y = int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t)
                img[max(0, y - 1):y + 1, max(0, x - 1):x + 1] = line
    else:
        sky = np.stack([0.55 + 0.25 * v, 0.62 + 0.2 * v, 0.70 + 0.15 * v], -1)
        if kind == "dusk":
            sky = np.stack([0.85 - 0.3 * v, 0.62 - 0.2 * v, 0.50 + 0.1 * v], -1)
        img = sky.astype(np.float32)
        far = 0.42 + 0.12 * np.abs(np.sin(u * 6 + 1.0)) + 0.03 * np.sin(u * 21)
        img[v < far] = (0.45, 0.50, 0.58)
        near = 0.25 + 0.07 * np.sin(u * 4 + 2.0)
        img[v < near] = (0.30, 0.38, 0.28)
        img[v < 0.1] = (0.25, 0.30, 0.22)
    img = np.clip(img + np.random.default_rng(1).normal(0, 0.015, img.shape), 0, 1)
    img = np.flipud(img)
    rgba = np.concatenate([img, np.ones((Hh, W, 1), np.float32)], -1).astype(np.float32)
    im = bpy.data.images.new(name, W, Hh)
    im.pixels.foreach_set(rgba.ravel())
    im.pack()
    MAT[name] = image_material(f"M_{name}", im)


painted_image("img_landscape", "landscape")
painted_image("img_dusk", "dusk")
painted_image("img_blueprint", "blueprint", 360, 260)

wf = MB()
# left: shelf on brackets above the counter
SX = -HW
wf.box((SX, -1.30, 1.62), (SX + 0.26, -0.30, 1.65), "white")
for yb in (-1.15, -0.45):
    wf.box((SX, yb - 0.015, 1.48), (SX + 0.02, yb + 0.015, 1.62), "gun")
    wf.prism([Vector((SX, yb - 0.01, 1.48)), Vector((SX, yb - 0.01, 1.62)),
              Vector((SX + 0.20, yb - 0.01, 1.62))], (0, 0.02, 0), "gun")
# framed landscape picture under the shelf
wf.box((SX, -1.12, 1.08), (SX + 0.025, -0.78, 1.34), "gun")
wf.card((SX + 0.027, -0.95, 1.21), (0, 1, 0), (0, 0, 1), 0.30, 0.22, "img_landscape")
# right: cork pinboard with a blueprint, notes and two photos
PX = HW
wf.box((PX - 0.03, -1.55, 1.05), (PX, -0.35, 1.85), "gun")
wf.box((PX - 0.04, -1.51, 1.09), (PX - 0.03, -0.39, 1.81), "cork")
right = (0, -1, 0)
wf.card((PX - 0.042, -1.10, 1.47), right, (0, 0, 1), 0.50, 0.36, "img_blueprint")
wf.card((PX - 0.042, -0.62, 1.62), right, (0, 0, 1), 0.16, 0.11, "img_landscape")
wf.card((PX - 0.042, -0.58, 1.30), right, (0, 0, 1), 0.14, 0.10, "img_dusk")
for (y, z) in ((-1.42, 1.73), (-1.40, 1.20), (-0.80, 1.74)):
    wf.box((PX - 0.043, y - 0.05, z - 0.05), (PX - 0.040, y + 0.05, z + 0.05), "paper")
built.append(wf.finish("Cockpit_WallFittings", C_BUILT))

# Floor grates along both sides of the walkway (darker steel, slots).
gr = MB()
for sx in (-1, 1):
    x0, x1 = sorted((sx * 0.55, sx * 0.90))
    gr.box((x0, -2.25, 0.0), (x1, 1.20, 0.008), "grate")
    y = -2.2
    while y < 1.15:
        gr.box((x0 + 0.04, y, 0.008), (x1 - 0.04, y + 0.025, 0.012), "gun")
        y += 0.075
built.append(gr.finish("Cockpit_FloorGrates", C_BUILT))

# ---------------------------------------------------------------------------
# 15. PROPS (origin = centre of the base; 0.05 m gap to walls)
# ---------------------------------------------------------------------------
props = []


def finish_prop(mb, name):
    ob = mb.finish(name, C_PROPS, origin=base_centre(mb))
    props.append(ob)
    return ob


# Command chair: pedestal, leather seat 0.48 m high, high back, armrests.
ch = MB()
CHY = 0.55
ch.cyl((0, CHY, 0.0), (0, CHY, 0.06), 0.30, "gun", sides=8)
ch.cyl((0, CHY, 0.06), (0, CHY, 0.38), 0.075, "gun_dark", sides=8)
ch.box((-0.20, CHY - 0.20, 0.36), (0.20, CHY + 0.20, 0.40), "gun")
ch.box((-0.27, CHY - 0.25, 0.40), (0.27, CHY + 0.27, 0.48), "leather")              # seat
ch.box((-0.25, CHY - 0.22, 0.40), (0.25, CHY + 0.26, 0.405), "gun_dark")
R = rot(rx=10)
bc = Vector((0, CHY - 0.27, 0.86))
ch.box_c(bc, (0.52, 0.12, 0.76), "leather", R)                                         # back
ch.box_c(bc + R.to_3x3() @ Vector((0, -0.065, 0)), (0.46, 0.02, 0.64), "white", R)      # back shell
ch.box_c(bc + R.to_3x3() @ Vector((0, 0.01, 0.47)), (0.32, 0.11, 0.17), "leather", R)   # headrest
for sx in (-1, 1):
    ch.box((sx * 0.30 - 0.04, CHY - 0.20, 0.64), (sx * 0.30 + 0.04, CHY + 0.22, 0.69), "leather")
    ch.box((sx * 0.30 - 0.025, CHY - 0.14, 0.44), (sx * 0.30 + 0.025, CHY - 0.10, 0.64), "gun")
    ch.box((sx * 0.30 - 0.025, CHY + 0.12, 0.44), (sx * 0.30 + 0.025, CHY + 0.16, 0.64), "gun")
    ch.box((sx * 0.30 - 0.03, CHY + 0.10, 0.69), (sx * 0.30 + 0.03, CHY + 0.20, 0.70), "led_amber")
for k in range(5):                                                                       # star base
    a = 2 * math.pi * k / 5
    ch.box_c((0.2 * math.cos(a), CHY + 0.2 * math.sin(a), 0.03), (0.36, 0.06, 0.04), "gun", rot(rz=math.degrees(a)))
finish_prop(ch, "Prop_CommandChair")

# Striped rug down the middle.
rg = MB()
RX, RY0, RY1 = 0.45, -2.25, 0.05
rg.box((-RX, RY0, 0.0), (RX, RY1, 0.010), "rug_base")
for (xa, xb, k) in ((-0.40, -0.34, "rug_light"), (-0.30, -0.27, "rug_dark"), (-0.22, -0.18, "rug_light"),
                    (0.18, 0.22, "rug_light"), (0.27, 0.30, "rug_dark"), (0.34, 0.40, "rug_light")):
    rg.box((xa, RY0 + 0.05, 0.010), (xb, RY1 - 0.05, 0.012), k)
for yy in (RY0 + 0.02, RY1 - 0.04):
    rg.box((-RX + 0.02, yy, 0.010), (RX - 0.02, yy + 0.02, 0.012), "rug_light")
finish_prop(rg, "Prop_Rug")

# Hard storage case (one model, placed three times).
cs = MB()
CW, CD, CHh = 0.62, 0.46, 0.40
cs.box((-CW / 2, -CD / 2, 0.0), (CW / 2, CD / 2, CHh * 0.62), "grey")
cs.box((-CW / 2 + 0.01, -CD / 2 + 0.01, CHh * 0.62), (CW / 2 - 0.01, CD / 2 - 0.01, CHh), "grey")
cs.box((-CW / 2 - 0.005, -CD / 2 - 0.005, CHh * 0.60), (CW / 2 + 0.005, CD / 2 + 0.005, CHh * 0.64), "gun")
for sx in (-1, 1):
    cs.box((sx * 0.20 - 0.03, -CD / 2 - 0.008, 0.0), (sx * 0.20 + 0.03, CD / 2 + 0.008, CHh + 0.005), "orange")
    cs.box((sx * 0.12 - 0.02, -CD / 2 - 0.02, CHh * 0.55), (sx * 0.12 + 0.02, -CD / 2, CHh * 0.70), "gun_dark")
cs.box((-0.08, -0.025, CHh), (0.08, 0.025, CHh + 0.03), "gun_dark")
case_ob = finish_prop(cs, "Prop_StorageCase")
case_ob.location = (-1.12, -1.50, 0.0)
for i, (x, y, z, rz) in enumerate(((1.12, -1.50, 0.0, 0), (1.10, -1.50, CHh + 0.035, 8))):
    dup = bpy.data.objects.new(f"Prop_StorageCase_{i + 2:02d}", case_ob.data)
    C_PROPS.objects.link(dup)
    dup.location = (x, y, z)
    dup.rotation_euler = (0, 0, math.radians(rz))
    props.append(dup)

# Table lamp on the left counter (warm lantern).
lp = MB()
LX, LY = -1.22, -0.45
lp.box((LX - 0.07, LY - 0.07, TOP_Z), (LX + 0.07, LY + 0.07, TOP_Z + 0.03), "gun")
lp.cyl((LX, LY, TOP_Z + 0.03), (LX, LY, TOP_Z + 0.21), 0.06, "lamp", sides=8)
for k in range(4):
    a = math.pi / 4 + k * math.pi / 2
    lp.box_c((LX + 0.062 * math.cos(a), LY + 0.062 * math.sin(a), TOP_Z + 0.12), (0.012, 0.012, 0.18), "gun")
lp.box((LX - 0.07, LY - 0.07, TOP_Z + 0.21), (LX + 0.07, LY + 0.07, TOP_Z + 0.24), "gun")
finish_prop(lp, "Prop_TableLamp")

# Books standing on the shelf.
bkm = MB()
y = -1.27
rnd = random.Random(3)
for k in range(9):
    w = rnd.choice((0.035, 0.045, 0.05))
    h = rnd.uniform(0.20, 0.27)
    d = rnd.uniform(0.15, 0.19)
    bkm.box((SX + 0.03, y, 1.65), (SX + 0.03 + d, y + w, 1.65 + h),
            rnd.choice(("book_r", "book_b", "book_g", "book_br")))
    y += w + 0.004
finish_prop(bkm, "Prop_Books")
# a single book lying on the right counter (same prop family)
b2 = MB()
R2 = Matrix.Translation((1.18, -0.05, TOP_Z)) @ rot(rz=12)
b2.box((-0.12, -0.16, 0.0), (0.12, 0.16, 0.006), "book_r", R2)
b2.box((-0.12, -0.16, 0.044), (0.12, 0.16, 0.05), "book_r", R2)
b2.box((-0.12, -0.16, 0.0), (-0.105, 0.16, 0.05), "book_r", R2)
b2.box((-0.105, -0.155, 0.006), (0.115, 0.155, 0.044), "paper", R2)
finish_prop(b2, "Prop_Books_Counter")

# Trailing plant at the shelf end.
pl = MB()
PXp, PYp, PZp = SX + 0.14, -0.42, 1.65
pl.cyl((PXp, PYp, PZp), (PXp, PYp, PZp + 0.13), 0.07, "pot", sides=8, r2=0.085)
rnd = random.Random(5)


def leaf(mb, base, direction, length, width, key):
    d = Vector(direction).normalized()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 0.1:
        side = Vector((1, 0, 0))
    side.normalize()
    up = side.cross(d)
    tip = base + d * length
    m = base + d * (length * 0.45) + up * (length * 0.1)
    mb.face([base, m + side * width, tip], key, normal=up)
    mb.face([base, tip, m - side * width], key, normal=up)


top = Vector((PXp, PYp, PZp + 0.13))
for k in range(14):
    a = 2 * math.pi * k / 14
    el = rnd.uniform(0.2, 0.9)
    leaf(pl, top, (math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)),
         rnd.uniform(0.09, 0.13), 0.04, "leaf" if k % 3 else "leaf_dark")
for vine in range(3):
    p = top + Vector((0.06, -0.03 + vine * 0.03, -0.02))
    for s in range(7):
        q = p + Vector((0.012, rnd.uniform(-0.02, 0.02), -0.07))
        pl.cyl(p, q, 0.004, "leaf_dark", sides=3)
        for sd in (-1, 1):
            leaf(pl, q, (0.6, sd * 0.7, -0.2), 0.055, 0.025, "leaf")
        p = q
finish_prop(pl, "Prop_Plant")

# Mug on the left counter, near the console.
mg = MB()
MX, MY = -1.18, 0.30
mg.cyl((MX, MY, TOP_Z), (MX, MY, TOP_Z + 0.095), 0.042, "ceramic", sides=10)
mg.cyl((MX, MY, TOP_Z + 0.082), (MX, MY, TOP_Z + 0.088), 0.036, "coffee", sides=10)
mg.box((MX + 0.04, MY - 0.008, TOP_Z + 0.025), (MX + 0.072, MY + 0.008, TOP_Z + 0.037), "ceramic")
mg.box((MX + 0.04, MY - 0.008, TOP_Z + 0.068), (MX + 0.072, MY + 0.008, TOP_Z + 0.080), "ceramic")
mg.box((MX + 0.060, MY - 0.008, TOP_Z + 0.025), (MX + 0.072, MY + 0.008, TOP_Z + 0.080), "ceramic")
finish_prop(mg, "Prop_Mug")

# ---------------------------------------------------------------------------
# 16. COLLIDERS
# ---------------------------------------------------------------------------
def collider(name, lo, hi):
    b = MB()
    b.box(lo, hi, "collider")
    ob = b.finish(f"COL_{name}", C_COL)
    ob.display_type = 'WIRE'
    ob.hide_render = True


collider("Floor", (-HW - T, -HL - T, -T), (HW + T, Y_NOSE + T, 0))
collider("Ceiling", (-HW - T, -HL - T, H), (HW + T, Y_ROOF0, H + T))
collider("Wall_L", (-HW - T, -HL - T, 0), (-HW, Y_CANOPY, H))
collider("Wall_R", (HW, -HL - T, 0), (HW + T, Y_CANOPY, H))
collider("RearWall", (-HW - T, -HL - T, 0), (HW + T, -HL, H + T))
collider("Nose", (-1.3, FY1, 0), (1.3, Y_NOSE + T, 2.3))
collider("Hood", (-1.25, 2.55, -0.35), (1.25, 3.5, 0.95))
collider("Counter_L", (-HW, CY0, 0), (-CX_IN, CY1, TOP_Z))
collider("Counter_R", (CX_IN, CY0, 0), (HW, CY1, TOP_Z))
collider("Console", (-HW, CY1, 0), (HW, FY1, TOP_Z + 0.05))
collider("Chair", (-0.36, CHY - 0.40, 0), (0.36, CHY + 0.30, 1.30))
collider("Cases_L", (-1.43, -1.73, 0), (-0.81, -1.27, CHh + 0.03))
collider("Cases_R", (0.79, -1.75, 0), (1.43, -1.25, 2 * CHh + 0.07))

# ---------------------------------------------------------------------------
# 17. REPORT
# ---------------------------------------------------------------------------
def tris(ob):
    ob.data.calc_loop_triangles()
    return len(ob.data.loop_triangles)


built_all = built + slot_objects
rep_built = {o.name: tris(o) for o in built_all}
rep_props = {o.name: tris(o) for o in props}
print("\n--- Cockpit v3 report ---")
for k, v in rep_built.items():
    print(f"  {k:28s} {v:6d}")
print(f"  BUILT-IN TOTAL               {sum(rep_built.values()):6d}  (budget 18000)")
for k, v in rep_props.items():
    print(f"  {k:28s} {v:6d}  (budget 1500)")
open_slots = []
for o in slot_objects:
    b = bmesh.new(); b.from_mesh(o.data)
    if any(not e.is_manifold for e in b.edges):
        open_slots.append(o.name)
    b.free()
print("  rear-wall slots:", len(slot_objects), "open:", open_slots or "none")
print(f"  walkway between counters: {2 * CX_IN:.2f} m; rear wall to chair back: "
      f"{(CHY - 0.40) - (-HL):.2f} m")

# ---------------------------------------------------------------------------
# 18. RENDER STAGING: dark space, stars, moon, asteroids (RENDER_ONLY)
# ---------------------------------------------------------------------------
world = bpy.data.worlds.new("Space")
scene.world = world
try:
    world.use_nodes = True
except Exception:
    pass
wn, wl = world.node_tree.nodes, world.node_tree.links
bg = wn["Background"]
tc = wn.new("ShaderNodeTexCoord")
vor = wn.new("ShaderNodeTexVoronoi")
vor.inputs["Scale"].default_value = 420
wl.new(tc.outputs["Generated"], vor.inputs["Vector"])
sr = wn.new("ShaderNodeMapRange")
sr.inputs["From Min"].default_value = 0.028
sr.inputs["From Max"].default_value = 0.0
wl.new(vor.outputs["Distance"], sr.inputs["Value"])
# sparse bigger stars
vor2 = wn.new("ShaderNodeTexVoronoi")
vor2.inputs["Scale"].default_value = 90
wl.new(tc.outputs["Generated"], vor2.inputs["Vector"])
sr2 = wn.new("ShaderNodeMapRange")
sr2.inputs["From Min"].default_value = 0.03
sr2.inputs["From Max"].default_value = 0.0
wl.new(vor2.outputs["Distance"], sr2.inputs["Value"])
add = wn.new("ShaderNodeMath"); add.operation = 'ADD'
wl.new(sr.outputs["Result"], add.inputs[0]); wl.new(sr2.outputs["Result"], add.inputs[1])
# faint desaturated Milky Way band
sep = wn.new("ShaderNodeSeparateXYZ")
wl.new(tc.outputs["Generated"], sep.inputs[0])
band_m = wn.new("ShaderNodeMath"); band_m.operation = 'ADD'
wl.new(sep.outputs["Z"], band_m.inputs[0]); wl.new(sep.outputs["X"], band_m.inputs[1])
band_a = wn.new("ShaderNodeMath"); band_a.operation = 'ABSOLUTE'
wl.new(band_m.outputs[0], band_a.inputs[0])
band_r = wn.new("ShaderNodeMapRange")
band_r.inputs["From Min"].default_value = 0.35
band_r.inputs["From Max"].default_value = 0.0
band_r.inputs["To Max"].default_value = 0.06
wl.new(band_a.outputs[0], band_r.inputs["Value"])
mix = wn.new("ShaderNodeMix"); mix.data_type = 'RGBA'
mix.inputs[6].default_value = (0.004, 0.005, 0.012, 1)
mix.inputs[7].default_value = (9.0, 8.6, 8.0, 1)
wl.new(add.outputs[0], mix.inputs["Factor"])
mix2 = wn.new("ShaderNodeMix"); mix2.data_type = 'RGBA'; mix2.blend_type = 'ADD'
wl.new(mix.outputs[2], mix2.inputs[6])
mix2.inputs[7].default_value = (0.5, 0.48, 0.52, 1)
wl.new(band_r.outputs["Result"], mix2.inputs["Factor"])
wl.new(mix2.outputs[2], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 1.0


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
        ld.shape = 'RECTANGLE'; ld.size = size; ld.size_y = size_y or size
    elif kind == 'SUN':
        ld.angle = math.radians(size or 1.0)
    elif size:
        ld.shadow_soft_size = size
    ob = bpy.data.objects.new(name, ld)
    C_RENDER.objects.link(ob)
    ob.location = loc
    if target is not None:
        look(ob, target)
    return ob


def faceted_rock(name, loc, radius, subdiv, seed, key_hex, rough=0.95):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=radius)
    rr = random.Random(seed)
    for v in bm.verts:
        v.co *= 1.0 + rr.uniform(-0.12, 0.12) * (1 if subdiv < 3 else 0.25)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    m = bpy.data.materials.new("M_" + name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    b = m.node_tree.nodes["Principled BSDF"]
    nz = m.node_tree.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.0
    rp = m.node_tree.nodes.new("ShaderNodeValToRGB")
    rp.color_ramp.elements[0].color = (*hexcol("#55555A"), 1)
    rp.color_ramp.elements[1].color = (*hexcol(key_hex), 1)
    m.node_tree.links.new(nz.outputs["Fac"], rp.inputs[0])
    m.node_tree.links.new(rp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    m.node_tree.links.new(rp.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 0.12     # faint earthshine so it reads in soft light
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    C_RENDER.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (rr.random() * 3, rr.random() * 3, rr.random() * 3)
    return ob


moon = faceted_rock("RENDER_Moon", (215, 665, 50), 70, 4, 1, "#A8A6A2")
asteroids = [faceted_rock(f"RENDER_Asteroid_{i}", loc, r, 1, 10 + i, "#8A847C")
             for i, (loc, r) in enumerate((((95, 380, 22), 4.5), ((140, 400, 55), 6),
                                            ((70, 350, -2), 3), ((165, 430, 8), 5),
                                            ((-30, 360, 30), 2.5), ((25, 420, -12), 3.5)))]

SUN = light("L_Sun", 'SUN', (-55, 60, 45), 3.0, "#FFF4E8", 2.0, (0, 0, 0))
SPACE_FILL = light("L_SpaceFill", 'SUN', (-40, -20, 10), 0.25, "#9DB0D0", 10, (0, 0, 0))
INTERIOR = [
    light("L_CeilingPanel", 'AREA', (0, -1.25, H - 0.10), 55, "#FFC07A", 0.9, (0, -1.25, 0), 0.8),
    light("L_SidePanels_L", 'AREA', (-0.8, -1.5, H - 0.08), 18, "#FFC07A", 0.2, (-0.8, -1.5, 0), 1.2),
    light("L_SidePanels_R", 'AREA', (0.8, -1.5, H - 0.08), 18, "#FFC07A", 0.2, (0.8, -1.5, 0), 1.2),
    light("L_Lamp", 'POINT', (LX, LY, TOP_Z + 0.13), 22, "#FFB46A", 0.06),
    light("L_ScreenGlow", 'AREA', (0, 1.30, 1.18), 25, "#7FE0C8", 1.4, (0, 0.2, 1.2), 0.3),
    light("L_RearFill", 'AREA', (0, -2.2, 2.6), 12, "#FFD7A8", 1.4, (0, 0, 0.8), 1.0),
]

# ---------------------------------------------------------------------------
# 19. CAMERAS
# ---------------------------------------------------------------------------
def camera(name, loc, target, lens, ortho=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.03
    cd.clip_end = 5000
    if ortho:
        cd.type = 'ORTHO'
        cd.ortho_scale = ortho
    ob = bpy.data.objects.new(name, cd)
    C_RENDER.objects.link(ob)
    ob.location = loc
    look(ob, target)
    return ob


CAM_MOCK = camera("CAM_MockupView", (0, -2.42, 1.70), (0, 2.5, 1.32), 17)
CAM_CLOSE = camera("CAM_Closeup", (0.52, 0.30, 1.70), (0.05, 2.05, 1.08), 24)
CAM_EXT = camera("CAM_Exterior", (-6.6, 9.4, 4.4), (0.1, 0.6, 1.0), 30)
CAM_SIDE = camera("CAM_Side", (-14, 0.3, 1.5), (0, 0.3, 1.5), 35, ortho=7.6)
CAM_TOP = camera("CAM_TopDown", (0, 0.4, 20), (0, 0.4, 0), 35, ortho=7.4)
CAM_TOP.rotation_euler = (0, 0, math.radians(90))
bpy.data.collections.remove(C_TMP)

# ---------------------------------------------------------------------------
# 20. SAVE + EXPORT
# ---------------------------------------------------------------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)
for o in scene.objects:
    o.select_set(False)
for o in built_all + props + list(C_COL.objects):
    o.select_set(True)
bpy.context.view_layer.objects.active = ob_hull
bpy.ops.export_scene.fbx(
    filepath=os.path.join(OUTPUT_DIR, "cockpit_v3.fbx"), use_selection=True, object_types={'MESH'},
    apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y',
    bake_space_transform=True, mesh_smooth_type='FACE', use_mesh_modifiers=True,
    add_leaf_bones=False, bake_anim=False)
scene.camera = CAM_MOCK
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTPUT_DIR, "cockpit_v3.blend"))
try:
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_mainfile()
except Exception as e:
    print("relative paths:", e)

# ---------------------------------------------------------------------------
# 21. RENDERS
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
        scene.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    try:
        tree = bpy.data.node_groups.new("Bloom", "CompositorNodeTree")
        tree.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
        rl = tree.nodes.new("CompositorNodeRLayers")
        g = tree.nodes.new("CompositorNodeGlare")
        g.inputs["Type"].default_value = 'Bloom'
        g.inputs["Threshold"].default_value = 0.9
        g.inputs["Strength"].default_value = 0.4
        g.inputs["Size"].default_value = 0.6
        out = tree.nodes.new("NodeGroupOutput")
        tree.links.new(rl.outputs["Image"], g.inputs["Image"])
        tree.links.new(g.outputs["Image"], out.inputs[0])
        scene.compositing_node_group = tree
    except Exception as e:
        print("bloom skipped:", e)


def cutaway(z_cut):
    temps = []
    for o in built_all:
        if o.name in ("Cockpit_Ceiling", "Cockpit_CeilingLights", "Cockpit_Pipes"):
            o.hide_render = True
            continue
        o.hide_render = True
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                               plane_co=(0, 0, z_cut), plane_no=(0, 0, 1), clear_outer=True)
        me = bpy.data.meshes.new(o.name + "_cut"); bm.to_mesh(me); bm.free()
        for m in o.data.materials:
            me.materials.append(m)
        t = bpy.data.objects.new(o.name + "_cut", me)
        C_RENDER.objects.link(t)
        t.location = o.location
        temps.append(t)
    return temps


def render(cam, fname, exposure=0.0, interior=True, sun=1.0):
    scene.camera = cam
    SUN.data.energy = sun
    for l in INTERIOR:
        l.hide_render = not interior
    scene.view_settings.exposure = exposure
    scene.render.filepath = os.path.join(OUTPUT_DIR, fname)
    bpy.ops.render.render(write_still=True)
    print("Rendered", fname)


def wanted(tag):
    return not ONLY or tag in ONLY.split(",")


if DO_RENDER:
    setup_render()
    if wanted("mockup"):
        render(CAM_MOCK, "cockpit_v3_mockup_view.png", -0.2, sun=0.8)
    if wanted("closeup"):
        render(CAM_CLOSE, "cockpit_v3_closeup.png", -0.1, sun=0.8)
    if wanted("exterior"):
        render(CAM_EXT, "cockpit_v3_exterior.png", 0.0, sun=3.5)
    if wanted("side"):
        render(CAM_SIDE, "cockpit_v3_side.png", 0.0, sun=3.5)
    if wanted("top"):
        temps = cutaway(2.0)
        top = light("L_TopSoft", 'AREA', (0, 0.4, 8), 600, "#FFF2E0", 5, (0, 0.4, 0), 8)
        render(CAM_TOP, "cockpit_v3_topdown.png", 0.0)
        for t in temps:
            bpy.data.objects.remove(t, do_unlink=True)
        for o in built_all:
            o.hide_render = False
        bpy.data.objects.remove(top, do_unlink=True)
print("Done.")
