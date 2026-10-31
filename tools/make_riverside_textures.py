"""Original repeatable bitmap surfaces and a handwritten-style stall sign."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import random,math
OUT=Path(__file__).resolve().parents[1]/'textures'
rng=random.Random(3023209092)
for name,base in [('limewash',(177,173,155)),('cut_limestone',(139,143,132)),('canvas',(186,169,126)),('paving',(137,133,118))]:
    im=Image.new('RGB',(512,512));p=im.load()
    for y in range(512):
        for x in range(512):
            grain=rng.uniform(-4,4)
            if name=='limewash':grain+=2.5*math.sin(x*.07)*math.sin(y*.031)+1.5*math.sin(y*.19)
            if name=='canvas':grain+=2*((x%3==0)+(y%3==0)-.66)
            p[x,y]=tuple(max(0,min(255,round(c+grain))) for c in base)
    d=ImageDraw.Draw(im)
    if name=='paving':
        for j in range(4):
            y=j*128;d.line((0,y,511,y),fill=(97,98,87),width=4)
            for x in range(-128+(j%2)*128,600,256):d.line((x,y,x,y+128),fill=(103,103,91),width=4)
    im.save(OUT/(name+'.png'))
im=Image.new('RGB',(1024,256),(81,42,26));d=ImageDraw.Draw(im)
d.rectangle((12,12,1011,243),outline=(158,132,86),width=4)
font=ImageFont.truetype('C:/Windows/Fonts/simkai.ttf',130)
d.text((512,127),'粽香茶铺',anchor='mm',font=font,fill=(222,207,166))
im.save(OUT/'stall_sign.png')
print('RIVERSIDE_TEXTURES_READY')
