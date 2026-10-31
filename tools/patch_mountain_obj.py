"""Replace terrain object blocks without re-exporting the animation or boats.
Positive OBJ indices are rebased with independently counted v/vt/vn streams.
The pinned source remains intact; the output is atomically replaced at the end.
"""
from pathlib import Path
import json,hashlib,os
R=Path(__file__).resolve().parents[1];M=R/'models';B=R.parent/'_work/dragonboat/before_mountain_refinement'
def patch():
 manifest=json.loads((M/'mountain_patch_manifest.json').read_text());replaced=set(manifest['terrain_objects']);shifts=manifest['rigid_vertical_shifts']
 source=Path(manifest['baseline_scene_obj']);pending=M/'scene_preview.obj.pending';old=[0,0,0];removed=[0,0,0];written=[0,0,0];group_start=[0,0,0];group='';discard=False;triangles=0;removed_triangles=0;found=set();shifted=set();shifted_vertices=0
 tags={'v':0,'vt':1,'vn':2}
 with source.open(encoding='utf8') as src,pending.open('w',encoding='utf8',newline='\n') as dst:
  for line in src:
   if line.startswith('o '):
    group=line[2:].strip();group_start=old.copy();discard=group in replaced
    if discard:found.add(group)
    else:dst.write(line)
    continue
   tag=line.split(' ',1)[0]
   if tag in tags:
    k=tags[tag];old[k]+=1
    if discard:removed[k]+=1;continue
    written[k]+=1
    if tag=='v' and group in shifts:
     x,y,z=map(float,line.split()[1:]);line=f'v {x:.6f} {y+shifts[group]:.6f} {z:.6f}\n';shifted.add(group);shifted_vertices+=1
    dst.write(line);continue
   if line.startswith('f '):
    refs=[token.split('/') for token in line.split()[1:]]
    if discard:removed_triangles+=len(refs)-2;continue
    out=[]
    for token in refs:
     values=[]
     for k,s in enumerate(token):
      if not s:values.append('');continue
      i=int(s);assert group_start[k]<i<=old[k],('Cross-object/invalid OBJ reference',group,token,group_start,old)
      values.append(str(i-removed[k]))
     out.append('/'.join(values))
    dst.write('f '+' '.join(out)+'\n');triangles+=len(refs)-2
   elif not discard:dst.write(line)
  assert found==replaced,('Missing baseline terrain objects',replaced-found)
  assert shifted==set(shifts),('Unmatched rigid tree meshes',set(shifts)-shifted)
  offset=written.copy();new_component_triangles=0
  for line in (M/'mountain_refined.obj').open(encoding='utf8'):
   tag=line.split(' ',1)[0]
   if tag in tags:written[tags[tag]]+=1
   if line.startswith(('mtllib ','#')):continue
   if line.startswith('f '):
    refs=[token.split('/') for token in line.split()[1:]];line='f '+' '.join('/'.join(str(int(s)+offset[k]) if s else '' for k,s in enumerate(token)) for token in refs)+'\n';triangles+=len(refs)-2;new_component_triangles+=len(refs)-2
   dst.write(line)
  dst.flush();os.fsync(dst.fileno())
 assert written[0]==written[1]==written[2]
 assert new_component_triangles==manifest['new_component']['triangles']
 inventory=json.loads((B/'inventory.json').read_text());base=next(i for i in inventory if i['file']=='scene_preview.obj')
 assert triangles==base['triangles']-removed_triangles+new_component_triangles
 base['triangles']=triangles;base['vertices']=written[0];inventory=[i for i in inventory if i['file']!='mountain_refined.obj'];inventory.append(manifest['new_component'])
 report=dict(status='PASS',objects_replaced=len(found),old_vertices=old,new_vertices=written,terrain_triangles_removed=removed_triangles,terrain_triangles_added=new_component_triangles,scene_triangles=triangles,rigid_tree_meshes_shifted=len(shifted),rigid_tree_vertices_shifted=shifted_vertices,source_sha256=hashlib.file_digest(source.open('rb'),'sha256').hexdigest())
 pending.replace(M/'scene_preview.obj');(M/'inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf8');(R/'results/mountain_obj_patch.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
if __name__=='__main__':patch()
