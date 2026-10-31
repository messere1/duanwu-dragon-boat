"""Original Anhui-inspired town: stepped firewalls, courtyards and inhabited lanes.
An artistic river-town setting, not a measured reconstruction of Hongcun/Xidi.
"""
material('huizhou_white',(.52,.51,.46),'huizhou_plaster.png',rough=.94)
material('huizhou_masonry',(.22,.24,.21),'huizhou_stone.png',rough=.92)
material('huizhou_path',(.31,.32,.27),'huizhou_paving.png',rough=.9)
material('huizhou_earth',(.17,.19,.13),'huizhou_soil.png',rough=.97)
material('clay_ochre',(.24,.13,.075),rough=.83)
material('clay_dark',(.09,.10,.075),rough=.72)
material('laundry_blue',(.15,.20,.21),rough=.95)
material('laundry_linen',(.43,.41,.33),'canvas.png',rough=.96)
material('drain_water',(.035,.055,.039),rough=.27)
material('hill_near',(.14,.19,.14),rough=1)
material('hill_far',(.25,.32,.29),rough=1)
material('woodland_bark',(.09,.067,.044),rough=.98)
material('woodland_leaf_a',(.075,.14,.05),rough=.95)
material('woodland_leaf_b',(.115,.19,.08),rough=.96)
material('woodland_leaf_c',(.13,.17,.075),rough=.98)
material('huizhou_shop_label',(.2,.12,.07),'huizhou_shop_sign.png',rough=.85)
material('huizhou_inn_label',(.2,.12,.07),'huizhou_inn_sign.png',rough=.85)
_aged=M['wood'].copy();_aged.name='aged_timber';M['aged_timber']=_aged
for n in _aged.node_tree.nodes:
    if n.type=='MIX_RGB' and n.blend_type=='MULTIPLY':n.inputs[2].default_value=(.44,.39,.30,1)
_aged['obj_diffuse_tint']=[.44,.39,.30]
for key,file in [('cut_limestone','huizhou_stone.png'),('tile_grey','huizhou_tiles.png'),('grass','huizhou_soil.png'),('paving','huizhou_paving.png')]:
    if key not in M:continue
    m=M[key];bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.91
    for l in list(bs.inputs['Base Color'].links):m.node_tree.links.remove(l)
    n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(ROOT/'textures'/file),check_existing=True)
    m.node_tree.links.new(n.outputs['Color'],bs.inputs['Base Color']);m['obj_base_image']=n.image.name;m['obj_diffuse_tint']=[1,1,1]

def facade_uv(o,height=5.8,axis=0,zbase=0):
    uv=o.data.uv_layers.new(name='UVMap')
    for p in o.data.polygons:
        for li in p.loop_indices:
            co=o.data.vertices[o.data.loops[li].vertex_index].co+o.location
            uv.data[li].uv=(co[axis]/4+.5,(co.z-zbase)/height)
    return o

def wall(name,loc,size,h):return facade_uv(_rbox(name,loc,size,'huizhou_white',.012),h)

def horse_wall(x,hy,eave,rise):
    # One watertight stepped prism: no seams from stacked cubes.
    edge=hy+.10;levels=[eave+.35,eave+rise*.70+.24,eave+rise+.43,eave+rise*.70+.24,eave+.35]
    cuts=[-edge,-edge*.60,-edge*.23,edge*.23,edge*.60,edge]
    profile=[(-edge,.18),(edge,.18),(edge,levels[-1])]
    for i in range(4,-1,-1):
        profile.append((cuts[i],levels[i]))
        if i>0:profile.append((cuts[i],levels[i-1]))
    vs=[(xx,y,z) for xx in (x-.10,x+.10) for y,z in profile];k=len(profile)
    fs=[tuple(reversed(range(k))),tuple(range(k,2*k))]+[(i,(i+1)%k,(i+1)%k+k,i+k) for i in range(k)]
    o=mesh('stepped_firewall',vs,fs,'huizhou_white');facade_uv(o,eave+rise+.43,1)
    for i,z in enumerate(levels):
        y=(cuts[i]+cuts[i+1])/2;length=cuts[i+1]-cuts[i]
        _rbox('firewall_dark_coping',(x,y,z+.045),(.31,length+.055,.095),'tile_grey',.012)
        _rbox('firewall_brick_dentil',(x,y,z-.05),(.23,length,.07),'huizhou_masonry',.006)
    # A few exposed grey bricks at the damp foot of each firewall.
    for j in range(2):
        for i in range(7):_rbox('firewall_exposed_base_brick',(x,(-3+i)*.50,.22+j*.13),(.225,.48,.115),'huizhou_masonry',.006)

