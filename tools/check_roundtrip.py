"""Re-import the actual deliverables in Blender and verify geometry/materials."""
import bpy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
expected=json.loads((ROOT/'models/inventory.json').read_text())
report=[]
selected=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
for filename in (selected or ('dragon_boat_red.obj','dragon_boat_jade.obj','scene_preview.obj','dragonboat_scene.glb')):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    p=ROOT/'models'/filename
    if p.suffix=='.obj':bpy.ops.wm.obj_import(filepath=str(p),forward_axis='NEGATIVE_Z',up_axis='Y')
    else:bpy.ops.import_scene.gltf(filepath=str(p))
    objects=[o for o in bpy.data.objects if o.type=='MESH'];count=0
    for o in objects:
        o.data.calc_loop_triangles();count+=len(o.data.loop_triangles)
        assert o.data.uv_layers.active is not None,(filename,o.name,'UV missing')
        assert o.data.materials,(filename,o.name,'material missing')
    if p.suffix=='.obj':
        target=next(i['triangles'] for i in expected if i['file']==filename)
        assert count==target,(filename,count,target)
    images=[im for im in bpy.data.images if im.source=='FILE']
    assert images,(filename,'no images')
    for im in images:assert im.size[0]>0 and im.size[1]>0,(filename,im.filepath,'image missing')
    report.append({'file':filename,'meshes':len(objects),'triangles_after_import':count,'images_loaded':len(images),'status':'PASS'})
out=ROOT/'models/roundtrip_validation.json'
if selected and out.exists():
    old=json.loads(out.read_text());report=[r for r in old if r['file'] not in selected]+report
out.write_text(json.dumps(report,indent=2),encoding='utf-8')
print('ROUNDTRIP_PASS',json.dumps(report))
