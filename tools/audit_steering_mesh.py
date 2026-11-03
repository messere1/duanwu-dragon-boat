"""Audit interpolated helmsman surfaces and both hulls against the actual oar mesh."""
import bpy,sys,json,math,struct,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));from steering_motion import steering_frame

def obj(name):
 vs=[];faces=[]
 for line in (R/'models'/name).open(encoding='utf8'):
  if line.startswith('v '):vs.append(tuple(map(float,line.split()[1:])))
  elif line.startswith('f '):
   ids=[int(t.split('/')[0])-1 for t in line.split()[1:]]
   for i in range(1,len(ids)-1):faces.append((ids[0],ids[i],ids[i+1]))
 return vs,faces
hulls={}
for team in ('red','jade'):
 vs=[];fs=[]
 for name in ('boat_hull_'+team+'.obj','dragon_tail_'+team+'.obj'):
  a,b=obj(name);start=len(vs);vs+=a;fs += [tuple(i+start for i in f) for f in b]
 hulls[team]=BVHTree.FromPolygons(vs,fs)
vp,fp=obj('steering_oar.obj');paddle=np.asarray(vp)
with (R/'models/steering_cycle.bin').open('rb') as f:
 magic,F,N,M=struct.unpack('<8sIII',f.read(20));assert magic==b'DBPOSE01';names=[]
 for i in range(M):
  size=struct.unpack('<I',f.read(4))[0];names.append(f.read(size).decode())
 ids=np.frombuffer(f.read(N*4),dtype='<u4');offset=f.tell()
poses=np.memmap(R/'models/steering_cycle.bin',dtype='<f4',mode='r',offset=offset,shape=(F,N,8))
triangles=[(i,i+1,i+2) for i in range(0,N,3)];radius=.021*.90*.65;body_min=1e9;hull_min=1e9;overlaps=[];body_hits=[];foot_change=0.;palm_error=0.;tip_levels=[];body_motion=0.
shoe=ids==next(i for i,n in enumerate(names) if 'shoes02' in n);base_feet=poses[0,shoe,:3].copy()
for k in range(80):
 phase=k/80;index=phase*F;a=int(index);b=(a+1)%F;t=index-a
 body=poses[a,:,:3]*(1-t)+poses[b,:,:3]*t;foot_change=max(foot_change,float(np.linalg.norm(body[shoe]-base_feet,axis=1).max()))
 body_motion=max(body_motion,float(np.linalg.norm(body-poses[0,:,:3],axis=1).max()));body=body+np.array([-4.12,.91,0]);bvh=BVHTree.FromPolygons([Vector(v) for v in body],triangles,all_triangles=True)
 g,h,d=map(Vector,steering_frame(phase));x=d.cross(Vector((0,0,1))).normalized();z=x.cross(d);origin=g-d*(.12*1.95)
 points=np.asarray([origin+x*p[0]*.90+d*p[1]*1.95+z*p[2]*.90 for p in paddle]);oar=BVHTree.FromPolygons([Vector(v) for v in points],fp,all_triangles=True)
 tip_levels.append(float(points[:,1].min()))
 for team,hull in hulls.items():
  pairs=hull.overlap(oar)
  if pairs:overlaps.append(dict(phase=phase,team=team,pairs=len(pairs)))
  for p in points[::4]:
   near,normal,_,distance=hull.find_nearest(Vector(p));hull_min=min(hull_min,distance)
 start=g.copy();remaining=1.56*1.95
 for hit_index in range(64):
  hit,normal,_,distance=bvh.ray_cast(start,-d,remaining)
  if hit is None:break
  if min((hit-g).length,(hit-h).length)>.145:body_hits.append(dict(phase=phase,kind='shaft_body_ray_intersection',point=list(hit)))
  remaining-=distance+.0001;start=hit-d*.0001
  if remaining<=0:break
 for distance in np.arange(0,1.56*1.95+.001,.018):
  p=g-d*float(distance)
  if min((p-g).length,(p-h).length)<.145:continue
  near,normal,_,gap=bvh.find_nearest(p);body_min=min(body_min,gap)
  if gap<radius+.003:body_hits.append(dict(phase=phase,shaft_distance=float(distance),clearance=gap,point=list(p)))
 print('STEER_AUDIT',k,'body_gap',round(body_min,5),'hull_pairs',len(overlaps),flush=True)
report=dict(status='PASS' if not overlaps and not body_hits and foot_change<.012 and body_motion>.03 else 'FAIL',pose_samples=80,maximum_character_vertex_motion_m=body_motion,both_hulls_checked=True,oar_hull_triangle_overlaps=overlaps,shaft_body_contacts_outside_grips=body_hits[:25],shaft_body_contact_count=len(body_hits),minimum_shaft_body_surface_distance_m=body_min,shaft_radius_m=radius,hand_contact_guard_radius_m=.145,minimum_oar_vertex_hull_distance_m=hull_min,maximum_planted_foot_vertex_motion_m=foot_change,blade_tip_height_range_m=[min(tip_levels),max(tip_levels)],method='Actual interpolated character meshes; shaft capsule samples outside intended hand contacts; both hull/tail triangle overlap against transformed dedicated steering-oar mesh')
(R/'results/steering_collision_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('STEERING_COLLISION',json.dumps(report),flush=True)
if report['status']!='PASS':raise RuntimeError('Steering geometry audit failed')
