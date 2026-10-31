#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#if defined(__GNUC__) && !defined(__clang__) && __GNUC__ < 8
#include <experimental/filesystem>
namespace fs = std::experimental::filesystem;
#else
#include <filesystem>
namespace fs = std::filesystem;
#endif
#include <cstdio>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

struct Vec3 {
    double x=0,y=0,z=0;
    Vec3 operator+(Vec3 b) const {return {x+b.x,y+b.y,z+b.z};}
    Vec3 operator-(Vec3 b) const {return {x-b.x,y-b.y,z-b.z};}
    Vec3 operator*(double s) const {return {x*s,y*s,z*s};}
};
inline double dot(Vec3 a,Vec3 b){return a.x*b.x+a.y*b.y+a.z*b.z;}
inline Vec3 cross(Vec3 a,Vec3 b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
inline double length(Vec3 a){return std::sqrt(dot(a,a));}
inline Vec3 unit(Vec3 a){double n=length(a); return n>1e-12?a*(1/n):Vec3{0,1,0};}
struct Vec2 {double u=0,v=0;};
struct Scene {
    Vec3 translation{},rotation{},eye{2.7,1.6,4.4};double scale=1,yaw=-121.5,pitch=-17;
    Vec3 front() const {double y=yaw*3.141592653589793/180,p=pitch*3.141592653589793/180;return unit({cos(y)*cos(p),sin(p),sin(y)*cos(p)});}
    Vec3 right() const {return unit(cross(front(),{0,1,0}));}
    Vec3 up() const {return unit(cross(right(),front()));}
    void look(double dx,double dy){yaw+=dx*.18;pitch=std::clamp(pitch-dy*.18,-85.0,85.0);}
    void pan(double dx,double dy){eye=eye+right()*(-dx*.006)+up()*(dy*.006);}
};
