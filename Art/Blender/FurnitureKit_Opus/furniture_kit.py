"""
SHAKEDOWN - furniture kit (suffix Opus)
=======================================

Builds every piece of the furniture kit (Docs/Prompts/blender-furniture-kit.md):
merging floor furniture, single floor pieces, decor, wall panels (normal and
chamfer row), the doorway frame and door leaf, and small items. Then it renders
a labelled catalogue and a furnished Cabin, and exports one FBX per family or
piece plus kit_manifest.csv.

HOW TO RUN
  New Blender file > Scripting > New > paste > Run Script. The scene is cleared.
  This script needs ../Compartments_Opus/compartments_Opus.py next to it: it runs
  that generator as a library (up to its section 6) so the wall panels are cut
  from real slots and fit them exactly, and so materials match.
  Rendering takes a while; set DO_RENDER = False to only build and export.

CONVENTIONS
  * 1 unit = 1 m. Floor pieces: origin at the centre of the footprint on the
    floor (Z = 0), front = +Y. Footprint W x L x H blocks = X x Y x Z.
  * 0.05 m margin to the footprint on every side, except the sides where a
    merging piece joins its neighbour (there the body runs to the block edge).
  * "Seen from the front" = standing in front of the piece, facing it. The
    viewer's LEFT is the piece's +X, the viewer's RIGHT is its -X.
    EndL: closed on the viewer's left, open to the right. EndR: the mirror.
    CornerIn: inside corner; walls behind and on the viewer's left; the run
      continues to the viewer's right and toward the front (rotated pieces).
    CornerOut: outside corner; the run comes from the viewer's right and
      continues behind; fronts on the front and on the viewer's left side.
  * Wall panels: origin at the bottom centre of the slot's inner face, +Y into
    the room, +X = viewer's left. The panel occupies Y -0.35 (hull skin) to 0
    (wall surface); only the inner side differs from a plain slot.
    Edge forms (_EdgeL/_EdgeR) carry the 45 degree mitre of a slot at a wall
    corner on that side.
  * ACCESS markers: empty objects named ACCESS_<piece> (Blender needs unique
    names), parented to the piece, 0.5 m in front of its front face.
"""

import bpy
import bmesh
import math
import os
import random
import csv
from mathutils import Vector, Matrix, Euler

# ---------------------------------------------------------------------------
# 0. SETTINGS + LOAD THE COMPARTMENT GENERATOR AS A LIBRARY
# ---------------------------------------------------------------------------
KIT_DIR = os.environ.get("KIT_OUT", os.path.expanduser("~/Shakedown/Art/Blender/FurnitureKit_Opus"))
COMP_PY = os.path.normpath(os.path.join(KIT_DIR, "..", "Compartments_Opus", "compartments_Opus.py"))
DO_RENDER = os.environ.get("KIT_RENDER", "1") == "1"
KIT_SAMPLES = int(os.environ.get("KIT_SAMPLES", "48"))
KIT_RES = int(os.environ.get("KIT_RES", "100"))
KIT_ONLY = os.environ.get("KIT_ONLY", "")

os.environ["COMP_OUT"] = os.path.dirname(COMP_PY)        # so its texture folder resolves
_src = open(COMP_PY).read().split("# 6. BUILD ALL SIX")[0]
exec(compile(_src, COMP_PY, "exec"))                     # clears the scene, defines MAT, MB,
                                                         # compartment_geometry, slot_list, ...
KIT_TMP = new_collection("KIT_TMP")
DO_RENDER = os.environ.get("KIT_RENDER", "1") == "1"     # set again: the library has its own DO_RENDER
M = 0.05            # margin to the footprint

# ---------------------------------------------------------------------------
# 1. EXTRA MATERIALS (cockpit palette; the compartment library has the rest)
# ---------------------------------------------------------------------------
TW, TH, TF, TM = T_WALL, T_HULL, T_FLOOR, T_METAL
TU = "tex_upholstery.png"
MAT.update({
    "white":     MAT["wall"], "grey": MAT["wall_low"], "gun": MAT["slate"], "gun_dark": MAT["recess"],
    "counter":   make_mat("M_Counter_Top",   "#9E9A94", rough=0.55, metal=0.2, tex=TM, scale=1.0),
    "steel":     MAT["floor"],
    "grate":     make_mat("M_Floor_Grate",   "#2E2D31", rough=0.6, metal=0.5, tex=TM, scale=1.0),
    "leather":   make_mat("M_Leather",       "#B4683A", rough=0.55, tex=TU, scale=2.0),
    "fabric":    make_mat("M_Fabric_Slate",  "#6F7479", rough=0.95, tex=TU, scale=2.0),
    "mattress":  make_mat("M_Mattress",      "#9AA2A6", rough=0.95, tex=TU, scale=2.0),
    "blanket":   make_mat("M_Blanket_Rust",  "#8A4A3A", rough=1.0, tex=TU, scale=2.0),
    "pillow":    make_mat("M_Pillow",        "#E2DCD0", rough=1.0, tex=TU, scale=2.0),
    "rug_base":  make_mat("M_Rug_Wool",      "#8A4A3A", rough=1.0, tex=TU, scale=2.0),
    "rug_light": make_mat("M_Rug_Cream",     "#CDBFA6", rough=1.0, tex=TU, scale=2.0),
    "rug_dark":  make_mat("M_Rug_Dark",      "#5C2A27", rough=1.0, tex=TU, scale=2.0),
    "cork":      make_mat("M_Cork",          "#A8834F", rough=0.95, tex=TU, scale=2.0),
    "book_r":    make_mat("M_Book_Red",      "#6E3B34", tex=TU, scale=2.0),
    "book_b":    make_mat("M_Book_Navy",     "#3B4660", tex=TU, scale=2.0),
    "book_g":    make_mat("M_Book_Olive",    "#5E6248", tex=TU, scale=2.0),
    "book_br":   make_mat("M_Book_Brown",    "#6B5040", tex=TU, scale=2.0),
    "paper":     make_mat("M_Paper",         "#E8E1D2", rough=0.9),
    "ceramic":   make_mat("M_Ceramic",       "#E6E1D8", rough=0.35, tex=TW, scale=2.0),
    "coffee":    make_mat("M_Coffee",        "#3A2A22", rough=0.2),
    "leaf":      make_mat("M_Leaf",          "#5F7F3E", rough=0.6),
    "leaf_dark": make_mat("M_LeafDark",      "#46602E", rough=0.6),
    "soil":      make_mat("M_Soil",          "#3B2F27", rough=1.0),
    "pot":       make_mat("M_Pot",           "#8E847A", rough=0.8, tex=TW, scale=2.0),
    "lamp":      make_mat("M_Lamp_Glow",     "#FFC07A", emit=9.0),
    "grow":      make_mat("M_GrowLight",     "#FFE2C0", emit=6.0),
    "led_amber": make_mat("M_LED_Amber",     "#FFB060", emit=5.0),
    "led_green": make_mat("M_LED_Green",     "#7FE0B0", emit=4.0),
    "molten":    make_mat("M_Molten_Glow",   "#FF7A2A", emit=8.0),
    "hob":       make_mat("M_Hob_Ring",      "#FF8A4A", emit=1.5),
    "glass_dark": make_mat("M_Glass_Dark",   "#20262A", rough=0.08, metal=0.1),
    "glass_frost": make_mat("M_Glass_Frosted", "#B8C4C8", rough=0.4, alpha=0.55),
    "water":     make_mat("M_Water",         "#5A8FA0", rough=0.05, alpha=0.5),
    "suit":      make_mat("M_Suit_Fabric",   "#D6D0C4", rough=0.9, tex=TU, scale=2.0),
    "visor":     make_mat("M_Visor",         "#3A3020", rough=0.05, metal=0.6),
})


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


def np_image(name, rgb):
    import numpy as np
    Hh, W = rgb.shape[:2]
    rgba = np.concatenate([np.flipud(rgb), np.ones((Hh, W, 1), np.float32)], -1).astype(np.float32)
    im = bpy.data.images.new(name, W, Hh)
    im.pixels.foreach_set(rgba.ravel())
    im.pack()
    return im


def screen_image(kind, W=384, Hh=240):
    import numpy as np
    img = np.zeros((Hh, W, 3), np.float32)
    img[:] = (0.02, 0.06, 0.06)
    yy, xx = np.mgrid[0:Hh, 0:W]
    teal = np.array((0.35, 0.95, 0.75), np.float32)
    dim = teal * 0.3
    img[(yy % 24) == 0] = dim * 0.5
    img[(xx % 24) == 0] = dim * 0.5

    def seg(x0, y0, x1, y1, w, col):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for t in np.linspace(0, 1, n):
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            img[max(0, int(y - w)):int(y + w) + 1, max(0, int(x - w)):int(x + w) + 1] = col

    def ring(cx, cy, r, w, col):
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        img[np.abs(d - r) < w] = col
    if kind == "data":
        for k in range(8):
            y0 = 25 + k * 25
            seg(20, y0, 20 + 50 + (k * 53) % 120, y0, 2.0, teal * (1.0 if k % 3 == 0 else 0.6))
            seg(220, y0, 220 + 30 + (k * 31) % 60, y0, 2.0, dim * 2)
    elif kind == "starmap":
        rng = np.random.default_rng(4)
        for _ in range(70):
            x, y = rng.integers(0, W), rng.integers(0, Hh)
            img[max(0, y - 1):y + 2, max(0, x - 1):x + 2] = (0.9, 0.9, 0.8)
        pts = [(60, 180), (130, 120), (210, 140), (300, 70)]
        for a, b in zip(pts[:-1], pts[1:]):
            seg(*a, *b, 1.0, teal)
        for p in pts[1:]:
            ring(p[0], p[1], 9, 1.3, np.array((1.0, 0.7, 0.35)))
    elif kind == "status":
        ring(W * 0.3, Hh * 0.5, 70, 2.0, teal)
        seg(W * 0.3, Hh * 0.5, W * 0.3 + 50, Hh * 0.5 - 50, 2.0, teal)
        for k in range(6):
            seg(W * 0.6, 40 + k * 30, W * 0.6 + 40 + k * 12, 40 + k * 30, 6.0, teal * (0.5 + 0.1 * k))
    elif kind == "light":
        for k in range(3):
            ring(W * (0.22 + 0.28 * k), Hh * 0.5, 34, 3, teal * (1.0 if k == 1 else 0.5))
    return np_image(f"img_{kind}", np.clip(img, 0, 1))


def painted_image(name, W=320, Hh=220):
    import numpy as np
    yy, xx = np.mgrid[0:Hh, 0:W]
    v = 1 - yy / (Hh - 1)
    u = xx / (W - 1)
    img = np.stack([0.55 + 0.25 * v, 0.62 + 0.2 * v, 0.70 + 0.15 * v], -1).astype(np.float32)
    far = 0.42 + 0.12 * np.abs(np.sin(u * 6 + 1.0)) + 0.03 * np.sin(u * 21)
    img[v < far] = (0.45, 0.50, 0.58)
    near = 0.25 + 0.07 * np.sin(u * 4 + 2.0)
    img[v < near] = (0.30, 0.38, 0.28)
    img = np.clip(img + np.random.default_rng(1).normal(0, 0.015, img.shape), 0, 1)
    return np_image(name, img.astype(np.float32))


for k in ("data", "starmap", "status", "light"):
    MAT[f"scr_{k}"] = image_material(f"M_Screen_{k}_Opus", screen_image(k), emit=2.2)
MAT["img_landscape"] = image_material("M_Picture_Landscape_Opus", painted_image("img_landscape"))


# ---------------------------------------------------------------------------
# 1b. LOOK PASS (mockup_quarters_v3, second round): a MAINTAINED ship.
#     Three value bands: light walls and cabinets, medium-dark floor, dark
#     gunmetal frames; saturated orange. Wear only where it belongs.
# ---------------------------------------------------------------------------
def recolor(mat, hx):
    col = hexcol(hx)
    b = mat.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*col, 1)
    for n in mat.node_tree.nodes:
        if n.bl_idname == "ShaderNodeMix" and n.blend_type == 'MULTIPLY' and n.name.startswith("Mix"):
            n.inputs[6].default_value = (*col, 1)
            break
    mat.diffuse_color = (*col, 1)


LOOK = {                 # changed values (also listed in notes.md)
    "wall": "#D2C9BB", "wall_low": "#CBC2B4", "ceiling": "#CEC5B7",
    "floor": "#5A5652", "accent": "#DDD6CC", "body": "#CFC7BA",
}
recolor(MAT["wall"], LOOK["wall"]);         MAT["wall"].name = "M_Panel_WarmGreyBeige_Opus"
recolor(MAT["wall_low"], LOOK["wall_low"]); MAT["wall_low"].name = "M_Panel_WarmGreyBeigeLow_Opus"
recolor(MAT["ceiling"], LOOK["ceiling"]);   MAT["ceiling"].name = "M_Ceiling_WarmGreyBeige_Opus"
recolor(MAT["floor"], LOOK["floor"])
MAT["white"] = make_mat("M_Panel_Accent", LOOK["accent"], tex=TW, scale=0.5)   # lighter accent panels
MAT["grey"] = make_mat("M_Body_WarmGreyBeige", LOOK["body"], tex=TW, scale=0.5)


def add_wear(mat, tex_k=0.42, edge=0.8, rust=0.55, grime=0.0, scuff=False, ao_dist=0.12):
    """Wear for a maintained ship:
       * the watercolour texture is blended toward white before the multiply
         (tex_k = share of the texture that remains; 0.35 => at most ~15 %
         darkening), so big surfaces read as clean painted metal;
       * dirt and short rust streaks only near panel edges, seams, bolts and
         corners (ambient-occlusion mask, Cycles);
       * floors: scuffed patches, strongest where people walk (low X);
       * optional faint overall grime.
    All in Object coordinates (no UVs)."""
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = nodes.get("Principled BSDF")
    if not bsdf.inputs["Base Color"].links:
        return
    mixwc = bsdf.inputs["Base Color"].links[0].from_node
    img = next((n for n in nodes if n.bl_idname == "ShaderNodeTexImage"), None)
    if img is not None:
        soft = nodes.new("ShaderNodeMix")
        soft.data_type = 'RGBA'
        soft.inputs["Factor"].default_value = tex_k
        soft.inputs[6].default_value = (1, 1, 1, 1)
        links.new(img.outputs["Color"], soft.inputs[7])
        links.new(soft.outputs[2], mixwc.inputs[7])
    cur = mixwc.outputs[2]
    tc = nodes.new("ShaderNodeTexCoord")

    def noise(scale, stretch=(1, 1, 1), detail=5.0):
        mp = nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = stretch
        links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nz = nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = scale
        nz.inputs["Detail"].default_value = detail
        links.new(mp.outputs["Vector"], nz.inputs["Vector"])
        return nz.outputs["Fac"]

    def ramp(src, lo, hi, c_lo=(0, 0, 0, 1), c_hi=(1, 1, 1, 1)):
        rp = nodes.new("ShaderNodeValToRGB")
        rp.color_ramp.elements[0].position = lo
        rp.color_ramp.elements[0].color = c_lo
        rp.color_ramp.elements[1].position = hi
        rp.color_ramp.elements[1].color = c_hi
        links.new(src, rp.inputs[0])
        return rp.outputs["Color"]

    def math(op, a, b=None, v=None):
        m = nodes.new("ShaderNodeMath")
        m.operation = op
        links.new(a, m.inputs[0])
        if b is not None:
            links.new(b, m.inputs[1])
        elif v is not None:
            m.inputs[1].default_value = v
        return m.outputs[0]

    def multiply_by(color_hex, fac_socket=None, fac=1.0):
        nonlocal cur
        mx = nodes.new("ShaderNodeMix")
        mx.data_type = 'RGBA'
        mx.blend_type = 'MULTIPLY'
        mx.inputs["Factor"].default_value = fac
        if fac_socket is not None:
            links.new(fac_socket, mx.inputs["Factor"])
        links.new(cur, mx.inputs[6])
        mx.inputs[7].default_value = (*hexcol(color_hex), 1)
        cur = mx.outputs[2]

    ao = nodes.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = ao_dist
    ao.only_local = True
    mask = ramp(ao.outputs["AO"], 0.55, 0.97, (1, 1, 1, 1), (0, 0, 0, 1))      # 1 near edges/bolts
    mask_v = math('MULTIPLY', mask, v=1.0)
    if edge:
        brk = ramp(noise(6.0), 0.35, 0.65)                                    # break the edge line up
        multiply_by("#5E4E40", math('MULTIPLY', math('MULTIPLY', mask_v, brk), v=edge))
    if rust:
        streak = ramp(noise(4.0, (9, 9, 0.8), 3.0), 0.55, 0.72)
        multiply_by("#8A5534", math('MULTIPLY', math('MULTIPLY', mask_v, streak), v=rust))
    if grime:
        multiply_by("#7A6A5A", math('MULTIPLY', ramp(noise(1.2), 0.5, 0.75), v=grime))
    if scuff:
        # walkway: X near the room centre wears most (Object space of the slot / room)
        sep = nodes.new("ShaderNodeSeparateXYZ")
        links.new(tc.outputs["Object"], sep.inputs[0])
        walk = ramp(math('ABSOLUTE', sep.outputs["X"]), 0.4, 1.4, (1, 1, 1, 1), (0, 0, 0, 1))
        sc = ramp(noise(3.5, detail=8.0), 0.45, 0.70)
        multiply_by("#3E3B39", math('MULTIPLY', math('MULTIPLY', walk, sc), v=0.55))
        lighten = nodes.new("ShaderNodeMix")
        lighten.data_type = 'RGBA'
        lighten.blend_type = 'SCREEN'
        links.new(math('MULTIPLY', math('MULTIPLY', walk, ramp(noise(9.0), 0.6, 0.8)), v=0.25), lighten.inputs["Factor"])
        links.new(cur, lighten.inputs[6])
        lighten.inputs[7].default_value = (0.55, 0.53, 0.50, 1)
        cur = lighten.outputs[2]
    links.new(cur, bsdf.inputs["Base Color"])


for k, kw in (("wall", {}), ("wall_low", {}), ("ceiling", dict(rust=0.25)),
              ("floor", dict(tex_k=0.6, edge=0.6, rust=0.0, scuff=True)),
              ("hull", dict(tex_k=0.5)), ("hull_sage", dict(tex_k=0.5)),
              ("white", dict(edge=0.45, rust=0.3)), ("grey", dict(edge=0.45, rust=0.3)),
              ("counter", dict(tex_k=0.45, edge=0.4, rust=0.0)),
              ("slate", dict(tex_k=0.7, edge=0.5, rust=0.5)),
              ("recess", dict(tex_k=0.7, edge=0.3, rust=0.0)),
              ("orange", dict(tex_k=0.35, edge=0.6, rust=0.45)),
              ("skirt", dict(tex_k=0.7))):
    add_wear(MAT[k], **kw)
