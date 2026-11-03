import bpy,math,json
from pathlib import Path
from mathutils import Vector
r=Path.cwd();bpy.ops.wm.open_mainfile(filepath=str(r/'models/helmsman_steering.blend'));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');oar=bpy.data.objects['steering_oar_animated'];rows=[];maximum=0
for phase in (0,.125,.25,.375,.5,.625,.75,.875,1):
 frame=1+phase*126;bpy.context.scene.frame_set(int(frame),subframe=frame%1);bpy.context.view_layer.update()
 palms=[rig.matrix_world@rig.pose.bones['wrist.'+side].tail for side in ('L','R')]
 grips=[oar.matrix_world@Vector((0,y,0)) for y in (.12,-.10)]
 error=min(max((palms[0]-grips[0]).length,(palms[1]-grips[1]).length),max((palms[0]-grips[1]).length,(palms[1]-grips[0]).length))
 maximum=max(maximum,error);rows.append(dict(phase=phase,palm_error_m=error))
report=dict(status='PASS' if maximum<.002 else 'FAIL',timeline_frames=127,fps=30,cycle_seconds=4.2,maximum_palm_error_m=maximum,samples=rows)
(r/'results/steering_authoring_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('STEERING_AUTHORING',json.dumps(report),flush=True)
assert report['status']=='PASS'