def hui_window(x,y,z,w=.68,h=.95):
    _rbox('deep_window_shadow',(x,y+.055,z),(w,.10,h),'window_shadow',.003)
    for dx in (-w/2,w/2):_rbox('aged_window_frame',(x+dx,y,z),(.06,.10,h+.12),'aged_timber',.006)
    for dz in (-h/2,h/2):_rbox('aged_window_sill',(x,y-.015,z+dz),(w+.14,.16,.065),'aged_timber',.008)
    for i in range(4):_rbox('fine_window_mullion',(x+(i-1.5)*w*.23,y-.015,z),(.023,.035,h-.04),'aged_timber',.003)
    for dz in (-h*.30,.08,h*.31):_rbox('fine_window_crosspiece',(x,y-.02,z+dz),(w-.03,.035,.023),'aged_timber',.003)

def hui_house(kind=0):
    tall=kind in (1,2);hx=2.15;hy=2.02;eave=5.15 if tall else 3.05;rise=.95
    _rbox('old_house_foundation',(0,0,.13),(4.52,4.25,.26),'huizhou_masonry',.025)
    # Front wall has an actual entrance opening, with a dark recess behind it.
    wall('front_wall_left',(-1.38,-hy+.10,eave/2+.15),(1.52,.20,eave-.04),eave+rise)
    wall('front_wall_right',(1.38,-hy+.10,eave/2+.15),(1.52,.20,eave-.04),eave+rise)
    wall('over_door_wall',(0,-hy+.10,(eave+2.16)/2),(1.25,.20,eave-2.16),eave+rise)
    wall('rear_courtyard_wall',(0,hy-.10,eave/2+.15),(4.30,.20,eave-.04),eave+rise)
    for s in (-1,1):wall('side_house_wall',(s*(hx-.10),0,eave/2+.15),(.20,4.04,eave-.04),eave+rise)
    _rbox('entrance_recess',(0,-hy+.23,1.15),(1.22,.08,2.05),'window_shadow',.003)
    for s in (-1,1):
        _rbox('weathered_double_door',(s*.265,-hy+.16,1.10),(.52,.075,1.98),'aged_timber',.009)
        for dz in (.57,1.12,1.72):_rbox('door_inset_panel',(s*.265,-hy+.11,dz),(.39,.025,.40),'darkwood',.006)
        _rbox('carved_stone_door_surround',(s*.64,-hy-.01,1.19),(.12,.27,2.18),'huizhou_masonry',.01)
        ring('old_door_iron_pull',(s*.10,-hy+.07,1.10),.041,.008,'aged_iron',16).rotation_euler[0]=pi/2
    _rbox('stone_entrance_lintel',(0,-hy-.015,2.31),(1.48,.33,.20),'huizhou_masonry',.012)
    _rbox('door_drip_cap',(0,-hy-.07,2.46),(1.65,.43,.07),'tile_grey',.012)
    for j in range(2):_rbox('worn_doorstep',(0,-hy-.17-j*.22,.14-j*.075),(1.45,.29,.15),'huizhou_masonry',.018)
    for x in (-1.40,1.40):hui_window(x,-hy-.025,1.68,.62,.83)
    if tall:
        for x in (-1.20,0,1.20):hui_window(x,-hy-.025,3.94,.65,1.05)
        _rbox('exposed_upper_floor_beam',(0,-hy-.025,2.78),(4.27,.09,.15),'aged_timber',.008)
        for y in (-.8,.85):
            _rbox('side_upper_shutter',(hx+.025,y,3.98),(.055,.58,.85),'aged_timber',.008)
    # Roof is enclosed between the stepped firewalls.
    roof('hui_small_tiles',0,0,eave,2.12,2.10,rise)
    for s in (-1,1):horse_wall(s*2.20,hy,eave,rise)
    if kind==2:
        plaque_quad('old_tea_shop_sign',(0,-hy-.055,3.02),(2.18,.48),'huizhou_shop_label')
        for x in (-1.62,1.62):_rrod('awning_timber_brace',(x,-hy-.05,2.05),(x,-hy-.70,2.38),.032,'aged_timber',n=8)
        vs=[];fs=[]
        for i in range(13):
            x=-1.85+3.70*i/12
            for j in range(7):
                t=j/6;vs.append((x,-hy-.08-.8*t,2.61-.28*t-.045*sin(pi*i/12)))
        for i in range(12):
            for j in range(6):a=i*7+j;fs.append((a,a+7,a+8,a+1))
        mesh('faded_shop_canvas',vs,fs,'laundry_linen')

