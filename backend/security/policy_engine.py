"""
VIKRAM AI - Security Policy Engine
Enforces strict boundaries:
1. Never routes LLM/natural language to raw, unvalidated shell commands.
2. Validates structured intents, parameter types, paths, and limits.
3. Enforces least-privilege checks via PermissionManager.
4. Identifies destructive/high-impact actions and demands confirmation.
"""

import logging
import os
import re
from typing import Any

from .permissions import PermissionManager

logger = logging.getLogger("vikram.security.policy")

# Deny-listed hazardous patterns or system areas
DANGEROUS_PATTERNS = [
    r"rmdir\s+/s",
    r"format\s+[a-z]:",
    r"reg\s+delete",
    r"del\s+/[sfq]",
    r":\(\)\{ :\|:& \};:",  # fork bomb
    r"powershell\s+.*-(enc|encodedcommand)",
    r"rundll32",
    r"vssadmin\s+delete\s+shadows"
]

CRITICAL_PATHS = [
    r"^[a-zA-Z]:\\Windows",
    r"^[a-zA-Z]:\\Program Files",
    r"^[a-zA-Z]:\\System Volume Information"
]


class PolicyViolation(Exception):
    pass


class PolicyEngine:
    @staticmethod
    def validate_action(intent: str, params: dict[str, Any]) -> tuple[bool, str, bool]:
        """
        Validates whether a structured action is permitted.
        Returns: (is_allowed: bool, reason_or_message: str, requires_confirmation: bool)
        """
        # Map intents to required permissions
        permission_map = {
            "OPEN_APPLICATION": "Application Control",
            "CLOSE_APPLICATION": "Application Control",
            "OPEN_WEBSITE": "Browser Control",
            "SEARCH_WEB": "Browser Control",
            "OPEN_FILE": "File Access",
            "READ_FILE": "File Access",
            "CREATE_FILE": "File Access",
            "RENAME_FILE": "File Access",
            "MOVE_FILE": "File Access",
            "COPY_FILE": "File Access",
            "DELETE_FILE": "File Access",
            "SEARCH_FILES": "File Access",
            "COMPILE_CODE": "File Access",
            "RUN_CODE": "File Access",
            "EXPLAIN_ERROR": "File Access",
            "SYSTEM_INFO": "System Information",
            "VOLUME_CONTROL": "System Controls",
            "BRIGHTNESS_CONTROL": "System Controls",
            "AIRPLANE_MODE_CONTROL": "System Controls",
            "ACCESSIBILITY_CONTROL": "System Controls",
            "OPEN_SETTINGS": "System Controls",
            "WIFI_CONTROL": "System Controls",
            "BLUETOOTH_CONTROL": "System Controls",
            "LOCK_DEVICE": "System Controls",
            "SLEEP_DEVICE": "System Controls",
            "RESTART_DEVICE": "System Controls",
            "SHUTDOWN_DEVICE": "System Controls",
            "SCREENSHOT": "System Controls",
            "EXECUTE_TASK_PLAN": "Application Control"
        }

        required_perm = permission_map.get(intent)
        if required_perm and not PermissionManager.is_granted(required_perm):
            return False, f"Permission '{required_perm}' is not granted for DOOM AI.", False

        # Destructive or high-impact actions requiring explicit confirmation
        high_impact_intents = {
            "DELETE_FILE": "Deleting this file is a destructive action. Should I continue?",
            "SHUTDOWN_DEVICE": "Shutting down your computer will close all running applications. Should I proceed?",
            "RESTART_DEVICE": "Restarting your system requires confirmation. Should I continue?",
        }

        requires_confirmation = intent in high_impact_intents
        confirm_message = high_impact_intents.get(intent, "")

        # Path validation for file operations
        if "file_path" in params or "path" in params:
            target_path = params.get("file_path") or params.get("path") or ""
            norm_path = os.path.normpath(str(target_path))
            for crit in CRITICAL_PATHS:
                if re.search(crit, norm_path, re.IGNORECASE):
                    return False, "Operating system system directories are protected from modification.", False

        # Dangerous command string inspection
        for val in params.values():
            if isinstance(val, str):
                for pattern in DANGEROUS_PATTERNS:
                    if re.search(pattern, val, re.IGNORECASE):
                        logger.warning(f"Blocked dangerous command pattern: {pattern} in {val}")
                        return False, "Action blocked by security policy due to unsafe parameters.", False

        return True, confirm_message or "Allowed", requires_confirmation
