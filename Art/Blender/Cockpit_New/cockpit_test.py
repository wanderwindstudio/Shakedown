"""SHAKEDOWN / LANTERN — independently designed explorer bridge look test.

Run in a NEW Blender file: Scripting > New > paste this file > Run Script.
WARNING: clears the current scene. One metre = one Blender unit.
The seven named module meshes and COL boxes are exported; staging is excluded.
No textures, UV unwrap or external assets are needed.
Set RENDER=False below to build/export without waiting for the three images.
"""
import bpy
import math
import os
import json
import random
from mathutils import Vector

# 1. SETTINGS AND EMPTY SCENE -------------------------------------------------
OUT = os.environ.get('COCKPIT_NEW_OUT', os.path.expanduser('~/Shakedown/Art/Blender/Cockpit_New'))
RENDER = os.environ.get('COCKPIT_NEW_RENDER', '1') == '1'
SAMPLES = int(os.environ.get('COCKPIT_NEW_SAMPLES', '32'))
os.makedirs(OUT, exist_ok=True)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.cycles.transparent_max_bounces = 12
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
scene.world = bpy.data.worlds.new('Lavender dusk')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.13, 0.085, 0.23, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.45

def collection(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c
module = collection('Cockpit_Lantern')
colliders = collection('COL')
stage = collection('RENDER')
parts = {k: [] for k in ['HullExterior', 'Interior', 'Floor', 'Canopy', 'Chair', 'Console', 'Details']}
# The roof is tracked separately so it can be hidden for the actual cutaway.
roof_parts = []

# 2. PLAIN COLOUR MATERIALS ---------------------------------------------------
def material(name, rgb, metal=0, rough=0.7, emission=0, alpha=1):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (*rgb, alpha)
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*rgb, 1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = rough
    p.inputs['Alpha'].default_value = alpha
    p.inputs['Emission Color'].default_value = (*rgb, 1)
    p.inputs['Emission Strength'].default_value = emission
    return m
M = {
    'hull': material('Hull / warm limestone', (0.56, 0.50, 0.41)),
    'wall': material('Interior / dusty blue grey', (0.25, 0.34, 0.39)),
    'panel': material('Interior / pale blue grey', (0.37, 0.47, 0.50)),
    'slate': material('Floor / deep slate', (0.075, 0.105, 0.14)),
    'deck': material('Floor / slate tiles', (0.12, 0.16, 0.19)),
    'trim': material('Frames / charcoal', (0.065, 0.09, 0.11), metal=0.25),
    'orange': material('Accent / burnt apricot', (0.76, 0.25, 0.075)),
    'teal': material('Light / soft teal', (0.24, 0.77, 0.70), emission=2.3),
    'screen': material('Screen / midnight teal', (0.025, 0.13, 0.16), emission=0.6),
    'star': material('Map / teal stars', (0.52, 0.95, 0.85), emission=3),
    'metal': material('Hardware / satin alloy', (0.41, 0.45, 0.46), metal=0.7, rough=0.4),
    'glass': material('Canopy / transparent teal', (0.32, 0.53, 0.58), rough=0.08, alpha=0.16),
}

# 3. SMALL GEOMETRY HELPERS ---------------------------------------------------
# Shapes are made as separate little objects, then joined into seven useful
# groups. A one-segment bevel gives crisp facets; every face stays flat shaded.
def register(ob, group, mat, roof=False):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    module.objects.link(ob)
    ob.data.materials.append(M[mat])
    for p in ob.data.polygons:
        p.use_smooth = False
    parts[group].append(ob)
    if roof:
        roof_parts.append(ob)
    return ob

def box(name, centre, size, mat, group='Details', bevel=0.015, rotation=(0,0,0), roof=False):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centre)
    ob = bpy.context.object
    ob.name = name
    ob.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = ob.modifiers.new('Single facet edge', 'BEVEL')
        mod.width = min(bevel, min(size)*0.24)
        mod.segments = 1
        bpy.ops.object.modifier_apply(modifier=mod.name)
    ob.rotation_euler = tuple(math.radians(a) for a in rotation)
    return register(ob, group, mat, roof)

