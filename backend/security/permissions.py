"""
VIKRAM AI - Permission Architecture
Implements least-privilege permission checking for Windows operations.
"""

from typing import Any

from ..database.sqlite import db


class PermissionManager:
    # Pre-defined permission definitions with clear rationale
    PERMISSIONS = {
        "Microphone": {
            "title": "Microphone Access",
            "description": "Continuous acoustic monitoring for the 'Hey Doom' wake word.",
            "risk": "Low"
        },
        "Speech Recognition": {
            "title": "Speech Recognition",
            "description": "Convert incoming speech into structured command intents.",
            "risk": "Low"
        },
        "System Information": {
            "title": "System Telemetry",
            "description": "Read CPU, RAM, GPU, storage, battery, and network status.",
            "risk": "Low"
        },
        "Application Control": {
            "title": "Application Management",
            "description": "Launch and close permitted Windows software (e.g. VS Code, Chrome).",
            "risk": "Medium"
        },
        "File Access": {
            "title": "File System Operations",
            "description": "Find, read, create, compile, and run code files.",
            "risk": "Medium"
        },
        "Browser Control": {
            "title": "Browser Navigation",
            "description": "Open websites, search engines, and YouTube in Google Chrome.",
            "risk": "Low"
        },
        "System Controls": {
            "title": "System Power & Lock",
            "description": "Control volume, display, and lock Windows session.",
            "risk": "Medium"
        },
        "Startup Service": {
            "title": "Windows Startup Service",
            "description": "Enable background assistant to initialize when Windows boots.",
            "risk": "Low"
        }
    }

    @classmethod
    def list_permissions(cls) -> list[dict[str, Any]]:
        """Returns the list of permissions with status and description."""
        db_perms = {p["permission_name"]: p["is_granted"] for p in db.get_permissions()}
        results = []
        for name, meta in cls.PERMISSIONS.items():
            results.append({
                "name": name,
                "title": meta["title"],
                "description": meta["description"],
                "risk": meta["risk"],
                "is_granted": bool(db_perms.get(name, 1))
            })
        return results

    @classmethod
    def is_granted(cls, permission_name: str) -> bool:
        """Checks if a given permission is granted."""
        return db.is_permission_granted(permission_name)

    @classmethod
    def set_permission(cls, permission_name: str, granted: bool) -> bool:
        """Updates a permission state in the database."""
        return db.set_permission(permission_name, granted)

    @classmethod
    def grant_all(cls) -> bool:
        """Grants all default permissions during setup."""
        for name in cls.PERMISSIONS.keys():
            db.set_permission(name, True)
        return True
