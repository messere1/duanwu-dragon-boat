"""Solid eroded bank edges; prevents floating water and angular flood tongues."""
def make_natural_banks(world):
    import bpy,math
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from river_routes import river_center,half_width,smooth
    changed=[];terrain=[]
    for r in world.children:
        if r.get('asset')=='river_surface':
            for o in r.children_recursive:
                if o.type!='MESH':continue
                for i,v in enumerate(o.data.vertices):
                    v.co.y=river_center(v.co.x)+(2*(i%25)/24-1)*half_width(v.co.x)
                o.data.update();changed.append(o)
        if r.get('asset')=='panorama_terrain':
            for o in r.children_recursive:
                if o.type!='MESH':continue
                for v in o.data.vertices:
                    x,y,z=v.co
                    if not 82<x<270:continue
                    d=abs(y-river_center(x))-half_width(x)
                    if -.1<d<8:
                        profile=(.20+.08*math.sin(x*.23))*(1-smooth(d/8))-.05*smooth(d/8)
                        v.co.z=max(z,profile)
                o.data.update();terrain.append(o);changed.append(o)
    vs=[];fs=[]
    for o in terrain:
        start=len(vs);vs.extend(o.matrix_world@v.co for v in o.data.vertices);fs.extend(tuple(start+k for k in p.vertices) for p in o.data.polygons)
    ground=BVHTree.FromPolygons(vs,fs);vs=[];fs=[]
    for side in (-1,1):
        start=len(vs)
        for i in range(377):
            x=82+i*.5;d=half_width(x);y=river_center(x)+side*(d-.035)
            hit,_,_,_=ground.ray_cast(Vector((x,river_center(x)+side*(d+.22),50)),Vector((0,0,-1)),100)
            z=hit.z if hit else .2+.08*math.sin(x*.23)
            vs.extend([(x,y,z+.008),(x,y,-1.6)])
        for i in range(376):
            a=start+i*2;q=(a,a+2,a+3,a+1);fs.append(q if side>0 else tuple(reversed(q)))
    data=bpy.data.meshes.new('eroded_bank_edges_mesh');data.from_pydata(vs,[],fs);data.update();data.materials.append(bpy.data.materials['river_gravel'])
    uv=data.uv_layers.new(name='UVMap')
    for p in data.polygons:
        for li in p.loop_indices:
            c=data.vertices[data.loops[li].vertex_index].co;uv.data[li].uv=(c.x/3,c.z/3)
    root=bpy.data.objects.new('eroded_riverbank_faces',None);bpy.context.collection.objects.link(root);root.parent=world;root['asset']='eroded_riverbank_faces'
    o=bpy.data.objects.new('continuous_solid_eroded_shore',data);bpy.context.collection.objects.link(o);o.parent=root
    return changed,root
