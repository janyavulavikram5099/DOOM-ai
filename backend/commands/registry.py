"""
VIKRAM AI - Action Registry
Formal definition of supported actions, metadata, permission mappings,
confirmation requirements, and verbal response templates.
"""

from typing import Any

ACTION_REGISTRY: dict[str, dict[str, Any]] = {
    "OPEN_APPLICATION": {
        "description": "Launches an authorized desktop application.",
        "permission": "Application Control",
        "confirmation_required": False,
        "voice_template": "Opening {app_name}, Master."
    },
    "CLOSE_APPLICATION": {
        "description": "Closes a running desktop application.",
        "permission": "Application Control",
        "confirmation_required": False,
        "voice_template": "Closing {app_name}, Master."
    },
    "OPEN_WEBSITE": {
        "description": "Navigates to a website in Google Chrome or default browser.",
        "permission": "Browser Control",
        "confirmation_required": False,
        "voice_template": "Opening {website} in {browser}, Master."
    },
    "SEARCH_WEB": {
        "description": "Performs a web search on Google or YouTube.",
        "permission": "Browser Control",
        "confirmation_required": False,
        "voice_template": "Searching {engine} for {query}, Master."
    },
    "OPEN_FILE": {
        "description": "Opens a document or directory in default viewer.",
        "permission": "File Access",
        "confirmation_required": False,
        "voice_template": "Opening {file_name}, Master."
    },
    "CREATE_FILE": {
        "description": "Creates a new source or text file.",
        "permission": "File Access",
        "confirmation_required": False,
        "voice_template": "Created {file_name}, Master."
    },
    "DELETE_FILE": {
        "description": "Permanently removes a file (requires confirmation).",
        "permission": "File Access",
        "confirmation_required": True,
        "voice_template": "File deleted, Master."
    },
    "SEARCH_FILES": {
        "description": "Finds files matching pattern in workspace.",
        "permission": "File Access",
        "confirmation_required": False,
        "voice_template": "Searching for files matching {pattern}, Master."
    },
    "COMPILE_CODE": {
        "description": "Compiles source code (Java, C, C++, etc.).",
        "permission": "File Access",
        "confirmation_required": False,
        "voice_template": "Compiling {file_name}, Master."
    },
    "RUN_CODE": {
        "description": "Executes compiled program or script.",
        "permission": "File Access",
        "confirmation_required": False,
        "voice_template": "Running {file_name}, Master."
    },
    "COMPILE_AND_RUN_CODE": {
        "description": "Compiles and executes in sequence.",
        "permission": "File Access",
        "confirmation_required": False,
        "voice_template": "Compiling and running {file_name}, Master."
    },
    "EXPLAIN_ERROR": {
        "description": "Analyzes compiler or runtime diagnostics.",
        "permission": "File Access",
        "confirmation_required": False,
        "voice_template": "Analyzing error output, Master."
    },
    "SYSTEM_INFO": {
        "description": "Reports real-time system performance telemetry.",
        "permission": "System Information",
        "confirmation_required": False,
        "voice_template": "Here is your system status, Master."
    },
    "VOLUME_CONTROL": {
        "description": "Controls audio volume and mute state.",
        "permission": "System Controls",
        "confirmation_required": False,
        "voice_template": "Volume adjusted, Master."
    },
    "LOCK_DEVICE": {
        "description": "Locks the Windows workstation session.",
        "permission": "System Controls",
        "confirmation_required": False,
        "voice_template": "Locking your laptop, Master."
    },
    "UNLOCK_DEVICE": {
        "description": "Initiates authentication for locked session.",
        "permission": "System Controls",
        "confirmation_required": False,
        "voice_template": "Windows requires your normal authentication, Master."
    },
    "SLEEP_DEVICE": {
        "description": "Puts the Windows machine to sleep.",
        "permission": "System Controls",
        "confirmation_required": False,
        "voice_template": "Putting your computer to sleep, Master."
    },
    "SCREENSHOT": {
        "description": "Captures desktop screen to file.",
        "permission": "System Controls",
        "confirmation_required": False,
        "voice_template": "Screenshot captured, Master."
    },
    "ASK_AI": {
        "description": "Searches the web and uses AI to answer questions in the user's language.",
        "permission": "Browser Control",
        "confirmation_required": False,
        "voice_template": "Let me find that for you, Master."
    },
    "GET_DATE_TIME": {
        "description": "Reports the exact current system date and/or time.",
        "permission": "System Information",
        "confirmation_required": False,
        "voice_template": "{response}"
    },
    "WIFI_CONTROL": {
        "description": "Controls laptop Wi-Fi radio (turn on, turn off, status).",
        "permission": "System Controls",
        "confirmation_required": False,
        "voice_template": "{response}"
    },
    "BLUETOOTH_CONTROL": {
        "description": "Controls laptop Bluetooth radio (turn on, turn off, status).",
        "permission": "System Controls",
        "confirmation_required": False,
        "voice_template": "{response}"
    }
}
