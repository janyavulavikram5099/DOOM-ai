"""
VIKRAM AI - Application Executor
Discovers, launches, and closes authorized Windows applications safely.
"""

import logging
import os
import re
import shutil
import subprocess

import psutil

logger = logging.getLogger("vikram.execution.application")

# Common application executable mappings
APP_MAP = {
    "vs code": ["code.cmd", "code.exe", "code"],
    "visual studio code": ["code.cmd", "code.exe", "code"],
    "vscode": ["code.cmd", "code.exe", "code"],
    "chrome": ["chrome.exe", "chrome"],
    "google chrome": ["chrome.exe", "chrome"],
    "discord": ["Discord.exe", "discord"],
    "notepad": ["notepad.exe", "notepad"],
    "file explorer": ["explorer.exe"],
    "explorer": ["explorer.exe"],
    "terminal": ["wt.exe", "powershell.exe", "cmd.exe"],
    "cmd": ["cmd.exe"],
    "calculator": ["calc.exe"],
    "calc": ["calc.exe"],
    "settings": ["SystemSettings.exe"],
    "setting": ["SystemSettings.exe"],
    "windows settings": ["SystemSettings.exe"],
    "task manager": ["taskmgr.exe"],
    "taskmgr": ["taskmgr.exe"],
    "paint": ["mspaint.exe"],
    "mspaint": ["mspaint.exe"],
    "edge": ["msedge.exe"],
    "microsoft edge": ["msedge.exe"],
    "word": ["winword.exe"],
    "excel": ["excel.exe"],
    "powerpoint": ["powerpnt.exe"],
    "roblox": ["RobloxPlayerBeta.exe", "RobloxPlayerLauncher.exe", "RobloxPlayer.exe"],
    "roblox player": ["RobloxPlayerBeta.exe", "RobloxPlayerLauncher.exe", "RobloxPlayer.exe"],
    "robolox": ["RobloxPlayerBeta.exe", "RobloxPlayerLauncher.exe", "RobloxPlayer.exe"],
    "robolox player": ["RobloxPlayerBeta.exe", "RobloxPlayerLauncher.exe", "RobloxPlayer.exe"],
    "roblox studio": ["RobloxStudioBeta.exe", "RobloxStudioInstaller.exe"],
    "robolox studio": ["RobloxStudioBeta.exe", "RobloxStudioInstaller.exe"],
    "opera": ["opera.exe"],
    "opera gx": ["opera.exe"],
    "opera gx browser": ["opera.exe"],
    "notepad++": ["notepad++.exe"],
    "notepad plus plus": ["notepad++.exe"],
    "intellij": ["idea64.exe"],
    "intellij idea": ["idea64.exe"],
    "postman": ["Postman.exe"],
    "docker": ["Docker Desktop.exe"],
    "docker desktop": ["Docker Desktop.exe"],
    "dev c++": ["devcpp.exe"],
    "devcpp": ["devcpp.exe"],
    "vantage": ["LenovoVantage.exe", "LenovoCompanion.exe"],
    "lenovo vantage": ["LenovoVantage.exe", "LenovoCompanion.exe"],
}

# Windows URI protocol handlers for modern Store and native apps
URI_MAP = {
    "settings": "ms-settings:",
    "setting": "ms-settings:",
    "windows settings": "ms-settings:",
    "pc settings": "ms-settings:",
    "store": "ms-windows-store:",
    "microsoft store": "ms-windows-store:",
    "windows store": "ms-windows-store:",
    "calculator": "calculator:",
    "calc": "calculator:",
    "camera": "microsoft.windows.camera:",
    "clock": "ms-clock:",
    "alarms": "ms-clock:",
    "alarm": "ms-clock:",
    "photos": "ms-photos:",
    "mail": "outlookmail:",
    "outlook": "outlookmail:",
    "copilot": "microsoft-edge:https://copilot.microsoft.com",
    "edge": "microsoft-edge:",
    "microsoft edge": "microsoft-edge:",
}

# Web fallbacks if native desktop/Store app is not installed
WEB_FALLBACK = {
    "whatsapp": "https://web.whatsapp.com",
    "whatsapp desktop": "https://web.whatsapp.com",
    "spotify": "https://open.spotify.com",
    "teams": "https://teams.microsoft.com",
    "discord": "https://discord.com/app",
    "youtube": "https://www.youtube.com",
    "chatgpt": "https://chatgpt.com",
    "roblox": "https://www.roblox.com",
    "roblox player": "https://www.roblox.com",
    "robolox": "https://www.roblox.com",
    "robolox player": "https://www.roblox.com",
}