def courtyard_house():
    # Four low wings around a real open-to-sky courtyard (not a painted roof hole).
    for y in (-2.25,2.25):
        wall('courtyard_front_rear_wing',(0,y,1.62),(4.65,1.45,3.12),4.2)
        roof('courtyard_wing',0,y,3.18,2.29,.86,.59)
    for s in (-1,1):
        wall('courtyard_side_wing',(s*1.90,0,1.62),(.85,3.12,3.12),4.2)
        before=begin();roof('courtyard_side_tiles',0,0,3.18,1.65,.56,.59);bpy.context.view_layer.update()
        xf=Matrix.Translation((s*1.90,0,0))@Matrix.Rotation(pi/2,4,'Z')
        for o in set(bpy.data.objects)-before:o.matrix_world=xf@o.matrix_world
        horse_wall(s*2.38,2.90,3.05,.93)
    _rbox('courtyard_flagstone_floor',(0,0,.10),(2.98,2.95,.08),'huizhou_path',.01)
    _rbox('courtyard_shadow_door',(0,-3.003,1.05),(1.05,.08,1.95),'aged_timber',.008)
    plaque_quad('courtyard_inn_sign',(0,-3.055,2.38),(1.78,.39),'huizhou_inn_label')
    for x in (-1.65,1.65):hui_window(x,-3.005,1.67,.58,.78)

def old_quay(variant=0):
    _rbox('old_quay_core',(0,0,-.015),(8,2,.76),'stone',.012)
    _rbox('uneven_quay_path',(0,.04,.405),(8,1.94,.08),'huizhou_path',.01)
    rng=random.Random(912)
    for j in range(3):
        for i in range(11):
            x=-3.73+i*.73+(.365 if j%2 else 0)
            if x>3.85:continue
            o=_rbox('dark_quay_ashlar',(x,-.989,-.28+j*.235),(.715,.11,.22),'huizhou_masonry',.014)
            facade_uv(o,.9,zbase=-.42)
    for i in range(13):
        x=-3.70+i*.615;z=.466+rng.uniform(-.012,.012)
        _rbox('worn_coping_flagstone',(x,-.86,z),(.596,.32,.135),'huizhou_masonry',.017)
    # Sparse, low parapets instead of an uninterrupted line of ornamental balusters.
    for x,w in (((-2.95,1.2),(2.70,.90)) if variant else ((-2.85,1.42),(2.95,1.20))):_rbox('short_low_quay_parapet',(x,-.79,.66),(w,.23,.36),'huizhou_masonry',.025)
    for y,z in ((1.04,.28),(1.27,.13)):_rbox('landward_worn_step',(0,y,z),(8,.27,.15),'huizhou_masonry',.018)
    for j in range(6):
        top=.46-j*.105;bottom=-.45
        _rbox('riverside_washing_step',(.65 if variant else 0,-.91-j*.26,(top+bottom)/2),(1.35,.31,top-bottom),'huizhou_masonry',.018)
    for x in (-3.40,3.37):
        ring('quay_mooring_iron_ring',(x,-1.065,.27),.09,.015,'aged_iron',20).rotation_euler[0]=pi/2

def bank_ground():
    _rbox('town_earth',(0,3.5,-.32),(180,14,.64),'huizhou_earth',.025)
    # Gap in the path is occupied by the open drainage channel.
    _rbox('old_street_outer_paving',(0,-1.18,.025),(48,.42,.06),'huizhou_path',.008)
    _rbox('old_street_inner_paving',(0,.83,.025),(48,3.30,.06),'huizhou_path',.008)

