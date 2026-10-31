"""Add a distant ridge without recomputing the large accepted scene OBJ."""
import bpy,ast,sys,json
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];MODELS=ROOT/'models';PRE=ROOT/'previews';sys.path.insert(0,str(ROOT/'tools'))
from add_valley_closure import add_valley_closure
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
world=bpy.data.objects['world_export'];assert bpy.data.objects.get('far_river_valley_closure') is None,'Already finalized'
ridge=add_valley_closure(world);bpy.context.view_layer.update()
source=(ROOT/'tools/build_models.py').read_text(encoding='utf-8')
for n in ast.parse(source).body:
    if isinstance(n,ast.FunctionDef) and n.name in {'descendants','evaluated','export_obj','arr'}:exec(compile(ast.Module(body=[n],type_ignores=[]),'build_models.py','exec'),globals())
CV=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
inventory=json.loads((MODELS/'inventory.json').read_text());item=export_obj('panorama_valley_closure',ridge)
scene_item=next(i for i in inventory if i['file']=='scene_preview.obj');offset=scene_item['vertices']
with (MODELS/'scene_preview.obj').open('a',encoding='utf-8') as f:
    for line in (MODELS/item['file']).open(encoding='utf-8'):
        if line.startswith(('#','mtllib')):continue
        if line.startswith('f '):line='f '+' '.join('/'.join(str(int(i)+offset) for i in token.split('/')) for token in line.split()[1:])+'\n'
        f.write(line)
scene_item['vertices']+=item['vertices'];scene_item['triangles']+=item['triangles'];inventory.append(item)
(MODELS/'inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
layout=json.loads((MODELS/'scene_layout.json').read_text(encoding='utf-8'))
for o in descendants(ridge):layout['nodes'].append({'name':o.name,'parent':o.parent.name if o.parent and o.parent!=world else None,'asset':o.get('asset'),'type':o.type,'render_mode':None,'scene_mesh_deformed':False,'local_matrix_zup':[arr(r) for r in o.matrix_local],'world_matrix_yup':[arr(r) for r in CV@o.matrix_world@CV.inverted()]})
(MODELS/'scene_layout.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2),encoding='utf-8')
for o in list(bpy.context.selected_objects):o.select_set(False)
for o in descendants(world):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(MODELS/'dragonboat_scene.glb'),use_selection=True,export_format='GLB',export_apply=True)
exec((ROOT/'tools/fix_sky_glb.py').read_text(encoding='utf-8'),globals());ensure_unlit_sky(MODELS/'dragonboat_scene.glb')
for o in list(bpy.context.selected_objects):o.select_set(False)
bpy.context.preferences.filepaths.save_version=0;bpy.context.scene.cycles.device='CPU';bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
exec((ROOT/'tools/configure_render_device.py').read_text(encoding='utf-8'),globals());configure_preview_device()
scene=bpy.context.scene;scene.cycles.samples=12;scene.render.resolution_x=2560;scene.render.resolution_y=1280
cam=scene.camera;cam.data.type='PANO';cam.data.panorama_type='EQUIRECTANGULAR';cam.location=(0,0,6);cam.rotation_euler=Vector((1,0,0)).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(PRE/'15_environment_360.png');render_preview_frame()
print('RIVER_HORIZON_FINALIZED',item['triangles'],flush=True)
