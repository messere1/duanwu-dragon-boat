"""Remove the old protected rectangular river-mouth closure in the far distance."""
import bpy,ast,json,math,sys
from pathlib import Path
from types import SimpleNamespace
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];MODELS=ROOT/'models';BASE=ROOT.parent/'_work/dragonboat/before_mountain_refinement';sys.path.insert(0,str(ROOT/'tools'))
from river_routes import river_center
for node in ast.parse((ROOT/'tools/refine_mountain_geometry.py').read_text(encoding='utf-8-sig')).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'smooth','noise'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<math>','exec'),globals())
manifest=json.loads((MODELS/'mountain_patch_manifest.json').read_text());names=manifest['terrain_objects']
bpy.ops.wm.open_mainfile(filepath=str(BASE/'dragonboat_realism.blend'));bpy.context.view_layer.update();vs=[];faces=[]
for name in names:
 o=bpy.data.objects[name];start=len(vs);vs.extend(o.matrix_world@v.co for v in o.data.vertices);faces.extend(tuple(start+i for i in p.vertices) for p in o.data.polygons)
old=BVHTree.FromPolygons(vs,faces);del vs,faces
bpy.ops.wm.open_mainfile(filepath=str(BASE/'mountain_with_understory.blend'));bpy.context.view_layer.update();terrain=[bpy.data.objects[name] for name in names];changed=0
for o in terrain:
 xf=o.matrix_world.copy();inv=xf.inverted()
 for v in o.data.vertices:
  p=xf@v.co
  if p.x<=235:continue
  river=smooth(18,34,abs(p.y-river_center(p.x)));extra=max(river,smooth(235,315,p.x))-river
  if extra<1e-9:continue
  hit,_,_,_=old.ray_cast(Vector((p.x,p.y,240)),Vector((0,0,-1)),500)
  if hit is None:continue
  wx=p.x+19*(noise(p.x*.009+9,p.y*.009-3)-.5);wy=p.y+19*(noise(p.x*.009-5,p.y*.009+14)-.5)
  ridge=1-abs(2*noise(wx*.012,wy*.012)-1);branch=1-abs(2*noise(wx*.027+21,wy*.027-13)-1);detail=noise(wx*.071-8,wy*.071+19)
  valley=max(smooth(6,39,abs(p.y-river_center(p.x))),smooth(260,350,p.x));profile=.50+.50*smooth(135,275,math.hypot(p.x,p.y))
  target=(5+37*ridge**1.65+13*branch**2.1+3*detail)*profile*valley
  p.z+=(target-hit.z)*extra;v.co=inv@p;changed+=1
 o.data.update()
bpy.context.view_layer.update();CV=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
for node in ast.parse((ROOT/'tools/build_models.py').read_text(encoding='utf8')).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'descendants','evaluated','export_obj'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<export>','exec'),globals())
item=export_obj('mountain_refined',SimpleNamespace(type='EMPTY',children_recursive=terrain,matrix_world=Matrix.Identity(4)));manifest['new_component']=item;(MODELS/'mountain_patch_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
r=json.loads((ROOT/'results/mountain_geometry_build.json').read_text());r['refined_triangles']=item['triangles'];r['far_closure_vertices_reconnected']=changed;r['far_river_protection_release_x_m']=[235,315];(ROOT/'results/mountain_geometry_build.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dragonboat_realism.blend'));print('FAR_RIDGE_RECONNECTED',changed,item['triangles'],flush=True)
