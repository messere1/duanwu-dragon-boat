"""Blender 4.3+: original parametric dragon-boat asset library.
blender -b --python tools/build_models.py
Z-up internally. OBJ exports use Y-up, forward +X; no per-file normalization.
"""
import bpy, math, json, random,sys,shutil
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin,cos,pi
ROOT=Path(__file__).resolve().parents[1]
MODELS=ROOT/'models'; PRE=ROOT/'previews'
for p in (MODELS,PRE): p.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.materials): bpy.data.materials.remove(d)
random.seed(27)
M={}; assets={}; nodes=[]
def material(name,color,texture=None,metal=0,rough=.5):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF'); bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Metallic'].default_value=metal; bs.inputs['Roughness'].default_value=rough
    if texture:
        tex=m.node_tree.nodes.new('ShaderNodeTexImage'); tex.image=bpy.data.images.load(str(ROOT/'textures'/texture));
        m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    M[name]=m; return m
material('wood',(.39,.20,.085),'wood.png'); material('darkwood',(.12,.055,.025))
material('red',(.65,.045,.035),'cloth_red.png');material('jade',(.025,.35,.29),'cloth_jade.png')
material('gold',(.86,.57,.14),metal=.65,rough=.28);material('ivory',(.92,.83,.59))
material('skin',(.67,.42,.25));material('hair',(.018,.024,.023));material('white',(.93,.94,.84))
material('black',(.008,.015,.014));material('stone',(.48,.52,.50),'stone.png');material('roof',(.07,.16,.16),'roof.png')
material('plaster',(.85,.80,.65));material('leaf',(.08,.28,.16));material('leaflight',(.21,.40,.19))
material('grass',(.25,.39,.23));material('water',(.025,.28,.31),metal=.25,rough=.24)
material('banner',(.7,.1,.1),'banner.png');material('plaque',(.6,.1,.1),'plaque.png')

def finish(o,name,mat,bevel=0,smooth=False):
    o.name=name; o.data.materials.append(M[mat])
    if bevel:
        mod=o.modifiers.new('small_edge_bevel','BEVEL'); mod.width=bevel;mod.segments=2
        mod=o.modifiers.new('weighted_normals','WEIGHTED_NORMAL')
    if smooth:
        for f in o.data.polygons:f.use_smooth=True
    return o
def box(name,loc,scale,mat,bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,mat,bevel)
def sphere(name,loc,scale,mat,seg=12,rings=8):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,radius=1,location=loc)
    o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,mat,smooth=True)
def rod(name,a,b,r,mat,r2=None,n=10):
    a,b=Vector(a),Vector(b); delta=b-a
    bpy.ops.mesh.primitive_cone_add(vertices=n,radius1=r,radius2=r if r2 is None else r2,depth=delta.length,location=(a+b)/2)
    o=bpy.context.object;o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();return finish(o,name,mat,smooth=True)
def mesh(name,verts,faces,mat):
    m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update()
    o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);finish(o,name,mat)
    # Recalculate mesh normals, retaining separate shells for intentional composite parts.
    import bmesh
    bm=bmesh.new();bm.from_mesh(m);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(m);bm.free()
    return o
def tube(name,points,r,mat):
    # Mesh tubes, not curves: every deliverable is directly OBJ compatible.
    vs=[];fs=[];n=8;previous_u=None
    for i,p in enumerate(points):
        t=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])
        t.normalize()
        u=(previous_u-t*previous_u.dot(t)) if previous_u is not None else t.cross(Vector((0,0,1)))
        if u.length<1e-5:u=t.cross(Vector((1,0,0)))
        u.normalize();vv=t.cross(u).normalized();previous_u=u
        rr=r*(1-.55*i/max(1,len(points)-1))
        for j in range(n):vs.append(Vector(p)+rr*(u*cos(2*pi*j/n)+vv*sin(2*pi*j/n)))
    for i in range(len(points)-1):
        for j in range(n):a=i*n+j;b=i*n+(j+1)%n;fs.append((a,b,b+n,a+n))
    fs += [tuple(reversed(range(n))),tuple((len(points)-1)*n+j for j in range(n))]
    return mesh(name,vs,fs,mat)
def empty(name,loc=(0,0,0)):
    o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.location=loc;return o
def parent_new(before,parent):
    for o in set(bpy.data.objects)-before:
        if o!=parent and o.parent is None:o.parent=parent
def begin():return set(bpy.data.objects)
def root_asset(name,fn):
    before=begin(); root=empty(name);fn();parent_new(before,root);assets[name]=root;return root

