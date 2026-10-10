"""
VIKRAM AI / DOOM AI - File Explorer Controller
Automates Windows File Explorer: opening directories, navigating folders, searching files, and clean closure.
"""

import logging
import os
import subprocess
import time
from typing import Any, Dict, List, Tuple

from ..action_engine import UIActionEngine
from ..base_controller import BaseAppController
from ...execution.application_executor import ApplicationExecutor

logger = logging.getLogger("vikram.automation.explorer")

KNOWN_DIRS = {
    "downloads": os.path.expanduser("~/Downloads"),
    "download": os.path.expanduser("~/Downloads"),
    "documents": os.path.expanduser("~/Documents"),
    "document": os.path.expanduser("~/Documents"),
    "desktop": os.path.expanduser("~/Desktop"),
    "pictures": os.path.expanduser("~/Pictures"),
    "photos": os.path.expanduser("~/Pictures"),
    "music": os.path.expanduser("~/Music"),
    "videos": os.path.expanduser("~/Videos"),
    "home": os.path.expanduser("~"),
    "user": os.path.expanduser("~"),
    "c": "C:\\",
    "c drive": "C:\\",
    "d": "D:\\",
    "d drive": "D:\\",
}


class FileExplorerController(BaseAppController):
    name = "File Explorer"
    aliases = ["file explorer", "explorer", "files", "windows explorer", "file explore", "my files"]

    def launch(self) -> Tuple[bool, str]:
        ok, msg = ApplicationExecutor.launch("file explorer")
        hwnd = UIActionEngine.wait_for_window("File Explorer", ["explorer.exe"], timeout=4.0)
        if hwnd:
            UIActionEngine.set_foreground(hwnd)
            return True, "Opening File Explorer, Master."
        return ok, msg

    def close(self) -> Tuple[bool, str]:
        return ApplicationExecutor.close("file explorer")

    def execute_action(self, action: str, params: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        action_name = action.lower().strip()

        if action_name == "open":
            folder = params.get("folder") or params.get("path")
            if folder:
                return self.open_folder(folder)
            ok, msg = self.launch()
            return ok, msg, {}

        if action_name == "close":
            ok, msg = self.close()
            return ok, msg, {}

        if action_name in ["open_folder", "navigate_to", "go_to"]:
            folder = params.get("folder") or params.get("path") or params.get("directory", "")
            return self.open_folder(folder)

        if action_name in ["search_file", "search"]:
            query = params.get("query") or params.get("file") or params.get("filename", "")
            return self.search_file(query)

        return False, f"Action '{action}' not supported by FileExplorerController.", {}

    def open_folder(self, folder_name_or_path: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Open a specific folder or path in File Explorer."""
        if not folder_name_or_path:
            return False, "No folder or path specified, Master.", {}

        clean_name = folder_name_or_path.lower().strip()
        target_path = KNOWN_DIRS.get(clean_name)

        if not target_path:
            expanded = os.path.expandvars(os.path.expanduser(folder_name_or_path))
            if os.path.exists(expanded):
                target_path = expanded
            else:
                user_sub = os.path.join(os.path.expanduser("~"), folder_name_or_path)
                if os.path.exists(user_sub):
                    target_path = user_sub
                else:
                    target_path = folder_name_or_path

        try:
            logger.info(f"Opening folder in File Explorer: {target_path}")
            if os.path.exists(target_path):
                os.startfile(target_path)
            else:
                subprocess.Popen(["explorer.exe", target_path], shell=False)

            time.sleep(1.0)
            hwnd = UIActionEngine.wait_for_window("File Explorer", ["explorer.exe"], timeout=4.0)
            if hwnd:
                UIActionEngine.set_foreground(hwnd)

            return True, f"Opened {folder_name_or_path} folder in File Explorer, Master.", {"path": target_path}
        except Exception as e:
            logger.error(f"Failed to open folder '{folder_name_or_path}': {e}")
            return False, f"Could not open {folder_name_or_path}: {str(e)}", {}

    def search_file(self, query: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Search for a file within the current File Explorer window (Ctrl+E)."""
        if not query:
            return False, "No search query provided, Master.", {}

        hwnd = UIActionEngine.wait_for_window("File Explorer", ["explorer.exe"], timeout=2.0)
        if hwnd:
            UIActionEngine.set_foreground(hwnd)
        time.sleep(0.3)

        UIActionEngine.send_hotkey("ctrl", "e")
        time.sleep(0.3)
        UIActionEngine.type_text(query)
        time.sleep(0.2)
        UIActionEngine.send_key("enter")

        return True, f"Searching File Explorer for '{query}', Master.", {"query": query}