MAT["fabric_blue"] = make_mat("M_Fabric_Steel", "#5E6A74", rough=0.95, tex=TU, scale=2.0)
MAT["strap"] = make_mat("M_Strap_Orange", "#C8682A", rough=0.8, tex=TU, scale=2.0)
MAT["steam"] = make_mat("M_Steam", "#FFFFFF", rough=1.0, alpha=0.08)
MAT["radio_glow"] = make_mat("M_Radio_Dial", "#FFB060", emit=3.0)
MAT["planet_light"] = make_mat("M_Planet", "#6E8FB5", rough=0.9, emit=0.4)
MAT["grime_decal"] = make_mat("M_Grime_Decal", "#3A2E26", rough=1.0, alpha=0.35)


# ---------------------------------------------------------------------------
# 2. MESH BUILDER WITH BEVELLED BOXES, PRISMS, CARDS
# ---------------------------------------------------------------------------
def rot(rx=0.0, ry=0.0, rz=0.0):
    return Euler((math.radians(rx), math.radians(ry), math.radians(rz))).to_matrix().to_4x4()


class KB(MB):
    def __init__(self):
        super().__init__()
        self.uv_faces = []

    def _solid(self, verts, faces_idx, key, bev, M=None):
        if M is not None:
            verts = [M @ Vector(v) for v in verts]
        vs = [self.bm.verts.new(Vector(v)) for v in verts]
        fs = []
        for idx in faces_idx:
            try:
                f = self.bm.faces.new([vs[i] for i in idx])
            except ValueError:
                continue
            f.material_index = self.slot(key)
            fs.append(f)
        bmesh.ops.recalc_face_normals(self.bm, faces=fs)
        if bev > 0:
            edges = list({e for f in fs for e in f.edges})
            bmesh.ops.bevel(self.bm, geom=edges, offset=bev, segments=1, affect='EDGES',
                            clamp_overlap=True, material=self.slot(key))
        return fs

    def cyl(self, a, b, r, key, sides=8, r2=None):
        """Faceted cylinder or cone from a to b (radius r at a, r2 at b)."""
        a, b = Vector(a), Vector(b)
        dv = (b - a).normalized()
        u = dv.cross(Vector((0, 0, 1)) if abs(dv.z) < 0.9 else Vector((1, 0, 0))).normalized()
        w = dv.cross(u)
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
        for f in fs:
            f.material_index = self.slot(key)
        bmesh.ops.recalc_face_normals(self.bm, faces=fs)

    def bbox(self, lo, hi, key, bev=0.01, M=None):
        """Box from lo to hi with bevelled edges (bev=0 for a sharp box)."""
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        if x1 - x0 < 1e-4 or y1 - y0 < 1e-4 or z1 - z0 < 1e-4:
            return
        bev = min(bev, (x1 - x0) * 0.3, (y1 - y0) * 0.3, (z1 - z0) * 0.3)
        v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self._solid(v, f, key, bev, M)

    def bbox_c(self, c, size, key, bev=0.01, R=None):
        h = Vector(size) / 2
        Mx = Matrix.Translation(Vector(c)) @ (R if R is not None else Matrix.Identity(4))
        self.bbox(-h, h, key, bev, Mx)

    def prism(self, profile, offset, key, bev=0.0, M=None):
        off = Vector(offset)
        n = len(profile)
        verts = [Vector(p) for p in profile] + [Vector(p) + off for p in profile]
        faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))]
        for i in range(n):
            j = (i + 1) % n
            faces.append((i, j, n + j, n + i))
        self._solid(verts, faces, key, bev, M)

    def hull(self, points, key, bev=0.0):
        """Convex hull of points as a closed solid."""
        bm2 = bmesh.new()
        for p in points:
            bm2.verts.new(Vector(p))
        bmesh.ops.convex_hull(bm2, input=bm2.verts[:])
        bmesh.ops.dissolve_limit(bm2, angle_limit=math.radians(0.5), verts=bm2.verts[:], edges=bm2.edges[:])
        verts = [v.co.copy() for v in bm2.verts]
        idx = {v: i for i, v in enumerate(bm2.verts)}
        faces = [tuple(idx[v] for v in f.verts) for f in bm2.faces]
        bm2.free()
        self._solid(verts, faces, key, bev)

    def card(self, centre, right, up, w, h, key):
        c, r, u = Vector(centre), Vector(right).normalized(), Vector(up).normalized()
        pts = [c - r * w / 2 - u * h / 2, c + r * w / 2 - u * h / 2,
               c + r * w / 2 + u * h / 2, c - r * w / 2 + u * h / 2]
        f = self.face(pts, key, normal=r.cross(u))
        self.uv_faces.append((f, pts, r, u, w, h))

    def leaf(self, base, direction, length, width, key):
        d = Vector(direction).normalized()
        side = d.cross(Vector((0, 0, 1)))
        if side.length < 0.1:
            side = Vector((1, 0, 0))
        side.normalize()
        up = side.cross(d)
        base = Vector(base)
        tip = base + d * length
        m = base + d * (length * 0.45) + up * (length * 0.1)
        self.face([base, m + side * width, tip], key, normal=up)
        self.face([base, tip, m - side * width], key, normal=up)

    def finish(self, name, coll, location=(0, 0, 0)):
        if self.uv_faces:
            uvl = self.bm.loops.layers.uv.new("UVMap")
            for (f, pts, r, u, w, h) in self.uv_faces:
                if not f.is_valid:
                    continue
                c = sum(pts, Vector()) / 4
                for l in f.loops:
                    d = l.vert.co - c
                    l[uvl].uv = (d.dot(r) / w + 0.5, d.dot(u) / h + 0.5)
        return super().finish(name, coll, location)


def frame(origin, u, n):
    """Local frame on a front face: x along u, y = outward n, z up."""
    u, n = Vector(u).normalized(), Vector(n).normalized()
    m = Matrix((u, n, Vector((0, 0, 1)))).transposed().to_4x4()
    m.translation = Vector(origin)
    return m


# ---------------------------------------------------------------------------
# 3. REGISTRY, ACCESS MARKERS
# ---------------------------------------------------------------------------
PIECES = []          # dicts: ob, name, W, L, H, family, variant, access, group, cat


def register(kb, name, coll, W=None, L=None, H=None, family="none", variant="-", access=False,
             group=None, cat="floor", access_y=None):
    ob = kb.finish(name, coll)
    acc = None
    if access:
        vs = [v.co for v in ob.data.vertices]
        ay = access_y if access_y is not None else max(v.y for v in vs) + 0.5
        acc = bpy.data.objects.new(f"ACCESS_{name}", None)
        acc.empty_display_type = 'SINGLE_ARROW'
        acc.empty_display_size = 0.3
        coll.objects.link(acc)
        acc.parent = ob
        acc.location = (0, ay, 0)
    ob.data.calc_loop_triangles()
    PIECES.append(dict(ob=ob, name=name, W=W, L=L, H=H, family=family, variant=variant,
                       access=access, acc=acc, group=group or name, cat=cat,
                       tris=len(ob.data.loop_triangles)))
    return ob


C_KIT = new_collection("Kit")
C_FLOOR = new_collection("Kit_Floor", C_KIT)
C_WALL = new_collection("Kit_Wall", C_KIT)
C_DECOR = new_collection("Kit_Decor", C_KIT)


# ---------------------------------------------------------------------------
# 4. MERGING FAMILIES: Counter, LowCabinet, Locker, Shelf
# ---------------------------------------------------------------------------
VARIANTS = ["Single", "EndL", "Mid", "EndR", "CornerIn", "CornerOut"]
FRONT_Y = 0.40          # body front plane of the floor units
TOP_FRONT = 0.45        # front edge of tops (5 cm overhang)
KICK = 0.10


def closed_sides(variant):
    """(closed at -X, closed at +X). Viewer's left = +X."""
    return {"Single": (True, True), "EndL": (False, True), "Mid": (False, False),
            "EndR": (True, False)}[variant]


def counter_front(kb, Mf, a0, a1, top_z):
    """Drawer over a door, on a front frame (x along the face, y outward)."""
    kb.bbox((a0 + 0.01, 0.0, top_z - 0.24), (a1 - 0.01, 0.018, top_z - 0.06), "white", 0.008, Mf)
    kb.bbox((a0 + 0.01, 0.0, KICK + 0.03), (a1 - 0.01, 0.018, top_z - 0.27), "white", 0.008, Mf)
    mid = (a0 + a1) / 2
    kb.bbox((mid - 0.11, 0.018, top_z - 0.165), (mid + 0.11, 0.035, top_z - 0.145), "gun", 0.004, Mf)
    kb.bbox((a1 - 0.09, 0.018, top_z - 0.48), (a1 - 0.07, 0.035, top_z - 0.36), "gun", 0.004, Mf)


def low_front(kb, Mf, a0, a1, top_z):
    hs = (top_z - KICK - 0.05) / 3
    for k in range(3):
        z0 = KICK + 0.02 + k * hs
        kb.bbox((a0 + 0.01, 0.0, z0), (a1 - 0.01, 0.018, z0 + hs - 0.02), "white", 0.008, Mf)
        mid = (a0 + a1) / 2
        zc = z0 + hs - 0.07
        kb.bbox((mid - 0.10, 0.018, zc - 0.01), (mid + 0.10, 0.035, zc + 0.01), "gun", 0.004, Mf)


def locker_front(kb, Mf, a0, a1, top_z):
    kb.bbox((a0 + 0.012, 0.0, KICK + 0.03), (a1 - 0.012, 0.018, top_z - 0.08), "white", 0.008, Mf)
    for zc in (top_z - 0.30, KICK + 0.22):                       # vent slots
        for k in range(4):
            z = zc + k * 0.04
            kb.bbox((a0 + 0.18, 0.012, z), (a1 - 0.18, 0.02, z + 0.018), "gun_dark", 0, Mf)
    kb.bbox((a1 - 0.10, 0.018, 0.92), (a1 - 0.075, 0.04, 1.10), "gun", 0.005, Mf)   # handle at 1.0 m
    kb.bbox((a0 + 0.08, 0.018, top_z - 0.16), (a0 + 0.26, 0.022, top_z - 0.11), "orange", 0, Mf)
    kb.bbox((a0 + 0.08, 0.018, top_z - 0.42), (a0 + 0.22, 0.021, top_z - 0.36), "white", 0, Mf)      # label plate
    kb.bbox((a1 - 0.10, 0.018, 1.16), (a1 - 0.075, 0.03, 1.18), "led_green", 0, Mf)               # status light


FAMILIES = {   # top height, front builder, top material, body material
    "Counter":    dict(top=0.90, front=counter_front, topkey="counter", body="grey", H=1),
    "LowCabinet": dict(top=0.60, front=low_front, topkey="counter", body="grey", H=1),
    "Locker":     dict(top=1.95, front=locker_front, topkey="gun", body="grey", H=2),
    "Shelf":      dict(top=1.95, front=None, topkey="counter", body="grey", H=2),
}


def unit_block(kb, fam, x0, x1, y0, y1, front_frames, closed=(), top_poly=None):
    """One floor unit: body from x0..x1, y0..y1 (body front at y1), kick, top,
    fronts on the given frames, side panels on the closed sides (list of
    ('x', value, y0, y1) or ('y', value, x0, x1))."""
    F = FAMILIES[fam]
    tz = F["top"]
    tt = 0.04 if fam != "Locker" else 0.05
    if fam == "Shelf":
        kb.bbox((x0, y0, 0.0), (x1, y0 + 0.02, tz), "grey", 0.005)              # back panel
        for z in (0.0, 0.48, 0.95, 1.42, tz - 0.025):
            kb.bbox((x0, y0 + 0.02, z), (x1, y1, z + 0.025), "counter", 0.004)
        kb.bbox((x0, y0 + 0.02, 0.0), (x1, y1 - 0.04, 0.06), "gun_dark", 0)    # plinth
    else:
        kb.bbox((x0, y0, KICK), (x1, y1, tz - tt), F["body"], 0.006)
        kb.bbox((x0, y0, 0.0), (x1, y1 - 0.06, KICK), "gun_dark", 0)            # recessed kick
        for Mf, a0, a1 in front_frames:
            F["front"](kb, Mf, a0, a1, tz - tt)
        if top_poly is None:
            kb.bbox((x0, y0, tz - tt), (x1, min(TOP_FRONT, y1 + 0.05), tz), F["topkey"], 0.008)
        else:
            kb.prism([Vector((x, y, tz - tt)) for (x, y) in top_poly], (0, 0, tt), F["topkey"], 0.006)
    for (ax, v, a, b) in closed:                                                 # side panels
        if ax == 'x':
            xa, xb = (v, v + 0.02) if v < 0 else (v - 0.02, v)
            kb.bbox((xa, a, 0.0), (xb, b, tz - (0.0 if fam in ("Locker", "Shelf") else tt)), "white", 0.006)
        else:
            ya, yb = (v, v + 0.02) if v < 0 else (v - 0.02, v)
            kb.bbox((a, ya, 0.0), (b, yb, tz), "white", 0.006)


def build_family(fam, variant):
    kb = KB()
    yb, yf = -0.5 + M, FRONT_Y
    if fam == "Shelf":
        yf = 0.40
    if variant in ("Single", "EndL", "Mid", "EndR"):
        cm, cp = closed_sides(variant)
        x0 = -0.5 + (M if cm else 0.0)
        x1 = 0.5 - (M if cp else 0.0)
        fr = [(frame((0, yf, 0), (-1, 0, 0), (0, 1, 0)), -x1 + (0.02 if cp else 0), -x0 - (0.02 if cm else 0))]
        closed = []
        if cm:
            closed.append(('x', x0, yb, (TOP_FRONT if fam != "Shelf" else yf)))
        if cp:
            closed.append(('x', x1, yb, (TOP_FRONT if fam != "Shelf" else yf)))
        unit_block(kb, fam, x0, x1, yb, yf, fr, closed)
        if fam == "Locker":                                   # continuous cornice
            kb.bbox((x0, yb, 1.95 - 0.05), (x1, 0.43, 1.95), "gun", 0.006)
    elif variant == "CornerIn":
        # main unit to the viewer's right (-X open), filler toward the front (+Y open)
        x0, x1 = -0.5, 0.5 - M
        fr = [(frame((0, yf, 0), (-1, 0, 0), (0, 1, 0)), -(0.5 - M) + 0.02 + 0.9, -x0)]   # small front strip
        top = [(-0.5, yb), (x1, yb), (x1, 0.5), (-(0.5 - M), 0.5), (-(0.5 - M), TOP_FRONT), (-0.5, TOP_FRONT)]
        unit_block(kb, fam, x0, x1, yb, yf, [], [('x', x1, yb, 0.5)], top_poly=top if fam not in ("Shelf",) else None)
        if fam == "Shelf":
            kb.bbox((x1 - 0.02, yb, 0.0), (x1, 0.5, 1.95), "grey", 0.005)     # second back panel
            for z in (0.0, 0.48, 0.95, 1.42, 1.925):
                kb.bbox((-(0.5 - M) + 0.4, yf, z), (x1 - 0.02, 0.5, z + 0.025), "counter", 0.004)
        else:
            tz = FAMILIES[fam]["top"]
            tt = 0.04 if fam != "Locker" else 0.05
            kb.bbox((-(0.5 - M) + 0.45, yf, KICK), (x1, 0.5, tz - tt), FAMILIES[fam]["body"], 0.006)
            kb.bbox((-(0.5 - M) + 0.45, yf, 0.0), (x1, 0.5, KICK), "gun_dark", 0)
            if fam == "Locker":
                kb.prism([Vector((x, y, 1.90)) for (x, y) in top], (0, 0, 0.05), "gun", 0.006)
    elif variant == "CornerOut":
        # run comes from the viewer's right (-X) and continues behind (-Y)
        x0, x1 = -0.5, 0.40
        y0 = -0.5
        c = 0.10                                              # chamfer of the outer corner
        if fam == "Shelf":
            for z in (0.0, 0.48, 0.95, 1.42, 1.925):
                kb.prism([Vector(p) for p in [(x0, y0, z), (x1 + 0.05, y0, z), (x1 + 0.05, yf + 0.05 - c, z),
                                              (x1 + 0.05 - c, yf + 0.05, z), (x0, yf + 0.05, z)]],
                         (0, 0, 0.025), "counter", 0.004)
            kb.bbox((x1 + 0.01, yf + 0.01, 0.0), (x1 + 0.05, yf + 0.05, 1.95), "gun", 0.005)   # corner post
            kb.bbox((x0, y0, 0.0), (x1, yf, 0.06), "gun_dark", 0)
        else:
            tz = FAMILIES[fam]["top"]
            tt = 0.04 if fam != "Locker" else 0.05
            body = [(x0, y0), (x1, y0), (x1, yf - c), (x1 - c, yf), (x0, yf)]
            kb.prism([Vector((x, y, KICK)) for (x, y) in body], (0, 0, tz - tt - KICK), FAMILIES[fam]["body"], 0.006)
            kick = [(x0, y0), (x1 - 0.06, y0), (x1 - 0.06, yf - 0.06 - c), (x1 - 0.06 - c, yf - 0.06), (x0, yf - 0.06)]
            kb.prism([Vector((x, y, 0.0)) for (x, y) in kick], (0, 0, KICK), "gun_dark", 0)
            ex = 0.05
            topp = [(x0, y0), (x1 + ex, y0), (x1 + ex, yf + ex - c), (x1 + ex - c, yf + ex), (x0, yf + ex)]
            kb.prism([Vector((x, y, tz - tt)) for (x, y) in topp], (0, 0, tt), FAMILIES[fam]["topkey"], 0.006)
            front = FAMILIES[fam]["front"]
            front(kb, frame((0, yf, 0), (-1, 0, 0), (0, 1, 0)), -(x1 - c), -x0, tz - tt)      # front face
            front(kb, frame((x1, 0, 0), (0, 1, 0), (1, 0, 0)), y0, yf - c, tz - tt)           # left-side face
    return kb


for fam in FAMILIES:
    for var in VARIANTS:
        kb = build_family(fam, var)
        H = FAMILIES[fam]["H"]
        register(kb, f"Furn_{fam}_{var}", C_FLOOR, 1, 1, H, fam, var, access=True, group=f"Furn_{fam}")


