"""Keep the emission-only background unlit in portable glTF viewers."""
def ensure_unlit_sky(path):
    import json,struct,shutil
    from pathlib import Path
    path=Path(path)
    with path.open('rb') as f:
        magic,version,total=struct.unpack('<4sII',f.read(12));length,kind=struct.unpack('<I4s',f.read(8));data=json.loads(f.read(length))
    assert magic==b'glTF' and version==2 and kind==b'JSON'
    materials=[m for m in data.get('materials',[]) if m.get('name','').startswith('panorama_sky')]
    if not materials or all('KHR_materials_unlit' in m.get('extensions',{}) for m in materials):return False
    for m in materials:
        factor=m.pop('emissiveFactor',[1,1,1]);texture=m.pop('emissiveTexture',None)
        pbr=m.setdefault('pbrMetallicRoughness',{});pbr['baseColorFactor']=factor+[1];pbr['metallicFactor']=0;pbr['roughnessFactor']=1
        if texture:pbr['baseColorTexture']=texture
        m.setdefault('extensions',{})['KHR_materials_unlit']={}
    used=data.setdefault('extensionsUsed',[])
    if 'KHR_materials_unlit' not in used:used.append('KHR_materials_unlit')
    payload=json.dumps(data,ensure_ascii=False,separators=(',',':')).encode('utf-8');payload+=b' '*((-len(payload))%4)
    pending=path.with_suffix('.sky-fixed.glb')
    with path.open('rb') as f,pending.open('wb') as out:
        f.seek(20+length);out.write(struct.pack('<4sII',magic,version,total-length+len(payload)));out.write(struct.pack('<I4s',len(payload),b'JSON'));out.write(payload);shutil.copyfileobj(f,out,1024*1024)
    pending.replace(path);print('GLB_SKY_UNLIT_PASS',flush=True);return True
