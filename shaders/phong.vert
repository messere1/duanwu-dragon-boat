#version 120
varying vec3 viewPosition;
varying vec3 viewNormal;
varying vec2 uv;
uniform int mode;
uniform float flagTime,flagSpeed,flagTeam;
uniform int isPerson;
uniform vec3 personHead,personStyle;
vec2 clothOffset(float x,float y){float u=clamp((x+4.45)/.88,0.0,1.0);float phase=9.0*u+3.0*(y-2.46)-flagTime*(4.0+.4*flagSpeed)+flagTeam*.9;return vec2(.012*u*u*sin(phase*.8),(.035+.012*flagSpeed)*u*u*(.7*sin(phase)+.3*sin(1.9*phase+.5)));}
void main(){
 vec4 local=gl_Vertex;vec3 normal=gl_Normal;
 if(isPerson!=0){vec3 d=local.xyz-personHead;float w=1.0-smoothstep(.13,.195,length(d)),angle=personStyle.z*w,c=cos(angle),s=sin(angle),scale=1.0+personStyle.x*w;d.xz=vec2(c*d.x+s*d.z,-s*d.x+c*d.z)*scale;local.xyz=personHead+d;local.y+=personStyle.y*w;normal.xz=vec2(c*normal.x+s*normal.z,-s*normal.x+c*normal.z)/scale;}
 if(mode==3){vec2 d=clothOffset(local.x,local.y),dx=(clothOffset(local.x+.002,local.y)-clothOffset(local.x-.002,local.y))/.004,dy=(clothOffset(local.x,local.y+.002)-clothOffset(local.x,local.y-.002))/.004;
  vec3 tx=vec3(1.0,dx.x,-normal.x/normal.z+dx.y),ty=vec3(0.0,1.0+dy.x,-normal.y/normal.z+dy.y);normal=normalize(cross(tx,ty))*sign(normal.z);local.yz+=d;
 }
 vec4 p=gl_ModelViewMatrix*local;viewPosition=p.xyz;viewNormal=normalize(gl_NormalMatrix*normal);uv=gl_MultiTexCoord0.xy;gl_Position=gl_ProjectionMatrix*p;
}