PROCESS_NAMES = {
    "whatsapp": ["WhatsApp.Root.exe", "WhatsApp.exe", "WhatsAppRoot.exe", "WhatsApp"],
    "whatsapp desktop": ["WhatsApp.Root.exe", "WhatsApp.exe", "WhatsAppRoot.exe", "WhatsApp"],
    "vs code": ["Code.exe"],
    "visual studio code": ["Code.exe"],
    "vscode": ["Code.exe"],
    "code": ["Code.exe"],
    "chrome": ["chrome.exe"],
    "google chrome": ["chrome.exe"],
    "browser": ["chrome.exe", "msedge.exe", "firefox.exe", "brave.exe"],
    "edge": ["msedge.exe"],
    "microsoft edge": ["msedge.exe"],
    "discord": ["Discord.exe"],
    "notepad": ["notepad.exe", "Notepad.exe"],
    "calculator": ["CalculatorApp.exe", "calc.exe", "Calculator.exe"],
    "calc": ["CalculatorApp.exe", "calc.exe"],
    "settings": ["SystemSettings.exe", "SystemSettingsAdminFlows.exe"],
    "setting": ["SystemSettings.exe", "SystemSettingsAdminFlows.exe"],
    "windows settings": ["SystemSettings.exe", "SystemSettingsAdminFlows.exe"],
    "task manager": ["Taskmgr.exe", "taskmgr.exe"],
    "taskmgr": ["Taskmgr.exe", "taskmgr.exe"],
    "spotify": ["Spotify.exe"],
    "telegram": ["Telegram.exe"],
    "roblox": [
        "RobloxPlayerBeta.exe", "RobloxPlayer.exe", "RobloxPlayerLauncher.exe",
        "RobloxStudioBeta.exe", "RobloxStudioInstaller.exe", "RobloxStudio.exe",
        "RobloxCrashHandler.exe"
    ],
    "roblox player": [
        "RobloxPlayerBeta.exe", "RobloxPlayer.exe", "RobloxPlayerLauncher.exe",
        "RobloxCrashHandler.exe"
    ],
    "robolox": [
        "RobloxPlayerBeta.exe", "RobloxPlayer.exe", "RobloxPlayerLauncher.exe",
        "RobloxStudioBeta.exe", "RobloxStudioInstaller.exe", "RobloxStudio.exe",
        "RobloxCrashHandler.exe"
    ],
    "robolox player": [
        "RobloxPlayerBeta.exe", "RobloxPlayer.exe", "RobloxPlayerLauncher.exe",
        "RobloxCrashHandler.exe"
    ],
    "roblox studio": ["RobloxStudioBeta.exe", "RobloxStudioInstaller.exe", "RobloxStudio.exe"],
    "robolox studio": ["RobloxStudioBeta.exe", "RobloxStudioInstaller.exe", "RobloxStudio.exe"],
    "opera": ["opera.exe"],
    "opera gx": ["opera.exe"],
    "opera gx browser": ["opera.exe"],
    "notepad++": ["notepad++.exe"],
    "notepad plus plus": ["notepad++.exe"],
    "intellij": ["idea64.exe"],
    "intellij idea": ["idea64.exe"],
    "postman": ["Postman.exe"],
    "docker": ["Docker Desktop.exe"],
    "docker desktop": ["Docker Desktop.exe"],
    "dev c++": ["devcpp.exe"],
    "devcpp": ["devcpp.exe"],
    "minecraft": ["Minecraft.Windows.exe", "javaw.exe"],
    "vlc": ["vlc.exe"],
    "steam": ["steam.exe", "steamwebhelper.exe"],
    "epic games": ["EpicGamesLauncher.exe"],
    "zoom": ["Zoom.exe"],
    "slack": ["slack.exe"],
    "teams": ["ms-teams.exe", "Teams.exe"],
    "word": ["WINWORD.EXE"],
    "excel": ["EXCEL.EXE"],
    "powerpoint": ["POWERPNT.EXE"],
    "paint": ["mspaint.exe"],
    "camera": ["WindowsCamera.exe"],
    "settings": ["SystemSettings.exe"],
    "windows settings": ["SystemSettings.exe"],
    "store": ["WinStore.App.exe"],
    "microsoft store": ["WinStore.App.exe"],
    "terminal": ["WindowsTerminal.exe"],
    "powershell": ["powershell.exe"],
    "cmd": ["cmd.exe"],
    "lenovo vantage": ["LenovoVantage.exe", "LenovoCompanion.exe"],
    "vantage": ["LenovoVantage.exe", "LenovoCompanion.exe"],
    "netflix": ["Netflix.exe"],
}


def _scan_start_menu_shortcuts() -> dict[str, str]:
    """Instantly scans Start Menu shortcuts (<0.05 seconds)."""
    apps: dict[str, str] = {}
    if os.name == "nt":
        shortcut_dirs = [
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs")
        ]
        for sdir in shortcut_dirs:
            if os.path.exists(sdir):
                for root, _, files in os.walk(sdir):
                    for f in files:
                        if f.lower().endswith(".lnk"):
                            clean_app_name = os.path.splitext(f)[0].lower()
                            clean_key = re.sub(r"[^\w\s]", "", clean_app_name).strip()
                            full_path = os.path.join(root, f)
                            if clean_app_name not in apps:
                                apps[clean_app_name] = full_path
                            if clean_key and clean_key not in apps:
                                apps[clean_key] = full_path
    return apps


def _load_installed_apps_catalog() -> dict[str, str]:
    """Loads all Windows Store & native desktop applications from cache and Start Menu shortcuts."""
    catalog: dict[str, str] = {}
    # 1. Load from installed_apps.json if present
    json_path = os.path.join(os.path.dirname(__file__), "installed_apps.json")
    if os.path.exists(json_path):
        try:
            import json
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, str) and v.lower().startswith("shell:appsfolder"):
                            catalog[k] = re.sub(r"^shell:appsfolder[\\/]+", r"shell:AppsFolder\\", v, flags=re.IGNORECASE)
                        else:
                            catalog[k] = v
        except Exception as e:
            logger.warning(f"Error loading installed_apps.json: {e}")

    # 2. Supplement with Start Menu shortcuts
    shortcuts = _scan_start_menu_shortcuts()
    for k, v in shortcuts.items():
        if k not in catalog:
            catalog[k] = v

    return catalog


# In-memory catalog of all installed Windows applications
# Synchronously initialized from installed_apps.json + Start Menu shortcuts for 0ms lookup
_INSTALLED_APPS_CACHE: dict[str, str] = _load_installed_apps_catalog()
_CACHE_INITIALIZED = True


