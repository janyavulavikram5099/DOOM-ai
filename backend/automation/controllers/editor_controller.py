"""
VIKRAM AI / DOOM AI - Editor Controller
Automates Visual Studio Code, Notepad, and code/text editors on Windows:
opening projects/files, typing code/notes, saving, and executing/running code.
"""

import logging
import os
import subprocess
import time
from typing import Any, Dict, List, Tuple

from ..action_engine import UIActionEngine
from ..base_controller import BaseAppController
from ...execution.application_executor import ApplicationExecutor

logger = logging.getLogger("vikram.automation.editor")


class EditorController(BaseAppController):
    def __init__(self, editor_type: str = "vscode"):
        self.editor_type = editor_type.lower()
        if self.editor_type == "vscode":
            self.name = "VS Code"
            self.aliases = ["vs code", "vscode", "visual studio code", "code"]
            self._proc_names = ["code.exe", "Code.exe"]
        elif self.editor_type == "notepad":
            self.name = "Notepad"
            self.aliases = ["notepad", "text editor", "notes"]
            self._proc_names = ["notepad.exe", "Notepad.exe"]
        else:
            self.name = editor_type.capitalize()
            self.aliases = [editor_type.lower()]
            self._proc_names = [f"{editor_type}.exe"]

    def launch(self) -> Tuple[bool, str]:
        ok, msg = ApplicationExecutor.launch(self.aliases[0])
        hwnd = UIActionEngine.wait_for_window(self.name, self._proc_names, timeout=5.0)
        if hwnd:
            UIActionEngine.set_foreground(hwnd)
            return True, f"Opening {self.name}, Master."
        return ok, msg

    def close(self) -> Tuple[bool, str]:
        return ApplicationExecutor.close(self.aliases[0])

    def execute_action(self, action: str, params: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        action_name = action.lower().strip()

        if action_name == "open":
            target = params.get("target") or params.get("path") or params.get("folder")
            if target:
                return self.open_path(target)
            ok, msg = self.launch()
            return ok, msg, {}

        if action_name == "close":
            ok, msg = self.close()
            return ok, msg, {}

        if action_name == "new_file":
            return self.new_file()

        if action_name in ["type_code", "type_text", "write"]:
            content = params.get("content") or params.get("code") or params.get("text", "")
            return self.type_content(content)

        if action_name in ["save_file", "save"]:
            return self.save_file()

        if action_name in ["run_code", "compile_and_run", "execute"]:
            command = params.get("command") or params.get("run_command", "")
            return self.run_code(command)

        if action_name in ["open_file", "open_folder"]:
            path = params.get("path") or params.get("target", "")
            return self.open_path(path)

        return False, f"Action '{action}' not supported by EditorController.", {}

    def open_path(self, path: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Open a file or directory in the editor."""
        if not path:
            return False, "No path provided to open in editor, Master.", {}

        try:
            if self.editor_type == "vscode":
                subprocess.Popen(["code", path], shell=True)
            elif self.editor_type == "notepad":
                subprocess.Popen(["notepad.exe", path], shell=False)
            else:
                subprocess.Popen([self.name, path], shell=True)

            time.sleep(1.5)
            hwnd = UIActionEngine.wait_for_window(self.name, self._proc_names, timeout=5.0)
            if hwnd:
                UIActionEngine.set_foreground(hwnd)
            return True, f"Opened '{path}' in {self.name}, Master.", {"path": path}
        except Exception as e:
            logger.error(f"Failed to open '{path}' in {self.name}: {e}")
            return False, f"Could not open '{path}': {str(e)}", {}

    def new_file(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Create a new file using Ctrl+N."""
        hwnd = UIActionEngine.wait_for_window(self.name, self._proc_names, timeout=2.0)
        if hwnd:
            UIActionEngine.set_foreground(hwnd)
        UIActionEngine.send_hotkey("ctrl", "n")
        time.sleep(0.3)
        return True, f"Created new file in {self.name}, Master.", {}

    def type_content(self, content: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Type or paste content into the editor."""
        if not content:
            return False, "No content provided to write, Master.", {}

        hwnd = UIActionEngine.wait_for_window(self.name, self._proc_names, timeout=2.0)
        if hwnd:
            UIActionEngine.set_foreground(hwnd)
        UIActionEngine.type_text(content)
        return True, f"Content entered into {self.name}, Master.", {"length": len(content)}

    def save_file(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Save the active file using Ctrl+S."""
        hwnd = UIActionEngine.wait_for_window(self.name, self._proc_names, timeout=2.0)
        if hwnd:
            UIActionEngine.set_foreground(hwnd)
        UIActionEngine.send_hotkey("ctrl", "s")
        time.sleep(0.3)
        return True, f"Saved active file in {self.name}, Master.", {}

    def run_code(self, command: str = "") -> Tuple[bool, str, Dict[str, Any]]:
        """Run code in VS Code."""
        hwnd = UIActionEngine.wait_for_window(self.name, self._proc_names, timeout=2.0)
        if hwnd:
            UIActionEngine.set_foreground(hwnd)

        if self.editor_type == "vscode":
            if command:
                UIActionEngine.send_hotkey("ctrl", "`")
                time.sleep(0.5)
                UIActionEngine.type_text(command)
                time.sleep(0.2)
                UIActionEngine.send_key("enter")
                return True, f"Running '{command}' in VS Code terminal, Master.", {"command": command}
            else:
                UIActionEngine.send_hotkey("ctrl", "f5")
                return True, "Triggered project execution in VS Code, Master.", {}
        else:
            return False, f"Run code is not supported in {self.name}, Master.", {}
