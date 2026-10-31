"""Continuous 360-degree land, river, village extensions, fields and sky."""
material('panorama_ground',(.20,.23,.15),'huizhou_soil.png',rough=1)
material('field_green',(.17,.25,.09),rough=1)
material('field_olive',(.25,.29,.12),rough=1)
material('field_earth',(.23,.20,.12),rough=1)
material('field_ridge',(.13,.16,.075),rough=1)
material('panorama_sky', (1,1,1),'panorama_sky.png',rough=1)
_sky=M['panorama_sky'];_sky['render_mode']='sky_unlit';_sky.node_tree.nodes.clear()
_im=bpy.data.images.load(str(ROOT/'textures/panorama_sky.png'),check_existing=True)
_tx=_sky.node_tree.nodes.new('ShaderNodeTexImage');_tx.image=_im
_em=_sky.node_tree.nodes.new('ShaderNodeEmission');_em.inputs['Strength'].default_value=.8
_out=_sky.node_tree.nodes.new('ShaderNodeOutputMaterial');_sky.node_tree.links.new(_tx.outputs['Color'],_em.inputs['Color']);_sky.node_tree.links.new(_em.outputs[0],_out.inputs['Surface'])
_sky['obj_base_image']=_im.name
# The former mist-colored backdrop is now a near, cultivated slope.
_slope=M['hill_far'];_bs=_slope.node_tree.nodes.get('Principled BSDF')
for _link in list(_bs.inputs['Base Color'].links):_slope.node_tree.links.remove(_link)
_soil=_slope.node_tree.nodes.new('ShaderNodeTexImage');_soil.image=bpy.data.images.load(str(ROOT/'textures/huizhou_soil.png'),check_existing=True)
_slope.node_tree.links.new(_soil.outputs['Color'],_bs.inputs['Base Color']);_slope['obj_base_image']=_soil.image.name;_slope['obj_diffuse_tint']=[1,1,1]

def river_center(x):
    t=max(0,min(1,(abs(x)-85)/90));t=t*t*(3-2*t)
    return (1 if x>=0 else -1)*22*sin((abs(x)-85)/90+.3)*t

def surrounding_ground_height(x,y):
    r=math.hypot(x,y);a=math.atan2(y,x);t=max(0,min(1,(r-90)/65));t=t*t*(3-2*t)
    valley=max(0,min(1,(abs(y-river_center(x))-5.7)/32));valley=valley*valley*(3-2*valley)
    height=14+7*sin(3*a+.7)+5*cos(5*a-.4)+3*sin(9*a+1)
    outer=18*math.exp(-((r-225)/72)**2)*(1+.28*sin(7*a))
    horizon=(42+8*sin(5*a+.4)+6*cos(7*a))*math.exp(-((r-355)/43)**2)
    return -.08+t*valley*(max(7,height)+outer)+horizon

def panorama_surface(x,y):
    z=surrounding_ground_height(x,y)
    if abs(x)<90 and 5.7<=abs(y)<=19.7:z=max(z,0)
    if abs(x)<=90 and 19.5<=abs(y)<=84.5:z=max(z,hill_height(x,abs(y)))
    return z

def panorama_terrain():
    nx,ny=200,100
    for side in (-1,1):
        vs=[];fs=[]
        for i in range(nx+1):
            x=-420+840*i/nx;cy=river_center(x)
            for j in range(ny+1):
                y=cy+side*(5.7+(420-5.7)*j/ny)
                vs.append((x,y,surrounding_ground_height(x,y)))
        for i in range(nx):
            for j in range(ny):
                a=i*(ny+1)+j;q=(a,a+ny+1,a+ny+2,a+1);fs.append(q if side>0 else tuple(reversed(q)))
        o=mesh('continuous_panorama_ground',vs,fs,'panorama_ground');uv=o.data.uv_layers.new(name='UVMap')
        for p in o.data.polygons:
            p.use_smooth=True
            for li in p.loop_indices:
                co=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(co.x/24,co.y/24)

def panorama_water():
    nx,ny=420,28;vs=[];fs=[]
    for i in range(nx+1):
        x=-420+840*i/nx
        for j in range(ny+1):
            y=river_center(x)-5.7+11.4*j/ny
            vs.append((x,y,-.06+.012*sin(x*1.2+y*2)+.005*sin(x*3-y)))
    for i in range(nx):
        for j in range(ny):a=i*(ny+1)+j;fs.append((a,a+ny+1,a+ny+2,a+1))
    mesh('continuous_bending_river',vs,fs,'water')

