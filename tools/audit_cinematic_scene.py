"""Ray-test the C++ exported camera against the final, saved scene geometry."""
import bpy, csv, json, math, sys, collections, hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from river_routes import river_center,half_width
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_realism.blend'))
bpy.context.view_layer.update();world=bpy.data.objects['world_export']
assets={'riverside_house','huizhou_tall_house','huizhou_tea_house','huizhou_courtyard','pavilion','arch_bridge','finish_gate','tea_stall','mooring_dock','quay_segment','quay_weathered_b','quay_access','panorama_terrain','bank_ground','distant_hills','panorama_streets','eroded_riverbank_faces','panorama_valley_closure','dispersed_village_landuse','river_surface','natural_riverbed','village_lived_detail','landscape_understory'}
vertices=[];faces=[]
for root in world.children:
    if root.get('asset') not in assets:continue
    for o in [root,*root.children_recursive]:
        if o.type!='MESH':continue
        base=len(vertices);vertices.extend(o.matrix_world@v.co for v in o.data.vertices)
        faces.extend(tuple(base+k for k in p.vertices) for p in o.data.polygons)
print('BLOCKERS',len(vertices),len(faces),flush=True)
bvh=BVHTree.FromPolygons(vertices,faces,epsilon=.001)
del vertices,faces
samples=list(csv.DictReader((ROOT/'results/cinematic_samples.csv').open()))
hits=[];checks=0;clearance=1e9;bank_clearance=1e9;near=1e9
for row in samples:
    row={k:float(v) for k,v in row.items()};eye=Vector([row['eye_'+c] for c in 'xyz'])
    # Six short rays catch camera contact with roofs/walls/ground.
    for axis in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
        point,_,_,distance=bvh.ray_cast(eye,Vector(axis),.65)
        if point is not None:hits.append({'type':'camera_clearance','time':row['time'],'point':list(point)})
    point,_,_,distance=bvh.ray_cast(eye,Vector((0,0,-1)),500)
    if point is not None:clearance=min(clearance,distance)
    for team in ('red','jade'):
        center=Vector([row[team+'_'+c] for c in 'xyz'])
        # Tangent of the unchanged river centreline, sufficient for sight anchors.
        slope=(river_center(center.x+.02)-river_center(center.x-.02))/.04
        forward=Vector((1,slope,0)).normalized()
        for x,z in ((-5.5,1.0),(0,1.3),(5.5,1.2),(-4.1,2.7)):
            target=center+forward*x+Vector((0,0,z));delta=target-eye
            near=min(near,delta.length)
            point,_,_,distance=bvh.ray_cast(eye,delta.normalized(),delta.length-.12)
            checks+=1
            if point is not None:hits.append({'type':'blocked_boat_anchor','time':row['time'],'team':team,'local_x':x,'point':list(point)})
        for x in (-6.1,0,6.1):
            for y in (-1.95,1.95):
                p=center+forward*x+Vector((-forward.y,forward.x,0))*y
                bank_clearance=min(bank_clearance,half_width(p.x)-abs(p.y-river_center(p.x)))
report={'status':'PASS' if not hits and bank_clearance>.45 else 'FAIL','camera_samples':len(samples),'boat_visibility_rays':checks,'camera_surface_clearance_m':clearance,'minimum_camera_anchor_distance_m':near,'boat_bank_margin_m':bank_clearance,'obstructions':hits[:80],'obstruction_count':len(hits),'scope':'Final Blender building/roof/bridge/terrain/shore and understory geometry; original tree canopies excluded. C++ camera samples at 60 Hz.'}
report['camera_samples_sha256']=hashlib.sha256((ROOT/'results/cinematic_samples.csv').read_bytes()).hexdigest()
report['flight_source_sha256']=hashlib.sha256((ROOT/'src/cinematic.h').read_bytes()).hexdigest()
report['obstruction_time_buckets']={str(k):v for k,v in sorted(collections.Counter(int(h['time']) for h in hits).items())}
(ROOT/'results/cinematic_geometry_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('CINEMATIC_AUDIT',json.dumps(report,ensure_ascii=False),flush=True)
if report['status']!='PASS':raise RuntimeError('Cinematic sight/clearance audit failed')