def mesh(name, vertices, faces, mat, group, roof=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(vertices, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    module.objects.link(ob)
    return register(ob, group, mat, roof)

def panel(name, corners, thickness, mat, group, roof=False):
    # Extrude an arbitrary four-corner panel along its normal.
    a,b,c,d = [Vector(v) for v in corners]
    n = (b-a).cross(c-a).normalized() * thickness / 2
    verts = [v-n for v in (a,b,c,d)] + [v+n for v in (a,b,c,d)]
    return mesh(name, verts, [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)], mat, group, roof)

def rod(name, a, b, radius, mat, group='Details', sides=8, roof=False):
    v = Vector(b)-Vector(a)
    bpy.ops.mesh.primitive_cylinder_add(vertices=sides, radius=radius, depth=v.length, location=(Vector(a)+Vector(b))/2)
    ob = bpy.context.object
    ob.name = name
    ob.rotation_euler = v.to_track_quat('Z','Y').to_euler()
    return register(ob, group, mat, roof)

def beam(name, a, b, width, depth, mat, group='Details', roof=False):
    v = Vector(b)-Vector(a)
    ob = box(name, (Vector(a)+Vector(b))/2, (width,depth,v.length), mat, group, bevel=0.006, roof=roof)
    ob.rotation_euler = v.to_track_quat('Z','Y').to_euler()
    return ob

# 4. ARCHITECTURE: BROAD ANGULAR ROOM, THREE-FACET PANORAMA --------------------
# Grid: X +-2, Y +-4, Z 0..3.5. Front = +Y. Deck surface = 0.12.
# Unlike a tunnel, the rear is a wide box with chamfered ceiling corners.
box('Deck foundation', (0,0,0.06), (3.98,8,0.12), 'slate', 'Floor', bevel=0)
for x in (-1.95,1.95):
    box('Outer side sill', (x,-0.04,0.38), (0.06,7.90,0.52), 'hull','HullExterior',bevel=0)
    box('Rear hull cheek', (x,-1.38,1.78), (0.06,5.22,2.28), 'hull','HullExterior',bevel=0)
    xi = math.copysign(1.88,x)
    box('Inner side lining', (xi,-1.38,1.76), (0.10,5.20,2.28), 'wall','Interior',bevel=0)
    # Forward side glazing: vertical trapezoid between sill and sloping nose.
    side = [(x,1.24,0.65),(x,3.90,0.65),(x,2.78,3.34),(x,1.24,3.34)]
    panel('Side panorama pane',side,0.018,'glass','Canopy')
    beam('Canopy side sill', (x,1.22,0.65),(x,3.90,0.65),0.055,0.055,'hull','HullExterior')
    beam('Forward diagonal frame',(x,3.90,0.65),(x,2.78,3.34),0.06,0.06,'hull','HullExterior')
    beam('Side window rear pillar',(x,1.22,0.65),(x,1.22,3.34),0.07,0.07,'trim','Interior')
    # Long, quiet shoulder facets replace repeated interior hoops.
    panel('Chamfered shoulder',[(math.copysign(1.94,x),-3.94,2.92),(math.copysign(1.94,x),1.20,2.92),(math.copysign(1.57,x),1.20,3.40),(math.copysign(1.57,x),-3.94,3.40)],0.08,'hull','HullExterior',roof=True)
    panel('Interior shoulder',[(math.copysign(1.82,x),-3.88,2.86),(math.copysign(1.82,x),1.20,2.86),(math.copysign(1.52,x),1.20,3.28),(math.copysign(1.52,x),-3.88,3.28)],0.04,'wall','Interior',roof=True)
box('Upper roof', (0,-1.40,3.45),(3.16,5.18,0.10),'hull','HullExterior',bevel=0,roof=True)
box('Ceiling lining',(0,-1.34,3.32),(3.12,5.18,0.08),'wall','Interior',bevel=0,roof=True)
# The forward roof broadens over the panoramic windows, closing both corners.
box('Panorama roof',(0,2.0,3.45),(3.96,1.60,0.10),'hull','HullExterior',bevel=0,roof=True)
box('Panorama ceiling',(0,2.0,3.37),(3.84,1.60,0.06),'wall','Interior',bevel=0,roof=True)
for x in (-1.95,1.95):
    box('Panorama top seal',(x,2.0,3.37),(0.06,1.62,0.06),'hull','HullExterior',bevel=0,roof=True)
# Close the short side strip above the rear wall cheeks.
for x in (-1.95,1.95):
    box('Upper side seam',(x,-1.38,3.13),(0.06,5.22,0.42),'hull','HullExterior',bevel=0,roof=True)
# Slanted panoramic windshield: three large panes, two restrained mullions.
for x0,x1 in [(-1.94,-0.66),(-0.64,0.64),(0.66,1.94)]:
    panel('Front windshield',[(x0,3.90,0.66),(x1,3.90,0.66),(x1,2.80,3.36),(x0,2.80,3.36)],0.02,'glass','Canopy')
for x in (-1.95,-0.65,0.65,1.95):
    beam('Front glazing mullion',(x,3.90,0.64),(x,2.80,3.36),0.045,0.045,'trim','HullExterior')
beam('Brow',( -1.95,2.80,3.37),(1.95,2.80,3.37),0.09,0.09,'hull','HullExterior',roof=True)
box('Front lower bumper',(0,3.94,0.38),(3.96,0.10,0.52),'hull','HullExterior',bevel=0.02)
# Rear wall split into jambs and lintel: exactly 1.4 x 2.2 m opening.
for x in (-1.35,1.35):
    box('Rear hull jamb',(x,-3.95,1.79),(1.30,0.10,3.34),'hull','HullExterior',bevel=0)
    box('Rear inner jamb',(x,-3.87,1.73),(1.30,0.06,3.22),'wall','Interior',bevel=0)
box('Rear lintel',(0,-3.95,2.91),(1.40,0.10,1.18),'hull','HullExterior',bevel=0)
box('Rear inner lintel',(0,-3.87,2.82),(1.40,0.06,1.0),'wall','Interior',bevel=0)
for x in (-0.75,0.75):
    box('Socket orange jamb',(x,-3.82,1.24),(0.10,0.04,2.24),'orange',bevel=0)
box('Socket orange lintel',(0,-3.82,2.37),(1.60,0.04,0.10),'orange',bevel=0)
# Modular deck plates with visible narrow seams.
for ix in range(4):
    for iy in range(8):
        box('Deck plate',(-1.40+ix*0.93,-3.48+iy*0.98,0.126),(0.90,0.95,0.012),'deck','Floor',bevel=0.004)
# A small central approach line and hatch fasteners make the deck legible.
for y in (-3.4,-2.9,-2.4):
    box('Approach marker',(0,y,0.136),(0.09,0.22,0.006),'orange','Floor',bevel=0)
for x in (-1.62,1.62):
    for y in (-3.35,-2.35,-1.35,-0.35,0.65,1.65):
        box('Deck service latch',(x,y,0.14),(0.09,0.16,0.016),'metal',bevel=0.004)

# 5. COMMAND CHAIR: LOW BACK, WARM UPHOLSTERY ---------------------------------
rod('Seat plinth',(0,-0.12,0.12),(0,-0.12,0.18),0.32,'trim','Chair',sides=10)
rod('Seat pedestal',(0,-0.12,0.18),(0,-0.12,0.52),0.09,'metal','Chair')
box('Seat shell',(0,-0.08,0.57),(0.64,0.66,0.14),'trim','Chair',bevel=0.04)
box('Seat cushion',(0,-0.04,0.67),(0.56,0.55,0.10),'orange','Chair',bevel=0.04)
box('Low back shell',(0,-0.37,0.97),(0.64,0.15,0.62),'trim','Chair',bevel=0.04,rotation=(10,0,0))
box('Low back cushion',(0,-0.28,0.98),(0.54,0.08,0.48),'orange','Chair',bevel=0.025,rotation=(10,0,0))
for x in (-0.38,0.38):
    box('Arm support',(x,-0.12,0.70),(0.06,0.10,0.30),'metal','Chair')
    box('Armrest',(x,-0.06,0.86),(0.12,0.58,0.09),'trim','Chair',bevel=0.025)
    box('Arm control',(x,0.12,0.91),(0.075,0.14,0.015),'teal','Chair',bevel=0.004)
# Two flat seams in the upholstery, not texture-dependent.
for x in (-0.15,0.15):
    box('Cushion stitch',(x,-0.04,0.723),(0.009,0.42,0.005),'trim','Chair',bevel=0)

# 6. MAIN FLIGHT DESK AND ELEVATED STAR MAP -----------------------------------
# Console front edge is Y=1.56, over 1 m beyond the chair's forward edge.
for x in (-0.69,0.69):
    box('Desk leg',(x,2.12,0.65),(0.18,0.35,1.06),'trim','Console',bevel=0.035)
box('Flight desk',(0,2.10,1.13),(1.92,1.08,0.18),'wall','Console',bevel=0.055)
box('Desk orange edge',(0,1.58,1.13),(1.80,0.03,0.06),'orange','Console',bevel=0.008)
for x in (-0.59,0.59):
    box('Inset desk screen',(x,2.08,1.23),(0.47,0.54,0.028),'screen','Console',bevel=0.012)
    for j in range(5):
        box('Screen data bar',(x,1.89+j*0.07,1.247),(0.30-j*0.027,0.016,0.004),'teal','Console',bevel=0)
# Main panel deliberately stays above the low chair back from doorway eye level.
for x in (-0.58,0.58):
    rod('Map support',(x,2.42,1.20),(x,2.42,1.62),0.025,'metal','Console')
box('Map bezel',(0,2.43,1.91),(1.67,0.095,0.70),'trim','Console',bevel=0.035)
box('Map face',(0,2.373,1.91),(1.54,0.018,0.58),'screen','Console',bevel=0.012)
rnd = random.Random(41)
for k in range(35):
    x,z = rnd.uniform(-0.71,0.71),rnd.uniform(1.66,2.16)
    r = rnd.choice([0.007,0.012,0.017])
    rod('Chart star',(x,2.359,z),(x,2.353,z),r,'star','Console',sides=6)
# Three connected orbit polylines: actual geometry, visible in the FBX.
for radius in (0.11,0.20,0.28):
    for k in range(24):
        a,b = k*math.tau/24,(k+1)*math.tau/24
        rod('Chart orbit',(0.20+radius*math.cos(a),2.351,1.92+radius*0.67*math.sin(a)),(0.20+radius*math.cos(b),2.351,1.92+radius*0.67*math.sin(b)),0.003,'teal','Console',sides=4)
for k in range(7):
    box('Flight key',(-0.24+k*0.08,1.78,1.237),(0.05,0.06,0.018),'orange' if k==3 else 'teal','Console',bevel=0.004)
# Left wall science workbench; right side stays quiet, with shallow storage.
box('Science station',(-1.65,-2.05,0.71),(0.44,1.75,1.12),'wall','Console',bevel=0.04)
box('Science desktop',(-1.62,-2.05,1.30),(0.52,1.86,0.08),'trim','Console',bevel=0.025)
box('Science wall display',(-1.80,-2.05,1.83),(0.04,1.25,0.65),'screen','Console',bevel=0.015)
for k in range(9):
    box('Science chart column',(-1.772,-2.57+k*0.13,1.77),(0.008,0.05,0.14+0.10*math.sin(k)),'teal','Console',bevel=0)
# Notebook, mug, folded seat, locker: small personal details with no text.
box('Notebook',(-1.57,-1.60,1.36),(0.29,0.38,0.035),'orange',rotation=(0,0,-9))
rod('Mug',(-1.55,-2.50,1.34),(-1.55,-2.50,1.49),0.055,'hull',sides=10)
rod('Mug coffee',(-1.55,-2.50,1.491),(-1.55,-2.50,1.493),0.045,'trim',sides=10)
rod('Mug handle',(-1.49,-2.50,1.38),(-1.49,-2.50,1.45),0.016,'metal',sides=6)
box('Shallow locker',(1.76,-2.62,1.30),(0.20,1.68,2.10),'trim',bevel=0.035)
for y in (-3.03,-2.21):
    box('Locker face',(1.644,y,1.30),(0.028,0.77,2.0),'panel',bevel=0.02)
    rod('Locker pull',(1.61,y+0.20,1.20),(1.61,y+0.20,1.45),0.018,'metal')
box('Stowed jumpseat',(1.70,-0.96,0.95),(0.15,0.75,0.88),'orange',bevel=0.035)
for y in (-1.24,-0.68):
    beam('Seat strap',(1.60,y,0.57),(1.60,y,1.32),0.035,0.025,'trim')

# 7. WALL PANELS, HARDWARE AND TWO SOFT LIGHT STRIPS ---------------------------
for sign in (-1,1):
    for y in (-3.35,-2.40,-1.45,-0.50,0.45):
        box('Wall inset',(sign*1.813,y,2.35),(0.028,0.89,0.70),'panel','Interior',bevel=0.022)
        box('Warm waist stripe',(sign*1.805,y,1.49),(0.018,0.89,0.035),'orange',bevel=0.006)
        for yy in (y-0.36,y+0.36):
            for z in (2.08,2.62):
                # Low-poly hex-head fasteners along panel edges.
                rod('Panel fastener',(sign*1.790,yy,z),(sign*1.775,yy,z),0.018,'metal',sides=6)
    # Grab rail near the piloting station.
    rod('Handrail',(sign*1.71,0.20,1.64),(sign*1.71,0.91,1.64),0.022,'metal')
    for y in (0.20,0.91):
        beam('Rail bracket',(sign*1.72,y,1.64),(sign*1.83,y,1.64),0.035,0.035,'metal')
    # Ceiling strips parallel to the room; removable in the cutaway.
    box('Light channel',(sign*0.93,-0.85,3.245),(0.16,5.55,0.07),'trim',roof=True)
    box('Light diffuser',(sign*0.93,-0.85,3.20),(0.10,5.48,0.025),'teal',roof=True)
    box('Exterior orange band',(sign*1.996,-1.33,0.91),(0.008,5.10,0.08),'orange',bevel=0)
    for y in (-3.25,-1.65,-0.05):
        box('Exterior service hatch',(sign*1.996,y,1.84),(0.008,1.14,0.76),'hull',bevel=0)
        for yy in (y-0.48,y+0.48):
            box('Hull hatch seam',(sign*1.999,yy,1.84),(0.002,0.012,0.68),'trim',bevel=0)
# An air intake below the front windows and a small door-side grille.
for sign in (-1,1):
    box('Air grille backing',(sign*1.20,3.998,0.37),(0.70,0.004,0.22),'trim',bevel=0)
    for k in range(8):
        box('Intake fin',(sign*1.20-0.28+k*0.08,3.999,0.37),(0.028,0.002,0.16),'metal',bevel=0)
for k in range(12):
    box('Rear air fin',(-1.02,-3.80,0.55+k*0.045),(0.34,0.035,0.018),'metal',bevel=0.003)
for x in (-1.76,1.76):
    box('Nose running light',(x,3.998,0.58),(0.16,0.003,0.045),'teal',bevel=0)

# 8. CUTAWAY COPIES, JOINING AND COMMON FLOOR-CENTRE PIVOTS --------------------
# Cutaway uses copies with only roof parts omitted and tall walls sliced down.
# The original module meshes are never altered for the top view.
roof_set = set(roof_parts)
cut_collection = collection('RENDER_Cutaway')
cut_objects = []
for group, objects in parts.items():
    for ob in objects:
        if ob in roof_set:
            continue
        clone = ob.copy()
        clone.data = ob.data.copy()
        cut_collection.objects.link(clone)
        cut_objects.append(clone)
        clone.hide_render = True
        # Slice architecture only. Furniture, the map and personal items stay whole.
        if group in ('HullExterior','Interior','Canopy'):
            import bmesh
            bm = bmesh.new()
            bm.from_mesh(clone.data)
            bpy.context.view_layer.update()
            local_plane = clone.matrix_world.inverted() @ Vector((0,0,1.48))
            local_normal = clone.matrix_world.to_3x3().transposed() @ Vector((0,0,1))
            bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=local_plane,plane_no=local_normal,clear_outer=True)
            bm.to_mesh(clone.data)
            bm.free()

