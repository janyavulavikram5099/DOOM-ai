"""
VIKRAM AI / DOOM AI - Generic Application Controller
Universal fallback controller for any application discovered on the Windows device.
Supports opening, closing, window management, keystroke injection, and text typing.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from ..action_engine import UIActionEngine
from ..base_controller import BaseAppController
from ...execution.application_executor import ApplicationExecutor

logger = logging.getLogger("vikram.automation.generic")


class GenericAppController(BaseAppController):
    def __init__(self, app_id: str, app_names: Optional[List[str]] = None, window_titles: Optional[List[str]] = None):
        self.name = app_id.capitalize()
        self.aliases = app_names or [app_id.lower()]
        self.window_titles = window_titles or [self.name]
        self._app_id = app_id.lower()

    def launch(self) -> Tuple[bool, str]:
        ok, msg = ApplicationExecutor.launch(self._app_id)
        hwnd = UIActionEngine.wait_for_window(self.name, [f"{self._app_id}.exe"], timeout=4.0)
        if hwnd:
            UIActionEngine.set_foreground(hwnd)
            return True, f"Opening {self.name}, Master."
        return ok, msg

    def close(self) -> Tuple[bool, str]:
        return ApplicationExecutor.close(self._app_id)

    def execute_action(self, action: str, params: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        action_name = action.lower().strip()

        if action_name == "open":
            ok, msg = self.launch()
            return ok, msg, {}

        if action_name == "close":
            ok, msg = self.close()
            return ok, msg, {}

        if action_name in ["focus", "bring_to_front"]:
            hwnd = UIActionEngine.wait_for_window(self.name, [f"{self._app_id}.exe"], timeout=2.0)
            if hwnd and UIActionEngine.set_foreground(hwnd):
                return True, f"Focused {self.name}, Master.", {}
            return False, f"Could not find active window for {self.name}, Master.", {}

        if action_name == "minimize":
            hwnd = UIActionEngine.wait_for_window(self.name, [f"{self._app_id}.exe"], timeout=2.0)
            if hwnd and UIActionEngine.minimize_window(hwnd):
                return True, f"Minimized {self.name}, Master.", {}
            return False, f"Could not minimize {self.name}, Master.", {}

        if action_name == "maximize":
            hwnd = UIActionEngine.wait_for_window(self.name, [f"{self._app_id}.exe"], timeout=2.0)
            if hwnd and UIActionEngine.maximize_window(hwnd):
                return True, f"Maximized {self.name}, Master.", {}
            return False, f"Could not maximize {self.name}, Master.", {}

        if action_name in ["type_text", "type", "write"]:
            text = params.get("text") or params.get("content", "")
            if not text:
                return False, "No text provided to type, Master.", {}
            hwnd = UIActionEngine.wait_for_window(self.name, [f"{self._app_id}.exe"], timeout=2.0)
            if hwnd:
                UIActionEngine.set_foreground(hwnd)
            UIActionEngine.type_text(text)
            return True, f"Typed text into {self.name}, Master.", {}

        if action_name in ["press_key", "send_key"]:
            key = params.get("key", "")
            if not key:
                return False, "No key specified, Master.", {}
            hwnd = UIActionEngine.wait_for_window(self.name, [f"{self._app_id}.exe"], timeout=2.0)
            if hwnd:
                UIActionEngine.set_foreground(hwnd)
            UIActionEngine.send_key(key)
            return True, f"Pressed key '{key}', Master.", {}

        if action_name == "send_hotkey":
            keys = params.get("keys", [])
            if isinstance(keys, str):
                keys = [k.strip() for k in keys.split("+")]
            if not keys:
                return False, "No hotkey specified, Master.", {}
            hwnd = UIActionEngine.wait_for_window(self.name, [f"{self._app_id}.exe"], timeout=2.0)
            if hwnd:
                UIActionEngine.set_foreground(hwnd)
            UIActionEngine.send_hotkey(*keys)
            return True, f"Sent hotkey '{'+'.join(keys)}', Master.", {}

        return False, f"Action '{action}' not supported on {self.name}.", {}
