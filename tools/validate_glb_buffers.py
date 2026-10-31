"""Validate the actual final GLB buffers without rebuilding 25k Blender nodes."""
import json,struct
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'models/dragonboat_scene.glb'
with path.open('rb') as f:
    magic,version,total=struct.unpack('<4sII',f.read(12));assert magic==b'glTF' and version==2 and total==path.stat().st_size
    size,kind=struct.unpack('<I4s',f.read(8));assert kind==b'JSON';doc=json.loads(f.read(size))
    bsize,kind=struct.unpack('<I4s',f.read(8));assert kind==b'BIN\0';start=f.tell();assert start+bsize==total
raw=np.memmap(path,mode='r',dtype=np.uint8)
types={5120:np.int8,5121:np.uint8,5122:np.dtype('<i2'),5123:np.dtype('<u2'),5125:np.dtype('<u4'),5126:np.dtype('<f4')};dims={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def accessor(i):
    a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];dt=np.dtype(types[a['componentType']]);n=dims[a['type']]
    offset=start+v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',dt.itemsize*n)
    assert offset+(a['count']-1)*stride+n*dt.itemsize<=start+v.get('byteOffset',0)+v['byteLength']
    return np.ndarray((a['count'],n),dtype=dt,buffer=raw,offset=offset,strides=(stride,dt.itemsize))
triangles=0;primitives=0;mesh_counts=[]
for mesh in doc['meshes']:
    mesh_total=0
    for p in mesh['primitives']:
        assert p.get('mode',4)==4 and 'material' in p and 0<=p['material']<len(doc['materials'])
        attributes=p['attributes'];assert all(k in attributes for k in ('POSITION','NORMAL','TEXCOORD_0')),(mesh['name'],'Missing geometry attributes')
        pos=accessor(attributes['POSITION']);normal=accessor(attributes['NORMAL']);uv=accessor(attributes['TEXCOORD_0'])
        assert len(pos)==len(normal)==len(uv) and np.isfinite(pos).all() and np.isfinite(normal).all() and np.isfinite(uv).all()
        indices=accessor(p['indices']);assert len(indices)%3==0 and indices.max()<len(pos)
        triangles+=len(indices)//3;mesh_total+=len(indices)//3;primitives+=1
    mesh_counts.append(mesh_total)
for im in doc.get('images',[]):assert 'bufferView' in im and doc['bufferViews'][im['bufferView']]['byteLength']>0
for n in doc['nodes']:
    for c in n.get('children',[]):assert 0<=c<len(doc['nodes'])
sky=[m for m in doc['materials'] if m.get('name','').startswith('panorama_sky')]
assert sky and all('KHR_materials_unlit' in m.get('extensions',{}) for m in sky)
report={'status':'PASS','file':path.name,'meshes':len(doc['meshes']),'primitives':primitives,'mesh_triangles_before_instancing':triangles,'triangles_after_node_instancing':sum(mesh_counts[n['mesh']] for n in doc['nodes'] if 'mesh' in n),'nodes':len(doc['nodes']),'embedded_images':len(doc.get('images',[])),'checks':['GLB length and chunks','all position/normal/UV buffers finite and bounded','triangle indices','material references','embedded images','node references','unlit photographic sky']}
(ROOT/'models/glb_buffer_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('GLB_BUFFER_VALIDATION_PASS',json.dumps(report))
