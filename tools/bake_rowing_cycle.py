"""Bake the CC0 athlete's IK rowing cycle; Blender is an authoring dependency only.

The runtime interpolates a fixed topology pose sequence, sharing it across all
rowers. Paddle and hand targets use the same six-key closed stroke trajectory.
No scene geometry or original Blender assembly is overwritten.
"""
import bpy, math, struct, json, sys
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
DRUM='--drum' in sys.argv
ROLE='drumming' if DRUM else 'rowing'
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(ROOT/'external_assets/makehuman_cc0/athlete_rigged_cc0.blend'), link=False) as (src,dst):
    dst.objects=src.objects
objects=[o for o in dst.objects if o]
for o in objects: bpy.context.collection.objects.link(o)
rig=next(o for o in objects if o.type=='ARMATURE')
meshes=[o for o in objects if o.type=='MESH']
S=1.10
transform=Matrix.Translation((0,0,.18-.74357736*S)) @ Matrix.Rotation(math.pi/2,4,'Z') @ Matrix.Scale(S,4)
inv=transform.inverted()
CV=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
for b in rig.pose.bones:
    b.matrix_basis=Matrix.Identity(4)
    for c in list(b.constraints): b.constraints.remove(c)
    if b.name.startswith('finger'):
        b.rotation_mode='XYZ'; b.rotation_euler[0]=.65

def ik(bone, point, chain, pole=None):
    target=bpy.data.objects.new('target_'+bone,None); bpy.context.collection.objects.link(target)
    target.location=inv@Vector(point)
    c=rig.pose.bones[bone].constraints.new('IK'); c.target=target; c.chain_count=chain; c.iterations=500
    if pole:
        p=bpy.data.objects.new('pole_'+bone,None); bpy.context.collection.objects.link(p); p.location=inv@Vector(pole)
        c.pole_target=p; c.pole_angle=-math.pi/2
    return target

hands={}; hand_bones={}
for side,s in [('L',1),('R',-1)]:
    shoulder=transform@rig.data.bones['upperarm01.'+side].head_local
    # The outside hand holds the shaft; the inside hand holds the T grip.
    key='bottom' if shoulder.y>0 else 'top'
    bone=('wrist.' if 'wrist.'+side in rig.pose.bones else 'hand.')+side
    if bone not in rig.pose.bones: bone='lowerarm02.'+side
    hands[key]=ik(bone,(.3,.3,.7),7 if bone.startswith(('wrist','hand')) else 6)
    hand_bones[key]=bone
    ik('lowerleg02.'+side,(.40,s*.12,-.12),4,(.90,s*.12,.35))

KEYS=[(0,24,-.13,.10,0),(.10,22,-.22,.06,0),(.50,-20,-.20,-.10,1),(.64,-25,.10,-.10,17),(.83,3,.14,.03,18),(1,24,-.13,.10,0)]
def stroke(phase):
    for a,b in zip(KEYS,KEYS[1:]):
        if phase<=b[0]:
            f=(phase-a[0])/(b[0]-a[0]); f=f*f*(3-2*f)
            return [a[i]*(1-f)+b[i]*f for i in (1,2,3,4)]
def paddle_point(z, phase):
    angle,dy,dx,feather=stroke(phase); a=math.radians(angle); tilt=.4+math.radians(feather)
    # Z-up paddle root relative to athlete, already tilted outboard by .4 rad.
    x=.42; y=.26-math.sin(tilt)*z; h=.69+math.cos(tilt)*z
    return Vector((x+dx-math.sin(a)*(h-.69),y,.69+dy+math.cos(a)*(h-.69)))

DRUM_KEYS=[(0,28,.04),(.05,0,0),(.10,20,.035),(.32,58,.11),(.65,54,.10),(.88,48,.08),(1,28,.04)]
def drum_motion(phase):
    phase%=1
    for a,b in zip(DRUM_KEYS,DRUM_KEYS[1:]):
        if phase<=b[0]:
            f=(phase-a[0])/(b[0]-a[0]); f=f*f*(3-2*f)
            return (a[1]*(1-f)+b[1]*f,a[2]*(1-f)+b[2]*f)
def drum_palm(key,phase):
    side=-1 if key=='bottom' else 1
    angle,lift=drum_motion(phase+(.5 if side<0 else 0))
    # Boat grip (3.89+lift, +/- .22, 1.77+lift), inverse of stern-facing root.
    return Vector((.36-lift,-side*.22,.62+lift))

frames=[]; topology=[]; names=[]; errors=[]; F=40
for fi in range(F+1):
    phase=fi/F
    for b in rig.pose.bones:
        if not b.name.startswith('finger'): b.matrix_basis=Matrix.Identity(4)
    # Hinge the torso from the hips; leg IK keeps the seated feet in place.
    lean=math.radians((3+2*math.cos(phase*4*math.pi)) if DRUM else (12+22*(.5+.5*math.cos(phase*2*math.pi))))
    spine=rig.pose.bones.get('spine03')
    if spine:
        pivot=transform@spine.bone.head_local
        bend=Matrix.Translation(pivot)@Matrix.Rotation(lean,4,'Y')@Matrix.Translation(-pivot)
        spine.matrix=inv@bend@transform@spine.bone.matrix_local
    for key,z in [('top',.12),('bottom',-.30)]:
        hands[key].location=inv@(drum_palm(key,phase) if DRUM else paddle_point(z,phase))
    bpy.context.view_layer.update(); dg=bpy.context.evaluated_depsgraph_get()
    errors.append({key:(transform@rig.pose.bones[hand_bones[key]].tail-transform@hands[key].location).length for key in hands})
    if fi==0 and '--audit' in sys.argv:
        for key in hands:
            print('TARGET',key,list(drum_palm(key,phase) if DRUM else paddle_point(.12 if key=='top' else -.30,phase)),flush=True)
            b=rig.pose.bones[hand_bones[key]]
            for _ in range(7):
                print('CHAIN',b.name,list(transform@b.head),list(transform@b.tail),'lock',b.lock_ik_x,b.lock_ik_y,b.lock_ik_z,flush=True)
                b=b.parent
    if '--audit' in sys.argv: continue
    packed=[]; parts=[]
    for mi,o in enumerate(meshes):
        evaluated=o.evaluated_get(dg); mesh=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=dg)
        mesh.calc_loop_triangles(); xf=CV@transform@o.matrix_world; normal=xf.to_3x3().inverted().transposed()
        # Expanded triangle corners preserve skin UV seams and constant topology.
        for tri in mesh.loop_triangles:
            material=o.data.materials[tri.material_index]
            name='open_human_seated_'+material.name
            if fi==0 and name not in names: names.append(name)
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

if '--audit' in sys.argv:
    audit={'max_wrist_target_error_m':max(v for row in errors for v in row.values()),'per_phase':errors}
    (ROOT/('results/'+ROLE+'_ik_audit.json')).write_text(json.dumps(audit,indent=2),encoding='utf8')
    print('IK_AUDIT',audit['max_wrist_target_error_m'],flush=True)
    sys.exit(0)
out=ROOT/('models/'+ROLE+'_cycle.bin')
with out.open('wb') as f:
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
(ROOT/('models/'+ROLE+'_cycle.json')).write_text(json.dumps({'frames':F,'vertices':count,'materials':names,'closed_cycle_max_error_m':closure,'max_palm_target_error_m':max_error,'source':'MakeHuman CC0 rig; analytic grip path + Blender arm/leg IK','phase_keys':DRUM_KEYS if DRUM else KEYS},ensure_ascii=False,indent=2),encoding='utf8')
print('BAKED',out,closure,flush=True)
