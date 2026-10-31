"""Reproducible refinement of the accepted panorama, preserving boat assets.

The original .blend is backed up outside Project once. Every run starts there,
so repeated execution never bends or displaces geometry twice.
"""
import bpy,ast,json,math,random,sys,shutil
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];MODELS=ROOT/'models';PRE=ROOT/'previews'
sys.path.insert(0,str(ROOT/'tools'))
from river_routes import *
BACKUP=ROOT.parent/'_work/dragonboat/before_river_refinement'
BACKUP.mkdir(parents=True,exist_ok=True)
if not (BACKUP/'dragonboat_models.blend').exists():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
    existing=bpy.data.objects.get('world_export')
    if existing and any(r.get('river_refinement') for r in existing.children):
        raise RuntimeError('This delivered scene is already refined. Keep it as-is, or rebuild the straight base with build_models.py before creating a new refinement baseline.')
    shutil.copy2(ROOT/'dragonboat_models.blend',BACKUP/'dragonboat_models.blend')
    shutil.copy2(MODELS/'inventory.json',BACKUP/'inventory.json')
bpy.ops.wm.open_mainfile(filepath=str(BACKUP/'dragonboat_models.blend'))
source=(ROOT/'tools/build_models.py').read_text(encoding='utf-8')
helpers={'material','finish','mesh','empty','begin','parent_new','root_asset','descendants','evaluated','export_obj','arr'}
for n in ast.parse(source).body:
    if isinstance(n,ast.FunctionDef) and n.name in helpers:exec(compile(ast.Module(body=[n],type_ignores=[]),'build_models.py','exec'),globals())
M={m.name:m for m in bpy.data.materials if m.use_nodes}
inventory=json.loads(((MODELS if '--reuse-obj' in sys.argv else BACKUP)/'inventory.json').read_text());assets={i['file'][:-4]:bpy.data.objects.get(i['file'][:-4]) for i in inventory}
worldroot=bpy.data.objects['world_export'];bpy.context.view_layer.update()
continuous={'river_surface','panorama_terrain','panorama_farmland','panorama_streets','bank_ground','distant_hills','quay_segment','quay_weathered_b','quay_access','street_gutter'}
warped=0;rigid=0
for root in list(worldroot.children):
    asset=root.get('asset','')
    if root.name.startswith('dragon_boat_') or asset=='panorama_sky':continue
    if asset in continuous:
        for o in root.children_recursive:
            if o.type!='MESH':continue
            # Scene-only copies: source prototypes and both boats stay untouched.
            o.data=o.data.copy();xf=o.matrix_world.copy();inv=xf.inverted()
            # Long pavement and ground boxes need intermediate vertices;
            # bending only their endpoints would cut diagonally across the town.
            import bmesh
            bm=bmesh.new();bm.from_mesh(o.data)
            long_edges=[e for e in bm.edges if (xf.to_3x3()@(e.verts[1].co-e.verts[0].co)).length>5]
            if long_edges:
                cuts=min(120,max(1,math.ceil(max((xf.to_3x3()@(e.verts[1].co-e.verts[0].co)).length for e in long_edges)/1.3)-1))
                bmesh.ops.subdivide_edges(bm,edges=long_edges,cuts=cuts,use_grid_fill=True)
                bm.to_mesh(o.data)
            bm.free()
            for v in o.data.vertices:
                p=xf@v.co;v.co=inv@Vector(warp(*p))
            o.data.update();warped+=1
    else:
        old=root.location.copy();root.location=warp(*old)
        root.rotation_euler.z+=tangent(old.x)
        rigid+=1
    root['river_refinement']='bent mesh' if asset in continuous else 'rigid placement'

# Replace river surface with a dense, nearly level ribbon, not mountainous water.
river=next(r for r in worldroot.children if r.get('asset')=='river_surface')
for o in reversed(descendants(river)):bpy.data.objects.remove(o,do_unlink=True)
material('river_silt',(.23,.22,.15),'huizhou_soil.png',rough=.96)
material('river_gravel',(.31,.32,.27),'huizhou_soil.png',rough=.92)

def grid(name,x0,x1,nx,ny,point,mat):
    vs=[point(x0+(x1-x0)*i/nx,j/ny) for i in range(nx+1) for j in range(ny+1)]
    fs=[]
    for i in range(nx):
        for j in range(ny):
            a=i*(ny+1)+j;fs.append((a,a+ny+1,a+ny+2,a+1))
    o=mesh(name,vs,fs,mat);uv=o.data.uv_layers.new(name='UVMap')
    for p in o.data.polygons:
        p.use_smooth=True
        for li in p.loop_indices:
            v=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(v.x/3,v.y/3)
    return o

newroot=empty('river');newroot.parent=worldroot;newroot['asset']='river_surface'
o=grid('bending_river_surface',-420,420,840,24,
       lambda x,t:(x,river_center(x)+(2*t-1)*half_width(x),-.06+.009*math.sin(x*1.2+t*12)), 'water');o.parent=newroot
