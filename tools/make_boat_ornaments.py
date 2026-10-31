"""Original painted scales, cloud borders and lotus roundels, generated as UV decals."""
from pathlib import Path
from PIL import Image,ImageDraw
import random,math
R=Path(__file__).resolve().parents[1];rng=random.Random(42)
for team,col in [('red',(145,37,25)),('jade',(22,90,72))]:
    im=Image.new('RGB',(4096,160));p=im.load()
    for y in range(160):
        for x in range(4096):
            n=rng.uniform(-5,5)+2*math.sin(x*.12+y*.034)
            p[x,y]=tuple(max(0,min(255,int(c+n))) for c in col)
    d=ImageDraw.Draw(im);gold=(185,143,67);light=(214,179,104);dark=(45,24,14)
    for y in (5,11,149,155):d.line((0,y,4096,y),fill=gold,width=2)
    # Small, flush painted scales; the entire image spans the boat's side.
    for row in range(4):
        yy=12+row*34
        for j in range(-1,60):
            xx=j*70+(row%2)*35
            d.arc((xx,yy,xx+70,yy+54),0,180,fill=gold,width=1)
    for cx in (500,2048,3596):
        cy=80;d.ellipse((cx-60,cy-60,cx+60,cy+60),fill=col,outline=gold,width=3)
        for j in range(10):
            a=j*math.tau/10;tip=(cx+47*math.cos(a),cy+47*math.sin(a))
            left=(cx+26*math.cos(a-.35),cy+26*math.sin(a-.35));right=(cx+26*math.cos(a+.35),cy+26*math.sin(a+.35))
            d.line([left,tip,right,(cx,cy),left],fill=light,width=2)
        d.ellipse((cx-10,cy-10,cx+10,cy+10),outline=light,width=2)
    im.save(R/'textures'/('boat_painted_'+team+'.png'))
print('Painted boat textures ready')
