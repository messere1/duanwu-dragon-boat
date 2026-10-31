"""Original riverside architecture and festival props, in metres, Z up.
Loaded after the approved boat overrides; leaves the boat parts unchanged.
"""
material('limewash',(.58,.56,.49),'limewash.png',rough=.94)
material('cut_limestone',(.36,.38,.35),'cut_limestone.png',rough=.89)
material('tile_grey',(.09,.105,.10),'roof.png',rough=.82)
material('window_shadow',(.028,.043,.043),rough=.4)
material('aged_iron',(.045,.045,.038),metal=.55,rough=.55)
material('bamboo',(.27,.23,.11),rough=.7)
material('basket_fibre',(.34,.24,.12),rough=.85)
material('zongzi_leaf',(.08,.15,.055),rough=.64)
material('reed_leaf',(.14,.21,.075),rough=.82)
material('canvas',(.58,.50,.34),'canvas.png',rough=.96)
material('ceramic',(.36,.42,.37),rough=.3)
material('paving',(.38,.37,.31),'paving.png',rough=.92)
material('festival_sign',(.3,.1,.06),'stall_sign.png',rough=.82)

def _rbox(name,loc,scale,mat,bevel=.025):
    # Direct datablocks avoid repeated whole-scene operator updates.
    vs=[(x*scale[0]/2,y*scale[1]/2,z*scale[2]/2) for x,y,z in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    o=mesh(name,vs,[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],mat);o.location=loc
    if bevel:
        m=o.modifiers.new('small_edge_bevel','BEVEL');m.width=bevel;m.segments=2
        o.modifiers.new('weighted_normals','WEIGHTED_NORMAL')
    return o

def _rrod(name,a,b,r,mat,r2=None,n=10):
    a,b=Vector(a),Vector(b);delta=b-a;h=delta.length;r2=r if r2 is None else r2
    assert h>1e-6 and r>0 and r2>0,(name,'invalid rod')
    vs=[(rr*cos(2*pi*i/n),rr*sin(2*pi*i/n),z) for rr,z in ((r,-h/2),(r2,h/2)) for i in range(n)]
    fs=[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]+[tuple(reversed(range(n))),tuple(range(n,2*n))]
    o=mesh(name,vs,fs,mat);o.location=(a+b)/2;o.rotation_euler=delta.to_track_quat('Z','Y').to_euler()
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    return o

def _rsphere(name,loc,scale,mat,seg=12,rings=8):
    vs=[(0,0,scale[2]),(0,0,-scale[2])];fs=[]
    for j in range(1,rings):
        t=pi*j/rings
        for i in range(seg):
            a=2*pi*i/seg;vs.append((scale[0]*sin(t)*cos(a),scale[1]*sin(t)*sin(a),scale[2]*cos(t)))
    for i in range(seg):fs.append((0,2+i,2+(i+1)%seg));fs.append((1,2+(rings-2)*seg+(i+1)%seg,2+(rings-2)*seg+i))
    for j in range(rings-2):
        for i in range(seg):
            a=2+j*seg+i;b=2+j*seg+(i+1)%seg;fs.append((a,b,b+seg,a+seg))
    o=mesh(name,vs,fs,mat);o.location=loc
    for p in o.data.polygons:p.use_smooth=True
    return o

def ring(name,center,radius,thick,mat,n=32):
    # Constant-radius closed mesh torus; no duplicated end cap or zero-length edge.
    vs=[];fs=[];cx,cy,cz=center
    for i in range(n):
        a=2*pi*i/n
        for j in range(6):
            b=2*pi*j/6;rr=radius+thick*cos(b)
            vs.append((rr*cos(a),rr*sin(a),thick*sin(b)))
    for i in range(n):
        for j in range(6):
            a=i*6+j;b=((i+1)%n)*6+j;c=((i+1)%n)*6+(j+1)%6;d=i*6+(j+1)%6
            fs.append((a,b,c,d))
    o=mesh(name,vs,fs,mat);o.location=center
    for p in o.data.polygons:p.use_smooth=True
    return o

def roof(name,cx,cy,z,hx,hy,height,mat='tile_grey'):
    # All tile channels share two meshes rather than thousands of objects.
    nx=max(20,round(2*hx/.155));ny=20
    def shape(x,t):return z+height*(1-t)**1.6+.15*t**4+.14*(abs(x)/hx)**8*t**3
    for side in (-1,1):
        vs=[];fs=[]
        for i in range(nx+1):
            x=-hx+2*hx*i/nx
            for j in range(ny+1):
                t=j/ny;vs.append((cx+x,cy+side*hy*t,shape(x,t)-.045))
        for i in range(nx):
            for j in range(ny):
                a=i*(ny+1)+j;fs.append((a,a+ny+1,a+ny+2,a+1))
        o=mesh(name+'_roof_board',vs,fs,'darkwood');m=o.modifiers.new('closed_eave_board','SOLIDIFY');m.thickness=.075
        vs=[];fs=[]
        for k in range(nx):
            xc=-hx+(k+.5)*2*hx/nx;width=2*hx/nx
            start=len(vs)
            for j in range(ny+1):
                t=j/ny
                for a in range(7):
                    u=a/6;x=xc+(u-.5)*width
                    # Curved barrel cap and small overlap lips along the slope.
                    lip=.012 if j%2==0 else 0
                    vs.append((cx+x,cy+side*hy*t,shape(x,t)+.035*sin(pi*u)+lip))
            for j in range(ny):
                for a in range(6):
                    p=start+j*7+a;fs.append((p,p+7,p+8,p+1))
        o=mesh(name+'_barrel_tile_channels',vs,fs,'tile_grey')
        for p in o.data.polygons:p.use_smooth=True
        # Eave end disks and visible horizontal fascia.
        for i in range(nx):
            x=-hx+(i+.5)*2*hx/nx;zz=shape(x,1)
            _rrod('tile_eave_end',(cx+x,cy+side*(hy-.02),zz),(cx+x,cy+side*(hy+.035),zz),.043,'tile_grey',n=10)
        bent('eave_fascia',[(cx-hx+2*hx*i/24,cy+side*hy,shape(-hx+2*hx*i/24,1)-.07) for i in range(25)],.055,'darkwood')
    _rrod('ceramic_roof_ridge',(cx-hx,cy,z+height+.07),(cx+hx,cy,z+height+.07),.095,'tile_grey',n=16)
    for s in (-1,1):
        bent('swept_ridge_end',[(cx+s*(hx-.35),cy,z+height+.07),(cx+s*hx,cy,z+height+.14),(cx+s*(hx+.12),cy,z+height+.34)],.075,'tile_grey')

def bracket(x,y,z,axis=0):
    for j,(w,dz) in enumerate(((.40,0),(.65,.15),(.85,.29))):
        o=_rbox('timber_bracket_course',(x,y,z+dz),(w,.17,.13),'darkwood',.012);o.rotation_euler[2]=axis
    for s in (-1,1):
        a=Vector((s*.12,0,0));b=Vector((s*.37,0,.29));rot=Matrix.Rotation(axis,3,'Z')
        _rrod('bracket_diagonal',Vector((x,y,z))+rot@a,Vector((x,y,z))+rot@b,.045,'wood',n=8)

def lattice_window(x,y,z,w=1.0,h=1.12):
    _rbox('recessed_window',(x,y+.025,z),(w,.06,h),'window_shadow',.005)
    for dx in (-w/2,w/2):_rbox('window_jamb',(x+dx,y-.015,z),(.055,.09,h+.1),'darkwood',.008)
    for dz in (-h/2,h/2):_rbox('window_sill',(x,y-.025,z+dz),(w+.12,.14,.06),'wood',.008)
    for i in range(5):_rbox('lattice_vertical',(x-w*.4+i*w*.2,y-.05,z),(.027,.025,h-.05),'wood',.003)
    for dz in (-h*.32,0,h*.32):_rbox('lattice_horizontal',(x,y-.055,z+dz),(w-.03,.025,.025),'wood',.003)
    # Central diamond motif.
    for a,b in [((-.17,0),(0,.17)),((0,.17),(.17,0)),((.17,0),(0,-.17)),((0,-.17),(-.17,0))]:
        _rrod('lattice_diamond',(x+a[0],y-.06,z+a[1]),(x+b[0],y-.06,z+b[1]),.014,'wood',n=6)

def house():
    _rbox('house_plinth',(0,0,.12),(4.35,3.5,.24),'cut_limestone',.04)
    _rbox('house_limewashed_walls',(0,0,1.51),(3.9,2.95,2.66),'limewash',.035)
    for y in (-1.5,1.5):
        for j in range(3):
            for k in range(9):_rbox('brick_damp_course',(-1.79+k*.447,y,.24+j*.13),(.435,.06,.116),'cut_limestone',.008)
    for x in (-1.88,0,1.88):_rbox('exposed_facade_post',(x,-1.51,1.51),(.115,.10,2.65),'darkwood',.012)
    _rbox('facade_lintel',(0,-1.52,2.59),(3.92,.13,.17),'wood',.012)
    for s in (-1,1):lattice_window(s*1.15,-1.54,1.64,.79,1.13)
    for s in (-1,1):
        _rbox('double_door_leaf',(s*.217,-1.55,1.16),(.419,.075,1.95),'wood',.012)
        for z in (.54,1.08,1.7):_rbox('door_recess_panel',(s*.217,-1.598,z),(.30,.018,.36),'darkwood',.008)
        ring('door_pull',(s*.075,-1.625,1.12),.045,.009,'aged_iron',16).rotation_euler[0]=pi/2
    _rbox('threshold',(0,-1.66,.24),(1.05,.32,.14),'cut_limestone',.025)
    for i in range(2):_rbox('entrance_step',(0,-1.83-i*.22,.11-i*.055),(1.35,.27,.11),'cut_limestone',.02)
    for x in (-1.95,1.95):
        vs=[(x,-1.48,2.80),(x,1.48,2.80)]
        for j in range(17):
            y=1.48-2.96*j/16;t=abs(y)/1.96
            vs.append((x,y,2.84+.99*(1-t)**1.6+.15*t**4+.14*(abs(x)/2.30)**8*t**3-.025))
        mesh('curved_gable_infill',vs,[tuple(range(len(vs)))],'limewash')
    roof('house',0,0,2.84,2.30,1.96,.99)
    # Side-wall wooden shutters, shifted clear of the plaster.
    for s in (-1,1):
        o=_rbox('side_shutter',(s*1.977,.20,1.64),(.045,.83,1.0),'wood',.01)
        for j in range(7):_rbox('shutter_louvre',(s*2.005,.20,1.25+j*.13),(.025,.76,.035),'darkwood',.004)

def pavilion():
    _rbox('pavilion_base',(0,0,.12),(4.8,4.1,.24),'cut_limestone',.04)
    _rbox('pavilion_paved_floor',(0,0,.29),(4.4,3.7,.10),'paving',.02)
    for x in (-1.68,1.68):
        for y in (-1.30,1.30):
            _rrod('column_stone_drum',(x,y,.31),(x,y,.54),.21,'cut_limestone',n=16)
            _rrod('aged_red_column',(x,y,.5),(x,y,3.11),.12,'lacquer_red',n=16)
            bracket(x,y,2.69);bracket(x,y,2.69,pi/2)
    for y in (-1.3,1.3):_rbox('principal_beam',(0,y,3.00),(3.72,.19,.23),'wood',.012)
    for x in (-1.68,1.68):_rbox('cross_beam',(x,0,3.0),(.19,3.2,.23),'wood',.012)
    roof('pavilion',0,0,3.16,2.48,2.09,1.02)
    for x in (-1.55,1.55):
        _rbox('pavilion_side_bench',(x,0,.86),(.34,2.6,.12),'wood',.02)
        for y in (-.9,.9):_rbox('bench_leg',(x,y,.58),(.12,.15,.48),'darkwood',.01)
        for z in (.62,1.25):_rbox('side_railing',(x,0,z),(.07,2.6,.07),'darkwood',.01)
    _rbox('back_bench',(0,1.26,.86),(2.8,.36,.12),'wood',.02)
    plaque_quad('pavilion_inscription',(0,-1.416,2.64),(1.56,.39),'plaque')
    for j in range(3):_rbox('pavilion_stone_step',(0,-2.04-j*.24,.24-j*.08),(2.20,.30,.15),'cut_limestone',.02)

def quay(opening=False):
    _rbox('quay_structural_core',(0,0,-.02),(8,2,.76),'stone',.015)
    _rbox('quay_paving',(0,0,.39),(8,2,.09),'paving',.012)
    for y,z in ((1.04,.28),(1.27,.13)):_rbox('landward_walkway_step',(0,y,z),(8,.27,.15),'cut_limestone',.012)
    for j in range(3):
        for i in range(10):
            x=-3.60+i*.8+(.4 if j%2 else 0)
            if x>3.8:continue
            _rbox('facing_stone_block',(x,-.995,-.29+j*.23),(.78,.075,.215),'cut_limestone',.012)
    for i in range(10):_rbox('coping_stone',(-3.6+i*.8,-.87,.46),(.78,.31,.13),'cut_limestone',.018)
    for x in ((-3.9,-1.95,-1.35,1.35,1.95,3.9) if opening else (-3.9,-1.95,0,1.95,3.9)):
        _rbox('square_rail_base',(x,-.8,.58),(.27,.27,.14),'cut_limestone',.012)
        _rbox('chamfered_stone_post',(x,-.8,1.0),(.16,.16,.83),'cut_limestone',.018)
        _rsphere('stone_post_cap',(x,-.8,1.47),(.14,.14,.10),'cut_limestone',12,6)
    for z in (.85,1.26):
        if opening:
            for s in (-1,1):_rbox('stone_rail_open_access',(s*2.625,-.8,z),(2.55,.105,.11),'cut_limestone',.012)
        else:_rbox('stone_rail',(0,-.8,z),(7.80,.105,.11),'cut_limestone',.012)
    if opening:
        for j in range(3):_rbox('water_access_step',(0,-.93-j*.24,.36-j*.11),(2.05,.29,.16),'cut_limestone',.016)

def bridge():
    # Real open arch: wedge-shaped voussoirs, masonry spandrels and coping.
    n=36;half=6.55
    def zz(y):return .52+2.15*(1-(y/half)**2)
    vs=[];fs=[]
    for i in range(n):
        y0=-half+2*half*i/n+.014;y1=-half+2*half*(i+1)/n-.014
        start=len(vs)
        for x in (-1.12,1.12):
            for y,z in ((y0,zz(y0)),(y1,zz(y1)),(y1,zz(y1)-.49),(y0,zz(y0)-.49)):vs.append((x,y,z))
        fs += [tuple(start+k for k in q) for q in ((3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7))]
    mesh('arch_voussoir_blocks',vs,fs,'cut_limestone')
    for i in range(54):
        y=-half+(i+.5)*2*half/54;dy=2*half/54
        o=_rbox('bridge_paving_slab',(0,y,zz(y)+.035),(2.13,dy-.012,.11),'paving',.008)
        o.rotation_euler[0]=math.atan(-4.3*y/(half*half))
    for x in (-1.12,1.12):
        for j in range(15):
            y=-half+2*half*j/14;z=zz(y)
            _rbox('bridge_baluster_base',(x,y,z+.1),(.25,.25,.16),'cut_limestone',.018)
            _rrod('bridge_octagonal_baluster',(x,y,z+.12),(x,y,z+.98),.079,'cut_limestone',n=8)
            _rsphere('bridge_lotus_cap',(x,y,z+1.01),(.115,.115,.11),'cut_limestone',12,8)
        # Two continuous rails follow the deck without descending to the water.
        for h in (.47,.87):
            pts=[(x,-half+2*half*j/64,zz(-half+2*half*j/64)+h) for j in range(65)]
            bent('bridge_curved_handrail',pts,.055,'cut_limestone')
    for s in (-1,1):
        _rbox('abutment_foundation',(0,s*6.32,-.04),(2.65,.9,.78),'stone',.02)
        for k in range(3):_rbox('bridge_approach_step',(0,s*(6.73+.25*k),.38-.13*k),(2.55,.30,.16),'cut_limestone',.015)

def gate():
    for y in (-6.05,6.05):
        _rbox('gate_stone_plinth',(0,y,.39),(1.05,1.05,.68),'cut_limestone',.04)
        _rrod('gate_timber_column',(0,y,.66),(0,y,5.91),.18,'lacquer_red',n=16)
        _rrod('gate_base_collar',(0,y,.68),(0,y,.96),.235,'darkwood',n=16)
        bracket(0,y,5.4,pi/2)
        for s in (-1,1):_rrod('gate_knee_brace',(0,y+s*.13,4.95),(0,y+s*.85,5.67),.075,'darkwood',n=10)
    _rbox('gate_header',(0,0,5.85),(.28,12.9,.36),'wood',.015)
    before=begin();roof('finish_gate',0,0,6.01,6.65,.63,.34)
    bpy.context.view_layer.update()
    transform=Matrix.Rotation(pi/2,4,'Z')
    for o in set(bpy.data.objects)-before:o.matrix_world=transform@o.matrix_world
    for side in (-1,1):
        o=plaque_quad('finish_inscription',(0,0,0),(7.0,.93),'banner');o.rotation_euler[2]=side*pi/2;o.location=(side*.18,0,5.12)
    for y in (-4.3,4.3):
        _rrod('festival_lantern_cord',(-.1,y,5.62),(-.1,y,5.05),.012,'gold')
        hanging_lantern((-.1,y,4.72),.29)

def hanging_lantern(pos,r=.25):
    x,y,z=pos
    _rsphere('silk_lantern',pos,(r,r,r*1.26),'red',24,14)
    for i in range(12):
        a=2*pi*i/12;pts=[]
        for j in range(11):
            t=.15+(pi-.30)*j/10
            pts.append((x+(r+.006)*sin(t)*cos(a),y+(r+.006)*sin(t)*sin(a),z+r*1.26*cos(t)))
        bent('lantern_bamboo_rib',pts,.0045,'basket_fibre')
    for s in (-1,1):_rrod('lantern_cap',(x,y,z+s*r*1.17-.028),(x,y,z+s*r*1.17+.028),r*.48,'darkwood',n=16)
    for i in range(7):_rrod('silk_tassel',(x+(i-3)*.014,y,z-r*1.24),(x+(i-3)*.014,y,z-r*2.02),.005,'gold',n=6)

def lantern():
    _rbox('lamp_stone_socket',(0,0,.54),(.30,.30,.22),'cut_limestone',.025)
    _rrod('lamp_timber_pole',(0,0,.5),(0,0,3.14),.052,'darkwood',n=12)
    bent('lamp_hook',[(0,0,3.12),(0,.30,3.23),(0,.60,3.12),(0,.60,2.99)],.042,'darkwood')
    _rrod('hanging_cord',(0,.60,3.01),(0,.60,2.74),.012,'basket_fibre')
    hanging_lantern((0,.60,2.40),.25)

def mooring_dock():
    # Narrow pontoon projects into the water from an open bank access.
    for i in range(9):_rbox('dock_weathered_board',((i-4)*.22,0,.17),(.207,3.1,.11),'wood',.012)
    for y in (-1.2,1.2):
        _rbox('dock_cross_joist',(0,y,.01),(2.08,.17,.20),'darkwood',.01)
        for x in (-.85,.85):
            _rrod('dock_pile',(x,y,-.62),(x,y,.42),.09,'wood',n=12)
            _rrod('pile_cap',(x,y,.38),(x,y,.43),.103,'darkwood',n=12)
    for x in (-.73,.73):
        _rrod('mooring_bollard',(x,-1.04,.2),(x,-1.04,.64),.075,'darkwood',n=10)
        ring('bollard_rope',(x,-1.04,.42),.085,.014,'basket_fibre',20)
    for j in range(4):ring('coiled_mooring_rope',(.37,-.51,.24+j*.016),.19-j*.028,.012,'basket_fibre',28)

def bench():
    for y in (-.15,0,.15):_rbox('bench_seat_slat',(0,y,.58),(1.75,.13,.075),'wood',.012)
    for x in (-.63,.63):
        _rbox('bench_stone_support',(x,0,.27),(.24,.46,.55),'cut_limestone',.025)

def zongzi(x,y,z,s=.16):
    vs=[(x-s,y-s*.6,z),(x+s,y-s*.6,z),(x,y+s,z),(x,y,z+s*1.6)]
    mesh('leaf_wrapped_zongzi',vs,[(0,2,1),(0,1,3),(1,2,3),(2,0,3)],'zongzi_leaf')
    bent('zongzi_binding',[(x-s*.65,y-s*.2,z+.02),(x,y-s*.25,z+s*1.46),(x+s*.65,y-s*.2,z+.02),(x,y+s*.6,z+.02)],.005,'ivory')

def basket():
    # Open wicker vessel: annular weave, radial ribs and a solid woven base.
    _rrod('woven_basket_base',(0,0,.025),(0,0,.045),.34,'basket_fibre',n=32)
    for j in range(10):ring('basket_horizontal_weave',(0,0,.06+j*.022),.34+j*.011,.008,'basket_fibre',40)
    for i in range(24):
        a=2*pi*i/24
        _rrod('basket_vertical_weave',(.34*cos(a),.34*sin(a),.05),(.45*cos(a),.45*sin(a),.28),.008,'bamboo',n=6)
    ring('basket_bound_rim',(0,0,.29),.456,.018,'basket_fibre',40)
    for i in range(7):
        a=i*2.4;r=.20 if i else 0;zongzi(r*cos(a),r*sin(a),.12+(i%2)*.045,.135)

def tea_stall():
    for x in (-1.22,1.22):
        for y in (-.68,.68):
            _rrod('stall_timber_upright',(x,y,0),(x,y,2.49 if y>0 else 2.24),.047,'wood',n=10)
    for y,z in ((-.68,2.24),(.68,2.49)):_rrod('stall_roof_crossbar',(-1.4,y,z),(1.4,y,z),.055,'bamboo',n=10)
    vs=[];fs=[]
    for i in range(17):
        x=-1.5+3*i/16
        for j in range(13):
            y=-.98+1.96*j/12;zz=2.36+.18*y-.055*(1-(x/1.5)**2)+.014*sin(i*pi/2)
            vs.append((x,y,zz))
    for i in range(16):
        for j in range(12):a=i*13+j;fs.append((a,a+13,a+14,a+1))
    o=mesh('sagging_canvas_awning',vs,fs,'canvas');mod=o.modifiers.new('fabric_thickness','SOLIDIFY');mod.thickness=.008
    plaque_quad('stall_handwritten_sign',(0,-.985,2.01),(1.4,.31),'festival_sign')
    _rbox('stall_counter',(0,0,.89),(2.67,1.35,.10),'wood',.02)
    for x in (-1.1,1.1):
        for y in (-.49,.49):_rbox('table_leg',(x,y,.43),(.075,.075,.85),'darkwood',.008)
    for y in (-.49,.49):_rbox('table_stretcher',(0,y,.22),(2.28,.065,.065),'wood',.006)
    before=begin();basket()
    for o in set(bpy.data.objects)-before:o.location+=Vector((-.68,0,.95))
    # Stoneware teapot, lid, curved spout, handle and two cups.
    _rsphere('teapot_body',(.45,.10,1.09),(.20,.15,.145),'ceramic',20,12)
    _rrod('teapot_lid',(.45,.10,1.21),(.45,.10,1.23),.115,'ceramic',n=20)
    _rsphere('teapot_lid_knob',(.45,.10,1.25),(.035,.035,.028),'ceramic',12,8)
    bent('teapot_spout',[(.58,.10,1.08),(.71,.10,1.10),(.78,.10,1.22)],.045,'ceramic')
    o=ring('teapot_handle',(.25,.10,1.13),.11,.018,'ceramic',24);o.rotation_euler[0]=pi/2
    for x in (.27,.65):_rrod('tea_cup',(x,-.33,.95),(x,-.33,1.035),.061,'ceramic',r2=.074,n=20)

def bamboo_planter():
    _rbox('planter_stone_box',(0,0,.24),(.80,.65,.46),'cut_limestone',.025)
    _rbox('planter_soil',(0,0,.475),(.72,.57,.025),'darkwood',.005)
    for i in range(5):
        x=(i-2)*.11;y=.13*sin(i*3);h=1.15+.17*sin(i*2)
        _rrod('bamboo_culm',(x,y,.48),(x+.05,y,h),.018,'bamboo',n=8)
        for j in range(3):
            zz=.65+j*.21;ring('bamboo_node',(x,y,zz),.019,.004,'bamboo',12)
            for s in (-1,1):
                mesh('bamboo_lanceolate_leaf',[(x,y,zz),(x+s*.18,y-.045,zz+.11),(x+s*.37,y,zz+.08),(x+s*.15,y+.02,zz+.07)],[(0,1,2,3)],'reed_leaf')

def reed_patch():
    rng=random.Random(104)
    for i in range(16):
        x=rng.uniform(-.6,.6);y=rng.uniform(-.27,.27);h=rng.uniform(.36,.85)
        _rrod('reed_stalk',(x,y,0),(x+.07,y,h),.008,'bamboo',n=6)
        if i%3==0:_rrod('reed_seed_head',(x+.07,y,h*.8),(x+.07,y,h*1.1),.021,'basket_fibre',n=8)
        for s in (-1,1):
            mesh('curved_reed_blade',[(x,y,.05),(x+s*.11,y-.025,h*.62),(x+s*.32,y,h*.66),(x+s*.13,y+.025,h*.48)],[(0,1,2,3)],'reed_leaf')

def bank_ground():
    _rbox('bank_earth',(0,0,-.32),(48,7,.64),'grass',.10)
    _rbox('bank_flagstone_path',(0,-.25,.025),(47.9,1.75,.06),'paving',.015)

