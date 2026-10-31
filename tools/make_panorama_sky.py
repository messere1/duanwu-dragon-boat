"""Bake the credited CC0 photographic HDR sky into a portable PNG. Run with Blender."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'external_assets/kloofendal_48d_partly_cloudy'
source=folder/'kloofendal_48d_partly_cloudy_2k.hdr'
if not source.exists():source=folder/'kloofendal_48d_partly_cloudy_1k.hdr'
assert source.is_file(),source
im=bpy.data.images.load(str(source),check_existing=True)
scene=bpy.context.scene;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
scene.view_settings.view_transform='Standard';scene.view_settings.exposure=-.7;scene.view_settings.gamma=1
out=ROOT/'textures/panorama_sky.png';im.save_render(str(out),scene=scene)
print('PHOTOGRAPHIC_CC0_SKY_READY',str(out),flush=True)