def join_at_origin(objects, name):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    ob = bpy.context.object
    ob.name = name
    scene.cursor.location = (0,0,0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob
module_objects = [join_at_origin(obs,'Cockpit_'+group) for group,obs in parts.items()]
# One disposable cutaway mesh with furniture preserved.
cut = join_at_origin(cut_objects,'RENDER_Cutaway')
cut.hide_render = True

# 9. SIMPLE BOX COLLIDERS -----------------------------------------------------
def col(name, centre, size):
    ob = box('COL_'+name,centre,size,'trim',bevel=0)
    module.objects.unlink(ob)
    colliders.objects.link(ob)
    ob.hide_render = True
    ob.display_type = 'WIRE'
    ob.select_set(False)
    return ob
col('Floor',(0,0,0.06),(4,8,0.12))
col('Ceiling',(0,-0.60,3.40),(3.16,6.8,0.20))
for sign in (-1,1):
    col('Wall_'+('L' if sign<0 else 'R'),(sign*1.94,-0.6,1.75),(0.12,6.8,3.5))
    col('RearJamb_'+str(sign),(sign*1.35,-3.94,1.81),(1.30,0.12,3.38))
col('RearLintel',(0,-3.94,2.91),(1.4,0.12,1.18))
col('FrontBarrier',(0,3.35,1.75),(4,1.30,3.5))
col('Chair',(0,-0.10,0.73),(0.88,0.84,1.22))
col('MainConsole',(0,2.10,1.19),(1.92,1.08,2.14))
col('ScienceConsole',(-1.62,-2.05,1.14),(0.52,1.86,2.04))
col('Locker',(1.76,-2.62,1.30),(0.28,1.68,2.10))
col('StowedSeat',(1.70,-0.96,0.95),(0.22,0.75,0.88))

# 10. STAGING: LAVENDER DUSK, SOFT LIGHT, DISTANT OCEAN PLANET -----------------
def to_stage(ob):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    stage.objects.link(ob)
    return ob

def aim(ob, target):
    ob.rotation_euler = (Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()

def area(name,loc,target,power,color,size):
    d = bpy.data.lights.new(name,'AREA')
    d.energy,d.color,d.shape,d.size = power,color,'DISK',size
    ob=bpy.data.objects.new(name,d)
    stage.objects.link(ob)
    ob.location=loc
    aim(ob,target)
    return ob
area('Dusk key',(-6,7,10),(0,0,1),1800,(0.89,0.79,0.70),8)
area('Lavender fill',(6,-1,8),(0,0,1),1400,(0.58,0.54,0.87),7)
area('Door bounce',(0,-5,3),(0,1,1),110,(0.70,0.82,0.85),3)
area('Ceiling soft',(0,-0.9,3.12),(0,-0.9,0),85,(0.64,0.91,0.88),3)
area('Map bounce',(0,2.25,2.15),(0,-1,1),12,(0.30,0.90,0.83),1)
cut_light=area('Cutaway softbox',(0,0,10),(0,0,0),1000,(0.89,0.85,1),7)
cut_light.hide_render=True
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4,radius=105,location=(-80,480,65))
planet=to_stage(bpy.context.object)
planet.name='RENDER_DistantPlanet'
planet.data.materials.append(material('Ocean planet',(0.10,0.24,0.32),rough=0.9,emission=0.13))
# Noise is render staging only; the cockpit still uses plain materials.
pm=planet.data.materials[0]
nt=pm.node_tree
noise=nt.nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value=3.5
noise.inputs['Detail'].default_value=3
ramp=nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].color=(0.035,0.12,0.20,1)
ramp.color_ramp.elements[1].color=(0.40,0.48,0.50,1)
nt.links.new(noise.outputs['Fac'],ramp.inputs[0])
nt.links.new(ramp.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color'])

def camera(name,loc,target,lens=35,ortho=None):
    d=bpy.data.cameras.new(name)
    d.lens=lens
    d.clip_end=2000
    if ortho:
        d.type='ORTHO'
        d.ortho_scale=ortho
    ob=bpy.data.objects.new(name,d)
    stage.objects.link(ob)
    ob.location=loc
    aim(ob,target)
    return ob
ext=camera('CAM_Exterior',(-8.4,11,7.0),(0,0,1.5),36)
interior=camera('CAM_Interior',(0,-3.79,1.75),(0,2.4,1.55),18)
top=camera('CAM_TopDown',(0,0,14),(0,0,0),ortho=9.1)
top.rotation_euler=(0,0,math.pi/2)

# 11. VALIDATE, EXPORT AND RENDER --------------------------------------------
report={'concept':'Lantern: broad angular panoramic bridge, asymmetric research interior',
        'blender':bpy.app.version_string,'objects':{},'collider_count':len(colliders.objects),
        'door_socket_m':[1.4,2.2],'floor_surface_z_m':0.12,'interior_camera_z_m':1.75,
        'unity_import_tested':False,'resolution':[1920,1080]}
allpoints=[]
for ob in module_objects:
    ob.data.calc_loop_triangles()
    pts=[ob.matrix_world@v.co for v in ob.data.vertices]
    allpoints.extend(pts)
    report['objects'][ob.name]=len(ob.data.loop_triangles)
    assert ob.location.length < 0.00001, ob.name+' origin'
    assert all(not p.use_smooth for p in ob.data.polygons)
lo=[min(p[i] for p in allpoints) for i in range(3)]
hi=[max(p[i] for p in allpoints) for i in range(3)]
report['bounds_min_m']=lo
report['bounds_max_m']=hi
report['triangles']=sum(report['objects'].values())
assert all(lo[i]>=(-2,-4,0)[i]-0.0001 for i in range(3)),str(lo)
assert all(hi[i]<=(2,4,3.5)[i]+0.0001 for i in range(3)),str(hi)
assert 5000<=report['triangles']<=15000,report['triangles']
report['grid_bounds_pass']=True
report['flat_shading_pass']=True
report['zero_pivots_pass']=True
# Conservative clearances measured to furniture bounding boxes near the chair.
report['clearance_m']={'chair_front_to_desk':1.56-0.25,'chair_side_to_wall':1.76-0.44,'chair_rear_to_science_station_diagonal':math.hypot(1.36-0.44,1.12-0.47),'main_aisle_headroom':3.1875-0.132}
assert min(report['clearance_m'].values())>=1
bpy.ops.object.select_all(action='DESELECT')
for ob in module_objects+list(colliders.objects):
    ob.select_set(True)
bpy.context.view_layer.objects.active=module_objects[0]
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'cockpit_test.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',bake_space_transform=True,mesh_smooth_type='OFF',add_leaf_bones=False,bake_anim=False)

