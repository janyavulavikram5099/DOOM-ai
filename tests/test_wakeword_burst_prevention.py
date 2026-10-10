"""
Unit tests verifying burst prevention, activation cooldown, and clean pause/resume
in DOOM AI wakeword & command execution pipeline.
Ensures that commands do not run simultaneously upon activation.
"""

import time
import unittest
from unittest.mock import MagicMock, patch

from backend.assistant.wakeword import wakeword_listener
from backend.service.lifecycle import lifecycle, AssistantState


class TestWakewordBurstPrevention(unittest.TestCase):
    def setUp(self):
        wakeword_listener.is_active = True
        wakeword_listener.is_paused = False
        wakeword_listener._activation_cooldown_until = 0.0
        wakeword_listener._last_cmd_time = 0.0
        wakeword_listener._last_cmd_text = ""
        self.mock_callback = MagicMock()
        wakeword_listener.on_command_detected = self.mock_callback

    def test_activation_cooldown_drops_stale_commands(self):
        """Commands arriving within the activation cooldown window must be ignored."""
        wakeword_listener._activation_cooldown_until = time.time() + 2.0
        success, cmd = wakeword_listener.process_speech_input("close downloads", allow_direct=True)
        self.assertFalse(success)
        self.assertEqual(cmd, "")
        self.mock_callback.assert_not_called()

    def test_burst_commands_are_rate_limited(self):
        """
        Rapid successive commands arriving within 1 second must not run at the same time.
        Only the first valid spoken command runs; subsequent bursts in the same second are dropped.
        """
        # First command succeeds
        success1, cmd1 = wakeword_listener.process_speech_input("open chrome", allow_direct=True)
        self.assertTrue(success1)
        self.assertEqual(cmd1, "open chrome")
        self.assertEqual(self.mock_callback.call_count, 1)

        # Immediate second command (e.g., from buffer dump 50ms later) must be dropped
        success2, cmd2 = wakeword_listener.process_speech_input("lock", allow_direct=True)
        self.assertFalse(success2)
        self.assertEqual(cmd2, "")
        # Call count should STILL be 1 (second command blocked)
        self.assertEqual(self.mock_callback.call_count, 1)

        # Immediate third command (e.g., another buffer dump item) must also be dropped
        success3, cmd3 = wakeword_listener.process_speech_input("turn off bluetooth", allow_direct=True)
        self.assertFalse(success3)
        self.assertEqual(cmd3, "")
        self.assertEqual(self.mock_callback.call_count, 1)

    def test_spaced_voice_commands_both_work(self):
        """
        When the user speaks commands with normal human pacing (>1.0s apart),
        both commands must work properly.
        """
        success1, cmd1 = wakeword_listener.process_speech_input("open notepad", allow_direct=True)
        self.assertTrue(success1)
        self.assertEqual(cmd1, "open notepad")

        # Simulate user waiting 1.1 seconds before giving the next voice command
        wakeword_listener._last_cmd_time = time.time() - 1.1

        success2, cmd2 = wakeword_listener.process_speech_input("close notepad", allow_direct=True)
        self.assertTrue(success2)
        self.assertEqual(cmd2, "close notepad")
        self.assertEqual(self.mock_callback.call_count, 2)

    def test_pause_and_resume_sets_cooldown_and_drains(self):
        """
        Resuming sets activation cooldown and drains any pending pipe buffer,
        preventing buffered backlog execution.
        """
        wakeword_listener.pause()
        self.assertTrue(wakeword_listener.is_paused)

        # While paused, inputs must not be processed
        success_paused, _ = wakeword_listener.process_speech_input("open chrome", allow_direct=True)
        self.assertFalse(success_paused)

        wakeword_listener.resume()
        self.assertFalse(wakeword_listener.is_paused)
        # Activation cooldown must be active in the future
        self.assertGreater(wakeword_listener._activation_cooldown_until, time.time())

        # Inputs immediately after resume are in cooldown window
        success_cooldown, _ = wakeword_listener.process_speech_input("unmute", allow_direct=True)
        self.assertFalse(success_cooldown)
        self.mock_callback.assert_not_called()


if __name__ == "__main__":
    unittest.main()
