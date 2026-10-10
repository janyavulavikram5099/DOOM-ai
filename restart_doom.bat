@echo off
title DOOM AI - Clean Restart
echo ===================================================
echo         DOOM AI - RESTARTING ENGINE
echo ===================================================

cd /d "%~dp0"

echo Stopping any running DOOM AI processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8765 " ^| findstr "LISTENING"') do (
    echo Terminating PID %%a on port 8765...
    taskkill /f /pid %%a >nul 2>&1
)

taskkill /f /im powershell.exe /fi "WINDOWTITLE eq DOOM*" >nul 2>&1
timeout /t 1 /nobreak >nul

echo Starting DOOM AI with updated Bilingual Engine and Audio Core...
call run_vikram.bat
