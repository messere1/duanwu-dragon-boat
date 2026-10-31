"""Dispersed inland settlement and irregular terrain-conforming field mosaic."""
import bpy,ast,json,math,random,sys,shutil
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];MODELS=ROOT/'models';PRE=ROOT/'previews';sys.path.insert(0,str(ROOT/'tools'))
from river_routes import river_center
backup=ROOT.parent/'_work/dragonboat/before_dispersed_village';backup.mkdir(parents=True,exist_ok=True)
if not (backup/'dragonboat_models.blend').exists():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
    if any(o.get('asset')=='dispersed_village_landuse' for o in bpy.data.objects):
        raise RuntimeError('The delivered village is already dispersed. Edit the saved scene directly, or rebuild an undistributed river scene before creating a fresh baseline.')
    shutil.copy2(ROOT/'dragonboat_models.blend',backup/'dragonboat_models.blend');shutil.copy2(MODELS/'inventory.json',backup/'inventory.json')
if not (backup/'scene_preview.obj').exists():shutil.copy2(MODELS/'scene_preview.obj',backup/'scene_preview.obj')
bpy.ops.wm.open_mainfile(filepath=str(backup/'dragonboat_models.blend'))
source=(ROOT/'tools/build_models.py').read_text(encoding='utf-8')
for n in ast.parse(source).body:
    if isinstance(n,ast.FunctionDef) and n.name in {'mesh','finish','empty','descendants','evaluated','export_obj','arr'}:exec(compile(ast.Module(body=[n],type_ignores=[]),'build_models.py','exec'),globals())
M={m.name:m for m in bpy.data.materials if m.use_nodes};world=bpy.data.objects['world_export'];bpy.context.view_layer.update()
verts=[];faces=[]
for r in world.children:
    if r.get('asset') not in ('panorama_terrain','distant_hills','bank_ground'):continue
    for o in r.children_recursive:
        if o.type!='MESH':continue
        base=len(verts);verts.extend(o.matrix_world@v.co for v in o.data.vertices);faces.extend(tuple(base+k for k in p.vertices) for p in o.data.polygons)
ground=BVHTree.FromPolygons(verts,faces)
def height(x,y):
    p,_,_,_=ground.ray_cast(Vector((x,y,150)),Vector((0,0,-1)),300)
    assert p is not None,(x,y);return p.z

houses=[r for r in world.children if r.get('asset') in {'riverside_house','huizhou_tall_house','huizhou_tea_house','huizhou_courtyard'}]
moved=[r for r in houses if 'back_lane_house' in r.name or 'pano_back_house' in r.name or ('pano_front_house' in r.name and int(r.name.rsplit('_',1)[1])%2==1)]
occupied=[(r.location.x,r.location.y,4.8 if r.get('asset')=='huizhou_courtyard' else 3.9) for r in houses if r not in moved]
rng=random.Random(302320);oldmat={o.name:o.matrix_world.copy() for r in moved for o in descendants(r) if o.type=='MESH'}
centres=[(-61,34),(-26,43),(16,33),(57,48),(-62,-41),(-24,-32),(19,-49),(57,-35)]
placements=[]
for i,r in enumerate(moved):
    cx,cy=centres[i%len(centres)];rad=4.8 if r.get('asset')=='huizhou_courtyard' else 3.9
    for attempt in range(1500):
        a=rng.uniform(0,math.tau);d=rng.uniform(0,12+attempt*.015);x=cx+d*math.cos(a);y=cy+d*math.sin(a)
        if abs(y-river_center(x))<24 or abs(y)>76 or abs(x)>92:continue
        if any(math.hypot(x-xx,y-yy)<rad+rr+1.2 for xx,yy,rr in occupied):continue
        samples=[height(x+dx,y+dy) for dx,dy in [(0,0),(-3,-3),(3,-3),(3,3),(-3,3)]]
        if max(samples)-min(samples)>4.2:continue
        break
    else:raise RuntimeError(('Cannot place inland house',r.name))
    angle=(0 if cy>0 else math.pi)+rng.uniform(-.48,.48)
    w=3.8 if r.get('asset')=='huizhou_courtyard' else 3.4
    footing_samples=[height(x+dx*math.cos(angle)-dy*math.sin(angle),y+dx*math.sin(angle)+dy*math.cos(angle)) for dx,dy in [(-w,-w),(w,-w),(w,w),(-w,w)]]
    r.location=(x,y,max(samples+footing_samples)+.04);r.rotation_euler.z=angle;r['settlement_cluster']=i%len(centres)
    occupied.append((x,y,rad));placements.append((r,x,y,rad))
