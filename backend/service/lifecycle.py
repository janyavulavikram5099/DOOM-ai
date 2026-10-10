"""
VIKRAM AI - Process Lifecycle & State Manager
Coordinates assistant operational states:
OFFLINE, STARTING, ONLINE, LISTENING, VOICE VERIFIED, PROCESSING,
EXECUTING, SPEAKING, ERROR, AUTHENTICATION REQUIRED.
"""

import enum
import logging
from collections.abc import Callable

logger = logging.getLogger("vikram.service.lifecycle")


class AssistantState(str, enum.Enum):
    OFFLINE = "OFFLINE"
    STARTING = "STARTING"
    ONLINE = "ONLINE"
    PAUSED = "PAUSED"
    LISTENING = "LISTENING"
    VOICE_VERIFIED = "VOICE VERIFIED"
    PROCESSING = "PROCESSING"
    EXECUTING = "EXECUTING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION REQUIRED"


class LifecycleManager:
    def __init__(self):
        self._current_state: AssistantState = AssistantState.OFFLINE
        self._listeners: list[Callable[[str], None]] = []

    @property
    def state(self) -> str:
        return self._current_state.value

    def set_state(self, new_state: AssistantState):
        if self._current_state != new_state:
            self._current_state = new_state
            logger.info(f"State transition -> {new_state.value}")
            for listener in self._listeners:
                try:
                    listener(new_state.value)
                except Exception as e:
                    logger.error(f"Error in state listener: {e}")

    def add_listener(self, listener: Callable[[str], None]):
        self._listeners.append(listener)


# Global lifecycle manager
lifecycle = LifecycleManager()
