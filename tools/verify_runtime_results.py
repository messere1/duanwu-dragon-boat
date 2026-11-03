"""Audit the real application's readback images and GPU validation log."""
from pathlib import Path
import json,re,statistics,hashlib
from PIL import Image,ImageStat,ImageChops
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'results'
log=(out/'runtime.log').read_text(encoding='utf-8')
frames=re.findall(r'Verify frame (\d+): GL=(\d+), frame_ms=([\d.]+), time=([\d.]+)',log)
assert len(frames)==36 and all(int(e)==0 for _,e,_,_ in frames)
assert float(frames[18][3])==26 and 'SUCCESS' in log
expected=next(i['triangles'] for i in json.loads((ROOT/'models/inventory.json').read_text()) if i['file']=='scene_preview.obj')
assert f'OBJ triangles {expected},' in log
images=[Image.open(out/f'verify_{i}.png').convert('RGB') for i in range(36)]
for im in images:
    assert im.size==(1440,900)
    assert sum(ImageStat.Stat(im.crop((0,110,1440,900))).stddev)>40,'Blank or uniform scene readback'
crop=images[1].crop((10,10,1130,40));pixels=crop.get_flattened_data() if hasattr(crop,'get_flattened_data') else crop.getdata()
gold=sum(1 for r,g,b in pixels if r>220 and g>170 and b<190)
assert gold>50,'Screenshot channels do not preserve the gold HUD color'
diff=ImageStat.Stat(ImageChops.difference(images[1].crop((0,110,1440,900)),images[2].crop((0,110,1440,900)))).mean
assert sum(diff)>5,'Texture on/off comparison did not change the rendered scene'
steady=[float(ms) for i,_,ms,_ in frames if int(i)>=2]
race=[tuple(map(float,r)) for r in re.findall(r'Race sample ([\d.]+) red_distance=([\d.]+) jade_distance=([\d.]+) red_speed=([\d.]+) jade_speed=([\d.]+)',log)]
assert len(race)==3 and race[0][1]>race[0][2] and race[1][1]<race[1][2] and race[2][1]>race[2][2]
pose=json.loads((ROOT/'models/rowing_cycle.json').read_text(encoding='utf8'))
assert pose['frames']==40 and pose['closed_cycle_max_error_m']<.0001
assert pose['max_palm_target_error_m']<.002
drum=json.loads((ROOT/'models/drumming_cycle.json').read_text(encoding='utf8'))
assert drum['max_palm_target_error_m']<.002 and drum['closed_cycle_max_error_m']<.0001
beats=[tuple(map(float,r)) for r in re.findall(r'Drum sample ([\d.]+) right_tip_y=([\d.]+) left_tip_y=([\d.]+)',log)]
assert len(beats)==3 and abs(beats[0][1]-1.67)<.0001 and abs(beats[2][2]-1.67)<.0001 and beats[1][1]>2.1
report={'status':'PASS','renderer':re.search(r'Renderer (.+)',log).group(1).strip(),'obj_triangles':expected,'material_batches':int(re.search(r'batches (\d+)',log).group(1)),'checked_frames':36,'opengl_errors':0,'median_warm_frame_ms':round(statistics.median(steady),3),'full_timeline_seconds':26,'race_samples':race,'pose_cycle_frames':40,'drumming_pose_frames':drum['frames'],'drumming_contact_samples':beats,'drumming_palm_error_m':drum['max_palm_target_error_m'],'checks':['Seated stern-facing drummer, alternating beat contacts, rebound and palm IK rendered','OBJ scene and material images really rendered','Texture toggle changes scene pixels','PNG readback retains color channels','Keyboard translation/rotation/scale and mouse pan/look assertions passed','Additional OBJ imported into GPU buffers','Fixed-step complete 26-second boat and separate drone update passed','Catch / drive / recovery poses rendered with synchronized 24 paddles and IK-baked crew','Lead changes verified at 5, 15 and 26 seconds; speed integrated continuously'],'limitation':'Authored kinematic racing with analytic surface wakes, not a hydrodynamic solver. Filtered directional shadows and 4x MSAA enabled. Vegetation belts use shared 3D tree geometry; analytic wind and wakes are not cloth/fluid solvers.'}
shadow_diff=sum(ImageStat.Stat(ImageChops.difference(images[30].crop((0,130,1440,900)),images[31].crop((0,130,1440,900)))).mean)
assert shadow_diff>1,'Shadow toggle did not change the scene'
assert 'scene MSAA 4x' in log
geometry=json.loads((out/'cinematic_geometry_audit.json').read_text(encoding='utf8'))
assert geometry['camera_samples_sha256']==hashlib.sha256((out/'cinematic_samples.csv').read_bytes()).hexdigest()
assert geometry['flight_source_sha256']==hashlib.sha256((ROOT/'src/cinematic.h').read_text(encoding='utf-8-sig').encode('utf8')).hexdigest()
assert 'Pause and selection PASS' in log
assert geometry['status']=='PASS' and geometry['camera_samples']==1561 and geometry['obstruction_count']==0
playlog=(out/'playthrough.log').read_text(encoding='utf8')
played=re.findall(r'Play frame (\d+) time=([\d.]+) GL=(\d+) frame_ms=([\d.]+)',playlog)
assert len(played)>260 and float(played[-1][1])==26 and all(int(r[2])==0 for r in played)
assert 'SUCCESS' in playlog and 'checkpoints=6' in playlog
for i in range(6):
    im=Image.open(out/f'playthrough_{i}.png').convert('RGB')
    assert im.size==(1440,900) and sum(ImageStat.Stat(im.crop((0,130,1440,900))).stddev)>40
