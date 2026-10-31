"""Refresh affected street and cardinal previews using the saved final scene."""
import bpy,sys,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];PRE=ROOT/'previews'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
exec((ROOT/'tools/configure_render_device.py').read_text(encoding='utf-8'),globals());configure_preview_device()
scene=bpy.context.scene;scene.render.use_persistent_data=True;scene.cycles.samples=12;scene.render.resolution_x=1600;scene.render.resolution_y=1000;cam=scene.camera;cam.data.type='PERSP';cam.data.lens=32
for name,loc,target in [('16_view_east',(-8,0,9),(70,0,8)),('17_view_south',(0,1,10),(0,-75,10)),('18_view_west',(8,0,9),(-70,0,8)),('19_view_north',(0,-1,10),(0,75,10)),('12_old_town_street',(-22,7.85,1.75),(1,8.4,2.6))]:
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(PRE/(name+'.png'));render_preview_frame()
shutil.copy2(PRE/'12_old_town_street.png',PRE/'06_riverside_architecture.png')
for name in ['01_scene_overview.png','11_huizhou_overview.png']:shutil.copy2(PRE/'25_dispersed_village.png',PRE/name)
print('DISPERSED_VIEWS_CURRENT',flush=True)
