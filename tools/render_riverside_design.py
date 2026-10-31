"""Inspect the bank assets before expensive model exports."""
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world.use_nodes=True;configure_open_environment(scene.world)
d=bpy.data.lights.new('ReviewLight','AREA');d.energy=3500;d.size=12
o=bpy.data.objects.new('ReviewLight',d);scene.collection.objects.link(o);o.location=(0,-12,19);o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
cd=bpy.data.cameras.new('ReviewCamera');cam=bpy.data.objects.new('ReviewCamera',cd);scene.collection.objects.link(cam);scene.camera=cam
def shot(name,loc,target,lens=48):
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='PERSP';cd.lens=lens
    scene.render.filepath=str(PRE/name);bpy.ops.render.render(write_still=True)
shot('11_huizhou_overview.png',(32,-44,22),(0,4,3),35)
shot('06_riverside_architecture.png',(-22,7.85,1.75),(1,8.4,2.6),32)
shot('07_finish_and_bridge.png',(9,-18,12),(19,0,2.2),45)
shot('08_festival_stall.png',(-6,-3,4.5),(-10,-9.1,1.2),55)
shot('09_mooring_dock.png',(-5,1,6),(-12,-5.3,.7),52)
shot('13_huizhou_courtyard.png',(-13,13.3,10),(-14.4,16.25,1.5),42)
shot('14_weathered_quay.png',(2,-1,3.3),(4,-6.6,.55),40)
print('RIVERSIDE_PREVIEW_READY',flush=True)
