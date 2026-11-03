#define NOMINMAX
#include <windows.h>
#include "assets.h"
#include "routes.h"
#include "cinematic.h"
#include "steering.h"
#include <iostream>
void require(bool ok,const char* what){if(!ok)throw std::runtime_error(what);}
void write(const fs::path& p,const std::string& s){FILE* f=_wfopen(p.c_str(),L"wb");if(!f)throw std::runtime_error("Cannot write test fixture");fwrite(s.data(),1,s.size(),f);fclose(f);}
int main(){try{
 wchar_t exe[32768];GetModuleFileNameW(nullptr,exe,32768);auto root=fs::path(exe).parent_path().parent_path()/L"results/tests_fixture";fs::create_directories(root/L"models");
 auto obj=root/L"models/scene_preview.obj",mtl=root/L"models/palette.mtl";
 write(mtl,"newmtl stone\nKd 0.2 0.3 0.4\nNs 20\n");auto mats=readMTL(mtl);require(mats.size()==2&&std::abs(mats[1].color.y-.3)<1e-8,"MTL material parameters");
 write(obj,"o floor\nv 100 0 0\nv 104 0 0\nv 104 0 4\nv 100 0 4\nvt 0 0\nvt 1 0\nvt 1 1\nvt 0 1\nvn 0 1 0\nusemtl stone\nf -4/1/1 -3/2/1 -2/3/1 -1/4/1\n");
 auto a=readSceneOBJ(obj,mats);require(a.triangles==2&&a.batches[0].indices.size()==6,"Negative indices and quad triangulation");require(a.vertices[0].p[0]==100,"Scene coordinates must not be normalized");require(a.vertices[2].uv[0]==1&&a.batches[0].material==1,"UV and multi-material references");
 bool hit=false;loadScene(root,mats,hit);loadScene(root,mats,hit);require(hit,"Binary scene cache reuse");
 write(obj,"v 101 0 0\nv 104 0 0\nv 100 0 4\nf 1 2 3\n");loadScene(root,mats,hit);require(!hit,"Source changes invalidate cache");
 write(obj,"v 0 0 0\nf 1 2 3\n");bool rejected=false;try{readSceneOBJ(obj,mats);}catch(const std::exception&){rejected=true;}require(rejected,"Invalid OBJ indices rejected");
 auto b=boatPath(),d=dronePath();require(length(b.at(0)-Vec3{-18,0,0})<1e-6&&length(b.at(1)-Vec3{100,28,0})<1e-6,"Boat Bezier endpoints");
 double lo=1e30,hi=0;for(int i=1;i<=200;++i){double step=length(b.at(i/200.)-b.at((i-1)/200.));lo=std::min(lo,step);hi=std::max(hi,step);}require(hi/lo<1.005,"Arc-length speed stability");require(length((d.at(1)-b.at(1))-(d.at(0)-b.at(0)))>5,"Drone must have an independent route");require(length(fromZup({1,2,3})-Vec3{1,3,-2})<1e-8,"Z-up to Y-up conversion");
 require(entityForGroup("red_rower_1__body")==1&&entityForGroup("jade_dragon_head__face")==2&&entityForGroup("irregular_field_berm")==0,"Dynamic boat classification");
 require(motionForGroup("red_paddle_5_-1__grip")==11&&motionForGroup("jade_paddle_0_1__timber_shaft")==2&&motionForGroup("red_rower_2_1__body")==-1,"Paddle and replaced crew classification");
 RaceMotion race;require(race.at(0,5).distance>race.at(1,5).distance&&race.at(1,15).distance>race.at(0,15).distance&&race.at(0,26).distance>race.at(1,26).distance,"Different race strategies produce lead changes");
 for(int team=0;team<2;++team)for(int i=1;i<=2600;++i){auto a=race.at(team,(i-1)*.01),b=race.at(team,i*.01);require(b.distance>=a.distance&&b.cycles>a.cycles,"Distance and stroke phase monotonic");require(std::abs((b.distance-a.distance)/.01-(a.speed+b.speed)*.5)<1e-8,"Speed integrated continuously into distance");}
 require(length(paddlePoint(0,1,-1.6,.1)-paddlePoint(0,1,-1.6,.5))>.8,"Paddle blade must move visibly through drive");
 require(paddlePoint(0,1,-1.94,.1).y<-.06&&paddlePoint(0,1,-1.94,.83).y>.08,"Full blade tip enters the water and clears it in recovery");
 require(length(paddlePoint(0,1,-1.6,0)-paddlePoint(0,1,-1.6,1))<1e-8,"Paddle loop is closed");
 for(int i=0;i<=1000;++i){double reach=std::abs(paddlePoint(0,1,-1.94,i/1000.).z);require(reach<2.05&&reach+2.05<5.7,"Recovering paddles preserve lane gap and bank clearance");}
 require(motionForGroup("red_drummer__open_human_drummer__0")==-2&&motionForGroup("red_drummer_stool__seat")==0&&motionForGroup("jade_drumstick.001")==21,"Drummer/stick classification must preserve the stool");
 require(std::abs(drumTip(.1,1).y-1.67)<1e-8&&std::abs(drumTip(1.1,-1).y-1.67)<1e-8,"Alternating drum contacts align with each stroke catch");
 require(drumTip(.64,1).y>2.1&&drumTip(.64,1).y-drumTip(.1,1).y>.4,"Drumstick raises visibly and returns to the skin");
 require(length(drumTip(0,1)-drumTip(2,1))<1e-8,"Drumming loop closes after two strokes");
 for(int side:{-1,1})for(int i=0;i<=2000;++i){auto tip=drumTip(i/1000.,side);require(tip.y>=1.669,"Stick tip must not pass through drum skin");require(std::abs(drumGrip(i/1000.,side).x-3.89)<=.111,"Hands stay within a seated player's reach");}
 require(motionForGroup("red_pennant__flag_cloth")==30&&motionForGroup("jade_pennant__flagpole.001")==0,"Flag cloth separated from the fixed pole");
 auto flagMatrix=flagOrientation();
 auto flagPoint=[&](Vec3 p){return Vec3{flagMatrix[0]*p.x+flagMatrix[4]*p.y+flagMatrix[8]*p.z+flagMatrix[12],flagMatrix[1]*p.x+flagMatrix[5]*p.y+flagMatrix[9]*p.z+flagMatrix[13],flagMatrix[2]*p.x+flagMatrix[6]*p.y+flagMatrix[10]*p.z+flagMatrix[14]};};
 for(int team=0;team<2;++team)for(int i=0;i<=260;++i){
  double t=i*.1;auto wave=flagOffset(1,2.7,t,5,team);Vec3 pole{-4.45,2.7,-.18},tip=flagPoint({pole.x+.88,pole.y+wave.vertical,pole.z+wave.lateral});
  require(length(flagPoint(pole)-pole)<1e-10,"Reversing the flag must leave its pole edge fixed");
  auto heading=b.direction(t/26.);Vec3 trailing{heading.x*(tip.x-pole.x)-heading.y*(tip.z-pole.z),heading.y*(tip.x-pole.x)+heading.x*(tip.z-pole.z),0};
  require(dot(trailing,heading)<-.87,"Flag must trail toward the stern through river turns for both teams");
 }
 for(int i=0;i<1000;++i){auto a=flagOffset(0,2.7,i*.03,5,0);require(a.vertical==0&&a.lateral==0,"Flag pole edge must be pinned");}
 require(std::abs(flagOffset(1,2.7,0,5,0).lateral-flagOffset(1,2.7,.3,5,0).lateral)>.015,"Flag free edge visibly moves");
 CameraFlight flight;for(int i=1;i<6;++i){double t=flight.keys[i].time,h=.0001;Vec3 left=(flight.at(t)-flight.at(t-h))*(1/h),right=(flight.at(t+h)-flight.at(t))*(1/h);require(length(left-right)<.002,"Cinematic Bezier camera has continuous velocity");}
 for(int i=1;i<=1560;++i){auto a=flight.at((i-1)/60.),b=flight.at(i/60.);require(length(b-a)<.2&&b.z>3.1,"Drone low flight remains above water with smooth per-frame motion");}
 require(length((flight.at(26)-b.at(1))-(flight.at(0)-b.at(0)))>12,"Cinematic camera is not rigidly attached to a boat");
 require(motionForGroup("red_helmsman__body")==-3&&motionForGroup("jade_steering_oar__timber_shaft")==-4,"Static helmsmen and steering oars must be replaced");
 {auto samples=fs::path(exe).parent_path().parent_path()/L"models/steering_samples.csv";FILE* file=_wfopen(samples.c_str(),L"rb");require(file!=nullptr,"Baked steering sample file exists");char sampleLine[512];fgets(sampleLine,sizeof(sampleLine),file);int checked=0;
  while(fgets(sampleLine,sizeof(sampleLine),file)){std::string line(sampleLine);std::replace(line.begin(),line.end(),',',' ');std::istringstream row(line);double phase;Vec3 upper,lower;row>>phase>>upper.x>>upper.y>>upper.z>>lower.x>>lower.y>>lower.z;auto p=steeringFrame(phase);require(length(p.upper-upper)<.002&&length(p.lower-lower)<.002,"Baked palms must match the runtime steering-oar grips");++checked;}fclose(file);require(checked==41,"Complete closed steering cycle samples");}
 for(int team=0;team<2;++team)for(int i=0;i<=1560;++i){auto p=steeringFrame(steeringPhase(i/60.,team));require(p.lower.x<p.upper.x&&p.lower.z>.40,"Steering shaft must slope aft and outboard of the torso");}
 std::cout<<"PASS: OBJ/cache/coordinates, independent Bezier camera, variable speeds, paddles, drum contacts, linked steering grips, flag pinning, sternward direction and motion, cinematic velocity continuity\n";return 0;
 }catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<"\n";return 1;}}
