"""
DOOM AI - Physical Keyboard Shortcut Controller
Listens for:
  ALT + UP ARROW   -> ACTIVATE DOOM AI & OPEN/FOCUS HUD
  ALT + DOWN ARROW -> DEACTIVATE DOOM AI (KEEPS HUD OPEN)

Rules:
- Down Arrow alone must NOT deactivate DOOM AI.
- Up Arrow alone must NOT activate DOOM AI.
- Alt alone must NOT trigger anything.
- Only Alt + Up Arrow controls ON and opens the HUD.
- Only Alt + Down Arrow controls OFF (keeps HUD open).
- Prevents repeated triggering when keys are held down.
- Hotkey debounce included.
- Runs persistently in the background.
- Completely immune to laptop FnLock / multimedia key overrides.
- Never bypasses Windows security or authentication.
"""

import ctypes
from ctypes import wintypes
import logging
import os
import subprocess
import threading
import time
from typing import Any
import webbrowser

import requests

logger = logging.getLogger("vikram.assistant.shortcut_controller")

# Virtual Key Codes & Modifiers
VK_MENU = 0x12     # Alt key
VK_LMENU = 0xA4    # Left Alt
VK_RMENU = 0xA5    # Right Alt
VK_UP = 0x26       # Up arrow key
VK_DOWN = 0x28     # Down arrow key

MOD_ALT = 0x0001
MOD_NOREPEAT = 0x4000

HOTKEY_ACTIVATE_ID = 101
HOTKEY_DEACTIVATE_ID = 102
WM_HOTKEY = 0x0312
PM_REMOVE = 0x0001

MUTEX_NAME = "DOOM_AI_SHORTCUT_CONTROLLER_MUTEX"
ERROR_ALREADY_EXISTS = 183