_field_ground_bvh=None
def actual_field_ground(x,y):
    global _field_ground_bvh
    if _field_ground_bvh is None:
        from mathutils.bvhtree import BVHTree
        bpy.context.view_layer.update();verts=[];faces=[]
        sources=[('distant_hills',Matrix.Identity(4)),('distant_hills',Matrix.Rotation(pi,4,'Z')),('bank_ground',Matrix.Translation((0,9.2,0))),('bank_ground',Matrix.Translation((0,-9.2,0))@Matrix.Rotation(pi,4,'Z')),('panorama_terrain',Matrix.Identity(4))]
        for name,xf in sources:
            root=assets[name]
            for o in root.children_recursive:
                if o.type!='MESH':continue
                transform=xf@root.matrix_world.inverted()@o.matrix_world;start=len(verts)
                verts.extend(transform@v.co for v in o.data.vertices)
                faces.extend(tuple(start+i for i in p.vertices) for p in o.data.polygons)
        _field_ground_bvh=BVHTree.FromPolygons(verts,faces)
    hit,normal,index,distance=_field_ground_bvh.ray_cast(Vector((x,y,150)),Vector((0,0,-1)),300)
    assert hit is not None,('Field without terrain',x,y)
    return hit.z

def field_patch(x,y,w,d,mat):
    nx,ny=math.ceil(w/.4),math.ceil(d/.4);vs=[];fs=[]
    for i in range(nx+1):
        for j in range(ny+1):
            xx=x+(i/nx-.5)*w;yy=y+(j/ny-.5)*d
            vs.append((xx,yy,actual_field_ground(xx,yy)+.09))
    for i in range(nx):
        for j in range(ny):a=i*(ny+1)+j;fs.append((a,a+ny+1,a+ny+2,a+1))
    o=mesh('cultivated_field_patch',vs,fs,mat)
    for p in o.data.polygons:p.use_smooth=True
    # Narrow raised rows follow the actual ground, including the old hill surface.
    for row in range(5):
        yy=y+(row-2)*d/5;rv=[];rf=[]
        for i in range(13):
            xx=x+(i/12-.5)*w
            for s in (-1,1):
                ry=yy+s*.065;rv.append((xx,ry,actual_field_ground(xx,ry)+.16))
        for i in range(12):a=i*2;rf.append((a,a+2,a+3,a+1))
        mesh('cultivation_row',rv,rf,'field_ridge')

def panorama_farmland():
    rng=random.Random(816)
    for side in (-1,1):
        for row in range(3):
            for col in range(10):
                x=-72+col*16+rng.uniform(-1,1);y=side*(27+row*12+rng.uniform(-1,1))
                field_patch(x,y,rng.uniform(12,14.8),rng.uniform(8,10.5),('field_green','field_olive','field_earth')[(col+row)%3])

def path_ribbon(name,points,width=.9):
    vs=[];fs=[]
    for k,(x,y) in enumerate(points):
        before=Vector(points[max(0,k-1)]);after=Vector(points[min(len(points)-1,k+1)]);t=(after-before).normalized();n=Vector((-t.y,t.x))
        for s in (-1,1):
            p=Vector((x,y))+n*(width*.5*s);vs.append((p.x,p.y,panorama_surface(p.x,p.y)+.065))
    for i in range(len(points)-1):a=i*2;fs.append((a,a+2,a+3,a+1))
    mesh(name,vs,fs,'huizhou_path')

def panorama_streets():
    for side in (-1,1):
        for end in (-1,1):
            _rbox('extended_riverside_paving',(end*52,side*8.75,.025),(56,3.3,.06),'huizhou_path',.008)
            for s in (-1,1):_rbox('extended_gutter_lip',(end*52,side*(8.3+s*.113),.065),(56,.065,.09),'huizhou_masonry',.008)
            _rbox('extended_street_watercourse',(end*52,side*8.3,.037),(56,.125,.015),'drain_water',.001)
            for k in range(2):
                xx=end*(31.6+k*24)
                points=[(xx,side*9),(xx,side*12.8),(xx-end*1.1,side*14.5),(xx-end*1.1,side*20.8)]
                path_ribbon('village_cross_lane',points,1.0)
        points=[(-82+i*2,side*(20.7+.25*sin(i*.22))) for i in range(83)]
        path_ribbon('continuous_back_lane',points,1.2)