def _refresh_installed_apps():
    """Dynamically supplements _INSTALLED_APPS_CACHE with Store/AppX apps via Get-StartApps and persists cache."""
    global _INSTALLED_APPS_CACHE
    if os.name == "nt":
        try:
            import json
            ps_cmd = "Get-StartApps | ConvertTo-Json -Compress"
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=15,
                check=False
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout)
                items = data if isinstance(data, list) else [data]
                updated = False
                for item in items:
                    name = item.get("Name", "").strip().lower()
                    clean_k = re.sub(r"[^\w\s]", "", name).strip()
                    app_id = item.get("AppID", "").strip()
                    if name and app_id:
                        target = app_id if (os.path.exists(app_id) or ":\\" in app_id or app_id.lower().endswith((".exe", ".lnk", ".bat", ".cmd"))) else f"shell:AppsFolder\\{app_id}"
                        if name not in _INSTALLED_APPS_CACHE:
                            _INSTALLED_APPS_CACHE[name] = target
                            updated = True
                        if clean_k and clean_k not in _INSTALLED_APPS_CACHE:
                            _INSTALLED_APPS_CACHE[clean_k] = target
                            updated = True
                
                if updated:
                    json_path = os.path.join(os.path.dirname(__file__), "installed_apps.json")
                    try:
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump(_INSTALLED_APPS_CACHE, f, indent=2, ensure_ascii=False)
                    except Exception as e:
                        logger.debug(f"Failed to persist installed_apps.json: {e}")
        except Exception as e:
            logger.debug(f"Error querying Get-StartApps: {e}")


# Further supplement with Store apps in background thread
import threading
threading.Thread(target=_refresh_installed_apps, daemon=True, name="VikramAppCatalog").start()


