"""Build a CC0 MakeHuman avatar with MPFB, kept outside course runtime dependencies."""
import bpy,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];W=R.parent/'_work/dragonboat'
sys.path.insert(0,str(W/'mpfb2-2.0.18/src'))
import mpfb
# Source-only tool session: keep addon caches in _work and do not save preferences.
bpy.context.preferences.use_preferences_save=False
bpy.utils.extension_path_user=lambda package,path='',create=False:str(W/'mpfb_user'/path)
if 'mpfb' not in bpy.context.preferences.addons:
    bpy.context.preferences.addons.new().module='mpfb'
mpfb.register()
from mpfb.services.humanservice import HumanService
from mpfb.services.targetservice import TargetService
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.0,age=.30,muscle=.65,weight=.45)
macro['race']={'asian':1.0,'african':0,'caucasian':0}
body=HumanService.create_human(macro_detail_dict=macro)
rig=HumanService.add_builtin_rig(body,'default')
print('HUMAN_CREATED',body.name,'BONES',list(rig.pose.bones.keys()),flush=True)
A=W/'makehuman_selected'
if not A.exists():A=R/'external_assets/makehuman_cc0'
skin=A/'skins/middleage_asian_male/middleage_asian_male.mhmat'
HumanService.set_character_skin(str(skin),body,skin_type='MAKESKIN')
for rel in ['clothes/male_casualsuit04/male_casualsuit04.mhclo','hair/short01/short01.mhclo','eyes/low-poly/low-poly.mhclo','eyebrows/eyebrow001/eyebrow001.mhclo','clothes/shoes02/shoes02.mhclo']:
    file=A/rel
    if file.exists():HumanService.add_mhclo_asset(str(file),body,set_up_rigging=True,interpolate_weights=True,import_subrig=False,import_weights=True)
print('BONE_COORDS',json.dumps({b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None} for b in rig.data.bones}),flush=True)
for im in bpy.data.images:
    if im.source=='FILE' and im.size[0]>0:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(W/'human_base.blend'))
