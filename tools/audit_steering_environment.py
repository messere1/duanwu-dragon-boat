"""Sweep the real steering-oar mesh through both exact C++ race trajectories."""
import bpy,csv,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));from steering_motion import steering_frame
bpy.ops.wm.open_mainfile(filepath=str(R/'dragonboat_realism.blend'));bpy.context.view_layer.update()
assets={'mooring_dock','arch_bridge','quay_segment','quay_weathered_b','quay_access','street_gutter','natural_riverbed','eroded_riverbank_faces','bank_ground'}
vs=[];fs=[]
for root in bpy.data.objects['world_export'].children:
 if root.get('asset') not in assets:continue
 for o in [root,*root.children_recursive]:
  if o.type!='MESH':continue
  start=len(vs);vs.extend(o.matrix_world@v.co for v in o.data.vertices);fs.extend(tuple(start+i for i in p.vertices) for p in o.data.polygons)
environment=BVHTree.FromPolygons(vs,fs);del vs,fs
v=[];f=[]
for line in (R/'models/steering_oar.obj').open(encoding='utf8'):
 if line.startswith('v '):v.append(Vector(tuple(map(float,line.split()[1:]))))
 elif line.startswith('f '):
  ids=[int(t.split('/')[0])-1 for t in line.split()[1:]]
  for i in range(1,len(ids)-1):f.append((ids[0],ids[i],ids[i+1]))
rows=list(csv.DictReader((R/'results/steering_world_samples.csv').open()));contacts=[]
for k,row in enumerate(rows):
 row={n:float(value) for n,value in row.items()};g,h,d=map(Vector,steering_frame(row['phase']));x=d.cross(Vector((0,0,1))).normalized();z=x.cross(d);origin=g-d*(.12*1.95)
 center=Vector((row['x'],row['y'],row['z']));forward=Vector((row['forward_x'],row['forward_y'],0));right=Vector((forward.y,-forward.x,0));points=[]
 for p in v:
  q=origin+x*p.x*.90+d*p.y*1.95+z*p.z*.90;points.append(center+forward*q.x+right*q.z+Vector((0,0,q.y)))
 oar=BVHTree.FromPolygons(points,f,all_triangles=True);pairs=environment.overlap(oar)
 if pairs:contacts.append(dict(time=row['time'],team=int(row['team']),intersections=len(pairs)))
 if k%400==0:print('STEERING_WORLD',k,'contacts',len(contacts),flush=True)
report=dict(status='PASS' if not contacts else 'FAIL',trajectory_samples=len(rows),samples_per_team=len(rows)//2,frequency_hz=60,environment_assets=sorted(assets),contact_count=len(contacts),contacts=contacts[:60],trajectory_sha256=hashlib.sha256((R/'results/steering_world_samples.csv').read_bytes()).hexdigest(),method='Full transformed steering-oar triangles versus quay, docks, bridges, banks and riverbed at every C++ 1/60-second race sample')
(R/'results/steering_environment_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('STEERING_ENVIRONMENT',json.dumps(report),flush=True)
assert report['status']=='PASS'
