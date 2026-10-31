"""Use audited third-party meshes and photographic materials in the course scene."""
_asset_file=ROOT/'external_assets/prepared_open_assets.blend'
with bpy.data.libraries.load(str(_asset_file),link=False) as (_src,_dst):
    _dst.objects=[n for n in _src.objects if n.startswith('open_')]
_open_objects=[o for o in _dst.objects if o]
for _o in _open_objects:
    for _m in _o.data.materials:
        if _m:M[_m.name]=_m
def _copy_open(prefix):
    for src in _open_objects:
        if src.name.startswith(prefix+'__'):
            o=src.copy();bpy.context.collection.objects.link(o);o.matrix_world=Matrix.Identity(4)
            if prefix=='open_head':
                pivot=Vector((4.75,0,.9))
                o.matrix_world=Matrix.Translation((-.20,0,.05))@Matrix.Translation(pivot)@Matrix.Rotation(-.25,4,'Y')@Matrix.Translation(-pivot)
def dragon_head(team):
    _copy_open('open_head')
    loft('wooden_head_mount',[(4.42,0,.85,.17,.10),(4.62,0,.98,.20,.16),(4.82,0,1.09,.18,.17)],'darkwood')
def tree():_copy_open('open_tree')
def rock():_copy_open('open_rock')
def person(team,standing=False,role='rower'):
    _copy_open('open_human_drummer' if role=='drummer' else ('open_human_standing' if standing else 'open_human_seated'))

def photo_material(name,asset,tint=(1,1,1)):
    m=M[name];bs=m.node_tree.nodes.get('Principled BSDF');folder=ROOT/'external_assets'/asset
    nodes=m.node_tree.nodes;links=m.node_tree.links
    for l in list(bs.inputs['Base Color'].links):links.remove(l)
    tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(folder/(asset+'_Diffuse.jpg')))
    _=tex.image.pixels[0]
    tex.image.filepath_raw=str(ROOT/'textures'/(asset+'_Diffuse.png'));tex.image.file_format='PNG';tex.image.save();tex.image.pack()
    mul=nodes.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;mul.inputs[2].default_value=(*tint,1)
    links.new(tex.outputs['Color'],mul.inputs[1]);links.new(mul.outputs['Color'],bs.inputs['Base Color'])
    m['obj_base_image']=tex.image.name;m['obj_diffuse_tint']=list(tint)
    for kind in ('nor_gl','Rough'):
        n=nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(folder/(asset+'_'+kind+'.jpg')));n.image.colorspace_settings.name='Non-Color'
        _=n.image.pixels[0]
        n.image.filepath_raw=str(ROOT/'textures'/(asset+'_'+kind+'.png'));n.image.file_format='PNG';n.image.save();n.image.pack()
        if kind=='nor_gl':
            normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.55;links.new(n.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],bs.inputs['Normal'])
            m['obj_normal_image']=n.image.name
        else:links.new(n.outputs['Color'],bs.inputs['Roughness']);m['obj_rough_image']=n.image.name
photo_material('wood','wood_planks_grey',(.65,.43,.24))
photo_material('stone','stone_brick_wall_001')
def configure_open_environment(world):
    world.use_nodes=True;n=world.node_tree.nodes;n.clear();l=world.node_tree.links
    env=n.new('ShaderNodeTexEnvironment');env.image=bpy.data.images.load(str(ROOT/'external_assets/kloofendal_48d_partly_cloudy/kloofendal_48d_partly_cloudy_1k.hdr'));env.image.pack()
    hdr=n.new('ShaderNodeBackground');hdr.inputs['Strength'].default_value=.45;l.new(env.outputs['Color'],hdr.inputs['Color'])
    bg=n.new('ShaderNodeBackground');bg.inputs['Color'].default_value=(.22,.25,.26,1);bg.inputs['Strength'].default_value=.8
    rays=n.new('ShaderNodeLightPath');mix=n.new('ShaderNodeMixShader');l.new(rays.outputs['Is Camera Ray'],mix.inputs[0]);l.new(hdr.outputs[0],mix.inputs[1]);l.new(bg.outputs[0],mix.inputs[2])
    out=n.new('ShaderNodeOutputWorld');l.new(mix.outputs[0],out.inputs['Surface'])