class DOOMShortcutController:
    def __init__(self, api_base: str = "http://127.0.0.1:8765"):
        self.api_base = api_base.rstrip("/")
        self.is_running: bool = False
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._mutex_handle: int | None = None

        # Debounce & state tracking
        self._last_activate_time: float = 0.0
        self._last_deactivate_time: float = 0.0
        self._debounce_interval: float = 0.6  # seconds
        self._up_was_pressed: bool = False
        self._down_was_pressed: bool = False

        self._user32 = ctypes.windll.user32 if os.name == "nt" else None
        self._kernel32 = ctypes.windll.kernel32 if os.name == "nt" else None

        self._setup_ctypes_signatures()

    def _setup_ctypes_signatures(self):
        """Sets explicit 64-bit argument and return types for Win32 API calls."""
        if not self._user32:
            return

        try:
            self._user32.RegisterHotKey.argtypes = [
                wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT
            ]
            self._user32.RegisterHotKey.restype = wintypes.BOOL

            self._user32.UnregisterHotKey.argtypes = [
                wintypes.HWND, ctypes.c_int
            ]
            self._user32.UnregisterHotKey.restype = wintypes.BOOL

            self._user32.PeekMessageW.argtypes = [
                ctypes.POINTER(wintypes.MSG), wintypes.HWND,
                wintypes.UINT, wintypes.UINT, wintypes.UINT
            ]
            self._user32.PeekMessageW.restype = wintypes.BOOL

            self._user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
            self._user32.TranslateMessage.restype = wintypes.BOOL

            self._user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
            self._user32.DispatchMessageW.restype = wintypes.LPARAM

            self._user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
            self._user32.GetAsyncKeyState.restype = ctypes.c_short
        except Exception as e:
            logger.debug(f"Win32 ctypes signature setup notice: {e}")

    def acquire_mutex(self) -> bool:
        """Ensures only a single instance of the shortcut controller runs."""
        if not self._kernel32:
            return True
        handle = self._kernel32.CreateMutexW(None, False, MUTEX_NAME)
        if not handle:
            return True
        if self._kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
            logger.info("Another DOOMShortcutController instance is already running.")
            self._kernel32.CloseHandle(handle)
            return False
        self._mutex_handle = handle
        return True

    def release_mutex(self):
        """Releases the named mutex upon shutdown."""
        if self._kernel32 and self._mutex_handle:
            self._kernel32.CloseHandle(self._mutex_handle)
            self._mutex_handle = None

    def is_server_running(self) -> bool:
        """Checks if the DOOM AI API server is responsive."""
        try:
            r = requests.get(f"{self.api_base}/api/status", timeout=0.6)
            return r.status_code == 200
        except Exception:
            return False

    def is_server_active(self) -> bool:
        """Checks if DOOM AI server is currently in ONLINE/active state."""
        try:
            r = requests.get(f"{self.api_base}/api/status", timeout=0.6)
            if r.status_code == 200:
                data = r.json()
                state = data.get("state", "").upper()
                return state in ["ONLINE", "LISTENING", "PROCESSING", "SPEAKING", "EXECUTING"]
        except Exception:
            pass
        return False

    def open_hud(self):
        """Opens or brings the DOOM AI HUD browser interface to the foreground."""
        try:
            from backend.automation.action_engine import action_engine
            hwnds = action_engine.find_windows_by_title_or_process(
                "DOOM",
                ["msedge.exe", "chrome.exe", "firefox.exe", "opera.exe", "brave.exe"]
            )
            if hwnds:
                logger.info(f"Bringing existing DOOM HUD window (HWND {hwnds[0]}) to foreground...")
                action_engine.set_foreground(hwnds[0])
                return
        except Exception as ex:
            logger.debug(f"Window focus notice: {ex}")

        # If window not found, open in default browser
        try:
            logger.info("Opening DOOM HUD at http://127.0.0.1:8765...")
            webbrowser.open("http://127.0.0.1:8765")
        except Exception as e:
            logger.error(f"Failed to open HUD in browser: {e}")

    def launch_doom_hub(self) -> bool:
        """Launches open_doom_hub.vbs (or open_doom_hud.vbs) silently."""
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        vbs_paths = [
            os.path.join(root, "open_doom_hub.vbs"),
            os.path.join(root, "open_doom_hud.vbs")
        ]
        target_vbs = None
        for p in vbs_paths:
            if os.path.exists(p):
                target_vbs = p
                break

        if target_vbs:
            try:
                logger.info(f"Launching {target_vbs} via wscript...")
                subprocess.Popen(["wscript.exe", target_vbs], cwd=root)
                return True
            except Exception as e:
                logger.error(f"Failed to launch {target_vbs}: {e}")

        # Fallback: launch python uvicorn directly if VBS failed
        py_exe = os.path.join(root, ".venv", "Scripts", "python.exe")
        if not os.path.exists(py_exe):
            py_exe = "python"
        try:
            logger.info("Spawning DOOM AI uvicorn server directly as fallback...")
            flags = 0x00000008 | 0x08000000 if os.name == "nt" else 0  # DETACHED_PROCESS | CREATE_NO_WINDOW
            subprocess.Popen(
                [py_exe, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8765"],
                cwd=root,
                creationflags=flags
            )
            return True
        except Exception as ex:
            logger.error(f"Fallback uvicorn launch error: {ex}")
            return False

    def send_activate_request(self) -> bool:
        """Notifies the running DOOM AI instance to activate/resume."""
        try:
            r = requests.post(f"{self.api_base}/api/assistant/activate", timeout=2.5)
            logger.info(f"Activate request result: {r.status_code}")
            return r.status_code == 200
        except Exception as e:
            logger.debug(f"Activate request error: {e}")
            return False

    def send_deactivate_request(self) -> bool:
        """Notifies the running DOOM AI instance to deactivate/pause."""
        try:
            r = requests.post(f"{self.api_base}/api/assistant/deactivate", timeout=2.5)
            logger.info(f"Deactivate request result: {r.status_code}")
            return r.status_code == 200
        except Exception as e:
            logger.debug(f"Deactivate request error: {e}")
            return False

    def on_activate(self):
        """
        ALT + UP ARROW Handler
        - Activates DOOM AI (resumes listening, announces readiness)
        - Opens or focuses the DOOM AI HUD browser interface
        - If DOOM AI is OFF -> Launches server & opens HUD
        - If DOOM AI is already ON -> Activates & focuses/opens HUD
        - Never creates duplicate instances.
        """
        now = time.time()
        if now - self._last_activate_time < self._debounce_interval:
            return
        self._last_activate_time = now

        logger.info("[KEYBOARD] ALT + UP ARROW detected -> ACTIVATE DOOM AI & OPEN HUD")

        if self.send_activate_request():
            logger.info("DOOM AI activated successfully. Focusing/opening HUD...")
            self.open_hud()
            return

        logger.info("DOOM AI is OFF. Launching open_doom_hub.vbs...")
        self.launch_doom_hub()
        for _ in range(20):
            time.sleep(0.5)
            if self.is_server_running():
                logger.info("DOOM AI server is now responsive.")
                self.send_activate_request()
                self.open_hud()
                return
        logger.warning("DOOM AI server launch timed out.")

    def on_deactivate(self):
        """
        ALT + DOWN ARROW Handler
        - Deactivates DOOM AI (stops voice listening, active speech/TTS, automations)
        - Leaves the HUD open (does NOT close browser window)
        - Keeps the shortcut controller running in the background.
        """
        now = time.time()
        if now - self._last_deactivate_time < self._debounce_interval:
            return
        self._last_deactivate_time = now

        logger.info("[KEYBOARD] ALT + DOWN ARROW detected -> DEACTIVATE DOOM AI (KEEPS HUD OPEN)")
        self.send_deactivate_request()

    def start(self, blocking: bool = False):
        """Starts the persistent background shortcut listener."""
        if not self.acquire_mutex():
            return

        self.is_running = True
        self._stop_event.clear()

        if blocking:
            self._listener_loop()
        else:
            self._thread = threading.Thread(
                target=self._listener_loop,
                daemon=True,
                name="DOOMShortcutListener"
            )
            self._thread.start()
            logger.info("DOOM AI Physical Shortcut Controller started in background.")

    def stop(self):
        """Stops the shortcut controller loop safely."""
        self.is_running = False
        self._stop_event.set()
        self.release_mutex()

    def _listener_loop(self):
        """
        Rock-solid global keyboard listener using pynput low-level hook (WH_KEYBOARD_LL)
        with ctypes hardware fallback.
        Captures ALT + UP ARROW (Activate & Open HUD) and ALT + DOWN ARROW (Deactivate).
        Arrow keys alone and Alt alone NEVER trigger.
        """
        # Import pynput once; used by on_press, on_release, and listener creation below
        try:
            from pynput import keyboard as kb
        except ImportError:
            logger.warning("pynput not available, falling back to polling loop...")
            self._polling_loop()
            return

        alt_pressed = False

        def is_alt_down():
            nonlocal alt_pressed
            if alt_pressed:
                return True
            if self._user32:
                try:
                    return bool(
                        (self._user32.GetAsyncKeyState(VK_MENU) & 0x8000) or
                        (self._user32.GetAsyncKeyState(VK_LMENU) & 0x8000) or
                        (self._user32.GetAsyncKeyState(VK_RMENU) & 0x8000)
                    )
                except Exception:
                    pass
            return False

        def on_press(key):
            nonlocal alt_pressed
            try:
                if key in (kb.Key.alt, kb.Key.alt_l, kb.Key.alt_r, kb.Key.alt_gr):
                    alt_pressed = True
                elif key == kb.Key.up and is_alt_down():
                    self.on_activate()
                elif key == kb.Key.down and is_alt_down():
                    self.on_deactivate()
            except Exception as e:
                logger.debug(f"Key press notice: {e}")

        def on_release(key):
            nonlocal alt_pressed
            try:
                if key in (kb.Key.alt, kb.Key.alt_l, kb.Key.alt_r, kb.Key.alt_gr):
                    alt_pressed = False
            except Exception:
                pass

        listener = None
        try:
            listener = kb.Listener(on_press=on_press, on_release=on_release)
            listener.start()
            logger.info("DOOM AI low-level physical keyboard listener active (pynput WH_KEYBOARD_LL).")

            while not self._stop_event.is_set():
                time.sleep(0.05)

        except Exception as e:
            logger.warning(f"pynput hook initialization notice: {e}, falling back to polling loop...")
            self._polling_loop()
        finally:
            if listener:
                try:
                    listener.stop()
                except Exception:
                    pass
            self.release_mutex()

    def _polling_loop(self):
        """Fallback GetAsyncKeyState polling loop if pynput is unavailable."""
        if not self._user32:
            return
        while not self._stop_event.is_set():
            alt_down = bool(
                (self._user32.GetAsyncKeyState(VK_MENU) & 0x8000) or
                (self._user32.GetAsyncKeyState(VK_LMENU) & 0x8000) or
                (self._user32.GetAsyncKeyState(VK_RMENU) & 0x8000)
            )
            up_down = bool(self._user32.GetAsyncKeyState(VK_UP) & 0x8000)
            down_down = bool(self._user32.GetAsyncKeyState(VK_DOWN) & 0x8000)

            if alt_down and up_down:
                if not self._up_was_pressed:
                    self._up_was_pressed = True
                    self.on_activate()
            elif not up_down:
                self._up_was_pressed = False

            if alt_down and down_down:
                if not self._down_was_pressed:
                    self._down_was_pressed = True
                    self.on_deactivate()
            elif not down_down:
                self._down_was_pressed = False

            time.sleep(0.025)


# Global shortcut controller instance
shortcut_controller = DOOMShortcutController()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print("=======================================================")
    print("  DOOM AI PHYSICAL SHORTCUT CONTROLLER")
    print("  ALT + UP ARROW   -> ACTIVATE DOOM AI & OPEN HUD")
    print("  ALT + DOWN ARROW -> DEACTIVATE DOOM AI (HUD STAYS OPEN)")
    print("  (Arrow keys / Alt alone do nothing)")
    print("=======================================================")
    controller = DOOMShortcutController()
    controller.start(blocking=True)
