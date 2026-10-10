"""
VIKRAM AI - Windows Startup Manager
Configures Windows autorun via registry (HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run)
to launch the VIKRAM Background Service silently on system boot.
"""

import logging
import os

from ..database.sqlite import db

logger = logging.getLogger("vikram.service.startup")

RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "DOOM_AI_Assistant"


class StartupManager:
    @classmethod
    def is_startup_enabled(cls) -> bool:
        """Checks if DOOM AI is registered in Windows Startup registry."""
        if os.name != "nt":
            return False
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ) as key:
                try:
                    val, _ = winreg.QueryValueEx(key, APP_NAME)
                    return bool(val)
                except FileNotFoundError:
                    val, _ = winreg.QueryValueEx(key, "VIKRAM_AI_Assistant")
                    return bool(val)
        except Exception:
            return False

    @classmethod
    def set_startup(cls, enable: bool = True) -> bool:
        """Adds or removes DOOM AI from Windows Startup registry."""
        if os.name != "nt":
            return False
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
                if enable:
                    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    bat_path = os.path.join(root_dir, "run_doom.bat")
                    if not os.path.exists(bat_path):
                        bat_path = os.path.join(root_dir, "run_vikram.bat")
                    vbs_path = os.path.join(root_dir, "start_doom_silent.vbs")
                    if os.path.exists(vbs_path):
                        command = f'wscript.exe "{vbs_path}"'
                    else:
                        command = f'"{bat_path}" --headless'
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
                    db.set_setting("start_with_windows", "1")
                    logger.info("DOOM AI registered in Windows startup (Permanent Boot Service).")
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                    except FileNotFoundError:
                        pass
                    try:
                        winreg.DeleteValue(key, "VIKRAM_AI_Assistant")
                    except FileNotFoundError:
                        pass
                    db.set_setting("start_with_windows", "0")
                    logger.info("DOOM AI unregistered from Windows startup.")
            return True
        except Exception as e:
            logger.error(f"Error modifying Windows startup registry: {e}")
            return False

    @classmethod
    def set_startup_enabled(cls, enable: bool = True) -> bool:
        """Alias for set_startup to prevent AttributeError from API callers."""
        return cls.set_startup(enable=enable)

