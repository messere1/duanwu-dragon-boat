#version 120
uniform sampler2D colorMap,normalMap,skyMap;
uniform int useTexture,useLighting,useNormals,useEnvironment,mode;
uniform vec3 baseColor,lightView,cameraRight,cameraUp,cameraFront,eye;
uniform float shininess,specularStrength,time;
uniform sampler2DShadow shadowMap;
uniform mat4 shadowMatrix;
uniform int shadowPass,useShadows,surfaceType;
uniform vec3 fabricColor;
uniform vec3 characterTint;
uniform int raceActive;
uniform float raceTime;
uniform vec3 wake[24],ripples[24],boatPosition[2],boatDirection[2],boatSpeed[2];
varying vec3 viewPosition,viewNormal;
varying vec2 uv;
float hashWater(vec2 p){p=fract(p*vec2(.1031,.11369));p+=dot(p,p.yx+vec2(19.19,27.31));return fract(p.x*p.y*73.156);}
float noiseWater(vec2 p){vec2 a=floor(p),f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(hashWater(a),hashWater(a+vec2(1.0,0.0)),f.x),mix(hashWater(a+vec2(0.0,1.0)),hashWater(a+vec2(1.0,1.0)),f.x),f.y);}
vec3 noiseGradient(vec2 p){vec2 a=floor(p),q=fract(p),f=q*q*(3.0-2.0*q),df=6.0*q*(1.0-q);float h00=hashWater(a),h10=hashWater(a+vec2(1,0)),h01=hashWater(a+vec2(0,1)),h11=hashWater(a+vec2(1,1));return vec3(mix(mix(h00,h10,f.x),mix(h01,h11,f.x),f.y),mix(h10-h00,h11-h01,f.y)*df.x,mix(h01-h00,h11-h10,f.x)*df.y);}
float sunVisibility(vec3 world,float ndotl){if(useShadows==0)return 1.0;vec4 p=shadowMatrix*vec4(world,1);vec3 q=p.xyz/p.w*.5+.5;if(q.z<0.0||q.z>1.0||q.x<.001||q.y<.001||q.x>.999||q.y>.999)return 1.0;float bias=.00018+.0005*(1.0-max(ndotl,0.0)),sum=0.0;for(int x=0;x<2;x++)for(int y=0;y<2;y++){vec2 d=(vec2(float(x),float(y))*2.0-1.0)*.8/4096.0;sum+=shadow2D(shadowMap,vec3(q.xy+d,q.z-bias)).r;}float edge=smoothstep(0.0,.025,min(min(q.x,q.y),min(1.0-q.x,1.0-q.y)));return mix(1.0,sum*.25,edge);}
void main(){
 vec4 tex=useTexture!=0?texture2D(colorMap,uv):vec4(1.0);
 if(tex.a<(surfaceType==7?.08:.35))discard;
 if(shadowPass!=0){gl_FragColor=vec4(1);return;}
 if(mode==1){gl_FragColor=vec4(tex.rgb*.98,1.0);return;}
 vec3 n=normalize(viewNormal);if(!gl_FrontFacing)n=-n;
 if(useNormals!=0){vec3 dp1=dFdx(viewPosition),dp2=dFdy(viewPosition);vec2 dt1=dFdx(uv),dt2=dFdy(uv);float determinant=dt1.x*dt2.y-dt1.y*dt2.x;
  if(abs(determinant)>0.00000001){vec3 t=normalize((dp1*dt2.y-dp2*dt1.y)/determinant);t=normalize(t-n*dot(n,t));vec3 b=normalize(cross(n,t))*sign(determinant);vec3 m=texture2D(normalMap,uv).xyz*2.0-1.0;n=normalize(t*m.x+b*m.y+n*m.z);}}
 vec3 world=eye+cameraRight*viewPosition.x+cameraUp*viewPosition.y-cameraFront*viewPosition.z;
 vec3 l=normalize(lightView),v=normalize(-viewPosition);vec3 albedo=pow(max(tex.rgb,vec3(0.0)),vec3(2.2))*baseColor;
 if(surfaceType==6)albedo*=characterTint;
 if(surfaceType==1&&useTexture!=0){
  vec2 q=world.xz;vec3 wn=normalize(cameraRight*n.x+cameraUp*n.y-cameraFront*n.z);
  vec3 a=texture2D(colorMap,q*.31).rgb,b=texture2D(colorMap,vec2(q.x*.57+q.y*.31,-q.x*.31+q.y*.57)+.37).rgb;
  float patch=noiseWater(q*.23+vec2(noiseWater(q*.08)*2.0));float grass=smoothstep(.30,.70,patch)*smoothstep(.18,.72,abs(wn.y));
  vec3 soil=mix(vec3(.31,.33,.20),vec3(.25,.32,.145),grass)*(.7+.65*mix(a,b,.45));
  float pixel=max(length(dFdx(q)),length(dFdy(q)));float fine=mix(1.0,.82+.36*noiseWater(q*7.0),1.0-smoothstep(.09,.45,pixel));
  albedo=pow(soil,vec3(2.2))*fine;float wet=1.0-smoothstep(-.05,.9,world.y);albedo=mix(albedo,vec3(.065,.058,.039),wet*.6);
 }
 if(surfaceType==2){float dirt=noiseWater(world.xz*.81+vec2(world.y*.3,world.y*.63));albedo*=.86+.19*dirt;albedo=mix(albedo,albedo*vec3(.59,.60,.48),(1.0-smoothstep(.15,1.8,world.y))*(.2+.6*dirt));}
 if(surfaceType==4){float grain=noiseWater(world.xz*.85+world.y*.17);float gray=dot(albedo,vec3(.2126,.7152,.0722));albedo=mix(albedo,vec3(gray)*vec3(.89,.91,.88),.4)*(.84+.23*grain);float damp=(1.0-smoothstep(.12,1.05,world.y))*(.2+.3*grain);albedo=mix(albedo,albedo*vec3(.54,.62,.49),damp);}
 if(surfaceType==5){float luminance=min(dot(tex.rgb,vec3(.2126,.7152,.0722)),.48);albedo=fabricColor*pow(luminance+.15,2.2)*1.8;}
 float foam=0.0;
 if(mode==2){
  // Small inland wind ripples. Different directions/wavelengths prevent a tiled grid.
  vec2 q=world.xz;
  float brokenWater=.25+.75*noiseWater(q*8.0+vec2(noiseWater(q*2.0),0.0));
  vec3 w1=noiseGradient(q*.73+vec2(time*.13,-time*.08));vec3 w2=noiseGradient(vec2(.8*q.x+.6*q.y,-.6*q.x+.8*q.y)*2.4+vec2(-time*.2,time*.11));vec3 w3=noiseGradient(vec2(.48*q.x-.88*q.y,.88*q.x+.48*q.y)*7.7+vec2(time*.3,time*.16));
  vec2 slope=.024*.73*w1.yz+.008*2.4*vec2(.8*w2.y-.6*w2.z,.6*w2.y+.8*w2.z)+.002*7.7*vec2(.48*w3.y+.88*w3.z,-.88*w3.y+.48*w3.z);
  if(raceActive!=0){
   for(int i=0;i<24;i++){
    float age=wake[i].z;
    if(age<0.0)continue;
    vec2 d=q-wake[i].xy;
    if(dot(d,d)>16.0)continue;
    int j=i==11?10:(i==23?22:i+1);
    vec2 forward=normalize(wake[i].xy-wake[j].xy+vec2(.00001,0.0));
    if(i==11||i==23)forward=-forward;
    vec2 across=vec2(-forward.y,forward.x);
    float x=dot(d,forward),y=dot(d,across),spread=.20+.48*age;
    float envelope=exp(-x*x/1.8-age*.78)*smoothstep(0.0,1.4,raceTime);
    float edge=exp(-pow((abs(y)-spread)/.15,2.0));
    float strength=clamp(boatSpeed[i<12?0:1].x/5.0,0.0,1.2);
    foam+=strength*envelope*(.08*edge+.018*exp(-y*y/(spread*spread)))*brokenWater;
    slope+=across*(envelope*.018*sin(y*13.0-age*9.0)*exp(-y*y/4.0));
   }
   for(int i=0;i<24;i++){
    float age=ripples[i].z;if(age<0.0)continue;
    vec2 d=q-ripples[i].xy-vec2(-.12,.04)*age;float r=length(d)*(1.0+.10*sin(atan(d.y+.00001,d.x+.00002)*3.0+float(i)*.73)),radius=.10+age*.74;
    if(r>1.6)continue;
    float envelope=exp(-pow((r-radius)/.13,2.0))*exp(-age*2.3);
    foam+=envelope*.035*brokenWater;
    slope+=d/max(r,.02)*envelope*.03*sin((r-radius)*20.0);
   }
   for(int i=0;i<2;i++){
    vec2 dir=boatDirection[i].xz;
    vec2 d=q-(boatPosition[i].xz+dir*4.15);
    float back=-dot(d,dir),side=abs(dot(d,vec2(-dir.y,dir.x)));
    if(back>0.0&&back<7.0){float edge=exp(-pow((side-(.45+back*.24))/.14,2.0))*exp(-back*.45);
     foam+=edge*.17*clamp(boatSpeed[i].x/5.0,0.0,1.0);}
   }
  }
  vec3 wn=normalize(vec3(-slope.x,1.0,-slope.y));
  n=normalize(vec3(dot(wn,cameraRight),dot(wn,cameraUp),-dot(wn,cameraFront)));
 }
 float diffuse=max(dot(n,l),0.0);float highlight=diffuse>0.0?pow(max(dot(reflect(-l,n),v),0.0),max(shininess,4.0)):0.0;
 float visibility=sunVisibility(world,diffuse);vec3 wnBase=normalize(cameraRight*n.x+cameraUp*n.y-cameraFront*n.z);float ambient=surfaceType==7?.50:(.29+.11*max(wnBase.y,0.0));float materialSpec=surfaceType==1||surfaceType==2||surfaceType==3||surfaceType==5?.025:specularStrength;
 vec3 color=useLighting!=0?albedo*(vec3(.81,.88,1.0)*ambient+vec3(1.0,.92,.80)*(.88*diffuse*visibility))+vec3(1.0,.95,.85)*highlight*materialSpec*visibility:albedo;
 if(surfaceType==8&&useLighting!=0){vec3 leaf=mix(tex.rgb,vec3(.38,.44,.20),.30);color=pow(leaf,vec3(2.2))*vec3(.96,1.12,.86)*(.72+.45*abs(dot(n,l)))*(.7+.3*visibility);}
 if(surfaceType==7&&useLighting!=0)color=albedo*vec3(1.2,1.7,1.05)*(.82+.18*visibility);
 if(mode==2&&useEnvironment!=0){vec3 wn=normalize(cameraRight*n.x+cameraUp*n.y-cameraFront*n.z);vec3 ray=reflect(normalize(world-eye),wn);vec2 env=vec2(atan(-ray.z,ray.x)/6.2831853,asin(clamp(ray.y,-1.0,1.0))/3.14159265+.5);float fresnel=.025+.975*pow(1.0-max(dot(n,v),0.0),5.0);color=mix(color,pow(texture2D(skyMap,env).rgb,vec3(2.2))*.8,fresnel);}
 if(mode==2)color=mix(color,vec3(.55,.62,.58),clamp(foam,0.0,.48));
 float fog=smoothstep(48.0,380.0,length(viewPosition));color=mix(color,vec3(.34,.40,.43),fog*.68);gl_FragColor=vec4(pow(max(color,vec3(0.0)),vec3(1.0/2.2)),1.0);
}


