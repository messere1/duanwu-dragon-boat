"""Extend the delivered town into a complete 360-degree modeled environment."""
import bpy,ast,json,math,random,sys,shutil
from pathlib import Path
from mathutils import Vector,Matrix
from math import sin,cos,pi
ROOT=Path(__file__).resolve().parents[1];MODELS=ROOT/'models';PRE=ROOT/'previews'
source=(ROOT/'tools/build_models.py').read_text(encoding='utf-8')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
helpers={'material','finish','box','rod','mesh','sphere','tube','empty','begin','parent_new','root_asset','descendants','clone','place','evaluated','export_obj','arr'}
for n in ast.parse(source).body:
    if isinstance(n,ast.FunctionDef) and n.name in helpers:exec(compile(ast.Module(body=[n],type_ignores=[]),'build_models.py','exec'),globals())
for file,names in [('style_riverside.py',{'_rbox'}),('style_huizhou.py',{'hill_height'})]:
    for n in ast.parse((ROOT/'tools'/file).read_text(encoding='utf-8')).body:
        if isinstance(n,ast.FunctionDef) and n.name in names:exec(compile(ast.Module(body=[n],type_ignores=[]),file,'exec'),globals())
M={m.name:m for m in bpy.data.materials if m.use_nodes};_new_material=material
def material(name,color,texture=None,metal=0,rough=.5):return M[name] if name in M else _new_material(name,color,texture,metal,rough)
inventory=json.loads((MODELS/'inventory.json').read_text());assets={i['file'][:-4]:bpy.data.objects.get(i['file'][:-4]) for i in inventory}
worldroot=bpy.data.objects['world_export']
for root in list(worldroot.children):
    if root.name.startswith(('pano_','panorama_')) or root.get('asset')=='river_surface':
        for o in reversed(descendants(root)):bpy.data.objects.remove(o,do_unlink=True)
exec((ROOT/'tools/style_panorama.py').read_text(encoding='utf-8'),globals())
changed=['river_surface','panorama_terrain','panorama_farmland','panorama_streets','panorama_sky']
for name in changed:
    root=bpy.data.objects.get(name)
    if root:
        for o in reversed(descendants(root)):bpy.data.objects.remove(o,do_unlink=True)
root_asset('river_surface',panorama_water);install_panorama_assets()
for name in changed:
    for o in descendants(assets[name]):o.hide_render=True;o.hide_set(True)
scene_roots=list(worldroot.children);place('river_surface','river');layout_panorama_extensions()
for root in scene_roots:root.parent=worldroot
bpy.context.view_layer.update()
for m in bpy.data.meshes:
    if m.uv_layers.active:continue
    uv=m.uv_layers.new(name='UVMap')
    for p in m.polygons:
        axis=max(range(3),key=lambda a:abs(p.normal[a]))
        for li in p.loop_indices:
            co=m.vertices[m.loops[li].vertex_index].co;uv.data[li].uv=(co[(axis+1)%3]/2,co[(axis+2)%3]/2)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.use_denoising=True;scene.cycles.samples=12
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.film_transparent=False
cam=scene.camera;camd=cam.data;camd.clip_end=2000
exec((ROOT/'tools/configure_render_device.py').read_text(encoding='utf-8'),globals())
def shot(name,loc,target,lens=35):
    scene.render.resolution_x=1600;scene.render.resolution_y=1000;camd.type='PERSP';camd.lens=lens
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(PRE/(name+'.png'));render_preview_frame()
def panorama():
    scene.render.resolution_x=2560;scene.render.resolution_y=1280;camd.type='PANO';camd.panorama_type='EQUIRECTANGULAR'
    cam.location=(0,0,6);cam.rotation_euler=Vector((1,0,0)).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(PRE/'15_environment_360.png');render_preview_frame()
def hero():shot('11_huizhou_overview',(32,-44,22),(0,4,3),35)
if '--preview-only' in sys.argv:
    configure_preview_device();scene.cycles.samples=8;panorama()
    if '--panorama-only' not in sys.argv:hero()
    print('PANORAMA_PREVIEW_READY',flush=True);raise SystemExit(0)
CV=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
for name in changed+['scene_preview']:
    item=export_obj(name,worldroot if name=='scene_preview' else assets[name]);inventory=[i for i in inventory if i['file']!=item['file']];inventory.append(item)
(MODELS/'inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
exec((ROOT/'tools/restore_texture_paths.py').read_text(encoding='utf-8'),globals());restore_material_image_paths()
exec(source[source.index('mtl=[]'):source.index('# Scene graph contains')],globals())
nodes=[]
for root in scene_roots:
    for o in descendants(root):nodes.append({'name':o.name,'parent':o.parent.name if o.parent and o.parent!=worldroot else None,'asset':o.get('asset'),'type':o.type,'render_mode':o.get('render_mode'),'local_matrix_zup':[arr(row) for row in o.matrix_local],'world_matrix_yup':[arr(row) for row in CV@o.matrix_world@CV.inverted()]})
(MODELS/'scene_layout.json').write_text(json.dumps({'units':'metres','obj_axes':'Y up, +X forward','scene_internal_axes':'Z up','nodes':nodes},ensure_ascii=False,indent=2),encoding='utf-8')
for im in bpy.data.images:
    if im.source=='FILE' and im.size[0]>0:im.pack()
for o in list(bpy.context.selected_objects):o.select_set(False)
for o in descendants(worldroot):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(MODELS/'dragonboat_scene.glb'),use_selection=True,export_format='GLB',export_apply=True)
exec((ROOT/'tools/fix_sky_glb.py').read_text(encoding='utf-8'),globals());ensure_unlit_sky(MODELS/'dragonboat_scene.glb')
for o in list(bpy.context.selected_objects):o.select_set(False)
camd.type='PERSP';camd.lens=35;cam.location=(32,-44,22);cam.rotation_euler=(Vector((0,4,3))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.context.preferences.filepaths.save_version=0;scene.cycles.device='CPU';bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
configure_preview_device()
panorama();hero();shutil.copy2(PRE/'11_huizhou_overview.png',PRE/'01_scene_overview.png')
for name,loc,target in [('16_view_east',(-8,0,9),(70,0,8)),('17_view_south',(0,1,10),(0,-75,10)),('18_view_west',(8,0,9),(-70,0,8)),('19_view_north',(0,-1,10),(0,75,10))]:shot(name,loc,target,32)
shot('20_panorama_aerial',(115,-145,112),(0,0,2),35)
shot('12_old_town_street',(-22,7.85,1.75),(1,8.4,2.6),32);shutil.copy2(PRE/'12_old_town_street.png',PRE/'06_riverside_architecture.png')
for name,loc,target,lens in [('07_finish_and_bridge',(9,-18,12),(19,0,2.2),45),('08_festival_stall',(-6,-3,4.5),(-10,-9.1,1.2),45),('09_mooring_dock',(-5,1,6),(-12,-5.3,.7),45),('14_weathered_quay',(2,-1,3.3),(4,-6.6,.55),40)]:shot(name,loc,target,lens)
print('PANORAMA_ENVIRONMENT_COMPLETE',json.dumps({'obj_files':len(inventory),'nodes':len(nodes)}),flush=True)
