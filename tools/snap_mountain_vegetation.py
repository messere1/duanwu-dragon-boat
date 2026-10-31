"""Snap rigid vegetation to the actual refined triangles and audit house support."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];M=R/'models';B=R.parent/'_work/dragonboat/before_mountain_refinement'
manifest=json.loads((M/'mountain_patch_manifest.json').read_text());names=manifest['terrain_objects']
def ground():
 vs=[];fs=[]
 for name in names:
  o=bpy.data.objects[name];start=len(vs);vs.extend(o.matrix_world@v.co for v in o.data.vertices);fs.extend(tuple(start+i for i in p.vertices) for p in o.data.polygons)
 return BVHTree.FromPolygons(vs,fs)
def height(bvh,x,y):
 p,_,_,_=bvh.ray_cast(Vector((x,y,240)),Vector((0,0,-1)),600)
 return None if p is None else p.z
bpy.ops.wm.open_mainfile(filepath=str(B/'dragonboat_realism.blend'));bpy.context.view_layer.update();old=ground();world=bpy.data.objects['world_export']
trees=[(o.name,o.matrix_world.translation.copy(),[c.name.replace(' ','_') for c in o.children_recursive if c.type=='MESH']) for o in world.children if o.get('asset') in {'tree','distant_tree'}]
parents=[bpy.data.objects['rural_3d_tree_'+str(i)].location.copy() for i in range(216)]
houses=[(o.name,[list(row) for row in o.matrix_world],o.matrix_world.translation.copy()) for o in world.children if o.get('asset') in {'riverside_house','huizhou_tall_house','huizhou_tea_house','huizhou_courtyard'}]
points=[]
for name,_,p in houses:
 for dx,dy in ((0,0),(-1.4,-1.4),(-1.4,1.4),(1.4,-1.4),(1.4,1.4)):
  z=height(old,p.x+dx,p.y+dy)
  if z is not None:points.append((name,p.x+dx,p.y+dy,z))
bpy.ops.wm.open_mainfile(filepath=str(R/'dragonboat_realism.blend'));bpy.context.view_layer.update();new=ground()
def delta(x,y):
 a=height(old,x,y);b=height(new,x,y)
 assert a is not None and b is not None,(x,y,'ground coverage')
 return b-a
shifts={};moved=0
for name,p,children in trees:
 d=delta(p.x,p.y);bpy.data.objects[name].location.z=p.z+d
 if abs(d)>1e-7:
  moved+=1
  for n in children:shifts[n]=d
rows=[]
for i,line in enumerate((B/'vegetation_instances.txt').read_text().splitlines()):
 row=list(map(float,line.split()));d=delta(row[0],-row[2]);row[1]+=d;rows.append(row);bpy.data.objects['rural_3d_tree_'+str(i)].location.z=parents[i].z+d
(M/'vegetation_instances.txt').write_text('\n'.join(' '.join(f'{v:.7f}' for v in row) for row in rows)+'\n',encoding='ascii')
manifest['rigid_vertical_shifts']=shifts;(M/'mountain_patch_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
error=0.
for name,mat,p in houses:
 current=bpy.data.objects[name].matrix_world
 error=max(error,max(abs(current[i][j]-mat[i][j]) for i in range(4) for j in range(4)))
support=[(name,abs(height(new,x,y)-z)) for name,x,y,z in points];maximum=max(d for _,d in support)
report=dict(status='PASS' if error<1e-6 and maximum<.06 else 'FAIL',houses_checked=len(houses),house_matrix_max_error=error,ground_support_samples=len(points),maximum_ground_support_change_m=maximum,rigid_trees_snapped=moved,shared_trees_snapped=len(rows),method='Old/new triangle BVH ground difference preserves original trunk planting depth')
(R/'results/mountain_support_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('MOUNTAIN_SUPPORT',json.dumps(report),flush=True)
assert report['status']=='PASS',sorted(support,key=lambda p:-p[1])[:10]
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(R/'dragonboat_realism.blend'))
