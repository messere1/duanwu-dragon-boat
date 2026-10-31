"""Integrated racing-boat design: flared bow, painted carving and visible timber framing."""
import bmesh
for team,color in [('red',(.24,.025,.012)),('jade',(.018,.13,.088))]:
    material('carved_'+team,color,rough=.54)
    m=material('painted_'+team,color,'boat_painted_'+team+'.png',rough=.63)
material('edge_gold',(.48,.29,.075),metal=.38,rough=.5)
material('cream_paint',(.64,.55,.34),rough=.57)
def bow_lift(x):
    t=max(0,min(1,(x-3.35)/1.8));return .10*(abs(x)/5.1)**4+.53*t*t*(3-2*t)
def breadth(x):
    t=max(0,min(1,(x+4.95)/10.05));return .88*(.10+.90*sin(pi*t)**.51)
def hull_point(x,t,inside=False):
    w=breadth(x)-(.052 if inside else 0)
    return (x,w*sin(t),.82+bow_lift(x)-(.59-(.063 if inside else 0))*cos(t))
def ribbon(name,side,t0,t1,mat):
    vs=[];fs=[];nx=80;ny=8
    for i in range(nx+1):
        x=-4.95+10.05*i/nx
        for j in range(ny+1):
            t=t0+(t1-t0)*j/ny
            p=list(hull_point(x,side*t));p[1]+=side*.012;vs.append(p)
    for i in range(nx):
        for j in range(ny):a=i*(ny+1)+j;fs.append((a,a+ny+1,a+ny+2,a+1))
    o=mesh(name,vs,fs,mat);uv=o.data.uv_layers.new(name='UVMap')
    for p in o.data.polygons:
        p.use_smooth=True
        for li in p.loop_indices:
            vi=o.data.loops[li].vertex_index;uv.data[li].uv=(vi//(ny+1)/nx,(vi%(ny+1))/ny)
    return o
def hull(team):
    nx=80;nt=24;v=[];f=[]
    for inside in (False,True):
        for i in range(nx+1):
            x=-4.95+10.05*i/nx
            for j in range(nt+1):v.append(hull_point(x,-pi/2+pi*j/nt,inside))
    k=(nx+1)*(nt+1)
    for layer in range(2):
        for i in range(nx):
            for j in range(nt):
                a=layer*k+i*(nt+1)+j;q=(a,a+nt+1,a+nt+2,a+1)
                f.append(q if layer==0 else q[::-1])
    for i in range(nx):
        for j in (0,nt):a=i*(nt+1)+j;b=a+nt+1;f.append((a,b,b+k,a+k))
    for i in (0,nx):
        for j in range(nt):a=i*(nt+1)+j;f.append((a,a+1,a+1+k,a+k))
    o=mesh('continuous_upturned_bow_shell',v,f,'wood')
    for p in o.data.polygons:p.use_smooth=True
    # Upper painted strake follows the actual hull curvature, including the rising bow.
    for side in (-1,1):
        ribbon('painted_dragon_scale_strake',side,.91,pi/2,'painted_'+team)
        for t,r,mat in [(pi/2,.047,'darkwood'),(1.49,.014,'edge_gold'),(.91,.021,'edge_gold'),(.76,.022,'carved_'+team),(.48,.019,'darkwood')]:
            pts=[]
            for i in range(nx+1):
                x=-4.95+10.05*i/nx;p=list(hull_point(x,side*t));p[1]+=side*.016;pts.append(p)
            bent('layered_sheer_strake',pts,r,mat)
        # Long timber seams and fastening heads make construction readable close up.
        for t in (.24,.49,.74):
            pts=[hull_point(-4.90+9.96*i/80,side*t) for i in range(81)]
            bent('plank_caulking',pts,.0055,'darkwood')
        for x in (-3.5,-2.4,-1.3,-.2,.9,2.,3.1,4.1):
            p=Vector(hull_point(x,side*1.36));p.y+=side*.025
            sphere('bronze_plank_fastener',p,(.016,.009,.016),'edge_gold',10,6)
    # Keel, bottom boards, internal ribs and inboard stringers.
    bent('keel',[(x,0,.245+bow_lift(x)) for x in [-4.8+i*9.7/64 for i in range(65)]],.055,'darkwood')
    for j in range(7):
        y=(j-3)*.14;start=-4.35;end=3.3
        def floor_clearance(x):
            c=(.82+bow_lift(x)-.45)/(.59-.063)
            return max(0,breadth(x)-.052)*math.sqrt(max(0,1-c*c))
        while floor_clearance(start)<abs(y)+.069:start+=.02
        while floor_clearance(end)<abs(y)+.069:end-=.02
        box('fitted_bottom_floorboard',((start+end)/2,y,.45),(end-start,.132,.048),'wood',.006)
    for i in range(14):
        x=-4.15+i*.62;pts=[hull_point(x,-1.48+2.96*j/20,True) for j in range(21)]
        bent('steam_bent_frame_rib',pts,.029,'darkwood')
    for side in (-1,1):
        bent('inboard_seat_stringer',[(x,side*(breadth(x)-.09),.67+bow_lift(x)) for x in [-4.4+i*8.8/64 for i in range(65)]],.032,'wood')
    for x in (-3,-1.9,-.8,.3,1.4,2.5):
        box('cross_thwart_seat',(x,0,.76),(.27,1.40,.08),'wood',.013)
        box('rowing_foot_stretcher',(x+.43,0,.55),(.40,1.23,.10),'wood',.013)
        for side in (-1,1):
            box('seat_knee_bracket',(x,side*.59,.64),(.13,.13,.22),'darkwood',.018)
            for dx in (-.075,.075):sphere('seat_dowel',(x+dx,side*.56,.805),(.011,.011,.006),'edge_gold',8,4)
    # Broad drum platform, with fitted planks and a raised carved perimeter.
    for j in range(7):
        y=(j-3)*.146
        end=4.67
        def deck_clearance(x):
            c=(.82+bow_lift(x)-(.88-.0375))/.59
            return breadth(x)*math.sqrt(max(0,1-c*c)) if c<1 else 0
        while deck_clearance(end)<abs(y)+.084:end-=.015
        start=2.93
        box('fitted_foredeck_plank',((start+end)/2,y,.88),(end-start,.138,.075),'wood',.008)
    for side in (-1,1):
        bent('drum_platform_rail',[(2.92,side*.58,.93),(3.8,side*.56,.95),(4.52,side*.37,1.09)],.035,'carved_'+team)
        bent('platform_inlay',[(2.92,side*.60,.95),(3.8,side*.58,.97),(4.52,side*.39,1.11)],.009,'edge_gold')
    for j in range(5):box('stern_platform_plank',(-4.12,(j-2)*.13,.86),(.88,.122,.08),'wood',.008)
    # The stem rises into a carved neck seat, rather than ending below an unrelated head.
    loft('bow_stem_fairing',[(4.48,0,.92,.28,.20),(4.77,0,1.12,.25,.29),(5.00,0,1.35,.22,.31),(5.18,0,1.53,.27,.29)],'carved_'+team)
    for side in (-1,1):
        bent('stem_gold_scroll',[(4.25,side*.30,.89),(4.65,side*.28,1.03),(4.89,side*.26,1.31),(5.13,side*.28,1.49)],.015,'edge_gold')

_head_materials={}
def carved_material(src,team):
    key=(src.name,team)
    if key in _head_materials:return _head_materials[key]
    m=src.copy();m.name='boat_sculpt_'+team+'_'+src.name;M[m.name]=m
    bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if bs:
        bs.inputs['Metallic'].default_value=0
        for l in list(bs.inputs['Metallic'].links):m.node_tree.links.remove(l)
        for l in list(bs.inputs['Roughness'].links):m.node_tree.links.remove(l)
        bs.inputs['Roughness'].default_value=.56
        if 'Parts' not in src.name:
            pigment=(.24,.025,.012,1) if team=='red' else (.018,.13,.088,1)
            image=next((n for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and n.image.colorspace_settings.name=='sRGB'),None)
            for l in list(bs.inputs['Base Color'].links):m.node_tree.links.remove(l)
            bs.inputs['Base Color'].default_value=pigment
            # Keep the sculpted normal map, but replace the grey creature skin with paint.
            m['obj_base_image']='';m['obj_solid_color']=list(pigment[:3]);m.diffuse_color=pigment
            if image:image.mute=True
    _head_materials[key]=m;return m
def dragon_head(team):
    # Adapt CalWhite's sculpt: remove the long bust and towering spikes, widen the face.
    for src in _open_objects:
        if not src.name.startswith('open_head__'):continue
        o=src.copy();o.data=src.data.copy();bpy.context.collection.objects.link(o);o.matrix_world=Matrix.Identity(4)
        bm=bmesh.new();bm.from_mesh(o.data)
        for co,no,inner,outer in [((5.60,0,0),(1,0,0),True,False),((0,0,1.94),(0,0,1),False,True),((0,0,1.07),(0,0,1),True,False)]:
            result=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=co,plane_no=no,clear_inner=inner,clear_outer=outer)
            boundary=[e for e in result['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_boundary]
            if boundary:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
        for v in bm.verts:
            p=v.co.copy();v.co=(5.0+(p.x-5.60)*.94,p.y*1.32,1.48+(p.z-1.30)*1.06)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
        old=list(o.data.materials);o.data.materials.clear()
        for m in old:o.data.materials.append(carved_material(m,team))
        o.name='compact_painted_dragon_face_'+team
    # Short carved antlers and layered flame-like ears share the boat's aged gold.
    for side in (-1,1):
        bent('carved_antler',[(5.35,side*.27,2.08),(5.20,side*.29,2.27),(5.15,side*.34,2.47),(5.25,side*.37,2.57)],.055,'cream_paint')
        bent('antler_branch',[(5.20,side*.29,2.28),(5.03,side*.35,2.38)],.032,'cream_paint')
        bent('painted_brow',[(5.57,side*.31,2.05),(5.69,side*.38,2.10),(5.91,side*.32,2.02)],.033,'cream_paint')
        for i in range(3):
            pts=[(5.35+i*.05,side*.28,1.78+i*.055),(5.14+i*.06,side*.39,1.88+i*.07),(4.99+i*.07,side*.43,2.08+i*.07),(5.24+i*.06,side*.43,2.00+i*.07),(5.48+i*.05,side*.30,1.87+i*.055)]
            o=mesh('flame_shaped_ear_carving',pts,[(0,1,2),(0,2,3),(0,3,4)],'carved_'+team)
            mod=o.modifiers.new('carved_ear_thickness','SOLIDIFY');mod.thickness=.018
            bent('ear_gold_inlay',pts[1:4],.009,'edge_gold')
    # Shared paint and overlapping solid volumes close the neck-to-stem transition.
    loft('carved_neck_transition',[(4.82,0,1.21,.23,.25),(5.02,0,1.45,.31,.34),(5.24,0,1.65,.34,.32)],'carved_'+team)
    for side in (-1,1):
        for j in range(4):
            x=4.95+j*.09
            bent('neck_carving_inlay',[(x,side*.25,1.27+j*.09),(x+.11,side*.32,1.37+j*.09),(x+.22,side*.27,1.39+j*.09)],.009,'edge_gold')

def dragon_tail(team):
    loft('upturned_carved_stern',[(-4.40,0,.82,.10,.04),(-4.68,0,.90,.17,.15),(-4.96,0,1.02,.16,.20),(-5.23,0,1.27,.11,.24),(-5.42,0,1.52,.05,.19)],'carved_'+team)
    for side in (-1,1):
        for i in range(3):
            bent('tail_flame_carving',[(-5.00,side*.08,1.03+i*.07),(-5.28,side*(.10+i*.045),1.26+i*.12),(-5.53,side*(.12+i*.07),1.48+i*.17),(-5.62,side*(.12+i*.07),1.68+i*.17)],.024,'edge_gold')
