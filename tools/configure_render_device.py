"""Use a local Cycles GPU for preview renders without saving user preferences."""
def configure_preview_device():
    import bpy
    bpy.context.preferences.use_preferences_save=False
    prefs=bpy.context.preferences.addons['cycles'].preferences
    for backend in ('OPTIX','CUDA','HIP'):
        try:
            prefs.compute_device_type=backend;prefs.refresh_devices()
            devices=[d for d in prefs.devices if d.type==backend]
            if not devices:continue
            for d in prefs.devices:d.use=d in devices
            bpy.context.scene.cycles.device='GPU'
            print('PREVIEW_GPU',backend,[d.name for d in devices],flush=True)
            return
        except (TypeError,RuntimeError):continue
    bpy.context.scene.cycles.device='CPU';print('PREVIEW_CPU',flush=True)

def render_preview_frame():
    import bpy
    try:bpy.ops.render.render(write_still=True)
    except RuntimeError:
        if bpy.context.scene.cycles.device!='GPU':raise
        bpy.context.scene.cycles.device='CPU';print('PREVIEW_GPU_FALLBACK_TO_CPU',flush=True)
        bpy.ops.render.render(write_still=True)
