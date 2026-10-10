@echo off
title DOOM AI - Permanent Windows Auto-Run Setup
echo ===================================================
echo      DOOM AI - PERMANENT WINDOWS AUTORUN SETUP
echo ===================================================
echo.
cd /d "%~dp0"

echo [1/4] Registering DOOM AI Assistant in Windows Startup Registry...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DOOM_AI_Assistant" /t REG_SZ /d "wscript.exe \"%~dp0start_doom_silent.vbs\"" /f >nul
if %errorlevel% equ 0 (
    echo       [OK] DOOM AI Assistant registered in Run registry.
) else (
    echo       [WARN] Could not write Assistant to registry.
)

echo.
echo [2/4] Registering Physical Shortcut Controller (Alt+Up / Alt+Down) in Startup Registry...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DOOM_AI_Shortcuts" /t REG_SZ /d "wscript.exe \"%~dp0start_shortcut_controller.vbs\"" /f >nul
if %errorlevel% equ 0 (
    echo       [OK] Shortcut Controller registered in Run registry.
) else (
    echo       [WARN] Could not write Shortcut Controller to registry.
)

echo.
echo [3/4] Adding scripts to Windows Startup Folder...
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
if exist "%STARTUP_FOLDER%" (
    copy /y "%~dp0start_doom_silent.vbs" "%STARTUP_FOLDER%\DOOM_AI.vbs" >nul
    copy /y "%~dp0start_shortcut_controller.vbs" "%STARTUP_FOLDER%\DOOM_AI_Shortcuts.vbs" >nul
    echo       [OK] Installed in Windows Startup folder:
    echo            %STARTUP_FOLDER%\DOOM_AI.vbs
    echo            %STARTUP_FOLDER%\DOOM_AI_Shortcuts.vbs
)

echo.
echo [4/4] Creating 1-Click Desktop Shortcuts...
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $desktop = [Environment]::GetFolderPath('Desktop'); $s = $ws.CreateShortcut(\"$desktop\DOOM AI.lnk\"); $s.TargetPath = \"wscript.exe\"; $s.Arguments = \"`\"%~dp0open_doom_hud.vbs`\"\"; $s.WorkingDirectory = \"%~dp0\"; $s.Description = \"DOOM AI - Personal Assistant\"; $s.Save()" >nul 2>&1
echo       [OK] Desktop shortcut 'DOOM AI' created.

echo.
echo ===================================================
echo   SUCCESS: DOOM AI IS NOW PERMANENTLY INSTALLED!
echo ===================================================
echo - ALT + UP ARROW   = DOOM AI ON (Activates voice commands & opens HUD)
echo - ALT + DOWN ARROW = DOOM AI OFF (Deactivates listening & automation)
echo - Shortcut Controller and DOOM AI will launch automatically on boot.
echo.
pause
