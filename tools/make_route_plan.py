"""Generate an inspectable animation plan; does not claim rendered animation."""
import json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from river_routes import *

def lut(curves,n=1000):
    pts=[route(curves,i/n) for i in range(n+1)];s=[0.]
    for a,b in zip(pts,pts[1:]):s.append(s[-1]+math.dist(a,b))
    return pts,s

TABLES={id(curves):lut(curves) for curves in (BOAT_CURVES,DRONE_CURVES)}

def by_distance(curves,f):
    import bisect
    pts,s=TABLES[id(curves)];d=max(0,min(1,f))*s[-1];i=max(1,min(len(s)-1,bisect.bisect_left(s,d)))
    t=(d-s[i-1])/(s[i]-s[i-1]);return tuple(a+(b-a)*t for a,b in zip(pts[i-1],pts[i]))

frames=[]
for i in range(625):
    t=i/24;u=min(1,t/26);b=by_distance(BOAT_CURVES,u);c=by_distance(DRONE_CURVES,u)
    target=by_distance(BOAT_CURVES,min(1,u+.025))
    frames.append({'time':round(t,6),'boat_center_zup':b,'camera_zup':c,'look_at_zup':[target[0],target[1],1.15]})
plan={'status':'camera and boat path design; not the final OpenGL animation','duration_seconds':26,'fps':24,'axes':'Z-up metres; convert (x,y,z) to OpenGL (x,z,-y)','boat_lane_offsets':[-1.8,1.8],'boat_cubic_bezier':BOAT_CURVES,'camera_cubic_bezier':DRONE_CURVES,'parameterization':'Independent arc-length tables. Look at boat centre 0.65 seconds ahead; world up remains Z.','samples':frames}
(ROOT/'models/animation_route_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')

def point(x,y):return (80+(x+40)*7,400-y*5)
def poly(points):return ' '.join(f'{point(p[0],p[1])[0]:.2f},{point(p[0],p[1])[1]:.2f}' for p in points)
river=[(x,river_center(x),0) for x in range(-30,121)]
boat=[route(BOAT_CURVES,i/200) for i in range(201)];drone=[route(DRONE_CURVES,i/200) for i in range(201)]
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="650" viewBox="0 0 1280 650">','<rect width="1280" height="650" fill="#f5f2e9"/>','<g font-family="Microsoft YaHei, sans-serif">','<text x="40" y="45" font-size="26" fill="#243833">26 秒航线规划：龙舟与无人机分别走曲线</text>','<text x="40" y="78" font-size="16" fill="#596960">俯视示意 · 橙色为龙舟中心线，蓝色为相机飞行路线；虚线连接同一时刻</text>',f'<polyline points="{poly(river)}" fill="none" stroke="#8db7ad" stroke-width="58" stroke-linecap="round"/>',f'<polyline points="{poly(boat)}" fill="none" stroke="#b65d35" stroke-width="4"/>',f'<polyline points="{poly(drone)}" fill="none" stroke="#41688b" stroke-width="4"/>']
for t in [0,6.5,13,19.5,26]:
    b=by_distance(BOAT_CURVES,t/26);c=by_distance(DRONE_CURVES,t/26);bx,by=point(*b[:2]);cx,cy=point(*c[:2])
    svg.extend([f'<path d="M{bx},{by} L{cx},{cy}" stroke="#819287" stroke-dasharray="5 5"/>',f'<circle cx="{bx}" cy="{by}" r="6" fill="#b65d35"/>',f'<circle cx="{cx}" cy="{cy}" r="6" fill="#41688b"/>',f'<text x="{cx-10}" y="{cy+24}" font-size="14">{t:g}s · 高 {c[2]:.1f}m</text>'])
svg.extend(['<text x="40" y="610" font-size="16" fill="#596960">位置按各自弧长采样；镜头持续看向龙舟前方，独立升降、侧移和拉远。此图为方案，非成片。</text>','</g></svg>'])
(ROOT/'previews/24_drone_route_plan.svg').write_text('\n'.join(svg),encoding='utf-8')
print('ROUTE_PLAN_READY',len(frames))