bpy.context.view_layer.update();deltas={name:(o.matrix_world@oldmat[name].inverted()) for name in oldmat if (o:=bpy.data.objects.get(name))}

# Remove the rectangular field carpet and obsolete straight rear lanes.
removed_names=set()
for r in list(world.children):
    if r.get('asset')=='panorama_farmland':
        for o in reversed(descendants(r)):
            if o.type=='MESH':removed_names.add(o.name.replace(' ','_'))
            bpy.data.objects.remove(o,do_unlink=True)
    elif r.get('asset')=='panorama_streets':
        for o in list(r.children_recursive):
            if 'continuous_back_lane' in o.name or 'village_cross_lane' in o.name:
                removed_names.add(o.name.replace(' ','_'));bpy.data.objects.remove(o,do_unlink=True)

detail=empty('dispersed_village_landuse');detail.parent=world;detail['asset']='dispersed_village_landuse'
def newmesh(name,vs,fs,mat):
    o=mesh(name,vs,fs,mat);o.parent=detail;uv=o.data.uv_layers.new(name='UVMap')
    for p in o.data.polygons:
        p.use_smooth=True
        for li in p.loop_indices:
            v=o.data.vertices[o.data.loops[li].vertex_index].co;scale=24 if name=='graded_inland_earth' else 3;uv.data[li].uv=(v.x/scale,v.y/scale)
    return o
def ribbon(name,points,width,mat,lift=.065):
    dense=[]
    for a,b in zip(points,points[1:]):
        n=max(1,math.ceil(math.dist(a,b)/.45));dense.extend((a[0]+(b[0]-a[0])*j/n,a[1]+(b[1]-a[1])*j/n) for j in range(n))
    dense.append(points[-1]);vs=[];fs=[]
    for i,p in enumerate(dense):
        a=Vector(dense[max(0,i-1)]);b=Vector(dense[min(len(dense)-1,i+1)]);d=(b-a).normalized();normal=Vector((-d.y,d.x))
        for s in (-1,1):
            q=Vector(p)+normal*(s*width*.5);vs.append((q.x,q.y,height(q.x,q.y)+lift))
    for i in range(len(dense)-1):a=i*2;fs.append((a,a+2,a+3,a+1))
    return newmesh(name,vs,fs,mat)

roads=[]
for k,(cx,cy) in enumerate(centres):
    side=1 if cy>0 else -1
    roads.append([(cx+rng.uniform(-5,5),river_center(cx)+side*19),(cx-3,side*25),(cx+1,cy-side*7),(cx,cy)])
    ribbon('branching_village_lane',roads[-1],1.4,'huizhou_path')
for r,x,y,rad in placements:
    centre=centres[r['settlement_cluster']];ribbon('house_approach_lane',[centre,(x,y)],.85,'huizhou_path')
    # A terrain-following stone footing supports each hillside house.
    w=3.4 if r.get('asset')!='huizhou_courtyard' else 3.8;z=r.location.z
    a=r.rotation_euler.z;corners=[(x+dx*math.cos(a)-dy*math.sin(a),y+dx*math.sin(a)+dy*math.cos(a)) for dx,dy in [(-w,-w),(w,-w),(w,w),(-w,w)]]
    vs=[(xx,yy,z-.025) for xx,yy in corners]+[(xx,yy,z-.22) for xx,yy in corners]
    fs=[(0,1,2,3)]+[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)]
    newmesh('hillside_house_stone_footing',vs,fs,'huizhou_masonry')

