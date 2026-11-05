"""SHAKEDOWN / CREW QUARTERS / SOL — comparison build, v2.

One commented, self-contained bpy script. Run in a NEW Blender Scripting tab.
WARNING: clears the current scene. All outputs stay in Quarters_Sol.
Uses only the five supplied watercolour surface textures (packed in the blend).
No UV unwrap. Set RENDER=False for a quick model/export-only run.
Axes: +Y forward; module envelope X +-2, Y +-4, Z 0..3.5 metres.
"""
import bpy, bmesh, math, os, json, random
from mathutils import Vector, Matrix
OUT = os.path.expanduser('~/Shakedown/Art/Blender/Quarters_Sol')
TEX = os.path.expanduser('~/Shakedown/Art/Textures/WatercolourTest')
RENDER = os.environ.get('QUARTERS_SOL_RENDER','1') == '1'
SAMPLES = int(os.environ.get('QUARTERS_SOL_SAMPLES','48'))
os.makedirs(OUT,exist_ok=True)
# 1. Reset; collections make the export/render separation explicit.
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob,do_unlink=True)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1

def collection(name):
    c=bpy.data.collections.new(name); scene.collection.children.link(c); return c
shellcol=collection('Quarters_Sol')
propcol=collection('PROPS_Sol')
colcol=collection('COL_Sol')
stage=collection('RENDER_ONLY_Sol')
cutcol=collection('CUTAWAY_RENDER_ONLY_Sol')
groups={}; roof=[]

# 2. Palette and the exact requested object-coordinate box projection graph.
def linear_hex(h):
    vals=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in vals)
imgs={}
for key,file in {'hull':'tex_hull_plating.png','wall':'tex_interior_wall.png','floor':'tex_floor.png','metal':'tex_console_metal.png','fabric':'tex_upholstery.png'}.items():
    im=bpy.data.images.load(os.path.join(TEX,file),check_existing=True); im.pack(); imgs[key]=im

def mat(name,h,kind=None,emission=0,alpha=1,metallic=0):
    m=bpy.data.materials.new(name+'_Sol'); m.use_nodes=True
    rgb=linear_hex(h); m.diffuse_color=(*rgb,alpha)
    nt=m.node_tree; p=nt.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*rgb,1)
    p.inputs['Roughness'].default_value=.78 if kind else .55
    p.inputs['Metallic'].default_value=metallic
    p.inputs['Alpha'].default_value=alpha
    p.inputs['Emission Color'].default_value=(*rgb,1)
    p.inputs['Emission Strength'].default_value=emission
    if kind:
        co=nt.nodes.new('ShaderNodeTexCoord'); co.location=(-750,60)
        mp=nt.nodes.new('ShaderNodeMapping'); mp.location=(-540,60)
        scale={'hull':.5,'wall':.5,'floor':.5,'metal':1,'fabric':2}[kind]
        mp.inputs['Scale'].default_value=(scale,)*3
        tx=nt.nodes.new('ShaderNodeTexImage'); tx.image=imgs[kind]
        tx.projection='BOX'; tx.projection_blend=.2; tx.extension='REPEAT'; tx.location=(-320,60)
        mix=nt.nodes.new('ShaderNodeMixRGB'); mix.blend_type='MULTIPLY'
        mix.inputs[0].default_value=1; mix.inputs[1].default_value=(*rgb,1); mix.location=(-70,60)
        nt.links.new(co.outputs['Object'],mp.inputs['Vector']); nt.links.new(mp.outputs[0],tx.inputs['Vector'])
        nt.links.new(tx.outputs['Color'],mix.inputs[2]); nt.links.new(mix.outputs[0],p.inputs['Base Color'])
        m['texture_kind']=kind; m['mapping_scale']=scale
    return m
M={
'hull':mat('Hull_Cream','E8DDD2','hull'),'wall':mat('Wall_WarmBeige','E3D3C6','wall'),
'cream':mat('Cabinet_Cream','E8DDD2','metal'),'slate':mat('Ribs_DarkSlate','4A4650','metal'),
'floor':mat('Floor_GreyViolet','5A5560','floor'),'sage':mat('Lockers_Sage','7FA39A','metal'),
'fabric':mat('Cushions_Sage','7FA39A','fabric'),'teal':mat('Accent_DeepTeal','5E857F','metal'),
'ochre':mat('Ladder_Pipes_Ochre','C9973A','metal'),'blanket':mat('Blanket_Ochre','C9973A','fabric'),
'pillow':mat('Pillow_Cream','E8DDD2','fabric'),'dark':mat('Recess_Shadow','37343E','metal'),
'light':mat('Light_WarmAmber','FFD9A3',emission=2.5),'glass':mat('Porthole_Glass','B9D3D7',alpha=.12),
'leaf':mat('Plant_Sage','7FA39A','fabric'),'leafdark':mat('Plant_DeepTeal','5E857F','fabric'),
'soil':mat('Pot_Soil','4A4650','floor'),'paper':mat('Picture_Paper','E8DDD2','wall'),
'picturepurple':mat('Picture_Hills','877A96','fabric'),'picturesky':mat('Picture_Dusk','BCA0A2','fabric'),
}

