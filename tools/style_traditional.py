"""Active modeling overrides, executed in build_models.py's Blender namespace.
Carved timber and a restrained riverside setting; no toy/block characters.
"""
# Muted, rough surfaces. Keep cloth separate from lacquered carving.
for name,color,rough,metal in [
 ('gold',(.39,.25,.085),.57,.48),('ivory',(.29,.21,.12),.65,0),
 ('skin',(.43,.25,.14),.75,0),('hair',(.025,.022,.017),.85,0),
 ('white',(.56,.47,.30),.72,0),('plaster',(.56,.54,.47),.95,0),
 ('leaf',(.055,.12,.045),.85,0),('leaflight',(.12,.20,.065),.88,0),
 ('grass',(.16,.20,.115),.96,0),('water',(.055,.105,.09),.20,.1),
 ('darkwood',(.055,.039,.026),.72,0)]:
    m=M[name];m.diffuse_color=(*color,1);b=m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
material('lacquer_red',(.24,.026,.018),rough=.48)
material('lacquer_jade',(.025,.092,.063),rough=.52)
material('eye_amber',(.33,.18,.045),rough=.4)
material('linen',(.46,.43,.34),rough=.95)
material('trousers',(.045,.055,.06),rough=.95)
material('bark',(.10,.077,.052),rough=.96)
material('skin_shadow',(.32,.17,.095),rough=.85)

def loft(name,sections,mat,n=24):
    """Cross sections are x,y,z,width,height; end caps avoid zero-radius poles."""
    vs=[];fs=[]
    for x,y,z,w,h in sections:
        for j in range(n):
            t=2*pi*j/n;vs.append((x,y+w*cos(t),z+h*sin(t)))
    for i in range(len(sections)-1):
        for j in range(n):a=i*n+j;b=i*n+(j+1)%n;fs.append((a,b,b+n,a+n))
    fs.extend([tuple(reversed(range(n))),tuple((len(sections)-1)*n+j for j in range(n))])
    o=mesh(name,vs,fs,mat)
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    return o

def bent(name,points,r,mat):
    # Catmull-Rom interpolation gives horns, muscles and branches curved silhouettes.
    if len(points)>10:
        o=tube(name,points,r,mat)
        for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
        return o
    dense=[];pp=[Vector(points[0])]+[Vector(p) for p in points]+[Vector(points[-1])]
    for i in range(1,len(pp)-2):
        a,b,c,d=pp[i-1:i+3]
        for k in range(5):
            t=k/5;dense.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    dense.append(Vector(points[-1]));o=tube(name,dense,r,mat)
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    return o

def hull(team):
    ns=64;nt=22;v=[];f=[]
    for inner in (False,True):
        for i in range(ns+1):
            x=-4.9+9.8*i/ns;w=.84*(.10+.90*sin(pi*i/ns)**.48)
            lift=.23*(abs(x)/4.9)**5
            for j in range(nt+1):
                t=-pi/2+pi*j/nt
                v.append((x,(w-(.045 if inner else 0))*sin(t),.80+lift-(.57-(.055 if inner else 0))*cos(t)))
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
    o=mesh('planked_timber_hull',v,f,'wood')
    for p in o.data.polygons:p.use_smooth=True
    for s in (-1,1):
        for z,r,mat in ((.82,.032,'darkwood'),(.68,.014,'gold'),(.57,.019,'lacquer_'+team)):
            pts=[(-4.9+9.8*i/ns,s*.84*(.10+.90*sin(pi*i/ns)**.48),z+.23*(abs(-4.9+9.8*i/ns)/4.9)**5) for i in range(ns+1)]
            bent('slender_gunwale',pts,r,mat)
        # Longitudinal seams are flush to the hull, not large scale-shaped plates.
        for t in (.30,.58,.91,1.25):
            pts=[]
            for i in range(1,ns):
                x=-4.9+9.8*i/ns;w=.84*(.10+.90*sin(pi*i/ns)**.48)
                pts.append((x,s*(w+.003)*sin(t),.80+.23*(abs(x)/4.9)**5-.57*cos(t)))
            bent('plank_seam',pts,.006,'darkwood')
    for x in (-3,-1.9,-.8,.3,1.4,2.5):
        box('narrow_thwart',(x,0,.76),(.22,1.34,.075),'wood',.009)
        for s in (-1,1):sphere('iron_fastener',(x,s*.60,.803),(.015,.015,.006),'black',8,4)
    for i in range(6):box('foredeck_plank',(3.11+i*.20,0,.87),(.19,1.02,.075),'wood',.006)
    box('stern_deck',(-4.05,0,.80),(.65,.66,.09),'wood',.008)