def hull(team):
    # Hollow U-section with inner surface and thick top rim, six seats.
    ns=40; nt=16;v=[];f=[]
    for inner in (False,True):
        for i in range(ns+1):
            x=-4.9+9.8*i/ns;w=.90*(.12+.88*sin(pi*i/ns)**.55)
            lift=.32*(abs(x)/4.9)**4
            for j in range(nt+1):
                t=-pi/2+pi*j/nt
                v.append((x,(w-(.07 if inner else 0))*sin(t),.85+lift-(.64-(.08 if inner else 0))*cos(t)))
    k=(ns+1)*(nt+1)
    for layer in range(2):
        for i in range(ns):
            for j in range(nt):
                a=layer*k+i*(nt+1)+j;q=(a,a+nt+1,a+nt+2,a+1)
                f.append(q if layer==0 else tuple(reversed(q)))
    for i in range(ns):
        for j in (0,nt):a=i*(nt+1)+j;b=(i+1)*(nt+1)+j;f.append((a,b,b+k,a+k))
    for i in (0,ns):
        for j in range(nt):a=i*(nt+1)+j;f.append((a,a+1,a+1+k,a+k))
    mesh('hollow_hull',v,f,'wood')
    for s in (-1,1):
        for z in (.62,.87):
            pts=[(-4.9+9.8*i/ns,s*.9*(.12+.88*sin(pi*i/ns)**.55),z+.32*(abs(-4.9+9.8*i/ns)/4.9)**4) for i in range(ns+1)]
            tube('gold_gunwale',pts,.045,'gold')
        # Stylised overlapping dragon scales: geometry remains visible with textures disabled.
        for i in range(22):
            x=-4.25+i*.39; w=.9*(.12+.88*sin(pi*(x+4.9)/9.8)**.55)
            for row in range(2):
                xx=x+row*.14;yy=s*(w-(.04 if row==0 else .18)); zz=.69-row*.21
                pts=[(xx-.16,yy,zz+.10),(xx+.13,yy,zz+.10),(xx+.20,yy,zz-.015),(xx,yy+s*.045,zz-.14),(xx-.20,yy,zz-.015)]
                mesh('scale',pts,[(0,1,2,3,4)],team if (i+row)%3 else 'gold')
    for x in (-3,-1.9,-.8,.3,1.4,2.5):box('seat',(x,0,.76),(.26,1.44,.11),'wood')
    box('foredeck',(3.65,0,.91),(1.25,1.12,.14),'wood')
    box('stern_deck',(-4.05,0,.84),(.65,.72,.12),'wood')

def dragon_head(team):
    tube('curved_neck',[(4.6,0,.78),(4.95,0,1.05),(5.10,0,1.55),(5.38,0,1.82)],.37,team)
    sphere('head',(5.43,0,1.77),(.58,.40,.40),team)
    sphere('upper_muzzle',(5.93,0,1.62),(.49,.29,.19),team)
    sphere('open_mouth',(5.97,0,1.44),(.38,.265,.065),'black')
    sphere('jaw',(5.92,0,1.34),(.42,.26,.09),'gold')
    for s in (-1,1):
        sphere('eye_white',(5.57,s*.348,1.90),(.17,.075,.13),'white')
        sphere('eye_pupil',(5.63,s*.409,1.91),(.065,.028,.079),'black')
        tube('brow',[(5.31,s*.32,2.02),(5.49,s*.40,2.07),(5.75,s*.33,2.03)],.055,'gold')
        tube('antler',[(5.16,s*.24,2.0),(4.95,s*.32,2.35),(5.03,s*.34,2.65)],.105,'ivory')
        tube('antler_branch',[(4.99,s*.32,2.36),(4.76,s*.35,2.48)],.065,'ivory')
        sphere('nostril',(6.20,s*.17,1.75),(.066,.035,.045),'black')
        tube('whisker',[(6.13,s*.24,1.55),(6.40,s*.45,1.50),(6.20,s*.64,1.67)],.027,'gold')
        rod('fang',(5.97,s*.21,1.53),(5.95,s*.21,1.40),.04,'ivory',r2=.008,n=6)
    for i in range(5):
        x=4.88+i*.10;z=1.55+i*.09
        mesh('mane',[(x,-.20,z),(x,.20,z),(x-.40,0,z+.40)],[(0,1,2)],'gold')
def dragon_tail(team):
    tube('tail',[(-4.7,0,.8),(-5.10,0,1.00),(-5.45,0,1.36),(-5.65,0,1.64)],.23,team)
    for s in (-1,0,1):
        mesh('tail_fin',[(-5.48,0,1.39),(-5.7,s*.12,1.9),(-6.16,s*.35,2.08),(-5.98,s*.26,1.52)],[(0,1,2),(0,2,3)],'gold')
def paddle(team='red'):
    rod('shaft',(0,0,.12),(0,0,-1.45),.028,'wood')
    # Blade shares the shoulder/hand pivot at the origin.
    vs=[(-.13,-.035,-1.28),(.13,-.035,-1.28),(.19,-.035,-1.90),(0,-.035,-2.04),(-.19,-.035,-1.90)]
    vs+= [(x,-y,z) for x,y,z in vs]
    fs=[(4,3,2,1,0),(5,6,7,8,9)]+[(i,(i+1)%5,(i+1)%5+5,i+5) for i in range(5)]
    mesh('blade',vs,fs,team);box('grip',(0,0,.12),(.21,.06,.06),'darkwood')
