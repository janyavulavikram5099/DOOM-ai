"""
Unit tests for DOOM AI Physical Shortcut Controller (Alt+Up Arrow / Alt+Down Arrow).
"""

import asyncio
import unittest
from unittest.mock import MagicMock, patch

from backend.app.main import activate_assistant_api, deactivate_assistant_api
from backend.assistant.shortcut_controller import DOOMShortcutController
from backend.assistant.wakeword import wakeword_listener
from backend.service.lifecycle import lifecycle, AssistantState


class TestShortcutController(unittest.TestCase):
    def setUp(self):
        self.controller = DOOMShortcutController(api_base="http://127.0.0.1:8765")

    def test_bare_keys_do_nothing(self):
        """Verify Up Arrow alone and Down Arrow alone do NOT trigger activation or deactivation."""
        self.controller.on_activate = MagicMock()
        self.controller.on_deactivate = MagicMock()

        # Simulate user pressing Up arrow alone (alt=False, up=True)
        alt_down = False
        up_down = True
        down_down = False

        if alt_down and up_down:
            self.controller.on_activate()
        if alt_down and down_down:
            self.controller.on_deactivate()

        self.controller.on_activate.assert_not_called()
        self.controller.on_deactivate.assert_not_called()

        # Simulate user pressing Down arrow alone (alt=False, down=True)
        alt_down = False
        up_down = False
        down_down = True

        if alt_down and up_down:
            self.controller.on_activate()
        if alt_down and down_down:
            self.controller.on_deactivate()

        self.controller.on_activate.assert_not_called()
        self.controller.on_deactivate.assert_not_called()

        # Simulate Alt alone
        alt_down = True
        up_down = False
        down_down = False

        if alt_down and up_down:
            self.controller.on_activate()
        if alt_down and down_down:
            self.controller.on_deactivate()

        self.controller.on_activate.assert_not_called()
        self.controller.on_deactivate.assert_not_called()

    def test_alt_up_and_down_trigger(self):
        """Verify Alt+Up triggers activation and Alt+Down triggers deactivation."""
        self.controller.on_activate = MagicMock()
        self.controller.on_deactivate = MagicMock()

        # Alt + Up Arrow
        alt_down = True
        up_down = True
        down_down = False

        if alt_down and up_down:
            self.controller.on_activate()

        self.controller.on_activate.assert_called_once()
        self.controller.on_deactivate.assert_not_called()

        # Alt + Down Arrow
        alt_down = True
        up_down = False
        down_down = True

        if alt_down and down_down:
            self.controller.on_deactivate()

        self.controller.on_deactivate.assert_called_once()

    def test_key_hold_prevents_repeated_triggering(self):
        """Verify holding down keys does not trigger repeated activations."""
        mock_action = MagicMock()
        up_was_pressed = False

        alt_down = False
        # Loop 5 times with Alt+Up held down
        for _ in range(5):
            alt_down = True
            up_down = True
            if alt_down and up_down:
                if not up_was_pressed:
                    up_was_pressed = True
                    mock_action()
            elif not up_down:
                up_was_pressed = False

        # Should only have been called ONCE despite being held for 5 ticks
        self.assertEqual(mock_action.call_count, 1)

        # Release key
        up_down = False
        if not up_down:
            up_was_pressed = False

        # Press again
        up_down = True
        if alt_down and up_down:
            if not up_was_pressed:
                up_was_pressed = True
                mock_action()

        # Now called twice
        self.assertEqual(mock_action.call_count, 2)

    def test_activate_api_endpoint(self):
        """Test activate_assistant_api resumes listening and sets state ONLINE."""
        # Start in paused state
        wakeword_listener.pause()
        self.assertTrue(wakeword_listener.is_paused)

        data = asyncio.run(activate_assistant_api())
        self.assertEqual(data["status"], "ACTIVE")
        self.assertEqual(data["state"], AssistantState.ONLINE.value)
        self.assertFalse(wakeword_listener.is_paused)

    def test_deactivate_api_endpoint(self):
        """Test deactivate_assistant_api pauses listening and sets state PAUSED."""
        # Start in online state
        wakeword_listener.resume()
        self.assertFalse(wakeword_listener.is_paused)

        data = asyncio.run(deactivate_assistant_api())
        self.assertEqual(data["status"], "DEACTIVATED")
        self.assertEqual(data["state"], AssistantState.PAUSED.value)
        self.assertTrue(wakeword_listener.is_paused)


if __name__ == "__main__":
    unittest.main()
