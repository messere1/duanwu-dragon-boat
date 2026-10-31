"""Translate former village-edge trees clear of the expanded houses.
Keep local tree geometry, normals, UVs and all unrelated OBJ records unchanged.
"""
import bpy,ast,json,math,struct,shutil
from pathlib import Path
from mathutils import Vector,Matrix
from math import sin,cos,pi
ROOT=Path(__file__).resolve().parents[1];MODELS=ROOT/'models';PRE=ROOT/'previews'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
inventory=json.loads((MODELS/'inventory.json').read_text());assets={i['file'][:-4]:bpy.data.objects.get(i['file'][:-4]) for i in inventory}
_field_ground_bvh=None
for file,names in [('style_huizhou.py',{'hill_height'}),('style_panorama.py',{'river_center','surrounding_ground_height','panorama_surface','actual_field_ground','relocate_village_trees'})]:
    for n in ast.parse((ROOT/'tools'/file).read_text(encoding='utf-8')).body:
        if isinstance(n,ast.FunctionDef) and n.name in names:exec(compile(ast.Module(body=[n],type_ignores=[]),file,'exec'),globals())
changes=relocate_village_trees();assert len(changes)==14
bpy.context.view_layer.update();CV=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
deltas={name:CV.to_3x3()@(after-before) for name,(before,after) in changes.items()}
for name in deltas:deltas[name]=tuple(round(float(v),6) for v in deltas[name])
obj=MODELS/'scene_preview.obj';pending=MODELS/'scene_preview.tree-fix.obj';counts={name:0 for name in changes};active=None
with obj.open(encoding='utf-8') as src,pending.open('w',encoding='utf-8',newline='\n') as dst:
    for line in src:
        if line.startswith('o '):
            group=line[2:].strip();active=next((name for name in changes if group.startswith(name+'__')),None)
        if active and line.startswith('v '):
            old=tuple(map(float,line.split()[1:]));new=tuple(v+d for v,d in zip(old,deltas[active]))
            assert all(math.isfinite(v) for v in new);line='v %.6f %.6f %.6f\n'%new;counts[active]+=1
        dst.write(line)
assert all(counts.values()),counts
pending.replace(obj)
layout=json.loads((MODELS/'scene_layout.json').read_text(encoding='utf-8'))
for node in layout['nodes']:
    o=bpy.data.objects[node['name']]
    if o.name in changes or any(o.name.startswith(name+'__') for name in changes):
        node['local_matrix_zup']=[[round(float(v),6) for v in row] for row in o.matrix_local]
        node['world_matrix_yup']=[[round(float(v),6) for v in row] for row in CV@o.matrix_world@CV.inverted()]
(MODELS/'scene_layout.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2),encoding='utf-8')
glb=MODELS/'dragonboat_scene.glb'
with glb.open('rb') as f:
    magic,version,total=struct.unpack('<4sII',f.read(12));length,kind=struct.unpack('<I4s',f.read(8));data=json.loads(f.read(length))
updated=[]
for node in data['nodes']:
    name=node.get('name','')
    if name not in changes:continue
    transform=CV@bpy.data.objects[name].matrix_local@CV.inverted()
    for key in ('translation','rotation','scale'):node.pop(key,None)
    node['matrix']=[float(transform[r][c]) for c in range(4) for r in range(4)];updated.append(name)
assert set(updated)==set(changes)
payload=json.dumps(data,ensure_ascii=False,separators=(',',':')).encode('utf-8');payload+=b' '*((-len(payload))%4)
pending=glb.with_suffix('.tree-fix.glb')
with glb.open('rb') as src,pending.open('wb') as dst:
    src.seek(20+length);dst.write(struct.pack('<4sII',magic,version,total-length+len(payload)));dst.write(struct.pack('<I4s',len(payload),kind));dst.write(payload);shutil.copyfileobj(src,dst,1024*1024)
pending.replace(glb)
scene=bpy.context.scene;scene.cycles.device='CPU';bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
(MODELS/'panorama_tree_clearance.json').write_text(json.dumps({'status':'PASS','translated_roots':list(changes),'translated_vertices':counts,'checks':['Former village-edge trees relocated outside expanded houses','OBJ records changed only by uniform translations in named tree groups','GLB tree roots and Blender transforms updated consistently']},indent=2),encoding='utf-8')
print('TREE_CLEARANCE_FILES_PASS',json.dumps(counts),flush=True)
cam=scene.camera;camd=cam.data
exec((ROOT/'tools/configure_render_device.py').read_text(encoding='utf-8'),globals());configure_preview_device()
source=(ROOT/'tools/update_panorama_environment.py').read_text(encoding='utf-8')
for n in ast.parse(source).body:
    if isinstance(n,ast.FunctionDef) and n.name in ('shot','panorama','hero'):exec(compile(ast.Module(body=[n],type_ignores=[]),'update_panorama_environment.py','exec'),globals())
exec(source[source.index('panorama();hero();'):source.index("print('PANORAMA_ENVIRONMENT_COMPLETE'")],globals())
print('TREE_CLEARANCE_AND_PREVIEWS_COMPLETE',flush=True)
