"""Create a modeling-stage handoff, with checksums and no tool installation files."""
from pathlib import Path
import hashlib,json,zipfile,sys
ROOT=Path(__file__).resolve().parents[1]
excluded={'.git','__pycache__','cache','intermediate','.vs','CMakeFiles','tests_fixture'}
files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.suffix not in ('.blend1','.pyc') and not excluded.intersection(p.parts) and p.name!='checksums.sha256')
checks=[]
for p in files:checks.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix())
checksum=ROOT/'checksums.sha256';checksum.write_text('\n'.join(checks)+'\n',encoding='utf-8');files.append(checksum)
out=ROOT.parent/'端午龙舟_建模阶段.zip'
pending=out.with_suffix('.pending.zip')
with zipfile.ZipFile(pending,'w',zipfile.ZIP_DEFLATED,compresslevel=1 if '--fast' in sys.argv else 6) as z:
    for p in files:z.write(p,Path('Project')/p.relative_to(ROOT))
with zipfile.ZipFile(pending) as z:assert z.testzip() is None
pending.replace(out)
print(json.dumps({'zip':str(out),'files':len(files),'size_mb':round(out.stat().st_size/1024**2,2)},ensure_ascii=False))
