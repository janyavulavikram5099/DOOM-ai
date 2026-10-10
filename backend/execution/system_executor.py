"""
VIKRAM AI - System Executor
Executes safe Windows OS operations:
- Genuine Windows session locking (ctypes.windll.user32.LockWorkStation)
- Volume and mute control
- Screenshots
- System power actions
"""

import ctypes
import logging
import os
import subprocess
import time
from datetime import datetime
from typing import Any

from PIL import ImageGrab

logger = logging.getLogger("vikram.execution.system")

SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "screenshots")


class SystemExecutor:
    @classmethod
    def lock_workstation(cls, lang: str = "en") -> tuple[bool, str]:
        """Locks the Windows workstation using the official Windows API."""
        msg = "ల్యాప్‌టాప్ లాక్ చేస్తున్నాను, మాస్టర్." if lang == "te" else "Locking your laptop, Master."
        try:
            if os.name == "nt":
                try:
                    from ..assistant.text_to_speech import tts
                    tts.speak(msg, lang=lang)
                    # Allow the deep male voice response to finish cleanly before locking the session
                    time.sleep(1.8)
                except Exception as ex:
                    logger.debug(f"Pre-lock speech notice: {ex}")

                user32 = ctypes.windll.User32
                success = user32.LockWorkStation()
                if success:
                    return True, msg
                else:
                    return False, "Failed to lock workstation via Windows API."
            else:
                return False, "Workstation lock is only supported on Windows."
        except Exception as e:
            logger.error(f"Error locking workstation: {e}")
            return False, f"Error locking workstation: {e}"

    @classmethod
    def is_workstation_locked(cls) -> bool:
        """
        Checks whether the Windows workstation is currently locked (Winlogon desktop active).
        """
        if os.name != "nt":
            return False
        try:
            from ctypes.wintypes import BOOL, DWORD, HANDLE, LPCWSTR
            user32 = ctypes.WinDLL('user32', use_last_error=True)
            open_desktop = user32.OpenDesktopW
            switch_desktop = user32.SwitchDesktop
            close_desktop = user32.CloseDesktop
            open_desktop.argtypes = (LPCWSTR, DWORD, BOOL, DWORD)
            open_desktop.restype = HANDLE
            switch_desktop.argtypes = (HANDLE,)
            switch_desktop.restype = DWORD
            close_desktop.argtypes = (HANDLE,)
            close_desktop.restype = DWORD

            # Attempt to open the default desktop with DESKTOP_SWITCHDESKTOP (0x0100)
            hnd_dt = open_desktop('default', 0, False, 0x0100)
            if not hnd_dt:
                return True
            result = switch_desktop(hnd_dt)
            close_desktop(hnd_dt)
            return result == 0
        except Exception as e:
            logger.debug(f"Error checking workstation lock status: {e}")
            return False

    @classmethod
    def unlock_request(cls) -> tuple[bool, str]:
        """
        Wakes the display from standby.
        Detects if Windows is locked (Winlogon desktop) to prevent keystroke leakage
        into the user's active browser HUD window.
        """
        from ..database.sqlite import db
        pin = db.get_setting("unlock_pin", "8055") or "8055"
        try:
            if os.name == "nt":
                user32 = ctypes.windll.user32
                # 1. Wake display from standby by moving mouse cursor
                user32.mouse_event(0x0001, 1, 1, 0, 0)
                time.sleep(0.05)
                user32.mouse_event(0x0001, -1, -1, 0, 0)

                # 2. Check if the workstation is locked on the secure Winlogon desktop
                locked = cls.is_workstation_locked()
                if locked:
                    logger.info("Windows workstation is locked (Winlogon desktop active).")
                    # Do NOT inject simulated keyboard keystrokes via keybd_event here.
                    # Because Windows UIPI blocks keystrokes into Winlogon, keybd_event
                    # would route them to the Default desktop (typing 8055 into the HUD!).
                    # Security rule: Never speak or disclose the PIN out loud when locked.
                    return True, "Enter pin yourself, Master."

                return True, "Enter pin yourself, Master."
        except Exception as e:
            logger.debug(f"Unlock execution notice: {e}")
        return True, "Enter pin yourself, Master."

    @classmethod
    def sleep_device(cls) -> tuple[bool, str]:
        """Puts Windows into sleep mode."""
        try:
            if os.name == "nt":
                subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
                return True, "Putting your computer to sleep."
            return False, "Sleep command only supported on Windows."
        except Exception as e:
            return False, f"Failed to put system to sleep: {e}"

    @classmethod
    def restart_device(cls) -> tuple[bool, str]:
        """Restarts Windows."""
        try:
            subprocess.run(["shutdown", "/r", "/t", "5"])
            return True, "Restarting your system in 5 seconds."
        except Exception as e:
            return False, f"Failed to initiate restart: {e}"

    @classmethod
    def shutdown_device(cls) -> tuple[bool, str]:
        """Shuts down Windows."""
        try:
            subprocess.run(["shutdown", "/s", "/t", "10"])
            return True, "Laptop is shutdown now, Master."
        except Exception as e:
            return False, f"Failed to initiate shutdown: {e}"

    _brightness_cache: int = 70
    _airplane_cache: bool = False

    @classmethod
    def _run_settings_script(cls, category: str, action: str = "status", level: int = -1, feature: str = "general") -> tuple[bool, str]:
        """Invokes the unified settings control PowerShell helper."""
        script_path = os.path.join(os.path.dirname(__file__), "settings_control.ps1")
        if not os.path.exists(script_path):
            return False, f"Settings script not found at {script_path}"
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                script_path,
                "-Category",
                category,
                "-Action",
                action,
                "-Level",
                str(level),
                "-Feature",
                feature
            ]
            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=8, startupinfo=startupinfo)
            output = res.stdout.strip()
            if "SUCCESS" in output or "FALLBACK" in output or res.returncode == 0:
                return True, output
            err = res.stderr.strip() or output
            return False, err
        except Exception as e:
            logger.error(f"Error executing settings script ({category}/{action}): {e}")
            return False, str(e)

    @classmethod
    def brightness_control(cls, action: str = "up", level: int = 15, lang: str = "en") -> tuple[bool, str]:
        """Controls display brightness with step increment, decrement, percentage set, max, and min."""
        action = action.lower().strip()
        current = cls._brightness_cache

        if action in ["up", "increase", "more", "raise", "boost"]:
            step = level if (level > 0 and level <= 50) else 15
            target = min(100, current + step)
            cls._brightness_cache = target
            cls._run_settings_script("brightness", "up", step)
            msg = f"బ్రైట్‌నెస్ {target} శాతానికి పెంచాను, మాస్టర్." if lang == "te" else f"Brightness increased to {target} percent, Master."
            return True, msg

        elif action in ["down", "decrease", "dim", "lower", "reduce"]:
            step = level if (level > 0 and level <= 50) else 15
            target = max(10, current - step)
            cls._brightness_cache = target
            cls._run_settings_script("brightness", "down", step)
            msg = f"బ్రైట్‌నెస్ {target} శాతానికి తగ్గించాను, మాస్టర్." if lang == "te" else f"Brightness decreased to {target} percent, Master."
            return True, msg

        elif action in ["max", "maximum", "full", "highest"]:
            cls._brightness_cache = 100
            cls._run_settings_script("brightness", "max", 100)
            msg = "బ్రైట్‌నెస్ గరిష్టంగా సెట్ చేశాను, మాస్టర్." if lang == "te" else "Brightness set to maximum, Master."
            return True, msg

        elif action in ["min", "minimum", "lowest"]:
            cls._brightness_cache = 10
            cls._run_settings_script("brightness", "min", 10)
            msg = "బ్రైట్‌నెస్ కనిష్టంగా సెట్ చేశాను, మాస్టర్." if lang == "te" else "Brightness set to minimum, Master."
            return True, msg

        elif action == "set":
            target = max(0, min(100, level))
            cls._brightness_cache = target
            cls._run_settings_script("brightness", "set", target)
            msg = f"బ్రైట్‌నెస్ {target} శాతానికి సెట్ చేశాను, మాస్టర్." if lang == "te" else f"Brightness set to {target} percent, Master."
            return True, msg

        elif action in ["status", "check"]:
            ok, out = cls._run_settings_script("brightness", "status")
            val = cls._brightness_cache
            if ok and "%" in out:
                try:
                    import re
                    m = re.search(r"(\d+)%", out)
                    if m:
                        val = int(m.group(1))
                        cls._brightness_cache = val
                except Exception:
                    pass
            msg = f"డిస్‌ప్లే బ్రైట్‌నెస్ ప్రస్తుతం {val} శాతం ఉంది, మాస్టర్." if lang == "te" else f"Display brightness is currently {val} percent, Master."
            return True, msg

        return False, f"Unknown brightness action: {action}"

    @classmethod
    def set_airplane_mode(cls, action: str = "on", lang: str = "en") -> tuple[bool, str]:
        """Turns Windows Airplane/Aeroplane Mode on or off by cutting or restoring network radios."""
        action = action.lower().strip()
        if action in ["on", "enable", "turn on", "switch on", "activate"]:
            cls._airplane_cache = True
            cls._run_settings_script("airplane", "on")
            msg = "ఏరోప్లేన్ మోడ్ ఆన్ చేయబడింది, మాస్టర్." if lang == "te" else "Airplane mode is now turned on, Master."
            return True, msg

        elif action in ["off", "disable", "turn off", "switch off", "deactivate"]:
            cls._airplane_cache = False
            cls._run_settings_script("airplane", "off")
            msg = "ఏరోప్లేన్ మోడ్ ఆఫ్ చేయబడింది, మాస్టర్." if lang == "te" else "Airplane mode is now turned off, Master."
            return True, msg

        elif action in ["status", "check"]:
            ok, out = cls._run_settings_script("airplane", "status")
            is_on = ("ON" in out.upper()) if ok else cls._airplane_cache
            if is_on:
                msg = "ఏరోప్లేన్ మోడ్ ప్రస్తుతం ఆన్‌లో ఉంది, మాస్టర్." if lang == "te" else "Airplane mode is currently turned on, Master."
            else:
                msg = "ఏరోప్లేన్ మోడ్ ప్రస్తుతం ఆఫ్‌లో ఉంది, మాస్టర్." if lang == "te" else "Airplane mode is currently turned off, Master."
            return True, msg

        return False, f"Unknown airplane mode action: {action}"

    @classmethod
    def accessibility_control(cls, action: str = "open", feature: str = "general", lang: str = "en") -> tuple[bool, str]:
        """Controls Windows Accessibility features: Magnifier, Narrator, On-Screen Keyboard, High Contrast."""
        action = action.lower().strip()
        feature = feature.lower().strip()

        if feature == "magnifier":
            if action in ["on", "open", "enable", "start"]:
                try:
                    subprocess.Popen(["magnify.exe"], shell=False)
                except Exception:
                    pass
                msg = "మాగ్నిఫైయర్ ఆన్ చేశాను, మాస్టర్." if lang == "te" else "Magnifier turned on, Master."
                return True, msg
            elif action in ["off", "close", "disable", "stop"]:
                try:
                    subprocess.run(["taskkill", "/IM", "magnify.exe", "/F"], capture_output=True)
                except Exception:
                    pass
                msg = "మాగ్నిఫైయర్ ఆఫ్ చేశాను, మాస్టర్." if lang == "te" else "Magnifier turned off, Master."
                return True, msg

        elif feature == "narrator":
            if action in ["on", "open", "enable", "start"]:
                try:
                    subprocess.Popen(["narrator.exe"], shell=False)
                except Exception:
                    pass
                msg = "నెరేటర్ ఆన్ చేశాను, మాస్టర్." if lang == "te" else "Narrator turned on, Master."
                return True, msg
            elif action in ["off", "close", "disable", "stop"]:
                try:
                    subprocess.run(["taskkill", "/IM", "narrator.exe", "/F"], capture_output=True)
                except Exception:
                    pass
                msg = "నెరేటర్ ఆఫ్ చేశాను, మాస్టర్." if lang == "te" else "Narrator turned off, Master."
                return True, msg

        elif feature in ["keyboard", "osk", "on-screen keyboard"]:
            if action in ["on", "open", "enable", "start"]:
                try:
                    subprocess.Popen(["osk.exe"], shell=False)
                except Exception:
                    pass
                msg = "ఆన్-స్క్రీన్ కీబోర్డ్ ఓపెన్ చేశాను, మాస్టర్." if lang == "te" else "On-Screen Keyboard opened, Master."
                return True, msg
            elif action in ["off", "close", "disable", "stop"]:
                try:
                    subprocess.run(["taskkill", "/IM", "osk.exe", "/F"], capture_output=True)
                except Exception:
                    pass
                msg = "ఆన్-స్క్రీన్ కీబోర్డ్ క్లోజ్ చేశాను, మాస్టర్." if lang == "te" else "On-Screen Keyboard closed, Master."
                return True, msg

        elif feature in ["highcontrast", "high contrast"]:
            cls._run_settings_script("accessibility", "open", feature="highcontrast")
            msg = "హై కాంట్రాస్ట్ సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్." if lang == "te" else "High Contrast settings opened, Master."
            return True, msg

        # General Accessibility
        cls._run_settings_script("accessibility", "open", feature="general")
        msg = "యాక్సెసిబిలిటీ సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్." if lang == "te" else "Accessibility settings opened, Master."
        return True, msg

    @classmethod
    def open_settings_page(cls, setting: str = "general", lang: str = "en") -> tuple[bool, str]:
        """Opens specific Windows Settings pages via native ms-settings URIs."""
        setting = setting.lower().strip()
        uri_map = {
            "display": "ms-settings:display",
            "sound": "ms-settings:sound",
            "audio": "ms-settings:sound",
            "wifi": "ms-settings:network-wifi",
            "bluetooth": "ms-settings:bluetooth",
            "airplane": "ms-settings:network-airplanemode",
            "aeroplane": "ms-settings:network-airplanemode",
            "battery": "ms-settings:batterysaver",
            "accessibility": "ms-settings:easeofaccess",
            "easeofaccess": "ms-settings:easeofaccess",
            "general": "ms-settings:"
        }
        target_uri = uri_map.get(setting, "ms-settings:")

        opened = False
        try:
            if os.name == "nt":
                os.startfile(target_uri)
                opened = True
        except Exception as e:
            logger.debug(f"Direct os.startfile for {target_uri} notice: {e}")

        if not opened:
            cls._run_settings_script("settings", "open", feature=setting)
        
        name_map = {
            "display": ("డిస్‌ప్లే సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్.", "Display settings opened, Master."),
            "sound": ("సౌండ్ సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్.", "Sound settings opened, Master."),
            "audio": ("సౌండ్ సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్.", "Sound settings opened, Master."),
            "wifi": ("వైఫై సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్.", "Wi-Fi settings opened, Master."),
            "bluetooth": ("బ్లూటూత్ సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్.", "Bluetooth settings opened, Master."),
            "airplane": ("ఏరోప్లేన్ మోడ్ సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్.", "Airplane mode settings opened, Master."),
            "aeroplane": ("ఏరోప్లేన్ మోడ్ సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్.", "Airplane mode settings opened, Master."),
            "battery": ("బ్యాటరీ సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్.", "Battery settings opened, Master."),
            "accessibility": ("యాక్సెసిబిలిటీ సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్.", "Accessibility settings opened, Master."),
        }
        te_msg, en_msg = name_map.get(setting, ("విండోస్ సెట్టింగ్స్ ఓపెన్ చేశాను, మాస్టర్.", "Windows Settings opened, Master."))
        return True, te_msg if lang == "te" else en_msg

    @classmethod
    def volume_control(cls, action: str, level: int = 50, lang: str = "en") -> tuple[bool, str]:
        """Controls audio volume via instant native Windows virtual audio keystrokes (<0.1ms)."""
        try:
            if os.name == "nt":
                user32 = ctypes.windll.user32
                VK_VOLUME_MUTE = 0xAD
                VK_VOLUME_DOWN = 0xAE
                VK_VOLUME_UP = 0xAF

                if action in ["up", "increase", "raise", "louder"]:
                    for _ in range(5):
                        user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
                        user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
                    msg = "వాల్యూమ్ పెంచాను, మాస్టర్." if lang == "te" else "Volume increased, Master."
                    return True, msg

                elif action in ["down", "decrease", "lower", "quieter"]:
                    for _ in range(5):
                        user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
                        user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
                    msg = "వాల్యూమ్ తగ్గించాను, మాస్టర్." if lang == "te" else "Volume decreased, Master."
                    return True, msg

                elif action in ["max", "maximum", "full"]:
                    for _ in range(50):
                        user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
                        user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
                    msg = "వాల్యూమ్ గరిష్టంగా సెట్ చేశాను, మాస్టర్." if lang == "te" else "Volume set to maximum, Master."
                    return True, msg

                elif action in ["min", "minimum", "lowest"]:
                    for _ in range(50):
                        user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
                        user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
                    # tap once up so audio isn't 0 if min means lowest audible
                    user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
                    user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
                    msg = "వాల్యూమ్ కనిష్టంగా సెట్ చేశాను, మాస్టర్." if lang == "te" else "Volume set to minimum, Master."
                    return True, msg

                elif action == "set":
                    target = max(0, min(100, level))
                    # Reset to 0 then step up to target
                    for _ in range(50):
                        user32.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
                        user32.keybd_event(VK_VOLUME_DOWN, 0, 2, 0)
                    steps = target // 2
                    for _ in range(steps):
                        user32.keybd_event(VK_VOLUME_UP, 0, 0, 0)
                        user32.keybd_event(VK_VOLUME_UP, 0, 2, 0)
                    msg = f"వాల్యూమ్ {target} శాతానికి సెట్ చేశాను, మాస్టర్." if lang == "te" else f"Volume set to {target} percent, Master."
                    return True, msg

                elif action in ["mute", "unmute"]:
                    user32.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
                    user32.keybd_event(VK_VOLUME_MUTE, 0, 2, 0)
                    if action == "mute":
                        msg = "వాల్యూమ్ మ్యూట్ చేశాను, మాస్టర్." if lang == "te" else "Audio muted, Master."
                    else:
                        msg = "వాల్యూమ్ అన్‌మ్యూట్ చేశాను, మాస్టర్." if lang == "te" else "Audio unmuted, Master."
                    return True, msg

            msg = "వాల్యూమ్ సర్దుబాటు చేయబడింది, మాస్టర్." if lang == "te" else "Volume command processed, Master."
            return True, msg
        except Exception as e:
            return False, f"Error controlling volume: {e}"

    @classmethod
    def take_screenshot(cls) -> tuple[bool, str, str]:
        """Captures full screen and saves to screenshots directory."""
        try:
            os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(SCREENSHOTS_DIR, filename)

            screenshot = ImageGrab.grab()
            screenshot.save(filepath, "PNG")
            return True, "Screenshot captured.", filepath
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return False, f"Failed to capture screenshot: {e}", ""

    @classmethod
    def get_date_time(cls, query_type: str = "both") -> tuple[bool, str, dict[str, Any]]:
        """Returns the exact local system date and/or time."""
        now = datetime.now()
        time_str = now.strftime("%I:%M %p").lstrip("0")
        day_name = now.strftime("%A")
        month_name = now.strftime("%B")
        date_str = f"{day_name}, {month_name} {now.day}, {now.year}"

        if query_type == "time":
            msg = f"The time is {time_str}, Master."
        elif query_type == "date":
            msg = f"Today is {date_str}, Master."
        else:
            msg = f"It is {time_str} on {date_str}, Master."

        details = {
            "time": time_str,
            "date": date_str,
            "iso": now.isoformat(),
            "timestamp": now.timestamp()
        }
        return True, msg, details

    @classmethod
    def _run_radio_script(cls, target: str, action: str) -> tuple[bool, str]:
        """Invokes the radio control helper."""
        # Try unified settings_control.ps1 first, fallback to radio_control.ps1
        ok, out = cls._run_settings_script(target.lower(), action)
        if ok:
            return True, out

        script_path = os.path.join(os.path.dirname(__file__), "radio_control.ps1")
        if not os.path.exists(script_path):
            return False, f"Radio script not found at {script_path}"
        try:
            res = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    script_path,
                    "-Target",
                    target,
                    "-Action",
                    action
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            output = res.stdout.strip()
            if "SUCCESS" in output or res.returncode == 0:
                return True, output
            err = res.stderr.strip() or output
            return False, err
        except Exception as e:
            logger.error(f"Error controlling radio {target}: {e}")
            return False, str(e)

    @classmethod
    def _broadcast_doom_animation(cls, event: str, data: dict):
        """Broadcasts a DOOM AI dramatic visual/audio animation event to all HUD WebSocket clients."""
        try:
            from backend.app.main import sync_broadcast
            sync_broadcast(event, data)
        except Exception:
            try:
                from ..app.main import sync_broadcast
                sync_broadcast(event, data)
            except Exception:
                pass

    @classmethod
    def _get_wifi_current_state(cls) -> bool:
        """Returns True if Wi-Fi radio is currently ON, False if OFF."""
        try:
            res = subprocess.run(
                [
                    "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-Command",
                    "(Get-NetAdapter | Where-Object { $_.Name -match 'Wi-?Fi|Wireless|WLAN' -and $_.Status -eq 'Up' } | Measure-Object).Count -gt 0"
                ],
                capture_output=True, text=True, timeout=5
            )
            return "True" in res.stdout
        except Exception:
            return False

    @classmethod
    def _get_bluetooth_current_state(cls) -> bool:
        """Returns True if Bluetooth radio is currently ON, False if OFF."""
        try:
            res = subprocess.run(
                [
                    "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                    "-Command",
                    "(Get-PnpDevice | Where-Object { $_.Class -eq 'Bluetooth' -and $_.Status -eq 'OK' } | Measure-Object).Count -gt 0"
                ],
                capture_output=True, text=True, timeout=5
            )
            return "True" in res.stdout
        except Exception:
            return False

    @classmethod
    def set_wifi_state(cls, action: str = "on", lang: str = "en") -> tuple[bool, str]:
        """Turns Wi-Fi on or off, toggles, or reports status."""
        action = action.lower().strip()

        if action == "toggle":
            # Check current state then flip
            is_on = cls._get_wifi_current_state()
            # Broadcast DOOM AI dramatic animation before toggling
            cls._broadcast_doom_animation("doom_action", {
                "type": "radio_toggle",
                "radio": "wifi",
                "current_state": "on" if is_on else "off",
                "new_state": "off" if is_on else "on",
                "animation": "pulse_red" if is_on else "pulse_green"
            })
            if is_on:
                cls._run_radio_script("WiFi", "off")
                msg = "వైఫై ఆఫ్ చేయబడింది, మాస్టర్." if lang == "te" else "Wi-Fi toggled off, Master."
            else:
                cls._run_radio_script("WiFi", "on")
                msg = "వైఫై ఆన్ చేయబడింది, మాస్టర్." if lang == "te" else "Wi-Fi toggled on, Master."
            return True, msg

        if action in ["on", "enable", "turn on", "switch on"]:
            cls._broadcast_doom_animation("doom_action", {
                "type": "radio_toggle", "radio": "wifi", "new_state": "on", "animation": "pulse_green"
            })
            ok, out = cls._run_radio_script("WiFi", "on")
            msg = "వైఫై ఆన్ చేయబడింది, మాస్టర్." if lang == "te" else "Wi-Fi is now turned on, Master."
            return True, msg
        elif action in ["off", "disable", "turn off", "switch off"]:
            cls._broadcast_doom_animation("doom_action", {
                "type": "radio_toggle", "radio": "wifi", "new_state": "off", "animation": "pulse_red"
            })
            ok, out = cls._run_radio_script("WiFi", "off")
            msg = "వైఫై ఆఫ్ చేయబడింది, మాస్టర్." if lang == "te" else "Wi-Fi is now turned off, Master."
            return True, msg
        elif action in ["status", "check"]:
            ok, out = cls._run_radio_script("WiFi", "status")
            if "On" in out or "SUCCESS" in out:
                msg = "వైఫై ప్రస్తుతం ఆన్‌లో ఉంది, మాస్టర్." if lang == "te" else "Wi-Fi is currently turned on, Master."
            elif "Off" in out:
                msg = "వైఫై ప్రస్తుతం ఆఫ్‌లో ఉంది, మాస్టర్." if lang == "te" else "Wi-Fi is currently turned off, Master."
            else:
                msg = f"వైఫై స్థితి: {out}" if lang == "te" else f"Wi-Fi status: {out}"
            return True, msg
        return False, f"Unknown Wi-Fi action: {action}"

    @classmethod
    def set_bluetooth_state(cls, action: str = "on", lang: str = "en") -> tuple[bool, str]:
        """Turns Bluetooth on or off, toggles, or reports status."""
        action = action.lower().strip()

        if action == "toggle":
            # Check current state then flip
            is_on = cls._get_bluetooth_current_state()
            # Broadcast DOOM AI dramatic animation before toggling
            cls._broadcast_doom_animation("doom_action", {
                "type": "radio_toggle",
                "radio": "bluetooth",
                "current_state": "on" if is_on else "off",
                "new_state": "off" if is_on else "on",
                "animation": "pulse_blue_off" if is_on else "pulse_blue_on"
            })
            if is_on:
                cls._run_radio_script("Bluetooth", "off")
                msg = "బ్లూటూత్ ఆఫ్ చేయబడింది, మాస్టర్." if lang == "te" else "Bluetooth toggled off, Master."
            else:
                cls._run_radio_script("Bluetooth", "on")
                msg = "బ్లూటూత్ ఆన్ చేయబడింది, మాస్టర్." if lang == "te" else "Bluetooth toggled on, Master."
            return True, msg

        if action in ["on", "enable", "turn on", "switch on"]:
            cls._broadcast_doom_animation("doom_action", {
                "type": "radio_toggle", "radio": "bluetooth", "new_state": "on", "animation": "pulse_blue_on"
            })
            ok, out = cls._run_radio_script("Bluetooth", "on")
            msg = "బ్లూటూత్ ఆన్ చేయబడింది, మాస్టర్." if lang == "te" else "Bluetooth is now turned on, Master."
            return True, msg
        elif action in ["off", "disable", "turn off", "switch off"]:
            cls._broadcast_doom_animation("doom_action", {
                "type": "radio_toggle", "radio": "bluetooth", "new_state": "off", "animation": "pulse_blue_off"
            })
            ok, out = cls._run_radio_script("Bluetooth", "off")
            msg = "బ్లూటూత్ ఆఫ్ చేయబడింది, మాస్టర్." if lang == "te" else "Bluetooth is now turned off, Master."
            return True, msg
        elif action in ["status", "check"]:
            ok, out = cls._run_radio_script("Bluetooth", "status")
            if "On" in out or "SUCCESS" in out:
                msg = "బ్లూటూత్ ప్రస్తుతం ఆన్‌లో ఉంది, మాస్టర్." if lang == "te" else "Bluetooth is currently turned on, Master."
            elif "Off" in out:
                msg = "బ్లూటూత్ ప్రస్తుతం ఆఫ్‌లో ఉంది, మాస్టర్." if lang == "te" else "Bluetooth is currently turned off, Master."
            else:
                msg = f"బ్లూటూత్ స్థితి: {out}" if lang == "te" else f"Bluetooth status: {out}"
            return True, msg
        return False, f"Unknown Bluetooth action: {action}"


