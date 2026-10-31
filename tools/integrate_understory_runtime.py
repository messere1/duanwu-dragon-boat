from pathlib import Path
p=Path('src/main.cpp');s=p.read_text(encoding='utf-8-sig')
if 'GPU gpu,extra,landscapeDetails,villageDetails,understory;' in s:raise SystemExit('Runtime overlay already integrated')
s=s.replace('landscapeDetails,villageDetails;', 'landscapeDetails,villageDetails,understory;')
s=s.replace('villageDetails.init();shader.initialize', 'villageDetails.init();understory.init();shader.initialize')
s=s.replace('villageDetails.destroy();landscapeDetails.destroy();', 'understory.destroy();villageDetails.destroy();landscapeDetails.destroy();')
needle=' if(villageDetails.vertices){'
idx=s.index(needle)
end=s.index('\n}',idx)
block=s[idx:end]
s=s[:end]+ '\n'+block.replace('villageDetails','understory')+s[end:]
needle='sunShadows.init();antialias.init(sunShadows);'
load='{auto detailMaterials=readMTL(root/L"models/landscape_understory.mtl");Asset details=readSceneOBJ(root/L"models/landscape_understory.obj",detailMaterials,true);initializeTextures(detailMaterials);int offset=int(materials.size());for(auto& b:details.batches)b.material+=offset;materials.insert(materials.end(),detailMaterials.begin(),detailMaterials.end());triangles+=details.triangles;logFile<<"Understory triangles "<<details.triangles<<"\\n";understory.upload(std::move(details));}'
s=s.replace(needle,load+needle)
p.write_text(s,encoding='utf8')
p=Path('shaders/phong.frag');s=p.read_text(encoding='utf-8-sig')
a=s.index(' if(surfaceType==1&&useTexture!=0)');b=s.index('\n if(surfaceType==2)',a)
s=s[:a]+''' if(surfaceType==1&&useTexture!=0){
  vec2 q=world.xz;vec3 wn=normalize(cameraRight*n.x+cameraUp*n.y-cameraFront*n.z);
  vec3 a=texture2D(colorMap,q*.31).rgb,b=texture2D(colorMap,vec2(q.x*.57+q.y*.31,-q.x*.31+q.y*.57)+.37).rgb;
  float patch=noiseWater(q*.23+vec2(noiseWater(q*.08)*2.0));float grass=smoothstep(.30,.70,patch)*smoothstep(.42,.9,abs(wn.y));
  vec3 soil=mix(vec3(.36,.32,.23),vec3(.25,.32,.145),grass)*(.7+.65*mix(a,b,.45));
  float pixel=max(length(dFdx(q)),length(dFdy(q)));float fine=mix(1.0,.82+.36*noiseWater(q*7.0),1.0-smoothstep(.09,.45,pixel));
  albedo=pow(soil,vec3(2.2))*fine;float wet=1.0-smoothstep(-.05,.9,world.y);albedo=mix(albedo,vec3(.065,.058,.039),wet*.6);
 }''' +s[b:]
# Distant terrain is softened by aerial perspective before fine detail aliases.
s=s.replace('float fog=smoothstep(85.0,480.0,length(viewPosition));','float fog=smoothstep(48.0,380.0,length(viewPosition));')
p.write_text(s,encoding='ascii')