def dragon_head(team):
    mat='lacquer_'+team
    loft('carved_neck',[(4.62,0,.82,.17,.16),(4.82,0,.97,.22,.25),(4.98,0,1.24,.25,.31),(5.13,0,1.49,.30,.32),(5.36,0,1.59,.34,.28)],mat)
    loft('angular_cranium',[(5.03,0,1.61,.23,.23),(5.23,0,1.72,.35,.30),(5.49,0,1.72,.32,.25),(5.71,0,1.61,.23,.17),(6.02,0,1.59,.20,.13),(6.34,0,1.66,.23,.16),(6.45,0,1.63,.13,.10),(6.51,0,1.63,.025,.025)],mat)
    loft('lower_carved_jaw',[(5.34,0,1.35,.20,.045),(5.70,0,1.30,.22,.05),(6.08,0,1.31,.20,.048),(6.36,0,1.41,.12,.05),(6.44,0,1.43,.025,.012)],mat)
    loft('mouth_recess',[(5.58,0,1.40,.215,.022),(5.94,0,1.42,.205,.025),(6.30,0,1.49,.16,.02)],'darkwood')
    for s in (-1,1):
        sphere('recessed_eye',(5.43,s*.302,1.81),(.085,.026,.060),'eye_amber',20,12)
        sphere('slit_pupil',(5.46,s*.327,1.81),(.023,.008,.042),'black',16,10)
        bent('carved_brow',[(5.17,s*.27,1.93),(5.36,s*.34,1.94),(5.61,s*.27,1.88)],.043,'gold')
        bent('cheek_ridge',[(5.19,s*.31,1.65),(5.42,s*.34,1.54),(5.72,s*.25,1.53)],.036,'gold')
        bent('swept_antler',[(5.12,s*.23,1.94),(4.94,s*.28,2.17),(4.83,s*.30,2.40),(4.62,s*.36,2.51)],.071,'ivory')
        bent('antler_fork',[(4.92,s*.29,2.21),(5.04,s*.36,2.41),(4.99,s*.41,2.55)],.041,'ivory')
        bent('nostril_rim',[(6.22,s*.12,1.78),(6.32,s*.18,1.77),(6.37,s*.16,1.73)],.025,'gold')
        sphere('nostril',(6.31,s*.165,1.78),(.045,.027,.022),'black',16,8)
        bent('long_whisker',[(6.30,s*.20,1.58),(6.48,s*.42,1.50),(6.15,s*.65,1.58),(5.95,s*.67,1.73)],.018,'gold')
        for x in (5.85,6.12):rod('small_tooth',(x,s*.185,1.48),(x+.025,s*.18,1.385),.022,'white',r2=.003,n=8)
        for i in range(5):
            x=5.1-i*.08
            bent('swept_carved_mane',[(x,s*.22,1.76-i*.08),(x-.25,s*.32,1.79-i*.08),(x-.46,s*.31,1.95-i*.07)],.062,'gold' if i%2==0 else mat)
    for j in range(3):
        y=(j-1)*.11
        bent('beard',[(5.49,y,1.31),(5.34,y,1.12),(5.12,y,.99)],.025,'ivory')

def dragon_tail(team):
    mat='lacquer_'+team
    bent('curled_tail',[(-4.72,0,.78),(-5.12,0,.94),(-5.51,0,1.14),(-5.73,0,1.43),(-5.69,0,1.73)],.16,mat)
    for i in range(5):
        y=(i-2)*.07
        bent('tail_carving',[(-5.36,y,1.13),(-5.72,y*1.8,1.35),(-5.95,y*2,1.67),(-5.86,y*2,1.94)],.042,'gold' if i%2==0 else mat)

def person(team,standing=False,role='rower'):
    hip=.85 if standing else .22
    # Tapered hip, waist, ribcage and shoulder sections rather than a cube torso.
    sphere('pelvis',(0,0,hip),(.145,.20,.17),'trousers',20,12)
    # Torso rings use Z as the long axis and lean slightly forward into the stroke.
    vs=[];fs=[];n=20
    sections=[(hip+.08,.11,.16,-.03),(hip+.19,.12,.17,-.01),(hip+.38,.145,.215,.015),(hip+.53,.13,.235,.035),(hip+.60,.09,.18,.04)]
    for z,depth,width,x in sections:
        for j in range(n):t=2*pi*j/n;vs.append((x+depth*cos(t),width*sin(t),z))
    for i in range(len(sections)-1):
        for j in range(n):a=i*n+j;b=i*n+(j+1)%n;fs.append((a,b,b+n,a+n))
    fs+=[tuple(reversed(range(n))),tuple((len(sections)-1)*n+j for j in range(n))]
    o=mesh('tailored_sleeveless_jersey',vs,fs,team)
    for p in o.data.polygons:p.use_smooth=True
    rod('neck',(.035,0,hip+.58),(.07,0,hip+.70),.06,'skin',r2=.055,n=16)
    sphere('human_skull',(.085,0,hip+.83),(.11,.10,.17),'skin',24,16)
    sphere('nose',(.191,0,hip+.84),(.026,.021,.038),'skin',16,10)
    sphere('close_cropped_hair',(.064,0,hip+.935),(.112,.107,.075),'hair',24,12)
    for s in (-1,1):
        sphere('ear',(.065,s*.105,hip+.83),(.025,.017,.044),'skin',12,8)
        bent('eyebrow',[(.185,s*.035,hip+.88),(.185,s*.071,hip+.88)],.006,'hair')
        # Eyes remain subtle at scene scale; no large black toy beads.
        sphere('eye',(.188,s*.055,hip+.865),(.006,.011,.005),'black',10,6)
        if standing:
            rod('trouser_leg',(-.02,s*.11,.12),(0,s*.11,.77),.082,'trousers',r2=.10,n=16)
            sphere('cloth_shoe',(.07,s*.11,.065),(.145,.075,.058),'darkwood',16,10)
        else:
            rod('shorts_leg',(0,s*.11,.22),(.32,s*.11,.19),.093,'trousers',r2=.078,n=16)
            sphere('knee',(.33,s*.11,.17),(.075,.075,.078),'skin',16,10)
            rod('shin',(.34,s*.11,.14),(.40,s*.11,-.16),.052,'skin',r2=.041,n=16)
            sphere('cloth_shoe',(.47,s*.11,-.19),(.13,.063,.045),'darkwood',16,10)
    for s in (-1,1):
        before=begin();shoulder=(.035,s*.23,hip+.51)
        a=empty('shoulder_L' if s==1 else 'shoulder_R',shoulder)
        elbow=(.26,s*.30,hip+.29)
        hand=(.48,.44,hip+.47+(0.10 if s<0 else 0)) if role=='rower' else (.48,s*.44,hip+.47)
        rod('upper_arm',shoulder,elbow,.056,'skin',r2=.046,n=16)
        sphere('elbow',elbow,(.048,.048,.048),'skin',16,10)
        rod('forearm',elbow,hand,.046,'skin',r2=.031,n=16)
        sphere('hand',hand,(.053,.038,.035),'skin',16,10)
        bpy.context.view_layer.update()
        for o in set(bpy.data.objects)-before:
            if o!=a:o.parent=a;o.matrix_parent_inverse=a.matrix_world.inverted()

