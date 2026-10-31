"""Prepare licensed assets for the common scene units, axes and real-time budget."""
import bpy,math,json,sys
from mathutils import Vector,Matrix
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'external_assets';W=R.parent/'_work/dragonboat'
human_only='--human-only' in sys.argv
if human_only:
    bpy.ops.wm.open_mainfile(filepath=str(E/'prepared_open_assets.blend'))
    for o in list(bpy.data.objects):
        if o.name.startswith('open_human'):bpy.data.objects.remove(o,do_unlink=True)
else:bpy.ops.wm.read_factory_settings(use_empty=True)
stats=[]
def bounds(obs):
    ps=[o.matrix_world@Vector(v) for o in obs for v in o.bound_box]
    return Vector([min(p[i] for p in ps) for i in range(3)]),Vector([max(p[i] for p in ps) for i in range(3)])
def bake(o,xf=Matrix.Identity(4),ratio=1):
    if ratio<1:
        mod=o.modifiers.new('realtime_LOD','DECIMATE');mod.ratio=ratio
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
    m=bpy.data.meshes.new_from_object(o.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg)
    m.transform(xf@o.matrix_world);m.update();o.parent=None;o.matrix_world=Matrix.Identity(4);o.modifiers.clear();o.data=m
def collect(prefix,obs):
    for i,o in enumerate(obs):o.name=prefix+'__'+str(i)
    used={m for o in obs for m in o.data.materials if m}
    for mat in used:
        mat.name=prefix+'_'+mat.name
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type=='TEX_IMAGE' and node.image and node.image.size[0]>0:
                    im=node.image
                    if not im.get('prepared_file'):
                        name=prefix+'_'+im.name.replace('/','_').replace('\\','_').split('.')[0]+'.png'
                        im.filepath_raw=str(R/'textures'/name);im.file_format='PNG';im.save();im.pack();im['prepared_file']=name
    for o in obs:o.data.calc_loop_triangles()
    stats.append({'asset':prefix,'meshes':len(obs),'triangles':sum(len(o.data.loop_triangles) for o in obs)})

if not human_only:
    # CalWhite's hand-modeled Chinese dragon head, CC BY 4.0. Forward -Y -> +X.
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(E/'chinese_dragon_head/chinese_dragon_head.glb'))
    obs=[o for o in set(bpy.data.objects)-before if o.type=='MESH']
    xf=Matrix.Translation((6.34,0,1.626))@Matrix.Rotation(math.pi/2,4,'Z')@Matrix.Scale(.13,4)
    for o in obs:bake(o,xf,.12)
    collect('open_head',obs)

    # Poly Haven's real branch and foliage mesh. Reduce geometry while keeping UVs.
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(E/'tree_small_02/tree_small_02_1k.gltf'))
    obs=[o for o in set(bpy.data.objects)-before if o.type=='MESH'];lo,hi=bounds(obs);s=4.2/(hi.z-lo.z)
    xf=Matrix.Scale(s,4)@Matrix.Translation((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))
    for o in obs:bake(o,xf,.038)
    collect('open_tree',obs)

    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(E/'rock_moss_set_01/rock_moss_set_01_1k.gltf'))
    obs=[o for o in set(bpy.data.objects)-before if o.type=='MESH']
    # Choose one stone when the library has separate stones, otherwise keep the set as a cluster.
    if len(obs)>1:
        keep=max(obs,key=lambda o:o.dimensions.x*o.dimensions.y*o.dimensions.z)
        for o in obs:
            if o!=keep:bpy.data.objects.remove(o,do_unlink=True)
        obs=[keep]
    lo,hi=bounds(obs);s=1.4/max(hi.x-lo.x,hi.y-lo.y)
    xf=Matrix.Scale(s,4)@Matrix.Translation((-(lo.x+hi.x)/2,-(lo.y+hi.y)/2,-lo.z))
    for o in obs:bake(o,xf,.55)
    collect('open_rock',obs)

# The CC0 MakeHuman meshes retain skin UVs, clothing, hair, eyes and eyebrows.
_human_file=W/'human_base.blend'
if not _human_file.exists():_human_file=E/'makehuman_cc0/athlete_rigged_cc0.blend'
with bpy.data.libraries.load(str(_human_file),link=False) as (src,dst):dst.objects=src.objects
human_objects=[o for o in dst.objects if o]
for o in human_objects:bpy.context.collection.objects.link(o)
rig=next(o for o in human_objects if o.type=='ARMATURE')
source_meshes=[o for o in human_objects if o.type=='MESH']
for kind in ('seated','standing','drummer'):
    for b in rig.pose.bones:
        b.matrix_basis=Matrix.Identity(4)
        for c in list(b.constraints):b.constraints.remove(c)
    S=1.10;hip=.74357736;zoffset=(.18-hip*S) if kind in ('seated','drummer') else 0
    transform=Matrix.Translation((0,0,zoffset))@Matrix.Rotation(math.pi/2,4,'Z')@Matrix.Scale(S,4)
    inv=transform.inverted();targets=[]
    def ik(bone,modelpoint,chain,pole=None):
        o=bpy.data.objects.new('pose_target',None);bpy.context.collection.objects.link(o);o.location=inv@Vector(modelpoint);targets.append(o)
        c=rig.pose.bones[bone].constraints.new('IK');c.target=o;c.chain_count=chain;c.iterations=500
        if pole:
            p=bpy.data.objects.new('pose_pole',None);bpy.context.collection.objects.link(p);p.location=inv@Vector(pole);targets.append(p);c.pole_target=p;c.pole_angle=-math.pi/2
    for side,s in [('L',1),('R',-1)]:
        h=(.36,s*.22,.62) if kind=='drummer' else ((.30,.18,.65+(0.10 if s<0 else 0)) if kind=='seated' else (.30,s*.25,1.28))
        ik('lowerarm02.'+side,h,4)
        if kind in ('seated','drummer'):ik('lowerleg02.'+side,(.40,s*.12,-.12),4,(.90,s*.12,.35))
        for b in rig.pose.bones:
            if b.name.startswith('finger') and b.name.endswith('.'+side):
                b.rotation_mode='XYZ';b.rotation_euler[0]=.65
    bpy.context.view_layer.update()
    copies=[]
    for o in source_meshes:
        n=o.copy();n.data=o.data.copy();bpy.context.collection.objects.link(n)
        # Copy still refers to the posed source armature; evaluate before removing modifiers.
        bake(n,transform);copies.append(n)
    collect('open_human_'+kind,copies)
    for b in rig.pose.bones:
        for c in list(b.constraints):b.constraints.remove(c)
    for o in targets:bpy.data.objects.remove(o,do_unlink=True)
for o in human_objects:
    if o.name in bpy.data.objects:bpy.data.objects.remove(o,do_unlink=True)
# Source import empties are no longer needed; prepared meshes have identity transforms.
for o in list(bpy.data.objects):
    if o.type!='MESH':bpy.data.objects.remove(o,do_unlink=True)
stats=[]
for prefix in ('open_head','open_tree','open_rock','open_human_seated','open_human_standing','open_human_drummer'):
    group=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(prefix+'__')]
    for o in group:o.data.calc_loop_triangles()
    stats.append({'asset':prefix,'meshes':len(group),'triangles':sum(len(o.data.loop_triangles) for o in group)})
(E/'preparation.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(E/'prepared_open_assets.blend'))
print('PREPARED_OPEN_ASSETS',json.dumps(stats),flush=True)
