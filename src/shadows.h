#pragma once
#include "gpu.h"
struct SunShadows {
 using Gen=void(APIENTRY*)(GLsizei,GLuint*);using Bind=void(APIENTRY*)(GLenum,GLuint);using Attach=void(APIENTRY*)(GLenum,GLenum,GLenum,GLuint,GLint);using Status=GLenum(APIENTRY*)(GLenum);using Blit=void(APIENTRY*)(GLint,GLint,GLint,GLint,GLint,GLint,GLint,GLint,GLbitfield,GLenum);
 using Delete=void(APIENTRY*)(GLsizei,const GLuint*);Gen gen;Delete del;Bind bind;Attach attach;Status status;Blit blit;GLuint fb[2]{},depth[2]{};GLfloat matrix[16]{};bool ready=false;static constexpr int size=4096;
 void init(){gen=glProc<Gen>("glGenFramebuffers");del=glProc<Delete>("glDeleteFramebuffers");bind=glProc<Bind>("glBindFramebuffer");attach=glProc<Attach>("glFramebufferTexture2D");status=glProc<Status>("glCheckFramebufferStatus");blit=glProc<Blit>("glBlitFramebuffer");gen(2,fb);glGenTextures(2,depth);
  for(int i=0;i<2;++i){glBindTexture(GL_TEXTURE_2D,depth[i]);glTexImage2D(GL_TEXTURE_2D,0,0x81A6,size,size,0,GL_DEPTH_COMPONENT,GL_UNSIGNED_INT,nullptr);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,0x884C,0x884E);glTexParameteri(GL_TEXTURE_2D,0x884D,GL_LEQUAL);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,0x812D);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,0x812D);GLfloat border[]={1,1,1,1};glTexParameterfv(GL_TEXTURE_2D,GL_TEXTURE_BORDER_COLOR,border);bind(0x8D40,fb[i]);attach(0x8D40,0x8D00,GL_TEXTURE_2D,depth[i],0);glDrawBuffer(GL_NONE);glReadBuffer(GL_NONE);if(status(0x8D40)!=0x8CD5)throw std::runtime_error("Shadow depth framebuffer incomplete");}end();
 }
 void begin(int layer){bind(0x8D40,fb[layer]);glViewport(0,0,size,size);glEnable(GL_DEPTH_TEST);glDepthMask(GL_TRUE);glEnable(GL_POLYGON_OFFSET_FILL);glPolygonOffset(1.6f,2.0f);glColorMask(GL_FALSE,GL_FALSE,GL_FALSE,GL_FALSE);glClear(GL_DEPTH_BUFFER_BIT);
  glMatrixMode(GL_PROJECTION);glLoadIdentity();glOrtho(-125,125,-95,95,1,360);GLfloat projection[16];glGetFloatv(GL_PROJECTION_MATRIX,projection);glMatrixMode(GL_MODELVIEW);glLoadIdentity();Vec3 target{40,0,-5},eye=target+unit({-.35,.85,.25})*180,f=unit(target-eye),s=unit(cross(f,{0,1,0})),u=cross(s,f);GLdouble view[]={s.x,u.x,-f.x,0,s.y,u.y,-f.y,0,s.z,u.z,-f.z,0,0,0,0,1};glMultMatrixd(view);glTranslated(-eye.x,-eye.y,-eye.z);GLfloat v[16];glGetFloatv(GL_MODELVIEW_MATRIX,v);for(int c=0;c<4;++c)for(int r=0;r<4;++r){matrix[c*4+r]=0;for(int k=0;k<4;++k)matrix[c*4+r]+=projection[k*4+r]*v[c*4+k];}
 }
 void copyStatic(){bind(0x8CA8,fb[0]);bind(0x8CA9,fb[1]);blit(0,0,size,size,0,0,size,size,GL_DEPTH_BUFFER_BIT,GL_NEAREST);bind(0x8D40,fb[1]);}
 void end(){glDisable(GL_POLYGON_OFFSET_FILL);bind(0x8D40,0);glColorMask(GL_TRUE,GL_TRUE,GL_TRUE,GL_TRUE);glDrawBuffer(GL_BACK);glReadBuffer(GL_BACK);}
 void destroy(){del(2,fb);glDeleteTextures(2,depth);}
};
