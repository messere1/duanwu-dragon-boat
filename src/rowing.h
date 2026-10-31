#pragma once
#include "gpu.h"
#include "race_motion.h"

class RowingCycle {
    uint32_t frames=0,count=0;
    std::vector<PackedVertex> poses,interpolated;std::vector<uint32_t> hairIndices;
public:
    Vec3 headCenters[2];GPU mesh,alternate;double lastCycles[2]={-1e30,-1e30};
    GPU& meshFor(int team){return team?alternate:mesh;}
    void destroy(){mesh.destroy();alternate.destroy();}
    void load(const fs::path& path,const std::vector<Material>& materials){
        FILE* f=_wfopen(path.c_str(),L"rb");if(!f)throw std::runtime_error("Missing baked rowing cycle");
        struct Close{FILE* f;~Close(){fclose(f);}} close{f};
        auto read=[&](void* p,size_t bytes){if(fread(p,1,bytes,f)!=bytes)throw std::runtime_error("Truncated rowing cycle");};
        char magic[8];uint32_t materialCount;read(magic,8);read(&frames,4);read(&count,4);read(&materialCount,4);
        if(memcmp(magic,"DBPOSE01",8)||frames<2||frames>100||count>1000000||materialCount>100)throw std::runtime_error("Invalid rowing cycle header");
        std::vector<int> mat;int hairSlot=-1;
        for(uint32_t i=0;i<materialCount;++i){uint32_t n;read(&n,4);if(n>256)throw std::runtime_error("Invalid pose material name");std::string name(n,' ');read(&name[0],n);int found=-1;if(name.find(".short01")!=std::string::npos)hairSlot=int(i);
            std::string token=name.substr(name.find("Human.")+5);if(token==".male_casualsuit04")token=".male_casualsuit";
            for(size_t j=0;j<materials.size();++j)if(materials[j].name.find("open_human_standing_open_human_seated_Human"+token)!=std::string::npos)found=int(j);
            if(found<0)throw std::runtime_error("Pose material not found: "+name);mat.push_back(found);}
        std::vector<uint32_t> ids(count);read(ids.data(),count*4);for(uint32_t i=0;i<count;++i)if(int(ids[i])==hairSlot)hairIndices.push_back(i);poses.resize(size_t(frames)*count);read(poses.data(),poses.size()*sizeof(PackedVertex));
        Asset a;a.vertices.assign(poses.begin(),poses.begin()+count);a.batches.resize(materialCount);for(uint32_t i=0;i<materialCount;++i)a.batches[i].material=mat[i];
        for(uint32_t i=0;i<count;++i){if(ids[i]>=materialCount)throw std::runtime_error("Invalid pose material index");a.batches[ids[i]].indices.push_back(i);}a.triangles=count/3;
        interpolated.resize(count);mesh.init();alternate.init();Asset copy=a;mesh.upload(std::move(a));alternate.upload(std::move(copy));
    }
    void update(double cycles,int team=0){if(lastCycles[team]==cycles)return;lastCycles[team]=cycles;GPU& target=meshFor(team);double p=(cycles-floor(cycles))*frames;uint32_t a=uint32_t(p),b=(a+1)%frames;float t=float(p-a);const auto* pa=poses.data()+size_t(a)*count;const auto* pb=poses.data()+size_t(b)*count;
        for(uint32_t i=0;i<count;++i){auto& v=interpolated[i];for(int j=0;j<3;++j){v.p[j]=pa[i].p[j]*(1-t)+pb[i].p[j]*t;v.n[j]=pa[i].n[j]*(1-t)+pb[i].n[j]*t;}v.uv[0]=pa[i].uv[0];v.uv[1]=pa[i].uv[1];}
        Vec3 center{};for(auto i:hairIndices){const auto& p=interpolated[i].p;center=center+Vec3{p[0],p[1],p[2]};}headCenters[team]=hairIndices.empty()?Vec3{0,.9,0}:center*(1.0/hairIndices.size());
        target.bind(0x8892,target.vertices);target.data(0x8892,ptrdiff_t(count*sizeof(PackedVertex)),interpolated.data(),0x88E0);target.bind(0x8892,0);
    }
};
