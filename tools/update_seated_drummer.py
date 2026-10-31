"""Update the delivered editable assembly without rebuilding the bank geometry.
The canonical rebuild remains build_models.py + prepared_open_assets.blend.
"""
import bpy,ast,json,math,sys,shutil
from pathlib import Path
from mathutils import Vector,Matrix
from math import sin,cos,pi
ROOT=Path(__file__).resolve().parents[1];MODELS=ROOT/'models';PRE=ROOT/'previews'
source=(ROOT/'tools/build_models.py').read_text(encoding='utf-8')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
helpers={'finish','box','rod','mesh','empty','begin','parent_new','root_asset','descendants','clone','drummer_stool','evaluated','export_obj','camera','render','arr'}
for node in ast.parse(source).body:
    if isinstance(node,ast.FunctionDef) and node.name in helpers:exec(compile(ast.Module(body=[node],type_ignores=[]),str(ROOT/'tools/build_models.py'),'exec'),globals())
CV=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
worldroot=bpy.data.objects['world_export'];scene_roots=list(worldroot.children)
red=bpy.data.objects['dragon_boat_red'];jade=bpy.data.objects['dragon_boat_jade']
scene=bpy.context.scene;cam=scene.camera;camd=cam.data
with bpy.data.libraries.load(str(ROOT/'external_assets/prepared_open_assets.blend'),link=False) as (src,dst):
    dst.objects=[n for n in src.objects if n.startswith('open_human_drummer__')]
posed=[o for o in dst.objects if o];assert len(posed)==6
M={m.name:m for m in bpy.data.materials if m.use_nodes}
assets={x['file'][:-4]:bpy.data.objects.get(x['file'][:-4]) for x in json.loads((MODELS/'inventory.json').read_text())}
for name in ('drummer_red','drummer_jade','red_drummer','jade_drummer'):
    root=bpy.data.objects[name];prototype=name.startswith('drummer_')
    for o in list(root.children_recursive):bpy.data.objects.remove(o,do_unlink=True)
    for src in posed:
        o=src.copy();bpy.context.collection.objects.link(o);o.parent=root;o.matrix_basis=Matrix.Identity(4)
        o.name=name+'__'+src.name;o.hide_render=prototype;o.hide_set(prototype)
    if not prototype:root.location=(4.25,0,1.15);root.rotation_euler=(0,0,pi)
for name in ('red_drummer_stool','jade_drummer_stool','drummer_stool'):
    root=bpy.data.objects.get(name)
    if root:
        for o in reversed(descendants(root)):bpy.data.objects.remove(o,do_unlink=True)
stool=root_asset('drummer_stool',drummer_stool)
for o in descendants(stool):o.hide_render=True;o.hide_set(True)
for team,b in (('red',red),('jade',jade)):
    bpy.data.objects[team+'_drum'].location=(3.35,0,1.00)
    s=clone('drummer_stool',team+'_drummer_stool',(4.25,0,.918),parent=b)
    for o in descendants(s):o.hide_render=False;o.hide_set(False)
    for o in list(b.children_recursive):
        if o.name.startswith(team+'_drumstick'):bpy.data.objects.remove(o,do_unlink=True)
    for side in (-1,1):
        o=rod(team+'_drumstick',(3.89,side*.22,1.77),(3.35,side*.12,1.67),.018,'wood');o.parent=b
for m in bpy.data.meshes:
    if m.uv_layers.active:continue
    uv=m.uv_layers.new(name='UVMap')
    for p in m.polygons:
        a=max(range(3),key=lambda a:abs(p.normal[a]))
        for li in p.loop_indices:
            co=m.vertices[m.loops[li].vertex_index].co;uv.data[li].uv=(co[(a+1)%3],co[(a+2)%3])
bpy.context.view_layer.update()
# Validate actual rig-baked geometry rather than only the root orientation.
audit=[]
for team in ('red','jade'):
    root=bpy.data.objects[team+'_drummer'];assert (root.rotation_euler.to_matrix()@Vector((1,0,0))).x<-.999
    vs=[root.matrix_local@o.matrix_local@v.co for o in root.children if o.type=='MESH' for v in o.data.vertices]
    assert 2.00<max(v.z for v in vs)<2.2
    assert .90<min(v.z for v in vs)<.99
    audit.append({'team':team,'facing':'stern (-X)','pose':'seated','foot_min_z':min(v.z for v in vs),'head_max_z':max(v.z for v in vs),'stool_top_z':1.248,'drum_top_z':1.66})
