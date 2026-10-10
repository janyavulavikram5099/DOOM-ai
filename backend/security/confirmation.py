"""
VIKRAM AI - Confirmation Gate
Manages pending high-impact actions that require user confirmation before execution.
"""

import time
from typing import Any


class ConfirmationGate:
    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds
        self.pending_action: dict[str, Any] | None = None
        self.timestamp: float = 0.0

    def set_pending(self, intent: str, params: dict[str, Any], prompt: str):
        """Registers an action pending confirmation."""
        self.pending_action = {
            "intent": intent,
            "params": params,
            "prompt": prompt
        }
        self.timestamp = time.time()

    def has_pending(self) -> bool:
        """Checks if a pending action is currently active and not expired."""
        if not self.pending_action:
            return False
        if time.time() - self.timestamp > self.timeout_seconds:
            self.pending_action = None
            return False
        return True

    def clear(self):
        """Clears any pending action."""
        self.pending_action = None
        self.timestamp = 0.0

    def resolve(self, user_response: str) -> dict[str, Any] | None:
        """
        Evaluates user response. If affirmative, returns the pending action and clears it.
        If negative or unrecognized, clears and returns None.
        """
        if not self.has_pending():
            return None

        clean = user_response.lower().strip()
        affirmatives = ["yes", "proceed", "continue", "confirm", "do it", "sure", "affirmative", "go ahead"]
        negatives = ["no", "cancel", "stop", "abort", "don't", "dont", "negative"]

        if any(aff in clean for aff in affirmatives):
            action = self.pending_action
            self.clear()
            return action
        elif any(neg in clean for neg in negatives):
            self.clear()
            return None

        return None


# Global confirmation manager
confirmation_gate = ConfirmationGate()
