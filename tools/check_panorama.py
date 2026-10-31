"""Ray coverage audit of the saved panorama environment, not only one camera."""
import bpy,json,math,struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_models.blend'));bpy.context.view_layer.update()
scene=bpy.context.scene;graph=bpy.context.evaluated_depsgraph_get();world=bpy.data.objects['world_export']
assert any(o.get('asset')=='panorama_sky' for o in world.children)
ground_tests=0;sky_tests=0;misses=[]
for origin in (Vector((0,0,6)),Vector((0,0,18)),Vector((30,-20,12)),Vector((-30,20,12))):
    for angle in range(0,360,5):
        a=math.radians(angle)
        for pitch in (-15,-5,0):
            p=math.radians(pitch);direction=Vector((math.cos(a)*math.cos(p),math.sin(a)*math.cos(p),math.sin(p)))
            hit,point,normal,index,obj,matrix=scene.ray_cast(graph,origin,direction,distance=600)
            ground_tests+=1
            if not hit:misses.append({'origin':list(origin),'angle':angle,'pitch':pitch})
        for pitch in (20,45,80):
            p=math.radians(pitch);direction=Vector((math.cos(a)*math.cos(p),math.sin(a)*math.cos(p),math.sin(p)))
            hit,point,normal,index,obj,matrix=scene.ray_cast(graph,origin,direction,distance=1000)
            sky_tests+=1
            if not hit:misses.append({'origin':list(origin),'angle':angle,'pitch':pitch})
assert not misses,('Panorama uncovered directions',misses[:10])
with (ROOT/'models/dragonboat_scene.glb').open('rb') as f:
    magic,version,total=struct.unpack('<4sII',f.read(12));length,kind=struct.unpack('<I4s',f.read(8));data=json.loads(f.read(length))
sky_mats=[m for m in data.get('materials',[]) if m.get('name','').startswith('panorama_sky')]
assert sky_mats and all('KHR_materials_unlit' in m.get('extensions',{}) for m in sky_mats),'Sky material must stay unlit in GLB'
houses=[o for o in world.children if o.get('asset') in ('riverside_house','huizhou_tall_house','huizhou_tea_house','huizhou_courtyard')]
report={'status':'PASS','houses':len(houses),'ground_and_horizon_rays':ground_tests,'upper_hemisphere_rays':sky_tests,'uncovered_directions':0,'audit_positions':[list(p) for p in (Vector((0,0,6)),Vector((0,0,18)),Vector((30,-20,12)),Vector((-30,20,12)))],'camera_clip_end':scene.camera.data.clip_end,'sky_material':'KHR_materials_unlit'}
(ROOT/'models/panorama_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('PANORAMA_COVERAGE_PASS',json.dumps(report),flush=True)