# 3. Geometry helpers. Bevels use one flat segment: shape definition, not wear.
def add(ob,group,material,roofpart=False):
    for c in list(ob.users_collection): c.objects.unlink(ob)
    (propcol if group.startswith('Prop_') else shellcol).objects.link(ob)
    if isinstance(material,str): material=M[material]
    ob.data.materials.append(material)
    for p in ob.data.polygons: p.use_smooth=False
    groups.setdefault(group,[]).append(ob)
    if roofpart: roof.append(ob)
    ob.name=group+'_part_Sol'
    return ob

def box(group,c,size,material,bev=.018,rot=(0,0,0),roofpart=False):
    bpy.ops.mesh.primitive_cube_add(size=1,location=c); ob=bpy.context.object
    ob.dimensions=size; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bev:
        mod=ob.modifiers.new('One_flat_chamfer_Sol','BEVEL'); mod.width=min(bev,min(size)*.24); mod.segments=1
        bpy.ops.object.modifier_apply(modifier=mod.name)
    ob.rotation_euler=tuple(math.radians(a) for a in rot)
    return add(ob,group,material,roofpart)

def mesh(group,verts,faces,material,roofpart=False):
    me=bpy.data.meshes.new(group+'_Mesh_Sol'); me.from_pydata(verts,[],faces); me.update()
    ob=bpy.data.objects.new(group+'_part_Sol',me); shellcol.objects.link(ob)
    return add(ob,group,material,roofpart)

def prism(group,outline,offset,material,roofpart=False):
    pts=[Vector(v) for v in outline]; v=Vector(offset); n=len(pts)
    verts=pts+[p+v for p in pts]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    ob=mesh(group,verts,faces,material,roofpart)
    bm=bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces)); bm.to_mesh(ob.data); bm.free()
    return ob

def rod(group,a,b,r,material,n=8):
    a,b=Vector(a),Vector(b); d=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=d.length,location=(a+b)/2)
    ob=bpy.context.object; ob.rotation_euler=d.to_track_quat('Z','Y').to_euler()
    return add(ob,group,material)

def beam(group,a,b,width,depth,material):
    a,b=Vector(a),Vector(b); ob=box(group,(a+b)/2,(width,depth,(b-a).length),material,bev=.006)
    ob.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler(); return ob

def chamfer_rect(w,h,c):
    return [(-w/2+c,0),(w/2-c,0),(w/2,c),(w/2,h-c),(w/2-c,h),(-w/2+c,h),(-w/2,h-c),(-w/2,c)]

def ring_x(group,x0,x1,y,z,rin,rout,material,n=32):
    verts=[]
    for xx,rr in [(x0,rin),(x0,rout),(x1,rin),(x1,rout)]:
        verts += [(xx,y+math.cos(i*math.tau/n)*rr,z+math.sin(i*math.tau/n)*rr) for i in range(n)]
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces += [(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)]
    return mesh(group,verts,faces,material)

def inset(poly,d):
    # Offset every edge of a CCW convex polygon inwards by d metres.
    lines=[]
    for i,p in enumerate(poly):
        p,q=Vector(p),Vector(poly[(i+1)%len(poly)]); e=(q-p).normalized()
        lines.append((p+Vector((-e.y,e.x))*d,e))
    result=[]
    for i,(q,f) in enumerate(lines):
        p,e=lines[i-1]; den=e.x*f.y-e.y*f.x
        t=((q.x-p.x)*f.y-(q.y-p.y)*f.x)/den
        result.append(tuple(p+e*t))
    return result

# 4. The frozen octagonal section, with exact .8 upper / .5 lower chamfers.
O=[(-1.5,0),(1.5,0),(2,.5),(2,2.7),(1.2,3.5),(-1.2,3.5),(-2,2.7),(-2,.5)]
s=.25*math.sqrt(2)
I=[(-1.5+s-.2,.2),(1.5-s+.2,.2),(1.75,.25+s),(1.75,2.95-s),(1.5-s,3.2),(-1.5+s,3.2),(-1.75,2.95-s),(-1.75,.25+s)]
# Each long wall segment is a closed wedge, so the porthole Boolean is robust.
rightwall=None
for edge in (1,2,3,5,6,7):
    j=(edge+1)%8
    profile=[(O[edge][0],-3.75,O[edge][1]),(O[j][0],-3.75,O[j][1]),(I[j][0],-3.75,I[j][1]),(I[edge][0],-3.75,I[edge][1])]
    ob=prism('Walls',profile,(0,7.5,0),'hull',roofpart=edge in (3,5))
    ob.data.materials.append(M['wall'])
    # The inward face is the quad linking the two inner cross-section points.
    for p in ob.data.polygons:
        ids=list(p.vertices)
        if len(ids)==4 and all(i in (2,3,6,7) for i in ids): p.material_index=1
    if edge==2: rightwall=ob
# Roof and floor are separately removable/inspectable.
prism('Ceiling',[(O[4][0],-3.75,O[4][1]),(O[5][0],-3.75,O[5][1]),(I[5][0],-3.75,I[5][1]),(I[4][0],-3.75,I[4][1])],(0,7.5,0),'wall',roofpart=True)
prism('Floor',[(-1.5,-3.75,0),(1.5,-3.75,0),(1.7,-3.75,.2),(-1.7,-3.75,.2)],(0,7.5,0),'floor')
# Quiet, flush deck divisions. Rivets and scuffs come from the texture.
for y in (-3,-2,-1,0,1,2,3):
    box('Floor',(0,y,.201),(2.68,.012,.002),'slate',bev=0)
