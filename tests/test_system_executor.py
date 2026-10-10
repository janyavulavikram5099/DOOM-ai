"""
Unit tests for VIKRAM System Executor and Action Dispatcher.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.execution.system_executor import SystemExecutor
from backend.execution.action_executor import ActionDispatcher
from backend.database.sqlite import db


class TestSystemExecutor(unittest.TestCase):
    def test_unlock_security_boundary(self):
        # Genuine Windows security boundary test
        ok, msg = SystemExecutor.unlock_request()
        self.assertTrue(ok)
        self.assertTrue("Unlocking your laptop" in msg or "Enter pin yourself" in msg)

    def test_action_dispatcher_execution_and_logging(self):
        # Execute safe developer command via dispatcher
        parsed = {
            "intent": "COMPILE_CODE",
            "raw_text": "compile Hello.java",
            "params": {"file_name": "samples/Hello.java"}
        }
        res = ActionDispatcher.execute(parsed)
        self.assertEqual(res["status"], "SUCCESS")
        self.assertIn("Compilation completed successfully", res["voice_response"])

        # Verify it was logged in SQLite command history
        history = db.get_command_history(limit=5)
        self.assertTrue(len(history) > 0)
        self.assertEqual(history[0]["intent"], "COMPILE_CODE")
        self.assertEqual(history[0]["raw_command"], "compile Hello.java")

    def test_destructive_action_pending_confirmation(self):
        parsed = {
            "intent": "DELETE_FILE",
            "raw_text": "delete important.txt",
            "params": {"file_name": "important.txt"}
        }
        res = ActionDispatcher.execute(parsed)
        self.assertEqual(res["status"], "PENDING_CONFIRMATION")
        self.assertIn("destructive", res["message"].lower())


if __name__ == "__main__":
    unittest.main()
