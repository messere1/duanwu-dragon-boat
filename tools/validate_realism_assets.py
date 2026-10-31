"""Validate runtime overlay geometry, material dependencies and placements."""
from pathlib import Path
import json,math
from PIL import Image
R=Path(__file__).resolve().parents[1]
def check(name):
 p=R/'models'/name;vs=[];ns=[];faces=[];used=set()
 for line in p.read_text(encoding='utf8').splitlines():
  t=line.split()
  if not t:continue
  if t[0]=='v':vs.append(tuple(map(float,t[1:])))
  elif t[0]=='vn':ns.append(tuple(map(float,t[1:])))
  elif t[0]=='f':faces.append([int(x.split('/')[0])-1 for x in t[1:]])
  elif t[0]=='mtllib':mtl=p.parent/t[1]
  elif t[0]=='usemtl':used.add(t[1])
 assert all(math.isfinite(x) for v in vs for x in v)
 assert all(abs(sum(x*x for x in n)-1)<.00002 for n in ns)
 minimum=1e9
 for f in faces:
  assert len(f)==3 and all(0<=i<len(vs) for i in f)
  a,b,c=[vs[i] for i in f];u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
  cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]);area=sum(x*x for x in cross)
  assert area>1e-19,(name,f,area)
  minimum=min(minimum,area)
 defined=set();images=[]
 for line in mtl.read_text(encoding='utf8').splitlines():
  t=line.split()
  if not t:continue
  if t[0]=='newmtl':defined.add(t[1])
  if t[0] in ('map_Kd','map_Bump','bump'):
   tex=mtl.parent/t[1];assert tex.is_file(),tex
   with Image.open(tex) as im:im.verify()
   images.append(tex.name)
 assert used<=defined
 return dict(triangles=len(faces),vertices=len(vs),textures=images,minimum_cross_length_squared=minimum)
mountain=check('mountain_refined.obj');tree=check('vegetation_lod.obj');village=check('village_detail.obj');understory=check('landscape_understory.obj')
details=json.loads((R/'models/village_detail.json').read_text());assert village['triangles']==details['triangles']
trees=json.loads((R/'models/vegetation_lod.json').read_text());rows=[list(map(float,l.split())) for l in (R/'models/vegetation_instances.txt').read_text().splitlines()]
assert len(rows)==trees['instances']==216 and tree['triangles']==trees['prototype_triangles']
assert all(len(r)==5 and all(math.isfinite(x) for x in r) and .5<r[4]<2 for r in rows)
with (R/'dragonboat_realism.blend').open('rb') as f:assert f.read(7)==b'BLENDER'
cover=json.loads((R/'models/landscape_understory.json').read_text())
assert understory['triangles']==cover['triangles']
assert len(cover['shrubs_zup'])==cover['shrub_clumps'] and len(cover['bamboo_zup'])==cover['bamboo_groves']
from river_routes import river_center
assert all(abs(y-river_center(x))>=13 and all(math.isfinite(t) for t in (x,y,z,h)) for x,y,z,h in cover['shrubs_zup']+cover['bamboo_zup'])
mountain_build=json.loads((R/'results/mountain_geometry_build.json').read_text())
support=json.loads((R/'results/mountain_support_validation.json').read_text())
assert mountain_build['status']==support['status']=='PASS' and mountain['triangles']==mountain_build['refined_triangles']
report=dict(status='PASS',mountain_mesh=mountain,mountain_support=support,understory_mesh=understory,shrub_clumps=cover['shrub_clumps'],bamboo_groves=cover['bamboo_groves'],tree_instances=len(rows),tree_mesh=tree,village_mesh=village,village_details=details,native_scene='dragonboat_realism.blend')
(R/'results/realism_asset_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