detail=empty('natural_riverbed_and_banks');detail.parent=worldroot;detail['asset']='natural_riverbed'
o=grid('scoured_uneven_riverbed',-420,420,840,28,
       lambda x,t:(x,river_center(x)+(2*t-1)*(half_width(x)+3),-.40-1.10*math.sin(math.pi*t)**.65+.09*math.sin(x*.63+t*8)+.04*math.sin(x*1.3-t*21)), 'river_silt');o.parent=detail
from mathutils.bvhtree import BVHTree
bpy.context.view_layer.update();ground_vs=[];ground_fs=[]
for r in worldroot.children:
    if r.get('asset') not in ('panorama_terrain','bank_ground','distant_hills'):continue
    for obj in r.children_recursive:
        if obj.type!='MESH':continue
        base=len(ground_vs);ground_vs.extend(obj.matrix_world@v.co for v in obj.data.vertices)
        ground_fs.extend(tuple(base+k for k in p.vertices) for p in obj.data.polygons)
ground_bvh=BVHTree.FromPolygons(ground_vs,ground_fs)
# Extend the water *under* the uneven dry ground. Ending it at a fixed plan
# width leaves a black vertical slit wherever a bank vertex falls below water.
surface=next(o for o in newroot.children if o.type=='MESH')
wet_widths={}
for v in surface.data.vertices:
    x=v.co.x
    if x<=82:continue
    key=round(x,4)
    if key not in wet_widths:
        widths=[]
        for side in (-1,1):
            d=half_width(x)
            for k in range(45):
                d=half_width(x)+k*.25
                h,_,_,_=ground_bvh.ray_cast(Vector((x,river_center(x)+side*d,50)),Vector((0,0,-1)),100)
                if h and h.z>.14:break
            widths.append(d+.35)
        wet_widths[key]=widths
    t=(v.co.y-river_center(x))/half_width(x)
    v.co.y=river_center(x)+t*wet_widths[key][0 if t<0 else 1]
surface.data.update()
for r in worldroot.children:
    if r.get('asset')!='panorama_terrain':continue
    for o in r.children_recursive:
        if o.type!='MESH':continue
        o.data.materials.append(M['river_gravel']);slot=len(o.data.materials)-1
        for p in o.data.polygons:
            co=o.matrix_world@p.center
            if 84<co.x<240 and abs(co.y-river_center(co.x))<half_width(co.x)+4.3:p.material_index=slot
def shoreline_point(x,t,side):
    d=half_width(x)-.5+2.6*t;y=river_center(x)+side*d
    hit,_,_,_=ground_bvh.ray_cast(Vector((x,y,50)),Vector((0,0,-1)),100)
    base=hit.z if hit else -.08
    blend=smooth(t/.85)
    z=(-.32)*(1-blend)+(base-.035)*blend
    return (x,y,z)
# The visible shore uses the existing ground surface's gravel material, rather
# than a second coplanar skin (which produces dark seams in low-angle views).
# Pebble geometry is deliberately irregular, modest in size and concentrated at
# the shoreline. No copied unlicensed photographs are used as texture maps.
rng=random.Random(425)
vs=[];fs=[]
for side in (-1,1):
    for i in range(240):
        x=rng.uniform(85,205);d=half_width(x)+rng.uniform(.25,1.3);y=river_center(x)+side*d
        hit,_,_,_=ground_bvh.ray_cast(Vector((x,y,50)),Vector((0,0,-1)),100)
        z=hit.z+.015 if hit else -.12
        rx=rng.uniform(.08,.36);ry=rx*rng.uniform(.5,1.2);rz=rx*rng.uniform(.28,.65);base=len(vs)
        for j in range(8):
            a=2*math.pi*j/8;vs.append((x+rx*math.cos(a),y+ry*math.sin(a),z+rng.uniform(-.025,.025)))
        vs.extend([(x,y,z+rz),(x,y,z-rz*.3)])
        for j in range(8):fs.extend([(base+j,base+(j+1)%8,base+8),(base+(j+1)%8,base+j,base+9)])
o=mesh('scattered_river_pebbles',vs,fs,'river_gravel');o.parent=detail
for p in o.data.polygons:p.use_smooth=True
uv=o.data.uv_layers.new(name='UVMap')
for p in o.data.polygons:
    for li in p.loop_indices:
        v=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(v.x/3,v.y/3)

# The narrow old bridge cannot clear standing crew/flags. Keep the accepted
# bridge design and move the two downstream crossings beyond the animated run.
for name,x in [('bridge',122),('pano_bridge_64',164)]:
    root=bpy.data.objects.get(name)
    if root:
        root.location=(x,river_center(x),0);root.rotation_euler.z=tangent(x)
        root['relocated_for_boat_clearance']=True

