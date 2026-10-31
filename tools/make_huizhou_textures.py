"""Original weathered surfaces, with stains tied to wall height rather than noise alone."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter,ImageFont,ImageChops
import random,math
OUT=Path(__file__).resolve().parents[1]/'textures';N=1024
rng=random.Random(30323)
def noise(scale):
    n=Image.new('L',(scale,scale));n.putdata([rng.randrange(256) for _ in range(scale*scale)])
    return n.resize((N,N),Image.Resampling.BICUBIC)
coarse=noise(13);fine=noise(180);medium=noise(43)
for name,base in [('huizhou_plaster',(192,189,174)),('huizhou_stone',(107,111,102)),('huizhou_tiles',(49,55,52)),('huizhou_soil',(105,110,84))]:
    im=Image.new('RGB',(N,N));p=im.load();a=coarse.load();b=fine.load();c=medium.load()
    for y in range(N):
        # Image bottom is UV V=0: moisture rises unevenly from the base.
        height=1-y/(N-1)
        for x in range(N):
            n=(a[x,y]-128)*.12+(b[x,y]-128)*.035+(c[x,y]-128)*.07
            if name=='huizhou_tiles':n=(a[x,y]-128)*.025+(b[x,y]-128)*.015+(c[x,y]-128)*.02
            damp=max(0,1-height/(.17+.10*a[x,N-1]/255)) if name=='huizhou_plaster' else (max(0,1-abs(height-.41)/.22) if name=='huizhou_stone' else 0)
            wet=damp*(15+30*c[x,y]/255)
            p[x,y]=tuple(max(0,min(255,round(v+n-wet*(1.0 if i!=1 else .82)))) for i,v in enumerate(base))
    d=ImageDraw.Draw(im)
    if name=='huizhou_plaster':
        layer=Image.new('RGBA',(N,N));ld=ImageDraw.Draw(layer)
        for i in range(70):
            x=rng.randrange(N);y=rng.randrange(730,N)
            ld.line((x,y,x+rng.randrange(-4,5),y+rng.randrange(20,130)),fill=(102,111,94,rng.randrange(10,30)),width=rng.randrange(1,5))
        im=Image.alpha_composite(im.convert('RGBA'),layer.filter(ImageFilter.GaussianBlur(2))).convert('RGB')
        d=ImageDraw.Draw(im)
        for i in range(11):
            x=rng.randrange(N);y=rng.randrange(170,850);pts=[(x,y)]
            for k in range(rng.randrange(3,7)):x+=rng.randrange(-9,10);y+=rng.randrange(12,30);pts.append((x,y))
            d.line(pts,fill=(133,135,124),width=1)
    im.save(OUT/(name+'.png'))
# Irregular slabs; joints and weathered patches are asymmetric.
im=Image.new('RGB',(N,N),(65,72,58));d=ImageDraw.Draw(im)
for row in range(5):
    y=row*260-18;x=-rng.randrange(350)
    while x<N:
        w=rng.randrange(250,520);col=rng.randrange(106,145)
        pts=[(x+5,y+5),(x+w-6,y+rng.randrange(2,8)),(x+w-3,y+250),(x+rng.randrange(2,8),y+254)]
        d.polygon(pts,fill=(col,col+2,col-9));d.line(pts+[pts[0]],fill=(76,81,66),width=3);x+=w
im=Image.blend(im,noise(150).convert('RGB'),.06);im.save(OUT/'huizhou_paving.png')
for name,text in [('huizhou_shop_sign','徽州茶行'),('huizhou_inn_sign','临溪客栈')]:
    im=Image.new('RGB',(1024,256),(55,44,32));d=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/simkai.ttf',137)
    d.rectangle((12,12,1011,243),outline=(120,106,78),width=4);d.text((512,125),text,anchor='mm',font=font,fill=(186,174,139));im.save(OUT/(name+'.png'))
print('HUIZHOU_TEXTURES_READY')