print('SEATED_DRUMMER_ASSEMBLY_PASS',json.dumps(audit),flush=True)
def studio():
    for r in scene_roots:
        if r!=red:
            for o in descendants(r):o.hide_render=True
    red.location=(0,0,0);bpy.context.view_layer.update()
    return box('studio_floor',(0,0,-.65),(200,200,.12),'limewash',0)
if '--preview-only' in sys.argv:
    studio();render('10_seated_drummer',(2,-5,3.3),(3.8,0,1.3),4)
    raise SystemExit(0)
changed=('drummer_red','drummer_jade','drummer_stool','dragon_boat_red','dragon_boat_jade','scene_preview')
inventory=json.loads((MODELS/'inventory.json').read_text())
for name in changed:
    root=worldroot if name=='scene_preview' else bpy.data.objects[name]
    item=export_obj(name,root);inventory=[i for i in inventory if i['file']!=item['file']];inventory.append(item)
(MODELS/'inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
exec((ROOT/'tools/restore_texture_paths.py').read_text(encoding='utf-8'),globals());restore_material_image_paths()
exec(source[source.index('mtl=[]'):source.index('# Scene graph contains')],globals())
nodes=[]
for r in scene_roots:
    for o in descendants(r):nodes.append({'name':o.name,'parent':o.parent.name if o.parent and o.parent!=worldroot else None,'asset':o.get('asset'),'type':o.type,'local_matrix_zup':[arr(row) for row in o.matrix_local],'world_matrix_yup':[arr(row) for row in CV@o.matrix_world@CV.inverted()]})
(MODELS/'scene_layout.json').write_text(json.dumps({'units':'metres','obj_axes':'Y up, +X forward','scene_internal_axes':'Z up','nodes':nodes},ensure_ascii=False,indent=2),encoding='utf-8')
(MODELS/'drummer_validation.json').write_text(json.dumps({'status':'PASS','drummers':audit},indent=2),encoding='utf-8')
for im in bpy.data.images:
    if im.source=='FILE' and im.size[0]>0:im.pack()
for o in list(bpy.context.selected_objects):o.select_set(False)
for o in descendants(worldroot):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(MODELS/'dragonboat_scene.glb'),use_selection=True,export_format='GLB',export_apply=True)
exec((ROOT/'tools/fix_sky_glb.py').read_text(encoding='utf-8'),globals());ensure_unlit_sky(MODELS/'dragonboat_scene.glb')
for o in list(bpy.context.selected_objects):o.select_set(False)
camera((34,-43,34),(0,1,0),58)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
render('01_scene_overview',(31,-41,31),(0,1,0),58)
render('06_riverside_architecture',(-11,-11,10),(-7,9.3,1.9),22)
floor=studio()
render('02_dragon_boat',(12,-17,11),(0,0,1),16.8)
render('03_dragon_head',(10,-6,4.5),(5.45,0,1.8),4.6)
render('04_boat_side',(1,-20,6),(0,0,1.1),15.5)
# The exact close view was already verified in --preview-only mode.
for a,b in [('02_dragon_boat.png','design_01_boat.png'),('03_dragon_head.png','design_02_bow.png')]:shutil.copy2(PRE/a,PRE/b)
for o in descendants(red):
    if any(k in o.name for k in ('rower','drummer_red','red_drummer__','helmsman','paddle','steering_oar','drumstick')):o.hide_render=True
camera((6,-10,13),(0,0,.7),14.5);scene.render.filepath=str(PRE/'design_03_structure.png');bpy.ops.render.render(write_still=True)
for o in descendants(red):o.hide_render=True
exec(source[source.index('grid=['):source.index("print('MODELING_COMPLETE'")],globals())
print('SEATED_DRUMMER_UPDATE_COMPLETE',flush=True)
