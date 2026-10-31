import bpy,json,collections
from pathlib import Path
r=Path.cwd();bpy.ops.wm.open_mainfile(filepath=str(r/'dragonboat_realism.blend'))
w=bpy.data.objects['world_export'];counts=collections.Counter(o.get('asset','') for o in w.children);print('ROOT_ASSETS',json.dumps(counts),flush=True)
for root in w.children:
 if root.get('asset') in {'distant_hills','panorama_terrain','panorama_valley_closure','bank_ground','dispersed_village_landuse'}:
  obs=[o for o in [root,*root.children_recursive] if o.type=='MESH'];print('GROUND',root.name,root.get('asset'),[(o.name,len(o.data.vertices)) for o in obs[:7]],flush=True)