# Broad graded earth terraces blend into the hillside; only a low stone plinth
# is exposed, so houses never perch on tall detached square blocks.
for side in (-1,1):
    nx,ny=278,126;vs=[];fs=[]
    for i in range(nx+1):
        x=-110+222*i/nx
        for j in range(ny+1):
            y=river_center(x)+side*(9+101*j/ny);base=height(x,y);z=base
            for r,hx,hy,rad in placements:
                if abs(x-hx)>11 or abs(y-hy)>11:continue
                a=r.rotation_euler.z;dx=(x-hx)*math.cos(a)+(y-hy)*math.sin(a);dy=-(x-hx)*math.sin(a)+(y-hy)*math.cos(a)
                w=3.8 if r.get('asset')=='huizhou_courtyard' else 3.4
                distance=math.hypot(max(0,abs(dx)-w),max(0,abs(dy)-w));t=max(0,min(1,distance/5));t=t*t*(3-2*t)
                z=max(z,(r.location.z-.22)*(1-t)+base*t)
            vs.append((x,y,z+.025))
    for i in range(nx):
        for j in range(ny):
            k=i*(ny+1)+j;q=(k,k+ny+1,k+ny+2,k+1);fs.append(q if side>0 else tuple(reversed(q)))
    newmesh('graded_inland_earth',vs,fs,'panorama_ground')
    start=len(verts);verts.extend(Vector(v) for v in vs);faces.extend(tuple(start+k for k in p) for p in fs)
ground=BVHTree.FromPolygons(verts,faces)
for o in detail.children:
    if 'village_lane' in o.name or 'approach_lane' in o.name:
        for v in o.data.vertices:v.co.z=height(v.co.x,v.co.y)+.065
        o.data.update()

# Voronoi land parcels: clipped convex cells, varied setbacks, and fallow gaps.
def clip(poly,nx,ny,c):
    out=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        da=a[0]*nx+a[1]*ny-c;db=b[0]*nx+b[1]*ny-c
        if da<=0:out.append(a)
        if (da<=0)!=(db<=0):
            t=da/(da-db);out.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
    return out
