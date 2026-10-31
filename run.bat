@echo off
cd /d "%~dp0"
if not exist bin\DragonBoat.exe call build.bat
if not exist bin\DragonBoat.exe exit /b 1
start "" bin\DragonBoat.exe %*
