"""Check actual finger/palm triangles against both finite grip cylinders at runtime interpolation phases."""
import json,sys,struct,hashlib
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from steering_motion import steering_frame
with (R/'models/steering_cycle.bin').open('rb') as f:
 magic,F,N,M=struct.unpack('<8sIII',f.read(20));assert magic==b'DBPOSE01'
 for _ in range(M):size=struct.unpack('<I',f.read(4))[0];f.read(size)
 f.read(N*4);offset=f.tell()
poses=np.memmap(R/'models/steering_cycle.bin',dtype='<f4',mode='r',offset=offset,shape=(F,N,8));indices=json.loads((R/'models/steering_hand_indices.json').read_text())
def radial_distance(tri,center,axis):
 axis=np.asarray(axis);axis/=np.linalg.norm(axis);x=np.cross(axis,[0,0,1])
 if np.linalg.norm(x)<.01:x=np.cross(axis,[1,0,0])
 x/=np.linalg.norm(x);z=np.cross(axis,x);relative=tri-center;tri=np.stack((relative@x,relative@z),axis=-1)
 a,b,c=tri[:,0],tri[:,1],tri[:,2];best=np.full(len(tri),1e6);signs=[]
 for v,w in ((a,b),(b,c),(c,a)):
  edge=w-v;delta=-v;t=np.clip((delta*edge).sum(-1)/(edge*edge).sum(-1).clip(1e-20),0,1);q=delta-t[:,None]*edge;best=np.minimum(best,(q*q).sum(-1));signs.append(edge[:,0]*delta[:,1]-edge[:,1]*delta[:,0])
 inside=((signs[0]>=0)&(signs[1]>=0)&(signs[2]>=0))|((signs[0]<=0)&(signs[1]<=0)&(signs[2]<=0));inside &= np.abs(np.cross(b-a,c-a))>1e-12;best[inside]=0
 return float(np.sqrt(best.min()))
rows=[]
for k in range(160):
 phase=k/160;p=phase*F;i=int(p);t=p-i;vertices=poses[i,:,:3]*(1-t)+poses[(i+1)%F,:,:3]*t+np.array([-4.12,.91,0]);g,h,d=map(np.asarray,steering_frame(phase));x=np.cross(d,[0,0,1]);x/=np.linalg.norm(x)
 row={'phase':phase}
 for side,center,axis,radius in (('L',g,x,.012),('R',h,d,.012285)):
  ids=np.asarray(indices[side]);tri=vertices[ids[:,None]+np.arange(3)];gap=radial_distance(tri,center,axis)-radius;row[side+'_surface_gap_m']=gap
 rows.append(row)
gaps=[row[s+'_surface_gap_m'] for row in rows for s in ('L','R')];report={'status':'PASS' if min(gaps)>=-.00015 and max(gaps)<.003 else 'FAIL','interpolated_phases':len(rows),'hand_triangles':{s:len(v) for s,v in indices.items()},'minimum_surface_gap_m':min(gaps),'maximum_surface_gap_m':max(gaps),'maximum_penetration_m':max(0,-min(gaps)),'method':'Exact distance from grip axis to the projected palm/finger triangles; includes the hand contact regions without exemptions. Conservative infinite-axis cylinders cover the full finite handles.','pose_sha256':hashlib.sha256((R/'models/steering_cycle.bin').read_bytes()).hexdigest(),'oar_sha256':hashlib.sha256((R/'models/steering_oar.obj').read_bytes()).hexdigest(),'samples':rows}
(R/'results/steering_grip_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k!='samples'}));assert report['status']=='PASS'
