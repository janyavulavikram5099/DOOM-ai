"""
VIKRAM AI - Windows System Tray Integration
Provides continuous background presence and full system tray menu using pystray.
"""

import logging
import threading
import webbrowser
from collections.abc import Callable

from PIL import Image, ImageDraw

logger = logging.getLogger("vikram.app.tray")


def create_vikram_icon_image() -> Image.Image:
    """Generates an original futuristic glowing cyan VIKRAM AI Core tray icon."""
    size = (64, 64)
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Outer metallic ring
    draw.ellipse([2, 2, 62, 62], outline=(0, 240, 255, 200), width=3)
    # Inner energy ring
    draw.ellipse([12, 12, 52, 52], outline=(0, 160, 255, 230), width=2)
    # Glowing center core
    draw.ellipse([22, 22, 42, 42], fill=(0, 240, 255, 255))
    # Core hotspot
    draw.ellipse([27, 27, 37, 37], fill=(255, 255, 255, 255))

    return image


class SystemTrayManager:
    def __init__(
        self,
        on_open_gui: Callable[[], None] | None = None,
        on_pause_listening: Callable[[], None] | None = None,
        on_resume_listening: Callable[[], None] | None = None,
        on_stop_assistant: Callable[[], None] | None = None,
        on_restart_assistant: Callable[[], None] | None = None,
        on_exit_app: Callable[[], None] | None = None,
    ):
        self.on_open_gui = on_open_gui
        self.on_pause_listening = on_pause_listening
        self.on_resume_listening = on_resume_listening
        self.on_stop_assistant = on_stop_assistant
        self.on_restart_assistant = on_restart_assistant
        self.on_exit_app = on_exit_app

        self.tray_icon = None
        self.is_listening = True
        self.is_running = True
        self._thread = None

    def _create_menu(self):
        import pystray
        from pystray import MenuItem as item

        status_text = (
            "● Assistant Online" if self.is_listening else "○ Assistant Paused"
        )

        return pystray.Menu(
            item("VIKRAM AI", None, enabled=False),
            item(status_text, None, enabled=False),
            pystray.Menu.SEPARATOR,
            item("Open VIKRAM", lambda: self._action_open_gui()),
            item(
                "Pause Listening",
                lambda: self._action_pause(),
                checked=lambda _: not self.is_listening,
            ),
            item(
                "Resume Listening",
                lambda: self._action_resume(),
                checked=lambda _: self.is_listening,
            ),
            pystray.Menu.SEPARATOR,
            item("Microphone", lambda: self._action_open_gui_tab("voice")),
            item("Voice Profile", lambda: self._action_open_gui_tab("voice")),
            item("Permissions", lambda: self._action_open_gui_tab("permissions")),
            item("Command History", lambda: self._action_open_gui_tab("history")),
            item("Settings", lambda: self._action_open_gui_tab("settings")),
            pystray.Menu.SEPARATOR,
            item("Restart Assistant", lambda: self._action_restart()),
            item("Stop Assistant", lambda: self._action_stop()),
            item("Exit VIKRAM", lambda: self._action_exit()),
        )

    def _action_open_gui(self):
        if self.on_open_gui:
            self.on_open_gui()
        else:
            webbrowser.open("http://127.0.0.1:8765")

    def _action_open_gui_tab(self, tab: str):
        webbrowser.open(f"http://127.0.0.1:8765/?tab={tab}")

    def _action_pause(self):
        self.is_listening = False
        if self.on_pause_listening:
            self.on_pause_listening()
        self.update_tray()

    def _action_resume(self):
        self.is_listening = True
        if self.on_resume_listening:
            self.on_resume_listening()
        self.update_tray()

    def _action_stop(self):
        self.is_listening = False
        if self.on_stop_assistant:
            self.on_stop_assistant()
        self.update_tray()

    def _action_restart(self):
        if self.on_restart_assistant:
            self.on_restart_assistant()

    def _action_exit(self):
        self.is_running = False
        if self.tray_icon:
            self.tray_icon.stop()
        if self.on_exit_app:
            self.on_exit_app()

    def update_tray(self):
        if self.tray_icon:
            self.tray_icon.menu = self._create_menu()

    def start(self):
        import pystray

        image = create_vikram_icon_image()
        self.tray_icon = pystray.Icon(
            "VIKRAM", image, "VIKRAM AI Assistant", self._create_menu()
        )
        self._thread = threading.Thread(
            target=self.tray_icon.run, daemon=True, name="VikramTrayIconThread"
        )
        self._thread.start()
        logger.info("VIKRAM system tray icon initialized.")

    def stop(self):
        if self.tray_icon:
            self.tray_icon.stop()
