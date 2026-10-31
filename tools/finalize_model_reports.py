"""Consolidate unchanged asset checks and the final six modified OBJ checks."""
import json,base64,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];md=ROOT/'models'
old=json.loads((md/'validation.json').read_text(encoding='utf-8'))
latest=json.loads((md/'validation_final_attachments.json').read_text(encoding='utf-8'))
records={i['file']:i for i in old['files']};records.update({i['file']:i for i in latest['files']})
inventory=json.loads((md/'inventory.json').read_text())
assert set(records)=={i['file'] for i in inventory}
for i in inventory:assert records[i['file']]['status']=='PASS' and records[i['file']]['triangles']==i['triangles']
old.update(status='PASS',obj_files=len(records),scene_nodes=latest['scene_nodes'],files=[records[i['file']] for i in inventory],rechecked_after_river_refinement=[i['file'] for i in latest['files']])
(md/'validation.json').write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf-8')
# Keep fresh OBJ round trips; the final GLB has a separate complete buffer audit.
p=md/'roundtrip_validation.json';d=json.loads(p.read_text());d=[r for r in d if r['file']!='dragonboat_scene.glb'];p.write_text(json.dumps(d,indent=2),encoding='utf-8')
p=md/'panorama_tree_clearance.json'
if p.exists():
    d=json.loads(p.read_text());d['scope']='Historical tree relocation before river refinement; current placement follows scene_layout.json.';p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
html=(ROOT/'360全景预览.html').read_text(encoding='utf-8');data=re.search(r'data:image/png;base64,([A-Za-z0-9+/=]+)',html).group(1)
assert hashlib.sha256(base64.b64decode(data)).digest()==hashlib.sha256((ROOT/'previews/15_environment_360.png').read_bytes()).digest()
for n in ['river_validation.json','panorama_validation.json','glb_buffer_validation.json']:assert json.loads((md/n).read_text())['status']=='PASS'
print('FINAL_REPORTS_PASS',len(records),'OBJ files; current offline panorama matches PNG')
