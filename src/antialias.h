#pragma once
#include "shadows.h"
struct SceneAntialias {
 using Gen=void(APIENTRY*)(GLsizei,GLuint*);using Bind=void(APIENTRY*)(GLenum,GLuint);using Storage=void(APIENTRY*)(GLenum,GLsizei,GLenum,GLsizei,GLsizei);using Attach=void(APIENTRY*)(GLenum,GLenum,GLenum,GLuint);
 using Delete=void(APIENTRY*)(GLsizei,const GLuint*);Gen gen;Delete del;Bind bind;Storage storage;Attach attach;GLuint fb=0,rbo[2]{};int width=0,height=0;
 void init(SunShadows& s){gen=glProc<Gen>("glGenRenderbuffers");del=glProc<Delete>("glDeleteRenderbuffers");bind=glProc<Bind>("glBindRenderbuffer");storage=glProc<Storage>("glRenderbufferStorageMultisample");attach=glProc<Attach>("glFramebufferRenderbuffer");s.gen(1,&fb);gen(2,rbo);}
 void begin(SunShadows& s,int w,int h){s.bind(0x8D40,fb);if(w!=width||h!=height){width=w;height=h;for(int i=0;i<2;++i){bind(0x8D41,rbo[i]);storage(0x8D41,4,i?0x81A6:0x8058,w,h);attach(0x8D40,i?0x8D00:0x8CE0,0x8D41,rbo[i]);}glDrawBuffer(0x8CE0);glReadBuffer(0x8CE0);if(s.status(0x8D40)!=0x8CD5)throw std::runtime_error("MSAA framebuffer incomplete");}glEnable(0x809D);}
 void resolve(SunShadows& s){s.bind(0x8CA8,fb);s.bind(0x8CA9,0);s.blit(0,0,width,height,0,0,width,height,GL_COLOR_BUFFER_BIT,GL_NEAREST);s.bind(0x8D40,0);glDrawBuffer(GL_BACK);glReadBuffer(GL_BACK);}
 void destroy(SunShadows& s){del(2,rbo);s.del(1,&fb);}
};
