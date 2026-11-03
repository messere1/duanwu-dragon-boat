"""Rigid palm sockets fitted to the visible finger surfaces, in source rig space."""
import json
from pathlib import Path
from mathutils import Vector,Matrix
from steering_motion import steering_frame
PROFILE=json.loads((Path(__file__).resolve().parents[1]/'models/steering_grasp.json').read_text())
ROOT_OFFSET=Vector((-4.12,.91,0))

def finger_pose(rig):
    for b in rig.pose.bones:
        if b.name.startswith('finger'):
            digit,joint=map(int,b.name.split('.')[0][6:].split('-'))
            b.rotation_mode='XYZ'
            b.rotation_euler=(0,0,0)
            b.rotation_euler[0]=0 if digit==1 else PROFILE[b.name[-1]]['angles'][joint-1]

def socket_local(rig,side):
    return rig.data.bones['wrist.'+side].matrix_local.inverted()@Vector(PROFILE[side]['socket'])

def set_grasp_target(rig,target,side,key,phase,actor_to_yup):
    p=PROFILE[side];canonical=Matrix([p['row'],p['long'],p['normal']]).transposed()
    upper,lower,d=map(Vector,steering_frame(phase));out=Vector((0,0,1));x=d.cross(out).normalized()
    if key=='top':row=x;normal=-d;grip=upper
    else:row=-d;normal=(out-d*out.dot(d)).normalized();grip=lower
    long=normal.cross(row).normalized();desired=Matrix([row,long,normal]).transposed()@canonical.transposed()
    tail=grip+1.1*(desired@(rig.data.bones['wrist.'+side].tail_local-Vector(p['socket'])))
    target.location=actor_to_yup.inverted()@(tail-ROOT_OFFSET)
    rotation=actor_to_yup.to_3x3().normalized().inverted()@desired@rig.data.bones['wrist.'+side].matrix_local.to_3x3()
    target.rotation_mode='QUATERNION';target.rotation_quaternion=rotation.to_quaternion()
    return grip

def actual_socket(rig,side,actor_to_yup):
    return actor_to_yup@(rig.pose.bones['wrist.'+side].matrix@socket_local(rig,side))+ROOT_OFFSET