parcels=[]
for side in (-1,1):
    seeds=[]
    while len(seeds)<63:
        x=rng.uniform(-104,108);y=side*rng.uniform(24,91)+river_center(x)
        if all(math.dist((x,y),p)>7.5 for p in seeds):seeds.append((x,y))
    for sx,sy in seeds:
        if rng.random()<.16:continue
        poly=[(-108,22 if side>0 else -110),(112,22 if side>0 else -110),(112,118 if side>0 else -22),(-108,118 if side>0 else -22)]
        for tx,ty in seeds:
            if (tx,ty)==(sx,sy):continue
            poly=clip(poly,tx-sx,ty-sy,(tx*tx+ty*ty-sx*sx-sy*sy)/2)
            if not poly:break
        if len(poly)<3:continue
        cx=sum(p[0] for p in poly)/len(poly);cy=sum(p[1] for p in poly)/len(poly);inset=rng.uniform(.67,.86)
        poly=[(cx+(x-cx)*inset,cy+(y-cy)*inset) for x,y in poly]
        if any(math.hypot(cx-x,cy-y)<rad+max(math.dist((cx,cy),p) for p in poly)+1.3 for x,y,rad in occupied):continue
        if abs(cy-river_center(cx))<24:continue
        vs=[];fs=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            n=max(2,math.ceil(max(math.dist((cx,cy),a),math.dist(a,b),math.dist(b,(cx,cy)))/.65));base=len(vs);rows=[]
            for i in range(n+1):
                row=[]
                for j in range(n-i+1):
                    x=cx+(a[0]-cx)*i/n+(b[0]-cx)*j/n;y=cy+(a[1]-cy)*i/n+(b[1]-cy)*j/n
                    row.append(len(vs));vs.append((x,y,height(x,y)+.085))
                rows.append(row)
            for i in range(n):
                for j in range(n-i):
                    fs.append((rows[i][j],rows[i+1][j],rows[i][j+1]))
                    if j<n-i-1:fs.append((rows[i+1][j],rows[i+1][j+1],rows[i][j+1]))
        mat=rng.choice(['field_green','field_green','field_olive','field_earth']);newmesh('irregular_cultivated_parcel',vs,fs,mat)
        ribbon('irregular_field_berm',poly+[poly[0]],rng.uniform(.15,.27),'field_ridge',.14);parcels.append(poly)
        if mat!='field_earth':
            gx=height(cx+.3,cy)-height(cx-.3,cy);gy=height(cx,cy+.3)-height(cx,cy-.3)
            angle=math.atan2(gx,-gy)+rng.uniform(-.18,.18) if abs(gx)+abs(gy)>.03 else rng.uniform(0,math.pi)
            ca,sa=math.cos(angle),math.sin(angle);uv=[((x-cx)*ca+(y-cy)*sa,-(x-cx)*sa+(y-cy)*ca) for x,y in poly]
            v=min(p[1] for p in uv)+.65;step=rng.uniform(.85,1.35)
            while v<max(p[1] for p in uv)-.4:
                cross=[]
                for a,b in zip(uv,uv[1:]+uv[:1]):
                    if (a[1]<=v<b[1]) or (b[1]<=v<a[1]):cross.append(a[0]+(b[0]-a[0])*(v-a[1])/(b[1]-a[1]))
                if len(cross)>=2:
                    u0,u1=min(cross)+.25,max(cross)-.25
                    if u1-u0>.8:ribbon('contour_crop_row',[(cx+u0*ca-v*sa,cy+u0*sa+v*ca),(cx+u1*ca-v*sa,cy+u1*sa+v*ca)],rng.uniform(.045,.085),'field_ridge',.13)
                v+=step

# Relocate trees that now intersect roofs, without altering their geometry.
for r in world.children:
    if r.get('asset') not in ('tree','distant_tree'):continue
    x,y=r.location.x,r.location.y
    if not any(math.hypot(x-xx,y-yy)<rad+2.1 for xx,yy,rad in occupied):continue
    prior={o.name:o.matrix_world.copy() for o in descendants(r) if o.type=='MESH'}
    for j in range(1000):
        xx=x+rng.uniform(-18,18);yy=y+rng.uniform(-18,18)
        if abs(yy-river_center(xx))>23 and all(math.hypot(xx-a,yy-b)>rr+2.5 for a,b,rr in occupied):break
    r.location=(xx,yy,height(xx,yy));bpy.context.view_layer.update()
    for name,old in prior.items():deltas[name]=bpy.data.objects[name].matrix_world@old.inverted()

scene=bpy.context.scene;cam=scene.camera
exec((ROOT/'tools/configure_render_device.py').read_text(encoding='utf-8'),globals())
def render_views():
    configure_preview_device();scene.cycles.samples=12
    for name,loc,target in [('25_dispersed_village',(105,-122,105),(0,6,1)),('26_inland_village',(-51,-76,36),(-24,-34,5)),('21_bending_river_aerial',(125,-110,100),(65,12,0)),('20_panorama_aerial',(115,-145,112),(25,8,2))]:
        if '--preview-only' in sys.argv and name=='21_bending_river_aerial':return
        scene.render.resolution_x=1600;scene.render.resolution_y=1000;cam.data.type='PERSP';cam.data.lens=35;cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(PRE/(name+'.png'));render_preview_frame()
    scene.render.resolution_x=2560;scene.render.resolution_y=1280;cam.data.type='PANO';cam.data.panorama_type='EQUIRECTANGULAR';cam.location=(0,0,6);cam.rotation_euler=Vector((1,0,0)).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(PRE/'15_environment_360.png');render_preview_frame()
