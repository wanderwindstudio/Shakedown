"""Apply Shakedown's supplied watercolour images without UV unwrapping.
Run after cockpit_test.py, or run this file directly to update cockpit_test.blend.
A plain-colour backup is preferred as the repeatable input. Textures are packed.
"""
import bpy
import bmesh
import os
import json
from mathutils import Vector

OUT = os.path.expanduser('~/Shakedown/Art/Blender/Cockpit_New')
TEX = os.path.expanduser('~/Shakedown/Art/Textures/WatercolourTest')
source = os.path.join(OUT, 'Backup_PlainColours', 'cockpit_test.blend')
if not os.path.exists(source):
    source = os.path.join(OUT, 'cockpit_test.blend')
bpy.ops.wm.open_mainfile(filepath=source)
scene = bpy.context.scene
module = list(bpy.data.collections['Cockpit_Lantern'].objects)
cut = bpy.data.objects['RENDER_Cutaway']
images = {}
for kind, filename in {
    'hull':'tex_hull_plating.png', 'wall':'tex_interior_wall.png',
    'floor':'tex_floor.png', 'console':'tex_console_metal.png',
    'upholstery':'tex_upholstery.png', 'map':'tex_starmap_screen.png',
}.items():
    im = bpy.data.images.load(os.path.join(TEX, filename), check_existing=True)
    im.colorspace_settings.name = 'sRGB'
    im.pack()
    images[kind] = im
scales = {'hull':0.5, 'wall':0.5, 'floor':0.5, 'console':1.0, 'upholstery':2.0}
cache = {}

# Every mesh origin is the same module floor centre and its scale is applied.
# Object coordinates therefore measure metres and continue across object seams.
def textured(base, kind):
    key = (base.name, kind)
    if key in cache:
        return cache[key]
    mat = base.copy()
    mat.name = 'WC / '+kind+' / '+base.name
    nt = mat.node_tree
    bsdf = nt.nodes.get('Principled BSDF')
    original = tuple(bsdf.inputs['Base Color'].default_value)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    tc.name = 'WC Object coordinates (metres)'
    tc.location = (-800, 100)
    mapping = nt.nodes.new('ShaderNodeMapping')
    mapping.name = 'WC Repeat / '+str(1/scales[kind])+' metres'
    mapping.location = (-580,100)
    mapping.inputs['Scale'].default_value = (scales[kind],)*3
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.name = 'WC Box projection / blend 0.2'
    tex.location = (-350,100)
    tex.image = images[kind]
    tex.projection = 'BOX'
    tex.projection_blend = 0.2
    tex.extension = 'REPEAT'
    mix = nt.nodes.new('ShaderNodeMixRGB')
    mix.name = 'WC Multiply with original colour'
    mix.label = 'Original base colour × watercolour'
    mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 1.0
    mix.inputs[1].default_value = original
    mix.location = (-60,100)
    bsdf.location = (180,100)
    nt.links.new(tc.outputs['Object'], mapping.inputs['Vector'])
    nt.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
    nt.links.new(tex.outputs['Color'], mix.inputs[2])
    nt.links.new(mix.outputs[0], bsdf.inputs['Base Color'])
    mat['watercolour_kind'] = kind
    mat['repeat_metres'] = 1/scales[kind]
    mat['original_base_colour'] = original
    cache[key] = mat
    return mat

# A single flat projection maps local X/Z to the display's 0..1 rectangle.
# This is an explicit planar shader projection, not a mesh UV unwrap. The full
# image fits the existing wide panel; EXTEND prevents any repeated star maps.
star = bpy.data.materials.new('WC / Starmap / fitted emission')
star.use_nodes = True
nt = star.node_tree
p = nt.nodes.get('Principled BSDF')
p.inputs['Base Color'].default_value = (0.008,0.018,0.025,1)
p.inputs['Roughness'].default_value = 0.7
p.inputs['Emission Strength'].default_value = 2.5
tc = nt.nodes.new('ShaderNodeTexCoord')
tc.location = (-850,0)
sep = nt.nodes.new('ShaderNodeSeparateXYZ')
sep.location = (-650,0)
combine = nt.nodes.new('ShaderNodeCombineXYZ')
combine.location = (-470,0)
mp = nt.nodes.new('ShaderNodeMapping')
mp.location = (-270,0)
mp.name = 'Fit X [-0.77,0.77], Z [1.62,2.20] to image'
mp.inputs['Scale'].default_value = (1/1.54,1/0.58,1)
mp.inputs['Location'].default_value = (0.5,-1.62/0.58,0)
im = nt.nodes.new('ShaderNodeTexImage')
im.location = (-30,0)
im.image = images['map']
im.projection = 'FLAT'
im.extension = 'EXTEND'
nt.links.new(tc.outputs['Object'],sep.inputs[0])
nt.links.new(sep.outputs['X'],combine.inputs['X'])
nt.links.new(sep.outputs['Z'],combine.inputs['Y'])
nt.links.new(combine.outputs[0],mp.inputs['Vector'])
nt.links.new(mp.outputs[0],im.inputs['Vector'])
nt.links.new(im.outputs['Color'],p.inputs['Emission Color'])
p.location = (230,0)

# Remove only the old floating chart glyphs, so they cannot cover the new image.
removed = {}
for ob in [bpy.data.objects['Cockpit_Console'],cut]:
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    verts = [v for v in bm.verts if abs(v.co.x)<0.78 and 2.34<v.co.y<2.3629 and 1.62<v.co.z<2.20]
    removed[ob.name] = len(verts)
    bmesh.ops.delete(bm, geom=verts, context='VERTS')
    bm.to_mesh(ob.data)
    bm.free()

