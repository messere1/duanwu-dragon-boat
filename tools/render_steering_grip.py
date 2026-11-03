"""Render the editable helmsman grip for close contact inspection."""
import bpy,math
from pathlib import Path
from mathutils import Vector
R=Path.cwd();bpy.ops.wm.open_mainfile(filepath=str(R/'models/helmsman_steering.blend'))
s=bpy.context.scene;s.frame_set(32);s.render.engine='BLENDER_WORKBENCH';s.render.resolution_x=1100;s.render.resolution_y=900;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('ReviewWorld');s.display.shading.light='STUDIO';s.display.shading.studio_light='paint.sl';s.display.shading.color_type='OBJECT';s.display.shading.show_shadows=True;s.display.shading.show_cavity=True;s.display.shading.cavity_type='BOTH';s.world.color=(.19,.21,.23)
for o in s.objects:
 if o.type=='MESH':o.color=(.52,.29,.17,1) if o.name=='Human' else (.32,.12,.08,1) if 'casual' in o.name else (.22,.16,.10,1)
camdata=bpy.data.cameras.new('grip_review');cam=bpy.data.objects.new('grip_review',camdata);s.collection.objects.link(cam);s.camera=cam;camdata.type='ORTHO';camdata.ortho_scale=1.15;cam.location=(-2.6,-1.9,2.75);cam.rotation_euler=(Vector((-3.85,-.45,2.02))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(R/'results/steering_grip_closeup.png');bpy.ops.render.render(write_still=True)