box('Floor',(0,0,.201),(.012,7.9,.002),'slate',bev=0)
# Closed end walls with the exact chamfered door cutout.
D=[(x,z+.2) for x,z in chamfer_rect(1.4,2.2,.25)]
for front,y0,dy in [(False,-4,.25),(True,3.75,.25)]:
    wall=prism('EndWalls',[(x,y0,z) for x,z in O],(0,dy,0),'wall')
    cutter=prism('Temporary',[(x,y0-.1,z) for x,z in D],(0,.45,0),'dark')
    bpy.context.view_layer.objects.active=wall
    mod=wall.modifiers.new('Door_socket_Sol','BOOLEAN'); mod.operation='DIFFERENCE'; mod.solver='EXACT'; mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    groups['Temporary'].remove(cutter); bpy.data.objects.remove(cutter,do_unlink=True)
    # Separate, closed panel; frame outline follows the chamfered connector.
    yy=3.91 if front else -3.96
    name='Door_Front' if front else 'Door_Back'
    prism(name,[(x,yy,z) for x,z in D],(0,.045,0),'cream')
    larger=[(x,z+.13) for x,z in chamfer_rect(1.54,2.34,.27)]
    for i in range(8):
        a,b=larger[i],larger[(i+1)%8]
        beam('DoorFrames',(a[0],3.72 if front else -3.72,a[1]),(b[0],3.72 if front else -3.72,b[1]),.075,.06,'slate')
    box(name,(0,3.877 if front else -3.89,1.30),(.022,.009,1.57),'teal',bev=0)
    box(name,(.48,3.87 if front else -3.88,1.35),(.05,.018,.25),'teal',bev=.006)
# Octagonal ribs: ends are clipped inwards so no geometry crosses a grid face.
inner_rib=inset(I,.10)
for y in (-4,-2,0,2,4):
    a=max(-4,y-.1); b=min(4,y+.1)
    if y==-4: b=-3.8
    if y==4: a=3.8
    for i in range(1,8): # bottom bar omitted to keep the deck flush at Z=.2
        j=(i+1)%8
        rib=prism('Ribs',[(I[i][0],a,I[i][1]),(I[j][0],a,I[j][1]),(inner_rib[j][0],a,inner_rib[j][1]),(inner_rib[i][0],a,inner_rib[i][1])],(0,b-a,0),'slate',roofpart=i in (3,4,5))
        if abs(y)==4:
            # The end cap already supplies this face; remove its duplicate.
            bm=bmesh.new(); bm.from_mesh(rib.data)
            fs=[f for f in bm.faces if all(abs(v.co.y-y)<1e-5 for v in f.verts)]
            bmesh.ops.delete(bm,geom=fs,context='FACES_ONLY'); bm.to_mesh(rib.data); bm.free()
# Pipe positions are constant all the way through both section end planes.
pipe_positions=[(1.25,2.98,.045),(1.10,3.08,.035)]
for x,z,r in pipe_positions:
    rod('Pipes',(x,-4,z),(x,4,z),r,'ochre',n=10)
    for y in (-3.9,-2,0,2,3.9):
        rod('Pipes',(x,y-.035,z),(x,y+.035,z),r+.018,'slate',n=10)
        beam('Pipes',(x+.035,y,z+.035),(x+.105,y,z+.105),.045,.055,'slate')

# 5. Bunks: two chamfered open niches, bedding, drawer faces and ochre ladder.
# The front is at X=-.65; together with the dinette this leaves a 1.30 m aisle.
BY=-1.18
box('Bunks',(-1.22,BY,.45),(1.05,2.95,.50),'cream',bev=.045)
box('Bunks',(-1.22,BY,1.56),(1.05,2.95,.16),'cream',bev=.04)
box('Bunks',(-1.22,BY,2.64),(1.05,2.95,.15),'cream',bev=.04,roofpart=True)
# End partitions and niche backings; the opening's four clipped corners show
# as large, deliberate facets rather than dense bevel subdivisions.
for y in (BY-1.46,BY+1.46):
    box('Bunks',(-1.20,y,1.57),(1.10,.12,2.13),'cream',bev=.035)
for z in (.70,1.73):
    box('Bunks',(-1.704,BY,z+.38),(.055,2.78,.83),'teal',bev=.02)
    # Frame in the Y/Z plane, open middle; opening length 2.80, height .90.
    outline=[(y+BY,z+zz) for y,zz in chamfer_rect(2.80,.90,.16)]
    for i in range(8):
        a,b=outline[i],outline[(i+1)%8]
        beam('Bunks',(-.668,a[0],a[1]),(-.668,b[0],b[1]),.11,.10,'cream')
    box('Bunks',(-1.21,BY,z+.06),(.86,2.53,.16),'fabric',bev=.055)
    box('Bunks',(-1.21,BY+.80,z+.22),(.72,.50,.19),'pillow',bev=.07,rot=(0,-7,0))
    box('Bunks',(-1.21,BY-.67,z+.16),(.87,.82,.045),'blanket',bev=.015)
    box('Bunks',(-.785,BY-.67,z+.06),(.045,.82,.22),'blanket',bev=.012)
    # Warm reading light on each niche's inner end wall.
    box('Lights',(-1.29,BY+.99,z+.66),(.42,.08,.08),'slate',bev=.018)
    box('Lights',(-1.29,BY+.945,z+.64),(.34,.014,.045),'light',bev=.008)
for y in (BY-1.0,BY,BY+1.0):
    box('Bunks',(-.675,y,.43),(.035,.91,.34),'cream',bev=.02)
    box('Bunks',(-.649,y,.45),(.016,.31,.07),'dark',bev=.012)