# Split shared colour materials where necessary: orange chair cushions use
# fabric, while orange hull stripes and console keys keep their own surfaces.
def category(ob, poly, base):
    name = base.name
    x,y,z = poly.center
    if 'Canopy /' in name or 'Light /' in name or 'Map /' in name or 'Screen /' in name:
        return None
    if 'Floor /' in name:
        return 'floor'
    if 'Hull /' in name:
        return 'hull'
    if 'Interior /' in name:
        return 'console' if ob.name=='Cockpit_Console' else 'wall'
    if 'Accent /' in name:
        if (abs(x)<0.34 and -.55<y<.30 and .60<z<1.35) or (1.58<x<1.80 and -1.36<y<-.55 and .49<z<1.41):
            return 'upholstery'
    if ob.name=='Cockpit_HullExterior':
        return 'hull'
    if ob.name=='Cockpit_Interior':
        return 'wall'
    if ob.name=='Cockpit_Floor':
        return 'floor'
    return 'console'

def signature(poly,base):
    return (base.name,)+tuple(round(v,5) for v in poly.center)
lookup = {}
assignments = {}
for ob in module+[cut]:
    ob.data.update()
    originals = list(ob.data.materials)
    slot_map = {}
    counts = {}
    for poly in ob.data.polygons:
        base = originals[poly.material_index]
        key = signature(poly,base)
        x,y,z = poly.center
        if 'Screen /' in base.name and abs(x)<.78 and 2.36<y<2.39 and 1.60<z<2.22:
            mat = star
        elif ob==cut and key in lookup:
            mat = lookup[key]
        else:
            kind = category(ob,poly,base)
            mat = textured(base,kind) if kind else base
        if ob!=cut:
            lookup[key] = mat
        if mat.name not in slot_map:
            if mat in list(ob.data.materials):
                slot_map[mat.name] = list(ob.data.materials).index(mat)
            else:
                slot_map[mat.name] = len(ob.data.materials)
                ob.data.materials.append(mat)
        poly.material_index = slot_map[mat.name]
        counts[mat.name] = counts.get(mat.name,0)+1
    assignments[ob.name] = counts

# Fourth view: standing eye height, slightly left of the chair, facing forward.
stage = bpy.data.collections['RENDER']
cd = bpy.data.cameras.new('CAM_Closeup')
cd.lens = 19
cd.clip_start = 0.05
cd.clip_end = 2000
cam = bpy.data.objects.new('CAM_Closeup',cd)
stage.objects.link(cam)
cam.location = (-1.70,-0.70,1.75)
cam.rotation_euler = (Vector((0.10,0.90,1.04))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.cycles.samples = 48
scene.render.resolution_x,scene.render.resolution_y = 1920,1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
# Viewport hiding in the saved source should not interfere with the cutaway.
cut.hide_set(False)
cutlight = bpy.data.objects['Cutaway softbox']
planet = bpy.data.objects['RENDER_DistantPlanet']

def render(camera, name, cutaway=False):
    for ob in module:
        ob.hide_render = cutaway
    cut.hide_render = not cutaway
    cutlight.hide_render = not cutaway
    planet.hide_render = cutaway
    scene.camera = bpy.data.objects[camera]
    scene.render.filepath = os.path.join(OUT,name)
    bpy.ops.render.render(write_still=True)

render('CAM_Exterior','cockpit_exterior.png')
render('CAM_Interior','cockpit_interior.png')
render('CAM_TopDown','cockpit_topdown.png',True)
render('CAM_Closeup','cockpit_closeup.png')
for ob in module:
    ob.hide_render = False
cut.hide_render = True
cut.hide_set(True)
cutlight.hide_render = True
planet.hide_render = False
scene.camera = bpy.data.objects['CAM_Interior']
scene.render.filepath = os.path.join(OUT,'cockpit_interior.png')
cam.hide_set(True)
# Remove unused plain-colour slots so the material list shows only active shaders.
for ob in module+[cut]:
    previous = list(ob.data.materials)
    indices = sorted({p.material_index for p in ob.data.polygons})
    remap = {old:new for new,old in enumerate(indices)}
    saved = [remap[p.material_index] for p in ob.data.polygons]
    ob.data.materials.clear()
    for old in indices:
        ob.data.materials.append(previous[old])
    for poly,index in zip(ob.data.polygons,saved):
        poly.material_index = index
# Node-based box projection is preserved in .blend. FBX retains the updated
# geometry/material names, but a Unity shader must recreate these node graphs.
bpy.ops.object.select_all(action='DESELECT')
for ob in module+list(bpy.data.collections['COL'].objects):
    ob.hide_set(False)
    ob.select_set(True)
bpy.context.view_layer.objects.active = module[0]
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'cockpit_test.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',bake_space_transform=True,mesh_smooth_type='OFF',add_leaf_bones=False,bake_anim=False)
for ob in bpy.data.collections['COL'].objects:
    ob.hide_set(True)
bpy.data.texts.load(__file__)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'cockpit_test.blend'))
report = {'box_blend':0.2,'mapping_scale':scales,'image_files_packed':list(images),
          'uv_unwrap_performed':False,'closeup_camera_z':cam.location.z,
          'removed_chart_glyph_vertices':removed,'material_assignments':assignments}
for ob in module:
    ob.data.calc_loop_triangles()
report['module_triangles'] = sum(len(ob.data.loop_triangles) for ob in module)
with open(os.path.join(OUT,'watercolour_validation.json'),'w') as f:
    json.dump(report,f,indent=2)
print('WATERCOLOUR_COMPLETE',report['module_triangles'],flush=True)
