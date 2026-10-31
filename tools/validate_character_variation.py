"""Verify the head variation mask never reaches fingers through either pose cycle."""
from pathlib import Path
import struct,json,numpy as np
R=Path(__file__).resolve().parents[1];roles={}
for role in ('rowing','drumming'):
 with (R/f'models/{role}_cycle.bin').open('rb') as f:
  magic,frames,count,n=struct.unpack('<8sIII',f.read(20));assert magic==b'DBPOSE01'
  names=[]
  for _ in range(n):
   size=struct.unpack('<I',f.read(4))[0];names.append(f.read(size).decode())
  ids=np.frombuffer(f.read(count*4),dtype='<u4');poses=np.frombuffer(f.read(),dtype='<f4').reshape(frames,count,8)
 hair=ids==next(i for i,s in enumerate(names) if '.short01' in s)
 fingers=ids==next(i for i,s in enumerate(names) if '.fingernails' in s)
 assert hair.any() and fingers.any()
 minimum=1e9
 for a in range(frames):
  b=(a+1)%frames
  for t in np.linspace(0,1,40,endpoint=False):
   center=(poses[a,hair,:3]*(1-t)+poses[b,hair,:3]*t).mean(0)
   points=poses[a,fingers,:3]*(1-t)+poses[b,fingers,:3]*t
   minimum=min(minimum,float(np.linalg.norm(points-center,axis=1).min()))
 assert minimum>.197,(role,minimum)
 roles[role]=dict(hair_vertices=int(hair.sum()),finger_vertices=int(fingers.sum()),minimum_finger_distance_to_head_center_m=minimum,head_mask_radius_m=.195,interpolation_checks=frames*40)
report=dict(status='PASS',roles=roles)
(R/'results/character_variation_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
