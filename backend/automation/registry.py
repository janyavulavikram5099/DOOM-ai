"""
VIKRAM AI / DOOM AI - Application Controller Registry
Coordinates all specialized and generic application controllers.
Resolves voice app names and aliases, maintaining conversational context across turns.
"""

import logging
from typing import Dict, List, Optional

from .base_controller import BaseAppController
from .controllers.browser_controller import BrowserController
from .controllers.calculator_controller import CalculatorController
from .controllers.editor_controller import EditorController
from .controllers.file_explorer_controller import FileExplorerController
from .controllers.generic_controller import GenericAppController
from .controllers.spotify_controller import SpotifyController
from .controllers.whatsapp_controller import WhatsAppController
from ..execution.application_scanner import application_scanner

logger = logging.getLogger("vikram.automation.registry")


class AppControllerRegistry:
    """
    Central registry for application controllers.
    Resolves voice app names to controllers and maintains active context.
    """

    def __init__(self):
        self._specialized_controllers: List[BaseAppController] = [
            WhatsAppController(),
            CalculatorController(),
            BrowserController(),
            SpotifyController(),
            FileExplorerController(),
            EditorController("vscode"),
            EditorController("notepad"),
        ]
        self._last_active_app: Optional[str] = None

    @property
    def last_active_app(self) -> Optional[str]:
        return self._last_active_app

    def set_active_app(self, app_name: str):
        """Set the most recently interacted application for context preservation."""
        self._last_active_app = app_name.lower().strip()
        logger.info(f"Active application context set to: {self._last_active_app}")

    def clear_active_app(self):
        """Clear the active application context."""
        self._last_active_app = None

    def get_controller(self, app_name: str) -> BaseAppController:
        """
        Find the best controller for a given app name.
        1. Checks specialized controllers (exact / alias / match_app_name).
        2. Checks ApplicationScanner catalog for installed apps.
        3. Returns a GenericAppController if no specialized controller is found.
        """
        if not app_name:
            if self._last_active_app:
                logger.info(f"No app specified. Falling back to active context: {self._last_active_app}")
                return self.get_controller(self._last_active_app)
            raise ValueError("No application name provided and no active context available.")

        clean_name = app_name.strip().lower()

        # 1. Check specialized controllers
        for ctrl in self._specialized_controllers:
            if ctrl.matches_app_name(clean_name):
                self._last_active_app = ctrl.name.lower()
                return ctrl

        # Edge cases for browser aliases
        if clean_name in ["browser", "web browser", "internet"]:
            ctrl = self.get_controller("chrome")
            self._last_active_app = ctrl.name.lower()
            return ctrl

        # 2. Query application scanner
        scanned_app = application_scanner.find_app(clean_name)
        if scanned_app:
            display_name = scanned_app.get("display_name", clean_name)
            # Re-check specialized controllers with official display name
            for ctrl in self._specialized_controllers:
                if ctrl.matches_app_name(display_name):
                    self._last_active_app = ctrl.name.lower()
                    return ctrl

            # Return a generic controller tailored to this scanned app
            generic_ctrl = GenericAppController(
                app_id=clean_name,
                app_names=[clean_name, display_name.lower()],
                window_titles=[display_name, clean_name.capitalize()]
            )
            self._last_active_app = clean_name
            return generic_ctrl

        # 3. Fallback generic controller
        logger.warning(f"No scanned or specialized controller found for '{clean_name}'. Using generic controller.")
        self._last_active_app = clean_name
        return GenericAppController(app_id=clean_name)

    def list_supported_apps(self) -> List[str]:
        """Return list of supported specialized app names."""
        names: List[str] = []
        for ctrl in self._specialized_controllers:
            names.append(ctrl.name)
            names.extend(ctrl.aliases)
        return sorted(list(set(names)))


# Global singleton registry
app_registry = AppControllerRegistry()