# The ladder remains on the left side of the walkway, at the bunks' foot.
for y in (BY-1.25,BY-.68):
    beam('Bunks',(-.60,y,.24),(-.60,y,2.42),.075,.075,'slate')
for z in (.47,.88,1.29,1.70,2.11):
    rod('Bunks',(-.57,BY-1.25,z),(-.57,BY-.68,z),.037,'ochre',n=8)

# 6. Built-in overhead cabinets, warm strip and central ceiling panel.
for sign in (-1,1):
    for y in (-2.85,-1.85,-.85,.15,1.15):
        # Cabinet cross-section tucks into the upper chamfer.
        if sign<0:
            profile=[(-1.38,y-.46,2.70),(-1.38,y-.46,2.94),(-1.18,y-.46,3.13),(-1.04,y-.46,3.13),(-1.04,y-.46,2.70)]
        else:
            profile=[(1.68,y-.46,2.40),(1.68,y-.46,2.54),(1.46,y-.46,2.76),(1.04,y-.46,2.76),(1.04,y-.46,2.40)]
        prism('Cabinets',profile,(0,.92,0),'cream',roofpart=True)
        box('Cabinets',(sign*1.025,y,2.87 if sign<0 else 2.58),(.018,.32,.065),'teal',bev=.01,roofpart=True)
    if sign==1:
        box('Lights',(1.39,-.98,2.375),(.39,3.78,.045),'slate',roofpart=True)
        box('Lights',(1.39,-.98,2.346),(.29,3.68,.018),'light',bev=.006,roofpart=True)
box('Lights',(0,-.5,3.145),(1.03,1.60,.11),'slate',bev=.055,roofpart=True)
box('Lights',(0,-.5,3.078),(.85,1.40,.027),'light',bev=.025,roofpart=True)

# 7. Two far-end lockers (one prop) beside the central doorway.
for x in (-1.45,-.99):
    box('Prop_Lockers',(x,3.32,1.40),(.43,.66,2.35),'sage',bev=.045)
    box('Prop_Lockers',(x,2.971,1.43),(.36,.028,2.20),'sage',bev=.035)
    for z in (2.17,2.28,2.39):
        box('Prop_Lockers',(x,2.949,z),(.25,.012,.032),'dark',bev=.006)
    box('Prop_Lockers',(x+.105,2.938,1.28),(.04,.022,.27),'teal',bev=.009)
# Wash niche on the right of the rear wall, outside the full connector path.
box('WashNiche',(1.20,3.46,1.29),(.83,.49,2.10),'teal',bev=.045)
box('WashNiche',(1.20,3.187,1.86),(.72,.024,.86),'wall',bev=.04)
box('WashNiche',(1.20,3.15,.72),(.82,.52,1.03),'cream',bev=.045)
box('WashNiche',(1.20,2.98,1.20),(.84,.63,.16),'cream',bev=.055)
# Recessed basin ring: four broad rim pieces surrounding a dark well.
box('WashNiche',(1.20,2.96,1.287),(.53,.35,.014),'teal',bev=.045)
for x in (.87,1.53): box('WashNiche',(x,2.97,1.31),(.12,.52,.08),'cream',bev=.025)
for y in (2.75,3.18): box('WashNiche',(1.20,y,1.31),(.57,.10,.08),'cream',bev=.025)
rod('WashNiche',(1.18,3.17,1.31),(1.18,3.17,1.57),.025,'ochre')
rod('WashNiche',(1.18,3.17,1.57),(1.18,3.02,1.57),.025,'ochre')
rod('WashNiche',(1.18,3.02,1.57),(1.18,3.02,1.51),.025,'ochre')
box('WashNiche',(.94,3.08,1.47),(.12,.13,.23),'sage',bev=.025)
box('WashNiche',(.94,3.08,1.61),(.10,.04,.04),'slate',bev=.009)
box('WashNiche',(1.45,2.878,.79),(.035,.025,.25),'teal',bev=.006)
box('Lights',(1.20,3.15,2.38),(.72,.17,.11),'slate',bev=.025)
box('Lights',(1.20,3.102,2.315),(.58,.09,.025),'light',bev=.009)

# 8. Dinette prop: two opposed benches, wall-bracket table and sage cushions.
DY=-1.0
for y,sign in ((DY-1.04,-1),(DY+1.04,1)):
    box('Prop_Dinette',(1.17,y,.46),(1.04,.61,.52),'cream',bev=.055)
    box('Prop_Dinette',(1.17,y,.77),(.96,.59,.16),'fabric',bev=.055)
    box('Prop_Dinette',(1.17,y+sign*.25,1.09),(1.04,.15,.69),'cream',bev=.05)
    box('Prop_Dinette',(1.17,y+sign*.15,1.13),(.94,.13,.53),'fabric',bev=.045)
box('Prop_Dinette',(1.17,DY,1.01),(1.08,.97,.13),'cream',bev=.065)
for y in (DY-.31,DY+.31):
    beam('Prop_Dinette',(1.71,y,.58),(.81,y,.945),.075,.07,'slate')
