"""
DOOM AI - Physical Touch Command Listener (Dual Engine)
Listens for 3 rapid physical presses of the BACKSPACE key.
Uses both Low-Level Windows Keyboard Hook (WH_KEYBOARD_LL) and Async Key State Polling (GetAsyncKeyState)
for 100% detection reliability across all Windows applications and environments.

When activated:
1. Speaks "Yes master" immediately using Windows SAPI voice.
2. Executes open_doom_hud.vbs to launch or focus the DOOM AI Futuristic HUD.
"""

from ctypes import wintypes
import ctypes
import logging
import os
import subprocess
import sys
import threading
import time

try:
    # pyrefly: ignore [untyped-import]
    import win32com.client
    # pyrefly: ignore [untyped-import]
    import win32con
    # pyrefly: ignore [untyped-import]
    import win32gui
except ImportError:
    win32com = None  # type: ignore[assignment]
    win32con = None  # type: ignore[assignment]
    win32gui = None  # type: ignore[assignment]

# Directory paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Logger setup
logger = logging.getLogger("vikram.assistant.touch_listener")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "touch_listener.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

# Win32 Constants
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
VK_BACK = 0x08  # Backspace key

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


def speak_yes_master():
    """Speaks 'Yes master' using Windows SAPI voice asynchronously."""
    try:
        if win32com:
            voice = win32com.client.Dispatch("SAPI.SpVoice")
            # 1 = SVSFlagsAsync (non-blocking)
            voice.Speak("Yes master", 1)
            logger.info("Spoke 'Yes master' via SAPI.")
            return
    except Exception as e:  # noqa: BLE001
        logger.debug(f"SAPI voice notice: {e}, falling back to PowerShell SAPI...")

    try:
        cmd = "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).SpeakAsync('Yes master')"
        subprocess.Popen(["powershell.exe", "-NoProfile", "-Command", cmd], creationflags=0x08000000)
    except Exception as ex:  # noqa: BLE001
        logger.error(f"Voice speech error: {ex}")


def focus_existing_hud_window() -> bool:
    """Checks if a browser window with DOOM HUD is open and brings it to front."""
    if not win32gui or not win32con:
        return False

    try:
        found: list[int] = []

        def enum_cb(hwnd: int, _: object):
            # pyrefly: ignore [missing-attribute]
            if win32gui.IsWindowVisible(hwnd):
                # pyrefly: ignore [missing-attribute]
                title = win32gui.GetWindowText(hwnd)
                if any(k in title.lower() for k in ["doom ai", "vikram ai", "8765"]):
                    found.append(hwnd)

        # pyrefly: ignore [missing-attribute]
        win32gui.EnumWindows(enum_cb, None)
        if found:
            hwnd = found[0]
            # pyrefly: ignore [missing-attribute]
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            # pyrefly: ignore [missing-attribute]
            win32gui.SetForegroundWindow(hwnd)
            logger.info(f"Brought existing HUD window (HWND {hwnd}) to front.")
            return True
    except Exception as ex:  # noqa: BLE001
        logger.debug(f"Window focus notice: {ex}")
    return False


def activate_doom_ai():
    """Activates DOOM AI: speaks voice response and triggers open_doom_hud.vbs."""
    logger.info(">>> PHYSICAL TOUCH TRIGGER ACTIVATED: 3x BACKSPACE DETECTED <<<")
    # 1. Speak "Yes master" immediately
    threading.Thread(target=speak_yes_master, daemon=True, name="DoomTouchVoice").start()

    # 2. Focus existing HUD window if already open
    if focus_existing_hud_window():
        return

    # 3. Launch open_doom_hud.vbs
    vbs_path = os.path.join(PROJECT_ROOT, "open_doom_hud.vbs")
    if os.path.exists(vbs_path):
        try:
            logger.info(f"Executing {vbs_path}...")
            subprocess.Popen(
                ["wscript.exe", vbs_path],
                cwd=PROJECT_ROOT,
                creationflags=0x08000000  # CREATE_NO_WINDOW
            )
        except Exception as e:  # noqa: BLE001
            logger.error(f"Failed to execute open_doom_hud.vbs: {e}")
    else:
        bat_path = os.path.join(PROJECT_ROOT, "run_doom.bat")
        if os.path.exists(bat_path):
            try:
                subprocess.Popen(["cmd.exe", "/c", bat_path], cwd=PROJECT_ROOT)
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to execute run_doom.bat: {e}")