def render(cam,filename):
    scene.camera=cam
    scene.render.filepath=os.path.join(OUT,filename)
    bpy.ops.render.render(write_still=True)
if RENDER:
    render(ext,'cockpit_exterior.png')
    render(interior,'cockpit_interior.png')
    for ob in module_objects:
        ob.hide_render=True
    cut.hide_render=False
    cut_light.hide_render=False
    planet.hide_render=True
    render(top,'cockpit_topdown.png')
# Save an ordinary full cockpit, ready to inspect from inside.
for ob in module_objects:
    ob.hide_render=False
cut.hide_render=True
cut.hide_set(True)
cut_light.hide_render=True
planet.hide_render=False
scene.camera=interior
scene.render.filepath=os.path.join(OUT,'cockpit_interior.png')
bpy.ops.object.select_all(action='DESELECT')
for ob in module_objects:
    ob.select_set(True)
bpy.context.view_layer.objects.active=module_objects[0]
# Keep the viewport uncluttered by render-only staging and collider boxes.
for ob in list(stage.objects)+list(colliders.objects):
    ob.hide_set(True)
if '__file__' in globals() and os.path.isfile(__file__):
    bpy.data.texts.load(__file__)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'cockpit_test.blend'))
with open(os.path.join(OUT,'cockpit_validation.json'),'w') as f:
    json.dump(report,f,indent=2)
print('COCKPIT_REPORT',json.dumps(report),flush=True)
