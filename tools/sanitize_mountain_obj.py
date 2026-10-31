"""Remove triangle faces that collapse after six-decimal OBJ serialization."""
from pathlib import Path
from array import array
import json,os
R=Path(__file__).resolve().parents[1];M=R/'models';p=M/'mountain_refined.obj';tmp=p.with_suffix('.obj.clean');v=array('d');removed=0;kept=0
with p.open(encoding='utf8') as src,tmp.open('w',encoding='utf8',newline='\n') as dst:
 for line in src:
  if line.startswith('v '):v.extend(map(float,line.split()[1:]))
  elif line.startswith('f '):
   ids=[int(t.split('/')[0])-1 for t in line.split()[1:]];assert len(ids)==3
   a,b,c=[v[i*3:i*3+3] for i in ids];u=[b[j]-a[j] for j in range(3)];w=[c[j]-a[j] for j in range(3)];cross=(u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0])
   if sum(x*x for x in cross)<=1e-19:removed+=1;continue
   kept+=1
  dst.write(line)
 dst.flush();os.fsync(dst.fileno())
tmp.replace(p)
manifest=json.loads((M/'mountain_patch_manifest.json').read_text());manifest['new_component']['triangles']=kept;(M/'mountain_patch_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
r=json.loads((R/'results/mountain_geometry_build.json').read_text());r['refined_triangles']=kept;r['rounded_degenerate_triangles_removed']=removed;(R/'results/mountain_geometry_build.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print(dict(remaining_triangles=kept,removed_collapsed_faces=removed))