class PhysicalTouchListener:
    """
    Dual-engine listener for 3x Backspace presses:
    Engine 1: Low-Level Windows Hook (WH_KEYBOARD_LL) with message pump
    Engine 2: Hardware Key State Polling (GetAsyncKeyState) at 20ms intervals
    """
    def __init__(self, tap_count: int = 3, max_window: float = 1.3, cooldown: float = 2.0):
        self.target_taps = tap_count
        self.max_window = max_window
        self.cooldown = cooldown

        self.tap_times: list[float] = []
        self.last_trigger_time: float = 0.0
        self._lock = threading.Lock()

        # Engine 1 state
        self.hook_id = None
        self._hook_proc = None
        self.hook_key_down = False

        # Engine 2 state
        self.poll_key_down = False

        self._running = False
        self._thread_id: int | None = None
        self.h_mutex = None

    def _register_tap(self, source: str):
        """Thread-safe tap registration with deduplication and debounce."""
        now = time.time()
        with self._lock:
            # Check cooldown
            if now - self.last_trigger_time <= self.cooldown:
                return

            # Deduplicate taps captured within 80ms by both engines
            if self.tap_times and (now - self.tap_times[-1] < 0.08):
                return

            # Keep only taps within max_window
            self.tap_times = [t for t in self.tap_times if now - t <= self.max_window]
            self.tap_times.append(now)

            count = len(self.tap_times)
            logger.info(f"Physical Backspace tap ({count}/{self.target_taps}) [via {source}]")

            if count >= self.target_taps:
                self.last_trigger_time = now
                self.tap_times.clear()
                threading.Thread(
                    target=activate_doom_ai,
                    daemon=True,
                    name="DoomTouchActivator"
                ).start()

    # --- Engine 1: Low-Level Hook ---
    def _hook_callback(self, nCode: int, wParam: int, lParam: int):
        if nCode >= 0:
            kb = KBDLLHOOKSTRUCT.from_address(lParam)
            if kb.vkCode == VK_BACK:
                if wParam in (WM_KEYUP, WM_SYSKEYUP):
                    self.hook_key_down = False
                elif wParam in (WM_KEYDOWN, WM_SYSKEYDOWN) and not self.hook_key_down:
                    self.hook_key_down = True
                    self._register_tap("Hook")
        return user32.CallNextHookEx(self.hook_id, nCode, wParam, lParam)

    # --- Engine 2: Hardware Poller ---
    def _polling_loop(self):
        """Continuously checks physical Backspace state every 20ms."""
        logger.info("Physical Key Poller engine started.")
        while self._running:
            try:
                # 0x8000 bit indicates physical key is currently down
                is_down = bool(user32.GetAsyncKeyState(VK_BACK) & 0x8000)
                if is_down and not self.poll_key_down:
                    self.poll_key_down = True
                    self._register_tap("Poller")
                elif not is_down and self.poll_key_down:
                    self.poll_key_down = False
            except Exception as e:  # noqa: BLE001
                logger.debug(f"Poller notice: {e}")
            time.sleep(0.020)

    def start(self):
        """Starts both engines and runs the Windows event pump."""
        # Single-instance Named Mutex to prevent multiple processes
        mutex_name = "Global\\DOOM_AI_PhysicalTouchListener_Mutex"
        self.h_mutex = kernel32.CreateMutexW(None, False, mutex_name)
        if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            logger.info("Another instance of PhysicalTouchListener is already running. Exiting.")
            sys.exit(0)

        self._running = True
        self._thread_id = kernel32.GetCurrentThreadId()

        # Start Polling Engine in background thread
        poll_thread = threading.Thread(target=self._polling_loop, daemon=True, name="DoomTouchPoller")
        poll_thread.start()

        # Install Low-Level Hook Engine
        user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
        user32.SetWindowsHookExW.restype = wintypes.HHOOK
        user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
        user32.CallNextHookEx.restype = ctypes.c_long
        user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
        user32.UnhookWindowsHookEx.restype = wintypes.BOOL

        self._hook_proc = HOOKPROC(self._hook_callback)
        self.hook_id = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            self._hook_proc,
            None,
            0
        )

        if not self.hook_id:
            logger.warning("WH_KEYBOARD_LL hook not active. Relying on Poller engine.")
        else:
            logger.info("WH_KEYBOARD_LL hook active.")

        logger.info(f"DOOM AI Physical Touch Listener READY: Press Backspace {self.target_taps} times to activate.")

        # Windows Message Pump
        msg = wintypes.MSG()
        try:
            while self._running:
                b_ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if b_ret <= 0:
                    break
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            self.stop()

    def stop(self):
        self._running = False
        if self.hook_id:
            try:
                user32.UnhookWindowsHookEx(self.hook_id)
            except Exception as e:  # noqa: BLE001
                logger.debug(f"Unhook notice: {e}")
            self.hook_id = None
            logger.info("Physical Touch Listener hook uninstalled.")
        if hasattr(self, "_thread_id") and self._thread_id:
            try:
                user32.PostThreadMessageW(self._thread_id, 0x0012, 0, 0)
            except Exception as e:  # noqa: BLE001
                logger.debug(f"PostThreadMessage notice: {e}")


def run_listener():
    listener = PhysicalTouchListener(tap_count=3, max_window=1.3, cooldown=2.0)
    try:
        listener.start()
    except KeyboardInterrupt:
        listener.stop()


if __name__ == "__main__":
    run_listener()
