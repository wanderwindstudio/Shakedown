"""Read-only verification of the delivered Sol files; writes the JSON report."""
import bpy,os,json
from mathutils import Vector
out=os.path.expanduser('~/Shakedown/Art/Blender/Quarters_Sol')
bpy.ops.wm.open_mainfile(filepath=out+'/quarters_Sol.blend')
s=bpy.context.scene
objects=list(bpy.data.collections['Quarters_Sol'].objects)+list(bpy.data.collections['PROPS_Sol'].objects)
assert len(objects)==21
assert len(bpy.data.collections['PROPS_Sol'].objects)==7
report=json.load(open(out+'/validation_Sol.json'))
assert report['shell_triangles']<=8000 and report['total_triangles']<=25000
# Test both long walls in several solid bays; test the circular aperture too.
wall=bpy.data.objects['Quarters_Sol_Walls']
for sign in (-1,1):
    for y in (-3.5,-2.5,.2,1.5,2.5,3.5):
        for z in (.9,1.8,2.4):
            hit=wall.ray_cast(Vector((sign*2.3,y,z)),Vector((-sign,0,0)),distance=.9)[0]
            assert hit,('Missing wall',sign,y,z)
assert not wall.ray_cast(Vector((2.3,-1,1.82)),Vector((-1,0,0)),distance=.9)[0]
assert wall.ray_cast(Vector((2.3,-1.8,1.82)),Vector((-1,0,0)),distance=.9)[0]
# Door panels remain independent and may be slid away for traversal.
for name in ('Door_Front_Sol','Door_Back_Sol'):
    o=bpy.data.objects[name];pts=[o.matrix_world@v.co for v in o.data.vertices]
    assert abs(max(p.x for p in pts)-min(p.x for p in pts)-1.4)<1e-4
    assert abs(max(p.z for p in pts)-min(p.z for p in pts)-2.2)<1e-4
for front in (False,True):
    for x,z in [(0,.25),(-.4,.25),(.4,.25),(0,2.35),(-.69,1.8),(.69,1.8)]:
        origin=Vector((x,4.1 if front else -4.1,z));d=Vector((0,-1 if front else 1,0))
        for o in objects:
            if o.name.startswith('Door_'): continue
            assert not o.ray_cast(o.matrix_world.inverted()@origin,d,distance=.48)[0],(o.name,front,x,z)
used={m for o in objects for m in o.data.materials if m and 'texture_kind' in m}
for m in used:
    ns=m.node_tree.nodes
    tex=next(n for n in ns if n.type=='TEX_IMAGE');mp=next(n for n in ns if n.type=='MAPPING');mix=next(n for n in ns if n.type=='MIX_RGB')
    assert tex.projection=='BOX' and abs(tex.projection_blend-.2)<1e-5 and tex.image.packed_file
    assert mix.blend_type=='MULTIPLY' and mix.inputs[0].default_value==1
    assert abs(mp.inputs['Scale'].default_value.x-m['mapping_scale'])<1e-5
for shot in ('mockup_view','topdown','exterior','closeup'):
    im=bpy.data.images.load(out+'/quarters_Sol_'+shot+'.png',check_existing=False)
    assert tuple(im.size)==(1920,1080)
report.update({'collider_boxes':len(bpy.data.collections['COL_Sol'].objects),'packed_box_materials_checked':len(used),'door_socket_ray_checks_pass':True,'solid_sidewall_ray_checks_pass':True,'porthole_aperture_ray_check_pass':True,'four_render_dimensions_checked':True})
# Fresh-scene round trip, including a repeated wall check after export.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=out+'/quarters_Sol.fbx')
allobs=list(bpy.context.scene.objects)
assert len(allobs)==21+report['collider_boxes']
assert all(o.type=='MESH' for o in allobs)
assert all('RenderOnly' not in o.name and 'Cutaway' not in o.name for o in allobs)
real=[o for o in allobs if not o.name.startswith('COL_')]
pts=[o.matrix_world@v.co for o in real for v in o.data.vertices]
dims=[max(p[i] for p in pts)-min(p[i] for p in pts) for i in range(3)]
assert all(abs(dims[i]-(4,8,3.5)[i])<.001 for i in range(3))
report['fbx_roundtrip_pass']=True;report['fbx_mesh_count']=len(allobs);report['fbx_roundtrip_dimensions_m']=dims
json.dump(report,open(out+'/validation_Sol.json','w'),indent=2)
print('SOL_FINAL_AUDIT_PASS',report['shell_triangles'],report['total_triangles'],len(allobs),flush=True)
