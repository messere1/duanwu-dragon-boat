@echo off
setlocal
cd /d "%~dp0"
if not exist bin mkdir bin
where cl >nul 2>nul
if not errorlevel 1 goto msvc
if exist "%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" (
 for /f "usebackq tokens=*" %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do call "%%i\VC\Auxiliary\Build\vcvars64.bat"
)
where cl >nul 2>nul
if not errorlevel 1 goto msvc
where g++ >nul 2>nul
if errorlevel 1 exit /b 1
g++ -std=c++17 -O2 -Wall -Wextra -Wno-misleading-indentation -municode -mwindows src\main.cpp -o bin\DragonBoat.exe -static -lstdc++fs -lopengl32 -lgdi32 -lcomdlg32 -lshell32 -lole32 -lwindowscodecs -luuid
exit /b %errorlevel%
:msvc
cl /nologo /std:c++17 /utf-8 /EHsc /W4 /O2 /DUNICODE /D_UNICODE src\main.cpp /Fe:bin\DragonBoat.exe /Fo:bin\main.obj /link /SUBSYSTEM:WINDOWS opengl32.lib gdi32.lib comdlg32.lib shell32.lib user32.lib ole32.lib windowscodecs.lib uuid.lib
exit /b %errorlevel%
