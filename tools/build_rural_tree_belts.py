"""Bake the existing CC0 tree into an alpha atlas and add inexpensive tree belts.
This is a render of the audited 3D asset, not a generated photograph.
"""
import bpy,math,random,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(ROOT/'external_assets/prepared_open_assets.blend'),link=False) as (src,dst):
    dst.objects=[n for n in src.objects if n.startswith('open_tree__')]
for o in dst.objects:
    if o:bpy.context.collection.objects.link(o);o.hide_render=False;o.hide_set(False)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.render.film_transparent=True
scene.render.resolution_x=640;scene.render.resolution_y=768;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.world=bpy.data.worlds.new('Atlas ambient');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.75,.82,1,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.7
ld=bpy.data.lights.new('Atlas sun','SUN');ld.energy=2;sun=bpy.data.objects.new('Atlas sun',ld);bpy.context.collection.objects.link(sun);sun.rotation_euler=(.5,-.6,-.4)
cd=bpy.data.cameras.new('Tree atlas camera');cam=bpy.data.objects.new('Tree atlas camera',cd);bpy.context.collection.objects.link(cam);cam.location=(0,-10,2.2);cam.rotation_euler=(Vector((0,0,2.2))-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=5.2;scene.camera=cam
exec((ROOT/'tools/configure_render_device.py').read_text(encoding='utf8'),globals());configure_preview_device()
scene.render.filepath=str(ROOT/'textures/rural_tree_atlas.png')
if not (ROOT/'textures/rural_tree_atlas.png').exists():render_preview_frame()

bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_models.blend'));bpy.context.view_layer.update();world=bpy.data.objects['world_export']
ground_assets={'panorama_terrain','bank_ground','distant_hills','panorama_valley_closure'}
vs=[];fs=[];house_bounds=[]
for r in world.children:
    if r.get('asset') in ground_assets:
        for o in [r,*r.children_recursive]:
            if o.type!='MESH':continue
            base=len(vs);vs.extend(o.matrix_world@v.co for v in o.data.vertices);fs.extend(tuple(base+i for i in p.vertices) for p in o.data.polygons)
    if r.get('asset')=='dispersed_village_landuse':
        for o in r.children_recursive:
            if o.type=='MESH' and o.name.startswith('irregular_field'):
                pts=[o.matrix_world@Vector(v) for v in o.bound_box];house_bounds.append((min(v.x for v in pts)-.8,max(v.x for v in pts)+.8,min(v.y for v in pts)-.8,max(v.y for v in pts)+.8))
    if r.get('asset') in {'riverside_house','huizhou_tall_house','huizhou_tea_house','huizhou_courtyard','pavilion'}:
        pts=[o.matrix_world@Vector(v) for o in r.children_recursive if o.type=='MESH' for v in o.bound_box]
        if pts:house_bounds.append((min(v.x for v in pts)-3,max(v.x for v in pts)+3,min(v.y for v in pts)-3,max(v.y for v in pts)+3))
ground=BVHTree.FromPolygons(vs,fs);del vs,fs
import sys
sys.path.insert(0,str(ROOT/'tools'));from river_routes import river_center
rng=random.Random(20261030);vertices=[];uvs=[];faces=[];trees=[]
centers=[(-48,-42),(-28,43),(-2,-47),(18,44),(43,-31),(59,53),(76,-26),(86,65),(109,-29),(132,58),(152,-46),(147,94)]
for cx,cy in centers:
    for i in range(32):
        x=rng.gauss(cx,10);y=rng.gauss(cy,8)
        if abs(y-river_center(x))<25:continue
        if any(a<x<b and c<y<d for a,b,c,d in house_bounds):continue
        hit,_,_,_=ground.ray_cast(Vector((x,y,180)),Vector((0,0,-1)),350)
        if hit is None:continue
        h=rng.uniform(4.2,7.7);w=h*640/768;angle=rng.random()*math.pi;z=hit.z-(.4/5.2)*h-.08
        for a in (angle,angle+math.pi/2):
            dx=math.cos(a)*w/2;dy=math.sin(a)*w/2;base=len(vertices)
            vertices.extend([(x-dx,y-dy,z),(x+dx,y+dy,z),(x+dx,y+dy,z+h),(x-dx,y-dy,z+h)])
            uvs.extend([(0,0),(1,0),(1,1),(0,1)]);faces.extend([(base,base+1,base+2),(base,base+2,base+3)])
        trees.append((x,y,z,h))
mesh=bpy.data.meshes.new('Rural tree belt cards');mesh.from_pydata(vertices,[],faces);mesh.update();uv=mesh.uv_layers.new()
for p in mesh.polygons:
    for li in p.loop_indices:uv.data[li].uv=uvs[mesh.loops[li].vertex_index]
obj=bpy.data.objects.new('rural_tree_belts',mesh);bpy.context.collection.objects.link(obj);obj.parent=world;obj['asset']='rural_tree_belts'
mat=bpy.data.materials.new('rural_tree_atlas');mat.use_nodes=True;tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'textures/rural_tree_atlas.png'));tex.image.pack();bs=mat.node_tree.nodes.get('Principled BSDF');mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);mat.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha']);bs.inputs['Roughness'].default_value=.9;mat.surface_render_method='DITHERED';obj.data.materials.append(mat)
out=['mtllib environment_details.mtl','o rural_tree_belts','usemtl rural_tree_atlas']
# Native Z-up to the renderer's Y-up, with per-corner normals/UVs.
index=1
for p in mesh.polygons:
    n=p.normal
    for li in p.loop_indices:
        x,y,z=vertices[mesh.loops[li].vertex_index];u,v=uvs[mesh.loops[li].vertex_index];out.extend([f'v {x:.6f} {z:.6f} {-y:.6f}',f'vt {u} {v}',f'vn {n.x:.6f} {n.z:.6f} {-n.y:.6f}'])
    out.append('f '+' '.join(f'{i}/{i}/{i}' for i in range(index,index+3)));index+=3
(ROOT/'models/environment_details.obj').write_text('\n'.join(out)+'\n',encoding='utf8')
(ROOT/'models/environment_details.mtl').write_text('newmtl rural_tree_atlas\nKd 1 1 1\nKs 0 0 0\nNs 4\nmap_Kd ../textures/rural_tree_atlas.png\n',encoding='utf8')
(ROOT/'models/environment_details.json').write_text(json.dumps({'trees':len(trees),'triangles':len(faces),'source':'Existing CC0 Poly Haven Tree Small 02, Cycles orthographic alpha bake','placements_zup':trees},indent=2),encoding='utf8')
bpy.context.preferences.filepaths.save_version=0;bpy.context.scene.cycles.device='CPU';bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dragonboat_realism.blend'))
print('RURAL_BELTS',len(trees),'triangles',len(faces),flush=True)
