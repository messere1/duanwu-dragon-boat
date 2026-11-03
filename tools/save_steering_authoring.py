"""Called after the steering bake to retain editable rig/IK/oar keyframes."""
from mathutils import Vector,Matrix

def read_obj_mesh(name):
 vs=[];fs=[]
 for line in (ROOT/'models'/name).open(encoding='utf8'):
  if line.startswith('v '):vs.append(tuple(map(float,line.split()[1:])))
  elif line.startswith('f '):fs.append(tuple(int(t.split('/')[0])-1 for t in line.split()[1:]))
 return vs,fs
v,f=read_obj_mesh('paddle.obj');data=bpy.data.meshes.new('steering_oar_reference_mesh');data.from_pydata(v,[],f);data.update();oar=bpy.data.objects.new('steering_oar_animated',data);bpy.context.collection.objects.link(oar);oar.rotation_mode='QUATERNION'
wood=bpy.data.materials.new('steering_oar_wood');wood.diffuse_color=(.27,.18,.095,1);data.materials.append(wood)
spine=rig.pose.bones.get('spine03');spine.rotation_mode='QUATERNION'
for fi in range(F+1):
 phase=fi/F;frame=1+phase*126
 for b in rig.pose.bones:
  if not b.name.startswith('finger'):b.matrix_basis=Matrix.Identity(4)
 pivot=transform@spine.bone.head_local;lean=math.radians(5+3*math.sin(phase*math.tau));yaw=math.radians(-18+4*math.sin(phase*math.tau))
 spine.matrix=inv@Matrix.Translation(pivot)@Matrix.Rotation(yaw,4,'Z')@Matrix.Rotation(lean,4,'Y')@Matrix.Translation(-pivot)@transform@spine.bone.matrix_local
 for key in hands:
  hands[key].location=inv@steering_palm(key,phase);hands[key].keyframe_insert(data_path='location',frame=frame)
 for prop in ('location','rotation_quaternion','scale'):spine.keyframe_insert(data_path=prop,frame=frame)
 g,h,d=map(Vector,steering_frame(phase));x=d.cross(Vector((0,0,1))).normalized();z=x.cross(d);p=g-d*(.12*1.95)
 model=Matrix(((x.x*.9,d.x*1.95,z.x*.9,p.x),(x.y*.9,d.y*1.95,z.y*.9,p.y),(x.z*.9,d.z*1.95,z.z*.9,p.z),(0,0,0,1)))
 oar.matrix_world=CV.inverted()@model
 for prop in ('location','rotation_quaternion','scale'):oar.keyframe_insert(data_path=prop,frame=frame)
actor=bpy.data.objects.new('standing_helmsman_in_boat_space',None);bpy.context.collection.objects.link(actor)
for obj in list(bpy.context.scene.objects):
 if obj not in (actor,oar) and obj.parent is None:obj.parent=actor
actor.matrix_world=Matrix.Translation((-4.12,0,.91))@transform
# Keep a physical stern/deck reference for checking the editable steering pose.
v,f=read_obj_mesh('boat_hull_red.obj');f=[face for face in f if max(v[i][0] for i in face)<-2.8];m=bpy.data.meshes.new('stern_platform_reference');m.from_pydata(v,[],f);m.update();stern=bpy.data.objects.new('stern_platform_reference',m);bpy.context.collection.objects.link(stern);stern.matrix_world=CV.inverted();m.materials.append(wood)
for action in bpy.data.actions:
 for curve in action.fcurves:
  for key in curve.keyframe_points:key.interpolation='LINEAR'
for im in bpy.data.images:
 if im.source=='FILE' and im.size[0]>0 and not im.packed_file:im.pack()
scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=127;scene.render.fps=30;scene.frame_set(1)
for obj in list(bpy.context.selected_objects):obj.select_set(False)
rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models/helmsman_steering.blend'));print('EDITABLE_STEERING_ACTION_SAVED',flush=True)
