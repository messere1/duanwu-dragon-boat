"""Read selected CC0 MakeHuman assets from the official ZIP using HTTP ranges."""
import urllib.request,io,zipfile,json,hashlib
from pathlib import Path
URL='https://files.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip'
OUT=Path(__file__).resolve().parents[2]/'_work/dragonboat/makehuman_selected'
class RemoteFile(io.RawIOBase):
    def __init__(self,url):
        self.url=url;self.pos=0
        q=urllib.request.Request(url,method='HEAD');r=urllib.request.urlopen(q,timeout=30)
        self.size=int(r.headers['Content-Length']);self.cache={}
    def seekable(self):return True
    def seek(self,n,w=0):self.pos=n if w==0 else (self.pos+n if w==1 else self.size+n);return self.pos
    def tell(self):return self.pos
    def read(self,n=-1):
        n=min(n if n>=0 else self.size-self.pos,self.size-self.pos)
        if n<=0:return b''
        a=self.pos;b=a+n-1
        q=urllib.request.Request(self.url,headers={'Range':f'bytes={a}-{b}'})
        with urllib.request.urlopen(q,timeout=90) as r:
            assert r.status==206,'Server does not support range requests'
            data=r.read()
        self.pos+=len(data);return data
OUT.mkdir(parents=True,exist_ok=True)
z=zipfile.ZipFile(RemoteFile(URL));names=z.namelist()
(OUT/'archive_index.json').write_text(json.dumps(names,indent=2))
print('REMOTE_INDEX',len(names),flush=True)
want=['middleage_asian_male','short01','low-poly','male_casualsuit04','shoes02','eyebrow001']
for n in names:
    if not n.endswith('/') and (any('/'+w+'/' in '/'+n for w in want) or n.startswith('eyes/materials/') or n.startswith('eyes/textures/')):
        p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists():p.write_bytes(z.read(n))
        print('HUMAN_FILE',n,p.stat().st_size,flush=True)
print('SELECTED_HUMAN_READY',flush=True)
