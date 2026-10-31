import bpy,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'external_assets/prepared_open_assets.blend'))
obs=[o for o in bpy.data.objects if o.type=='MESH']
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True
s.render.resolution_x=1100;s.render.resolution_y=1000;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('PreviewWorld');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.4,.4,.4,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.7
cd=bpy.data.cameras.new('PreviewCamera');cam=bpy.data.objects.new('PreviewCamera',cd);s.collection.objects.link(cam);s.camera=cam;cd.type='ORTHO'
ld=bpy.data.lights.new('PreviewKey','AREA');light=bpy.data.objects.new('PreviewKey',ld);s.collection.objects.link(light)
for label,scale,eye,target in [('human',2.0,(2,-3,2),(.15,0,.50)),('head',3.2,(9,-5,3),(5.5,0,1.6)),('tree',5.4,(6,-9,5),(0,0,2))]:
    if '--human-only' in sys.argv and label!='human':continue
    prefix={'human':'open_human_seated','head':'open_head','tree':'open_tree'}[label]
    for o in obs:o.hide_render=not o.name.startswith(prefix+'__')
    cam.location=eye;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=scale
    light.location=Vector(target)+Vector((scale,-scale,scale*2));light.rotation_euler=(Vector(target)-light.location).to_track_quat('-Z','Y').to_euler();ld.energy=150*scale**2;ld.size=scale*2
    s.render.filepath=str(R/'previews'/('open_asset_'+label+'.png'));bpy.ops.render.render(write_still=True)
