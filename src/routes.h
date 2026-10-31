#pragma once
#include "math_scene.h"
struct CurvePath {
    std::array<std::array<Vec3,4>,2> control;
    std::vector<Vec3> points;std::vector<double> distances;
    Vec3 evaluate(double t)const{t=std::clamp(t,0.0,1.0)*2;int k=std::min(1,int(t));t-=k;double a=1-t;auto p=control[k];return p[0]*(a*a*a)+p[1]*(3*a*a*t)+p[2]*(3*a*t*t)+p[3]*(t*t*t);}
    void build(){points.clear();distances.clear();double lengthSum=0;for(int i=0;i<=2000;++i){Vec3 p=evaluate(i/2000.0);if(i)lengthSum+=length(p-points.back());points.push_back(p);distances.push_back(lengthSum);}}
    Vec3 at(double t)const{double d=std::clamp(t,0.0,1.0)*distances.back();size_t i=std::lower_bound(distances.begin(),distances.end(),d)-distances.begin();i=std::clamp(i,size_t(1),points.size()-1);double f=(d-distances[i-1])/(distances[i]-distances[i-1]);return points[i-1]*(1-f)+points[i]*f;}
    Vec3 direction(double t)const{return unit(at(std::min(1.0,t+.001))-at(std::max(0.0,t-.001)));}
};
inline CurvePath boatPath(){CurvePath p;p.control={{{{{-18,0,0},{-2.6666667,0,0},{12.6666667,0,0},{28,0,0}}},{{{28,0,0},{52,0,0},{76,28,0},{100,28,0}}}}};p.build();return p;}
inline CurvePath dronePath(){CurvePath p;p.control={{{{{-31,-26,22},{-17,-31,20},{6,-24,17},{24,-18,18}}},{{{24,-18,18},{42,-12,19},{63,-5,24},{90,10,30}}}}};p.build();return p;}
inline Vec3 fromZup(Vec3 p){return {p.x,p.z,-p.y};}
