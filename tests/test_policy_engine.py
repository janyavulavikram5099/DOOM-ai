"""
Security tests for VIKRAM Policy Engine and Confirmation Gate.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.security.policy_engine import PolicyEngine
from backend.security.confirmation import confirmation_gate


class TestPolicyEngine(unittest.TestCase):
    def test_safe_intent_allowed(self):
        allowed, msg, req_conf = PolicyEngine.validate_action("OPEN_APPLICATION", {"app_name": "notepad"})
        self.assertTrue(allowed)
        self.assertFalse(req_conf)

    def test_destructive_intent_requires_confirmation(self):
        allowed, msg, req_conf = PolicyEngine.validate_action("DELETE_FILE", {"file_name": "temp.txt"})
        self.assertTrue(allowed)
        self.assertTrue(req_conf)
        self.assertIn("destructive", msg.lower())

    def test_blocked_dangerous_patterns(self):
        allowed, msg, _ = PolicyEngine.validate_action("OPEN_APPLICATION", {"app_name": "notepad & format c:"})
        self.assertFalse(allowed)
        self.assertIn("blocked", msg.lower())

    def test_confirmation_gate_lifecycle(self):
        confirmation_gate.set_pending("DELETE_FILE", {"file_name": "foo.txt"}, "Confirm delete?")
        self.assertTrue(confirmation_gate.has_pending())

        resolved = confirmation_gate.resolve("yes please proceed")
        self.assertIsNotNone(resolved)
        assert resolved is not None
        self.assertEqual(resolved["intent"], "DELETE_FILE")
        self.assertFalse(confirmation_gate.has_pending())


if __name__ == "__main__":
    unittest.main()
