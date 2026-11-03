#pragma once
#include "routes.h"

// The speed envelopes are an authored 26 s demonstration, not measured race data.
// Integrating speed gives continuous distance; a change of pace cannot teleport a boat.
struct RaceSample {double distance=0,speed=0,cycles=0,rate=0;};
inline double smooth01(double x){x=std::clamp(x,0.0,1.0);return x*x*(3-2*x);}
inline double raceSpeed(int team,double t){
    double start=1-exp(-std::max(0.0,t)/(team?.95:.72));
    double surge=team?(1.03*exp(-pow((t-11)/3.4,2))+.36*smooth01((t-19)/3)):(.30*exp(-pow((t-5)/3.0,2))+.64*smooth01((t-21)/3));
    return start*(4.72+surge+(team?-.12:.02))*(1+.013*sin(t*1.1+(team?1.3:0)));
}
inline double strokeRate(int team,double t){return .80+.13*(1-exp(-t/2))+.10*exp(-pow((t-5)/3,2))+.10*smooth01((t-(team?19:21))/3)+(team?.025+.10*exp(-pow((t-11)/3.4,2)):0);}
class RaceMotion {
    std::array<std::vector<RaceSample>,2> table;
public:
    RaceMotion(){for(int team=0;team<2;++team){auto& v=table[team];v.resize(2601);for(int i=0;i<=2600;++i){double t=i*.01;v[i].speed=raceSpeed(team,t);v[i].rate=strokeRate(team,t);if(i){v[i].distance=v[i-1].distance+.005*(v[i-1].speed+v[i].speed);v[i].cycles=v[i-1].cycles+.005*(v[i-1].rate+v[i].rate);}}}}
    RaceSample at(int team,double t)const{double u=std::clamp(t,0.0,26.0)*100;int i=std::min(2599,int(u));double f=u-i;auto a=table[team][i],b=table[team][i+1];return {a.distance*(1-f)+b.distance*f,a.speed*(1-f)+b.speed*f,a.cycles*(1-f)+b.cycles*f,a.rate*(1-f)+b.rate*f};}
};
struct PaddlePose {double angle=0,lift=0,reach=0,feather=0;};
inline PaddlePose paddlePose(double phase){
    static const double k[][5]={{0,24,-.13,.10,0},{.10,22,-.22,.06,0},{.50,-20,-.20,-.10,1},{.64,-25,.10,-.10,17},{.83,3,.14,.03,18},{1,24,-.13,.10,0}};
    phase-=floor(phase);for(int i=1;i<6;++i)if(phase<=k[i][0]){double f=smooth01((phase-k[i-1][0])/(k[i][0]-k[i-1][0]));return {k[i-1][1]*(1-f)+k[i][1]*f,k[i-1][2]*(1-f)+k[i][2]*f,k[i-1][3]*(1-f)+k[i][3]*f,k[i-1][4]*(1-f)+k[i][4]*f};}return {};
}
inline Vec3 paddlePoint(int row,int side,double shaftZ,double phase){auto p=paddlePose(phase);double a=p.angle*3.141592653589793/180,tilt=.4+p.feather*3.141592653589793/180,d=cos(tilt)*shaftZ;return {-3+1.1*row+.42+p.reach-sin(a)*d,1.51+p.lift+cos(a)*d,-side*(.66-sin(tilt)*shaftZ)};}
inline int motionForGroup(const std::string& s){
    if(s.find("_helmsman__")!=s.npos)return -3;
    if(s.find("_steering_oar__")!=s.npos)return -4;
    if(s.find("_pennant__flag_cloth")!=s.npos)return 30;
    if(s.find("_drummer__")!=s.npos)return -2;
    if(s.find("_drumstick")!=s.npos)return s.find(".001")!=s.npos?21:20;
    if(s.find("_rower_")!=s.npos)return -1;
    size_t p=s.find("_paddle_");if(p==s.npos)return 0;int row=0,side=0;if(sscanf(s.c_str()+p+8,"%d_%d",&row,&side)==2&&row>=0&&row<6&&(side==1||side==-1))return 1+row*2+(side>0?1:0);return 0;
}
struct DrumPose {double angle=0,lift=0;};
inline DrumPose drumPose(double cycles,int side){
    static const double k[][3]={{0,28,.04},{.05,0,0},{.10,20,.035},{.32,58,.11},{.65,54,.10},{.88,48,.08},{1,28,.04}};
    double phase=cycles*.5+(side<0?.5:0);phase-=floor(phase);
    for(int i=1;i<7;++i)if(phase<=k[i][0]){double f=smooth01((phase-k[i-1][0])/(k[i][0]-k[i-1][0]));return {k[i-1][1]*(1-f)+k[i][1]*f,k[i-1][2]*(1-f)+k[i][2]*f};}return {};
}
inline Vec3 drumGrip(double cycles,int side){auto p=drumPose(cycles,side);return {3.89+p.lift,1.77+p.lift,-side*.22};}
inline Vec3 drumTip(double cycles,int side){auto p=drumPose(cycles,side);double a=-p.angle*3.141592653589793/180;return drumGrip(cycles,side)+Vec3{-.54*cos(a)+.10*sin(a),-.54*sin(a)-.10*cos(a),side*.10};}
