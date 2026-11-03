"""Bake a standing helmsman linked to an aft/outboard steering oar.

The ankle targets remain planted; surface-fitted palm sockets share the oar path.
Exports a closed pose sequence plus an editable Blender IK action.
"""
import bpy, math, struct, json, sys
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
DRUM=False
ROLE='steering'
sys.path.insert(0,str(ROOT/'tools'))
from steering_motion import steering_frame
from steering_grasp import finger_pose,set_grasp_target,actual_socket,socket_local
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(ROOT/'external_assets/makehuman_cc0/athlete_rigged_cc0.blend'), link=False) as (src,dst):
    dst.objects=src.objects
objects=[o for o in dst.objects if o]
for o in objects: bpy.context.collection.objects.link(o)
rig=next(o for o in objects if o.type=='ARMATURE')
meshes=[o for o in objects if o.type=='MESH']
S=1.10
transform=Matrix.Translation((0,0,0)) @ Matrix.Rotation(math.pi/2,4,'Z') @ Matrix.Scale(S,4)
inv=transform.inverted()
CV=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
for b in rig.pose.bones:
    b.matrix_basis=Matrix.Identity(4)
    for c in list(b.constraints): b.constraints.remove(c)
finger_pose(rig)

def ik(bone, point, chain, pole=None):
    target=bpy.data.objects.new('target_'+bone,None); bpy.context.collection.objects.link(target)
    target.location=inv@Vector(point)
    c=rig.pose.bones[bone].constraints.new('IK'); c.target=target; c.chain_count=chain; c.iterations=500
    if pole:
        p=bpy.data.objects.new('pole_'+bone,None); bpy.context.collection.objects.link(p); p.location=inv@Vector(pole)
        c.pole_target=p; c.pole_angle=-math.pi/2
    return target

hands={}; hand_bones={};hand_sides={}
for side,s in [('L',1),('R',-1)]:
    shoulder=transform@rig.data.bones['upperarm01.'+side].head_local
    # The outside hand holds the shaft; the inside hand holds the T grip.
    key='top' if shoulder.y>0 else 'bottom'
    bone=('wrist.' if 'wrist.'+side in rig.pose.bones else 'hand.')+side
    if bone not in rig.pose.bones: bone='lowerarm02.'+side
    hands[key]=ik(bone,(.3,.3,.7),7 if bone.startswith(('wrist','hand')) else 6)
    hand_bones[key]=bone;hand_sides[key]=side
    rig.pose.bones[bone].constraints[-1].use_rotation=True
    rig.pose.bones[bone].constraints[-1].orient_weight=1
    ik('lowerleg02.'+side,transform@rig.data.bones['lowerleg02.'+side].tail_local,4)

frames=[]; topology=[]; names=[]; errors=[]; samples=[]; F=40;hand_indices={'L':[],'R':[]}
for fi in range(F+1):
    phase=fi/F
    for b in rig.pose.bones:
        if not b.name.startswith('finger'): b.matrix_basis=Matrix.Identity(4)
    # Hinge the torso from the hips; ankle IK keeps both feet planted.
    lean=math.radians(5+3*math.sin(phase*2*math.pi))
    spine=rig.pose.bones.get('spine03')
    if spine:
        pivot=transform@spine.bone.head_local
        bend=Matrix.Translation(pivot)@Matrix.Rotation(math.radians(-18+4*math.sin(phase*2*math.pi)),4,'Z')@Matrix.Rotation(lean,4,'Y')@Matrix.Translation(-pivot)
        spine.matrix=inv@bend@transform@spine.bone.matrix_local
    targets={key:set_grasp_target(rig,hands[key],hand_sides[key],key,phase,CV@transform) for key in hands}
    bpy.context.view_layer.update(); dg=bpy.context.evaluated_depsgraph_get()
    errors.append({key:(actual_socket(rig,hand_sides[key],CV@transform)-targets[key]).length for key in hands})
    points=[actual_socket(rig,hand_sides[key],CV@transform) for key in ('top','bottom')]
    samples.append([phase,*points[0],*points[1]])
    packed=[]; parts=[]
    for mi,o in enumerate(meshes):
        evaluated=o.evaluated_get(dg); mesh=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=dg)
        mesh.calc_loop_triangles(); xf=CV@transform@o.matrix_world; normal=xf.to_3x3().inverted().transposed()
        # Expanded triangle corners preserve skin UV seams and constant topology.
        for tri in mesh.loop_triangles:
            material=o.data.materials[tri.material_index]
            name='open_human_seated_'+material.name
            if fi==0 and name not in names: names.append(name)
            if fi==0:
                for side in hand_indices:
                    groups={g.index for g in o.vertex_groups if g.name.endswith('.'+side) and g.name.startswith(('wrist','finger'))}
                    if min(sum(g.weight for g in mesh.vertices[i].groups if g.group in groups) for i in tri.vertices)>.20:hand_indices[side].append(len(packed))
            for li in tri.loops:
                loop=mesh.loops[li]; p=xf@mesh.vertices[loop.vertex_index].co; n=(normal@loop.normal).normalized()
                uv=mesh.uv_layers.active.data[li].uv if mesh.uv_layers.active else (0,0)
                packed.append((*p,*n,*uv))
                if fi==0: parts.append(names.index(name))
        evaluated.to_mesh_clear()
    if fi==0: topology=parts; count=len(packed)
    assert len(packed)==count
    frames.append(packed)
    print('POSE',fi,count,flush=True)

(ROOT/'results/steering_ik_audit.json').write_text(json.dumps({'per_phase':errors,'maximum':max(v for row in errors for v in row.values())},indent=2),encoding='utf8')
assert max(v for row in errors for v in row.values())<.002,errors
out=ROOT/('models/'+ROLE+'_cycle.bin')
pending=out.with_name(out.name+'.pending')
with pending.open('wb') as f:
    f.write(struct.pack('<8sIII',b'DBPOSE01',F,count,len(names)))
    for name in names:
        b=name.encode(); f.write(struct.pack('<I',len(b))); f.write(b)
    f.write(struct.pack('<'+'I'*count,*topology))
    for pose in frames[:-1]:
        for v in pose: f.write(struct.pack('<8f',*v))
closure=max((Vector(a[:3])-Vector(b[:3])).length for a,b in zip(frames[0],frames[-1]))
assert closure<.0001,closure
max_error=max(v for row in errors for v in row.values())
assert max_error<.002,max_error
pending.replace(out)
(ROOT/('models/'+ROLE+'_cycle.json')).write_text(json.dumps({'frames':F,'vertices':count,'materials':names,'closed_cycle_max_error_m':closure,'max_palm_target_error_m':max_error,'grip_model':'steering_oar.obj; 24 mm round T grip, 24.57 mm shaft; oriented surface-fitted palm sockets','source':'MakeHuman CC0 standing rig; linked steering oar, oriented wrist IK, planted ankle targets','phase_keys':'4.2 second steering correction cycle; both hands follow the same rigid oar'},ensure_ascii=False,indent=2),encoding='utf8')
(ROOT/'models/steering_hand_indices.json').write_text(json.dumps(hand_indices),encoding='utf8')
print('BAKED',out,closure,flush=True)

(ROOT/'models/steering_samples.csv').write_text('phase,upper_x,upper_y,upper_z,lower_x,lower_y,lower_z\n'+'\n'.join(','.join(f'{v:.9f}' for v in row) for row in samples)+'\n',encoding='utf8')

exec((ROOT/'tools/save_steering_authoring.py').read_text(encoding='utf-8-sig'),globals())