# Actual circular opening through the right wall; 32 facets, not smooth shading.
cutter=rod('Temporary',(1.40,DY,1.82),(2.15,DY,1.82),.595,'dark',n=32)
bpy.context.view_layer.objects.active=rightwall
mod=rightwall.modifiers.new('Porthole_aperture_Sol','BOOLEAN'); mod.operation='DIFFERENCE'; mod.solver='EXACT'; mod.object=cutter
bpy.ops.object.modifier_apply(modifier=mod.name)
groups['Temporary'].remove(cutter); bpy.data.objects.remove(cutter,do_unlink=True)
# The exterior rim sits in a shallow recess, never coplanar over the hull skin.
cutter=rod('Temporary',(1.969,DY,1.82),(2.12,DY,1.82),.732,'dark',n=32)
bpy.context.view_layer.objects.active=rightwall
mod=rightwall.modifiers.new('Outer_rim_recess_Sol','BOOLEAN'); mod.operation='DIFFERENCE'; mod.solver='EXACT'; mod.object=cutter
bpy.ops.object.modifier_apply(modifier=mod.name)
groups['Temporary'].remove(cutter); bpy.data.objects.remove(cutter,do_unlink=True)
ring_x('Porthole',1.69,1.76,DY,1.82,.58,.73,'cream')
ring_x('Porthole',1.675,1.70,DY,1.82,.577,.61,'ochre')
ring_x('Porthole',1.97,2.0,DY,1.82,.58,.73,'hull')
rod('Porthole',(1.88,DY,1.82),(1.889,DY,1.82),.581,'glass',n=32)
# Bolts define the porthole ring; no decorative hull rivet geometry.
for k in range(12):
    a=k*math.tau/12
    y,z=DY+.663*math.cos(a),1.82+.663*math.sin(a)
    rod('Porthole',(1.658,y,z),(1.681,y,z),.025,'slate',n=6)
# Ceramic mug on a coaster, hollow rim with coffee; closed sage book.
rod('Prop_Mug',(1.15,DY+.17,1.08),(1.15,DY+.17,1.092),.115,'ochre',n=12)
rod('Prop_Mug',(1.15,DY+.17,1.095),(1.15,DY+.17,1.275),.078,'cream',n=12)
# Cup rim in XY plane, made with torus; still deliberately flat shaded.
bpy.ops.mesh.primitive_torus_add(major_segments=12,minor_segments=4,location=(1.15,DY+.17,1.278),major_radius=.068,minor_radius=.012)
add(bpy.context.object,'Prop_Mug','cream')
rod('Prop_Mug',(1.15,DY+.17,1.277),(1.15,DY+.17,1.279),.055,'dark',n=12)
# Open handle loop, low-poly outline.
for a,b in [((1.22,DY+.17,1.23),(1.28,DY+.17,1.23)),((1.28,DY+.17,1.23),(1.28,DY+.17,1.13)),((1.28,DY+.17,1.13),(1.22,DY+.17,1.13))]: rod('Prop_Mug',a,b,.012,'cream',n=6)
box('Prop_Book',(1.04,DY-.23,1.10),(.31,.39,.045),'paper',bev=.007,rot=(0,0,-9))
for z in (1.073,1.127): box('Prop_Book',(1.04,DY-.23,z),(.33,.41,.012),'sage',bev=.006,rot=(0,0,-9))

# 9. Trailing plant in a wall holder. Broad faceted leaves, not smooth spheres.
PY=DY+.99
box('Prop_Plant',(1.69,PY,1.57),(.10,.42,.12),'slate',bev=.018)
rod('Prop_Plant',(1.54,PY,1.53),(1.54,PY,1.79),.145,'ochre',n=10)
rod('Prop_Plant',(1.54,PY,1.79),(1.54,PY,1.794),.13,'soil',n=10)
rnd=random.Random(14)
def leaf(c,angle,length,width,matkey):
    c=Vector(c); d=Vector((math.cos(angle),math.sin(angle),-.25)).normalized(); u=Vector((-d.y,d.x,0))
    tip=c+d*length
    pts=[c,c+d*length*.45+u*width,c+d*length*.53+Vector((0,0,.035)),tip,c+d*length*.45-u*width]
    mesh('Prop_Plant',pts,[(0,1,2),(1,3,2),(3,4,2),(4,0,2)],matkey)
for k in range(8):
    a=k*math.tau/8
    start=(1.54,PY,1.79); end=(1.54+.19*math.cos(a),PY+.19*math.sin(a),1.95+rnd.uniform(-.06,.14))
    rod('Prop_Plant',start,end,.009,'leafdark',n=5)
    leaf(end,a,.22,.085,'leaf' if k%2 else 'leafdark')
trail=[(1.48,PY-.11,1.83),(1.38,PY-.21,1.65),(1.35,PY-.26,1.43),(1.39,PY-.32,1.22),(1.35,PY-.35,1.07)]
for a,b in zip(trail,trail[1:]): rod('Prop_Plant',a,b,.009,'leafdark',n=5)
for k in range(12):
    t=k/3; i=min(int(t),3); f=min(t-i,1)
    c=Vector(trail[i]).lerp(Vector(trail[i+1]),f)
    leaf(c,(-1 if k%2 else 1)*1.5,.16,.06,'leaf' if k%2 else 'leafdark')