# ---------------------------------------------------------------------------
# 5. SINGLE FLOOR PIECES
# ---------------------------------------------------------------------------
def legs(kb, x0, x1, y0, y1, z1, key="gun", t=0.04):
    for x in (x0, x1 - t):
        for y in (y0, y1 - t):
            kb.bbox((x, y, 0), (x + t, y + t, z1), key, 0.006)


# Bed 1 x 2 x 1: a built-in spaceship berth. Head at -Y, foot (access) at +Y.
# The wall side is -X: a chamfered side panel; the room side (+X) has drawers.
def chamfer_prism_yz(kb, x0, x1, pts, key, bev=0.006):
    """Profile in (y, z), extruded along X from x0 to x1."""
    kb.prism([Vector((x0, y, z)) for (y, z) in pts], (x1 - x0, 0, 0), key, bev)


def chamfer_prism_xz(kb, y0, y1, pts, key, bev=0.006):
    """Profile in (x, z), extruded along Y from y0 to y1."""
    kb.prism([Vector((x, y0, z)) for (x, z) in pts], (0, y1 - y0, 0), key, bev)


def recessed_handle(kb, Mf, cx, cz, w=0.14, h=0.03):
    """A dark finger slot set into a front (no protruding knob)."""
    kb.bbox((cx - w / 2, -0.004, cz - h / 2), (cx + w / 2, 0.0005, cz + h / 2), "gun_dark", 0, Mf)
    kb.bbox((cx - w / 2, 0.0005, cz + h / 2 - 0.006), (cx + w / 2, 0.006, cz + h / 2), "gun", 0, Mf)


def wavy_sheet(kb, x_pts, y0, y1, nseg, key_for_y, amp=0.006, thick=0.012, seed=1):
    """Low-poly cloth: a cross-section polyline (x, z) swept along Y with a
    gentle wave, made solid. key_for_y(y) picks the colour per segment (stripes)."""
    rr = random.Random(seed)
    ys = [y0 + (y1 - y0) * k / nseg for k in range(nseg + 1)]
    waves = [amp * math.sin(k * 1.7) + rr.uniform(-amp, amp) * 0.5 for k in range(nseg + 1)]
    top = [[Vector((x, y, z + waves[k] * (0.3 + 0.7 * (i / max(1, len(x_pts) - 1)))))
            for i, (x, z) in enumerate(x_pts)] for k, y in enumerate(ys)]
    nrm_off = Vector((0, 0, -thick))
    for k in range(nseg):
        key = key_for_y((ys[k] + ys[k + 1]) / 2)
        for i in range(len(x_pts) - 1):
            a, b, c, d = top[k][i], top[k][i + 1], top[k + 1][i + 1], top[k + 1][i]
            kb.face([a, b, c, d], key, normal=(b - a).cross(d - a) if (b - a).cross(d - a).z >= 0 else -(b - a).cross(d - a))
            kb.face([a + nrm_off, b + nrm_off, c + nrm_off, d + nrm_off], key, normal=(0, 0, -1))
        # edge faces at the hanging edge and the top edge
        for i in (0, len(x_pts) - 1):
            a, d = top[k][i], top[k + 1][i]
            kb.face([a, d, d + nrm_off, a + nrm_off], key)
    for k in (0, nseg):
        for i in range(len(x_pts) - 1):
            a, b = top[k][i], top[k][i + 1]
            kb.face([a, b, b + nrm_off, a + nrm_off], key_for_y(ys[k]))


kb = KB()
X0, X1, Y0, Y1 = -0.45, 0.45, -0.95, 0.95
# base box with a recessed dark plinth (and a light strip under the frame)
kb.bbox((X0 + 0.05, Y0 + 0.04, KICK), (X1 - 0.02, Y1 - 0.04, 0.36), "grey", 0.01)
kb.bbox((X0 + 0.08, Y0 + 0.08, 0.0), (X1 - 0.07, Y1 - 0.08, KICK), "gun_dark", 0)
kb.bbox((X1 - 0.075, Y0 + 0.12, KICK - 0.014), (X1 - 0.065, Y1 - 0.12, KICK - 0.004), "amber", 0)
kb.bbox((X0 + 0.12, Y1 - 0.085, KICK - 0.014), (X1 - 0.12, Y1 - 0.075, KICK - 0.004), "amber", 0)
# drawers on the room side, recessed handles
Mside = frame((X1 - 0.026, 0, 0), (0, 1, 0), (1, 0, 0))
for (ya, yb_) in ((-0.88, -0.30), (-0.26, 0.32), (0.36, 0.88)):
    kb.bbox((ya, -0.0, KICK + 0.025), (yb_, 0.018, 0.335), "white", 0.006, Mside)
    recessed_handle(kb, Mside @ Matrix.Translation((0, 0.018, 0)), (ya + yb_) / 2, 0.29, 0.16, 0.025)
    kb.bbox((ya + 0.03, 0.018, KICK + 0.05), (ya + 0.09, 0.02, KICK + 0.07), "orange", 0, Mside)   # label
# wall-side panel along -X, chamfered top corners (ship octagon shape)
chamfer_prism_yz(kb, X0, X0 + 0.05, [(Y0, 0.0), (Y1, 0.0), (Y1, 0.62), (Y1 - 0.18, 0.80),
                                     (Y0 + 0.18, 0.80), (Y0, 0.62)], "white", 0.008)
kb.bbox((X0 + 0.05, Y0 + 0.2, 0.70), (X0 + 0.065, Y1 - 0.2, 0.73), "gun", 0.003)        # trim rail
# headboard (-Y), chamfered, with reading light, status screen and buttons
chamfer_prism_xz(kb, Y0, Y0 + 0.06, [(X0, 0.0), (X1, 0.0), (X1, 0.74), (X1 - 0.16, 0.90),
                                     (X0 + 0.16, 0.90), (X0, 0.74)], "white", 0.008)
Mh = frame((0, Y0 + 0.06, 0), (1, 0, 0), (0, 1, 0))
kb.bbox((-0.34, 0.0, 0.52), (0.34, 0.012, 0.84), "gun", 0.006, Mh)                        # dark inset panel
kb.bbox((-0.28, 0.012, 0.78), (0.28, 0.02, 0.80), "lamp", 0, Mh)                         # reading-light strip
kb.card(Vector((0.17, Y0 + 0.073, 0.65)), (1, 0, 0), (0, 0, 1), 0.12, 0.08, "scr_status")
for k in range(3):
    kb.bbox((-0.26 + k * 0.05, 0.012, 0.60), (-0.23 + k * 0.05, 0.022, 0.63),
            "led_green" if k == 0 else "grey", 0.002, Mh)
kb.bbox((-0.30, 0.012, 0.55), (-0.08, 0.016, 0.57), "orange", 0, Mh)                     # label strip
# foot rail (+Y), low, chamfered
chamfer_prism_xz(kb, Y1 - 0.05, Y1, [(X0, 0.0), (X1, 0.0), (X1, 0.40), (X1 - 0.08, 0.48),
                                     (X0 + 0.08, 0.48), (X0, 0.40)], "white", 0.008)
kb.bbox((X1 - 0.03, Y0 + 0.06, 0.34), (X1, Y1 - 0.05, 0.40), "gun", 0.004)               # room-side frame rail
# thin mattress, chamfered pillow
kb.bbox((X0 + 0.055, Y0 + 0.065, 0.36), (X1 - 0.035, Y1 - 0.055, 0.47), "mattress", 0.025)
kb.hull([(-0.28, -0.86, 0.47), (0.28, -0.86, 0.47), (-0.28, -0.60, 0.47), (0.28, -0.60, 0.47),
         (-0.24, -0.84, 0.57), (0.24, -0.84, 0.57), (-0.24, -0.63, 0.58), (0.24, -0.63, 0.58),
         (-0.31, -0.73, 0.52), (0.31, -0.73, 0.52), (0.0, -0.74, 0.60)], "pillow", 0.01)
# striped blanket with a soft fold, draping over the room side
def stripe(y):
    return "rug_light" if (-0.18 < y < -0.08) or (0.52 < y < 0.60) else ("rug_dark" if -0.08 <= y < -0.02 else "blanket")


wavy_sheet(kb, [(X0 + 0.06, 0.482), (0.0, 0.492), (0.30, 0.488), (X1 - 0.035, 0.470), (X1 - 0.012, 0.43),
                (X1 - 0.008, 0.33)], -0.36, Y1 - 0.06, 10, stripe, amp=0.008, thick=0.012, seed=3)
wavy_sheet(kb, [(X0 + 0.07, 0.505), (0.0, 0.515), (0.30, 0.51), (X1 - 0.02, 0.49)], -0.44, -0.30, 2,
           lambda y: "rug_light", amp=0.004, thick=0.012, seed=5)                         # turned-back fold
# folded safety strap at the room side, clipped to the frame rail
for k, z in enumerate((0.405, 0.418)):
    kb.bbox((X1 - 0.13 + k * 0.01, -0.08, z), (X1 - 0.005, 0.06, z + 0.012), "strap", 0.003)
kb.bbox((X1 - 0.008, -0.03, 0.30), (X1 + 0.0, 0.01, 0.40), "strap", 0)
kb.bbox((X1 - 0.010, -0.035, 0.27), (X1 + 0.0, 0.015, 0.30), "steel", 0.002)             # buckle
register(kb, "Furn_Bed", C_FLOOR, 1, 2, 1, access=True)

# Bunk 1 x 2 x 2: two berths, ladder at the foot end.
kb = KB()
for zb_ in (KICK, 1.08):
    kb.bbox((X0, Y0, zb_), (X1, Y1 - (0.02 if zb_ == KICK else 0.0), zb_ + 0.22), "grey", 0.008)
    kb.bbox((X0 + 0.03, Y0 + 0.03, zb_ + 0.22), (X1 - 0.03, Y1 - 0.03, zb_ + 0.40), "mattress", 0.03)
    kb.bbox((X0 + 0.10, Y0 + 0.08, zb_ + 0.40), (X1 - 0.10, Y0 + 0.38, zb_ + 0.50), "pillow", 0.04)
    kb.bbox((X0 + 0.01, Y0 + 0.80, zb_ + 0.30), (X1 - 0.01, Y1 - 0.05, zb_ + 0.42), "blanket", 0.02)
kb.bbox((X0 + 0.04, Y0 + 0.04, 0), (X1 - 0.04, Y1 - 0.06, KICK), "gun_dark", 0)
kb.bbox((-0.40, Y1 - 0.018, KICK + 0.03), (0.40, Y1, KICK + 0.19), "white", 0.005)     # drawer
kb.bbox((-0.12, Y1 - 0.02, KICK + 0.12), (0.12, Y1, KICK + 0.14), "gun", 0)
legs(kb, X0, X1, Y0, Y1, 1.90, "gun", 0.05)
kb.bbox((X0, Y0, 0.6), (X1, Y0 + 0.04, 1.0), "white", 0.01)                             # head panels
kb.bbox((X0, Y0, 1.6), (X1, Y0 + 0.04, 1.85), "white", 0.01)
for x in (X0, X1 - 0.04):                                                               # upper side rail
    kb.bbox((x, Y0 + 0.05, 1.60), (x + 0.04, Y1 - 0.45, 1.66), "gun", 0.005)
for x in (-0.22, 0.18):                                                                 # ladder at the foot
    kb.bbox((x, Y1 - 0.04, 0.0), (x + 0.04, Y1, 1.75), "gun", 0.005)
for z in (0.40, 0.75, 1.10, 1.45):
    kb.cyl((-0.20, Y1 - 0.02, z), (0.20, Y1 - 0.02, z), 0.016, "orange", sides=6)
register(kb, "Furn_Bunk", C_FLOOR, 1, 2, 2, access=True)

# Wardrobe 2 x 1 x 2: two doors.
kb = KB()
unit_block(kb, "Locker", -0.95, 0.95, -0.45, 0.40, [], [('x', -0.95, -0.45, 0.43), ('x', 0.95, -0.45, 0.43)])
kb.bbox((-0.95, -0.45, 1.90), (0.95, 0.43, 1.95), "gun", 0.006)
for (a0, a1, hx) in ((-0.93, -0.005, -0.08), (0.005, 0.93, 0.06)):
    kb.bbox((a0, 0.40, KICK + 0.03), (a1, 0.418, 1.86), "white", 0.008)
    kb.bbox((hx, 0.418, 0.90), (hx + 0.02, 0.44, 1.12), "gun", 0.005)
    kb.bbox(((a0 + a1) / 2 - 0.10, 0.418, 1.70), ((a0 + a1) / 2 + 0.10, 0.422, 1.74), "orange", 0)
register(kb, "Furn_Wardrobe", C_FLOOR, 2, 1, 2, access=True)

# Desk 1 x 2 x 1: desk in the back block, the front block is the chair space.
# Built-in look: chamfered top, gunmetal frame, drawer unit with recessed
# handles, status light, label, cable run down the back.
kb = KB()
top = [(-0.45, -0.95), (0.45, -0.95), (0.45, -0.34), (0.39, -0.28), (-0.39, -0.28), (-0.45, -0.34)]
kb.prism([Vector((x, y, 0.72)) for (x, y) in top], (0, 0, 0.03), "counter", 0.006)
kb.bbox((-0.45, -0.32, 0.705), (0.45, -0.30, 0.72), "gun", 0.003)                      # front lip
kb.bbox((-0.45, -0.95, 0.0), (-0.41, -0.32, 0.72), "gun", 0.006)                        # left frame leg
kb.bbox((-0.41, -0.95, 0.66), (0.05, -0.92, 0.72), "gun", 0.004)
kb.bbox((-0.41, -0.95, 0.30), (0.05, -0.93, 0.66), "grey", 0.005)                       # modesty panel
kb.bbox((0.05, -0.93, 0.0), (0.45, -0.33, 0.70), "grey", 0.008)                         # drawer unit
kb.bbox((0.07, -0.90, 0.0), (0.43, -0.36, 0.05), "gun_dark", 0)
Mf = frame((0, -0.33, 0), (1, 0, 0), (0, 1, 0))
for (za, zb_) in ((0.06, 0.30), (0.32, 0.50), (0.52, 0.68)):
    kb.bbox((0.07, 0.0, za), (0.43, 0.016, zb_), "white", 0.005, Mf)
    recessed_handle(kb, Mf @ Matrix.Translation((0, 0.016, 0)), 0.25, zb_ - 0.04, 0.14, 0.022)
kb.bbox((0.09, 0.016, 0.62), (0.15, 0.018, 0.64), "orange", 0, Mf)                       # label
kb.bbox((0.39, 0.016, 0.63), (0.41, 0.022, 0.65), "led_green", 0, Mf)                    # status light
# cable run: a tray under the back edge and two cables down to the floor
kb.bbox((-0.38, -0.93, 0.60), (0.02, -0.86, 0.63), "gun_dark", 0.003)
for x, r in ((-0.30, 0.008), (-0.26, 0.006)):
    kb.cyl((x, -0.90, 0.60), (x, -0.90, 0.30), r, "gun_dark", sides=5)
    kb.cyl((x, -0.90, 0.30), (x + 0.02, -0.91, 0.01), r, "gun_dark", sides=5)
kb.bbox((-0.20, -0.94, 0.75), (0.0, -0.90, 0.77), "gun", 0.003)                         # grommet strip
register(kb, "Furn_Desk", C_FLOOR, 1, 2, 1, access=True)

# Dinette 2 x 3 x 1: booth with benches along both long sides, table between,
# open at the front (+Y) where you slide in.
kb = KB()
for sx in (-1, 1):
    xo_, xi_ = sx * 0.95, sx * 0.50
    xa, xb_ = sorted((xo_, xi_))
    kb.bbox((xa, -1.45, KICK), (xb_, 1.00, 0.38), "grey", 0.008)
    kb.bbox((xa + 0.03, -1.43, 0), (xb_ - 0.03, 0.96, KICK), "gun_dark", 0)
    kb.bbox((xa + 0.01, -1.43, 0.38), (xb_ - 0.01, 0.98, 0.45), "leather", 0.02)       # seat 0.45
    xa2, xb2 = sorted((xo_, xo_ - sx * 0.12))
    kb.bbox((xa2, -1.45, 0.38), (xb2, 1.00, 0.95), "white", 0.01)                       # back frame
    xa3, xb3 = sorted((xo_ - sx * 0.12, xo_ - sx * 0.20))
    kb.bbox((xa3, -1.40, 0.48), (xb3, 0.95, 0.88), "leather", 0.02)
kb.bbox((-0.38, -1.40, 0.72), (0.38, 0.55, 0.75), "counter", 0.008)                     # table
kb.bbox((-0.06, -0.55, 0.0), (0.06, -0.31, 0.72), "gun", 0.005)
kb.bbox((-0.25, -0.65, 0.0), (0.25, -0.21, 0.03), "gun", 0.005)
register(kb, "Furn_Dinette", C_FLOOR, 2, 3, 1, access=True)

# Storage case 1 x 1 x 1: a hard storage chest with a chamfered lid, latches,
# side handles, stencil label and orange bands.
def storage_case(kb, cx=0, cy=0, cz=0):
    CW, CD, CH = 0.80, 0.50, 0.48
    zl = CH * 0.68
    o = Vector((cx, cy, cz))
    body = [(-CW / 2, 0), (CW / 2, 0), (CW / 2, zl), (-CW / 2, zl)]
    lid = [(-CW / 2, zl + 0.01), (CW / 2, zl + 0.01), (CW / 2, CH - 0.06), (CW / 2 - 0.06, CH),
           (-CW / 2 + 0.06, CH), (-CW / 2, CH - 0.06)]
    kb.prism([o + Vector((x, -CD / 2, z)) for (x, z) in body], (0, CD, 0), "grey", 0.015)
    kb.prism([o + Vector((x, -CD / 2 + 0.005, z)) for (x, z) in lid], (0, CD - 0.01, 0), "grey", 0.012)
    kb.bbox(o + Vector((-CW / 2 - 0.006, -CD / 2 - 0.006, zl - 0.02)), o + Vector((CW / 2 + 0.006, CD / 2 + 0.006, zl + 0.02)),
            "gun", 0.004)                                                                  # seal band
    kb.bbox(o + Vector((-CW / 2 - 0.004, -CD / 2 - 0.004, 0)), o + Vector((CW / 2 + 0.004, CD / 2 + 0.004, 0.04)), "gun", 0.004)
    for sx in (-1, 1):
        kb.bbox(o + Vector((sx * 0.25 - 0.035, -CD / 2 - 0.008, 0.0)), o + Vector((sx * 0.25 + 0.035, CD / 2 + 0.008, CH * 0.66)),
                "orange", 0.004)
        kb.bbox(o + Vector((sx * 0.13 - 0.025, CD / 2, zl - 0.07)), o + Vector((sx * 0.13 + 0.025, CD / 2 + 0.022, zl + 0.05)),
                "gun_dark", 0.004)                                                         # latches
        kb.bbox(o + Vector((sx * 0.13 - 0.015, CD / 2 + 0.022, zl - 0.02)), o + Vector((sx * 0.13 + 0.015, CD / 2 + 0.026, zl + 0.03)),
                "steel", 0.002)
        kb.bbox(o + Vector((sx * CW / 2, -0.10, zl - 0.12)), o + Vector((sx * (CW / 2 + 0.025), 0.10, zl - 0.08)), "gun", 0.004)
    kb.bbox(o + Vector((-0.09, CD / 2, 0.10)), o + Vector((0.09, CD / 2 + 0.003, 0.20)), "white", 0)   # stencil plate
    kb.bbox(o + Vector((-0.07, CD / 2 + 0.003, 0.14)), o + Vector((0.05, CD / 2 + 0.005, 0.16)), "gun_dark", 0)


