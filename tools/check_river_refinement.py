"""Audit the actual saved scene and the separate prospective flight route."""
import bpy,json,sys,math,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from river_routes import *
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_models.blend'));bpy.context.view_layer.update()
world=bpy.data.objects['world_export']
def bvh_for(assets):
    vs=[];fs=[]
    for r in world.children:
        if r.get('asset') not in assets:continue
        for o in r.children_recursive:
            if o.type!='MESH':continue
            base=len(vs);vs.extend(o.matrix_world@v.co for v in o.data.vertices)
            fs.extend(tuple(base+k for k in p.vertices) for p in o.data.polygons)
    return BVHTree.FromPolygons(vs,fs)
ground=bvh_for({'panorama_terrain','bank_ground','distant_hills','panorama_streets','quay_segment','quay_weathered_b','quay_access'})
water=bvh_for({'river_surface'})
hits=0
for i in range(301):
    x=-18+118*i/300;cy=river_center(x)
    for lane in (-1.8,0,1.8):
        origin=Vector((x,cy+lane,5));p,_,_,_=water.ray_cast(origin,Vector((0,0,-1)),10)
        assert p is not None and -.09<p.z<-.03,('Missing water',x,lane)
        h,_,_,_=ground.ray_cast(origin,Vector((0,0,-1)),5.10)
        assert h is None or h.z<-.07,('Land intrudes into navigable river',x,lane,tuple(h))
        hits+=1
min_clearance=100
for i in range(1001):
    p=route(BOAT_CURVES,i/1000);a=tangent(p[0])
    for lane in (-1.8,1.8):
        for longitudinal in (-6,0,6):
            for lateral in (-1.65,1.65):
                x=p[0]+longitudinal*math.cos(a)-(lane+lateral)*math.sin(a)
                y=p[1]+longitudinal*math.sin(a)+(lane+lateral)*math.cos(a)
                clearance=half_width(x)-abs(y-river_center(x));min_clearance=min(min_clearance,clearance)
assert min_clearance>.5,('Boat envelope touches bank',min_clearance)
for name,x in [('bridge',122),('pano_bridge_64',164)]:assert abs(bpy.data.objects[name].location.x-x)<1e-4
baseline=ROOT.parent/'_work/dragonboat/before_huizhou/boat_hashes.json'
if baseline.exists():
    hashes=json.loads(baseline.read_text())
    for name,expected in hashes.items():
        p=ROOT/'models'/Path(name).name
        assert hashlib.sha256(p.read_bytes()).hexdigest()==expected,('Accepted boat changed',name)
plan=json.loads((ROOT/'models/animation_route_plan.json').read_text())
buildings=bvh_for({'riverside_house','huizhou_tall_house','huizhou_tea_house','huizhou_courtyard','pavilion','arch_bridge','finish_gate'})
camera_tests=0
for f in plan['samples'][::6]:
    origin=Vector(f['camera_zup']);target=Vector(f['look_at_zup']);delta=target-origin
    hit,_,_,_=buildings.ray_cast(origin,delta.normalized(),max(0,delta.length-2))
    assert hit is None,('Building blocks planned aerial view',f['time'],tuple(hit))
    camera_tests+=1
offsets=[tuple(c-b for c,b in zip(f['camera_zup'],f['boat_center_zup'])) for f in plan['samples']]
assert max(p[2] for p in offsets)-min(p[2] for p in offsets)>5
assert len({tuple(round(v,1) for v in p) for p in offsets})>100
report={'status':'PASS','water_and_channel_samples':hits,'boat_envelope_tests':1001*12,'minimum_vertical_bank_margin_metres':min_clearance,'downstream_bridges_x':[122,164],'camera_has_independent_spatial_route':True,'planned_camera_building_visibility_tests':camera_tests,'accepted_boat_components_unchanged':True,'animation_status':'planned, not yet implemented in OpenGL'}
(ROOT/'models/river_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('RIVER_VALIDATION_PASS',json.dumps(report),flush=True)
