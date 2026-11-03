#pragma once
#include "math_scene.h"

// Boat-space Y-up frame. The blade trails aft and outboard of the stern.
struct SteeringFrame {Vec3 upper,lower,axis;std::array<double,16> matrix;};
inline SteeringFrame steeringFrame(double phase){
 double a=phase*6.283185307179586;Vec3 upper{-3.68+.035*sin(a),2.21+.025*cos(a),.42+.055*sin(a)};
 Vec3 y=unit({.68+.018*cos(2*a),.69+.018*sin(a),-.12+.025*sin(a)}),x=unit(cross(y,{0,0,1})),z=cross(x,y),origin=upper-y*(.12*1.95);
 return {upper,upper-y*(.22*1.95),y,{{x.x*.90,x.y*.90,x.z*.90,0,y.x*1.95,y.y*1.95,y.z*1.95,0,z.x*.90,z.y*.90,z.z*.90,0,origin.x,origin.y,origin.z,1}}};
}
inline double steeringPhase(double time,int team){return time/4.2+team*.21;}
