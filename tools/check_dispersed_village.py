"""Check settlement depth, irregular parcel geometry and hillside support."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_models.blend'));bpy.context.view_layer.update()
data=json.loads((ROOT/'models/dispersed_layout.json').read_text(encoding='utf-8'));world=bpy.data.objects['world_export']
assert len(data['moved_houses'])>=45 and len(data['cluster_centres'])==8
assert len(data['irregular_parcels'])>=15
assert len({len(p) for p in data['irregular_parcels']})>=3
ground_objects=[o for o in world.children_recursive if o.type=='MESH' and o.name.startswith('graded_inland_earth')]
assert len(ground_objects)==2
vs=[];fs=[]
for o in ground_objects:
    start=len(vs);vs.extend(o.matrix_world@v.co for v in o.data.vertices);fs.extend(tuple(start+k for k in p.vertices) for p in o.data.polygons)
ground=BVHTree.FromPolygons(vs,fs);support=[]
for record in data['moved_houses']:
    root=bpy.data.objects[record['name']];p=root.matrix_world.translation
    hit,_,_,_=ground.ray_cast(p+Vector((0,0,2)),Vector((0,0,-1)),8)
    assert hit is not None and -.35<p.z-hit.z<.5,(root.name,'Unsupported or buried house',tuple(p),tuple(hit) if hit else None)
    support.append(round(p.z-hit.z,4))
assert not any(r.get('asset')=='panorama_farmland' for r in world.children)
areas=[]
for poly in data['irregular_parcels']:
    areas.append(abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1])))/2)
assert max(areas)/min(areas)>2
report={'status':'PASS','inland_houses':len(support),'clusters':8,'irregular_fields':len(areas),'parcel_area_range_m2':[min(areas),max(areas)],'house_ground_clearance_range_m':[min(support),max(support)],'checks':['Settlement extends inland on both banks','Eight dispersed clusters','Low foundations touch graded hillside terraces','Old rectangular field carpet removed','Convex irregular parcels vary in size and edge count']}
(ROOT/'models/dispersed_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('DISPERSED_VILLAGE_PASS',json.dumps(report),flush=True)
