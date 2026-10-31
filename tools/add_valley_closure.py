"""Close the far eastern river mouth behind a low mountain saddle."""
def add_valley_closure(world):
    import bpy,math
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from river_routes import river_center,smooth
    existing=bpy.data.objects.get('far_river_valley_closure')
    if existing:return existing
    vs=[];fs=[]
    for root in world.children:
        if root.get('asset') not in ('panorama_terrain','distant_hills'):continue
        for o in root.children_recursive:
            if o.type!='MESH':continue
            start=len(vs);vs.extend(o.matrix_world@v.co for v in o.data.vertices)
            fs.extend(tuple(start+i for i in p.vertices) for p in o.data.polygons)
    ground=BVHTree.FromPolygons(vs,fs);vs=[];fs=[];nx,ny=170,80
    for i in range(nx+1):
        x=260+i
        for j in range(ny+1):
            d=-40+j;y=river_center(x)+d
            h,_,_,_=ground.ray_cast(Vector((x,y,150)),Vector((0,0,-1)),300)
            ridge=45*math.exp(-((x-372)/32)**2)*(1-smooth((abs(d)-10)/28))-.35
            vs.append((x,y,max(h.z+.003 if h else -.4,ridge)))
    for i in range(nx):
        for j in range(ny):a=i*(ny+1)+j;fs.append((a,a+ny+1,a+ny+2,a+1))
    data=bpy.data.meshes.new('far_river_saddle_mesh');data.from_pydata(vs,[],fs);data.update()
    data.materials.append(bpy.data.materials['panorama_ground']);uv=data.uv_layers.new(name='UVMap')
    for p in data.polygons:
        p.use_smooth=True
        for li in p.loop_indices:
            c=data.vertices[data.loops[li].vertex_index].co;uv.data[li].uv=(c.x/24,c.y/24)
    root=bpy.data.objects.new('far_river_valley_closure',None);bpy.context.collection.objects.link(root);root.parent=world;root['asset']='panorama_valley_closure'
    o=bpy.data.objects.new('distant_river_saddle',data);bpy.context.collection.objects.link(o);o.parent=root
    return root