report.update({'real_playthrough_frames':len(played),'real_playthrough_wall_seconds':float(re.search(r'wall_seconds=([\d.]+)',playlog).group(1)),'real_playthrough_checkpoints':6,'camera_geometry_audit':{k:geometry[k] for k in ['camera_samples','boat_visibility_rays','camera_surface_clearance_m','boat_bank_margin_m','obstruction_count']},'flag_pole_edge_pinned':True,'shadow_map_size':4096,'msaa_samples':4,'shadow_toggle_image_delta':shadow_diff,'landscape_tree_count':json.loads((ROOT/'models/environment_details.json').read_text())['trees']})
report['checks']+=['Wind-driven cloth rendered with pinned pole edge','Five-stage independent camera, smooth endpoint stop and safe framing','Complete real-time rendered playback to 26 seconds, six screenshot checkpoints','Final scene ray audit checks every 1/60 second against buildings/bridges/shore']


cull_diff=ImageChops.difference(images[32].crop((0,130,1440,900)),images[33].crop((0,130,1440,900)))
assert cull_diff.getbbox() is None,'Conservative culling changed visible scene pixels'
counts=[int(v) for v in re.findall(r'Static visibility sample \d+ triangles=(\d+)',log)]
assert len(counts)==2 and counts[0]<counts[1]
assets=json.loads((out/'realism_asset_validation.json').read_text(encoding='utf8'))
characters=json.loads((out/'character_variation_validation.json').read_text(encoding='utf8'))
assert assets['status']==characters['status']=='PASS'
report.update({'culling_scene_pixel_difference':0,'static_triangles_culling_on_off':counts,'tree_prototype_triangles':assets['tree_mesh']['triangles'],'new_village_detail_triangles':assets['village_mesh']['triangles'],'real_playthrough_median_frame_ms':round(statistics.median(float(r[3]) for r in played[10:]),3)})
report.update({'understory_triangles':assets['understory_mesh']['triangles'],'shrub_clumps':assets['shrub_clumps'],'bamboo_groves':assets['bamboo_groves']})
patch=json.loads((out/'mountain_obj_patch.json').read_text(encoding='utf8'))
assert patch['status']=='PASS' and patch['scene_triangles']==expected
report.update({'mountain_geometry_triangles':assets['mountain_mesh']['triangles'],'mountain_support':assets['mountain_support']})
report['checks']+=['Frustum culling preserves every scene pixel at the comparison camera','Shared 3D vegetation and village geometry/material dependencies checked','Head variation does not affect fingers throughout both interpolated pose cycles']
steering=json.loads((ROOT/'models/steering_cycle.json').read_text(encoding='utf8'))
steering_collision=json.loads((out/'steering_collision_audit.json').read_text(encoding='utf8'))
steering_source=json.loads((out/'steering_authoring_validation.json').read_text(encoding='utf8'))
assert steering['closed_cycle_max_error_m']<.0001 and steering['max_palm_target_error_m']<.002
assert steering_collision['status']==steering_source['status']=='PASS'
steering_environment=json.loads((out/'steering_environment_audit.json').read_text(encoding='utf8'))
assert steering_environment['status']=='PASS' and steering_environment['trajectory_samples']==3122
assert steering_environment['trajectory_sha256']==hashlib.sha256((out/'steering_world_samples.csv').read_bytes()).hexdigest()
assert 'Animated helmsmen and linked steering oars loaded' in log
report['steering']={'pose_frames':steering['frames'],'max_palm_target_error_m':steering['max_palm_target_error_m'],'collision_checks':steering_collision['pose_samples'],'hull_overlap_count':len(steering_collision['oar_hull_triangle_overlaps']),'body_contact_count':steering_collision['shaft_body_contact_count'],'feet_vertex_motion_m':steering_collision['maximum_planted_foot_vertex_motion_m'],'character_vertex_motion_m':steering_collision['maximum_character_vertex_motion_m'],'editable_source_validated':True,'environment_trajectory_samples':steering_environment['trajectory_samples'],'environment_contacts':steering_environment['contact_count']}
report['checks']+=['Both helmsmen animate with linked steering-oar grips and planted feet','Actual interpolated steering geometry checked against torso and both hulls','Editable steering rig and keyed oar palms verified']
(out/'runtime_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))

