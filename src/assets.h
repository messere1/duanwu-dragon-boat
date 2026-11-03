#pragma once
#include "math_scene.h"
#include <map>
#include <cstring>
#include <cstdint>
#include <limits>
#include <functional>
#include <tuple>
#include "race_motion.h"
struct PackedVertex {float p[3],n[3],uv[2];};
struct Material {std::string name;Vec3 color{.7,.7,.7};double shine=24,specular=.12;fs::path colorFile,normalFile;unsigned colorMap=0,normalMap=0;};
struct Batch {int material=0,entity=0;std::vector<uint32_t> indices;unsigned buffer=0;size_t count=0;int motion=0;Vec3 boundsMin{1e30,1e30,1e30},boundsMax{-1e30,-1e30,-1e30};};
struct Asset {std::vector<PackedVertex> vertices;std::vector<Batch> batches;size_t triangles=0;};
inline std::string trim(std::string s){auto a=s.find_first_not_of(" \t\r\n"),b=s.find_last_not_of(" \t\r\n");return a==s.npos?"":s.substr(a,b-a+1);}
inline fs::path utf8Path(const std::string& value){int n=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,value.c_str(),int(value.size()),nullptr,0);if(!n)throw std::runtime_error("Invalid UTF-8 asset path");std::wstring out(size_t(n),L' ');MultiByteToWideChar(CP_UTF8,0,value.c_str(),int(value.size()),&out[0],n);return fs::path(out);}
inline std::vector<Material> readMTL(const fs::path& path){
    FILE* f=_wfopen(path.c_str(),L"rb");if(!f)throw std::runtime_error("Cannot open palette.mtl");
    std::vector<Material> out(1);out[0].name="default";char line[4096];
    while(fgets(line,sizeof(line),f)){std::istringstream s(line);std::string tag;s>>tag;
        if(tag=="newmtl"){Material m;s>>m.name;out.push_back(m);}
        else if(tag=="Kd")s>>out.back().color.x>>out.back().color.y>>out.back().color.z;
        else if(tag=="Ns")s>>out.back().shine;
        else if(tag=="Ks"){double x;s>>x;out.back().specular=x;}
        else if(tag=="map_Kd"||tag=="map_Bump"||tag=="bump"){std::string value;std::getline(s,value);auto p=path.parent_path()/utf8Path(trim(value));if(tag=="map_Kd")out.back().colorFile=p;else out.back().normalFile=p;}
    }fclose(f);return out;
}
inline fs::path referencedMTL(const fs::path& obj){FILE* f=_wfopen(obj.c_str(),L"rb");if(!f)throw std::runtime_error("Cannot open OBJ");char line[4096];fs::path result;for(int i=0;i<1000&&fgets(line,sizeof(line),f);++i){if(strncmp(line,"mtllib ",7)==0){result=obj.parent_path()/utf8Path(trim(line+7));break;}}fclose(f);return result;}
inline int entityForGroup(const std::string& group){
    if(group.rfind("red_",0)==0)return 1;if(group.rfind("jade_",0)==0)return 2;
    if(group.find("inward_cloudy_sky")!=group.npos)return 3;
    if(group.find("bending_river_surface")!=group.npos||group.find("continuous_bending_river")!=group.npos)return 4;
    return 0;
}
inline Asset readSceneOBJ(const fs::path& path,const std::vector<Material>& materials,bool classify=true,const std::function<void(size_t)>& progress={}){
    FILE* f=_wfopen(path.c_str(),L"rb");if(!f)throw std::runtime_error("Cannot open OBJ");
    struct Close {FILE* f;~Close(){fclose(f);}} close{f};setvbuf(f,nullptr,_IOFBF,1024*1024);
    struct V3 {float x,y,z;};struct UV {float x,y;};std::vector<V3> p,n;std::vector<UV> uv;std::vector<uint32_t> remap;
    Asset a;std::map<std::tuple<int,int,int,int,int>,size_t> slots;std::map<std::string,int> matIDs;
    for(size_t i=0;i<materials.size();++i)matIDs[materials[i].name]=int(i);
    int mat=0,entity=0,motion=0;char line[16384];size_t lineNo=0;
    auto number=[](char*& c){while(*c==' '||*c=='\t')++c;char* end;float v=strtof(c,&end);if(c==end||!std::isfinite(v))throw std::runtime_error("Bad OBJ floating point value");c=end;return v;};
    auto idx=[](long x,size_t size){long long r=x>0?x-1:static_cast<long long>(size)+x;if(x==0||r<0||r>=static_cast<long long>(size))throw std::runtime_error("OBJ index out of bounds");return int(r);};
    while(fgets(line,sizeof(line),f)){
        ++lineNo;if(progress&&lineNo%300000==0)progress(lineNo);char* c=line;
        if(c[0]=='v'&&c[1]==' '){c+=2;V3 v;v.x=number(c);v.y=number(c);v.z=number(c);p.push_back(v);remap.push_back(UINT32_MAX);}
        else if(c[0]=='v'&&c[1]=='n'){c+=2;V3 v;v.x=number(c);v.y=number(c);v.z=number(c);n.push_back(v);}
        else if(c[0]=='v'&&c[1]=='t'){c+=2;UV t;t.x=number(c);t.y=number(c);uv.push_back(t);}
        else if(c[0]=='o'&&c[1]==' '){auto name=trim(c+2);entity=classify?entityForGroup(name):0;motion=classify&&(entity==1||entity==2)?motionForGroup(name):0;}
        else if(strncmp(c,"usemtl ",7)==0){auto it=matIDs.find(trim(c+7));if(it==matIDs.end())throw std::runtime_error("OBJ references undefined MTL material");mat=it->second;}
        else if(c[0]=='f'&&c[1]==' '){
            struct Ref {int p,t,n;};std::vector<Ref> refs;c+=2;
            while(*c){while(*c==' '||*c=='\t'||*c=='\r'||*c=='\n')++c;if(!*c||*c=='#')break;char* e;long pi=strtol(c,&e,10);if(e==c)throw std::runtime_error("Invalid OBJ face");c=e;Ref r{idx(pi,p.size()),-1,-1};
                if(*c=='/'){++c;if(*c!='/'){long ti=strtol(c,&e,10);c=e;r.t=idx(ti,uv.size());}if(*c=='/'){++c;long ni=strtol(c,&e,10);c=e;r.n=idx(ni,n.size());}}refs.push_back(r);
            }
            if(refs.size()<3)throw std::runtime_error("OBJ face has fewer than three corners");
            auto anchor=p[refs[0].p];int cellX=entity==0&&classify?int(floor(anchor.x/64)):0,cellZ=entity==0&&classify?int(floor(anchor.z/64)):0;
            auto key=std::make_tuple(entity,mat,motion,cellX,cellZ);auto it=slots.find(key);if(it==slots.end()){slots[key]=a.batches.size();a.batches.push_back({mat,entity,{ },0});a.batches.back().motion=motion;}auto& b=a.batches[slots[key]];
            for(size_t k=1;k+1<refs.size();++k){Ref tri[]={refs[0],refs[k],refs[k+1]};auto v0=p[tri[0].p],v1=p[tri[1].p],v2=p[tri[2].p];Vec3 normal=unit(cross(Vec3{v1.x-v0.x,v1.y-v0.y,v1.z-v0.z},Vec3{v2.x-v0.x,v2.y-v0.y,v2.z-v0.z}));
                for(auto r:tri){uint32_t index=UINT32_MAX;bool fast=r.p==r.t&&r.p==r.n;if(fast)index=remap[r.p];
                    if(index==UINT32_MAX){auto q=p[r.p];auto nn=r.n>=0?n[r.n]:V3{float(normal.x),float(normal.y),float(normal.z)};auto t=r.t>=0?uv[r.t]:UV{q.x*.1f,q.z*.1f};
                        if(entity==1){q.x+=5;q.z-=2.2f;}else if(entity==2){q.x+=6;q.z+=2.2f;}
                        PackedVertex v{{q.x,q.y,q.z},{nn.x,nn.y,nn.z},{t.x,t.y}};index=uint32_t(a.vertices.size());a.vertices.push_back(v);if(fast)remap[r.p]=index;
                    }b.indices.push_back(index);
                }++a.triangles;
            }
        }
    }
    if(ferror(f)||a.vertices.empty())throw std::runtime_error("OBJ incomplete or empty");return a;
}
struct CacheHeader {char magic[8];uint64_t size,stamp,mtlStamp,vertices,batches,triangles;};
inline uint64_t fileStamp(const fs::path& path){return uint64_t(fs::last_write_time(path).time_since_epoch().count());}
inline Asset loadScene(const fs::path& root,const std::vector<Material>& mats,bool& cacheHit,const std::function<void(size_t)>& progress={}){
    auto src=root/L"models/scene_preview.obj",mtl=root/L"models/palette.mtl",cache=root/L"cache/scene-v6.bin";
    CacheHeader want{};memcpy(want.magic,"DBSCN06",8);want.size=fs::file_size(src);want.stamp=fileStamp(src);want.mtlStamp=fileStamp(mtl);cacheHit=false;
    FILE* f=_wfopen(cache.c_str(),L"rb");if(f){CacheHeader h{};bool ok=fread(&h,sizeof(h),1,f)==1&&memcmp(h.magic,want.magic,8)==0&&h.size==want.size&&h.stamp==want.stamp&&h.mtlStamp==want.mtlStamp&&h.vertices<50000000&&h.batches<20000;
        Asset a;if(ok){a.vertices.resize(size_t(h.vertices));ok=fread(a.vertices.data(),sizeof(PackedVertex),a.vertices.size(),f)==a.vertices.size();
            for(uint64_t i=0;ok&&i<h.batches;++i){int info[3];uint64_t count=0;ok=fread(info,sizeof(info),1,f)==1&&fread(&count,sizeof(count),1,f)==1&&info[0]>=0&&info[0]<int(mats.size())&&info[1]>=0&&info[1]<=4&&count<=30000000;if(!ok)break;Batch b;b.material=info[0];b.entity=info[1];b.motion=info[2];b.indices.resize(size_t(count));ok=fread(b.indices.data(),sizeof(uint32_t),size_t(count),f)==count;if(ok)for(auto idx:b.indices)if(idx>=h.vertices){ok=false;break;}a.batches.push_back(std::move(b));}
            if(ok){a.triangles=size_t(h.triangles);cacheHit=true;fclose(f);return a;}
        }fclose(f);
    }
    Asset a=readSceneOBJ(src,mats,true,progress);fs::create_directories(cache.parent_path());auto pending=cache;pending+=L".tmp";f=_wfopen(pending.c_str(),L"wb");
    if(f){want.vertices=a.vertices.size();want.batches=a.batches.size();want.triangles=a.triangles;bool ok=fwrite(&want,sizeof(want),1,f)==1&&fwrite(a.vertices.data(),sizeof(PackedVertex),a.vertices.size(),f)==a.vertices.size();for(auto& b:a.batches){int info[]={b.material,b.entity,b.motion};uint64_t count=b.indices.size();ok=ok&&fwrite(info,sizeof(info),1,f)==1&&fwrite(&count,sizeof(count),1,f)==1&&fwrite(b.indices.data(),sizeof(uint32_t),b.indices.size(),f)==b.indices.size();}ok=ok&&fclose(f)==0;if(ok){if(fs::exists(cache))fs::remove(cache);fs::rename(pending,cache);}}
    return a;
}
