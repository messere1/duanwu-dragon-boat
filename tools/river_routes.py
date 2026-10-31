"""Original river and independent aerial route math; metres, Blender Z-up."""
import math

def smooth(t):
    t=max(0.,min(1.,t));return t*t*(3-2*t)

def old_center(x):
    return (1 if x>=0 else -1)*22*math.sin((abs(x)-85)/90+.3)*smooth((abs(x)-85)/90)

def river_center(x):
    if x<=28:return old_center(x)
    if x<100:return 28*smooth((x-28)/72)
    if x<180:return 28-38*smooth((x-100)/80)
    return -10+22*smooth((x-180)/240)

def tangent(x):
    return math.atan2(river_center(x+.02)-river_center(x-.02),.04)

def half_width(x):
    return 5.7+smooth((x-82)/40)*(1.4+.45*math.sin(x*.047))

def relief(x,y):
    # The street/building strip stays on its old foundation datum.
    lateral=abs(y-old_center(x))
    strength=smooth((lateral-21)/9)+.65*smooth((x-81)/18)*(1-smooth((lateral-21)/9))
    return strength*(.24*math.sin(x*.19+y*.13)+.13*math.sin(x*.47-y*.31)+.08*math.cos(y*.83))

def warp(x,y,z):
    d=y-old_center(x);widen=(half_width(x)-5.7)*(1-smooth((abs(d)-5.7)/8))
    return (x,y+river_center(x)-old_center(x)+(1 if d>=0 else -1)*widen,z+relief(x,y))

def bezier(cp,t):
    a=1-t
    return tuple(a*a*a*cp[0][i]+3*a*a*t*cp[1][i]+3*a*t*t*cp[2][i]+t*t*t*cp[3][i] for i in range(3))

# Design guide only. Boat Bezier control points are the river's exact cubic
# centreline; aerial position is authored separately, never parented to a boat.
BOAT_CURVES=[((-18,0,0),(-2.6666667,0,0),(12.6666667,0,0),(28,0,0)),
             ((28,0,0),(52,0,0),(76,28,0),(100,28,0))]
DRONE_CURVES=[((-31,-26,22),(-17,-31,20),(6,-24,17),(24,-18,18)),
              ((24,-18,18),(42,-12,19),(63,-5,24),(90,10,30))]

def route(curves,u):
    k=min(len(curves)-1,int(max(0,min(1,u))*len(curves)))
    return bezier(curves[k],max(0,min(1,u))*len(curves)-k)
