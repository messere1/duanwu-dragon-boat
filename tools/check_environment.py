"""Check the delivered Blender assembly, signs and navigable entrances."""
import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
bpy.context.view_layer.update()
checks=[]
def bounds(o):
    pts=[o.matrix_world@Vector(v) for v in o.bound_box]
    return [(min(p[i] for p in pts),max(p[i] for p in pts)) for i in range(3)]
gate=bpy.data.objects['finish']
ridge=next(o for o in gate.children_recursive if 'ceramic_roof_ridge' in o.name)
b=bounds(ridge)
assert b[1][1]-b[1][0]>13 and b[2][1]-b[2][0]<.25,b
assert b[2][1]<6.7,b
checks.append('Gate ridge follows the river width, with no vertical stray member')
for o in bpy.data.objects:
    if o.type!='MESH' or not any(k in o.name for k in ('stall_handwritten_sign','pavilion_inscription','finish_inscription')):continue
    uv=o.data.uv_layers.active;assert uv is not None,o.name
    xs=[v.co.x for v in o.data.vertices];zs=[v.co.z for v in o.data.vertices]
    for i,l in enumerate(o.data.loops):
        co=o.data.vertices[l.vertex_index].co
        expected=((co.x-min(xs))/(max(xs)-min(xs)),(co.z-min(zs))/(max(zs)-min(zs)))
        assert max(abs(uv.data[i].uv[j]-expected[j]) for j in range(2))<1e-5,(o.name,'rotated sign UV')
checks.append('Sign UVs follow horizontal and vertical geometry axes')
bridge=bpy.data.objects['bridge'];assert abs(bridge.location.x-122)<1e-5
for name in ('quay_-6.7_5','quay_6.7_5'):
    q=bpy.data.objects[name];assert q['asset']=='quay_access'
    rails=[o for o in q.children_recursive if 'stone_rail_open_access' in o.name]
    assert len(rails)==4
    # The former bridge entrances at X=20 remain public access steps.
    for o in rails:
        lo,hi=bounds(o)[0]
        assert hi<18.70 or lo>21.30,(o.name,lo,hi)
checks.append('Former bridge entrances remain open public access steps; downstream bridge moved beyond the animated boat route')
dock=bpy.data.objects['south_mooring_dock'];q=bpy.data.objects['quay_-6.7_1']
assert q['asset']=='quay_access'
boards=[o for o in dock.children_recursive if 'dock_weathered_board' in o.name]
stairs=[o for o in q.children_recursive if 'water_access_step' in o.name]
board_top=max(bounds(o)[2][1] for o in boards)
last_step=min(bounds(o)[2][1] for o in stairs)
assert abs(board_top-last_step)<.012,(board_top,last_step)
assert max(bounds(o)[1][1] for o in boards)<-3.5
checks.append('Dock deck meets the bottom access step and stays clear of the boat lane')
assert len([o for o in bpy.data.objects if o.get('asset')=='tea_stall'])>=1
assert len([o for o in bpy.data.objects if o.get('asset')=='reed_patch'])==12
checks.append('Festival stall and twelve reed patches are assembled in the scene')
report={'status':'PASS','checks':checks}
(ROOT/'models/environment_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('ENVIRONMENT_PASS',json.dumps(report),flush=True)