# 10. Hanging jacket and two taped landscape cards, on the far right sidewall.
# A thin extruded silhouette keeps the coat faceted but recognisably fabric.
JY=1.67
outline=[(-.22,0),(.22,0),(.23,.72),(.37,.47),(.47,.52),(.30,1.00),(.12,1.12),(-.12,1.12),(-.30,1.00),(-.47,.52),(-.37,.47),(-.23,.72)]
prism('Prop_Jacket',[(1.63,JY+y,1.02+z) for y,z in outline],(.075,0,0),'fabric')
box('Prop_Jacket',(1.616,JY,1.54),(.015,.018,.91),'teal',bev=.004)
for sign in (-1,1):
    prism('Prop_Jacket',[(1.60,JY+sign*.02,2.09),(1.60,JY+sign*.17,2.05),(1.60,JY+sign*.12,1.91)],(.025,0,0),'teal')
rod('WashNiche',(1.70,JY,2.21),(1.58,JY,2.21),.025,'slate')
rod('WashNiche',(1.58,JY,2.21),(1.58,JY,2.29),.025,'slate')
# Pictures are geometric paper collages tinted by the watercolour materials.
for yc,zc,w,h in ((2.48,2.05,.48,.48),(2.76,1.48,.35,.37)):
    box('Prop_Pictures',(1.705,yc,zc),(.025,w+.025,h+.025),'paper',bev=.007)
    box('Prop_Pictures',(1.685,yc,zc),(.008,w,h),'picturesky',bev=0)
    for row,material in ((0,'picturepurple'),(1,'teal')):
        pts=[(1.675-row*.002,yc-w/2,zc-h/2),(1.675-row*.002,yc+w/2,zc-h/2),(1.675-row*.002,yc+w/2,zc-h*.10-row*.06),(1.675-row*.002,yc+w*.15,zc+h*.15-row*.12),(1.675-row*.002,yc-w*.13,zc-h*.03-row*.05),(1.675-row*.002,yc-w*.35,zc+h*.24-row*.16),(1.675-row*.002,yc-w/2,zc)]
        mesh('Prop_Pictures',pts,[tuple(range(len(pts)))],material)
    for sign in (-1,1): box('Prop_Pictures',(1.66,yc+sign*w*.39,zc+h*.48),(.012,.065,.13),'pillow',bev=0,rot=(sign*7,0,0))

# 11. Exterior remains a clean faceted cream hull. Panel wear is in its texture.

# 12. Join semantic objects, bake scales, and set origins.
# Shell origins = section floor centre; prop origins = own footprint base centre.
# Cutaway copies keep the original world positions and are NOT exported.
# Pipe end caps are internal faces of the solid connector end wall: omit them.
for ob in groups['Pipes']:
    bpy.context.view_layer.update()
    bm=bmesh.new(); bm.from_mesh(ob.data)
    fs=[f for f in bm.faces if all(abs((ob.matrix_world@v.co).y-4)<1e-5 for v in f.verts) or all(abs((ob.matrix_world@v.co).y+4)<1e-5 for v in f.verts)]
    if fs: bmesh.ops.delete(bm,geom=fs,context='FACES_ONLY')
    bm.to_mesh(ob.data); bm.free()
roofset=set(roof)
cutparts=[]
for group,obs in groups.items():
    for ob in obs:
        if ob in roofset or group in ('Ceiling','Door_Back'): continue
        clone=ob.copy(); clone.data=ob.data.copy(); cutcol.objects.link(clone)
        # Slice architecture and end ribs; props remain intact.
        if not group.startswith('Prop_') and group not in ('Bunks','WashNiche','Porthole'):
            bpy.context.view_layer.update()
            bm=bmesh.new(); bm.from_mesh(clone.data)
            inv=clone.matrix_world.inverted()
            plane=inv@Vector((0,0,1.65)); normal=clone.matrix_world.to_3x3().transposed()@Vector((0,0,1))
            bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=plane,plane_no=normal,clear_outer=True)
            bm.to_mesh(clone.data); bm.free()
        clone.hide_render=True; cutparts.append(clone)

def join(obs,name,prop=False,targetcol=None):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in obs: ob.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    if len(obs)>1: bpy.ops.object.join()
    ob=bpy.context.object; ob.name=name
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    if prop:
        pts=[ob.matrix_world@v.co for v in ob.data.vertices]
        origin=Vector(((min(p.x for p in pts)+max(p.x for p in pts))/2,(min(p.y for p in pts)+max(p.y for p in pts))/2,min(p.z for p in pts)))
    else: origin=Vector((0,0,0))
    scene.cursor.location=origin; bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    for p in ob.data.polygons: p.use_smooth=False
    return ob
objects=[]
for group,obs in list(groups.items()):
    if not obs: continue
    prop=group.startswith('Prop_')
    name=(group+'_Sol') if prop or group.startswith('Door_') else ('Quarters_Sol_'+group)
    objects.append(join(obs,name,prop))
cut=join(cutparts,'Quarters_Sol_Cutaway_RenderOnly')
cut.hide_render=True

# 13. Box colliders: floor, sidewalls, door jambs, built-ins and prop bodies.
def collider(name,c,size):
    bpy.ops.mesh.primitive_cube_add(size=1,location=c); ob=bpy.context.object; ob.name='COL_'+name+'_Sol'
    ob.dimensions=size; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for cc in list(ob.users_collection): cc.objects.unlink(ob)
    colcol.objects.link(ob); ob.display_type='WIRE'; ob.hide_render=True
    return ob