kb = KB()
storage_case(kb)
register(kb, "Furn_StorageCase", C_FLOOR, 1, 1, 1, access=True)

# Smelter 2 x 2 x 2: furnace, hopper on top, glowing inspection window, heat
# duct out of the back (it stands against an outer wall).
kb = KB()
kb.bbox((-0.92, -0.80, 0.0), (0.92, 0.70, 0.10), "gun", 0.01)                            # base
kb.bbox((-0.85, -0.75, 0.10), (0.85, 0.62, 1.30), "grey", 0.02)                          # furnace body
for sx in (-1, 1):                                                                      # corner frames
    kb.bbox((sx * 0.85 - 0.05, 0.57, 0.10), (sx * 0.85 + 0.05, 0.67, 1.32), "gun", 0.008)
kb.bbox((-0.88, -0.78, 1.30), (0.88, 0.66, 1.38), "gun", 0.01)
kb.hull([(-0.55, -0.55, 1.38), (0.55, -0.55, 1.38), (0.55, 0.35, 1.38), (-0.55, 0.35, 1.38),
         (-0.70, -0.70, 1.88), (0.70, -0.70, 1.88), (0.70, 0.50, 1.88), (-0.70, 0.50, 1.88)], "white", 0.01)
kb.bbox((-0.72, -0.72, 1.88), (0.72, 0.52, 1.95), "gun", 0.008)                          # hopper rim
kb.bbox((-0.60, -0.60, 1.94), (0.60, 0.40, 1.951), "gun_dark", 0)
kb.bbox((-0.36, 0.62, 0.55), (0.36, 0.68, 1.02), "gun", 0.01)                            # window frame
kb.bbox((-0.30, 0.66, 0.60), (0.30, 0.685, 0.97), "molten", 0)
kb.bbox((-0.30, 0.62, 0.22), (0.30, 0.82, 0.30), "gun", 0.006)                           # ingot tray
for k in range(3):
    kb.bbox((-0.24 + k * 0.17, 0.66, 0.30), (-0.12 + k * 0.17, 0.78, 0.35), "counter", 0.006)
for k in range(5):                                                                      # hazard stripes
    kb.hull([(-0.85 + k * 0.36, 0.701, 0.02), (-0.70 + k * 0.36, 0.701, 0.02),
             (-0.62 + k * 0.36, 0.701, 0.09), (-0.77 + k * 0.36, 0.701, 0.09),
             (-0.85 + k * 0.36, 0.706, 0.02), (-0.62 + k * 0.36, 0.706, 0.09)], "orange")
kb.bbox((0.45, 0.62, 1.05), (0.80, 0.66, 1.25), "gun", 0.006)                            # control panel
kb.card((0.625, 0.662, 1.15), (1, 0, 0), (0, 0, 1), 0.30, 0.16, "scr_data")
kb.bbox((-0.30, -0.95, 1.00), (0.30, -0.75, 1.85), "gun", 0.012)                         # heat duct (back)
kb.bbox((-0.36, -0.95, 0.94), (0.36, -0.92, 1.91), "gun_dark", 0.006)                    # wall flange
for k in range(6):
    kb.bbox((-0.26, -0.952, 1.06 + k * 0.12), (0.26, -0.94, 1.10 + k * 0.12), "grate", 0)
register(kb, "Furn_Smelter", C_FLOOR, 2, 2, 2, access=True)

# Fabricator 1 x 2 x 2: enclosed print bay with a window, control panel.
kb = KB()
kb.bbox((-0.45, -0.95, 0.0), (0.45, 0.90, 0.10), "gun_dark", 0)
kb.bbox((-0.45, -0.95, 0.10), (0.45, 0.88, 1.90), "grey", 0.02)
kb.bbox((-0.45, -0.95, 1.85), (0.45, 0.90, 1.95), "gun", 0.01)
kb.bbox((-0.36, 0.86, 0.80), (0.36, 0.90, 1.55), "gun", 0.01)                            # bay frame
kb.bbox((-0.31, 0.89, 0.85), (0.31, 0.905, 1.50), "glass_dark", 0)
kb.bbox((-0.28, 0.84, 1.42), (0.28, 0.86, 1.46), "lamp", 0)                              # bay light
kb.bbox((-0.10, 0.70, 0.86), (0.10, 0.86, 0.92), "orange", 0.005)                       # part on the bed
kb.bbox((-0.40, 0.88, 0.30), (0.40, 0.90, 0.75), "white", 0.006)                         # lower door
kb.bbox((-0.30, 0.88, 0.60), (0.30, 0.88 + 0.02, 0.62), "gun", 0)
kb.bbox((0.15, 0.88, 1.60), (0.42, 0.92, 1.80), "gun", 0.006)                            # control panel
kb.card((0.285, 0.922, 1.70), (1, 0, 0), (0, 0, 1), 0.23, 0.15, "scr_status")
for k in range(4):
    kb.bbox((-0.40 + k * 0.08, 0.90, 1.70), (-0.35 + k * 0.08, 0.915, 1.74), "led_amber" if k % 2 else "led_green", 0)
for k in range(5):                                                                     # vent grille
    kb.bbox((-0.40, 0.88, 1.62 + k * 0.035), (0.05, 0.895, 1.64 + k * 0.035), "grate", 0)
register(kb, "Furn_Fabricator", C_FLOOR, 1, 2, 2, access=True)

# Hydroponics 1 x 3 x 2: two lit grow shelves, water tank below.
kb = KB()
YA, YB = -1.45, 1.45
legs(kb, -0.45, 0.45, YA, YB, 1.95, "gun", 0.05)
kb.bbox((-0.40, YA + 0.05, 0.06), (0.40, YB - 0.05, 0.50), "water", 0)                   # tank
kb.bbox((-0.42, YA + 0.03, 0.04), (0.42, YB - 0.03, 0.08), "gun", 0.005)
kb.bbox((-0.42, YA + 0.03, 0.50), (0.42, YB - 0.03, 0.54), "gun", 0.005)
rnd = random.Random(8)
for zt_, zl in ((0.70, 1.22), (1.30, 1.82)):
    kb.bbox((-0.42, YA + 0.03, zt_), (0.42, YB - 0.03, zt_ + 0.12), "white", 0.008)      # tray
    kb.bbox((-0.38, YA + 0.07, zt_ + 0.12), (0.38, YB - 0.07, zt_ + 0.125), "soil", 0)
    kb.bbox((-0.30, YA + 0.05, zl), (0.30, YB - 0.05, zl + 0.03), "gun", 0.005)          # light bar
    kb.bbox((-0.26, YA + 0.08, zl - 0.005), (0.26, YB - 0.08, zl), "grow", 0)
    for k in range(8):                                                                   # plants
        y = -1.05 + k * 0.30
        for x in (-0.18, 0.18):
            base = Vector((x, y + rnd.uniform(-0.05, 0.05), zt_ + 0.125))
            for a in range(4):
                ang = a * math.pi / 2 + rnd.uniform(-0.3, 0.3)
                kb.leaf(base, (math.cos(ang), math.sin(ang), 1.1), rnd.uniform(0.12, 0.2), 0.04,
                        "leaf" if a % 2 else "leaf_dark")
kb.bbox((-0.30, YB - 0.05, 0.55), (0.30, YB - 0.01, 0.68), "gun", 0.006)                 # control box
kb.card((0.0, YB - 0.009, 0.615), (-1, 0, 0), (0, 0, 1), 0.20, 0.08, "scr_data")
kb.cyl((0.30, YA + 0.20, 0.50), (0.30, YA + 0.20, 1.30), 0.015, "ochre", sides=6)        # water riser
register(kb, "Furn_Hydroponics", C_FLOOR, 1, 3, 2, access=True)


# Chair 1 x 1 x 1: padded swivel chair on a star base, seat 0.45 m.
def chair(kb):
    for k in range(5):                                                   # star base with casters
        a = 2 * math.pi * k / 5 + math.pi / 2
        d = Vector((math.cos(a), math.sin(a), 0))
        kb.hull([d * 0.04 + Vector((0, 0, 0.05)), d * 0.04 + Vector((0, 0, 0.09)),
                 d * 0.28 + Vector((0, 0, 0.045)), d * 0.28 + Vector((0, 0, 0.065)),
                 d * 0.04 + d.cross(Vector((0, 0, 1))) * 0.025 + Vector((0, 0, 0.07)),
                 d * 0.04 - d.cross(Vector((0, 0, 1))) * 0.025 + Vector((0, 0, 0.07)),
                 d * 0.28 + d.cross(Vector((0, 0, 1))) * 0.015 + Vector((0, 0, 0.055)),
                 d * 0.28 - d.cross(Vector((0, 0, 1))) * 0.015 + Vector((0, 0, 0.055))], "gun")
        kb.cyl(d * 0.27 + Vector((0, 0, 0.0)), d * 0.27 + Vector((0, 0, 0.045)), 0.022, "gun_dark", sides=6)
    kb.cyl((0, 0, 0.07), (0, 0, 0.32), 0.03, "steel", sides=8)          # gas column
    kb.cyl((0, 0, 0.08), (0, 0, 0.20), 0.04, "gun_dark", sides=8)
    kb.bbox((-0.12, -0.12, 0.32), (0.12, 0.12, 0.36), "gun", 0.006)     # seat plate
    kb.hull([(-0.22, -0.20, 0.36), (0.22, -0.20, 0.36), (-0.22, 0.20, 0.36), (0.22, 0.20, 0.36),
             (-0.20, -0.18, 0.45), (0.20, -0.18, 0.45), (-0.20, 0.17, 0.45), (0.20, 0.17, 0.45),
             (0.0, 0.0, 0.46)], "leather", 0.01)                         # padded seat
    kb.bbox((-0.04, -0.24, 0.36), (0.04, -0.20, 0.60), "gun", 0.005)    # back support
    R = rot(rx=-8)
    kb.bbox_c((0, -0.24, 0.74), (0.40, 0.08, 0.34), "leather", 0.025, R)   # padded back
    kb.bbox_c((0, -0.283, 0.74), (0.34, 0.012, 0.26), "gun", 0.004, R)
    for sx in (-1, 1):                                                 # armrests
        kb.bbox((sx * 0.21 - 0.02, -0.05, 0.36), (sx * 0.21 + 0.02, -0.01, 0.58), "gun", 0.004)
        kb.bbox((sx * 0.21 - 0.03, -0.16, 0.58), (sx * 0.21 + 0.03, 0.12, 0.61), "gun_dark", 0.008)


kb = KB()
chair(kb)
register(kb, "Furn_Chair", C_FLOOR, 1, 1, 1, access=True)

# WetCell 1 x 1 x 2: cubicle with a door (frosted window), shower head, fold-down seat.
kb = KB()
kb.bbox((-0.45, -0.45, 0.0), (0.45, 0.45, 0.08), "gun", 0.006)                           # shower tray
kb.bbox((-0.40, -0.40, 0.08), (0.40, 0.38, 0.09), "grate", 0)
kb.bbox((-0.45, -0.45, 0.0), (0.45, -0.41, 1.95), "white", 0.008)                        # back
kb.bbox((-0.45, -0.41, 0.0), (-0.41, 0.45, 1.95), "white", 0.008)                        # sides
kb.bbox((0.41, -0.41, 0.0), (0.45, 0.45, 1.95), "white", 0.008)
kb.bbox((-0.45, -0.45, 1.88), (0.45, 0.45, 1.945), "gun", 0.008)                         # roof
kb.bbox((-0.15, -0.15, 1.945), (0.15, 0.15, 1.95), "grate", 0)
for sx in (-1, 1):                                                                       # door frame
    kb.bbox((sx * 0.42 - 0.03, 0.40, 0.0), (sx * 0.42 + 0.03, 0.45, 1.90), "gun", 0.006)
kb.bbox((-0.39, 0.39, 0.08), (0.39, 0.42, 1.86), "white", 0.008)                         # door
kb.bbox((-0.30, 0.42, 1.05), (0.30, 0.423, 1.75), "glass_frost", 0)
kb.bbox((0.28, 0.42, 0.92), (0.30, 0.44, 1.10), "gun", 0.004)                            # handle at 1.0 m
kb.bbox((-0.33, 0.42, 0.15), (0.33, 0.422, 0.20), "orange", 0)
kb.cyl((0.0, -0.41, 1.80), (0.0, -0.25, 1.80), 0.012, "steel", sides=6)                  # shower head
kb.cyl((0.0, -0.25, 1.80), (0.0, -0.22, 1.76), 0.05, "steel", sides=8)
kb.bbox((-0.41, -0.30, 0.38), (-0.37, 0.15, 0.82), "white", 0.006)                       # fold-down seat (up)
kb.bbox((-0.41, -0.20, 0.36), (-0.35, 0.05, 0.40), "gun", 0.004)
register(kb, "Furn_WetCell", C_FLOOR, 1, 1, 2, access=True)

# Kitchenette 1 x 1 x 1: counter style, cooktop and oven. Open on the viewer's
# left (+X) to join a counter run, closed on the right: the end of a run.
kb = KB()
x0, x1 = -0.5 + M, 0.5
unit_block(kb, "Counter", x0, x1, -0.45, FRONT_Y, [], [('x', x0, -0.45, TOP_FRONT)])
kb.bbox((-0.36, -0.35, 0.90), (0.36, 0.28, 0.905), "glass_dark", 0)                      # cooktop
for (cx, cy, r) in ((-0.17, -0.12, 0.09), (0.17, 0.05, 0.07)):
    kb.cyl((cx, cy, 0.905), (cx, cy, 0.907), r, "hob", sides=12)
    kb.cyl((cx, cy, 0.906), (cx, cy, 0.908), r * 0.6, "glass_dark", sides=12)
kb.bbox((-0.43, 0.40, 0.68), (0.43, 0.418, 0.84), "white", 0.006)                        # knob strip
for k in range(4):
    kb.cyl((-0.27 + k * 0.18, 0.418, 0.76), (-0.27 + k * 0.18, 0.44, 0.76), 0.022, "gun", sides=8)
kb.bbox((-0.43, 0.40, 0.13), (0.43, 0.418, 0.64), "white", 0.006)                        # oven door
kb.bbox((-0.30, 0.418, 0.25), (0.30, 0.422, 0.52), "glass_dark", 0)
kb.bbox((-0.30, 0.418, 0.57), (0.30, 0.44, 0.59), "gun", 0.004)
register(kb, "Furn_Kitchenette", C_FLOOR, 1, 1, 1, family="Counter", variant="EndOfRun", access=True)

# Compactor 1 x 1 x 2: hopper on top, press inside, cubes out of a front tray.
kb = KB()
CF = 0.22                                                    # body front
kb.bbox((-0.45, -0.45, 0.0), (0.45, CF, 0.10), "gun_dark", 0)
kb.bbox((-0.45, -0.45, 0.10), (0.45, CF, 1.55), "grey", 0.02)
kb.hull([(-0.30, -0.35, 1.55), (0.30, -0.35, 1.55), (0.30, 0.10, 1.55), (-0.30, 0.10, 1.55),
         (-0.42, -0.43, 1.90), (0.42, -0.43, 1.90), (0.42, 0.20, 1.90), (-0.42, 0.20, 1.90)], "white", 0.01)
kb.bbox((-0.43, -0.44, 1.90), (0.43, 0.21, 1.95), "gun", 0.008)
kb.bbox((-0.30, CF - 0.02, 0.75), (0.30, CF + 0.02, 1.35), "gun", 0.01)                  # press window
kb.bbox((-0.25, CF + 0.01, 0.80), (0.25, CF + 0.025, 1.30), "glass_dark", 0)
kb.bbox((-0.20, CF - 0.12, 1.05), (0.20, CF, 1.12), "steel", 0.005)                      # press plate
kb.cyl((0.0, CF - 0.06, 1.12), (0.0, CF - 0.06, 1.28), 0.03, "steel", sides=6)
kb.bbox((-0.32, CF, 0.25), (0.32, 0.44, 0.32), "gun", 0.006)                             # output tray
for k in range(2):
    kb.bbox((-0.20 + k * 0.22, CF + 0.04, 0.32), (-0.04 + k * 0.22, CF + 0.18, 0.47), "counter", 0.006)
for k in range(3):
    kb.hull([(-0.45 + k * 0.32, CF + 0.001, 0.02), (-0.30 + k * 0.32, CF + 0.001, 0.02),
             (-0.22 + k * 0.32, CF + 0.001, 0.09), (-0.37 + k * 0.32, CF + 0.001, 0.09),
             (-0.45 + k * 0.32, CF + 0.006, 0.02), (-0.22 + k * 0.32, CF + 0.006, 0.09)], "orange")
kb.bbox((0.20, CF, 1.40), (0.40, CF + 0.02, 1.50), "gun", 0.004)
kb.bbox((0.24, CF + 0.02, 1.43), (0.30, CF + 0.03, 1.47), "led_green", 0)
register(kb, "Furn_Compactor", C_FLOOR, 1, 1, 2, access=True)

# Suit station 1 x 1 x 2: upright frame holding a suit and helmet.
kb = KB()
kb.bbox((-0.45, -0.45, 0.0), (0.45, 0.40, 0.06), "gun", 0.006)
kb.bbox((-0.45, -0.45, 0.0), (0.45, -0.40, 1.95), "grey", 0.008)
for sx in (-1, 1):
    kb.bbox((sx * 0.42 - 0.03, -0.45, 0.0), (sx * 0.42 + 0.03, 0.10, 1.95), "gun", 0.006)
