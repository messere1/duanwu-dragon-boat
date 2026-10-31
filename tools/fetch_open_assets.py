"""Fetch openly licensed source assets; preserve attribution, URLs and checksums."""
from pathlib import Path
import urllib.request,json,gzip,hashlib,concurrent.futures
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'external_assets';OUT.mkdir(exist_ok=True)
UA={'User-Agent':'DragonBoatCourseProject/1.0 (educational asset integration)'}
def get(url):return urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=120).read()
jobs=[];manifest=[]
def add_file(url,path,md5=None):jobs.append((url,path,md5))
for asset in ['tree_small_02','rock_moss_set_01','wood_planks_grey','stone_brick_wall_001','kloofendal_48d_partly_cloudy']:
    folder=OUT/asset;folder.mkdir(exist_ok=True)
    files=json.loads(get('https://api.polyhaven.com/files/'+asset));info=json.loads(get('https://api.polyhaven.com/info/'+asset))
    (folder/'api_files.json').write_text(json.dumps(files,indent=2));(folder/'source.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    if asset in ['tree_small_02','rock_moss_set_01']:
        entry=files['gltf']['1k']['gltf'];add_file(entry['url'],folder/(asset+'_1k.gltf'),entry['md5'])
        for path,entry in entry['include'].items():add_file(entry['url'],folder/path,entry['md5'])
    elif 'hdri' in files:
        e=files['hdri']['1k']['hdr'];add_file(e['url'],folder/(asset+'_1k.hdr'),e['md5'])
    else:
        for channel in ('Diffuse','nor_gl','Rough'):
            variants=files[channel]['2k'];fmt='jpg' if 'jpg' in variants else 'png';e=variants[fmt]
            add_file(e['url'],folder/(asset+'_'+channel+'.'+fmt),e['md5'])
    manifest.append({'id':asset,'source':'https://polyhaven.com/a/'+asset,'author':info.get('authors'),'license':'CC0-1.0','license_url':'https://polyhaven.com/license'})
uid='217d9a108f12485088dcaf49b11d9ac0'
folder=OUT/'chinese_dragon_head';folder.mkdir(exist_ok=True)
meta=json.loads(get('https://api.sketchfab.com/v3/models/'+uid));assert meta['license']['slug']=='by'
(folder/'source.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
mapping=json.loads(gzip.decompress(get('https://huggingface.co/datasets/allenai/objaverse/resolve/main/object-paths.json.gz')))
add_file('https://huggingface.co/datasets/allenai/objaverse/resolve/main/'+mapping[uid],folder/'chinese_dragon_head.glb')
manifest.append({'id':'chinese_dragon_head','name':meta['name'],'author':meta['user']['displayName'],'source':meta['viewerUrl'],'license':'CC-BY-4.0','license_url':meta['license']['url'],'download_via':'AllenAI Objaverse public release','modifications':'Scaled, reoriented, decimated if necessary and attached to boat; material variants derived from source textures.'})
def download(job):
    url,path,md5=job;path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and (not md5 or hashlib.md5(path.read_bytes()).hexdigest()==md5):return path
    data=get(url)
    if md5:assert hashlib.md5(data).hexdigest()==md5,(path,'checksum mismatch')
    path.write_bytes(data);print('FETCHED',path.name,len(data),flush=True);return path
with concurrent.futures.ThreadPoolExecutor(6) as pool:list(pool.map(download,jobs))
for item in manifest:
    folder=OUT/item['id'];item['files']=[{'path':str(p.relative_to(OUT)).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in folder.rglob('*') if p.is_file()]
if (OUT/'manifest.json').exists():
    previous=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    manifest.extend(x for x in previous if x['id'] not in {x['id'] for x in manifest})
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('OPEN_ASSETS_READY',len(manifest),flush=True)
