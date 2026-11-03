"""Shared steering-oar path in boat Y-up coordinates, used by Blender authoring."""
import math

def steering_frame(phase):
 a=phase*math.tau
 grip=(-3.68+.035*math.sin(a),2.21+.025*math.cos(a),.42+.055*math.sin(a))
 d=(.68+.018*math.cos(2*a),.69+.018*math.sin(a),-.12+.025*math.sin(a))
 n=math.sqrt(sum(v*v for v in d));d=tuple(v/n for v in d)
 # Native paddle grip is at y=.12; lower hand grasps the shaft at y=-.10.
 lower=tuple(grip[i]-d[i]*(.22*1.95) for i in range(3))
 return grip,lower,d