kb.bbox((-0.45, -0.45, 1.88), (0.45, 0.10, 1.95), "gun", 0.006)
kb.bbox((-0.03, -0.40, 1.40), (0.03, -0.10, 1.46), "gun", 0)                             # hanger arm
kb.bbox((-0.20, -0.20, 0.95), (0.20, 0.05, 1.45), "suit", 0.03)                          # torso
kb.bbox((-0.21, -0.21, 1.10), (0.21, 0.06, 1.14), "orange", 0)
kb.bbox((-0.17, -0.26, 1.00), (0.17, -0.20, 1.40), "grey", 0.02)                         # back pack
for sx in (-1, 1):
    kb.bbox((sx * 0.10 - 0.075, -0.15, 0.08), (sx * 0.10 + 0.075, 0.01, 0.95), "suit", 0.02)    # legs
    kb.bbox((sx * 0.10 - 0.08, -0.17, 0.06), (sx * 0.10 + 0.08, 0.05, 0.14), "gun", 0.01)       # boots
    kb.bbox((sx * 0.27 - 0.06, -0.14, 0.75), (sx * 0.27 + 0.06, -0.02, 1.42), "suit", 0.02)     # arms
    kb.bbox((sx * 0.27 - 0.065, -0.15, 0.70), (sx * 0.27 + 0.065, -0.01, 0.78), "gun", 0.01)    # gloves
bmh = bmesh.new()
bmesh.ops.create_icosphere(bmh, subdivisions=1, radius=0.15)
pts = [v.co + Vector((0, -0.07, 1.62)) for v in bmh.verts]
bmh.free()
kb.hull(pts, "suit")                                                                      # helmet
kb.bbox((-0.11, 0.04, 1.56), (0.11, 0.075, 1.70), "visor", 0.01)
kb.bbox((0.28, 0.05, 1.20), (0.40, 0.10, 1.45), "gun", 0.006)                             # control panel
kb.card((0.34, 0.101, 1.33), (1, 0, 0), (0, 0, 1), 0.10, 0.18, "scr_status")
register(kb, "Furn_SuitStation", C_FLOOR, 1, 1, 2, access=True)

# Analyzer 1 x 1 x 1: counter-height bench with a sample chamber.
kb = KB()
unit_block(kb, "Counter", -0.45, 0.45, -0.45, FRONT_Y, [], [('x', -0.45, -0.45, TOP_FRONT), ('x', 0.45, -0.45, TOP_FRONT)])
kb.bbox((-0.30, -0.35, 0.86), (0.10, 0.10, 0.95), "gun", 0.01)                           # chamber body
kb.bbox((-0.26, -0.31, 0.95), (0.06, 0.06, 0.951), "glass_dark", 0)
kb.bbox((-0.26, 0.10, 0.88), (0.06, 0.12, 0.94), "glass_dark", 0)                         # front window
kb.bbox((-0.12, -0.10, 0.88), (-0.08, -0.06, 0.93), "led_green", 0)                       # sample glow
kb.bbox((0.15, -0.10, 0.90), (0.42, 0.35, 0.93), "gun", 0.006)                            # screen ledge
kb.card((0.285, 0.12, 0.931), (1, 0, 0), (0, 1, 0), 0.24, 0.40, "scr_data")
kb.bbox((-0.43, 0.40, 0.66), (0.43, 0.418, 0.84), "white", 0.006)
kb.bbox((-0.43, 0.40, 0.13), (0.43, 0.418, 0.63), "white", 0.006)
kb.bbox((-0.12, 0.418, 0.74), (0.12, 0.435, 0.76), "gun", 0)
register(kb, "Furn_Analyzer", C_FLOOR, 1, 1, 1, access=True)

# Locker_Storage 1 x 1 x 1: small stackable storage locker.
kb = KB()
kb.bbox((-0.40, -0.40, 0.0), (0.40, 0.38, 0.85), "grey", 0.015)
for sx in (-1, 1):
    for sy in (-1, 1):
        kb.bbox((sx * 0.40 - 0.05 * (sx > 0), sy * 0.39 - 0.05 * (sy > 0) - 0.0, 0.0),
                (sx * 0.40 + 0.05 * (sx < 0), sy * 0.39 + 0.05 * (sy < 0), 0.85), "gun", 0.006)
kb.bbox((-0.34, -0.34, 0.85), (0.34, 0.32, 0.87), "gun", 0.004)                           # stacking lip
kb.bbox((-0.32, 0.38, 0.08), (0.32, 0.395, 0.78), "white", 0.006)
kb.bbox((0.20, 0.395, 0.38), (0.23, 0.41, 0.52), "gun", 0.003)
kb.bbox((-0.20, 0.395, 0.62), (0.05, 0.398, 0.70), "orange", 0)
register(kb, "Furn_Locker_Storage", C_FLOOR, 1, 1, 1, access=True)


# ---------------------------------------------------------------------------
# 6. DECOR (no footprint rule) AND SMALL ITEMS
# ---------------------------------------------------------------------------
def plant(kb, base=(0, 0, 0)):
    b = Vector(base)
    kb.cyl(b, b + Vector((0, 0, 0.13)), 0.07, "pot", sides=8)
    rr = random.Random(5)
    top = b + Vector((0, 0, 0.13))
    for k in range(14):
        a = 2 * math.pi * k / 14
        el = rr.uniform(0.2, 0.9)
        kb.leaf(top, (math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)),
                rr.uniform(0.09, 0.13), 0.04, "leaf" if k % 3 else "leaf_dark")
    for vine in range(3):
        p = top + Vector((0.06, -0.03 + vine * 0.03, -0.02))
        for s in range(5):
            q = p + Vector((0.012, rr.uniform(-0.02, 0.02), -0.06))
            kb.cyl(p, q, 0.004, "leaf_dark", sides=3)
            for sd in (-1, 1):
                kb.leaf(q, (0.6, sd * 0.7, -0.2), 0.05, 0.022, "leaf")
            p = q


def mug(kb, b=(0, 0, 0)):
    b = Vector(b)
    kb.cyl(b, b + Vector((0, 0, 0.095)), 0.042, "ceramic", sides=10)
    kb.cyl(b + Vector((0, 0, 0.082)), b + Vector((0, 0, 0.088)), 0.036, "coffee", sides=10)
    kb.bbox(b + Vector((0.04, -0.008, 0.025)), b + Vector((0.072, 0.008, 0.037)), "ceramic", 0)
    kb.bbox(b + Vector((0.04, -0.008, 0.068)), b + Vector((0.072, 0.008, 0.080)), "ceramic", 0)
    kb.bbox(b + Vector((0.060, -0.008, 0.025)), b + Vector((0.072, 0.008, 0.080)), "ceramic", 0)


def books(kb, b=(0, 0, 0)):
    b = Vector(b)
    rr = random.Random(3)
    x = -0.18
    for k in range(8):
        w = rr.choice((0.035, 0.045, 0.05))
        h = rr.uniform(0.20, 0.27)
        d = rr.uniform(0.15, 0.19)
        kb.bbox(b + Vector((x, -d / 2, 0)), b + Vector((x + w, d / 2, h)),
                rr.choice(("book_r", "book_b", "book_g", "book_br")), 0.004)
        x += w + 0.004


def table_lamp(kb, b=(0, 0, 0)):
    b = Vector(b)
    kb.bbox(b + Vector((-0.07, -0.07, 0)), b + Vector((0.07, 0.07, 0.03)), "gun", 0.005)
    kb.cyl(b + Vector((0, 0, 0.03)), b + Vector((0, 0, 0.21)), 0.06, "lamp", sides=8)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        kb.bbox_c(b + Vector((0.062 * math.cos(a), 0.062 * math.sin(a), 0.12)), (0.012, 0.012, 0.18), "gun", 0)
    kb.bbox(b + Vector((-0.07, -0.07, 0.21)), b + Vector((0.07, 0.07, 0.24)), "gun", 0.005)


def rug(kb, w=1.9, l=2.9):
    kb.bbox((-w / 2, -l / 2, 0), (w / 2, l / 2, 0.010), "rug_base", 0)
    for (xa, xb, k) in ((-0.85, -0.75, "rug_light"), (-0.68, -0.63, "rug_dark"), (-0.52, -0.46, "rug_light"),
                        (0.46, 0.52, "rug_light"), (0.63, 0.68, "rug_dark"), (0.75, 0.85, "rug_light")):
        kb.bbox((xa * w / 1.9, -l / 2 + 0.06, 0.010), (xb * w / 1.9, l / 2 - 0.06, 0.012), k, 0)
    for yy in (-l / 2 + 0.03, l / 2 - 0.05):
        kb.bbox((-w / 2 + 0.03, yy, 0.010), (w / 2 - 0.03, yy + 0.02, 0.012), "rug_light", 0)


for nm, fn in (("Plant", plant), ("Mug", mug), ("Books", books), ("TableLamp", table_lamp)):
    kb = KB()
    fn(kb)
    register(kb, f"Decor_{nm}", C_DECOR, cat="decor")
kb = KB()
rug(kb)
register(kb, "Decor_Rug_2x3", C_DECOR, cat="decor")

# Coffee machine (origin at the base centre).
kb = KB()
kb.bbox((-0.13, -0.16, 0.0), (0.13, 0.14, 0.03), "gun", 0.006)
kb.bbox((-0.13, -0.16, 0.03), (0.13, -0.02, 0.38), "white", 0.012)
kb.bbox((-0.13, -0.16, 0.30), (0.13, 0.12, 0.38), "white", 0.012)
kb.bbox((-0.09, -0.02, 0.03), (0.09, 0.12, 0.045), "grate", 0)                            # drip tray
kb.cyl((0, 0.04, 0.045), (0, 0.04, 0.20), 0.065, "glass_dark", sides=10)                  # carafe
kb.cyl((0, 0.04, 0.045), (0, 0.04, 0.12), 0.062, "coffee", sides=10)
kb.bbox((-0.10, 0.12, 0.31), (0.10, 0.13, 0.37), "gun_dark", 0)
for k in range(3):
    kb.bbox((-0.07 + k * 0.05, 0.13, 0.33), (-0.04 + k * 0.05, 0.135, 0.35), "led_amber" if k == 1 else "led_green", 0)
register(kb, "Decor_CoffeeMachine", C_DECOR, cat="small")

# Light switch: small flat wall screen, 0.15 x 0.25 m; origin at the back.
kb = KB()
kb.bbox((-0.075, 0.0, -0.125), (0.075, 0.012, 0.125), "white", 0.004)
kb.card((0, 0.0125, 0.03), (1, 0, 0), (0, 0, 1), 0.11, 0.13, "scr_light")
for k in range(2):
    kb.bbox((-0.05 + k * 0.06, 0.012, -0.10), (-0.01 + k * 0.06, 0.016, -0.07), "gun", 0)
register(kb, "Decor_LightSwitch", C_DECOR, cat="small")

# Picture frame; origin at the back.
kb = KB()
kb.bbox((-0.17, 0.0, -0.13), (0.17, 0.02, 0.13), "gun", 0.004)
kb.card((0, 0.0205, 0), (1, 0, 0), (0, 0, 1), 0.30, 0.22, "img_landscape")
register(kb, "Decor_PictureFrame", C_DECOR, cat="small")

# Clock; origin at the back.
kb = KB()
kb.cyl((0, 0, 0), (0, 0.03, 0), 0.13, "gun", sides=16)
kb.cyl((0, 0.03, 0), (0, 0.032, 0), 0.115, "paper", sides=16)
kb.bbox_c((0, 0.034, 0.035), (0.008, 0.003, 0.08), "gun_dark", 0)
kb.bbox_c((0.025, 0.035, 0.0), (0.06, 0.003, 0.008), "gun_dark", 0, rot(ry=-30))
for k in range(12):
    a = 2 * math.pi * k / 12
    kb.bbox_c((0.1 * math.sin(a), 0.033, 0.1 * math.cos(a)), (0.008, 0.002, 0.008), "gun_dark", 0)
register(kb, "Decor_Clock", C_DECOR, cat="small")


# Desk lamp: weighted base, two-part arm, shade with a warm bulb (origin at the base).
kb = KB()
kb.cyl((0, 0, 0), (0, 0, 0.025), 0.075, "gun", sides=10)
kb.cyl((0, 0, 0.025), (0, 0, 0.035), 0.06, "gun_dark", sides=10)
j1 = Vector((0.0, -0.02, 0.035))
j2 = Vector((0.04, -0.05, 0.30))
j3 = Vector((0.18, 0.06, 0.40))
kb.cyl(j1, j2, 0.009, "steel", sides=6)
kb.cyl(j2, j3, 0.009, "steel", sides=6)
kb.cyl(j2 + Vector((-0.02, 0, 0)), j2 + Vector((0.02, 0, 0)), 0.016, "gun", sides=8)
sh_top, sh_bot = j3 + Vector((0.02, 0.02, -0.01)), j3 + Vector((0.07, 0.07, -0.12))
DL_SHADE = (sh_top, sh_bot)
kb.cyl(sh_top, sh_bot + (sh_bot - sh_top) * 0.0, 0.03, "orange", sides=10)
kb.cyl(sh_bot - (sh_bot - sh_top).normalized() * 0.005, sh_bot, 0.055, "orange", sides=10)
kb.cyl(sh_bot - (sh_bot - sh_top).normalized() * 0.002, sh_bot + (sh_bot - sh_top).normalized() * 0.001, 0.045, "lamp", sides=10)
register(kb, "Decor_DeskLamp", C_DECOR, cat="small")

# Small radio: boxy, speaker grille, dial window, knobs, telescopic antenna.
kb = KB()
kb.bbox((-0.13, -0.05, 0.0), (0.13, 0.05, 0.14), "gun", 0.01)
kb.bbox((-0.12, 0.05, 0.02), (-0.01, 0.055, 0.12), "grate", 0)
for k in range(5):
    kb.bbox((-0.115, 0.055, 0.03 + k * 0.018), (-0.015, 0.058, 0.037 + k * 0.018), "gun_dark", 0)
kb.bbox((0.01, 0.05, 0.075), (0.12, 0.056, 0.12), "gun_dark", 0)
kb.bbox((0.015, 0.056, 0.08), (0.115, 0.058, 0.115), "radio_glow", 0)
for x in (0.035, 0.095):
    kb.cyl((x, 0.05, 0.045), (x, 0.068, 0.045), 0.014, "steel", sides=8)
kb.bbox((-0.10, -0.03, 0.14), (0.10, 0.03, 0.155), "orange", 0.004)                         # handle
kb.cyl((0.11, -0.03, 0.14), (0.16, -0.03, 0.40), 0.003, "steel", sides=4)                   # antenna
register(kb, "Decor_Radio", C_DECOR, cat="small")

# Taped photos: two small prints taped to a wall; origin at the back.
kb = KB()
for (x, z, w, h, a, img) in ((-0.07, 0.03, 0.12, 0.09, 4, "img_landscape"), (0.06, -0.04, 0.10, 0.12, -6, "img_landscape")):
    R = rot(ry=a)
    c = Vector((x, 0.003, z))
    kb.bbox_c(c + Vector((0, -0.0015, 0)), (w + 0.012, 0.002, h + 0.012), "paper", 0, R)
    kb.card(c + Vector((0, 0.0002, 0)), R.to_3x3() @ Vector((1, 0, 0)), R.to_3x3() @ Vector((0, 0, 1)), w, h, img)
    for sx in (-1, 1):
        kb.bbox_c(c + R.to_3x3() @ Vector((sx * w * 0.4, 0.001, h / 2)), (0.04, 0.001, 0.014), "paper", 0, R)
register(kb, "Decor_TapedPhotos", C_DECOR, cat="small")

# Wall shelf: gunmetal bracket shelf, 0.9 m, light strip underneath; origin at the
# back centre of the shelf board (bottom).
kb = KB()
kb.bbox((-0.45, 0.0, 0.0), (0.45, 0.24, 0.025), "counter", 0.004)
kb.bbox((-0.45, 0.22, 0.025), (0.45, 0.24, 0.05), "gun", 0.003)                             # front lip
for x in (-0.33, 0.33):
    kb.hull([(x - 0.01, 0.0, 0.0), (x + 0.01, 0.0, 0.0), (x - 0.01, 0.0, -0.16), (x + 0.01, 0.0, -0.16),
             (x - 0.01, 0.20, 0.0), (x + 0.01, 0.20, 0.0)], "gun")
    kb.cyl((x, 0.0, -0.10), (x, 0.01, -0.10), 0.01, "steel", sides=6)
kb.bbox((-0.40, 0.10, -0.012), (0.40, 0.16, 0.0), "gun_dark", 0)
kb.bbox((-0.38, 0.11, -0.016), (0.38, 0.15, -0.012), "amber", 0)
register(kb, "Decor_WallShelf", C_DECOR, cat="small")

# Potted plant (bushy, for desks and counters): angular pot, broad leaves.
kb = KB()
kb.cyl((0, 0, 0), (0, 0, 0.16), 0.07, "ceramic", sides=8, r2=0.085)
kb.cyl((0, 0, 0.15), (0, 0, 0.155), 0.08, "soil", sides=8)
rr = random.Random(12)
for k in range(16):
    a = 2 * math.pi * k / 16 + rr.uniform(-0.2, 0.2)
    el = rr.uniform(0.35, 1.2)
    base = Vector((rr.uniform(-0.02, 0.02), rr.uniform(-0.02, 0.02), 0.155))
    tip_dir = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)))
    stem_end = base + tip_dir * rr.uniform(0.06, 0.14)
    kb.cyl(base, stem_end, 0.003, "leaf_dark", sides=3)
    kb.leaf(stem_end, tip_dir + Vector((0, 0, -0.3)), rr.uniform(0.09, 0.14), 0.05, "leaf" if k % 3 else "leaf_dark")
register(kb, "Decor_PlantPotted", C_DECOR, cat="small")


# ---------------------------------------------------------------------------
# 7. WALL PANELS: cut from real slots of the compartment generator
# ---------------------------------------------------------------------------
G = compartment_geometry(3, 4, 3)                    # a Cabin: rows 0, 1 and the chamfer row
SLOTS = {s[0]: s for s in slot_list("Lib", G)}
EDGE_COL = {"": 1, "EdgeL": 0, "EdgeR": 2}           # Right wall: column 0 = viewer's left end


