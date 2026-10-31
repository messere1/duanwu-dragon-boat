"""Drop faces that collapse after six-decimal OBJ coordinate quantization."""
from pathlib import Path
from array import array
import json,sys
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'models'/(sys.argv[1] if len(sys.argv)>1 else 'scene_preview.obj')
tmp=path.with_suffix('.repair.tmp');v=array('d');normals=array('d');removed=0;faces=0;reversed_faces=0
with path.open(encoding='utf-8') as src,tmp.open('w',encoding='utf-8',newline='\n') as out:
    for line in src:
        if line.startswith('v '):v.extend(map(float,line.split()[1:]))
        elif line.startswith('vn '):normals.extend(map(float,line.split()[1:]))
        elif line.startswith('f '):
            ids=[(int(t.split('/',1)[0])-1)*3 for t in line.split()[1:]]
            i,j,k=ids
            ax=v[j]-v[i];ay=v[j+1]-v[i+1];az=v[j+2]-v[i+2]
            bx=v[k]-v[i];by=v[k+1]-v[i+1];bz=v[k+2]-v[i+2]
            cx=ay*bz-az*by;cy=az*bx-ax*bz;cz=ax*by-ay*bx
            if cx*cx+cy*cy+cz*cz<=1e-18:
                removed+=1;continue
            tokens=line.split()[1:];ni=(int(tokens[0].split('/')[2])-1)*3
            alignment=(cx*normals[ni]+cy*normals[ni+1]+cz*normals[ni+2])/(cx*cx+cy*cy+cz*cz)**.5
            if alignment<-.01:
                if cx*cx+cy*cy+cz*cz<1e-12:removed+=1;continue
                tokens[1],tokens[2]=tokens[2],tokens[1];line='f '+' '.join(tokens)+'\n';reversed_faces+=1
            faces+=1
        out.write(line)
tmp.replace(path)
p=ROOT/'models/inventory.json';inventory=json.loads(p.read_text())
for item in inventory:
    if item['file']==path.name:item['triangles']=faces
p.write_text(json.dumps(inventory,indent=2),encoding='utf-8')
print('QUANTIZED_DEGENERATES_REMOVED',removed,'TRIANGLES',faces,'WINDING_REPAIRS',reversed_faces)
