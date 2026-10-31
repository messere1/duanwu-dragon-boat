"""Replace only three scene mesh groups, keeping all other OBJ indices stable."""
import bpy,ast,json,sys
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];MODELS=ROOT/'models';PRE=ROOT/'previews';sys.path.insert(0,str(ROOT/'tools'))
from make_natural_banks import make_natural_banks
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
world=bpy.data.objects['world_export'];assert not bpy.data.objects.get('eroded_riverbank_faces')
changed,bank=make_natural_banks(world);bpy.context.view_layer.update()
source=(ROOT/'tools/build_models.py').read_text(encoding='utf-8')
for n in ast.parse(source).body:
    if isinstance(n,ast.FunctionDef) and n.name in {'descendants','evaluated','export_obj','arr'}:exec(compile(ast.Module(body=[n],type_ignores=[]),'build_models.py','exec'),globals())
CV=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));inventory=json.loads((MODELS/'inventory.json').read_text())
temporary=bpy.data.objects.new('bank_replacement_export',None);bpy.context.collection.objects.link(temporary)
parents={o:o.parent for o in changed}
for o in changed:o.parent=temporary
bank_parent=bank.parent;bank.parent=temporary
replacement=export_obj('bank_replacement_groups',temporary)
for o,p in parents.items():o.parent=p
bank.parent=bank_parent;bpy.data.objects.remove(temporary,do_unlink=True);bpy.context.view_layer.update()
scene=next(i for i in inventory if i['file']=='scene_preview.obj');offset=scene['vertices'];names={o.name.replace(' ','_') for o in changed};names.add('continuous_solid_eroded_shore')
p=MODELS/'scene_preview.obj';tmp=p.with_suffix('.banks.tmp');remove=False;removed=0
with p.open(encoding='utf-8') as src,tmp.open('w',encoding='utf-8',newline='\n') as out:
    for line in src:
        if line.startswith('o '):remove=line[2:].strip() in names
        if remove and line.startswith(('o ','usemtl ','f ')):
            if line.startswith('f '):removed+=1
            continue
        out.write(line)
    for line in (MODELS/'bank_replacement_groups.obj').open(encoding='utf-8'):
        if line.startswith(('#','mtllib')):continue
        if line.startswith('f '):line='f '+' '.join('/'.join(str(int(i)+offset) for i in token.split('/')) for token in line.split()[1:])+'\n'
        out.write(line)
tmp.replace(p);scene['vertices']+=replacement['vertices'];scene['triangles']+=replacement['triangles']-removed
water=next(r for r in world.children if r.get('asset')=='river_surface')
for name,root in [('river_surface',water),('eroded_riverbank_faces',bank)]:
    item=export_obj(name,root);inventory=[i for i in inventory if i['file']!=item['file']];inventory.append(item)
(MODELS/'inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
# The temporary group file is retained as a small independently checkable patch.
inventory.append(replacement);(MODELS/'inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
layout=json.loads((MODELS/'scene_layout.json').read_text(encoding='utf-8'))
for o in descendants(bank):layout['nodes'].append({'name':o.name,'parent':o.parent.name if o.parent and o.parent!=world else None,'asset':o.get('asset'),'type':o.type,'render_mode':None,'local_matrix_zup':[arr(r) for r in o.matrix_local],'world_matrix_yup':[arr(r) for r in CV@o.matrix_world@CV.inverted()]})
(MODELS/'scene_layout.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2),encoding='utf-8')
for o in list(bpy.context.selected_objects):o.select_set(False)
for o in descendants(world):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(MODELS/'dragonboat_scene.glb'),use_selection=True,export_format='GLB',export_apply=True)
exec((ROOT/'tools/fix_sky_glb.py').read_text(encoding='utf-8'),globals());ensure_unlit_sky(MODELS/'dragonboat_scene.glb')
for o in list(bpy.context.selected_objects):o.select_set(False)
bpy.context.scene.cycles.device='CPU';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
exec((ROOT/'tools/configure_render_device.py').read_text(encoding='utf-8'),globals());configure_preview_device()
scene=bpy.context.scene;cam=scene.camera;scene.cycles.samples=12
for name,loc,target in [('21_bending_river_aerial',(125,-110,100),(65,12,0)),('22_natural_riverbank',(111,9,3.8),(126,19,0)),('23_downstream_drone',(50,-19,15),(80,20,1)),('20_panorama_aerial',(115,-145,112),(25,8,2))]:
    scene.render.resolution_x=1600;scene.render.resolution_y=1000;cam.data.type='PERSP';cam.data.lens=35;cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(PRE/(name+'.png'));render_preview_frame()
scene.render.resolution_x=2560;scene.render.resolution_y=1280;cam.data.type='PANO';cam.data.panorama_type='EQUIRECTANGULAR';cam.location=(0,0,6);cam.rotation_euler=Vector((1,0,0)).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(PRE/'15_environment_360.png');render_preview_frame()
print('NATURAL_BANKS_COMPLETE',removed,replacement['triangles'],flush=True)
