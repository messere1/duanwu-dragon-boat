"""Validate exported deliverables, not Blender construction helpers."""
import json, math, re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; MD=ROOT/'models'
inventory=json.loads((MD/'inventory.json').read_text(encoding='utf-8'))
if len(sys.argv)>1:inventory=[x for x in inventory if x['file'] in sys.argv[1:]]
results=[]
for info in inventory:
    path=MD/info['file'];v=[];uv=[];ns=[];faces=0;materials=set();groups=0
    for line in path.open(encoding='utf-8'):
        parts=line.split()
        if not parts:continue
        if parts[0] in ('v','vt','vn'):
            vals=tuple(map(float,parts[1:]));assert all(math.isfinite(x) for x in vals),(path,'nonfinite')
            {'v':v,'vt':uv,'vn':ns}[parts[0]].append(vals)
            if parts[0]=='vn':assert abs(sum(x*x for x in vals)-1)<1e-4,(path,'normal')
        elif parts[0]=='usemtl':materials.add(parts[1])
        elif parts[0]=='o':groups+=1
        elif parts[0]=='f':
            assert len(parts)==4,(path,'not triangulated')
            pts=[]
            for token in parts[1:]:
                ids=list(map(int,token.split('/')));assert len(ids)==3
                for i,count in zip(ids,(len(v),len(uv),len(ns))):assert 1<=i<=count,(path,'invalid index')
                pts.append(v[ids[0]-1])
            a=[pts[1][i]-pts[0][i] for i in range(3)];b=[pts[2][i]-pts[0][i] for i in range(3)]
            cross=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
            assert sum(x*x for x in cross)>1e-18,(path,'degenerate triangle')
            normal=ns[int(parts[1].split('/')[2])-1]
            alignment=sum(a*b for a,b in zip(cross,normal))/math.sqrt(sum(x*x for x in cross))
            assert alignment>-0.01,(path,'smooth normal opposed to triangle winding',alignment)
            faces+=1
    assert faces==info['triangles'];assert len(v)==len(uv)==len(ns)==info['vertices']
    actual=[[min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)]]
    for calculated,expected in zip(actual,(info['min'],info['max'])):
        assert max(abs(a-b) for a,b in zip(calculated,expected))<2e-5
    results.append({'file':path.name,'triangles':faces,'groups':groups,'materials':sorted(materials),'status':'PASS'})
mtl=(MD/'palette.mtl').read_text(encoding='utf-8');defined=set(re.findall(r'^newmtl (.+)$',mtl,re.M))
for r in results:assert set(r['materials'])<=defined
for name in re.findall(r'^map_Kd (.+)$',mtl,re.M):assert (MD/name).is_file(),name
layout=json.loads((MD/'scene_layout.json').read_text(encoding='utf-8')); names={n['name'] for n in layout['nodes']}
assert len(names)==len(layout['nodes'])
for n in layout['nodes']:
    assert n['parent'] is None or n['parent'] in names
    for key in ('local_matrix_zup','world_matrix_yup'):
        assert len(n[key])==4 and all(len(row)==4 for row in n[key])
        assert all(math.isfinite(v) for row in n[key] for v in row)
assert (MD/'dragonboat_scene.glb').read_bytes()[:4]==b'glTF'
assert (ROOT/'dragonboat_models.blend').read_bytes()[:7]==b'BLENDER'
summary={'status':'PASS','obj_files':len(results),'scene_nodes':len(names),'checks':['triangle indices','finite positions and UVs','unit normals','nonzero triangle area','material and texture paths','manifest bounds','scene parent references','GLB and BLEND signatures'],'files':results}
out=MD/('validation_final_attachments.json' if len(sys.argv)>1 else 'validation.json')
out.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='files'},ensure_ascii=False))
