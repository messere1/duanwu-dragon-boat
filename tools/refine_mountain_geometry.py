"""Refine mountain geometry from a pinned baseline; preserve village foundations.
Blender Z-up. The runtime OBJ is patched by object, leaving boats/animation intact.
"""
import bpy,bmesh,ast,json,math,sys,shutil,hashlib
from pathlib import Path
from types import SimpleNamespace
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];MODELS=ROOT/'models';sys.path.insert(0,str(ROOT/'tools'))
from river_routes import river_center
BASE=ROOT.parent/'_work/dragonboat/before_mountain_refinement'
assert (BASE/'dragonboat_realism.blend').is_file() and (BASE/'scene_preview.obj').is_file()
bpy.ops.wm.open_mainfile(filepath=str(BASE/'dragonboat_realism.blend'));bpy.context.view_layer.update();world=bpy.data.objects['world_export']

def smooth(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)));return t*t*t*(t*(t*6-15)+10)
def noise(x,y):
 i=math.floor(x);j=math.floor(y);u=x-i;v=y-j;u=u*u*u*(u*(u*6-15)+10);v=v*v*v*(v*(v*6-15)+10)
 def h(a,b):return (math.sin(a*127.1+b*311.7+37.0)*43758.5453123)%1
 return ((1-u)*h(i,j)+u*h(i+1,j))*(1-v)+((1-u)*h(i,j+1)+u*h(i+1,j+1))*v

def meshes(root):return [o for o in [root,*root.children_recursive] if o.type=='MESH']
terrain=[];protected=[]
for root in world.children:
 asset=root.get('asset','')
 if asset in {'panorama_terrain','distant_hills','panorama_valley_closure'}:
  terrain+=meshes(root)
 elif asset=='bank_ground':terrain += [o for o in meshes(root) if 'town_earth' in o.name]
 elif asset=='dispersed_village_landuse':
  terrain += [o for o in meshes(root) if o.name.startswith('graded_inland_earth')]
  protected += [o for o in meshes(root) if o.name.startswith(('irregular_field','branching_village_lane','approach_lane','hillside_house_stone_footing'))]
 elif asset not in {'panorama_sky','rural_tree_belts','landscape_understory','village_lived_detail','tree','distant_tree','reed_patch','river_surface','natural_riverbed'} and asset:
  protected += meshes(root)
# Coalesce building parts into root bounds, and keep detailed parcel/lane bounds.
boxes=[]
for root in world.children:
 if root.get('asset') in {'riverside_house','huizhou_tall_house','huizhou_tea_house','huizhou_courtyard','pavilion'}:
  pts=[o.matrix_world@Vector(v) for o in meshes(root) for v in o.bound_box]
  boxes.append((min(v.x for v in pts)-1.0,max(v.x for v in pts)+1.0,min(v.y for v in pts)-1.0,max(v.y for v in pts)+1.0))
for o in protected:
 # House roots above already cover all subparts. Excluding their individual meshes
 # avoids a huge set of redundant window/roof bounds.
 ancestor=o
 while ancestor.parent and ancestor.parent!=world:ancestor=ancestor.parent
 if ancestor.get('asset') in {'riverside_house','huizhou_tall_house','huizhou_tea_house','huizhou_courtyard','pavilion'}:continue
 pts=[o.matrix_world@Vector(v) for v in o.bound_box]
 boxes.append((min(v.x for v in pts)-.6,max(v.x for v in pts)+.6,min(v.y for v in pts)-.6,max(v.y for v in pts)+.6))
# Spatial index for compact, smoothly feathered protection masks.
grid={};feather=6.
for box in boxes:
 a,b,c,d=box
 for ix in range(math.floor((a-feather)/24),math.floor((b+feather)/24)+1):
  for iy in range(math.floor((c-feather)/24),math.floor((d+feather)/24)+1):grid.setdefault((ix,iy),[]).append(box)
def protection(x,y):
 w=1.
 for a,b,c,d in grid.get((math.floor(x/24),math.floor(y/24)),[]):
  distance=math.hypot(max(a-x,0,x-b),max(c-y,0,y-d));w=min(w,smooth(0,feather,distance))
  if w==0:return 0.
 return w

vs=[];fs=[]
for o in terrain:
 start=len(vs);vs.extend(o.matrix_world@v.co for v in o.data.vertices);fs.extend(tuple(start+i for i in p.vertices) for p in o.data.polygons)