def panorama_sky():
    ns,nr=128,64;radius=700;vs=[(0,0,radius),(0,0,-radius)];fs=[]
    for j in range(1,nr):
        t=pi*j/nr
        for i in range(ns+1):
            a=2*pi*i/ns;vs.append((radius*sin(t)*cos(a),radius*sin(t)*sin(a),radius*cos(t)))
    for i in range(ns):fs.append((0,2+i,2+i+1))
    for j in range(nr-2):
        for i in range(ns):a=2+j*(ns+1)+i;fs.append((a,a+ns+1,a+ns+2,a+1))
    last=2+(nr-2)*(ns+1)
    for i in range(ns):fs.append((1,last+i+1,last+i))
    o=mesh('inward_cloudy_sky_sphere',vs,fs,'panorama_sky')
    import bmesh
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
    uv=o.data.uv_layers.new(name='UVMap')
    for p in o.data.polygons:
        p.use_smooth=True
        for li in p.loop_indices:
            vi=o.data.loops[li].vertex_index
            uv.data[li].uv=(.5,1 if vi==0 else 0) if vi<2 else (((vi-2)%(ns+1))/ns,1-(((vi-2)//(ns+1))+1)/nr)
    o.visible_shadow=False;o.visible_diffuse=False;o.visible_glossy=True;o.visible_transmission=False
    o['render_mode']='sky_unlit';o['background_radius']=radius

def install_panorama_assets():
    root_asset('panorama_terrain',panorama_terrain);root_asset('panorama_farmland',panorama_farmland)
    root_asset('panorama_streets',panorama_streets);root_asset('panorama_sky',panorama_sky)

def relocate_village_trees():
    changes={}
    for i in range(12):
        o=bpy.data.objects.get(f'village_edge_tree_{i}')
        if not o:continue
        old=o.location.copy();x=old.x;y=(1 if i<6 else -1)*(25+3*(i%3))
        o.location=(x,y,actual_field_ground(x,y));changes[o.name]=(old,o.location.copy())
    for name,x,y in [('lane_tree_6',-25.5,23),('lane_tree_7',25.5,-23)]:
        o=bpy.data.objects.get(name)
        if not o:continue
        old=o.location.copy();o.location=(x,y,actual_field_ground(x,y));changes[o.name]=(old,o.location.copy())
    return changes

def layout_panorama_extensions():
    relocate_village_trees()
    for name,label in [('panorama_terrain','panorama_landscape'),('panorama_farmland','panorama_fields'),('panorama_streets','panorama_roads'),('panorama_sky','panorama_cloud_sky')]:place(name,label)
    for side in (-1,1):
        for end in (-1,1):
            for i in range(7):
                x=end*(28+8*i);place('quay_weathered_b' if i%2 else 'quay_segment',f'pano_quay_{side}_{end}_{i}',(x,side*6.7,0),pi if side<0 else 0)
            for i in range(9):
                x=end*(28.6+6*i);y=side*(10.65 if side>0 else 11.8)
                proto=('riverside_house','huizhou_tall_house','huizhou_tea_house','riverside_house')[i%4]
                r=place(proto,f'pano_front_house_{side}_{end}_{i}',(x,y+.12*sin(i*2),0),0 if side>0 else pi);r.scale.z=.97+(i%3)*.035
                if i%2==0:place('household_props',f'pano_doorstep_{side}_{end}_{i}',(x-.9,side*8.65,.055),0 if side>0 else pi)
                if i%3==0:place('lantern_post',f'pano_lantern_{side}_{end}_{i}',(x+1,side*7.7,0),pi if side>0 else 0)
            for i in range(4):
                x=end*(34+12*i);proto='huizhou_courtyard' if i%2==0 else 'riverside_house'
                place(proto,f'pano_back_house_{side}_{end}_{i}',(x,side*16.25,0),0 if side>0 else pi)
    for x in (-56,64):place('arch_bridge',f'pano_bridge_{x}',(x,0,0))
    rng=random.Random(918)
    for i in range(96):
        a=2*pi*i/96+rng.uniform(-.018,.018);r=rng.uniform(95,143);x=r*cos(a);y=r*sin(a)
        if abs(y-river_center(x))<9:continue
        root=place('distant_tree',f'pano_forest_{i}',(x,y,panorama_surface(x,y)),rng.random()*2*pi)
        s=rng.uniform(1.25,2.15);root.scale=(s,s,s)

# Canonical build integration. Incremental updater uses only the extension function.
if 'layout_huizhou' in globals():
    _core_town_layout=layout_huizhou
    def layout_huizhou():_core_town_layout();layout_panorama_extensions()
if 'install_huizhou_assets' in globals():
    _core_town_assets=install_huizhou_assets
    def install_huizhou_assets():_core_town_assets();install_panorama_assets()
water=panorama_water
