"""
VIKRAM AI / DOOM AI - Spotify Controller
Automates Spotify playback, searching songs/artists/playlists, and track navigation.
"""

import logging
import os
import time
import urllib.parse
from typing import Any, Dict, List, Tuple

from ..action_engine import UIActionEngine
from ..base_controller import BaseAppController
from ...execution.application_executor import ApplicationExecutor

logger = logging.getLogger("vikram.automation.spotify")


class SpotifyController(BaseAppController):
    name = "Spotify"
    aliases = ["spotify", "spotify music"]

    def launch(self) -> Tuple[bool, str]:
        ok, msg = ApplicationExecutor.launch("spotify")
        hwnd = UIActionEngine.wait_for_window("Spotify", ["Spotify.exe"], timeout=5.0)
        if hwnd:
            UIActionEngine.set_foreground(hwnd)
            return True, "Opening Spotify, Master."
        return ok, msg

    def close(self) -> Tuple[bool, str]:
        return ApplicationExecutor.close("spotify")

    def execute_action(self, action: str, params: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        action_name = action.lower().strip()

        if action_name == "open":
            ok, msg = self.launch()
            return ok, msg, {}

        if action_name == "close":
            ok, msg = self.close()
            return ok, msg, {}

        if action_name in ["search_and_play", "search", "play_song"]:
            query = params.get("query") or params.get("song") or params.get("artist") or params.get("track", "")
            return self.search_and_play(query, auto_play=(action_name != "search"))

        if action_name in ["play", "pause", "toggle_play"]:
            return self.toggle_play()

        if action_name in ["next_track", "next", "skip"]:
            return self.next_track()

        if action_name in ["previous_track", "prev", "back"]:
            return self.previous_track()

        return False, f"Action '{action}' not supported by SpotifyController.", {}

    def search_and_play(self, query: str, auto_play: bool = True) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Search for a track or playlist in Spotify and optionally start playback.
        Uses spotify:search URI or Spotify search hotkey.
        """
        if not query:
            return False, "No song or artist query provided, Master.", {}

        # Launch directly with Spotify URI scheme
        encoded_query = urllib.parse.quote(query)
        try:
            os.system(f'start spotify:search:"{encoded_query}"')
            time.sleep(1.5)
        except Exception as e:
            logger.warning(f"Could not launch via spotify URI: {e}")

        hwnd = UIActionEngine.wait_for_window("Spotify", ["Spotify.exe"], timeout=4.0)
        if hwnd:
            UIActionEngine.set_foreground(hwnd)
            time.sleep(0.5)

        if auto_play:
            # Enter or space to play top track
            UIActionEngine.send_key("enter")
            time.sleep(0.5)
            UIActionEngine.send_key("space")

        return True, f"Now playing '{query}' on Spotify, Master.", {"query": query}

    def toggle_play(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Toggle play/pause in Spotify."""
        hwnd = UIActionEngine.wait_for_window("Spotify", ["Spotify.exe"], timeout=2.0)
        if hwnd:
            UIActionEngine.set_foreground(hwnd)
        UIActionEngine.send_key("space")
        return True, "Toggled Spotify playback, Master.", {}

    def next_track(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Skip to next track (Ctrl + Right arrow)."""
        hwnd = UIActionEngine.wait_for_window("Spotify", ["Spotify.exe"], timeout=2.0)
        if hwnd:
            UIActionEngine.set_foreground(hwnd)
        UIActionEngine.send_hotkey("ctrl", "right")
        return True, "Skipped to next track, Master.", {}

    def previous_track(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Go back to previous track (Ctrl + Left arrow)."""
        hwnd = UIActionEngine.wait_for_window("Spotify", ["Spotify.exe"], timeout=2.0)
        if hwnd:
            UIActionEngine.set_foreground(hwnd)
        UIActionEngine.send_hotkey("ctrl", "left")
        return True, "Navigated to previous track, Master.", {}
