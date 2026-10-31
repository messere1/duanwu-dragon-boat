"""Add editable, low-cost village and shoreline geometry to the current scene."""
import bpy,math,random,json,sys
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from river_routes import river_center,half_width
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_realism.blend'));bpy.context.view_layer.update()
world=bpy.data.objects['world_export'];old=bpy.data.objects.get('village_lived_detail')
if old:
    for o in list(old.children_recursive)[::-1]:bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.objects.remove(old,do_unlink=True)
rng=random.Random(3023209092);parts={};records={'shutter_windows':0,'potted_plants':0,'awnings':0,'reed_clumps':0,'shore_stones':0,'wall_vines':0}
spec={
 'detail_timber':((.32,.27,.19),'wood_planks_grey_Diffuse.png','wood_planks_grey_nor_gl.png'),
 'detail_iron':((.065,.06,.047),None,None),
 'detail_clay':((.27,.15,.085),None,None),
 'detail_leaf':((.07,.145,.035),None,None),
 'detail_dry_grass':((.23,.25,.10),None,None),
 'detail_linen':((.72,.65,.49),'canvas.png',None),
 'detail_indigo':((.16,.25,.27),'canvas.png',None),
 'detail_moss_stone':((.42,.47,.32),'huizhou_stone.png',None)}
def tri(mat,points):
    v=[Vector(p) for p in points]
    if (v[1]-v[0]).cross(v[2]-v[0]).length_squared>1e-13:parts.setdefault(mat,[]).append(v)
def quad(mat,a,b,c,d):tri(mat,(a,b,c));tri(mat,(a,c,d))
def box(mat,center,size,xf=Matrix.Identity(4)):
    c=Vector(center);s=Vector(size)*.5;v=[xf@(c+Vector((x*s.x,y*s.y,z*s.z))) for x,y,z in ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))]
    for f in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):quad(mat,*[v[i] for i in f])
def rod(mat,a,b,r,n=7,r2=None):
    a,b=Vector(a),Vector(b)
    if (b-a).length<1e-7:return
    axis=(b-a).normalized();u=axis.cross(Vector((0,0,1)))
    if u.length<.01:u=axis.cross(Vector((0,1,0)))
    u.normalize();v=axis.cross(u);r2=r if r2 is None else r2
    p=[a+(u*math.cos(i*math.tau/n)+v*math.sin(i*math.tau/n))*r for i in range(n)];q=[b+(u*math.cos(i*math.tau/n)+v*math.sin(i*math.tau/n))*r2 for i in range(n)]
    for i in range(n):j=(i+1)%n;quad(mat,p[i],p[j],q[j],q[i]);tri(mat,(a,p[j],p[i]));tri(mat,(b,q[i],q[j]))
def blade(base,height,width,angle,lean,mat='detail_leaf'):
    p=Vector(base);d=Vector((math.cos(angle),math.sin(angle),0));across=Vector((-d.y,d.x,0));centers=[p+Vector((0,0,height*t))+d*(lean*t*t) for t in (0,.32,.72,1)]
    for i in range(3):
        w0=width*math.sin(math.pi*i/3);w1=width*math.sin(math.pi*(i+1)/3)
        quad(mat,centers[i]-across*w0,centers[i]+across*w0,centers[i+1]+across*w1,centers[i+1]-across*w1)

houses=[r for r in world.children if r.get('asset') in {'riverside_house','huizhou_tall_house','huizhou_tea_house','huizhou_courtyard'}]
for h in sorted(houses,key=lambda o:o.name):
    windows=[o for o in h.children_recursive if o.type=='MESH' and 'deep_window_shadow' in o.name]
    for win in windows:
        if rng.random()>.38:continue
        bounds=[Vector(v) for v in win.bound_box];lo=Vector([min(v[k] for v in bounds) for k in range(3)]);hi=Vector([max(v[k] for v in bounds) for k in range(3)]);c=(lo+hi)*.5;w=hi.x-lo.x;hh=hi.z-lo.z
        if w<.2 or hh<.3:continue
        for side in (-1,1):
            angle=side*rng.uniform(.38,1.25);hinge=Vector((c.x+side*w*.5,lo.y-.045,c.z));xf=win.matrix_world@Matrix.Translation(hinge)@Matrix.Rotation(angle,4,'Z')
            for i in range(4):box('detail_timber',(-side*w*(i+.5)/8,0,0),(w/8-.006,.038,hh*.95),xf)
            for z in (-hh*.3,hh*.3):box('detail_timber',(-side*w*.25,-.024,z),(w*.49,.024,.048),xf)
        records['shutter_windows']+=1
    if rng.random()<.43:
        local=Vector((rng.choice((-1.45,1.5)),-2.35,.06));p=h.matrix_world@local
        rod('detail_clay',p,p+Vector((0,0,.29)),.135,10,.18);rod('detail_timber',p+Vector((0,0,.285)),p+Vector((0,0,.299)),.165,10)
        for i in range(9):blade(p+Vector((rng.uniform(-.08,.08),rng.uniform(-.08,.08),.30)),rng.uniform(.18,.43),.025,rng.random()*math.tau,rng.uniform(.08,.24))
        records['potted_plants']+=1
    if h.get('asset')!='huizhou_tea_house' and rng.random()<.22:
        mat='detail_linen' if rng.random()<.7 else 'detail_indigo';xf=h.matrix_world
        for i in range(8):
            for j in range(3):
                def p(u,v):return xf@Vector((-1.12+2.24*u,-2.12-.69*v,2.48-.25*v-.025*math.sin(u*math.tau*4)))
                quad(mat,p(i/8,j/3),p((i+1)/8,j/3),p((i+1)/8,(j+1)/3),p(i/8,(j+1)/3))
        for x in (-1.1,1.1):rod('detail_timber',xf@Vector((x,-2.1,2.15)),xf@Vector((x,-2.78,2.23)),.023)
        records['awnings']+=1
    if rng.random()<.20:
        xf=h.matrix_world;x=rng.choice((-1.95,1.95));last=xf@Vector((x,-2.13,.15))
        for j in range(15):
            p=xf@Vector((x+.065*math.sin(j*.8),-2.145,.15+j*.145));rod('detail_leaf',last,p,.006,5);last=p
            blade(p,rng.uniform(.07,.12),.035,rng.random()*math.tau,.12)
        records['wall_vines']+=1

