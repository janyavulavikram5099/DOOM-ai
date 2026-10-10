"""
VIKRAM AI / DOOM AI - Automation Controllers Package
"""

from .browser_controller import BrowserController
from .calculator_controller import CalculatorController
from .editor_controller import EditorController
from .file_explorer_controller import FileExplorerController
from .generic_controller import GenericAppController
from .spotify_controller import SpotifyController
from .whatsapp_controller import WhatsAppController

__all__ = [
    "BrowserController",
    "CalculatorController",
    "EditorController",
    "FileExplorerController",
    "GenericAppController",
    "SpotifyController",
    "WhatsAppController",
]