bpy.context.view_layer.update();scene_roots=list(worldroot.children)
from add_valley_closure import add_valley_closure
ridge=add_valley_closure(worldroot);bpy.context.view_layer.update();scene_roots=list(worldroot.children)
from make_natural_banks import make_natural_banks
_,bank_edges=make_natural_banks(worldroot);bpy.context.view_layer.update();scene_roots=list(worldroot.children)
CV=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
cam=scene.camera;cam.data.clip_end=2000
exec((ROOT/'tools/configure_render_device.py').read_text(encoding='utf-8'),globals())
def shot(name,loc,target,lens=35):
    scene.render.resolution_x=1600;scene.render.resolution_y=1000;cam.data.type='PERSP';cam.data.lens=lens
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(PRE/(name+'.png'));render_preview_frame()
def previews():
    configure_preview_device()
    if '--bank-only' in sys.argv:
        shot('22_natural_riverbank',(111,9,3.8),(126,19,0),35);return
    shot('21_bending_river_aerial',(125,-110,100),(65,12,0),36)
    shot('22_natural_riverbank',(111,9,3.8),(126,19,0),35)
    shot('23_downstream_drone',(50,-19,15),(80,20,1),28)
    if '--preview-only' in sys.argv:return
    shot('11_huizhou_overview',(32,-44,22),(0,4,3),35);shutil.copy2(PRE/'11_huizhou_overview.png',PRE/'01_scene_overview.png')
    shot('20_panorama_aerial',(115,-145,112),(25,8,2),35)
    shot('16_view_east',(-8,0,9),(70,0,8),32)
    shot('07_finish_and_bridge',(106,-18,13),(122,river_center(122),2),35)
    scene.render.resolution_x=2560;scene.render.resolution_y=1280;cam.data.type='PANO';cam.data.panorama_type='EQUIRECTANGULAR'
    cam.location=(0,0,6);cam.rotation_euler=Vector((1,0,0)).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(PRE/'15_environment_360.png');render_preview_frame()
if '--preview-only' in sys.argv:
    previews();print('RIVER_PREVIEW_READY',flush=True);raise SystemExit(0)

# Whole scene is the authoritative exported curved environment. Original
# reusable component OBJ files keep their straight, local modelling coordinates.
for name,root in [('river_surface',newroot),('natural_riverbed',detail),('panorama_valley_closure',ridge),('eroded_riverbank_faces',bank_edges),('scene_preview',worldroot)]:
    if '--reuse-obj' in sys.argv:
        assert (MODELS/(name+'.obj')).exists() and any(i['file']==name+'.obj' for i in inventory)
        continue
    item=export_obj(name,root);inventory=[i for i in inventory if i['file']!=item['file']];inventory.append(item)
(MODELS/'inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
exec((ROOT/'tools/restore_texture_paths.py').read_text(encoding='utf-8'),globals());restore_material_image_paths()
exec(source[source.index('mtl=[]'):source.index('# Scene graph contains')],globals())
nodes=[]
for root in scene_roots:
    for o in descendants(root):nodes.append({'name':o.name,'parent':o.parent.name if o.parent and o.parent!=worldroot else None,'asset':o.get('asset'),'type':o.type,'render_mode':o.get('render_mode'),'scene_mesh_deformed':root.get('river_refinement')=='bent mesh','local_matrix_zup':[arr(row) for row in o.matrix_local],'world_matrix_yup':[arr(row) for row in CV@o.matrix_world@CV.inverted()]})
(MODELS/'scene_layout.json').write_text(json.dumps({'units':'metres','obj_axes':'Y up, +X forward','scene_internal_axes':'Z up','deformed_environment':'Use scene_preview.obj groups or GLB mesh geometry, not straight source prototypes.','nodes':nodes},ensure_ascii=False,indent=2),encoding='utf-8')
for im in bpy.data.images:
    if im.source=='FILE' and im.size[0]>0:
        # World HDR images are outside material node trees and therefore need
        # their own path recovery after opening the backup in another folder.
        path=Path(bpy.path.abspath(im.filepath))
        if not path.is_file():
            rel=im.filepath[2:] if im.filepath.startswith('//') else ''
            candidate=ROOT/rel.replace('\\','/') if rel else ROOT/'external_assets'/path.name
            if candidate.is_file():im.filepath_raw=str(candidate)
            elif im.packed_file:continue
        if not im.packed_file:im.pack()
for o in list(bpy.context.selected_objects):o.select_set(False)
for o in descendants(worldroot):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(MODELS/'dragonboat_scene.glb'),use_selection=True,export_format='GLB',export_apply=True)
exec((ROOT/'tools/fix_sky_glb.py').read_text(encoding='utf-8'),globals());ensure_unlit_sky(MODELS/'dragonboat_scene.glb')
for o in list(bpy.context.selected_objects):o.select_set(False)
cam.data.type='PERSP';cam.data.lens=36;cam.location=(125,-110,100);cam.rotation_euler=(Vector((65,12,0))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.context.preferences.filepaths.save_version=0;scene.cycles.device='CPU';bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
previews()
print('RIVER_REFINEMENT_COMPLETE',json.dumps({'mesh_objects_warped':warped,'rigid_roots':rigid,'obj_files':len(inventory),'triangles':inventory[-1]['triangles']}),flush=True)