def slot_mesh(kind_row, edge):
    """A finished plain slot (same function as the compartments), moved into the
    panel frame: origin at the bottom centre of the inner face, +Y into the room."""
    c = EDGE_COL[edge]
    key = f"Lib_Right_{c:02d}_{'Chamfer' if kind_row == 'chamfer' else ('00' if kind_row == 'floor' else '01')}"
    sname, faces, owners, tags = SLOTS[key]
    ob = slot_object("TMP_slot", faces, owners, tags, G, KIT_TMP)
    yc = G.hl - c - 0.5
    z0 = {"floor": 0.0, "mid": 1.0, "chamfer": G.H - 1.0}[kind_row]
    P = Matrix.Translation((G.hw, yc, z0)) @ Matrix.Rotation(math.radians(90), 4, 'Z')
    ob.data.transform(P.inverted())
    return ob


def apply_cutters(ob, cutters):
    """Boolean difference with temporary cutter meshes (lists of KB)."""
    obs = []
    for i, kb in enumerate(cutters):
        co = kb.finish(f"TMP_cut{i}", KIT_TMP)
        m = ob.modifiers.new(co.name, 'BOOLEAN')
        m.operation = 'DIFFERENCE'
        m.object = co
        m.solver = 'EXACT'
        obs.append(co)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    for co in obs:
        bpy.data.objects.remove(co, do_unlink=True)
    ob.modifiers.clear()
    old = ob.data
    ob.data = me
    bpy.data.meshes.remove(old)
    return ob


def merge_into(kb, ob):
    """Append an object's mesh (with its materials) into a KB builder."""
    me = ob.data
    names = [m for m in me.materials]
    start = len(kb.bm.faces)
    kb.bm.from_mesh(me)
    kb.bm.faces.ensure_lookup_table()
    inv = {v: k for k, v in MAT.items()}
    for f in list(kb.bm.faces)[start:]:
        mat = names[f.material_index] if f.material_index < len(names) else None
        f.material_index = kb.slot(inv.get(mat, "recess"))
    bpy.data.objects.remove(ob, do_unlink=True)


def recess_box(x0, x1, z0, z1, depth):
    c = KB()
    c.bbox((x0, -depth, z0), (x1, 0.2, z1), "recess", 0)
    return c


def niche_back(kb, x0, x1, z0, z1, depth, key="grey"):
    kb.bbox((x0, -depth, z0), (x1, -depth + 0.01, z1), key, 0)


RIM = 0.05


def panel_body(kind_row, edge, cutters):
    ob = slot_mesh(kind_row, edge)
    if cutters:
        apply_cutters(ob, cutters)
    kb = KB()
    merge_into(kb, ob)
    return kb


def wall_cabinet(variant, edge):
    cm, cp = closed_sides(variant) if variant != "Single" else (True, True)
    x0 = -0.5 + (RIM if cm else -0.02)
    x1 = 0.5 - (RIM if cp else -0.02)
    kb = panel_body("mid", edge, [recess_box(x0, x1, RIM, 1 - RIM, 0.30)])
    niche_back(kb, max(x0, -0.5), min(x1, 0.5), RIM, 1 - RIM, 0.30)
    kb.bbox((max(x0, -0.5), -0.30, 0.48), (min(x1, 0.5), -0.02, 0.50), "grey", 0)        # inner shelf
    d0, d1 = max(x0, -0.5) + 0.004, min(x1, 0.5) - 0.004
    dm = (d0 + d1) / 2
    for (a_, b_, hx) in ((d0, dm - 0.006, dm - 0.06), (dm + 0.006, d1, dm + 0.02)):       # two flush doors
        kb.bbox((a_, -0.022, RIM + 0.004), (b_, -0.002, 1 - RIM - 0.004), "white", 0.006)
        kb.bbox((hx, -0.006, 0.12), (hx + 0.04, -0.0015, 0.30), "gun_dark", 0)            # inset handle
    trim(kb, x0, x1, RIM, 1 - RIM, cm, cp, t=0.04, d=0.02)
    kb.bbox((max(x0, -0.5) + 0.03, 0.004, RIM - 0.04), (min(x1, 0.5) - 0.03, 0.022, RIM - 0.033), "amber", 0)
    return kb


def trim(kb, x0, x1, z0, z1, cm=True, cp=True, t=0.025, d=0.012):
    """Gunmetal frame round a panel opening, 1.2 cm proud of the wall; merged
    sides get no vertical trim so a run reads as one cabinet."""
    xa, xb = max(x0, -0.5), min(x1, 0.5)
    kb.bbox((xa - (t if cm else 0), 0.0, z1), (xb + (t if cp else 0), d, z1 + t), "gun", 0.003)
    kb.bbox((xa - (t if cm else 0), 0.0, z0 - t), (xb + (t if cp else 0), d, z0), "gun", 0.003)
    if cm:
        kb.bbox((xa - t, 0.0, z0), (xa, d, z1), "gun", 0.003)
    if cp:
        kb.bbox((xb, 0.0, z0), (xb + t, d, z1), "gun", 0.003)


def shelf_niche(edge):
    kb = panel_body("mid", edge, [recess_box(-0.5 + RIM, 0.5 - RIM, RIM, 1 - RIM, 0.28)])
    niche_back(kb, -0.45, 0.45, RIM, 1 - RIM, 0.28)
    trim(kb, -0.5 + RIM, 0.5 - RIM, RIM, 1 - RIM)
    kb.bbox((-0.45, -0.28, 0.44), (0.45, 0.0, 0.47), "counter", 0.004)
    kb.bbox((-0.40, -0.10, 1 - RIM - 0.015), (0.40, -0.03, 1 - RIM), "amber", 0)
    books(kb, (0.05, -0.13, 0.47))
    return kb


def wall_light(edge):
    kb = panel_body("mid", edge, [recess_box(-0.38, 0.38, 0.22, 0.78, 0.06)])
    kb.bbox((-0.38, -0.06, 0.22), (0.38, -0.05, 0.78), "gun_dark", 0)
    kb.bbox((-0.33, -0.03, 0.27), (0.33, -0.02, 0.73), "lamp", 0)
    return kb


def vent(edge):
    kb = panel_body("mid", edge, [recess_box(-0.40, 0.40, 0.20, 0.80, 0.12)])
    kb.bbox((-0.40, -0.12, 0.20), (0.40, -0.11, 0.80), "gun_dark", 0)
    for k in range(10):
        z = 0.24 + k * 0.055
        kb.bbox_c((0, -0.03, z), (0.78, 0.02, 0.012), "gun", 0, rot(rx=-30))
    return kb


def screen(edge, img="scr_status", ledge=False):
    kb = panel_body("mid", edge, [recess_box(-0.40, 0.40, 0.20 if ledge else 0.18, 0.86, 0.05)])
    kb.bbox((-0.40, -0.05, 0.20 if ledge else 0.18), (0.40, -0.04, 0.86), "gun_dark", 0)
    kb.bbox((-0.37, -0.04, 0.26), (0.37, 0.015, 0.80), "gun", 0.008)                       # bezel
    kb.card((0, 0.0155, 0.53), (1, 0, 0), (0, 0, 1), 0.68, 0.48, img)
    if ledge:                                                                              # keyboard ledge
        kb.bbox((-0.35, 0.0, 0.05), (0.35, 0.20, 0.08), "gun", 0.008)
        kb.bbox((-0.28, 0.04, 0.08), (0.28, 0.16, 0.095), "gun_dark", 0.004)
        for r_ in range(3):
            for k in range(10):
                kb.bbox((-0.26 + k * 0.052, 0.05 + r_ * 0.035, 0.095), (-0.22 + k * 0.052, 0.078 + r_ * 0.035, 0.10),
                        "grey", 0)
    return kb


def porthole(edge):
    cut = KB()
    cut.cyl((0, -0.6, 0.5), (0, 0.3, 0.5), 0.30, "recess", sides=24)
    kb = panel_body("mid", edge, [cut])
    kb.ring((0, 0.0, 0.5), (0, 1, 0), 0.30, 0.42, 0.035, "gun", sides=24)                 # inside ring
    kb.ring((0, -0.35, 0.5), (0, -1, 0), 0.30, 0.40, 0.03, "gun", sides=24)               # outside ring
    for k in range(10):
        a = 2 * math.pi * k / 10
        for (y0, y1) in ((0.035, 0.05), (-0.38, -0.395)):
            kb.cyl((0.36 * math.cos(a), y0, 0.5 + 0.36 * math.sin(a)),
                   (0.36 * math.cos(a), y1, 0.5 + 0.36 * math.sin(a)), 0.018, "steel", sides=6)
    pts = [Vector((0.30 * math.cos(2 * math.pi * k / 24), -0.175, 0.5 + 0.30 * math.sin(2 * math.pi * k / 24)))
           for k in range(24)]
    kb.face(pts, "glass", normal=(0, 1, 0))
    return kb


def pinboard(edge):
    kb = panel_body("mid", edge, [recess_box(-0.44, 0.44, 0.10, 0.90, 0.02)])
    kb.bbox((-0.44, -0.02, 0.10), (0.44, 0.01, 0.90), "gun", 0.006)
    kb.bbox((-0.41, 0.0, 0.13), (0.41, 0.015, 0.87), "cork", 0.004)
    rr = random.Random(2)
    for k in range(5):
        x, z = rr.uniform(-0.3, 0.3), rr.uniform(0.25, 0.75)
        kb.bbox((x - 0.07, 0.015, z - 0.05), (x + 0.07, 0.017, z + 0.05), "paper", 0)
        kb.bbox((x - 0.008, 0.017, z + 0.03), (x + 0.008, 0.022, z + 0.045), "orange", 0)
    kb.card((0.16, 0.0175, 0.62), (1, 0, 0), (0, 0, 1), 0.20, 0.14, "img_landscape")
    return kb


# Fold table (floor-row slot). Hinge axis at Y 0, Z 0.75 (the top front edge
# of the folded leaf). Unity rotates Wall_FoldTable_Top +90 deg about X to open.
LEAF_L, LEAF_T, HINGE_Z = 0.74, 0.03, 0.75


def fold_leaf(kb, opened, M_=None):
    if not opened:
        kb.bbox((-0.40, -LEAF_T, HINGE_Z - LEAF_L), (0.40, 0.0, HINGE_Z), "white", 0.006, M_)
        kb.bbox((-0.12, -0.004, HINGE_Z - LEAF_L + 0.05), (0.12, 0.0005, HINGE_Z - LEAF_L + 0.08), "gun_dark", 0, M_)
    else:
        kb.bbox((-0.40, 0.0, HINGE_Z - LEAF_T), (0.40, LEAF_L, HINGE_Z), "counter", 0.006, M_)


def fold_table(edge, opened):
    kb = panel_body("floor", edge, [recess_box(-0.42, 0.42, 0.0, HINGE_Z + 0.02, 0.035)])
    kb.bbox((-0.42, -0.035, 0.0), (0.42, -0.03, HINGE_Z + 0.02), "gun_dark", 0)
    kb.bbox((-0.42, -0.01, HINGE_Z), (0.42, 0.012, HINGE_Z + 0.02), "gun", 0.004)        # hinge rail
    fold_leaf(kb, opened)
    if opened:                                                                           # fold-out brackets
        for x in (-0.30, 0.30):
            kb.hull([(x - 0.01, 0.0, HINGE_Z - LEAF_T - 0.30), (x + 0.01, 0.0, HINGE_Z - LEAF_T - 0.30),
                     (x - 0.01, 0.0, HINGE_Z - LEAF_T), (x + 0.01, 0.0, HINGE_Z - LEAF_T),
                     (x - 0.01, 0.40, HINGE_Z - LEAF_T), (x + 0.01, 0.40, HINGE_Z - LEAF_T)], "gun")
    return kb


def chamfer_cabinet(variant, edge):
    """Overhead cabinet replacing a Chamfer slot: a recess that follows the
    vertical top row and the 45 degree chamfer, with two flush doors."""
    cm, cp = closed_sides(variant) if variant != "Single" else (True, True)
    x0 = -0.5 + (RIM if cm else -0.02)
    x1 = 0.5 - (RIM if cp else -0.02)
    D = 0.28
    s = 1 / math.sqrt(2)
    # profile in (y, z): inner surface A-B-C, offset outward by D
    A, B = Vector((0.0, RIM)), Vector((0.0, 0.5))
    C = B + Vector((s, s)) * (0.707 - 0.08)
    out_v, out_c = Vector((-1, 0)), Vector((-s, s))
    Bp = Vector((-D, 0.5 + D * math.tan(math.radians(22.5))))
    prof = [A + Vector((0.01, 0)), B + Vector((0.01, -0.004)), C + Vector((s, -s)) * 0.01,
            C + out_c * D, Bp, A + out_v * D]
    cut = KB()
    cut.prism([Vector((x0, p.x, p.y)) for p in prof], (x1 - x0, 0, 0), "recess")
    kb = panel_body("chamfer", edge, [cut])
    d0, d1 = max(x0, -0.5) + 0.004, min(x1, 0.5) - 0.004
    kb.bbox((d0, -0.022, RIM + 0.004), (d1, -0.002, 0.496), "grey", 0.006)              # lower door
    xa, xb = max(x0, -0.5), min(x1, 0.5)
    kb.bbox((xa - (0.025 if cm else 0), 0.0, RIM - 0.025), (xb + (0.025 if cp else 0), 0.012, RIM), "gun", 0.003)
    Rm = Matrix.Translation((0, 0, 0)) @ rot(rx=45)
    L_ = 0.707 - 0.09
    mid = B + Vector((s, s)) * (L_ / 2 + 0.005)
    kb.bbox_c(Vector((0, mid.x, mid.y)) + Vector((0, -s, s)) * 0.012, (d1 - d0, 0.02, L_ - 0.01), "grey", 0.006, rot(rx=-45))
    hx = d1 - 0.09 if cp or variant == "Mid" else d0 + 0.05
    kb.bbox((hx, -0.004, 0.10), (hx + 0.04, 0.0005, 0.22), "gun_dark", 0)
    return kb


def window_hex(edge):
    """Chamfered-hexagon window through the slot (glass in the middle of the
    wall), with a bolted frame inside and out."""
    W2, H2, C = 0.42, 0.30, 0.17                    # half width, half height, chamfer
    zc = 0.5
    poly = [(-W2 + C, -H2), (W2 - C, -H2), (W2, -H2 + C), (W2, H2 - C), (W2 - C, H2),
            (-W2 + C, H2), (-W2, H2 - C), (-W2, -H2 + C)]
    cut = KB()
    cut.prism([Vector((x, 0.3, zc + z)) for (x, z) in poly], (0, -0.8, 0), "recess")
    kb = panel_body("mid", edge, [cut])
    outer = offset_poly(poly, [-0.075] * len(poly))

    def frame_ring(y0, y1, key):
        n = len(poly)
        for i in range(n):
            j = (i + 1) % n
            a, b, c, d = (Vector(v) for v in (poly[i], poly[j], outer[j], outer[i]))

            def P(v, y):
                return Vector((v.x, y, zc + v.y))
            kb.face([P(a, y1), P(b, y1), P(c, y1), P(d, y1)], key, normal=(0, 1, 0) if y1 > y0 else (0, -1, 0))
            kb.face([P(c, y0), P(c, y1), P(d, y1), P(d, y0)], key,
                    normal=(((c + d) / 2).x, 0, ((c + d) / 2).y))
            kb.face([P(a, y0), P(a, y1), P(b, y1), P(b, y0)], key, normal=(-((a + b) / 2).x, 0, -((a + b) / 2).y))
    frame_ring(0.0, 0.045, "gun")                     # inside frame, 4.5 cm proud
    frame_ring(-0.35, -0.385, "gun")                  # outside frame
    # inner chamfer liner through the wall
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        a, b = Vector(poly[i]), Vector(poly[j])
        kb.face([Vector((a.x, 0.0, zc + a.y)), Vector((b.x, 0.0, zc + b.y)),
                 Vector((b.x, -0.35, zc + b.y)), Vector((a.x, -0.35, zc + a.y))], "gun_dark",
                normal=(-((a + b) / 2).x, 0, -((a + b) / 2).y))
    # bolts at the corners and mid-edges of both frames
    for i in range(n):
        for t in (0.0, 0.5):
            p = Vector(outer[i]).lerp(Vector(outer[(i + 1) % n]), t)
            q = Vector(poly[i]).lerp(Vector(poly[(i + 1) % n]), t)
            m = (p + q) / 2
            for (y0, y1) in ((0.045, 0.055), (-0.385, -0.395)):
                kb.cyl((m.x, y0, zc + m.y), (m.x, y1, zc + m.y), 0.011, "steel", sides=6)
    kb.face([Vector((x, -0.175, zc + z)) for (x, z) in poly], "glass", normal=(0, 1, 0))
    return kb


EDGES = ["", "EdgeL", "EdgeR"]


def reg_panel(kb, name, access=False, group=None, variant="-", coll=C_WALL):
    register(kb, name, coll, family=("WallCabinet" if "Chamfer" not in name else "WallChamfer_WallCabinet")
             if "WallCabinet" in name else "none",
             variant=variant, access=access, group=group or "_".join(name.split("_")[:2]),
             cat="wall", access_y=0.5)


for edge in EDGES:
    sfx = f"_{edge}" if edge else ""
    for var in ("Single", "EndL", "Mid", "EndR"):
        reg_panel(wall_cabinet(var, edge), f"Wall_WallCabinet_{var}{sfx}", True, "Wall_WallCabinet", var + sfx)
        reg_panel(chamfer_cabinet(var, edge), f"WallChamfer_WallCabinet_{var}{sfx}", True,
                  "WallChamfer_WallCabinet", var + sfx)
    reg_panel(shelf_niche(edge), f"Wall_ShelfNiche{sfx}", True, "Wall_ShelfNiche", "Single" + sfx)
    reg_panel(wall_light(edge), f"Wall_WallLight{sfx}", False, "Wall_WallLight", "Single" + sfx)
    reg_panel(vent(edge), f"Wall_Vent{sfx}", False, "Wall_Vent", "Single" + sfx)
    reg_panel(screen(edge), f"Wall_Screen{sfx}", False, "Wall_Screen", "Single" + sfx)
    reg_panel(porthole(edge), f"Wall_Porthole{sfx}", False, "Wall_Porthole", "Single" + sfx)
    reg_panel(window_hex(edge), f"Wall_WindowHex{sfx}", False, "Wall_WindowHex", "Single" + sfx)
    reg_panel(pinboard(edge), f"Wall_Pinboard{sfx}", False, "Wall_Pinboard", "Single" + sfx)
    reg_panel(fold_table(edge, False), f"Wall_FoldTable_Folded{sfx}", True, "Wall_FoldTable", "Folded" + sfx)
    reg_panel(fold_table(edge, True), f"Wall_FoldTable_Open{sfx}", True, "Wall_FoldTable", "Open" + sfx)
    reg_panel(screen(edge, "scr_starmap", ledge=True), f"Wall_Terminal{sfx}", True, "Wall_Terminal", "Single" + sfx)
