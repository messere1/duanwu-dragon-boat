@echo off
setlocal
cd /d "%~dp0"
where g++ >nul 2>nul
if errorlevel 1 goto msvc
g++ -std=c++17 -O2 -Wall -Wextra -Wno-misleading-indentation src\tests.cpp -o bin\tests.exe -static -lstdc++fs
if errorlevel 1 exit /b 1
goto run
:msvc
where cl >nul 2>nul
if errorlevel 1 exit /b 1
cl /nologo /std:c++17 /utf-8 /EHsc /O2 src\tests.cpp /Fe:bin\tests.exe /Fo:bin\tests.obj
if errorlevel 1 exit /b 1
:run
bin\tests.exe
