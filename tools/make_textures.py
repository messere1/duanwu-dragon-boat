"""Original deterministic textures, no downloaded image assets. Run with Pillow."""
from pathlib import Path
import math, random
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'textures'; OUT.mkdir(exist_ok=True)
rng=random.Random(3023209092)
for name,base in [('wood',(83,58,39)),('stone',(118,121,112)),('roof',(48,52,49)),('cloth_red',(106,33,27)),('cloth_jade',(28,63,57))]:
    im=Image.new('RGB',(512,512)); pix=im.load()
    for y in range(512):
        for x in range(512):
            if name=='wood': v=4*math.sin(y*.49+2*math.sin(x*.008))+2*math.sin(y*1.25+x*.004)+rng.uniform(-3,3)
            elif name=='stone': v=rng.uniform(-11,11)+3*math.sin(x*.09)*math.cos(y*.09)
            elif name=='roof': v=7*math.cos(x*math.pi/16)+rng.uniform(-3,3)
            else: v=3*((x%4<2)+(y%4<2)-1)+rng.uniform(-2,2)
            pix[x,y]=tuple(max(0,min(255,int(c+v))) for c in base)
    d=ImageDraw.Draw(im)
    if name=='wood':
        for y in range(0,512,64): d.line((0,y,512,y),fill=(63,36,23),width=2)
    if name=='stone':
        for y in range(0,512,128):
            d.line((0,y,512,y),fill=(103,115,113),width=3)
            for x in range((y//128%2)*128,512,256): d.line((x,y,x,y+128),fill=(103,115,113),width=3)
    # Woven fabric stays plain; painted ornament is modeled separately.
    im.save(OUT/(name+'.png')); im.save(OUT/(name+'.bmp'))
font=ImageFont.truetype('C:/Windows/Fonts/simkai.ttf',118)
for name,label in [('banner','端午竞渡'),('plaque','竞渡亭')]:
    im=Image.new('RGB',(1024,256),(77,24,19)); d=ImageDraw.Draw(im)
    d.rectangle((10,10,1013,245),outline=(158,129,77),width=5)
    d.text((512,123),label,font=font,anchor='mm',fill=(212,190,139))
    im.save(OUT/(name+'.png')); im.save(OUT/(name+'.bmp'))
print('Textures written:',OUT)