# The hinged top on its own; origin on the hinge axis, modelled folded (hanging).
kb = KB()
fold_leaf(kb, False, Matrix.Translation((0, 0, -HINGE_Z)))
reg_panel(kb, "Wall_FoldTable_Top", False, "Wall_FoldTable", "HingedTop")

# ---------------------------------------------------------------------------
# 8. DOORWAY BETWEEN COMPARTMENTS: frame (1 m deep) and sliding leaf
#    Origin: centre of the opening at floor level, halfway through the 1 m gap.
#    The opening is in the XZ plane; you walk through along Y.
# ---------------------------------------------------------------------------
kb = KB()
DW, DH, DD = 1.0, 2.0, 1.0
L_ = 0.05                                                     # liner thickness
for sx in (-1, 1):                                            # side liners
    xa, xb = sorted((sx * DW / 2, sx * (DW / 2 - L_)))
    kb.bbox((xa, -DD / 2, 0.0), (xb, DD / 2, DH), "gun", 0.006)
kb.bbox((-DW / 2, -DD / 2, DH - L_), (DW / 2, DD / 2, DH), "gun", 0.006)                    # lintel
# threshold: fills the mitred bottom of both walls and the gap between them
prof = [(-DD / 2, 0.0), (-DD / 2 + T, -T), (DD / 2 - T, -T), (DD / 2, 0.0)]
kb.prism([Vector((-DW / 2, y, z)) for (y, z) in prof], (DW, 0, 0), "gun_dark", 0.0)
kb.bbox((-DW / 2 + L_, -DD / 2 + 0.02, -0.004), (DW / 2 - L_, DD / 2 - 0.02, 0.0), "grate", 0)
for sy in (-1, 1):                                            # orange safety edges at both ends
    y0, y1 = sorted((sy * DD / 2, sy * (DD / 2 - 0.06)))
    for sx in (-1, 1):
        xa, xb = sorted((sx * (DW / 2 - L_), sx * (DW / 2 - L_ - 0.008)))
        kb.bbox((xa, y0, 0.0), (xb, y1, DH - L_), "orange", 0)
    kb.bbox((-DW / 2 + L_, y0, DH - L_ - 0.008), (DW / 2 - L_, y1, DH - L_), "orange", 0)
    kb.bbox((-DW / 2 + L_, y0, -0.002), (DW / 2 - L_, y1, 0.003), "orange", 0)
kb.bbox((-DW / 2 + L_, -0.04, DH - L_ - 0.06), (DW / 2 - L_, 0.04, DH - L_), "gun_dark", 0)   # door track
register(kb, "Door_Frame", C_WALL, family="none", variant="-", access=False, group="Door", cat="door")
kb = KB()
lw, lh = DW - 2 * L_ - 0.004, DH - L_ - 0.064
kb.bbox((-lw / 2, -0.02, 0.0), (lw / 2, 0.02, lh), "white", 0.008)
kb.bbox((-lw / 2, -0.024, 0.0), (lw / 2, 0.024, 0.08), "gun", 0.006)
kb.bbox((-0.14, -0.024, 1.20), (0.14, 0.024, 1.55), "glass_dark", 0)
for k in range(4):
    for sy in (-1, 1):
        y = sy * 0.0245
        kb.hull([(-0.40 + k * 0.22, y, 0.08), (-0.30 + k * 0.22, y, 0.08), (-0.22 + k * 0.22, y, 0.18),
                 (-0.32 + k * 0.22, y, 0.18), (-0.40 + k * 0.22, y + sy * 0.002, 0.08),
                 (-0.22 + k * 0.22, y + sy * 0.002, 0.18)], "orange")
for sy in (-1, 1):
    kb.bbox((0.32, sy * 0.024 - 0.002, 0.92), (0.36, sy * 0.024 + 0.002, 1.08), "gun_dark", 0)
register(kb, "Door_Leaf", C_WALL, family="none", variant="-", access=False, group="Door", cat="door")

bpy.data.collections.remove(KIT_TMP)
# ---------------------------------------------------------------------------
# 9. CHECKS + MANIFEST
# ---------------------------------------------------------------------------
over, outside = [], []
for p in PIECES:
    if p["tris"] > 1500:
        over.append((p["name"], p["tris"]))
    if p["cat"] == "floor" and p["W"]:
        vs = [v.co for v in p["ob"].data.vertices]
        lo = [min(v[i] for v in vs) for i in range(3)]
        hi = [max(v[i] for v in vs) for i in range(3)]
        lim = (p["W"] / 2, p["L"] / 2, p["H"])
        merge = p["family"] in FAMILIES or p["variant"] == "EndOfRun"
        m_ = 0.0 if merge else M - 1e-4
        bad = (lo[0] < -lim[0] + m_ - 1e-4 or hi[0] > lim[0] - m_ + 1e-4 or lo[1] < -lim[1] + (0.0 if p["variant"] == "CornerOut" else M) - 0.0101 or
               hi[1] > lim[1] - (0.0 if p["variant"] in ("CornerIn",) else M) + 1e-3 or lo[2] < -1e-4 or
               hi[2] > lim[2] - M + 1e-3)
        if bad:
            outside.append((p["name"], [round(x, 3) for x in lo], [round(x, 3) for x in hi]))