def paddle(team='red'):
    rod('timber_shaft',(0,0,.12),(0,0,-1.44),.021,'wood',n=16)
    # Thin curved wooden blade, wider at the tip and almost unpainted.
    loft('shaped_paddle_blade',[(-.125,0,-1.4,.019,.08),(-.06,0,-1.65,.025,.25),(.04,0,-1.67,.025,.27),(.14,0,-1.67,.018,.25)],'wood',n=16)
    rod('grip',(-.08,0,.12),(.08,0,.12),.025,'darkwood',n=12)

def tree():
    # Willow: irregular trunk, fine branch structure and hanging leaf sprays.
    bent('willow_trunk',[(0,0,0),(.10,.02,1.1),(-.08,.04,2.1),(.08,0,3.0)],.17,'bark')
    rng=random.Random(103);verts=[];faces=[]
    for i in range(13):
        a=i*2.399;reach=rng.uniform(.8,1.65);z=rng.uniform(2.5,3.7)
        start=(0,0,1.6+i*.065);end=(reach*cos(a),reach*sin(a),z)
        bent('willow_branch',[start,(end[0]*.55,end[1]*.55,z-.2),end],.055,'bark')
        for j in range(8):
            t=.35+j*.09;x=end[0]*t+rng.uniform(-.12,.12);y=end[1]*t+rng.uniform(-.12,.12);top=z-.12+sin(t*pi)*.25+rng.uniform(-.15,.15)
            drop=rng.uniform(.8,1.8);pts=[]
            for k in range(6):
                u=k/5;pts.append((x+.14*u*cos(a+.6),y+.14*u*sin(a+.6),top-drop*u))
            bent('drooping_twig',pts,.009,'bark')
            for k in range(14):
                u=(k+.5)/14;zz=top-drop*u;xx=x+.14*u*cos(a+.6);yy=y+.14*u*sin(a+.6)
                for s in (-1,1):
                    ang=a+s*.8+rng.uniform(-.3,.3);dx=.08*cos(ang);dy=.08*sin(ang);w=.032
                    c=len(verts);verts.extend([(xx,yy,zz),(xx+dx-w*sin(ang),yy+dy+w*cos(ang),zz-.09),(xx+dx*1.5,yy+dy*1.5,zz-.20),(xx+dx+w*sin(ang),yy+dy-w*cos(ang),zz-.09)])
                    faces.append((c,c+1,c+2,c+3))
    o=mesh('willow_leaves',verts,faces,'leaflight')

def rock():
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=(0,0,.20));o=bpy.context.object
    for v in o.data.vertices:
        v.co.x*=.75+.10*sin(v.co.z*8);v.co.y*=.45;v.co.z*=.40
    finish(o,'weathered_bank_rock','stone')

# Architectural silhouettes stay simple; reduce the bright, gold-edged toy treatment.
_old_pavilion=pavilion
def pavilion():
    before=begin();_old_pavilion()
    for o in set(bpy.data.objects)-before:
        if o.type=='MESH' and ('dougong' in o.name):o.data.materials.clear();o.data.materials.append(M['darkwood'])
_old_house=house
def house():
    before=begin();_old_house()
    for o in set(bpy.data.objects)-before:
        if o.type=='MESH' and 'lattice' in o.name:o.data.materials.clear();o.data.materials.append(M['darkwood'])
