"""Fit a shaft socket inside each curled hand using the evaluated skin triangles.
Run in Blender before baking; the saved profile is shared by the runtime pose export.
"""
import bpy,math,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
R=Path.cwd();bpy.ops.wm.open_mainfile(filepath=str(R/'external_assets/makehuman_cc0/athlete_rigged_cc0.blend'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
for b in rig.pose.bones:
 b.matrix_basis=Matrix.Identity(4)
 for c in list(b.constraints):b.constraints.remove(c)
 if b.name.startswith('finger'):
  digit,joint=map(int,b.name.split('.')[0][6:].split('-'));b.rotation_mode='XYZ';b.rotation_euler[0]=(.35,.65,.65)[joint-1] if digit==1 else (.65,1.05,.85)[joint-1]
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();data={}
for side in ('L','R'):
 for angles in ((0,.9,.8),):
  for b in rig.pose.bones:
   if b.name.startswith('finger'):
    digit,joint=map(int,b.name.split('.')[0][6:].split('-'));b.rotation_euler[0]=0.0 if digit==1 else angles[joint-1]
  bpy.context.view_layer.update()
  wb=rig.data.bones['wrist.'+side];bases=[rig.data.bones[f'finger{i}-1.{side}'].head_local.copy() for i in range(2,6)];origin=sum(bases,Vector())/4;row=(bases[-1]-bases[0]).normalized();long=(origin-wb.head_local);long=(long-row*long.dot(row)).normalized();normal=row.cross(long).normalized()
  if normal.dot(rig.data.bones['finger3-1.'+side].matrix_local.to_3x3().col[2])<0:row=-row;normal=-normal
  tris=[]
  for o in bpy.context.scene.objects:
   if o.type!='MESH':continue
   gs={g.index for g in o.vertex_groups if g.name.endswith('.'+side) and g.name.startswith(('wrist','finger'))}
   ev=o.evaluated_get(dg);m=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);m.calc_loop_triangles();weights=[sum(g.weight for g in v.groups if g.group in gs) for v in m.vertices]
   for t in m.loop_triangles:
    if min(weights[i] for i in t.vertices)<.20:continue
    points=[o.matrix_world@m.vertices[i].co for i in t.vertices];tris.append([((p-origin).dot(long),(p-origin).dot(normal)) for p in points])
   ev.to_mesh_clear()
  tri=np.asarray(tris);print('HAND_TRIANGLES',side,len(tri),flush=True)
  def distance(points):
   # Exact point/triangle distance in the plane perpendicular to the grip axis.
   p=points[:,None,:];a,b,c=tri[:,0],tri[:,1],tri[:,2];best=np.full((len(points),len(tri)),1e6)
   signs=[]
   for v,w in ((a,b),(b,c),(c,a)):
    edge=w-v;delta=p-v;t=np.clip((delta*edge).sum(-1)/(edge*edge).sum(-1).clip(1e-20),0,1);q=delta-t[...,None]*edge;best=np.minimum(best,(q*q).sum(-1));signs.append(edge[:,0]*delta[...,1]-edge[:,1]*delta[...,0])
   inside=((signs[0]>=-1e-12)&(signs[1]>=-1e-12)&(signs[2]>=-1e-12))|((signs[0]<=1e-12)&(signs[1]<=1e-12)&(signs[2]<=1e-12));inside &= np.abs((b[:,0]-a[:,0])*(c[:,1]-a[:,1])-(b[:,1]-a[:,1])*(c[:,0]-a[:,0]))>1e-12;best[inside]=0
   return np.sqrt(best.min(1))
  pts=np.asarray([(u,v) for u in np.arange(-.025,.008,.0015) for v in np.arange(.015,.043,.0015)]);dist=[]
  for k in range(0,len(pts),120):dist.extend(distance(pts[k:k+120]))
  dist=np.asarray(dist);radius=(.012 if side=='L' else .012285)/1.1;eligible=np.where(dist>radius+.00012)[0]
  if len(eligible):
   idx=min(eligible,key=lambda i:np.linalg.norm(pts[i]-[-.0085,.03])+.2*abs(dist[i]-radius-.001));print('FIT',side,'center',pts[idx].tolist(),'gap',float(dist[idx]-radius),'max_clearance',float(dist.max()),flush=True);socket=origin+long*pts[idx][0]+normal*pts[idx][1]
  else:raise RuntimeError(f'No collision-free grip socket for {side}')
  candidate={'angles':angles,'score':float(np.linalg.norm(pts[idx]-[-.0085,.03])),'origin':list(origin),'row':list(row),'long':list(long),'normal':list(normal),'socket':list(socket),'radius':radius}
  print('ANGLES',side,angles,candidate['score'],flush=True)
  if side not in data or candidate['score']<data[side]['score']:data[side]=candidate
(R/'models/steering_grasp.json').write_text(json.dumps(data,indent=2),encoding='utf8')