def person(team,standing=False,role='rower'):
    # Root is at seat / feet. Separate upper and lower arms for later articulated animation.
    hip=.85 if standing else .22
    sphere('trousers',(0,0,hip),(.20,.24,.22),'darkwood')
    torso=box('jersey',(0,0,hip+.32),(.38,.47,.55),team,.065)
    rod('neck',(0,0,hip+.57),(0,0,hip+.68),.085,'skin')
    sphere('head',(0,0,hip+.85),(.18,.17,.22),'skin')
    sphere('hair',(-.035,0,hip+.97),(.17,.175,.12),'hair')
    # Headband across forehead, faces toward +X.
    sphere('headband',(0,0,hip+.94),(.184,.181,.035),team)
    for s in (-1,1):
        sphere('eye',(.165,s*.075,hip+.87),(.018,.022,.023),'black',8,4)
        if standing:
            rod('leg',(-.02,s*.13,.10),(0,s*.13,.76),.09,'darkwood')
            box('shoe',(.07,s*.13,.07),(.28,.16,.12),'black')
        else:
            rod('thigh',(0,s*.13,.22),(.38,s*.13,.18),.085,'darkwood')
            rod('calf',(.38,s*.13,.18),(.40,s*.13,-.17),.07,'darkwood')
            box('shoe',(.48,s*.13,-.19),(.25,.15,.11),'black')
    # Arms are empty-parented at shoulders; exact pivots are preserved in scene graph.
    for s in (-1,1):
        before=begin();a=empty('shoulder_L' if s==1 else 'shoulder_R',(0,s*.27,hip+.5))
        elbow=(.27,s*.34,hip+.27)
        hand=(.48,.44,hip+.47+(0.10 if s<0 else 0)) if role=='rower' else (.48,s*.44,hip+.47)
        rod('upper_arm',(0,s*.27,hip+.5),elbow,.065,'skin')
        rod('forearm',elbow,hand,.055,'skin');sphere('hand',hand,(.065,.06,.06),'skin',8,6)
        # parent in local coordinates while preserving visual pose
        bpy.context.view_layer.update()
        for o in set(bpy.data.objects)-before:
            if o!=a:o.parent=a;o.matrix_parent_inverse=a.matrix_world.inverted()

def drum():
    rod('drum_body',(0,0,.09),(0,0,.64),.33,'red',n=24)
    for z in (.10,.61):
        rod('drum_rim',(0,0,z-.025),(0,0,z+.025),.355,'gold',n=24)
    rod('drum_skin',(0,0,.64),(0,0,.66),.325,'ivory',n=24)
    for i in range(16):
        a=i*2*pi/16;sphere('stud',(.34*cos(a),.34*sin(a),.54),(.025,.025,.025),'gold',8,4)
    for s in (-1,1):rod('stand',(s*.23,0,-.05),(s*.28,0,.36),.04,'darkwood')
def drummer_stool():
    box('drummer_stool_seat',(0,0,.30),(.46,.46,.06),'wood',.018)
    for x in (-.16,.16):
        for y in (-.16,.16):box('drummer_stool_leg',(x,y,.14),(.065,.065,.28),'darkwood',.008)
    for y in (-.16,.16):box('drummer_stool_stretcher',(0,y,.11),(.34,.035,.035),'wood',.006)

def pennant(team):
    rod('flagpole',(0,0,0),(0,0,2.05),.027,'gold')
    nx=16;nz=8;v=[];f=[]
    for i in range(nx+1):
        for j in range(nz+1):
            u=i/nx;t=j/nz;v.append((u*.88,.10*u*sin(u*5+t*2),2-.52*t))
    for i in range(nx):
        for j in range(nz):a=i*(nz+1)+j;f.append((a,a+nz+1,a+nz+2,a+1))
    mesh('flag_cloth',v,f,team)

def roof(name,cx,cy,z,hx,hy,height,mat='roof'):
    # Swept, upturned eaves with tile strips; roof ridge runs X.
    for side in (-1,1):
        vs=[];fs=[];nx=12;ny=7
        for i in range(nx+1):
            x=-hx+2*hx*i/nx
            for j in range(ny+1):
                t=j/ny;y=side*hy*t
                zz=z+height*(1-t)**1.5+.22*t**4+.22*(abs(x)/hx)**6*t**3
                vs.append((cx+x,cy+y,zz))
        for i in range(nx):
            for j in range(ny):a=i*(ny+1)+j;fs.append((a,a+ny+1,a+ny+2,a+1))
        o=mesh(name,vs,fs,mat);mod=o.modifiers.new('roof_thickness','SOLIDIFY');mod.thickness=.09
        for i in range(19):
            x=-hx+2*hx*i/18
            pts=[]
            for j in range(8):
                t=j/7;pts.append((cx+x,cy+side*hy*t,z+height*(1-t)**1.5+.22*t**4+.22*(abs(x)/hx)**6*t**3+.045))
            tube('tile_rib',pts,.023,'roof')
    rod('ridge',(cx-hx,cy,z+height+.05),(cx+hx,cy,z+height+.05),.08,'roof')
    for s in (-1,1):tube('ridge_tip',[(cx+s*(hx-.25),cy,z+height),(cx+s*hx,cy,z+height+.12),(cx+s*(hx+.12),cy,z+height+.36)],.06,'gold')
