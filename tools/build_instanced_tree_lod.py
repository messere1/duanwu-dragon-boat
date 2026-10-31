"""Replace the baked cross cards with shared, genuine three-dimensional tree LODs."""
import bpy,ast,json,math,random
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[1];MODELS=ROOT/'models'
CV=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_realism.blend'))
world=bpy.data.objects['world_export'];old=bpy.data.objects.get('rural_tree_belts')
if old:
    for o in list(old.children_recursive)[::-1]:bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.objects.remove(old,do_unlink=True)
for old in list(bpy.data.objects):
    if old.name.startswith('vegetation_lod') and old.type=='EMPTY':
        for child in list(old.children_recursive)[::-1]:bpy.data.objects.remove(child,do_unlink=True)
        bpy.data.objects.remove(old,do_unlink=True)
with bpy.data.libraries.load(str(ROOT/'external_assets/prepared_open_assets.blend'),link=False) as (src,dst):dst.objects=[n for n in src.objects if n.startswith('open_tree__')]
source=[o for o in dst.objects if o];prototype=bpy.data.objects.new('vegetation_lod',None);bpy.context.collection.objects.link(prototype)
for o in source:
    bpy.context.collection.objects.link(o);o.hide_set(False);o.hide_render=False
    mod=o.modifiers.new('Foliage silhouette LOD','DECIMATE');mod.ratio=1.0
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();mesh=bpy.data.meshes.new_from_object(o.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg);o.modifiers.clear();o.data=mesh;o.parent=prototype
materials=[]
for o in source:
    for m in o.data.materials:
        if m and m not in materials:materials.append(m)
mtl=[]
for i,m in enumerate(materials):
    m.name='lod_tree_'+str(i);mtl.extend(['newmtl '+m.name,'Kd 0.88 0.95 0.82','Ks 0.025 0.025 0.025','Ns 8'])
    images=[n.image for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
    colors=[im for im in images if im.colorspace_settings.name not in ('Non-Color','Raw')]
    if not colors:raise RuntimeError('Tree color texture missing')
    im=colors[0];name='lod_tree_color_'+str(i)+'.png';im.filepath_raw=str(ROOT/'textures'/name);im.file_format='PNG';im.save();im.pack()
    mtl.append('map_Kd ../textures/'+name)
    print('TREE_MATERIAL',m.name,name,flush=True)
(MODELS/'vegetation_lod.mtl').write_text('\n'.join(mtl)+'\n',encoding='utf8')
source_text=(ROOT/'tools/build_models.py').read_text(encoding='utf8')
for node in ast.parse(source_text).body:
    if isinstance(node,ast.FunctionDef) and node.name in {'descendants','evaluated','export_obj'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<export>', 'exec'),globals())
item=export_obj('vegetation_lod',prototype)
# The shared exporter uses the scene palette by default; this asset has its own MTL.
p=MODELS/'vegetation_lod.obj';text=p.read_text(encoding='utf8').replace('mtllib palette.mtl','mtllib vegetation_lod.mtl');p.write_text(text,encoding='utf8')
placements=json.loads((MODELS/'environment_details.json').read_text())['placements_zup'];root=bpy.data.objects.new('rural_tree_belts',None);bpy.context.collection.objects.link(root);root.parent=world;root['asset']='rural_tree_belts';rng=random.Random(20261101);rows=[]
current_rows=[list(map(float,l.split())) for l in (MODELS/'vegetation_instances.txt').read_text().splitlines()] if (MODELS/'vegetation_instances.txt').exists() else []
for i,(x,y,z,h) in enumerate(placements):
    ground=(current_rows[i][1]+.035) if len(current_rows)==len(placements) else (z+h*.4/5.2+.08);scale=h*4.2/5.2/4.2;angle=rng.random()*math.tau
    parent=bpy.data.objects.new('rural_3d_tree_'+str(i),None);bpy.context.collection.objects.link(parent);parent.parent=root;parent.location=(x,y,ground-.035);parent.rotation_euler.z=angle;parent.scale=(scale,scale,scale)
    for src in source:
        o=src.copy();bpy.context.collection.objects.link(o);o.parent=parent;o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=src.matrix_basis.copy();o.hide_render=False;o.hide_set(False)
    rows.append((x,ground-.035,-y,math.degrees(angle),scale))
for o in [prototype,*source]:o.hide_render=True;o.hide_set(True)
(MODELS/'vegetation_instances.txt').write_text('\n'.join(' '.join(f'{v:.7f}' for v in row) for row in rows)+'\n',encoding='ascii')
report={'instances':len(rows),'prototype_triangles':item['triangles'],'source':'Poly Haven CC0 Tree Small 02, shared prepared mesh; foliage silhouette preserved without a second decimation','representation':'3D indexed mesh instances; no crossed image planes','color_materials':len(materials)}
(MODELS/'vegetation_lod.json').write_text(json.dumps(report,indent=2),encoding='utf8')
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dragonboat_realism.blend'));print('TREE_LOD',json.dumps(report),flush=True)

