"""Fast design review before writing the large OBJ/GLB deliverables."""
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=20;scene.cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world.use_nodes=True;configure_open_environment(scene.world)
def light(loc,power,size):
    d=bpy.data.lights.new('ReviewLight','AREA');d.energy=power;d.size=size
    o=bpy.data.objects.new('ReviewLight',d);scene.collection.objects.link(o);o.location=loc;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
light((1,-8,10),2600,8);light((-6,5,6),1300,6)
cd=bpy.data.cameras.new('ReviewCamera');cam=bpy.data.objects.new('ReviewCamera',cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO'
for root in scene_roots:
    if root!=red:
        for o in descendants(root):o.hide_render=True
red.location=(0,0,0);floor=box('ReviewFloor',(0,0,-.65),(200,200,.1),'plaster',0)
def shot(name,loc,target,scale):
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=scale
    scene.render.filepath=str(PRE/name);bpy.ops.render.render(write_still=True)
shot('design_01_boat.png',(10,-15,9),(0,0,1),15)
shot('design_02_bow.png',(10,-9,5),(4.95,0,1.3),5.8)
for o in descendants(red):
    if 'stool' not in o.name and any(k in o.name for k in ('rower','drummer','helmsman','paddle','steering_oar','drumstick')):o.hide_render=True
shot('design_03_structure.png',(6,-10,13),(0,0,.7),14.5)
print('DESIGN_PREVIEW_READY',flush=True)