def pavilion():
    box('foundation',(0,0,.15),(4.6,3.9,.3),'stone')
    for x in (-1.65,1.65):
        for y in (-1.3,1.3):
            rod('column',(x,y,.3),(x,y,3.2),.12,'red');rod('base',(x,y,.3),(x,y,.52),.18,'stone')
            box('dougong',(x,y,3.04),(.56,.50,.20),'gold')
    for y in (-1.3,1.3):box('beam',(0,y,3.0),(3.75,.18,.26),'red')
    roof('pavilion_roof',0,0,3.16,2.45,2.05,1.15)
    box('bench',(0,1.1,.88),(2.8,.40,.14),'wood')
    for x in (-1.1,1.1):box('bench_leg',(x,1.1,.60),(.12,.3,.5),'wood')
    plaque_quad('pavilion_sign',(0,-1.405,2.69),(1.65,.42),'plaque')
    for j in range(3):box('step',(0,-2.15-j*.25,.12-j*.045),(2,.28,.16),'stone')
def plaque_quad(name,loc,size,mat):
    x,y,z=loc;w,h=size
    o=mesh(name,[(x-w/2,y,z-h/2),(x+w/2,y,z-h/2),(x+w/2,y,z+h/2),(x-w/2,y,z+h/2)],[(0,1,2,3)],mat)
    uv=o.data.uv_layers.new(name='UVMap')
    for p in o.data.polygons:
        for li in p.loop_indices:
            co=o.data.vertices[o.data.loops[li].vertex_index].co
            uv.data[li].uv=((co.x-(x-w/2))/w,(co.z-(z-h/2))/h)
    return o
def house():
    box('house_base',(0,0,.17),(4.3,3.4,.34),'stone')
    box('white_walls',(0,0,1.45),(3.8,2.9,2.55),'plaster')
    for x in (-1.82,0,1.82):box('timber_frame',(x,-1.47,1.5),(.1,.1,2.7),'darkwood')
    box('door',(0,-1.51,.98),(.8,.08,1.7),'wood')
    for x in (-1.15,1.15):
        box('window',(x,-1.51,1.65),(.68,.08,.85),'darkwood')
        for dx in (-.19,0,.19):box('lattice',(x+dx,-1.56,1.65),(.035,.03,.77),'gold')
        for dz in (-.22,0,.22):box('lattice',(x,-1.56,1.65+dz),(.62,.03,.035),'gold')
    roof('house_roof',0,0,2.85,2.35,1.94,1.05)
def gate():
    # Gate spans the river in Y. Sign faces the approaching boats (-X).
    for y in (-5.8,5.8):
        box('gate_foot',(0,y,.25),(1.15,1.15,.5),'stone')
        rod('gate_post',(0,y,.4),(0,y,6.3),.20,'red')
        rod('gold_cap',(0,y,5.6),(0,y,6.0),.22,'gold')
    box('gate_beam',(0,0,5.65),(.40,12.6,.32),'red')
    for y in (-6.2,6.2):sphere('finial',(0,y,5.87),(.19,.19,.24),'gold')
    # Two independently UV-mapped faces: text remains readable from both directions.
    for side in (-1,1):
        o=plaque_quad('finish_banner_front' if side<0 else 'finish_banner_back',(0,0,0),(7.0,1.2),'banner')
        o.rotation_euler[2]=side*pi/2;o.location=(side*.05,0,4.85)
def quay():
    box('quay',(0,0,.0),(8,2,.8),'stone')
    for x in (-3.7,-1.85,0,1.85,3.7):
        box('railing_post',(x,-.8,.88),(.17,.17,1.05),'stone')
        sphere('post_cap',(x,-.8,1.43),(.16,.16,.14),'stone')
    for z in (.65,1.16):box('railing_bar',(0,-.8,z),(7.4,.12,.12),'stone')
def bridge():
    # Arched pedestrian bridge, kept beyond the finish so it does not obstruct the race.
    n=24;vs=[];fs=[]
    for i in range(n+1):
        y=-6+12*i/n;z=.6+2.2*(1-(y/6)**2)
        for x in (-1.0,1.0):vs.extend([(x,y,z),(x,y,z-.32)])
    for i in range(n):
        a=4*i;b=a+4;fs.extend([(a,b,b+2,a+2),(a+1,a+3,b+3,b+1),(a,a+1,b+1,b),(a+2,b+2,b+3,a+3)])
    fs.extend([(0,2,3,1),(n*4,n*4+1,n*4+3,n*4+2)]);mesh('arch_deck',vs,fs,'stone')
    for x in (-.94,.94):
        pts=[]
        for i in range(13):
            y=-6+i;z=.6+2.2*(1-(y/6)**2)
            rod('bridge_post',(x,y,z),(x,y,z+.85),.07,'stone');pts.append((x,y,z+.8))
        tube('bridge_rail',pts,.07,'stone')
def lantern():
    rod('pole',(0,0,0),(0,0,2.9),.06,'darkwood');rod('arm',(0,0,2.85),(0,.58,2.85),.05,'darkwood')
    rod('cord',(0,.52,2.85),(0,.52,2.52),.015,'gold')
    sphere('red_lantern',(0,.52,2.22),(.25,.25,.35),'red',16,10)
    for z in (1.91,2.53):rod('rim',(0,.52,z-.03),(0,.52,z+.03),.15,'gold')
    for i in range(6):rod('tassel',(0,.52+(i-2.5)*.03,1.93),(0,.52+(i-2.5)*.03,1.66),.009,'gold')