def street_gutter():
    _rbox('gutter_dark_bed',(0,0,.018),(48,.17,.025),'darkwood',.004)
    _rbox('gutter_shallow_water',(0,0,.036),(48,.125,.015),'drain_water',.001)
    for side in (-1,1):_rbox('gutter_stone_lip',(0,side*.113,.065),(48,.065,.09),'huizhou_masonry',.008)
    for x in (-21,-16.6,-11.9,-7.3,-1.4,4.1,8.8,13.4,18,22):_rbox('gutter_door_crossing',(x,0,.09),(.72,.34,.065),'huizhou_masonry',.01)

def clay_jar(x,y,z,scale=1,mat='clay_ochre'):
    profiles=[(.13,0),(.21,.05),(.28,.23),(.25,.43),(.16,.51),(.16,.55)]
    vs=[];fs=[];n=24
    for r,h in profiles:
        for i in range(n):a=2*pi*i/n;vs.append((x+r*scale*cos(a),y+r*scale*sin(a),z+h*scale))
    for j in range(len(profiles)-1):
        for i in range(n):a=j*n+i;b=j*n+(i+1)%n;fs.append((a,b,b+n,a+n))
    fs.append(tuple(reversed(range(n))));o=mesh('household_clay_jar',vs,fs,mat)
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    ring('jar_mouth_lip',(x,y,z+.55*scale),.16*scale,.015*scale,mat,24)
    _rrod('jar_dark_interior',(x,y,z+.47*scale),(x,y,z+.48*scale),.14*scale,'darkwood',n=24)

def household_props():
    clay_jar(-.38,0,0,1.10);clay_jar(.14,.18,0,.75,'clay_dark')
    for j in range(3):
        for i in range(4-j):
            x=.52+i*.13+j*.065;z=.067+j*.115
            _rrod('stacked_firewood',(x,-.30,z),(x,.17,z),.059,'aged_timber',n=8)
    clay_jar(.70,.28,0,.55,'clay_dark')
    rng=random.Random(42)
    for i in range(13):
        a=i*2.4;r=.20+rng.random()*.18;x=.70;y=.28;z=.30
        mesh('doorstep_pot_fern',[(x,y,z),(x+r*.45*cos(a)-.035,y+r*.45*sin(a),z+.15),(x+r*cos(a),y+r*sin(a),z+.12),(x+r*.45*cos(a)+.035,y+r*.45*sin(a),z+.11)],[(0,1,2,3)],'reed_leaf')

def laundry_rack():
    for x in (-1.15,1.15):_rrod('laundry_bamboo_upright',(x,0,0),(x,0,1.85),.031,'bamboo',n=8)
    _rrod('laundry_line',(-1.16,0,1.80),(1.16,0,1.80),.006,'basket_fibre',n=6)
    for i in range(3):
        cx=-.73+i*.70;vs=[];fs=[]
        for a in range(7):
            for b in range(9):
                u=a/6;v=b/8;vs.append((cx+(u-.5)*.53,.035*sin(u*3*pi)*v,1.79-v*(.78+.08*i)))
        for a in range(6):
            for b in range(8):p=a*9+b;fs.append((p,p+9,p+10,p+1))
        mesh('hanging_household_linen',vs,fs,'laundry_blue' if i==1 else 'laundry_linen')

def hill_height(x,y):
    t=max(0,min(1,(y-19.5)/65))
    return -.15+max(0,(8.5+4*sin(x*.092+1)+2*cos(x*.19-y*.052))*(sin(pi*min(1,t*1.3))**1.25))

def distant_hills():
    nx,ny=100,35;vs=[];fs=[]
    for i in range(nx+1):
        x=-90+180*i/nx
        for j in range(ny+1):
            y=19.5+65*j/ny;vs.append((x,y,hill_height(x,y)))
    for i in range(nx):
        for j in range(ny):a=i*(ny+1)+j;fs.append((a,a+ny+1,a+ny+2,a+1))
    o=mesh('rolling_town_backdrop_hills',vs,fs,'hill_far')
    for p in o.data.polygons:p.use_smooth=True

