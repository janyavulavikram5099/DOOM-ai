@echo off
title DOOM AI - Instant Restart
cd /d "%~dp0"
echo ===================================================
echo     RESTARTING DOOM AI (OFFLINE VOICE ENGINE)
echo ===================================================
echo.
echo [1/3] Terminating old background assistant process...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8765 " ^| findstr "LISTENING"') do (
    taskkill /f /t /pid %%a >nul 2>&1
)
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*native_listener.ps1*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1
ping 127.0.0.1 -n 2 >nul

echo [2/3] Booting DOOM AI with Native Offline Speech Listener...
if exist ".venv\Scripts\python.exe" (
    set "PY_EXE=.venv\Scripts\python.exe"
) else (
    set "PY_EXE=python"
)

start "DOOM AI Server" /MIN "%PY_EXE%" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765
ping 127.0.0.1 -n 3 >nul

echo [3/3] Opening DOOM AI HUD in Browser...
start http://127.0.0.1:8765

echo.
echo ===================================================
echo   DOOM AI IS READY!
echo   100%% OFFLINE VOICE COMMANDS ARE NOW ACTIVE!
echo ===================================================
echo.
ping 127.0.0.1 -n 4 >nul
