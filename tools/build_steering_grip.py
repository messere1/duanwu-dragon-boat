"""Keep the steering T-grip round after the runtime's axial oar scaling."""
from pathlib import Path
import math
R=Path(__file__).resolve().parents[1];lines=[];active=''
for line in (R/'models/paddle.obj').read_text(encoding='utf8').splitlines():
 if line.startswith('o '):active=line[2:].strip()
 if active=='grip' and line.startswith('v '):
  x,y,z=map(float,line.split()[1:]);line=f'v {x:.9f} {.12+(y-.12)*(.48/1.95):.9f} {z*(.48/.9):.9f}'
 elif active=='grip' and line.startswith('vn '):
  x,y,z=map(float,line.split()[1:]);y*=1.95/.48;z/=(.48/.9);n=math.sqrt(x*x+y*y+z*z);line=f'vn {x/n:.9f} {y/n:.9f} {z/n:.9f}'
 if active=='timber_shaft' and line.startswith('v '):
  x,y,z=map(float,line.split()[1:]);line=f'v {x*.65:.9f} {y:.9f} {z*.65:.9f}'
 lines.append(line)
(R/'models/steering_oar.obj').write_bytes(('\n'.join(lines)+'\n').encode())
