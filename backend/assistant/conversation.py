"""
VIKRAM AI - Conversation Context Manager
Tracks short-term conversational context (current active file, language, app, query),
with automatic TTL expiration, entity resolution (e.g. resolving "it" or "that"),
and state management.
"""

import time
from typing import Any


class ConversationContext:
    def __init__(self, ttl_seconds: int = 120):
        self.ttl_seconds = ttl_seconds
        self.last_interaction_time: float = 0.0
        self.current_file: str | None = None
        self.current_language: str | None = None
        self.current_app: str | None = None
        self.last_intent: str | None = None
        self.last_query: str | None = None
        self.last_topic: str | None = None
        self.last_compiler_output: dict[str, Any] | None = None
        self.last_error_analysis: dict[str, Any] | None = None

    def update(self, **kwargs):
        """Updates context variables and refreshes the timestamp."""
        self.last_interaction_time = time.time()
        for key, val in kwargs.items():
            if hasattr(self, key) and val is not None:
                setattr(self, key, val)

    def is_active(self) -> bool:
        """Checks if the context is still alive (not expired)."""
        return (time.time() - self.last_interaction_time) < self.ttl_seconds

    def resolve_reference(self, raw_text: str, detected_params: dict[str, Any]) -> dict[str, Any]:
        """
        Resolves pronouns and context references like 'it', 'the file', 'that project', 'search that'.
        For example: 'compile it' -> target file from context.
        """
        if not self.is_active():
            return detected_params

        params = dict(detected_params)
        text_lower = raw_text.lower()

        # If user asks to compile or run "it" or doesn't specify file, use current_file
        if any(w in text_lower for w in ["compile it", "run it", "execute it", "debug it", "explain it", "explain the error"]):
            if self.current_file and not params.get("file_name"):
                params["file_name"] = self.current_file
                if self.current_language:
                    params["language"] = self.current_language

        # If user says "close it", "close this", or "close that", use current_app if known
        if any(w in text_lower for w in ["close it", "close this", "close that"]) and self.current_app:
            if not params.get("app_name") or params.get("app_name") in ["active", "it", "this", "that"]:
                params["app_name"] = self.current_app

        # If user says "search about that", "search that", "search it", "search about it"
        if any(w in text_lower for w in ["search about that", "search that", "search it", "search about it", "search about this"]):
            target_topic = self.last_topic or self.last_query or (f"{self.current_app} application" if self.current_app else None)
            if target_topic:
                params["query"] = target_topic

        return params

    def clear(self):
        """Clears all stored conversational context."""
        self.last_interaction_time = 0.0
        self.current_file = None
        self.current_language = None
        self.current_app = None
        self.last_intent = None
        self.last_compiler_output = None
        self.last_error_analysis = None


# Global conversation context instance
conversation_context = ConversationContext()
