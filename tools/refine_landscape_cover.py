"""Terrain-fitted woodland understory and bamboo, editable in the full scene."""
import bpy,ast,math,random,json,sys
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];MODELS=ROOT/'models';sys.path.insert(0,str(ROOT/'tools'))
from river_routes import river_center
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'dragonboat_realism.blend'))
world=bpy.data.objects['world_export'];old=bpy.data.objects.get('landscape_understory')
if old:
 for o in list(old.children_recursive)[::-1]:bpy.data.objects.remove(o,do_unlink=True)
 bpy.data.objects.remove(old,do_unlink=True)
parts={};rng=random.Random(20261031)
for n in ast.parse((ROOT/'tools/add_lived_village_details.py').read_text(encoding='utf8')).body:
 if isinstance(n,ast.FunctionDef) and n.name in {'tri','quad','rod','blade'}:exec(compile(ast.Module(body=[n],type_ignores=[]),'<helpers>','exec'),globals())
verts=[];faces=[];exclusions=[]
for root in world.children:
 asset=root.get('asset')
 if asset in {'panorama_terrain','bank_ground','distant_hills','dispersed_village_landuse','panorama_valley_closure'}:
  for o in [root,*root.children_recursive]:
   if o.type!='MESH':continue
   if asset=='dispersed_village_landuse' and not o.name.startswith('graded_inland_earth'):
    if o.name.startswith(('irregular_field','village_lane','approach_lane')):
     p=[o.matrix_world@Vector(v) for v in o.bound_box];exclusions.append((min(v.x for v in p)-.6,max(v.x for v in p)+.6,min(v.y for v in p)-.6,max(v.y for v in p)+.6))
    continue
   start=len(verts);verts.extend(o.matrix_world@v.co for v in o.data.vertices);faces.extend(tuple(start+i for i in p.vertices) for p in o.data.polygons)
 if asset in {'riverside_house','huizhou_tall_house','huizhou_tea_house','huizhou_courtyard','pavilion'}:
  p=[o.matrix_world@Vector(v) for o in root.children_recursive if o.type=='MESH' for v in o.bound_box]
  if p:exclusions.append((min(v.x for v in p)-1.3,max(v.x for v in p)+1.3,min(v.y for v in p)-1.3,max(v.y for v in p)+1.3))
ground=BVHTree.FromPolygons(verts,faces);del verts,faces

def sample(x,y):
 if abs(y-river_center(x))<13 or any(a<x<b and c<y<d for a,b,c,d in exclusions):return None
 hit,normal,_,_=ground.ray_cast(Vector((x,y,180)),Vector((0,0,-1)),350)
 if hit is None or normal.z<.48:return None
 return hit

def leaf(center,size,angle,tilt,mat):
 u=Vector((math.cos(angle),math.sin(angle),0));v=Vector((-math.sin(angle)*math.cos(tilt),math.cos(angle)*math.cos(tilt),math.sin(tilt)));n=u.cross(v)
 # A shallow folded leaf, with an uneven tapered outline rather than a solid ball.
 p=[center+u*x*size+v*y*size for x,y in ((0,-.56),(.27,-.18),(.24,.17),(0,.64),(-.24,.17),(-.27,-.18))]
 c=center+n*size*.075
 for i in range(6):tri(mat,(c,p[i],p[(i+1)%6]))

shrubs=[];spacing=[]
for attempt in range(9000):
 x=rng.uniform(-95,165);y=river_center(x)+rng.choice((-1,1))*rng.uniform(14,102)
 density=.5+.26*math.sin(x*.067+y*.089)+.23*math.sin(x*.18-y*.12)
 if rng.random()>density or any((x-a)**2+(y-b)**2<1.2**2 for a,b in spacing):continue
 p=sample(x,y)
 if p is None:continue
 spacing.append((x,y));h=rng.uniform(.65,1.5) if abs(y-river_center(x))<23 else rng.uniform(1.6,3.9);radius=h*rng.uniform(.60,.82)
 for b in range(3):
  angle=rng.random()*math.tau;end=p+Vector((math.cos(angle)*radius*.55,math.sin(angle)*radius*.55,h*(.67+.09*b)))
  rod('understory_bark',p,end,.030,6,.006)
  for j in range(53):
   a=rng.random()*math.tau;r=math.sqrt(rng.random());z=rng.uniform(-1,1)
   center=end+Vector((math.cos(a)*radius*r,math.sin(a)*radius*r,z*h*.30))
   leaf(center,rng.uniform(.20,.38),rng.random()*math.tau,rng.uniform(.3,2.7),'understory_leaf_'+str(rng.randrange(3)))
 shrubs.append((x,y,p.z,h))
 if len(shrubs)>=1050:break

