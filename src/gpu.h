#pragma once
#include <windows.h>
#include <GL/gl.h>
#include <wincodec.h>
#include "assets.h"
#include <map>
template<class T>inline T glProc(const char* name){auto p=wglGetProcAddress(name);auto n=reinterpret_cast<intptr_t>(p);if(!p||n==1||n==2||n==3||n==-1)throw std::runtime_error(std::string("Missing OpenGL function: ")+name);return reinterpret_cast<T>(p);}
struct GPU {
    using Gen=void(APIENTRY*)(GLsizei,GLuint*);using Bind=void(APIENTRY*)(GLenum,GLuint);using Data=void(APIENTRY*)(GLenum,ptrdiff_t,const void*,GLenum);using Delete=void(APIENTRY*)(GLsizei,const GLuint*);using Active=void(APIENTRY*)(GLenum);using Mipmap=void(APIENTRY*)(GLenum);
    Gen gen;Bind bind;Data data;Delete del;Active active;Mipmap mipmap;GLuint vertices=0;size_t vertexCount=0;std::vector<Batch> batches;
    void init(){gen=glProc<Gen>("glGenBuffers");bind=glProc<Bind>("glBindBuffer");data=glProc<Data>("glBufferData");del=glProc<Delete>("glDeleteBuffers");active=glProc<Active>("glActiveTexture");mipmap=glProc<Mipmap>("glGenerateMipmap");}
    void destroy(){for(auto& b:batches)if(b.buffer)del(1,&b.buffer);batches.clear();if(vertices)del(1,&vertices);vertices=0;}
    void upload(Asset&& a){destroy();vertexCount=a.vertices.size();batches=std::move(a.batches);gen(1,&vertices);bind(0x8892,vertices);data(0x8892,ptrdiff_t(a.vertices.size()*sizeof(PackedVertex)),a.vertices.data(),0x88E4);for(auto& b:batches){for(auto index:b.indices){const auto& p=a.vertices[index].p;b.boundsMin={std::min(b.boundsMin.x,double(p[0])),std::min(b.boundsMin.y,double(p[1])),std::min(b.boundsMin.z,double(p[2]))};b.boundsMax={std::max(b.boundsMax.x,double(p[0])),std::max(b.boundsMax.y,double(p[1])),std::max(b.boundsMax.z,double(p[2]))};}gen(1,&b.buffer);bind(0x8893,b.buffer);data(0x8893,ptrdiff_t(b.indices.size()*4),b.indices.data(),0x88E4);b.count=b.indices.size();b.indices.clear();b.indices.shrink_to_fit();}bind(0x8892,0);bind(0x8893,0);if(glGetError()!=GL_NO_ERROR)throw std::runtime_error("GPU buffer upload failed");}
    void begin(){bind(0x8892,vertices);glEnableClientState(GL_VERTEX_ARRAY);glEnableClientState(GL_NORMAL_ARRAY);glEnableClientState(GL_TEXTURE_COORD_ARRAY);glVertexPointer(3,GL_FLOAT,sizeof(PackedVertex),nullptr);glNormalPointer(GL_FLOAT,sizeof(PackedVertex),reinterpret_cast<void*>(12));glTexCoordPointer(2,GL_FLOAT,sizeof(PackedVertex),reinterpret_cast<void*>(24));}
    void draw(const Batch& b){bind(0x8893,b.buffer);glDrawElements(GL_TRIANGLES,GLsizei(b.count),GL_UNSIGNED_INT,nullptr);}
    void end(){glDisableClientState(GL_VERTEX_ARRAY);glDisableClientState(GL_NORMAL_ARRAY);glDisableClientState(GL_TEXTURE_COORD_ARRAY);bind(0x8892,0);bind(0x8893,0);}
};
template<class T>struct Com {T* p=nullptr;~Com(){if(p)p->Release();}T** address(){return &p;}T* operator->(){return p;}};
inline void checked(HRESULT r,const char* operation){if(FAILED(r))throw std::runtime_error(std::string(operation)+" failed ("+std::to_string(uint32_t(r))+")");}
inline GLuint loadImage(const fs::path& path,GPU& gpu){
    Com<IWICImagingFactory> factory;checked(CoCreateInstance(CLSID_WICImagingFactory,nullptr,CLSCTX_INPROC_SERVER,IID_IWICImagingFactory,reinterpret_cast<void**>(factory.address())),"WIC factory");
    Com<IWICBitmapDecoder> decoder;checked(factory->CreateDecoderFromFilename(path.c_str(),nullptr,GENERIC_READ,WICDecodeMetadataCacheOnLoad,decoder.address()),"Image decode");
    Com<IWICBitmapFrameDecode> frame;checked(decoder->GetFrame(0,frame.address()),"Image frame");UINT w=0,h=0;frame->GetSize(&w,&h);if(!w||!h||w>16384||h>16384)throw std::runtime_error("Invalid texture size");
    Com<IWICFormatConverter> convert;checked(factory->CreateFormatConverter(convert.address()),"Pixel converter");checked(convert->Initialize(frame.p,GUID_WICPixelFormat32bppRGBA,WICBitmapDitherTypeNone,nullptr,0,WICBitmapPaletteTypeCustom),"RGBA conversion");
    std::vector<unsigned char> pixels(size_t(w)*h*4);checked(convert->CopyPixels(nullptr,w*4,UINT(pixels.size()),pixels.data()),"Image pixels");
    for(UINT y=0;y<h/2;++y)for(UINT x=0;x<w*4;++x)std::swap(pixels[size_t(y)*w*4+x],pixels[size_t(h-1-y)*w*4+x]);
    GLuint id;glGenTextures(1,&id);glBindTexture(GL_TEXTURE_2D,id);glPixelStorei(GL_UNPACK_ALIGNMENT,1);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA,w,h,0,GL_RGBA,GL_UNSIGNED_BYTE,pixels.data());gpu.mipmap(GL_TEXTURE_2D);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,0x2703);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT);return id;
}
inline void savePNG(const fs::path& path,int w,int h){
    std::vector<unsigned char> pixels(size_t(w)*h*4);glPixelStorei(GL_PACK_ALIGNMENT,1);glReadBuffer(GL_BACK);glReadPixels(0,0,w,h,0x80E1,GL_UNSIGNED_BYTE,pixels.data());for(int y=0;y<h/2;++y)for(int x=0;x<w*4;++x)std::swap(pixels[size_t(y)*w*4+x],pixels[size_t(h-1-y)*w*4+x]);
    Com<IWICImagingFactory> factory;checked(CoCreateInstance(CLSID_WICImagingFactory,nullptr,CLSCTX_INPROC_SERVER,IID_IWICImagingFactory,reinterpret_cast<void**>(factory.address())),"PNG factory");Com<IWICStream> stream;factory->CreateStream(stream.address());checked(stream->InitializeFromFilename(path.c_str(),GENERIC_WRITE),"PNG file");Com<IWICBitmapEncoder> encoder;factory->CreateEncoder(GUID_ContainerFormatPng,nullptr,encoder.address());encoder->Initialize(stream.p,WICBitmapEncoderNoCache);Com<IWICBitmapFrameEncode> frame;encoder->CreateNewFrame(frame.address(),nullptr);frame->Initialize(nullptr);frame->SetSize(w,h);WICPixelFormatGUID format=GUID_WICPixelFormat32bppBGRA;frame->SetPixelFormat(&format);checked(frame->WritePixels(h,w*4,UINT(pixels.size()),pixels.data()),"PNG encode");checked(frame->Commit(),"PNG frame commit");checked(encoder->Commit(),"PNG commit");
}
