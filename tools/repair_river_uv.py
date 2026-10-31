"""Repair only missing generated UV layers, preserving exported geometry."""
import bpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
count=0
for m in bpy.data.meshes:
    if m.uv_layers.active:continue
    uv=m.uv_layers.new(name='UVMap');count+=1
    for p in m.polygons:
        for li in p.loop_indices:
            v=m.vertices[m.loops[li].vertex_index].co;uv.data[li].uv=(v.x/3,v.y/3)
if count:
    exec((ROOT/'tools/restore_texture_paths.py').read_text(encoding='utf-8'),globals());restore_material_image_paths()
    for o in list(bpy.context.selected_objects):o.select_set(False)
    world=bpy.data.objects['world_export']
    for o in [world]+list(world.children_recursive):o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'models/dragonboat_scene.glb'),use_selection=True,export_format='GLB',export_apply=True)
    exec((ROOT/'tools/fix_sky_glb.py').read_text(encoding='utf-8'),globals());ensure_unlit_sky(ROOT/'models/dragonboat_scene.glb')
    for o in list(bpy.context.selected_objects):o.select_set(False)
    bpy.context.preferences.filepaths.save_version=0;bpy.context.scene.cycles.device='CPU'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dragonboat_models.blend'))
print('RIVER_UV_COMPLETE',count,flush=True)