def distant_tree():
    # Explicit leaf geometry keeps the crown intact at distance; decimating an
    # alpha-card tree would erase most of its foliage and leave ghost branches.
    rng=random.Random(219);vs=[];fs=[];slots=[]
    bent('woodland_broadleaf_trunk',[(0,0,0),(.04,.02,1.1),(-.03,.04,2.05),(.07,0,2.8)],.13,'woodland_bark')
    for branch in range(7):
        a=2*pi*branch/7;end=Vector((.82*cos(a),.82*sin(a),2.75+.40*sin(a*2)))
        bent('woodland_crown_branch',[(0,0,1.35),(.32*cos(a),.32*sin(a),2.08),end],.05,'woodland_bark')
        for j in range(200):
            while True:
                q=Vector((rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1)))
                if q.length_squared<1:break
            center=end+Vector((q.x*.76,q.y*.76,q.z*.82))
            yaw=rng.random()*2*pi;tilt=rng.uniform(.25,2.7)
            u=Vector((cos(yaw),sin(yaw),0));v=Vector((-sin(yaw)*cos(tilt),cos(yaw)*cos(tilt),sin(tilt)));normal=u.cross(v)
            length=rng.uniform(.16,.29);width=length*rng.uniform(.40,.65);start=len(vs)
            for xx,yy in ((0,-.50),(.40,-.29),(.50,.12),(0,.55),(-.50,.12),(-.40,-.29)):
                vs.append(center+u*(xx*width)+v*(yy*length))
            vs.append(center+normal*.009)
            mat=rng.randrange(3)
            for k in range(6):fs.append((start+6,start+k,start+(k+1)%6));slots.append(mat)
    o=mesh('woodland_individual_leaf_crown',vs,fs,'woodland_leaf_a')
    o.data.materials.append(M['woodland_leaf_b']);o.data.materials.append(M['woodland_leaf_c'])
    for p,slot in zip(o.data.polygons,slots):p.material_index=slot

def water():
    nx,ny=240,40;vs=[];fs=[]
    for i in range(nx+1):
        for j in range(ny+1):
            x=-90+180*i/nx;y=-5.7+11.4*j/ny;vs.append((x,y,-.06+.012*sin(x*1.2+y*2)+.005*sin(x*3-y)))
    for i in range(nx):
        for j in range(ny):a=i*(ny+1)+j;fs.append((a,a+ny+1,a+ny+2,a+1))
    mesh('extended_river_surface',vs,fs,'water')

# Replace only environment model factories.
house=lambda:hui_house(0)
_riverside_quay=quay
def quay(opening=False):return _riverside_quay(True) if opening else old_quay()

def install_huizhou_assets():
    root_asset('huizhou_tall_house',lambda:hui_house(1));root_asset('huizhou_tea_house',lambda:hui_house(2))
    root_asset('huizhou_courtyard',courtyard_house);root_asset('household_props',household_props)
    root_asset('laundry_rack',laundry_rack);root_asset('street_gutter',street_gutter);root_asset('distant_hills',distant_hills)
    root_asset('distant_tree',distant_tree);root_asset('quay_weathered_b',lambda:old_quay(1))

