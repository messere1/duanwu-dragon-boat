"""Verify the delivered town layout and actual open courtyard geometry."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from river_routes import river_center,half_width
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_models.blend'));bpy.context.view_layer.update()
world=bpy.data.objects['world_export'];types={'riverside_house','huizhou_tall_house','huizhou_tea_house','huizhou_courtyard'}
houses=[o for o in world.children if o.get('asset') in types];assert len(houses)>=33
for root in houses:
    ps=[o.matrix_world@Vector(p) for o in root.children_recursive if o.type=='MESH' for p in o.bound_box]
    distances=[p.y-river_center(p.x) for p in ps]
    ymin=min(distances);ymax=max(distances)
    assert all(d>half_width(p.x)+.15 for p,d in zip(ps,distances)) or all(d<-half_width(p.x)-.15 for p,d in zip(ps,distances)),(root.name,'building enters curved river corridor',ymin,ymax)
graph=bpy.context.evaluated_depsgraph_get();courtyards=[]
for root in houses:
    if root.get('asset')!='huizhou_courtyard':continue
    center=root.matrix_world.translation
    hit,point,normal,index,obj,matrix=bpy.context.scene.ray_cast(graph,center+Vector((0,0,10)),Vector((0,0,-1)),distance=12)
    assert hit and center.z-.1<point.z<center.z+.4,(root.name,'courtyard center covered or floor missing',point.z)
    courtyards.append({'name':root.name,'floor_hit_z':round(point.z,4)})
assert len(courtyards)>=6
assert len([o for o in world.children if o.get('asset')=='distant_tree'])>=32
assert len([o for o in world.children if o.get('asset')=='street_gutter'])==2
steps=[o for o in world.children_recursive if o.type=='MESH' and 'riverside_washing_step' in o.name]
assert steps
for o in steps:
    pts=[o.matrix_world@Vector(p) for p in o.bound_box]
    assert min(p.z for p in pts)<-.30,(o.name,'unsupported river stair')
    assert min(abs(p.y-river_center(p.x)) for p in pts)>3.2,(o.name,'stair enters boat lane')
result={'status':'PASS','houses':len(houses),'open_courtyards':courtyards,'supported_river_steps':len(steps),'checks':['All town buildings clear the river corridor','Courtyard sky openings verified by downward rays','Original woodland retained and extended','Two original street watercourses retained','River stairs have masonry below the water and clear the boat lanes']}
(ROOT/'models/huizhou_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('HUIZHOU_LAYOUT_PASS',json.dumps(result),flush=True)
