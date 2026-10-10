"""
VIKRAM AI - Security & Device Authentication
Handles device identification, pairing generation (VK-XXXX-XXXX), and secure token handling.
"""

import hashlib
import platform
import secrets
import socket
import uuid
from typing import Any

from ..database.sqlite import db


class DeviceAuthenticator:
    @staticmethod
    def generate_device_id() -> str:
        """Generates a structured, unique device ID formatted as VK-XXXX-XXXX."""
        raw = f"{platform.node()}-{socket.gethostname()}-{uuid.getnode()}"
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()
        return f"VK-{digest[:4]}-{digest[4:8]}"

    @staticmethod
    def generate_session_token() -> str:
        """Generates a cryptographically strong local auth token."""
        return secrets.token_hex(32)

    @classmethod
    def get_system_hardware_info(cls) -> dict[str, Any]:
        """Gathers safe, non-sensitive hardware identification details for detection."""
        return {
            "computer_name": platform.node(),
            "hostname": socket.gethostname(),
            "os": f"Windows {platform.release()} ({platform.version()})",
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }

    @classmethod
    def pair_current_device(cls, custom_device_name: str | None = None) -> dict[str, Any]:
        """Pairs the local Windows machine with VIKRAM."""
        device_id = cls.generate_device_id()
        device_name = custom_device_name or platform.node()
        os_info = f"Windows {platform.release()} ({platform.version()})"
        auth_token = cls.generate_session_token()

        db.save_pairing(device_id, device_name, os_info, auth_token)
        return {
            "device_id": device_id,
            "device_name": device_name,
            "os_info": os_info,
            "is_paired": True,
            "auth_token": auth_token
        }

    @classmethod
    def is_paired(cls) -> bool:
        """Checks if the device is already paired."""
        pairing = db.get_pairing_status()
        return bool(pairing and pairing.get("is_paired"))

    @classmethod
    def get_pairing_info(cls) -> dict[str, Any] | None:
        """Returns pairing details (excluding private tokens from public exposure)."""
        pairing = db.get_pairing_status()
        if not pairing:
            return None
        return {
            "device_id": pairing["device_id"],
            "device_name": pairing["device_name"],
            "os_info": pairing["os_info"],
            "paired_at": pairing["paired_at"],
            "is_paired": bool(pairing["is_paired"])
        }
