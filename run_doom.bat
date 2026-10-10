@echo off
title DOOM AI - Personal Assistant
echo ===================================================
echo              DOOM PERSONAL AI ASSISTANT
echo ===================================================
echo Starting DOOM AI Background Service and Control Center...

cd /d "%~dp0"

REM Use project virtual environment if present (absolute path)
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_EXE=%~dp0.venv\Scripts\python.exe"
) else (
    set "PY_EXE=python"
)

REM Terminate any stale process holding port 8765
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8765 " ^| findstr "LISTENING"') do (
    echo Terminating stale process PID %%a on port 8765...
    taskkill /f /t /pid %%a >nul 2>&1
)
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*native_listener.ps1*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1
ping 127.0.0.1 -n 2 >nul

REM Launch physical shortcut controller in background if not already running
wscript.exe "%~dp0start_shortcut_controller.vbs" >nul 2>&1

REM Check if running headless or with UI
if "%1"=="--headless" (
    echo Launching in Silent Headless Background Mode...
    "%PY_EXE%" -m backend.app.main
) else (
    REM Start the server in an independent background process and open HUD
    start "DOOM AI Server" /MIN "%PY_EXE%" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765
    ping 127.0.0.1 -n 3 >nul
    start http://127.0.0.1:8765
)
