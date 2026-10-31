import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(R/'external_assets/chinese_dragon_head/chinese_dragon_head.glb'))
obs=[o for o in bpy.data.objects if o.type=='MESH'];bb=[o.matrix_world@Vector(v) for o in obs for v in o.bound_box]
lo=Vector([min(p[i] for p in bb) for i in range(3)]);hi=Vector([max(p[i] for p in bb) for i in range(3)]);center=(lo+hi)/2;extent=max(hi-lo)
print('HEAD_BOUNDS',list(lo),list(hi),flush=True)
for o in obs:
    mod=o.modifiers.new('realtime_lod','DECIMATE');mod.ratio=.12
    print('MESH',o.name,len(o.data.polygons),flush=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('World');scene.world.color=(.45,.45,.45)
d=bpy.data.lights.new('Key','AREA');d.energy=1000*extent**2;d.size=extent*2;o=bpy.data.objects.new('Key',d);scene.collection.objects.link(o);o.location=center+Vector((extent,-extent,extent*2));o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('Camera');c=bpy.data.objects.new('Camera',cd);scene.collection.objects.link(c);scene.camera=c;cd.type='ORTHO';cd.ortho_scale=extent*1.2
for label,v in [('front_y',(0,-2,.3)),('side_x',(2,0,.3))]:
    c.location=center+Vector(v)*extent;c.rotation_euler=(center-c.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(R/'previews'/('open_head_'+label+'.png'));bpy.ops.render.render(write_still=True)
