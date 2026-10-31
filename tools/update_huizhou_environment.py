"""Replace the environment while preserving the approved boat assemblies."""
import bpy,ast,json,math,random,sys,shutil
from pathlib import Path
from mathutils import Vector,Matrix
from math import sin,cos,pi
ROOT=Path(__file__).resolve().parents[1];MODELS=ROOT/'models';PRE=ROOT/'previews'
source=(ROOT/'tools/build_models.py').read_text(encoding='utf-8')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
helpers={'material','finish','box','rod','mesh','sphere','tube','empty','begin','parent_new','root_asset','descendants','clone','place','plaque_quad','evaluated','export_obj','arr'}
for n in ast.parse(source).body:
    if isinstance(n,ast.FunctionDef) and n.name in helpers:exec(compile(ast.Module(body=[n],type_ignores=[]),str(ROOT/'tools/build_models.py'),'exec'),globals())
# The riverside helpers reuse existing materials on an incremental update.
M={m.name:m for m in bpy.data.materials if m.use_nodes};_new_material=material
for n in ast.parse((ROOT/'tools/style_traditional.py').read_text(encoding='utf-8')).body:
    if isinstance(n,ast.FunctionDef) and n.name=='bent':exec(compile(ast.Module(body=[n],type_ignores=[]),'style_traditional.py','exec'),globals())
def material(name,color,texture=None,metal=0,rough=.5):
    return M[name] if name in M else _new_material(name,color,texture,metal,rough)
exec((ROOT/'tools/style_riverside.py').read_text(encoding='utf-8'),globals())
exec((ROOT/'tools/style_huizhou.py').read_text(encoding='utf-8'),globals())
inventory=json.loads((MODELS/'inventory.json').read_text())
assets={i['file'][:-4]:bpy.data.objects.get(i['file'][:-4]) for i in inventory}
worldroot=bpy.data.objects['world_export'];red=bpy.data.objects['dragon_boat_red'];jade=bpy.data.objects['dragon_boat_jade']
for root in list(worldroot.children):
    if root not in (red,jade):
        for o in reversed(descendants(root)):bpy.data.objects.remove(o,do_unlink=True)
changed=['riverside_house','quay_segment','bank_ground','river_surface','huizhou_tall_house','huizhou_tea_house','huizhou_courtyard','household_props','laundry_rack','street_gutter','distant_hills','distant_tree','quay_weathered_b']
for name in changed:
    root=bpy.data.objects.get(name)
    if root:
        for o in reversed(descendants(root)):bpy.data.objects.remove(o,do_unlink=True)
root_asset('riverside_house',house);root_asset('quay_segment',quay);root_asset('bank_ground',bank_ground);root_asset('river_surface',water)
install_huizhou_assets()
for name in changed:
    for o in descendants(assets[name]):o.hide_render=True;o.hide_set(True)
scene_roots=[red,jade];layout_huizhou()
for root in scene_roots:root.parent=worldroot
bpy.context.view_layer.update()
for m in bpy.data.meshes:
    if m.uv_layers.active:continue
    uv=m.uv_layers.new(name='UVMap')
    for p in m.polygons:
        axis=max(range(3),key=lambda a:abs(p.normal[a]))
        for li in p.loop_indices:
            co=m.vertices[m.loops[li].vertex_index].co;uv.data[li].uv=(co[(axis+1)%3],co[(axis+2)%3])
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
for l in bpy.data.lights:
    if l.type=='SUN':l.energy=1.1;l.angle=.25
    elif l.type=='AREA':l.size=max(12,l.size)
for n in scene.world.node_tree.nodes:
    if n.type=='BACKGROUND' and not n.inputs['Color'].links:n.inputs['Color'].default_value=(.43,.48,.48,1)
cam=scene.camera;camd=cam.data
def shot(name,loc,target,lens=40,ortho=None):
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    camd.type='ORTHO' if ortho else 'PERSP'
    if ortho:camd.ortho_scale=ortho
    else:camd.lens=lens
    scene.render.filepath=str(PRE/(name+'.png'));bpy.ops.render.render(write_still=True)
def preview():
    shot('11_huizhou_overview',(32,-44,22),(0,4,3),35)
    shot('12_old_town_street',(-22,7.85,1.75),(1,8.4,2.6),32)
if '--preview-only' in sys.argv:
    scene.cycles.samples=12
    if '--overview-only' in sys.argv:shot('11_huizhou_overview',(32,-44,22),(0,4,3),35)
    else:preview()
    print('HUIZHOU_PREVIEW_READY',flush=True);raise SystemExit(0)
CV=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
for name in changed+['scene_preview']:
    item=export_obj(name,worldroot if name=='scene_preview' else assets[name])
    inventory=[i for i in inventory if i['file']!=item['file']];inventory.append(item)
(MODELS/'inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
exec((ROOT/'tools/restore_texture_paths.py').read_text(encoding='utf-8'),globals());restore_material_image_paths()
exec(source[source.index('mtl=[]'):source.index('# Scene graph contains')],globals())
nodes=[]
for root in scene_roots:
    for o in descendants(root):nodes.append({'name':o.name,'parent':o.parent.name if o.parent and o.parent!=worldroot else None,'asset':o.get('asset'),'type':o.type,'local_matrix_zup':[arr(row) for row in o.matrix_local],'world_matrix_yup':[arr(row) for row in CV@o.matrix_world@CV.inverted()]})
(MODELS/'scene_layout.json').write_text(json.dumps({'units':'metres','obj_axes':'Y up, +X forward','scene_internal_axes':'Z up','nodes':nodes},ensure_ascii=False,indent=2),encoding='utf-8')
for im in bpy.data.images:
    if im.source=='FILE' and im.size[0]>0:im.pack()
for o in list(bpy.context.selected_objects):o.select_set(False)
for o in descendants(worldroot):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(MODELS/'dragonboat_scene.glb'),use_selection=True,export_format='GLB',export_apply=True)
for o in list(bpy.context.selected_objects):o.select_set(False)
cam.location=(32,-44,22);cam.rotation_euler=(Vector((0,4,3))-cam.location).to_track_quat('-Z','Y').to_euler();camd.type='PERSP';camd.lens=35
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
preview();shutil.copy2(PRE/'11_huizhou_overview.png',PRE/'01_scene_overview.png');shutil.copy2(PRE/'12_old_town_street.png',PRE/'06_riverside_architecture.png')
shot('13_huizhou_courtyard',(-13,13.3,10),(-14.4,16.25,1.5),42)
shot('14_weathered_quay',(2,-1,3.3),(4,-6.6,.55),40)
shot('07_finish_and_bridge',(9,-18,12),(19,0,2.2),45)
shot('08_festival_stall',(-6,-3,4.5),(-10,-9.1,1.2),45)
shot('09_mooring_dock',(-5,1,6),(-12,-5.3,.7),45)
for root in scene_roots:
    for o in descendants(root):o.hide_render=True
_rbox('library_floor',(0,0,-.65),(220,220,.10),'limewash',0)
grid=['riverside_house','huizhou_tall_house','huizhou_tea_house','huizhou_courtyard','quay_segment','household_props','laundry_rack','pavilion','mooring_dock']
for i,name in enumerate(grid):
    r=clone(name,'display_'+name,((i%3)*8,-(i//3)*8,0))
    for o in descendants(r):o.hide_render=False;o.hide_set(False)
shot('05_asset_library',(30,-35,30),(8,-8,1.7),ortho=34)
print('HUIZHOU_ENVIRONMENT_COMPLETE',json.dumps({'assets':len(inventory)-3,'obj_files':len(inventory),'nodes':len(nodes)}),flush=True)