bamboos=[]
for attempt in range(700):
 x=rng.uniform(-70,130);y=river_center(x)+rng.choice((-1,1))*rng.uniform(16,43)
 p=sample(x,y)
 if p is None or any((x-a)**2+(y-b)**2<9**2 for a,b,_,_ in bamboos):continue
 for stem in range(rng.randint(5,9)):
  angle=rng.random()*math.tau;r=rng.uniform(.05,.65);h=rng.uniform(2.7,4.8);base=p+Vector((math.cos(angle)*r,math.sin(angle)*r,-.03));lean=Vector((rng.uniform(-.32,.32),rng.uniform(-.32,.32),0))
  for seg in range(7):
   a=base+Vector((0,0,h*seg/7))+lean*(seg/7)**2;b=base+Vector((0,0,h*(seg+1)/7))+lean*((seg+1)/7)**2
   rod('understory_bamboo',a,b,.026*(1-seg*.07),6,.023*(1-seg*.07))
   rod('understory_node',b-Vector((0,0,.014)),b+Vector((0,0,.014)),.028*(1-seg*.07),6)
   if seg<3:continue
   for side in (-1,1):
    d=Vector((math.cos(angle+side*.8),math.sin(angle+side*.8),.30));end=b+d*rng.uniform(.45,.85);rod('understory_bamboo',b,end,.006,4,.0015)
    for j in range(5):
     c=b.lerp(end,.25+j*.15);blade(c,.08,.018,angle+side*1.1,.22,'understory_bamboo_leaf')
 bamboos.append((x,y,p.z,h))
 if len(bamboos)>=38:break

spec={'understory_bark':(.16,.12,.07),'understory_leaf_0':(.105,.18,.055),'understory_leaf_1':(.17,.25,.078),'understory_leaf_2':(.23,.29,.11),'understory_bamboo':(.22,.31,.11),'understory_node':(.32,.35,.16),'understory_bamboo_leaf':(.13,.25,.075)}
root=bpy.data.objects.new('landscape_understory',None);bpy.context.collection.objects.link(root);root.parent=world;root['asset']='landscape_understory'
# Split by spatial cell as well as material so the runtime can reject whole patches.
for mat,triangles in parts.items():
 m=bpy.data.materials.get(mat) or bpy.data.materials.new(mat);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*spec[mat],1);bs.inputs['Roughness'].default_value=.9
 cells={}
 for t in triangles:
  center=sum(t,Vector())/3;cells.setdefault((math.floor(center.x/32),math.floor(center.y/32)),[]).append(t)
 for (cx,cy),ts in cells.items():
  vs=[tuple(v) for t in ts for v in t];mesh=bpy.data.meshes.new(mat);mesh.from_pydata(vs,[],[(i,i+1,i+2) for i in range(0,len(vs),3)]);mesh.update();obj=bpy.data.objects.new(f'{mat}_{cx}_{cy}',mesh);bpy.context.collection.objects.link(obj);obj.parent=root;mesh.materials.append(m)
CV=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
for n in ast.parse((ROOT/'tools/build_models.py').read_text(encoding='utf8')).body:
 if isinstance(n,ast.FunctionDef) and n.name in {'descendants','evaluated','export_obj'}:exec(compile(ast.Module(body=[n],type_ignores=[]),'<export>','exec'),globals())
item=export_obj('landscape_understory',root);path=MODELS/item['file'];path.write_text(path.read_text(encoding='utf8').replace('mtllib palette.mtl','mtllib landscape_understory.mtl'),encoding='utf8')
mtl=[]
for mat,color in spec.items():mtl.extend(['newmtl '+mat,'Kd '+' '.join(map(str,color)),'Ks 0.015 0.015 0.015','Ns 6'])
(MODELS/'landscape_understory.mtl').write_text('\n'.join(mtl)+'\n',encoding='utf8')
report=dict(shrub_clumps=len(shrubs),bamboo_groves=len(bamboos),triangles=item['triangles'],shrubs_zup=shrubs,bamboo_zup=bamboos,terrain_fitted=True,seed=20261031)
(MODELS/'landscape_understory.json').write_text(json.dumps(report,indent=2),encoding='utf8')
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'dragonboat_realism.blend'));print('UNDERSTORY',len(shrubs),len(bamboos),item['triangles'],flush=True)