class ApplicationExecutor:
    @classmethod
    def _launch_target(cls, target: str) -> bool:
        """
        Launches an application target safely on Windows.
        Handles shell:AppsFolder targets (Store & UWP apps), native .exe paths, .lnk shortcuts, and protocols.
        """
        if not target:
            return False
        target_clean = target.strip()
        if target_clean.lower().startswith("shell:appsfolder"):
            target_clean = re.sub(r"^shell:appsfolder[\\/]+", r"shell:AppsFolder\\", target_clean, flags=re.IGNORECASE)

        # 1. os.startfile (fastest, natively handles shell:AppsFolder, .lnk, .exe, and URI protocols)
        if hasattr(os, "startfile"):
            try:
                os.startfile(target_clean)
                return True
            except Exception as e:
                logger.debug(f"os.startfile failed for {target_clean}: {e}")

        # 2. If it's a shell:AppsFolder app, invoke via explorer.exe
        if target_clean.lower().startswith("shell:"):
            try:
                subprocess.Popen(["explorer.exe", target_clean])
                return True
            except Exception as e:
                logger.debug(f"explorer.exe launch failed for {target_clean}: {e}")

        # 3. Direct executable launch or cmd /c start
        try:
            if os.path.exists(target_clean):
                subprocess.Popen([target_clean], shell=True)
                return True
            subprocess.Popen(["cmd", "/c", "start", "", target_clean], shell=True)
            return True
        except Exception as e:
            logger.error(f"Command start failed for {target_clean}: {e}")
            return False

    @classmethod
    def launch(cls, app_name: str) -> tuple[bool, str]:
        """
        Launches ANY authorized application via:
        1. Direct specialized handlers (File Explorer, Chrome, Gmail)
        2. Dynamic Windows Installed Apps Catalog (Store/AppX apps via shell:AppsFolder, Win32 apps)
        3. Native Windows URI protocol handlers
        4. Standard PATH and Windows Program directories
        5. Web fallback (e.g. WhatsApp Web)
        """
        clean_name = app_name.lower().strip()
        clean_name = re.sub(r"^(?:the|my|an|a)\s+", "", clean_name).strip()
        for noise in ["the app ", "the application ", "the program ", "the window ", "the ", "app ", "application ", "my "]:
            if clean_name.startswith(noise):
                clean_name = clean_name[len(noise):].strip()
        for noise in [" application", " app", " window", " program", " please", " now", " for me"]:
            if clean_name.endswith(noise):
                clean_name = clean_name[:-len(noise)].strip()

        # Normalize colloquial aliases & speech variations
        alias_map = {
            "whatsup": "whatsapp",
            "whats up": "whatsapp",
            "whatsapp desktop": "whatsapp",
            "vscode": "visual studio code",
            "vs code": "visual studio code",
            "code": "visual studio code",
            "visual studio": "visual studio code",
            "calc": "calculator",
            "taskmgr": "task manager",
            "vantage": "lenovo vantage",
            "lenovo": "lenovo vantage",
            "store": "microsoft store",
            "windows store": "microsoft store",
            "edge": "microsoft edge",
            "chrome": "google chrome",
            "browser": "google chrome",
            "file explore": "file explorer",
            "explore": "file explorer",
            "files": "file explorer",
            "my files": "file explorer",
            "this pc": "file explorer",
            "my computer": "file explorer",
            "word": "word",
            "ms word": "word",
            "microsoft word": "word",
            "excel": "excel",
            "ms excel": "excel",
            "microsoft excel": "excel",
            "powerpoint": "powerpoint",
            "ms powerpoint": "powerpoint",
            "power point": "powerpoint",
            "ppt": "powerpoint",
            "roblox": "roblox player",
            "robolox": "roblox player",
            "robolox player": "roblox player",
            "roblox player": "roblox player",
            "roblox studio": "roblox studio",
            "robolox studio": "roblox studio",
            "opera": "opera gx browser",
            "opera gx": "opera gx browser",
            "notepad++": "notepad++",
            "notepad plus plus": "notepad++",
            "intellij": "intellij idea",
            "dev c++": "dev-c++",
            "devcpp": "dev-c++",
            "movies": "netflix",
            "vlc player": "vlc media player",
            "vlc": "vlc media player",
            "epic": "epic games launcher",
            "epic games": "epic games launcher",
            "cmd": "command prompt",
            "command prompt": "command prompt",
        }
        clean_name = alias_map.get(clean_name, clean_name)

        # 1. Dedicated Direct Handlers
        # Windows File Explorer direct launcher (opens user home folder in visible window)
        explorer_aliases = [
            "file explorer", "explorer", "file explore", "explore", "files", "my files",
            "this pc", "my computer", "file manager", "folder", "open file explorer",
            "open file explore", "open explorer", "open files", "show files"
        ]
        if clean_name in explorer_aliases:
            target_folder = os.environ.get("USERPROFILE", "C:\\")
            try:
                subprocess.Popen(["explorer.exe", target_folder])
                return True, "Opening File Explorer, Master."
            except Exception:
                try:
                    if hasattr(os, "startfile"):
                        os.startfile(target_folder)
                    return True, "Opening File Explorer, Master."
                except Exception as inner_e:
                    logger.error(f"Error launching File Explorer: {inner_e}")
                    return False, f"Failed to open File Explorer: {inner_e}"

        if clean_name in ["downloads", "my downloads", "download"]:
            target_folder = os.path.expanduser(r"~\Downloads")
            try:
                subprocess.Popen(["explorer.exe", target_folder])
                return True, "Opening Downloads, Master."
            except Exception:
                try:
                    if hasattr(os, "startfile"):
                        os.startfile(target_folder)
                    return True, "Opening Downloads, Master."
                except Exception as inner_e:
                    logger.error(f"Error launching Downloads: {inner_e}")
                    return False, f"Failed to open Downloads: {inner_e}"

        if clean_name in ["documents", "my documents", "document"]:
            target_folder = os.path.expanduser(r"~\Documents")
            try:
                subprocess.Popen(["explorer.exe", target_folder])
                return True, "Opening Documents, Master."
            except Exception as inner_e:
                return False, f"Failed to open Documents: {inner_e}"

        if clean_name in ["desktop", "my desktop"]:
            target_folder = os.path.expanduser(r"~\Desktop")
            try:
                subprocess.Popen(["explorer.exe", target_folder])
                return True, "Opening Desktop, Master."
            except Exception as inner_e:
                return False, f"Failed to open Desktop: {inner_e}"

        if clean_name in ["google chrome", "chrome", "browser"]:
            from .browser_executor import BrowserExecutor
            return BrowserExecutor.open_chrome()

        if clean_name in ["gmail", "email", "mail", "my email", "inbox"]:
            from .browser_executor import BrowserExecutor
            return BrowserExecutor.open_website("gmail")

        # 2. Dynamic Installed Windows Apps Catalog (Store/AppX & Win32 applications)
        # 2a. Exact match
        if clean_name in _INSTALLED_APPS_CACHE:
            target = _INSTALLED_APPS_CACHE[clean_name]
            if cls._launch_target(target):
                display_title = clean_name.title()
                if clean_name == "whatsapp":
                    display_title = "WhatsApp"
                return True, f"Opening {display_title}, Master."

        # 2b. Boundary / Prefix / Substring match in installed apps
        for installed_name, target in _INSTALLED_APPS_CACHE.items():
            if (
                clean_name == installed_name
                or f" {clean_name} " in f" {installed_name} "
                or installed_name.startswith(f"{clean_name} ")
                or installed_name.endswith(f" {clean_name}")
                or (len(clean_name) >= 4 and clean_name in installed_name)
            ):
                if cls._launch_target(target):
                    display_title = installed_name.title()
                    if "whatsapp" in installed_name:
                        display_title = "WhatsApp"
                    return True, f"Opening {display_title}, Master."

        # 3. Native Windows URI Protocol Handlers (Settings, Store, Clock, Camera)
        uri_target = URI_MAP.get(clean_name)
        if uri_target or clean_name.endswith(":"):
            uri = uri_target or clean_name
            if cls._launch_target(uri):
                return True, f"Opening {clean_name.title()}, Master."

        # 4. Standard Executable Discovery & Well-Known Paths
        candidates = APP_MAP.get(clean_name, [clean_name])
        for cand in candidates:
            found = shutil.which(cand)
            if not found and os.name == "nt":
                paths = [
                    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd"),
                    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
                    os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
                    os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
                    os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
                    os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe --processStart Discord.exe"),
                    os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
                    os.path.expandvars(r"%WINDIR%\system32\notepad.exe"),
                    os.path.expandvars(r"%WINDIR%\explorer.exe"),
                    os.path.expandvars(r"%WINDIR%\system32\calc.exe"),
                    os.path.expandvars(r"%WINDIR%\system32\taskmgr.exe"),
                    os.path.expandvars(r"%WINDIR%\system32\mspaint.exe"),
                    os.path.expandvars(r"%ProgramFiles%\VideoLAN\VLC\vlc.exe"),
                    os.path.expandvars(r"%ProgramFiles(x86)%\VideoLAN\VLC\vlc.exe"),
                ]
                for p in paths:
                    if cand.lower() in p.lower() and os.path.exists(p.split()[0]):
                        found = p
                        break

            if found:
                try:
                    subprocess.Popen(found, shell=True)
                    return True, f"Opening {clean_name.title()}, Master."
                except Exception as e:
                    logger.error(f"Error launching {found}: {e}")
                    return False, f"Failed to start {clean_name}: {e}"

        # 5. Generic attempt if executable exists on system
        where_check = shutil.which(clean_name) or shutil.which(f"{clean_name}.exe")
        if where_check:
            try:
                subprocess.Popen([where_check], shell=True)
                return True, f"Opening {clean_name.title()}, Master."
            except Exception as e:
                logger.error(f"Error launching {where_check}: {e}")
                return False, f"Failed to start {clean_name}: {e}"

        return False, f"I couldn't locate {clean_name.title()} on your system, Master."

    @classmethod
    def _send_alt_f4(cls):
        """Simulates Alt+F4 keystroke safely."""
        if os.name == "nt":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                VK_MENU = 0x12  # Alt
                VK_F4 = 0x73    # F4
                KEYEVENTF_KEYUP = 0x0002
                user32.keybd_event(VK_MENU, 0, 0, 0)
                user32.keybd_event(VK_F4, 0, 0, 0)
                user32.keybd_event(VK_F4, 0, KEYEVENTF_KEYUP, 0)
                user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
            except Exception as e:
                logger.debug(f"Alt+F4 error: {e}")

    @classmethod
    def close_tab(cls) -> tuple[bool, str]:
        """Closes the current browser or application tab using Ctrl+W."""
        if os.name == "nt":
            try:
                import ctypes
                user32 = ctypes.windll.user32
                VK_CONTROL = 0x11
                VK_W = 0x57
                KEYEVENTF_KEYUP = 0x0002
                user32.keybd_event(VK_CONTROL, 0, 0, 0)
                user32.keybd_event(VK_W, 0, 0, 0)
                user32.keybd_event(VK_W, 0, KEYEVENTF_KEYUP, 0)
                user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
                return True, "Closed current tab, Master."
            except Exception as e:
                logger.debug(f"Tab close error: {e}")
                return False, f"Failed to close tab: {e}"
        return False, "Tab close is only supported on Windows."

    @classmethod
    def close_active_window(cls) -> tuple[bool, str]:
        """
        Gracefully closes the currently focused/foreground user application window on Windows:
        1. Identifies foreground window handle (HWND) and process ID.
        2. Protects Windows core shell, background services, and DOOM AI backend from accidental termination.
        3. If foreground is DOOM AI HUD or shell, traverses to the top user application window.
        4. Posts WM_SYSCOMMAND (SC_CLOSE) and WM_CLOSE, and sends Alt+F4.
        """
        if os.name != "nt":
            return False, "Active window closing is only supported on Windows."
        try:
            import ctypes
            from ctypes import wintypes
            import time

            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                cls._send_alt_f4()
                return True, "Closed active window."

            # Get Window Title & Class
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value.strip()

            class_buff = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_buff, 256)
            class_name = class_buff.value.strip()

            # Get Process Name
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            proc_name = ""
            if pid.value:
                try:
                    proc = psutil.Process(pid.value)
                    proc_name = proc.name().lower()
                except Exception:
                    pass

            protected_foreground = {"python.exe", "pythonw.exe", "svchost.exe", "csrss.exe", "dwm.exe", "lsass.exe"}

            # If foreground window belongs to DOOM AI HUD or desktop shell, traverse to find the top user window
            if proc_name in protected_foreground or "doom" in title.lower() or "vikram" in title.lower() or class_name in ["Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"]:
                curr = hwnd
                for _ in range(15):
                    curr = user32.GetWindow(curr, 2)  # GW_HWNDNEXT = 2
                    if not curr or not user32.IsWindow(curr) or not user32.IsWindowVisible(curr):
                        continue
                    c_buff = ctypes.create_unicode_buffer(256)
                    user32.GetClassNameW(curr, c_buff, 256)
                    cn = c_buff.value.strip()
                    if cn in ["Progman", "WorkerW", "Shell_TrayWnd", "Shell_SecondaryTrayWnd"]:
                        continue
                    p_id = wintypes.DWORD()
                    user32.GetWindowThreadProcessId(curr, ctypes.byref(p_id))
                    p_name = ""
                    if p_id.value:
                        try:
                            p_name = psutil.Process(p_id.value).name().lower()
                        except Exception:
                            pass
                    if p_name and p_name not in protected_foreground:
                        hwnd = curr
                        proc_name = p_name
                        l = user32.GetWindowTextLengthW(hwnd)
                        b = ctypes.create_unicode_buffer(l + 1)
                        user32.GetWindowTextW(hwnd, b, l + 1)
                        title = b.value.strip()
                        break

            # Send WM_SYSCOMMAND / SC_CLOSE (0x0112 / 0xF060) and WM_CLOSE (0x0010)
            WM_SYSCOMMAND = 0x0112
            SC_CLOSE = 0xF060
            WM_CLOSE = 0x0010
            user32.PostMessageW(hwnd, WM_SYSCOMMAND, SC_CLOSE, 0)
            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)

            # Bring to foreground and send Alt+F4
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.04)
            cls._send_alt_f4()

            # If modern UWP process (Settings, Calculator, etc.), kill process directly if still present
            if proc_name in ["systemsettings.exe", "systemsettingsadminflows.exe", "calculatorapp.exe", "calc.exe"]:
                try:
                    for p in psutil.process_iter(['pid', 'name']):
                        if p.info['name'].lower() == proc_name:
                            p.kill()
                except Exception:
                    pass

            clean_display = title or proc_name.replace(".exe", "").title() or "active window"
            if len(clean_display) > 30:
                clean_display = clean_display[:30] + "..."
            return True, f"Closed {clean_display}."
        except Exception as e:
            logger.debug(f"Error closing active window: {e}")
            cls._send_alt_f4()
            return True, "Closed active window."

    @classmethod
    def close_file_explorer(cls) -> tuple[bool, str]:
        """
        Closes all open Windows File Explorer folder windows without terminating the desktop taskbar:
        1. Enumerates all visible top-level windows in the system using Win32 API.
        2. Filters specifically for 'CabinetWClass' (File Explorer folder windows) and 'ExploreWClass'.
        3. Strictly protects 'Progman', 'WorkerW', 'Shell_TrayWnd', and 'Shell_SecondaryTrayWnd' (Desktop/Taskbar).
        4. Sends WM_CLOSE (0x0010) and WM_SYSCOMMAND/SC_CLOSE (0xF060) to each folder window.
        5. Also attempts Shell.Application COM Quit() as secondary fallback.
        """
        if os.name != "nt":
            return False, "File Explorer is only available on Windows."

        closed_count = 0
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            WM_CLOSE = 0x0010
            WM_SYSCOMMAND = 0x0112
            SC_CLOSE = 0xF060

            explorer_hwnds: list[int] = []

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

            def _enum_windows_cb(hwnd, lparam):
                if user32.IsWindow(hwnd):
                    class_buff = ctypes.create_unicode_buffer(256)
                    user32.GetClassNameW(hwnd, class_buff, 256)
                    cname = class_buff.value.strip()
                    if cname in ["CabinetWClass", "ExploreWClass"]:
                        explorer_hwnds.append(hwnd)
                return True

            cb = WNDENUMPROC(_enum_windows_cb)
            user32.EnumWindows(cb, 0)

            for hwnd in explorer_hwnds:
                try:
                    user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
                    user32.PostMessageW(hwnd, WM_SYSCOMMAND, SC_CLOSE, 0)
                    res = ctypes.c_ulong()
                    user32.SendMessageTimeoutW(hwnd, WM_CLOSE, 0, 0, 0x0002, 200, ctypes.byref(res))
                    closed_count += 1
                except Exception:
                    pass

            # If active foreground window is File Explorer, send Alt+F4
            fg_hwnd = user32.GetForegroundWindow()
            if fg_hwnd:
                fg_class = ctypes.create_unicode_buffer(256)
                user32.GetClassNameW(fg_hwnd, fg_class, 256)
                if fg_class.value.strip() in ["CabinetWClass", "ExploreWClass"]:
                    cls._send_alt_f4()

        except Exception as e:
            logger.debug(f"Win32 EnumWindows error closing File Explorer: {e}")

        # Secondary fallback: Shell.Application COM object
        try:
            ps_code = "$sh = New-Object -ComObject Shell.Application; foreach ($w in $sh.Windows()) { try { $w.Quit() } catch {} }"
            subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_code],
                capture_output=True,
                timeout=3,
                check=False
            )
        except Exception:
            pass

        return True, "Closed File Explorer."

    @classmethod
    def close_all_apps(cls) -> tuple[bool, str]:
        """
        Closes all running user applications cleanly (browsers, code editors, messaging, games, office, etc.)
        while strictly preserving system services and DOOM AI background processes.
        """
        # Close open File Explorer folder windows cleanly
        cls.close_file_explorer()

        user_app_targets = [
            "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe",
            "idea64.exe", "devcpp.exe", "notepad++.exe", "notepad.exe",
            "WhatsApp.Root.exe", "WhatsApp.exe", "Discord.exe", "Spotify.exe", "Telegram.exe",
            "RobloxPlayerBeta.exe", "RobloxPlayer.exe", "RobloxStudioBeta.exe",
            "WINWORD.EXE", "EXCEL.EXE", "POWERPNT.EXE", "mspaint.exe",
            "vlc.exe", "Zoom.exe", "Teams.exe", "ms-teams.exe", "CalculatorApp.exe", "calc.exe",
            "LenovoVantage.exe", "LenovoCompanion.exe",
            "SystemSettings.exe", "SystemSettingsAdminFlows.exe"
        ]

        closed_any = False

        # Terminate via in-process psutil
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pname = proc.info.get('name', '')
                if not pname:
                    continue
                pname_lower = pname.lower()
                if any(t.lower() == pname_lower for t in user_app_targets) or "systemsettings" in pname_lower:
                    proc.kill()
                    closed_any = True
            except Exception:
                pass

        for target in user_app_targets:
            try:
                res = subprocess.run(
                    ["taskkill", "/F", "/T", "/IM", target],
                    capture_output=True,
                    text=True,
                    timeout=1,
                    check=False
                )
                if res.returncode == 0:
                    closed_any = True
            except Exception:
                pass

        return True, "Closed all running applications, Master."

    @classmethod
    def close(cls, app_name: str) -> tuple[bool, str]:
        """
        Gracefully terminates running applications across Windows:
        Handles active window, all applications, tab closing, Win32, Windows Store/AppX (WhatsApp, Vantage, Calculator),
        File Explorer windows, and multi-process applications (Chrome, Discord, VS Code).
        """
        clean_name = app_name.lower().strip()

        # 1. Strip common conversational filler words
        for noise in ["the app ", "the application ", "the program ", "the window ", "the ", "app ", "application ", "my "]:
            if clean_name.startswith(noise):
                clean_name = clean_name[len(noise):].strip()
        for noise in [" application", " app", " window", " program", " browser", " please", " now", " for me"]:
            if clean_name.endswith(noise):
                clean_name = clean_name[:-len(noise)].strip()

        # 2. Check for Active Window / Standalone Close
        if not clean_name or clean_name in ["active", "current", "window", "app", "this", "it", "that", "foreground", "screen", "active window", "current app", "this app"]:
            return cls.close_active_window()

        # 3. Check for Tab Close
        if clean_name in ["tab", "current tab", "the tab", "browser tab", "active tab"]:
            return cls.close_tab()

        # 4. Check for All Apps Close
        if clean_name in ["all", "all apps", "all applications", "all windows", "apps", "everything", "all programs", "app for apps", "apps for apps"]:
            return cls.close_all_apps()

        # 5. Check for Website / Tab Close (e.g. "close youtube", "close google")
        if clean_name in ["youtube", "google", "gmail", "reddit", "stackoverflow", "chatgpt", "github"]:
            return cls.close_tab()

        # 6. Alias resolution
        alias_map = {
            "whatsapp desktop": "whatsapp",
            "google chrome": "chrome",
            "microsoft edge": "edge",
            "visual studio code": "vs code",
            "vscode": "vs code",
            "code": "vs code",
            "file": "file explorer",
            "the file": "file explorer",
            "my file": "file explorer",
            "file explore": "file explorer",
            "file explorer": "file explorer",
            "files": "file explorer",
            "the files": "file explorer",
            "my files": "file explorer",
            "explorer": "file explorer",
            "explore": "file explorer",
            "folder": "file explorer",
            "folders": "file explorer",
            "directory": "file explorer",
            "directories": "file explorer",
            "file manager": "file explorer",
            "this pc": "file explorer",
            "my computer": "file explorer",
            "computer": "file explorer",
            "downloads folder": "file explorer",
            "documents folder": "file explorer",
            "downloads": "file explorer",
            "documents": "file explorer",
            "calc": "calculator",
            "taskmgr": "task manager",
            "vantage": "lenovo vantage",
            "lenovo": "lenovo vantage",
            "roblox player": "roblox",
            "robolox": "roblox",
            "robolox player": "roblox",
            "roblox studio": "roblox",
            "robolox studio": "roblox",
            "opera gx": "opera",
            "opera gx browser": "opera",
            "notepad++": "notepad++",
            "notepad plus plus": "notepad++",
            "intellij": "idea64",
            "intellij idea": "idea64",
            "setting": "settings",
            "windows settings": "settings",
            "pc settings": "settings",
        }
        clean_name = alias_map.get(clean_name, clean_name)

        # 7. Settings App Special Handling (Win10/11 UWP Settings)
        if clean_name in ["settings", "setting", "windows settings", "pc settings"]:
            # 1. Kill via psutil directly
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    pname = proc.info.get('name', '').lower()
                    if "systemsettings" in pname:
                        proc.kill()
                except Exception:
                    pass

            # 2. Taskkill
            try:
                subprocess.run(["taskkill", "/F", "/T", "/IM", "SystemSettings.exe"], capture_output=True, timeout=1, check=False)
                subprocess.run(["taskkill", "/F", "/T", "/IM", "SystemSettingsAdminFlows.exe"], capture_output=True, timeout=1, check=False)
            except Exception:
                pass

            # 3. Win32 WM_SYSCOMMAND / SC_CLOSE & Alt+F4 to any settings window
            try:
                import ctypes
                from ctypes import wintypes
                user32 = ctypes.windll.user32
                WM_SYSCOMMAND = 0x0112
                SC_CLOSE = 0xF060
                WM_CLOSE = 0x0010

                def _close_settings_cb(hwnd, lparam):
                    if user32.IsWindow(hwnd):
                        length = user32.GetWindowTextLengthW(hwnd)
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        title = buff.value.strip().lower()

                        class_buff = ctypes.create_unicode_buffer(256)
                        user32.GetClassNameW(hwnd, class_buff, 256)
                        cname = class_buff.value.strip()

                        if "settings" in title or (cname == "ApplicationFrameWindow" and "settings" in title):
                            user32.PostMessageW(hwnd, WM_SYSCOMMAND, SC_CLOSE, 0)
                            user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
                            user32.SetForegroundWindow(hwnd)
                            cls._send_alt_f4()
                    return True

                cb = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(_close_settings_cb)
                user32.EnumWindows(cb, 0)
            except Exception:
                pass

            return True, "Closed Settings, Master."

        # 8. File Explorer Special Handling (Closes open folder windows without crashing desktop taskbar)
        if clean_name in [
            "file explorer", "file", "files", "my file", "my files", "the file", "the files",
            "file explore", "explore", "explorer", "folder", "folders", "directory", "directories",
            "file manager", "this pc", "my computer", "computer", "downloads", "documents"
        ]:
            return cls.close_file_explorer()

        # 8. Resolve Target Process Images
        targets: list[str] = list(PROCESS_NAMES.get(clean_name, []))
        if not targets:
            targets.append(f"{clean_name}.exe")
            targets.append(clean_name)

        # Check installed apps cache for executable name
        for k, v in _INSTALLED_APPS_CACHE.items():
            if clean_name == k or (len(clean_name) >= 4 and clean_name in k):
                for exe_match in re.findall(r"[\w-]+\.exe", v, re.IGNORECASE):
                    if exe_match not in targets:
                        targets.append(exe_match)

        # Protected system processes and Windows services that must NEVER be terminated
        # (Terminating Windows Services causes Windows SCM to automatically restart and reopen them)
        protected = {
            "svchost.exe", "csrss.exe", "smss.exe", "services.exe", "lsass.exe",
            "wininit.exe", "winlogon.exe", "dwm.exe", "system", "idle",
            "registry", "python.exe", "pythonw.exe", "powershell.exe", "cmd.exe", "explorer.exe",
            "conhost.exe", "fontdrvhost.exe", "sihost.exe", "ctfmon.exe", "runtimebroker.exe",
            "searchapp.exe", "searchhost.exe", "shellexperiencehost.exe", "startmenuexperiencehost.exe",
            "systemsettingsbroker.exe", "securityhealthservice.exe", "audiodg.exe", "spoolsv.exe",
            "lenovovantageservice.exe", "lenovoutilityservice.exe", "lenovo.modern.imcontroller.exe",
            "lenovonow.task.exe"
        }

        # Filter out background Windows services from targets to prevent auto-restart loops
        filtered_targets = []
        for t in targets:
            t_lower = t.lower()
            if t_lower in protected:
                continue
            if "service" in t_lower or "imcontroller" in t_lower or "daemon" in t_lower:
                continue
            filtered_targets.append(t)
        targets = filtered_targets

        # 9. Stage 1: Ultra-fast kernel taskkill by image name (<400ms)
        for target in targets:
            if not target.lower().endswith(".exe"):
                continue
            if target.lower() in protected:
                continue
            try:
                res = subprocess.run(
                    ["taskkill", "/F", "/T", "/IM", target],
                    capture_output=True,
                    text=True,
                    timeout=1,
                    check=False
                )
                if res.returncode == 0:
                    display_name = clean_name.title()
                    if clean_name == "chrome":
                        display_name = "Google Chrome"
                    elif clean_name in ["vs code", "vscode"]:
                        display_name = "Visual Studio Code"
                    elif clean_name == "whatsapp":
                        display_name = "WhatsApp"
                    elif clean_name in ["lenovo vantage", "vantage"]:
                        display_name = "Lenovo Vantage"
                    return True, f"Closed {display_name}."
            except Exception as e:
                logger.debug(f"Taskkill /IM error for {target}: {e}")

        # 10. Search active running processes for matching UI names
        active_pids: list[int] = []
        is_roblox = clean_name in ["roblox", "robolox"]
        is_vantage = clean_name in ["vantage", "lenovo vantage"]

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pname = proc.info.get('name')
                if not pname:
                    continue
                pname_lower = pname.lower()
                if pname_lower in protected:
                    continue
                if "service" in pname_lower or "imcontroller" in pname_lower or "daemon" in pname_lower:
                    continue

                # Check if process name matches target or clean_name
                matches = (
                    any(t.lower() == pname_lower for t in targets) or
                    pname_lower == f"{clean_name}.exe" or
                    (is_roblox and "roblox" in pname_lower) or
                    (is_vantage and "lenovovantage" in pname_lower and "service" not in pname_lower) or
                    (len(clean_name) >= 4 and clean_name in pname_lower and "service" not in pname_lower) or
                    (len(clean_name) >= 4 and pname_lower.startswith(clean_name))
                )
                if matches:
                    if pname not in targets:
                        targets.append(pname)
                    active_pids.append(proc.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        terminated_count = 0

        # 11. Stage 2: Ultra-fast in-process psutil termination (<1ms Win32 TerminateProcess)
        if active_pids:
            for pid in active_pids:
                try:
                    proc = psutil.Process(pid)
                    if proc.name().lower() in protected:
                        continue
                    for child in proc.children(recursive=True):
                        try:
                            child.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    proc.kill()
                    terminated_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # If all matching processes terminated, exit instantly
            if not any(psutil.pid_exists(p) for p in active_pids):
                display_name = clean_name.title()
                if clean_name == "chrome":
                    display_name = "Google Chrome"
                elif clean_name in ["vs code", "vscode"]:
                    display_name = "Visual Studio Code"
                elif clean_name == "whatsapp":
                    display_name = "WhatsApp"
                elif clean_name in ["lenovo vantage", "vantage"]:
                    display_name = "Lenovo Vantage"
                return True, f"Closed {display_name}."

        # 12. Stage 3: Fast Name-based taskkill for Win32 targets
        for target in targets:
            if not target.lower().endswith(".exe"):
                continue
            if target.lower() in protected:
                continue
            try:
                res = subprocess.run(
                    ["taskkill", "/F", "/T", "/IM", target],
                    capture_output=True,
                    text=True,
                    timeout=1,
                    check=False
                )
                if res.returncode == 0:
                    terminated_count += 1
                    break
            except Exception as e:
                logger.debug(f"Taskkill /IM error for {target}: {e}")

        # 13. Stage 4: PID-based taskkill for any lingering processes
        still_alive = [p for p in active_pids if psutil.pid_exists(p)]
        if still_alive:
            for pid in still_alive:
                try:
                    res = subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        capture_output=True,
                        text=True,
                        timeout=1,
                        check=False
                    )
                    if res.returncode == 0:
                        terminated_count += 1
                except Exception as e:
                    logger.debug(f"PID taskkill error for PID {pid}: {e}")

        # 14. Stage 5: PowerShell Stop-Process fallback ONLY if processes still persist
        final_check = [p for p in active_pids if psutil.pid_exists(p)]
        if final_check:
            pids_str = ",".join(str(p) for p in final_check)
            try:
                ps_cmd = f"Stop-Process -Id {pids_str} -Force -ErrorAction SilentlyContinue"
                subprocess.run(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                    capture_output=True,
                    timeout=2,
                    check=False
                )
                terminated_count += len(final_check)
            except Exception as e:
                logger.debug(f"PowerShell Stop-Process error: {e}")

        display_name = clean_name.title()
        if clean_name == "chrome":
            display_name = "Google Chrome"
        elif clean_name in ["vs code", "vscode"]:
            display_name = "Visual Studio Code"
        elif clean_name == "whatsapp":
            display_name = "WhatsApp"
        elif clean_name in ["lenovo vantage", "vantage"]:
            display_name = "Lenovo Vantage"

        if terminated_count > 0:
            return True, f"Closed {display_name}."
        return False, f"No running instance of {display_name} was found."