for i in range(220):
    x=-38+i*.69+rng.uniform(-.28,.28)
    for side in (-1,1):
        if rng.random()>.24:continue
        y=river_center(x)+side*(half_width(x)-rng.uniform(.04,.24));base=Vector((x,y,-.11))
        for j in range(rng.randint(6,12)):
            p=base+Vector((rng.uniform(-.18,.18),rng.uniform(-.11,.11),rng.uniform(-.025,.025)))
            blade(p,rng.uniform(.25,.72),rng.uniform(.009,.018),rng.random()*math.tau,rng.uniform(.05,.22),'detail_dry_grass' if j%5==0 else 'detail_leaf')
        records['reed_clumps']+=1
        if rng.random()<.7:
            for j in range(rng.randint(2,4)):
                p=base+Vector((rng.uniform(-.28,.28),side*rng.uniform(-.10,.1),.05));rad=rng.uniform(.045,.11)
                # Irregular low shore stones, mostly submerged.
                top=p+Vector((rng.uniform(-.02,.02),rng.uniform(-.02,.02),rad*.7));ring=[p+Vector((math.cos(k*math.tau/7)*rad,math.sin(k*math.tau/7)*rad*.7,rng.uniform(-.01,.01))) for k in range(7)]
                for k in range(7):tri('detail_moss_stone',(ring[k],ring[(k+1)%7],top))
                records['shore_stones']+=1

root=bpy.data.objects.new('village_lived_detail',None);bpy.context.collection.objects.link(root);root.parent=world;root['asset']='village_lived_detail'
lines=['mtllib village_detail.mtl'];idx=1;mtl=[];total=0
for mat,triangles in parts.items():
    color,texture,normal=spec[mat];m=bpy.data.materials.get(mat) or bpy.data.materials.new(mat);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.86
    if texture:
        node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=bpy.data.images.load(str(ROOT/'textures'/texture),check_existing=True);node.image.pack();m.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color'])
    vs=[tuple(v) for t in triangles for v in t];mesh=bpy.data.meshes.new(mat);mesh.from_pydata(vs,[],[(i,i+1,i+2) for i in range(0,len(vs),3)]);mesh.update();uv=mesh.uv_layers.new();obj=bpy.data.objects.new(mat,mesh);bpy.context.collection.objects.link(obj);obj.parent=root;obj.data.materials.append(m)
    lines.extend(['o '+mat,'usemtl '+mat])
    for p in mesh.polygons:
        n=p.normal;axis=max(range(3),key=lambda k:abs(n[k]))
        for li in p.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co;u=v[(axis+1)%3];vv=v[(axis+2)%3];uv.data[li].uv=(u,vv);lines.extend([f'v {v.x:.6f} {v.z:.6f} {-v.y:.6f}',f'vt {u:.6f} {vv:.6f}',f'vn {n.x:.6f} {n.z:.6f} {-n.y:.6f}'])
        lines.append('f '+' '.join(f'{j}/{j}/{j}' for j in range(idx,idx+3)));idx+=3;total+=1
    mtl.extend(['newmtl '+mat,'Kd '+' '.join(map(str,color)),'Ks 0.035 0.035 0.035','Ns 12'])
    if texture:mtl.append('map_Kd ../textures/'+texture)
    if normal:mtl.append('map_Bump ../textures/'+normal)
(ROOT/'models/village_detail.obj').write_text('\n'.join(lines)+'\n',encoding='utf8');(ROOT/'models/village_detail.mtl').write_text('\n'.join(mtl)+'\n',encoding='utf8')
records['triangles']=total;records['houses_considered']=len(houses);(ROOT/'models/village_detail.json').write_text(json.dumps(records,indent=2),encoding='utf8')
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dragonboat_realism.blend'));print('VILLAGE_DETAILS',json.dumps(records),flush=True)
