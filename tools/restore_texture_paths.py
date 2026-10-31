"""Recover external texture references after loading packed Blender/GLB assets."""
def restore_material_image_paths():
    import bpy,re
    from pathlib import Path
    texture_root=ROOT/'textures';restored=[]
    images={n.image for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
    for im in images:
        existing=Path(bpy.path.abspath(im.filepath)) if im.filepath else None
        if existing and existing.is_file():
            im.filepath_raw=str(existing)
            continue
        clean=re.sub(r'\.\d{3}$','',im.name)
        candidates=[im.get('prepared_file',''),clean,Path(clean).stem+'.png']
        target=next((texture_root/name for name in candidates if name and (texture_root/name).is_file()),None)
        if target is None:
            assert im.size[0]>0 and im.size[1]>0,('Cannot restore packed image',im.name)
            target=texture_root/('packed_'+re.sub(r'[^\w.-]','_',Path(clean).stem)+'.png')
            im.filepath_raw=str(target);im.file_format='PNG';im.save()
        im.filepath_raw=str(target);restored.append(target.name)
    print('RESTORED_TEXTURE_REFERENCES',len(restored),flush=True)
    return restored