if '--preview-only' in sys.argv:
    render_views();print('DISPERSED_PREVIEW_READY',len(moved),len(parcels),flush=True);raise SystemExit(0)

CV=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
inventory=json.loads((backup/'inventory.json').read_text());item=export_obj('dispersed_village_landuse',detail);scene_item=next(i for i in inventory if i['file']=='scene_preview.obj');offset=scene_item['vertices']
transforms={name.replace(' ','_'):CV@delta@CV.inverted() for name,delta in deltas.items()};norms={name:mat.to_3x3().inverted().transposed() for name,mat in transforms.items()}
p=MODELS/'scene_preview.obj';tmp=p.with_suffix('.sprawl.tmp');removed=0;active=None;omit=False
with (backup/'scene_preview.obj').open(encoding='utf-8') as src,tmp.open('w',encoding='utf-8',newline='\n') as dst:
    for line in src:
        if line.startswith('o '):active=line[2:].strip();omit=active in removed_names
        if omit and line.startswith(('o ','usemtl ','f ')):
            if line.startswith('f '):removed+=1
            continue
        if active in transforms:
            if line.startswith('v '):line='v %.6f %.6f %.6f\n'%tuple(transforms[active]@Vector(tuple(map(float,line.split()[1:]))))
            elif line.startswith('vn '):line='vn %.6f %.6f %.6f\n'%tuple((norms[active]@Vector(tuple(map(float,line.split()[1:])))).normalized())
        dst.write(line)
    for line in (MODELS/item['file']).open(encoding='utf-8'):
        if line.startswith(('#','mtllib')):continue
        if line.startswith('f '):line='f '+' '.join('/'.join(str(int(i)+offset) for i in token.split('/')) for token in line.split()[1:])+'\n'
        dst.write(line)
tmp.replace(p);scene_item['triangles']+=item['triangles']-removed;scene_item['vertices']+=item['vertices'];inventory.append(item)
(MODELS/'inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
nodes=[]
for root in world.children:
    for o in descendants(root):nodes.append({'name':o.name,'parent':o.parent.name if o.parent and o.parent!=world else None,'asset':o.get('asset'),'type':o.type,'render_mode':o.get('render_mode'),'local_matrix_zup':[arr(row) for row in o.matrix_local],'world_matrix_yup':[arr(row) for row in CV@o.matrix_world@CV.inverted()]})
(MODELS/'scene_layout.json').write_text(json.dumps({'units':'metres','obj_axes':'Y up, +X forward','scene_internal_axes':'Z up','nodes':nodes},ensure_ascii=False,indent=2),encoding='utf-8')
for o in list(bpy.context.selected_objects):o.select_set(False)
for o in descendants(world):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(MODELS/'dragonboat_scene.glb'),use_selection=True,export_format='GLB',export_apply=True)
exec((ROOT/'tools/fix_sky_glb.py').read_text(encoding='utf-8'),globals());ensure_unlit_sky(MODELS/'dragonboat_scene.glb')
for o in list(bpy.context.selected_objects):o.select_set(False)
scene.cycles.device='CPU';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
(MODELS/'dispersed_layout.json').write_text(json.dumps({'moved_houses':[{'name':r.name,'position':list(r.location),'cluster':r['settlement_cluster']} for r in moved],'cluster_centres':centres,'irregular_parcels':parcels,'old_regular_field_groups_removed':len(removed_names),'status':'built'},ensure_ascii=False,indent=2),encoding='utf-8')
render_views();print('DISPERSED_VILLAGE_COMPLETE',len(moved),len(parcels),flush=True)