def tree():
    rod('trunk',(0,0,0),(0,0,2.5),.19,'wood',r2=.12)
    for a in (0,2.1,4.2):
        end=(.75*cos(a),.75*sin(a),2.65);rod('branch',(0,0,1.6),end,.09,'wood',r2=.04)
        sphere('canopy',end,(1.05,.95,.85),'leaf' if a else 'leaflight',10,6)
    sphere('crown',(0,0,3.12),(1.05,1.0,.85),'leaflight',10,6)
def rock():
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(0,0,.32));o=bpy.context.object;o.scale=(.8,.55,.65);finish(o,'rock','stone')
def buoy():
    sphere('buoy',(0,0,.08),(.22,.22,.18),'gold',12,8);rod('buoy_pin',(0,0,.15),(0,0,.72),.018,'red')
    mesh('buoy_flag',[(0,0,.70),(.28,0,.62),(0,0,.52)],[(0,1,2)],'red')
def water():
    nx,ny=100,40;v=[];f=[]
    for i in range(nx+1):
        for j in range(ny+1):
            x=-24+48*i/nx;y=-5.7+11.4*j/ny
            v.append((x,y,-.06+.018*sin(x*1.2+y*2)))
    for i in range(nx):
        for j in range(ny):a=i*(ny+1)+j;f.append((a,a+ny+1,a+ny+2,a+1))
    mesh('river_surface',v,f,'water')

# Active art direction overrides: carved wood, natural anatomy and willow branches.
exec((ROOT/'tools'/'style_traditional.py').read_text(encoding='utf-8'),globals())
exec((ROOT/'tools'/'style_open_assets.py').read_text(encoding='utf-8'),globals())
exec((ROOT/'tools'/'style_ceremonial_boat.py').read_text(encoding='utf-8'),globals())
exec((ROOT/'tools'/'style_riverside.py').read_text(encoding='utf-8'),globals())
exec((ROOT/'tools'/'style_huizhou.py').read_text(encoding='utf-8'),globals())
exec((ROOT/'tools'/'style_panorama.py').read_text(encoding='utf-8'),globals())

# Prototypes: local coordinates and pivots are retained in each individual OBJ.
root_asset('boat_hull_red',lambda:hull('red'));root_asset('dragon_head_red',lambda:dragon_head('red'))
root_asset('dragon_tail_red',lambda:dragon_tail('red'))
root_asset('boat_hull_jade',lambda:hull('jade'));root_asset('dragon_head_jade',lambda:dragon_head('jade'))
root_asset('dragon_tail_jade',lambda:dragon_tail('jade'))
root_asset('paddle',paddle);root_asset('paddle_jade',lambda:paddle('jade'))
root_asset('rower_red',lambda:person('red'));root_asset('rower_jade',lambda:person('jade'))
root_asset('drummer_red',lambda:person('red',True,'drummer'));root_asset('drummer_jade',lambda:person('jade',True,'drummer'))
root_asset('helmsman_red',lambda:person('red',True,'helmsman'));root_asset('helmsman_jade',lambda:person('jade',True,'helmsman'))
root_asset('drum',drum);root_asset('pennant_red',lambda:pennant('red'));root_asset('pennant_jade',lambda:pennant('jade'))
root_asset('drummer_stool',drummer_stool)
root_asset('pavilion',pavilion);root_asset('riverside_house',house);root_asset('finish_gate',gate)
root_asset('quay_segment',quay);root_asset('arch_bridge',bridge);root_asset('lantern_post',lantern)
root_asset('tree',tree);root_asset('rock',rock);root_asset('course_buoy',buoy);root_asset('river_surface',water)
root_asset('bank_ground',bank_ground)
root_asset('quay_access',lambda:quay(True));root_asset('mooring_dock',mooring_dock)
root_asset('riverside_bench',bench);root_asset('zongzi_basket',basket)
root_asset('tea_stall',tea_stall);root_asset('bamboo_planter',bamboo_planter);root_asset('reed_patch',reed_patch)
install_huizhou_assets()

def descendants(root):return [root]+list(root.children_recursive)
def clone(proto,name,loc=(0,0,0),rot=0,parent=None):
    mapping={}
    for old in descendants(assets[proto]):
        new=old.copy();bpy.context.collection.objects.link(new);mapping[old]=new
    for old,new in mapping.items():
        new.parent=mapping.get(old.parent)
        new.matrix_parent_inverse=old.matrix_parent_inverse.copy()
        new.matrix_basis=old.matrix_basis.copy()
        new.name=name+'__'+old.name
    root=mapping[assets[proto]];root.name=name;root.location=loc;root.rotation_euler[2]=rot;root.parent=parent
    root['asset']=proto
    return root