collider('Floor',(0,0,.10),(3.0,8,.20))
for sign in (-1,1): collider('Wall_'+str(sign),(sign*1.88,0,1.75),(.24,8,3.5))
collider('Ceiling',(0,0,3.35),(2.30,8,.30))
for tag,y in [('Back',-3.88),('Front',3.88)]:
    collider(tag+'_Left',(-1.35,y,1.75),(1.30,.24,3.5))
    collider(tag+'_Right',(1.35,y,1.75),(1.30,.24,3.5))
    collider(tag+'_Top',(0,y,2.95),(1.4,.24,1.10))
    collider('Door_'+tag,(0,y,1.30),(1.4,.05,2.20))
collider('Bunks',(-1.20,BY,1.43),(1.10,3.08,2.46))
collider('Ladder',(-.60,BY-.965,1.32),(.075,.65,2.16))
collider('Lockers',(-1.22,3.32,1.40),(.89,.68,2.35))
collider('WashNiche',(1.20,3.25,1.29),(.84,.86,2.10))
for y in (DY-1.04,DY+1.04): collider('Bench_'+str(y),(1.17,y, .85),(1.04,.76,1.30))
collider('Table',(1.17,DY,1.01),(1.08,.97,.13))

# 14. Warm render-only lighting and the view through the real porthole opening.
scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=SAMPLES
scene.cycles.use_denoising=True; scene.cycles.max_bounces=8; scene.cycles.transparent_max_bounces=12
scene.render.resolution_x=1920; scene.render.resolution_y=1080; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.view_settings.view_transform='AgX'
scene.world=bpy.data.worlds.new('Dusk_World_Sol'); scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.13,.095,.19,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35

def aim(ob,target): ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
def light(name,loc,target,power,color,size):
    d=bpy.data.lights.new(name+'_Sol','AREA'); d.energy=power; d.color=color; d.shape='DISK'; d.size=size
    ob=bpy.data.objects.new(name+'_Sol',d); stage.objects.link(ob); ob.location=loc; aim(ob,target); return ob
light('CeilingSoft',(0,-.5,3.02),(0,-.5,.3),80,(1,.78,.53),2.5)
light('WarmFill',(0,-3.45,2.45),(0,1.7,1.1),55,(1,.82,.64),2.5)
light('FarFill',(0,2.3,2.9),(0,1,.5),45,(1,.82,.65),1.6)
light('DinetteGlow',(1.29,DY,2.28),(.7,DY,.7),32,(1,.77,.48),1.2)
for z in (1.10,2.13): light('BunkReading_'+str(z),(-1.2,BY+.90,z+.15),(-1.2,BY,z-.2),9,(1,.74,.43),.35)
light('WashGlow',(1.2,2.94,2.3),(1.2,3.1,1.2),13,(1,.80,.58),.5)
light('WindowSky',(2.8,DY,2.0),(0,DY,1.0),45,(.60,.72,1),2)
extkey=light('ExteriorDuskKey',(-6,-7,10),(0,0,1),1700,(1,.84,.73),8)
extfill=light('ExteriorLavender',(5,5,8),(0,0,1),1250,(.66,.61,1),7)
cutlight=light('CutawaySoftbox',(0,0,10),(0,0,0),900,(1,.86,.71),7); cutlight.hide_render=True
# A faceted ocean world glimpsed through the window. Never exported.
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3,radius=8.5,location=(10,10,-6))
planet=bpy.context.object; planet.name='Planet_RenderOnly_Sol'
for c in list(planet.users_collection): c.objects.unlink(planet)
stage.objects.link(planet)
pm=mat('Planet_RenderOnly','7F9BAE',emission=.35); planet.data.materials.append(pm)
# Dark starfield beyond the porthole. Explicit geometry belongs only to staging.
skymat=mat('Starfield_RenderOnly','10182E',emission=.6)
me=bpy.data.meshes.new('Starfield_Backdrop_Mesh_Sol')
me.from_pydata([(19,-18,-12),(19,40,-12),(19,40,18),(19,-18,18)],[],[(0,1,2,3)])
sky=bpy.data.objects.new('Starfield_Backdrop_RenderOnly_Sol',me); stage.objects.link(sky); me.materials.append(skymat)
star_mat=mat('Stars_RenderOnly','D8DDE8',emission=2)
rng=random.Random(78); vs=[]; fs=[]
for k in range(420):
    y,z=rng.uniform(-18,40),rng.uniform(-12,18); r=rng.uniform(.012,.055); q=len(vs)
    vs.extend([(18.95,y+math.cos(j*math.tau/5)*r,z+math.sin(j*math.tau/5)*r) for j in range(5)])
    fs.append(tuple(range(q,q+5)))
sm=bpy.data.meshes.new('Stars_Mesh_RenderOnly_Sol'); sm.from_pydata(vs,[],fs)
stars=bpy.data.objects.new('Stars_RenderOnly_Sol',sm); stage.objects.link(stars); sm.materials.append(star_mat)
# Gentle fog glow uses compositor nodes; no harsh bloom halo.
nt=bpy.data.node_groups.new('WarmGlow_Compositor_Sol','CompositorNodeTree')
scene.compositing_node_group=nt
nt.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
rl=nt.nodes.new('CompositorNodeRLayers'); glare=nt.nodes.new('CompositorNodeGlare')
glare.inputs['Type'].default_value='Fog Glow'
glare.inputs['Quality'].default_value='High'
glare.inputs['Threshold'].default_value=1.5
glare.inputs['Strength'].default_value=.07
comp=nt.nodes.new('NodeGroupOutput'); nt.links.new(rl.outputs['Image'],glare.inputs['Image']); nt.links.new(glare.outputs['Image'],comp.inputs['Image'])

