@echo off
setlocal
cd /d "%~dp0"
if defined BLENDER_EXE if exist "%BLENDER_EXE%" goto custom
set "LOCAL_BLENDER=%~dp0..\_work\dragonboat\blender-4.3.2-windows-x64\blender.exe"
if exist "%LOCAL_BLENDER%" (
 start "" "%LOCAL_BLENDER%" "%~dp0dragonboat_realism.blend"
 exit /b 0
)
where blender >nul 2>nul
if not errorlevel 1 (
 start "" blender "%~dp0dragonboat_realism.blend"
 exit /b 0
)
echo Blender was not found. Install Blender or set BLENDER_EXE to blender.exe.
pause
exit /b 1
:custom
start "" "%BLENDER_EXE%" "%~dp0dragonboat_realism.blend"