def layout_huizhou():
    place('river_surface','river')
    place('bank_ground','north_bank',(0,9.2,0));place('bank_ground','south_bank',(0,-9.2,0),pi)
    for y in (-6.7,6.7):
        for i,x in enumerate((-20,-12,-4,4,12,20)):
            access=(y<0 and x==-12) or x==20
            place('quay_access' if access else ('quay_weathered_b' if i%2 else 'quay_segment'),f'quay_{y}_{i}',(x,y,0),pi if y<0 else 0)
    place('finish_gate','finish',(14,0,0));place('arch_bridge','bridge',(20,0,0))
    place('pavilion','riverside_pavilion',(-1.4,10.55,0))
    front=[(-21.2,10.5,'riverside_house'),(-16.6,10.8,'huizhou_tall_house'),(-11.9,10.5,'huizhou_tea_house'),(-7.3,10.7,'riverside_house'),(4.1,10.65,'huizhou_tea_house'),(8.8,10.8,'huizhou_tall_house'),(13.4,10.5,'riverside_house'),(18,11.0,'huizhou_tall_house'),(22.5,10.7,'riverside_house')]
    for i,(x,y,proto) in enumerate(front):
        r=place(proto,f'north_street_house_{i}',(x,y,0));r.scale.z=(.97,1.035,1.0,1.02)[i%4]
    for i,x in enumerate((-19.6,-14.4,-9.2,-4.0,1.5,6.7,11.9,17.1,22.3)):
        proto='huizhou_courtyard' if i in (1,4,7) else ('huizhou_tall_house' if i%2 else 'riverside_house')
        place(proto,f'north_back_lane_house_{i}',(x,16.05+(i%2)*.2,0),.015*sin(i*2))
    for i,x in enumerate((-21,-16.2,-4.9,.1,10.1,15.1,20.1)):
        proto='huizhou_tall_house' if i in (1,5) else 'riverside_house'
        place(proto,f'south_street_house_{i}',(x,-11.9-(i%2)*.13,0),pi)
    for i,x in enumerate((-20,-14.6,-8.7,-3.1,2.7,8.5,14.3,20.2)):
        place('huizhou_courtyard' if i%3==0 else 'riverside_house',f'south_back_lane_house_{i}',(x,-17.0,0),pi+.012*sin(i))
    place('street_gutter','north_street_watercourse',(0,8.30,0))
    place('street_gutter','south_street_watercourse',(0,-8.30,0),pi)
    place('distant_hills','north_distant_landscape')
    place('distant_hills','south_distant_landscape',(0,0,0),pi)
    place('mooring_dock','south_mooring_dock',(-12,-5.1,0))
    place('tea_stall','festival_tea_stall',(-10,-9.1,.04),pi)
    for i,(x,y,rot) in enumerate([(-20,8.4,0),(-15,8.7,.2),(-10.5,8.2,0),(-6.0,8.6,0),(5.7,8.5,.1),(10.1,8.6,0),(17.0,8.9,0),(-18,-9.6,pi),(-3.3,-9.7,pi),(12,-9.6,pi),(20,-9.5,pi)]):
        place('household_props',f'doorstep_household_{i}',(x,y,.055),rot)
    for i,x in enumerate((-17,-5,7,19)):
        place('laundry_rack',f'north_lane_laundry_{i}',(x,13.6,.03),.08*sin(i))
    for i,(x,y) in enumerate([(-19,-8.7),(-2,-8.5),(8,-8.6),(17,-8.8)]):place('riverside_bench',f'old_street_bench_{i}',(x,y,.055),pi)
    for i,(x,y) in enumerate([(-22,13.7),(-3.9,13.8),(20.5,14.0),(-19,-14.5),(5.6,-14.2),(22,-14.6),(-27,9),(28,11)]):
        r=place('tree',f'lane_tree_{i}',(x,y,-.05),i*1.6);s=.92+(i%3)*.12;r.scale=(s,s,s)
    for i in range(20):
        x=-37+i*3.9;y=22.0+3.1*(.5+.5*sin(i*2.1))
        r=place('distant_tree',f'woodland_back_{i}',(x,y,hill_height(x,y)),i*1.7);s=1.05+(i%4)*.17;r.scale=(s,s,s)
    for i in range(12):
        side=-1 if i<6 else 1;x=side*(29+(i%6)*5.8);y=10.5+(i%3)*3.2
        r=place('distant_tree',f'village_edge_tree_{i}',(x,y,-.03),i*2.1);s=1.1+(i%3)*.2;r.scale=(s,s,s)
    for i,x in enumerate((-21,-16,-7,2,9,16)):
        for s in (-1,1):place('reed_patch',f'reeds_{i}_{s}',(x,s*5.77,-.08),i*.7)
    for i,x in enumerate((-22,-16,-7,3,9,17,23)):
        place('lantern_post',f'north_old_lane_lamp_{i}',(x,7.75,0),pi)
    for i,x in enumerate((-20,-8,4,15,23)):place('lantern_post',f'south_old_lane_lamp_{i}',(x,-7.8,0))
    for i,x in enumerate((-20,-14,-8,-2,4,10,16)):place('course_buoy',f'buoy_{i}',(x,0,0))
    for i in range(8):place('rock',f'bank_rock_{i}',(-20+i*5.5,-6.0,-.12))
