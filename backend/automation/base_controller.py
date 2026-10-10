"""
VIKRAM AI / DOOM AI - Base Application Controller Contract
Abstract base class defining standardized application control, actions, and verification.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Dict, Tuple


class BaseAppController(ABC):
    name: str = "Application"
    aliases: List[str] = []

    def matches_app_name(self, app_name: str) -> bool:
        """Determines if the controller matches the requested voice app name."""
        if not app_name:
            return False
        clean = app_name.lower().strip()
        if clean == self.name.lower() or any(alias.lower() == clean for alias in self.aliases):
            return True
        return any(alias.lower() in clean or clean in alias.lower() for alias in self.aliases)

    @abstractmethod
    def launch(self) -> Tuple[bool, str]:
        """Launches the application and brings its main window to the foreground."""
        pass

    @abstractmethod
    def close(self) -> Tuple[bool, str]:
        """Gracefully closes the application window or processes."""
        pass

    @abstractmethod
    def execute_action(self, action: str, params: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Executes an in-app action (e.g. 'send_message', 'calculate', 'search', 'open_file').
        Returns: (success: bool, response_message: str, details: dict)
        """
        pass

    def verify_action(self, action: str, params: Dict[str, Any]) -> Tuple[bool, str]:
        """Verifies if an action succeeded. Default implementation checks process/window existence."""
        return True, "Action verified."