def boat(team):
    b=empty('dragon_boat_'+team)
    for part in ('boat_hull','dragon_head','dragon_tail'):clone(part+'_'+team,team+'_'+part,parent=b)
    for row,x in enumerate((-3,-1.9,-.8,.3,1.4,2.5)):
        for s in (-1,1):
            rower=clone('rower_'+team,f'{team}_rower_{row}_{s}',(x,s*.40,.82),parent=b)
            rower.scale.y=s
            # Paddle held beside the crew; at rest blade is outside hull.
            p=clone('paddle' if team=='red' else 'paddle_jade',f'{team}_paddle_{row}_{s}',(x+.42,s*.66,1.51),parent=b)
            p.rotation_euler[0]=s*.40
            p['animation_pivot']='grip';p['row']=row;p['side']=s
    clone('drum',team+'_drum',(3.35,0,1.00),parent=b)
    clone('drummer_stool',team+'_drummer_stool',(4.25,0,.918),parent=b)
    clone('drummer_'+team,team+'_drummer',(4.25,0,1.15),pi,parent=b)
    # Seated drummer faces the stern (-X), with sticks reaching back to the drum.
    for s in (-1,1):
        o=rod(team+'_drumstick',(3.89,s*.22,1.77),(3.35,s*.12,1.67),.018,'wood');o.parent=b
    clone('helmsman_'+team,team+'_helmsman',(-4.12,0,.91),parent=b)
    p=clone('paddle',team+'_steering_oar',(-3.72,-.29,2.21),parent=b);p.rotation_euler=(.45,-.6,0)
    clone('pennant_'+team,team+'_pennant',(-4.45,.18,.98),parent=b)
    return b

# Hide prototypes during scene renders; still export them separately.
proto_objects=set(o for r in assets.values() for o in descendants(r))
for o in proto_objects:o.hide_render=True;o.hide_set(True)
red=boat('red');jade=boat('jade');red.location=(-5,-2.2,0);jade.location=(-6,2.2,0)
for b in (red,jade):
    for o in descendants(b):o.hide_render=False;o.hide_set(False)
scene_roots=[red,jade]
def place(proto,name,loc=(0,0,0),rot=0):
    r=clone(proto,name,loc,rot)
    for o in descendants(r):o.hide_render=False;o.hide_set(False)
    scene_roots.append(r);return r
layout_huizhou()

# Verify that copied upper arms still meet their shoulder pivots.
bpy.context.view_layer.update()
for b in (red,jade):
    for o in descendants(b):
        if o.type=='MESH' and '__upper_arm' in o.name:
            zmin=min(v.co.z for v in o.data.vertices);zmax=max(v.co.z for v in o.data.vertices)
            ends=[o.matrix_world@Vector((0,0,z)) for z in (zmin,zmax)]
            assert min((p-o.parent.matrix_world.translation).length for p in ends)<1e-4,('detached shoulder',o.name)

# Apply modifiers to copied evaluated meshes at export; UVs use dominant-axis projection.
def evaluated(o):
    dg=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dg)
    m=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);m.calc_loop_triangles();return ev,m
CV=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
def export_obj(name,root):
    path=MODELS/(name+'.obj');lines=['# Original course project assets. Y-up; +X forward.','mtllib palette.mtl']
    idx=1;tris=0;lo=[float('inf')]*3;hi=[-float('inf')]*3
    bpy.context.view_layer.update()
    for o in descendants(root):
        if o.type!='MESH':continue
        ev,m=evaluated(o); xf=CV@root.matrix_world.inverted()@o.matrix_world;norm=xf.to_3x3().inverted().transposed()
        lines.append('o '+o.name.replace(' ','_'))
        oldmat=None;vertex_cache={};mirrored=xf.to_3x3().determinant()<0
        for tri in m.loop_triangles:
            pts=[xf@m.vertices[k].co for k in tri.vertices]
            if (pts[1]-pts[0]).cross(pts[2]-pts[0]).length<1e-9:continue
            rounded=[Vector(tuple(round(float(c),6) for c in p)) for p in pts]
            if (rounded[1]-rounded[0]).cross(rounded[2]-rounded[0]).length<=1e-9:continue
            if (rounded[1]-rounded[0]).cross(rounded[2]-rounded[0]).dot((pts[1]-pts[0]).cross(pts[2]-pts[0]))<=0:continue
            mat=o.data.materials[min(tri.material_index,len(o.data.materials)-1)].name
            if mat!=oldmat:lines.append('usemtl '+mat);oldmat=mat
            n=(norm@tri.normal).normalized()
            # Mirrored crew instances have negative determinants: reverse winding.
            if mirrored:
                pts[1],pts[2]=pts[2],pts[1]
                vindices=list(tri.vertices);lindices=list(tri.loops)
                vindices[1],vindices[2]=vindices[2],vindices[1];lindices[1],lindices[2]=lindices[2],lindices[1]
            else:vindices=tri.vertices;lindices=tri.loops
            refs=[]
            for k,(vi,li) in enumerate(zip(vindices,lindices)):
                p=pts[k]
                if m.uv_layers.active:uv=m.uv_layers.active.data[li].uv
                else:
                    a=max(range(3),key=lambda a:abs(n[a]));uv=(p[(a+1)%3],p[(a+2)%3])
                sn=(norm@m.corner_normals[li].vector).normalized()
                if sn.dot(n)<.05:sn=n
                record=('v %.6f %.6f %.6f\n'%tuple(p))+('vt %.6f %.6f\n'%tuple(uv))+('vn %.6f %.6f %.6f'%tuple(sn))
                index=vertex_cache.get(record)
                if index is None:
                    index=idx;idx+=1;vertex_cache[record]=index;lines.append(record)
                    for axis in range(3):lo[axis]=min(lo[axis],p[axis]);hi[axis]=max(hi[axis],p[axis])
                refs.append(index)
            lines.append('f '+' '.join(f'{i}/{i}/{i}' for i in refs));tris+=1
        ev.to_mesh_clear()
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return {'file':path.name,'triangles':tris,'vertices':idx-1,'min':lo,'max':hi}