print("\n--- Kit report ---")
print("pieces:", len(PIECES), " over budget:", over or "none")
print("outside footprint margin:", outside or "none")
os.makedirs(KIT_DIR, exist_ok=True)
with open(os.path.join(KIT_DIR, "kit_manifest.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["name", "footprint_WxLxH", "merge_family", "variant", "access_marker", "triangles"])
    for p in PIECES:
        if p["cat"] in ("floor",):
            fp = f"{p['W']}x{p['L']}x{p['H']}"
        elif p["cat"] == "wall":
            fp = "wall slot (chamfer row)" if p["name"].startswith("WallChamfer") else \
                 ("wall slot (floor row)" if "FoldTable" in p["name"] else "wall slot")
        elif p["cat"] == "door":
            fp = "doorway 1x2 (1 m deep)"
        else:
            fp = "none (decor/small item)"
        w.writerow([p["name"], fp, p["family"] if p["family"] != "none" else "none",
                    p["variant"], "yes" if p["access"] else "no", p["tris"]])
print("manifest written:", len(PIECES), "rows")


# ---------------------------------------------------------------------------
# 10. CATALOGUE LAYOUT (labelled grid) + 1.8 m scale figure
# ---------------------------------------------------------------------------
C_RENDER_KIT = new_collection("RENDER_ONLY_Kit")
by_name = {p["name"]: p for p in PIECES}


def short(n):
    for pre in ("Furn_", "Decor_", "WallChamfer_", "Wall_"):
        if n.startswith(pre):
            return ("Chamfer " if pre == "WallChamfer_" else "") + n[len(pre):].replace("_", " ")
    return n.replace("_", " ")


ROWS = [
    [f"Furn_Counter_{v}" for v in VARIANTS] + [f"Furn_LowCabinet_{v}" for v in VARIANTS],
    [f"Furn_Locker_{v}" for v in VARIANTS] + [f"Furn_Shelf_{v}" for v in VARIANTS],
    ["Furn_Bed", "Furn_Bunk", "Furn_Wardrobe", "Furn_Desk", "Furn_Dinette", "Furn_StorageCase",
     "Furn_Smelter", "Furn_Fabricator", "Furn_Hydroponics"],
    ["Furn_Chair", "Furn_WetCell", "Furn_Kitchenette", "Furn_Compactor", "Furn_SuitStation",
     "Furn_Analyzer", "Furn_Locker_Storage", "Door_Frame", "Door_Leaf"],
    [f"Wall_WallCabinet_{v}" for v in ("Single", "EndL", "Mid", "EndR")] +
    ["Wall_ShelfNiche", "Wall_WallLight", "Wall_Vent", "Wall_Screen", "Wall_Porthole", "Wall_WindowHex", "Wall_Pinboard",
     "Wall_Terminal", "Wall_FoldTable_Folded", "Wall_FoldTable_Open", "Wall_FoldTable_Top"],
    [f"WallChamfer_WallCabinet_{v}" for v in ("Single", "EndL", "Mid", "EndR")] +
    ["Decor_Plant", "Decor_Mug", "Decor_Books", "Decor_TableLamp", "Decor_CoffeeMachine",
     "Decor_LightSwitch", "Decor_PictureFrame", "Decor_Clock", "Decor_DeskLamp", "Decor_Radio",
     "Decor_TapedPhotos", "Decor_WallShelf", "Decor_PlantPotted", "Decor_Rug_2x3", "HUMAN"],
]
label_mat = make_mat("M_Label", "#2B2A2E", rough=0.9)


def label(text, x, y):
    cu = bpy.data.curves.new(f"lbl_{text}", 'FONT')
    cu.body = text
    cu.size = 0.15
    cu.align_x = 'CENTER'
    ob = bpy.data.objects.new(f"LABEL_{text}", cu)
    C_RENDER_KIT.objects.link(ob)
    ob.location = (x, y, 0.003)
    ob.rotation_euler = (0, 0, math.radians(180))
    cu.materials.append(label_mat)
    return ob


def extent(ob):
    vs = [v.co for v in ob.data.vertices]
    return (min(v.x for v in vs), max(v.x for v in vs), min(v.y for v in vs), max(v.y for v in vs),
            min(v.z for v in vs))


# scale figure (not exported)
fig = KB()
for sx in (-0.11, 0.11):
    fig.bbox((sx - 0.07, -0.08, 0), (sx + 0.07, 0.08, 0.86), "gun", 0.01)
fig.bbox((-0.21, -0.12, 0.84), (0.21, 0.12, 1.48), "gun", 0.02)
for sx in (-0.27, 0.27):
    fig.bbox((sx - 0.055, -0.06, 0.80), (sx + 0.055, 0.06, 1.45), "gun", 0.01)
fig.bbox((-0.06, -0.06, 1.48), (0.06, 0.06, 1.56), "gun", 0)
fig.cyl((0, 0, 1.56), (0, 0, 1.80), 0.11, "gun", sides=8)
human = fig.finish("RENDER_ScaleFigure_1p8m", C_RENDER_KIT)

y_cursor = 0.0
cat_lo, cat_hi = [1e9, 1e9], [-1e9, -1e9]
ROW_HEAD = ["Counter  |  LowCabinet", "Locker  |  Shelf", "", "", "Wall panels", "Chamfer cabinets  |  decor"]
for ri, row in enumerate(ROWS):
    row_kind = "family" if ri < 2 else "piece"
    items = []
    for n in row:
        ob = human if n == "HUMAN" else by_name[n]["ob"]
        items.append((n, ob, extent(ob)))
    depth = max(e[3] - e[2] for (_, _, e) in items)
    widths = [max(1.05, (e[1] - e[0]) + 0.35) for (_, _, e) in items]
    total = sum(widths)
    x = total / 2                                     # screen-right is -X: start at +X
    for (n, ob, e), w in zip(items, widths):
        cx = x - w / 2
        ox = cx - (e[0] + e[1]) / 2
        oy = y_cursor - e[3]                          # align fronts on the row line
        lift = max(0.0, -e[4]) + (0.25 if n.startswith(("Decor_LightSwitch", "Decor_PictureFrame", "Decor_Clock", "Decor_TapedPhotos")) else 0.0)
        ob.location = (ox, oy, lift)
        txt = "1.8 m" if n == "HUMAN" else (n.split("_")[-1] if row_kind == "family" else short(n))
        label(txt, cx, y_cursor + 0.40)
        cat_lo[0] = min(cat_lo[0], cx - w / 2); cat_hi[0] = max(cat_hi[0], cx + w / 2)
        x -= w
    if ROW_HEAD[ri]:
        hd = label(ROW_HEAD[ri], (total / 2) + 0.1, y_cursor + 0.40)
        hd.data.size = 0.17
        hd.data.align_x = 'RIGHT'
        cat_hi[0] = max(cat_hi[0], total / 2 + 2.6)
    cat_lo[1] = min(cat_lo[1], y_cursor - depth)
    cat_hi[1] = max(cat_hi[1], y_cursor + 0.7)
    y_cursor -= depth + 1.05

# Edge forms of the wall panels are not shown in the catalogue: park them beside it.
park_x = cat_lo[0] - 40.0
k = 0
for p in PIECES:
    if p["ob"].location.length == 0 and p["ob"] is not human:
        p["ob"].location = (park_x - (k % 6) * 1.4, -(k // 6) * 1.4, 0.4)
        k += 1


# ---------------------------------------------------------------------------
# 11. ROOM TEST: a Cabin from the compartment generator, furnished with kit
#     pieces, with wall slots swapped for panels
# ---------------------------------------------------------------------------
RX = -100.0
room = build_compartment("Cabin", 3, 4, 3, x_offset=RX)
CAB = compartment_geometry(3, 4, 3)
room_objs = []


def place(name, loc, rz=0.0):
    src_ob = by_name[name]["ob"]
    ob = bpy.data.objects.new(f"RT_{name}", src_ob.data)
    room.objects.link(ob)
    ob.location = Vector((RX, 0, 0)) + Vector(loc)
    ob.rotation_euler = (0, 0, math.radians(rz))
    room_objs.append(ob)
    return ob


def swap_slot(slot_name, panel_name):
    """Remove a wall slot and put the panel in its place."""
    side, c, r = slot_name.split("_")[1], int(slot_name.split("_")[2]), slot_name.split("_")[3]
    r = CAB.H - 1 if r == "Chamfer" else int(r)
    bpy.data.objects.remove(bpy.data.objects[slot_name], do_unlink=True)
    if side == "Right":
        loc, rz = (CAB.hw, CAB.hl - c - 0.5, r), 90
    elif side == "Left":
        loc, rz = (-CAB.hw, -CAB.hl + c + 0.5, r), -90
    elif side == "Front":
        loc, rz = (-CAB.hw + c + 0.5, CAB.hl, r), 180
    else:
        loc, rz = (CAB.hw - c - 0.5, -CAB.hl, r), 0
    return place(panel_name, loc, rz)


# --- Layout (mockup_quarters_v3): a lived-in berth room -------------------------
# left wall: built-in berth under the hex window, high shelf with a trailing
# plant, hard chest at the foot of the bed
place("Furn_Bed", (-1.5, -0.5, 0), 0)
swap_slot("Cabin_Left_01_01", "Wall_WindowHex")
place("Decor_WallShelf", (-2.0, -1.0, 2.02), -90)
place("Decor_Plant", (-1.88, -1.20, 2.045), -90)
place("Decor_Books", (-1.88, -0.78, 2.045), -90)
place("Furn_StorageCase", (-1.5, 1.0, 0), 90)
# back wall: counter run of 3 ending in the kitchenette, wall-cabinet run above;
# picture, taped photos and clock above the bed head
place("Furn_Kitchenette", (-0.5, -1.0, 0), 0)
place("Furn_Counter_Mid", (0.5, -1.0, 0), 0)
place("Furn_Counter_EndL", (1.5, -1.0, 0), 0)
place("Decor_CoffeeMachine", (0.62, -1.22, 0.90), 0)
place("Decor_Mug", (0.95, -1.12, 0.90), 30)
place("Decor_PlantPotted", (1.68, -1.25, 0.90), 0)
swap_slot("Cabin_Back_00_01", "Wall_WallCabinet_EndL_EdgeL")
swap_slot("Cabin_Back_01_01", "Wall_WallCabinet_Mid")
swap_slot("Cabin_Back_02_01", "Wall_WallCabinet_EndR")
place("Decor_PictureFrame", (-1.50, -1.5, 1.55), 0)
place("Decor_TapedPhotos", (-1.20, -1.5, 1.24), 0)
place("Decor_Clock", (-1.55, -1.5, 2.28), 0)
# right wall: desk with drawer unit and swivel chair, shelf niche above it;
# wet cell in the front-right corner
place("Furn_Desk", (1.0, 0.0, 0), 90)
place("Furn_Chair", (0.72, 0.05, 0), -110)
swap_slot("Cabin_Right_01_01", "Wall_ShelfNiche")
place("Decor_DeskLamp", (1.78, -0.32, 0.75), 95)
place("Decor_PlantPotted", (1.80, 0.34, 0.75), 0)
place("Decor_Mug", (1.42, 0.08, 0.75), 0)
place("Decor_Radio", (2.12, 0.18, 1.47), 90)
place("Decor_LightSwitch", (2.0, 0.66, 1.20), 90)
place("Furn_WetCell", (1.5, 1.0, 0), 90)
# front wall: fold-out table (open) with two chairs pulled up to it
swap_slot("Cabin_Front_01_00", "Wall_FoldTable_Open")
place("Furn_Chair", (-0.76, 0.78, 0), -6)
place("Furn_Chair", (-0.24, 0.80, 0), 8)
place("Decor_Books", (-0.66, 1.16, 0.75), 180)
# striped rug through the middle
place("Decor_Rug_2x3", (0.0, 0.10, 0), 90)
DESK_MUG = Vector((1.42, 0.08, 0.75))


# --- Room dressing (render test only): hip-height orange band, rivets, beams ----
def dressing(name):
    kb = KB()
    return kb


band = KB()
hw, hl = CAB.hw, CAB.hl
for (x0, y0, x1, y1, n, z0, z1) in (
        (-hw, -hl, -hw, hl, (1, 0), 0.90, 1.10),          # left wall
        (-hw, -hl, hw, -hl, (0, 1), 0.90, 1.00),          # back wall: backsplash under the cabinets
        (-hw, hl, hw, hl, (0, -1), 0.90, 1.10),           # front wall
        (hw, -hl, hw, hl, (-1, 0), 0.90, 1.10)):          # right wall
    nx, ny = n
    lo = (min(x0, x1) + (0.004 * nx if nx > 0 else 0), min(y0, y1) + (0.004 * ny if ny > 0 else 0), z0)
    hi = (max(x0, x1) + (0.004 * nx if nx < 0 else 0), max(y0, y1) + (0.004 * ny if ny < 0 else 0), z1)
    lo = (lo[0] if nx >= 0 else lo[0] - 0.004, lo[1] if ny >= 0 else lo[1] - 0.004, z0)
    hi = (hi[0] if nx <= 0 else lo[0] + 0.004, hi[1] if ny <= 0 else lo[1] + 0.004, z1)
    if nx > 0:
        lo, hi = (-hw, -hl, z0), (-hw + 0.004, hl, z1)
    elif nx < 0:
        lo, hi = (hw - 0.004, -hl, z0), (hw, hl, z1)
    elif ny > 0:
        lo, hi = (-hw, -hl, z0), (hw, -hl + 0.004, z1)
    else:
        lo, hi = (-hw, hl - 0.004, z0), (hw, hl, z1)
    band.bbox(lo, hi, "orange", 0)
    band.bbox((lo[0], lo[1], z1 - 0.012) if True else lo, (hi[0], hi[1], z1), "gun", 0)
b_ob = band.finish("RT_Dress_HipBand", room, (RX, 0, 0))

riv = KB()
n_riv = 0


def rivet_row(p0, p1, n_out, count):
    global n_riv
    for k in range(count):
        t = (k + 0.5) / count
        p = Vector(p0).lerp(Vector(p1), t)
        riv.cyl(p, p + Vector(n_out) * 0.006, 0.010, "steel", sides=6)
        n_riv += 1


for ob in list(bpy.data.collections["Cabin_Slots"].objects):
    parts = ob.name.split("_")
    side, c, r = parts[1], parts[2], parts[3]
    if side in ("Floor", "Ceiling") or r == "Chamfer":
        continue
    c, r = int(c), int(r)
    if side in ("Right", "Left"):
        sx = 1 if side == "Right" else -1
        ya, yb = (hl - c - 1, hl - c) if side == "Right" else (-hl + c, -hl + c + 1)
        x = sx * hw - sx * 0.0
        for z in (r + 0.05, r + 0.95):
            rivet_row((x, ya + 0.06, z), (x, yb - 0.06, z), (-sx, 0, 0), 7)
    else:
        sy = 1 if side == "Front" else -1
        xa, xb = (-hw + c, -hw + c + 1) if side == "Front" else (hw - c - 1, hw - c)
        y = sy * hl
        zs = (r + 0.05,) if r == CAB.H - 1 else (r + 0.05, r + 0.95)
        for z in zs:
            rivet_row((xa + 0.06, y, z), (xb - 0.06, y, z), (0, -sy, 0), 7)
print("rivets:", n_riv)
riv.finish("RT_Dress_Rivets", room, (RX, 0, 0))

bm_ = KB()
for yb_ in (-0.55, 1.0):                                   # heavier ceiling beams with bolts
    bm_.bbox((-hw + CH_IN, yb_ - 0.08, CAB.H - 0.10), (hw - CH_IN, yb_ + 0.08, CAB.H), "slate", 0.012)
    for sx in (-1, 1):                                     # angled brackets down the chamfers
        a = Vector((sx * (hw - CH_IN), yb_, CAB.H))
        b = Vector((sx * hw, yb_, CAB.H - CH_IN))
        mid = (a + b) / 2
        R = Matrix.Rotation(math.radians(-45 * sx), 4, 'Y')
        nrm = Vector((-sx, 0, -1)).normalized()
        bm_.bbox_c(mid + nrm * 0.05, (0.72, 0.16, 0.10), "slate", 0.012, R)
    for k in range(9):
        x = -hw + CH_IN + 0.12 + k * (2 * (hw - CH_IN) - 0.24) / 8
        for dy in (-0.05, 0.05):
            bm_.cyl((x, yb_ + dy, CAB.H - 0.10), (x, yb_ + dy, CAB.H - 0.108), 0.011, "steel", sides=6)
bm_.finish("RT_Dress_CeilingBeams", room, (RX, 0, 0))

# steam above the desk mug (render only): three faint twisting ribbons
st = KB()
mug_top = DESK_MUG + Vector((0, 0, 0.10))
for k in range(3):
    pts = []
    for j in range(9):
        t = j / 8
        a = t * 4.0 + k * 2.1
        pts.append(mug_top + Vector((0.015 * math.cos(a) + 0.01 * k - 0.01, 0.015 * math.sin(a), t * 0.16)))
    for j in range(8):
        p, q = pts[j], pts[j + 1]
        w = 0.008 + 0.012 * (j / 8)
        st.face([p + Vector((-w, 0, 0)), p + Vector((w, 0, 0)), q + Vector((w, 0, 0)), q + Vector((-w, 0, 0))],
                "steam", normal=(0, -1, 0))
st.finish("RT_Dress_Steam", room, (RX, 0, 0))

# local wear decals (render test): a soft grime patch on the floor in front of
# and under the kitchenette, and scuffs at the fold table
gd = KB()
for (cx, cy, w, l) in ((-0.5, -0.62, 0.8, 0.35), (-0.5, 1.05, 0.7, 0.3)):
    gd.face([Vector((cx - w / 2, cy - l / 2, 0.003)), Vector((cx + w / 2, cy - l / 2, 0.003)),
             Vector((cx + w / 2, cy + l / 2, 0.003)), Vector((cx - w / 2, cy + l / 2, 0.003))], "grime_decal",
            normal=(0, 0, 1))
gd.finish("RT_Dress_GrimeDecals", room, (RX, 0, 0))

# dim the compartment's own ceiling strip; the room gets local light pools instead
MAT["amber_dim"] = make_mat("M_Light_AmberDim", "#FFC07A", emit=1.6)
cl = bpy.data.objects.get("Cabin_Light")
if cl is not None:
    for i, m in enumerate(cl.data.materials):
        if m == MAT["amber"]:
            cl.data.materials[i] = MAT["amber_dim"]


# ---------------------------------------------------------------------------
# 12. EXPORT: one FBX per family or piece (meshes + ACCESS empties)
# ---------------------------------------------------------------------------
groups = {}
for p in PIECES:
    groups.setdefault(p["group"], []).append(p)
for g, plist in groups.items():
    for o in bpy.context.scene.objects:
        o.select_set(False)
    saved = []
    for p in plist:
        ob = p["ob"]
        saved.append((ob, ob.location.copy()))
        ob.location = (0, 0, 0)
        ob.select_set(True)
        if p["acc"] is not None:
            p["acc"].select_set(True)
    bpy.context.view_layer.objects.active = plist[0]["ob"]
    bpy.context.view_layer.update()
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(KIT_DIR, f"{g}.fbx"), use_selection=True, object_types={'MESH', 'EMPTY'},
        apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y',
        bake_space_transform=True, mesh_smooth_type='FACE', use_mesh_modifiers=True,
        add_leaf_bones=False, bake_anim=False)
    for ob, l in saved:
        ob.location = l
print("FBX files:", len(groups))


# ---------------------------------------------------------------------------
# 13. RENDER STAGING
# ---------------------------------------------------------------------------
def look(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat('-Z', 'Y').to_euler()


def add_light(name, kind, loc, power, hx, size=None, target=None, size_y=None):
    ld = bpy.data.lights.new(name, kind)
    ld.energy = power
    ld.color = hexcol(hx)
    if kind == 'AREA':
        ld.shape = 'RECTANGLE'; ld.size = size; ld.size_y = size_y or size
    elif kind == 'SUN':
        ld.angle = math.radians(size or 2)
    elif size:
        ld.shadow_soft_size = size
    ob = bpy.data.objects.new(name, ld)
    C_RENDER_KIT.objects.link(ob)
    ob.location = loc
    if target is not None:
        look(ob, target)
    return ob


def add_camera(name, loc, target, lens=35, ortho=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.03
    cd.clip_end = 2000
    if ortho:
        cd.type = 'ORTHO'
        cd.ortho_scale = ortho
    ob = bpy.data.objects.new(name, cd)
    C_RENDER_KIT.objects.link(ob)
    ob.location = loc
    look(ob, target)
    return ob


# studio world for the catalogue, dark space with stars for the room test
w_studio = bpy.data.worlds.new("Studio")
try:
    w_studio.use_nodes = True
except Exception:
    pass
w_studio.node_tree.nodes["Background"].inputs["Color"].default_value = (*hexcol("#8E8A86"), 1)
w_studio.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
w_space = bpy.data.worlds.new("Space")
try:
    w_space.use_nodes = True
except Exception:
    pass
wn, wl = w_space.node_tree.nodes, w_space.node_tree.links
tc = wn.new("ShaderNodeTexCoord")
vor = wn.new("ShaderNodeTexVoronoi")
vor.inputs["Scale"].default_value = 300
wl.new(tc.outputs["Generated"], vor.inputs["Vector"])
mr = wn.new("ShaderNodeMapRange")
mr.inputs["From Min"].default_value = 0.03
mr.inputs["From Max"].default_value = 0.0
wl.new(vor.outputs["Distance"], mr.inputs["Value"])
mx = wn.new("ShaderNodeMix")
mx.data_type = 'RGBA'
mx.inputs[6].default_value = (0.004, 0.005, 0.012, 1)
mx.inputs[7].default_value = (8.0, 7.6, 7.0, 1)
wl.new(mr.outputs["Result"], mx.inputs["Factor"])
wl.new(mx.outputs[2], wn["Background"].inputs["Color"])

cx_ = (cat_lo[0] + cat_hi[0]) / 2
cy_ = (cat_lo[1] + cat_hi[1]) / 2
bpy.ops.mesh.primitive_plane_add(size=1, location=(cx_, cy_, -0.001))
ground = bpy.context.object
ground.name = "RENDER_Ground"
ground.scale = (cat_hi[0] - cat_lo[0] + 12, cat_hi[1] - cat_lo[1] + 12, 1)
for c_ in list(ground.users_collection):
    c_.objects.unlink(ground)
C_RENDER_KIT.objects.link(ground)
ground.data.materials.append(make_mat("M_Ground", "#C9C4BC", rough=0.95))

cat_lights = [add_light("L_CatSun", 'SUN', (cx_ + 15, cy_ + 25, 40), 3.0, "#FFF2E4", 12, (cx_, cy_, 0)),
              add_light("L_CatFill", 'SUN', (cx_ - 25, cy_ + 10, 15), 0.8, "#DDE6FF", 10, (cx_, cy_, 0))]
span_w = cat_hi[0] - cat_lo[0]
span_d = cat_hi[1] - cat_lo[1]
elev = math.radians(58)
ortho = max(span_w, (span_d * math.sin(elev) + 1.6) * 16 / 9) * 1.02
CAM_CAT = add_camera("CAM_Catalogue", (cx_, cy_ + 40 * math.cos(elev), 40 * math.sin(elev)),
                     (cx_, cy_ + 0.2, 0.7), ortho=ortho)

O = Vector((RX, 0, 0))


def at(name):
    return bpy.data.objects[f"RT_{name}"]


def spot(name, loc, target, power, hx, size_deg=75, radius=0.03):
    ld = bpy.data.lights.new(name, 'SPOT')
    ld.energy = power
    ld.color = hexcol(hx)
    ld.spot_size = math.radians(size_deg)
    ld.spot_blend = 0.7
    ld.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, ld)
    C_RENDER_KIT.objects.link(ob)
    ob.location = loc
    look(ob, target)
    return ob


lamp = at("Decor_DeskLamp")
Rl = lamp.matrix_world.to_3x3()
shade_bot = lamp.matrix_world @ DL_SHADE[1]
shade_dir = Rl @ (DL_SHADE[1] - DL_SHADE[0]).normalized()
room_lights = [
    add_light("L_RoomCeilingDim", 'AREA', O + Vector((0, 0.2, 2.86)), 28, "#FFC07A", 1.6, O + Vector((0, 0.2, 0)), 0.25),
    add_light("L_WarmFill", 'AREA', O + Vector((0.0, 0.3, 2.6)), 32, "#FFD2A0", 3.0, O + Vector((0.0, 0.0, 0.0)), 2.2),
    add_light("L_WarmBounce", 'AREA', O + Vector((0.3, 0.6, 1.4)), 22, "#FFB878", 1.2, O + Vector((-1.5, -1.0, 0.8)), 1.2),
    spot("L_DeskLamp", shade_bot - shade_dir * 0.01, shade_bot + shade_dir, 45, "#FFB466", 95, 0.03),
    add_light("L_DeskLampBulb", 'POINT', shade_bot - shade_dir * 0.03, 1.5, "#FFB466", 0.02),
    add_light("L_DeskLampWall", 'POINT', shade_bot - shade_dir * 0.05 + Vector((0.08, 0, 0.02)), 9, "#FFB466", 0.04),
    add_light("L_UnderCabinets", 'AREA', O + Vector((0.5, -1.40, 0.99)), 30, "#FFC07A", 2.8, O + Vector((0.5, -1.52, 0)), 0.06),
    add_light("L_UnderWallShelf", 'AREA', O + Vector((-1.88, -1.0, 1.99)), 14, "#FFC07A", 0.06, O + Vector((-2.05, -1.0, 0.8)), 0.8),
    add_light("L_ShelfNiche", 'AREA', O + Vector((2.12, 0.0, 1.92)), 10, "#FFC07A", 0.1, O + Vector((2.12, 0.0, 0)), 0.7),
    add_light("L_UnderBed", 'AREA', O + Vector((-1.10, -0.5, 0.085)), 4, "#FFB060", 0.05, O + Vector((-1.10, -0.5, -1)), 1.6),
    add_light("L_BedReading", 'AREA', O + Vector((-1.5, -1.36, 0.82)), 4, "#FFC889", 0.5, O + Vector((-1.5, -0.6, 0.45)), 0.05),
    add_light("L_BedReadingWall", 'POINT', O + Vector((-1.80, -1.30, 0.84)), 7, "#FFC889", 0.04),
    add_light("L_WindowCool", 'AREA', O + Vector((-1.92, 0.0, 1.50)), 20, "#8FAEE0", 0.8, O + Vector((1.0, 0.0, 0.7)), 0.6),
    add_light("L_Kitchen", 'POINT', O + Vector((-0.5, -1.05, 1.15)), 3, "#FFB060", 0.05),
]
PLANET_SUN = add_light("L_PlanetSun", 'SUN', O + Vector((40, 30, 40)), 3.0, "#FFF4E8", 1.0, O + Vector((-120, -40, -60)))
room_lights.append(PLANET_SUN)

# the planet outside the window (render only)
CAM_ROOM = add_camera("CAM_RoomTest", O + Vector((-0.05, 1.40, 1.62)), O + Vector((-0.55, -1.50, 1.20)), lens=11)
CAM_ROOM_B = add_camera("CAM_RoomTest_B", O + Vector((-1.40, -1.30, 1.65)), O + Vector((1.0, 1.3, 0.95)), lens=12)
win_c = O + Vector((-hw, 0.0, 1.5))
ray = (win_c - CAM_ROOM.location).normalized()
bmp = bmesh.new()
bmesh.ops.create_icosphere(bmp, subdivisions=5, radius=95)
pme = bpy.data.meshes.new("RENDER_Planet")
bmp.to_mesh(pme)
bmp.free()
planet = bpy.data.objects.new("RENDER_Planet", pme)
C_RENDER_KIT.objects.link(planet)
planet.location = CAM_ROOM.location + ray * 170 + Vector((0, 0, -86))
pm = bpy.data.materials.new("M_PlanetRender")
try:
    pm.use_nodes = True
except Exception:
    pass
pn = pm.node_tree
pb = pn.nodes["Principled BSDF"]
nz = pn.nodes.new("ShaderNodeTexNoise")
nz.inputs["Scale"].default_value = 0.035
nz.inputs["Detail"].default_value = 10
rp = pn.nodes.new("ShaderNodeValToRGB")
rp.color_ramp.elements[0].position = 0.45
rp.color_ramp.elements[0].color = (*hexcol("#1D4A86"), 1)
rp.color_ramp.elements[1].position = 0.62
rp.color_ramp.elements[1].color = (*hexcol("#5E7F4E"), 1)
e = rp.color_ramp.elements.new(0.70)
e.color = (*hexcol("#E8EEF2"), 1)
pn.links.new(nz.outputs["Fac"], rp.inputs[0])
pn.links.new(rp.outputs["Color"], pb.inputs["Base Color"])
pn.links.new(rp.outputs["Color"], pb.inputs["Emission Color"])
pb.inputs["Emission Strength"].default_value = 0.30
pme.materials.append(pm)
for p_ in pme.polygons:
    p_.use_smooth = True


def setup_render(samples):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.cycles.transparent_max_bounces = 8
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.render.resolution_percentage = KIT_RES
    sc.render.image_settings.file_format = 'PNG'
    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Base Contrast'
    except Exception:
        pass
    try:
        tree = bpy.data.node_groups.new("Bloom", "CompositorNodeTree")
        tree.interface.new_socket("Image", in_out='OUTPUT', socket_type='NodeSocketColor')
        rl = tree.nodes.new("CompositorNodeRLayers")
        gl = tree.nodes.new("CompositorNodeGlare")
        gl.inputs["Type"].default_value = 'Bloom'
        gl.inputs["Threshold"].default_value = 1.0
        gl.inputs["Strength"].default_value = 0.3
        gl.inputs["Size"].default_value = 0.6
        out = tree.nodes.new("NodeGroupOutput")
        tree.links.new(rl.outputs["Image"], gl.inputs["Image"])
        tree.links.new(gl.outputs["Image"], out.inputs[0])
        sc.compositing_node_group = tree
    except Exception as e:
        print("bloom skipped:", e)


sc = bpy.context.scene
sc.camera = CAM_ROOM
sc.world = w_space
w_studio.use_fake_user = True
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(KIT_DIR, "furniture_kit.blend"))
try:
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_mainfile()
except Exception as e:
    print("relative paths:", e)


ROOM_EXPOSURE = float(os.environ.get("KIT_ROOM_EXPOSURE", "0.0"))


def kit_render(cam, fname, world, lights_on, exposure=0.0):
    sc.camera = cam
    sc.world = world
    for l in cat_lights + room_lights:
        l.hide_render = l not in lights_on
    sc.view_settings.exposure = exposure
    try:
        sc.view_settings.look = 'AgX - Medium High Contrast' if world is w_space else 'AgX - Base Contrast'
    except Exception:
        pass
    sc.render.filepath = os.path.join(KIT_DIR, fname)
    bpy.ops.render.render(write_still=True)
    print("Rendered", fname)


if DO_RENDER:
    setup_render(KIT_SAMPLES)
    if not KIT_ONLY or "room" in KIT_ONLY:
        ground.hide_render = True
        kit_render(CAM_ROOM, "kit_room_test.png", w_space, room_lights, ROOM_EXPOSURE)
        if not KIT_ONLY or "roomb" in KIT_ONLY:
            kit_render(CAM_ROOM_B, "kit_room_test_b.png", w_space, room_lights, ROOM_EXPOSURE)
        ground.hide_render = False
    if not KIT_ONLY or "cat" in KIT_ONLY:
        for o in room.all_objects:
            o.hide_render = True
        planet.hide_render = True
        kit_render(CAM_CAT, "kit_catalogue.png", w_studio, cat_lights, 0.0)
        planet.hide_render = False
        for o in room.all_objects:
            o.hide_render = False
print("Done.")