old_ground=BVHTree.FromPolygons(vs,fs);del vs,fs
cache={}
def offset(x,y):
 key=(round(x,4),round(y,4))
 if key in cache:return cache[key]
 river=max(smooth(18,34,abs(y-river_center(x))),smooth(235,315,x));protect=protection(x,y)
 if river*protect<1e-10:cache[key]=0.;return 0.
 # Two warped scales produce branching ridges, saddles and small shoulder gullies.
 wx=x+19*(noise(x*.009+9,y*.009-3)-.5);wy=y+19*(noise(x*.009-5,y*.009+14)-.5)
 ridge=1-abs(2*noise(wx*.012,wy*.012)-1);branch=1-abs(2*noise(wx*.027+21,wy*.027-13)-1)
 detail=noise(wx*.071-8,wy*.071+19)
 r=math.hypot(x,y);far=smooth(110,215,r)
 near=2.25*(noise(wx*.047,wy*.047)*2-1)+.55*(detail*2-1)-.8*(1-branch)**3
 delta=near
 if far>0:
  hit,_,_,_=old_ground.ray_cast(Vector((x,y,240)),Vector((0,0,-1)),500)
  if hit:
   # Background ridges stay connected and rise gradually; the river closes only
   # beyond the animated course, avoiding a cut-off mountain wall at its mouth.
   valley=max(smooth(6,39,abs(y-river_center(x))),smooth(260,350,x))
   profile=.50+.50*smooth(135,275,r)
   target=(5+37*ridge**1.65+13*branch**2.1+3.0*detail)*profile*valley
   delta=near*(1-far)+(target-hit.z)*far
 value=delta*river*protect;cache[key]=value;return value

print('TERRAIN_OBJECTS',len(terrain),'PROTECTED_BOUNDS',len(boxes),flush=True)
before_vertices=sum(len(o.data.vertices) for o in terrain);old_tri=0;protected_checks=0;protected_error=0.;changes=[];bounds=[1e9,-1e9]
for o in terrain:
 o.data=o.data.copy();o.data.calc_loop_triangles();old_tri+=len(o.data.loop_triangles)
 # Refine only coarse terrain edges; fine graded village terraces stay compact.
 if 'continuous_panorama_ground' in o.name:
  bm=bmesh.new();bm.from_mesh(o.data);xf=o.matrix_world.to_3x3();edges=[e for e in bm.edges if (xf@(e.verts[1].co-e.verts[0].co)).length>3.2]
  if edges:bmesh.ops.subdivide_edges(bm,edges=edges,cuts=1,use_grid_fill=True)
  bm.to_mesh(o.data);bm.free()
 xf=o.matrix_world.copy();inv=xf.inverted()
 for v in o.data.vertices:
  p=xf@v.co;d=offset(p.x,p.y)
  if protection(p.x,p.y)==0 or (abs(p.y-river_center(p.x))<=18 and p.x<=235):
   protected_checks+=1;protected_error=max(protected_error,abs(d))
  p.z+=d;v.co=inv@p;changes.append(abs(d));bounds=[min(bounds[0],d),max(bounds[1],d)]
 for polygon in o.data.polygons:polygon.use_smooth=True
 o.data.update();print('REFINED',o.name,len(o.data.vertices),flush=True)
bpy.context.view_layer.update()
# Rigid baseline trees translate as a whole, retaining their trunks and crowns.
rigid_shifts={};moved_trees=[]
for root in world.children:
 if root.get('asset') not in {'tree','distant_tree'}:continue
 p=root.matrix_world.translation.copy();d=offset(p.x,p.y)
 if abs(d)<1e-8:continue
 root.location.z+=d;moved_trees.append((root.name,d))
 for o in meshes(root):rigid_shifts[o.name.replace(' ','_')]=d
instance_rows=[]
for i,line in enumerate((BASE/'vegetation_instances.txt').read_text().splitlines()):
 row=list(map(float,line.split()));d=offset(row[0],-row[2]);row[1]+=d;instance_rows.append(row)
 parent=bpy.data.objects.get('rural_3d_tree_'+str(i));assert parent is not None;parent.location.z+=d
(MODELS/'vegetation_instances.txt').write_text('\n'.join(' '.join(f'{v:.7f}' for v in row) for row in instance_rows)+'\n',encoding='ascii')
# Export only refined surfaces; an OBJ stream patch preserves all other geometry.
CV=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
for node in ast.parse((ROOT/'tools/build_models.py').read_text(encoding='utf8')).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'descendants','evaluated','export_obj'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<export>','exec'),globals())
proxy=SimpleNamespace(type='EMPTY',children_recursive=terrain,matrix_world=Matrix.Identity(4))
item=export_obj('mountain_refined',proxy)
manifest={'terrain_objects':[o.name.replace(' ','_') for o in terrain],'rigid_vertical_shifts':rigid_shifts,'new_component':item,'baseline_scene_obj':str(BASE/'scene_preview.obj')}
(MODELS/'mountain_patch_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
report={'status':'PASS' if protected_error<1e-8 else 'FAIL','terrain_objects':len(terrain),'vertices_before':before_vertices,'vertices_after':sum(len(o.data.vertices) for o in terrain),'baseline_terrain_triangles':old_tri,'refined_triangles':item['triangles'],'protected_bounds':len(boxes),'protected_terrain_vertex_checks':protected_checks,'maximum_protected_displacement_m':protected_error,'height_offset_range_m':bounds,'terrain_vertices_changed':sum(d>1e-4 for d in changes),'rigid_trees_repositioned':len(moved_trees),'shared_tree_instances':len(instance_rows),'old_tree_shifts':moved_trees,'source':'Warped multiscale ridges and gullies; original village foundation and river masks; smooth interpolated normals'}
assert report['status']=='PASS'
(ROOT/'results/mountain_geometry_build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dragonboat_realism.blend'));print('MOUNTAIN_GEOMETRY',json.dumps(report),flush=True)