# Add UVs to source meshes, so Blender and GLB also contain complete texture coordinates.
for m in bpy.data.meshes:
    if m.uv_layers.active:continue
    uv=m.uv_layers.new(name='UVMap')
    for p in m.polygons:
        a=max(range(3),key=lambda a:abs(p.normal[a]))
        for li in p.loop_indices:
            co=m.vertices[m.loops[li].vertex_index].co
            uv.data[li].uv=(co[(a+1)%3],co[(a+2)%3])

if '--design-preview' in sys.argv:
    exec((ROOT/'tools/render_boat_design.py').read_text(encoding='utf-8'),globals())
    raise SystemExit(0)
if '--environment-preview' in sys.argv:
    exec((ROOT/'tools/render_riverside_design.py').read_text(encoding='utf-8'),globals())
    raise SystemExit(0)
inventory=[]
for name,root in assets.items():inventory.append(export_obj(name,root))
inventory.append(export_obj('dragon_boat_red',red));inventory.append(export_obj('dragon_boat_jade',jade))
exec((ROOT/'tools/restore_texture_paths.py').read_text(encoding='utf-8'),globals())
restore_material_image_paths()
mtl=[]
for name,m in M.items():
    images=[tex.image for tex in m.node_tree.nodes if tex.type=='TEX_IMAGE' and tex.image]
    diffuse=bpy.data.images.get(m.get('obj_base_image',''))
    if diffuse is None:diffuse=next((im for im in images if im.colorspace_settings.name=='sRGB'),None)
    if 'obj_solid_color' in m:diffuse=None
    kd=m.get('obj_diffuse_tint',(1,1,1)) if diffuse else m.diffuse_color[:3]
    bs=m.node_tree.nodes.get('Principled BSDF');rough=bs.inputs['Roughness'].default_value if bs else .75
    ks=.03+.25*(1-rough)
    mtl+=['newmtl '+name,'Ka 0.18 0.18 0.18','Kd '+' '.join(f'{x:.5f}' for x in kd),f'Ks {ks:.4f} {ks:.4f} {ks:.4f}',f'Ns {max(4,128*(1-rough)**2):.2f}','d 1']
    if diffuse:mtl+=['map_Kd ../textures/'+Path(bpy.path.abspath(diffuse.filepath)).name]
    normal=bpy.data.images.get(m.get('obj_normal_image','')) or next((im for im in images if 'normal' in im.name.lower() or 'nor_gl' in im.name.lower()),None)
    if normal is None and bs and bs.inputs['Normal'].links:
        nn=bs.inputs['Normal'].links[0].from_node
        if nn.type=='NORMAL_MAP' and nn.inputs['Color'].links:
            tn=nn.inputs['Color'].links[0].from_node
            if tn.type=='TEX_IMAGE':normal=tn.image
    if normal:mtl+=['map_Bump ../textures/'+Path(bpy.path.abspath(normal.filepath)).name]
    if diffuse and any(n.type=='BSDF_PRINCIPLED' and n.inputs['Alpha'].links for n in m.node_tree.nodes):mtl+=['map_d ../textures/'+Path(bpy.path.abspath(diffuse.filepath)).name]
    mtl.append('')
(MODELS/'palette.mtl').write_text('\n'.join(mtl),encoding='utf-8')

# Scene graph contains all local transforms, including shoulder and paddle pivots.
def arr(v):return [round(float(x),6) for x in v]
for r in scene_roots:
    for o in descendants(r):
        nodes.append({'name':o.name,'parent':o.parent.name if o.parent else None,'asset':o.get('asset'),'render_mode':o.get('render_mode'),
                      'type':o.type,'local_matrix_zup':[arr(row) for row in o.matrix_local],
                      'world_matrix_yup':[arr(row) for row in CV@o.matrix_world@CV.inverted()]})
(MODELS/'scene_layout.json').write_text(json.dumps({'units':'metres','obj_axes':'Y up, +X forward','scene_internal_axes':'Z up','nodes':nodes},ensure_ascii=False,indent=2),encoding='utf-8')
(MODELS/'inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')

# Export a unified scene OBJ with all meshes in world coordinates.
worldroot=empty('world_export')
for r in scene_roots:r.parent=worldroot
inventory.append(export_obj('scene_preview',worldroot))
(MODELS/'inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')

# Native editable source and GLB (hierarchy, materials and packed image textures).
for im in bpy.data.images:
    if im.source=='FILE':im.pack()
for o in bpy.context.selected_objects:o.select_set(False)
for r in scene_roots:
    for o in descendants(r):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(MODELS/'dragonboat_scene.glb'),use_selection=True,export_format='GLB',export_apply=True)
exec((ROOT/'tools/fix_sky_glb.py').read_text(encoding='utf-8'),globals());ensure_unlit_sky(MODELS/'dragonboat_scene.glb')
for o in list(bpy.context.selected_objects):o.select_set(False)

scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24
exec((ROOT/'tools/configure_render_device.py').read_text(encoding='utf-8'),globals())
scene.cycles.use_denoising=True;scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world.color=(.30,.35,.40)
world=scene.world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.38,.48,.55,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65
configure_open_environment(world)
for n in world.node_tree.nodes:
    if n.type=='BACKGROUND' and not n.inputs['Color'].links:n.inputs['Color'].default_value=(.43,.48,.48,1)
scene.view_settings.view_transform='AgX'
def area(name,loc,power,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler();return o
area('warm_key',(-9,-12,22),4800,14);area('cool_fill',(8,9,16),2800,12)
sun=bpy.data.lights.new('sun','SUN');sun.energy=1.1;sun.angle=.25
so=bpy.data.objects.new('sun',sun);bpy.context.collection.objects.link(so);so.rotation_euler=(.5,-.3,-.5)
camd=bpy.data.cameras.new('Camera');cam=bpy.data.objects.new('Camera',camd);bpy.context.collection.objects.link(cam);scene.camera=cam;camd.clip_end=2000
def camera(loc,target,ortho):
    cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();camd.type='ORTHO';camd.ortho_scale=ortho
def render(name,loc,target,ortho):
    camera(loc,target,ortho)
    if name!='05_asset_library':
        camd.type='PERSP';camd.lens={'01_scene_overview':35,'11_huizhou_overview':35,'12_old_town_street':32,'13_huizhou_courtyard':42,'14_weathered_quay':40,'03_dragon_head':65}.get(name,45)
    scene.render.filepath=str(PRE/(name+'.png'))
    if 'render_preview_frame' in globals():render_preview_frame()
    else:bpy.ops.render.render(write_still=True)
camera((32,-44,22),(0,4,3),58);camd.type='PERSP';camd.lens=35
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.region_3d.view_perspective='CAMERA'
            a.spaces.active.shading.color_type='MATERIAL'
bpy.context.preferences.filepaths.save_version=0
scene.cycles.device='CPU';bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
configure_preview_device()
render('01_scene_overview',(32,-44,22),(0,4,3),58)
shutil.copy2(PRE/'01_scene_overview.png',PRE/'11_huizhou_overview.png')
render('12_old_town_street',(-22,7.85,1.75),(1,8.4,2.6),22)
shutil.copy2(PRE/'12_old_town_street.png',PRE/'06_riverside_architecture.png')
render('13_huizhou_courtyard',(-13,13.3,10),(-14.4,16.25,1.5),22)
render('14_weathered_quay',(2,-1,3.3),(4,-6.6,.55),12)
render('07_finish_and_bridge',(9,-18,12),(19,0,2.2),26)
render('08_festival_stall',(-6,-3,4.5),(-10,-9.1,1.2),9)
render('09_mooring_dock',(-5,1,6),(-12,-5.3,.7),12)
scene.render.resolution_x=2560;scene.render.resolution_y=1280;camd.type='PANO';camd.panorama_type='EQUIRECTANGULAR'
cam.location=(0,0,6);cam.rotation_euler=Vector((1,0,0)).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(PRE/'15_environment_360.png');render_preview_frame()
scene.render.resolution_x=1600;scene.render.resolution_y=1000
for name,loc,target in [('16_view_east',(-8,0,9),(70,0,8)),('17_view_south',(0,1,10),(0,-75,10)),('18_view_west',(8,0,9),(-70,0,8)),('19_view_north',(0,-1,10),(0,75,10))]:render(name,loc,target,120)
render('20_panorama_aerial',(115,-145,112),(0,0,2),260)
# Close inspection of the red boat on a neutral studio floor.
for r in scene_roots:
    if r!=red:
        for o in descendants(r):o.hide_render=True
red.location=(0,0,0);bpy.context.view_layer.update()
floor=box('studio_floor',(0,0,-.65),(200,200,.12),'plaster',0)
render('02_dragon_boat',(12,-17,11),(0,0,1),16.8)
render('03_dragon_head',(10,-6,4.5),(5.45,0,1.8),4.6)
render('04_boat_side',(1,-20,6),(0,0,1.1),15.5)
render('10_seated_drummer',(2,-5,3.3),(3.8,0,1.3),4)
for o in descendants(red):o.hide_render=True
floor.hide_render=False
# Contact-sheet style asset layout, each assembled independently.
grid=['riverside_house','huizhou_tall_house','huizhou_tea_house','huizhou_courtyard','quay_segment','household_props','laundry_rack','pavilion','mooring_dock']
display=[]
for i,name in enumerate(grid):
    x=(i%3)*8;y=-(i//3)*8
    o=clone(name,'display_'+name,(x,y,0))
    if name=='paddle':o.location.z=2.12
    if name=='finish_gate':o.rotation_euler[2]=pi/2;o.scale=(.55,.55,.55)
    if name=='arch_bridge':o.rotation_euler[2]=pi/2;o.scale=(.55,.55,.55)
    for child in descendants(o):child.hide_render=False;child.hide_set(False)
    display.append(o)
render('05_asset_library',(30,-35,30),(8,-8,1.7),34)
print('MODELING_COMPLETE',json.dumps({'assets':len(assets),'obj_files':len(inventory),'triangles_scene':inventory[-1]['triangles']}),flush=True)