def camera(name,loc,target,lens=20,ortho=None):
    d=bpy.data.cameras.new(name+'_Sol'); d.lens=lens; d.clip_start=.04; d.clip_end=2000
    if ortho: d.type='ORTHO'; d.ortho_scale=ortho
    ob=bpy.data.objects.new(name+'_Sol',d); stage.objects.link(ob); ob.location=loc; aim(ob,target); return ob
cam=camera('CAM_Mockup',(0,-3.67,1.90),(0,2.1,1.57),20)
# Eye height is 1.7 m above the standardized deck surface at Z=.2.
close=camera('CAM_Closeup',(-.45,-2.63,1.90),(1.24,-.94,1.47),23)
top=camera('CAM_Topdown',(0,0,14),(0,0,0),ortho=9.05); top.rotation_euler=(0,0,math.pi/2)
ext=camera('CAM_Exterior',(8.2,-10.6,6.6),(0,0,1.65),40)

# 15. Validate the envelope, flat shading, prop pivots and budgets before export.
report={'suffix':'Sol','section_size_m':[4,8,3.5],'floor_z':.2,'ceiling_underside_z':3.2,
        'doorway_m':[1.4,2.2],'door_corner_chamfer_m':.25,'outer_chamfers_m':{'upper':.8,'lower':.5},
        'wall_thickness_m':.25,'rib_centres_y':[-4,-2,0,2,4],'pipe_positions_xz':pipe_positions,
        'main_camera_eye_above_floor_m':1.7,'minimum_central_furniture_aisle_m':1.13,
        'triangles':{},'prop_origins':{},'unity_import_tested':False}
pts=[]
for ob in objects:
    ob.data.calc_loop_triangles(); count=len(ob.data.loop_triangles); report['triangles'][ob.name]=count
    assert all(not p.use_smooth for p in ob.data.polygons),ob.name
    coords=[ob.matrix_world@v.co for v in ob.data.vertices]; pts+=coords
    if ob.name.startswith('Prop_'):
        assert count<=1500,(ob.name,count)
        report['prop_origins'][ob.name]=list(ob.location)
    else: assert ob.location.length<1e-5,ob.name
lo=[min(p[i] for p in pts) for i in range(3)]; hi=[max(p[i] for p in pts) for i in range(3)]
report['bounds_min_m']=lo; report['bounds_max_m']=hi
assert all(lo[i]>=(-2,-4,0)[i]-.0001 for i in range(3)),lo
assert all(hi[i]<=(2,4,3.5)[i]+.0001 for i in range(3)),hi
shelltris=sum(n for k,n in report['triangles'].items() if not k.startswith('Prop_'))
total=sum(report['triangles'].values()); report['shell_triangles']=shelltris; report['total_triangles']=total
print('TRIANGLE_REPORT',json.dumps(report),flush=True)
assert shelltris<=8000,shelltris
assert total<=25000,total
# Validate a 1 m-wide continuous aisle with doors treated as open connectors.
walk=[]
for y in [(-3.6+i*.2) for i in range(37)]:
    for x in (-.5,0,.5):
        origin=Vector((x,y,.215))
        for ob in objects:
            if ob.name.startswith('Door_'): continue
            inv=ob.matrix_world.inverted(); local=inv@origin
            # Every object's rotation/scale has been applied; origin is the only offset.
            hit,loc,normal,idx=ob.ray_cast(local,Vector((0,0,1)),distance=1.85)
            assert not hit,('Walkway obstruction',ob.name,x,y,list(loc))
report['continuous_1m_aisle_ray_checks_pass']=True
# Export only intended meshes, never the cutaway, cameras, lights or planets.
bpy.ops.object.select_all(action='DESELECT')
for ob in objects+list(colcol.objects): ob.select_set(True)
bpy.context.view_layer.objects.active=objects[0]
bpy.ops.export_scene.fbx(filepath=os.path.join(OUT,'quarters_Sol.fbx'),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',bake_space_transform=True,mesh_smooth_type='OFF',add_leaf_bones=False,bake_anim=False)

def render(camera,filename,cutaway=False):
    for ob in objects: ob.hide_render=cutaway
    cut.hide_render=not cutaway; cutlight.hide_render=not cutaway
    planet.hide_render=cutaway or camera==ext
    sky.hide_render=cutaway or camera==ext
    stars.hide_render=cutaway or camera==ext
    scene.camera=camera; scene.render.filepath=os.path.join(OUT,filename)
    bpy.ops.render.render(write_still=True)
if RENDER:
    render(cam,'quarters_Sol_mockup_view.png')
    render(top,'quarters_Sol_topdown.png',True)
    render(ext,'quarters_Sol_exterior.png')
    render(close,'quarters_Sol_closeup.png')
for ob in objects: ob.hide_render=False
cut.hide_render=True; cut.hide_set(True); cutlight.hide_render=True; planet.hide_render=False; sky.hide_render=False; stars.hide_render=False
scene.camera=cam; scene.render.filepath=os.path.join(OUT,'quarters_Sol_mockup_view.png')
for ob in list(stage.objects)+list(colcol.objects): ob.hide_set(True)
scene.cursor.location=(0,0,0)
if '__file__' in globals(): bpy.data.texts.load(__file__)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'quarters_Sol.blend'))
with open(os.path.join(OUT,'validation_Sol.json'),'w') as f: json.dump(report,f,indent=2)
print('QUARTERS_SOL_COMPLETE',flush=True)
