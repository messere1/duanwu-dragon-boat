#pragma once
#include <windows.h>
#include <GL/gl.h>
#include "math_scene.h"
#include <cstdint>
#include <map>
inline std::string readTextFile(const fs::path& path){
    FILE* f=_wfopen(path.c_str(),L"rb");if(!f)throw std::runtime_error("Cannot open shader file");
    std::string s;char buffer[4096];size_t n;while((n=fread(buffer,1,sizeof(buffer),f)))s.append(buffer,n);fclose(f);return s;
}
class Shader {
    std::map<std::string,GLint> uniforms;
    using CreateShader=GLuint(APIENTRY*)(GLenum);
    using ShaderSource=void(APIENTRY*)(GLuint,GLsizei,const char* const*,const GLint*);
    using CompileShader=void(APIENTRY*)(GLuint);
    using GetShaderiv=void(APIENTRY*)(GLuint,GLenum,GLint*);
    using GetShaderInfoLog=void(APIENTRY*)(GLuint,GLsizei,GLsizei*,char*);
    using CreateProgram=GLuint(APIENTRY*)();
    using AttachShader=void(APIENTRY*)(GLuint,GLuint);
    using LinkProgram=void(APIENTRY*)(GLuint);
    using GetProgramiv=void(APIENTRY*)(GLuint,GLenum,GLint*);
    using GetProgramInfoLog=void(APIENTRY*)(GLuint,GLsizei,GLsizei*,char*);
    using UseProgram=void(APIENTRY*)(GLuint);
    using DeleteShader=void(APIENTRY*)(GLuint);
    using DeleteProgram=void(APIENTRY*)(GLuint);
    using GetUniformLocation=GLint(APIENTRY*)(GLuint,const char*);
    using Uniform1i=void(APIENTRY*)(GLint,GLint);
    using Uniform1f=void(APIENTRY*)(GLint,GLfloat);
    using Uniform3f=void(APIENTRY*)(GLint,GLfloat,GLfloat,GLfloat);
    using UniformMatrix=void(APIENTRY*)(GLint,GLsizei,GLboolean,const GLfloat*);UniformMatrix uniformMatrix;
    CreateShader createShader;ShaderSource shaderSource;CompileShader compileShader;GetShaderiv getShaderiv;GetShaderInfoLog shaderLog;
    CreateProgram createProgram;AttachShader attachShader;LinkProgram linkProgram;GetProgramiv getProgramiv;GetProgramInfoLog programLog;
    UseProgram useProgram;DeleteShader deleteShader;DeleteProgram deleteProgram;GetUniformLocation location;Uniform1i uniform1i;Uniform1f uniform1f;Uniform3f uniform3f;
    template<class T>T proc(const char* name){
        auto p=wglGetProcAddress(name);auto value=reinterpret_cast<intptr_t>(p);
        if(!p||value==1||value==2||value==3||value==-1)throw std::runtime_error(std::string("OpenGL 2.0 shader support required: ")+name);
        return reinterpret_cast<T>(p);
    }
    GLuint compile(GLenum kind,const std::string& code){
        GLuint id=createShader(kind);const char* ptr=code.c_str();shaderSource(id,1,&ptr,nullptr);compileShader(id);
        GLint ok=0;getShaderiv(id,0x8B81,&ok);if(!ok){char log[8192]{};shaderLog(id,sizeof(log),nullptr,log);deleteShader(id);throw std::runtime_error(std::string("GLSL compile failed: ")+log);}return id;
    }
public:
    GLint uniform(const char* name){auto it=uniforms.find(name);if(it!=uniforms.end())return it->second;GLint id=location(program,name);uniforms[name]=id;return id;}
    GLuint program=0;
    void initialize(const fs::path& root){
        uniformMatrix=proc<UniformMatrix>("glUniformMatrix4fv");
#define LOAD(member,Type,Name) member=proc<Type>(Name)
        LOAD(createShader,CreateShader,"glCreateShader");LOAD(shaderSource,ShaderSource,"glShaderSource");LOAD(compileShader,CompileShader,"glCompileShader");
        LOAD(getShaderiv,GetShaderiv,"glGetShaderiv");LOAD(shaderLog,GetShaderInfoLog,"glGetShaderInfoLog");LOAD(createProgram,CreateProgram,"glCreateProgram");
        LOAD(attachShader,AttachShader,"glAttachShader");LOAD(linkProgram,LinkProgram,"glLinkProgram");LOAD(getProgramiv,GetProgramiv,"glGetProgramiv");
        LOAD(programLog,GetProgramInfoLog,"glGetProgramInfoLog");LOAD(useProgram,UseProgram,"glUseProgram");LOAD(deleteShader,DeleteShader,"glDeleteShader");
        LOAD(deleteProgram,DeleteProgram,"glDeleteProgram");LOAD(location,GetUniformLocation,"glGetUniformLocation");LOAD(uniform1i,Uniform1i,"glUniform1i");LOAD(uniform1f,Uniform1f,"glUniform1f");LOAD(uniform3f,Uniform3f,"glUniform3f");
#undef LOAD
        GLuint v=compile(0x8B31,readTextFile(root/L"shaders"/L"phong.vert"));
        GLuint f=compile(0x8B30,readTextFile(root/L"shaders"/L"phong.frag"));
        program=createProgram();attachShader(program,v);attachShader(program,f);linkProgram(program);deleteShader(v);deleteShader(f);
        GLint ok=0;getProgramiv(program,0x8B82,&ok);if(!ok){char log[8192]{};programLog(program,sizeof(log),nullptr,log);throw std::runtime_error(std::string("GLSL link failed: ")+log);}
    }
    void use(){useProgram(program);}void stop(){useProgram(0);}
    void integer(const char* name,int v){uniform1i(uniform(name),v);}
    void matrix(const char* name,const GLfloat* value){uniformMatrix(uniform(name),1,GL_FALSE,value);}
    void scalar(const char* name,double v){uniform1f(uniform(name),static_cast<float>(v));}
    void vector(const char* name,Vec3 v){uniform3f(uniform(name),static_cast<float>(v.x),static_cast<float>(v.y),static_cast<float>(v.z));}
    void destroy(){if(program){deleteProgram(program);program=0;}}
};
