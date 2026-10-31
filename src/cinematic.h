#pragma once
#include "math_scene.h"

// Independent timed spatial spline. Hermite endpoints are converted to cubic
// Bezier control points; shared endpoint velocities keep the flight C1 smooth.
struct CameraKey {double time;Vec3 eyeZup;double fov;};
struct CameraFlight {
    std::array<CameraKey,7> keys{{{0,{-30,-19,19},55},{4,{-11,-11,14},50},{6,{-5,0,3.2},50},{10,{13,0,3.2},50},{17,{57,1,16},48},{22,{80,4,25},54},{26,{72,-24,32},54}}};
    Vec3 velocity(int i)const{if(i==0||i==6)return {};int a=std::max(0,i-1),b=std::min(6,i+1);Vec3 v=(keys[b].eyeZup-keys[a].eyeZup)*(1/(keys[b].time-keys[a].time));if(i==2||i==3){v.y=0;v.z=0;}return v;}
    int segment(double t)const{int i=0;while(i<5&&t>keys[i+1].time)++i;return i;}
    Vec3 at(double t)const{t=std::clamp(t,0.0,26.0);int i=segment(t);double dt=keys[i+1].time-keys[i].time,u=(t-keys[i].time)/dt,a=1-u;Vec3 p=keys[i].eyeZup,q=p+velocity(i)*(dt/3),s=keys[i+1].eyeZup,r=s-velocity(i+1)*(dt/3);return p*(a*a*a)+q*(3*a*a*u)+r*(3*a*u*u)+s*(u*u*u);}
    double fov(double t)const{t=std::clamp(t,0.0,26.0);int i=segment(t);double u=(t-keys[i].time)/(keys[i+1].time-keys[i].time);u=u*u*(3-2*u);return keys[i].fov*(1-u)+keys[i+1].fov*u;}
    const char* stage(double t)const{return t<4?"SHOT 1 | Village and race start":t<10?"SHOT 2 | Approach the competing crews":t<17?"SHOT 3 | Side tracking and middle-race surge":t<22?"SHOT 4 | Rise above the river bend":"SHOT 5 | Final sprint and wide aerial finish";}
};
struct FlagOffset {double vertical=0,lateral=0;};
// The stored flag mesh extends along +X. Rotate it about its pole into the
// apparent wind: -X in boat space. A rotation preserves winding and normals.
inline std::array<double,16> flagOrientation(){return {{-1,0,0,0, 0,1,0,0, 0,0,-1,0, -8.9,0,-.36,1}};}
inline FlagOffset flagOffset(double u,double height,double time,double speed,int team){u=std::clamp(u,0.0,1.0);double phase=9*u+3*(height-2.46)-time*(4+.4*speed)+team*.9;return {.012*u*u*sin(phase*.8),(.035+.012*speed)*u*u*(.7*sin(phase)+.3*sin(1.9*phase+.5))};}
