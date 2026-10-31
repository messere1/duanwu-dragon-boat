import bpy,json
from pathlib import Path
r=Path.cwd()
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(r/'external_assets/prepared_open_assets.blend'),link=False) as (s,d):d.objects=[n for n in s.objects if n.startswith('open_tree__')]
for o in d.objects:
 o.data.calc_loop_triangles();counts={}
 for t in o.data.loop_triangles:counts[t.material_index]=counts.get(t.material_index,0)+1
 print('PART',o.name,'matrix',list(o.matrix_world.translation),'counts',counts)
 for i,m in enumerate(o.data.materials):
  print('MAT',i,m.name)
  bs=m.node_tree.nodes.get('Principled BSDF')
  for tag in ['Base Color','Alpha']:
   print(tag,[(l.from_node.name,l.from_socket.name) for l in bs.inputs[tag].links])
  for n in m.node_tree.nodes:
   if n.type=='TEX_IMAGE':
    print('IMAGE',n.name,n.image.name,n.image.colorspace_settings.name,n.image.channels,n.image.alpha_mode)
    if 'leaves_diff' in n.image.name:
     import numpy as np
     a=np.array(n.image.pixels[:],dtype='f4').reshape(-1,4);print('ALPHA',a[:,3].min(),a[:,3].max(),a[:,:3].mean(0))
