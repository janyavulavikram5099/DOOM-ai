"""
VIKRAM AI - SQLite Database Manager
Handles secure local persistence for device pairing, settings, permissions,
voice profile metadata, and command history.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("vikram.database")

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "vikram.db")


class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Device pairing & identity
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_pairing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                device_name TEXT NOT NULL,
                os_info TEXT NOT NULL,
                paired_at TEXT NOT NULL,
                auth_token TEXT NOT NULL,
                is_paired INTEGER DEFAULT 0
            )
            """)

            # System permissions
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS permissions (
                permission_name TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                is_granted INTEGER DEFAULT 0,
                updated_at TEXT NOT NULL
            )
            """)

            # Voice profile metadata & acoustic fingerprint
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS voice_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT DEFAULT 'Master',
                is_enrolled INTEGER DEFAULT 0,
                sample_count INTEGER DEFAULT 0,
                acoustic_data TEXT,
                confidence_threshold REAL DEFAULT 0.65,
                created_at TEXT NOT NULL
            )
            """)

            # Command history
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                speaker TEXT NOT NULL,
                raw_command TEXT NOT NULL,
                intent TEXT NOT NULL,
                status TEXT NOT NULL,
                vikram_response TEXT NOT NULL,
                details TEXT
            )
            """)

            # General system settings
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """)

            # Initialize default permissions if empty
            cursor.execute("SELECT COUNT(*) as count FROM permissions")
            if cursor.fetchone()["count"] == 0:
                default_permissions = [
                    ("Microphone", "Voice capture & wake-word listening", 1),
                    ("Speech Recognition", "Convert spoken audio to structured commands", 1),
                    ("System Information", "Read CPU, RAM, GPU, storage and battery telemetry", 1),
                    ("Application Control", "Launch and terminate authorized Windows applications", 1),
                    ("File Access", "Read, create, search and modify files in authorized paths", 1),
                    ("Browser Control", "Open web applications and search engines in Chrome", 1),
                    ("System Controls", "Session lock, volume control and power operations", 1),
                    ("Startup Service", "Persistent background monitoring on Windows boot", 1)
                ]
                now = datetime.now(timezone.utc).isoformat()
                for name, desc, granted in default_permissions:
                    cursor.execute(
                        "INSERT INTO permissions (permission_name, description, is_granted, updated_at) VALUES (?, ?, ?, ?)",
                        (name, desc, granted, now)
                    )

            # Initialize default settings
            default_settings = {
                "start_with_windows": "1",
                "minimize_to_tray": "1",
                "background_assistant": "1",
                "wake_word": "Hey Vikram",
                "alternative_wake_word": "Vikram",
                "speaker_verification_enabled": "1",
                "voice_speed": "0",  # SAPI speed -10 to +10
                "voice_name": "Microsoft David Desktop",
                "ai_provider": "local",  # local | cloud | hybrid
                "ai_model": "rule_nlu_v1",
                "hud_density": "high",
                "animation_intensity": "high"
            }
            now = datetime.now(timezone.utc).isoformat()
            for k, v in default_settings.items():
                cursor.execute(
                    "INSERT OR IGNORE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                    (k, v, now)
                )

            conn.commit()

    # --- Pairing Operations ---
    def get_pairing_status(self) -> dict[str, Any] | None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM device_pairing ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def save_pairing(self, device_id: str, device_name: str, os_info: str, auth_token: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
            INSERT OR REPLACE INTO device_pairing (id, device_id, device_name, os_info, paired_at, auth_token, is_paired)
            VALUES (1, ?, ?, ?, ?, ?, 1)
            """, (device_id, device_name, os_info, now, auth_token))
            conn.commit()
            return True

    def reset_pairing(self) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM device_pairing")
            cursor.execute("DELETE FROM voice_profiles")
            conn.commit()
            return True

    # --- Permissions Operations ---
    def get_permissions(self) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM permissions")
            return [dict(row) for row in cursor.fetchall()]

    def set_permission(self, name: str, is_granted: bool) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
            UPDATE permissions SET is_granted = ?, updated_at = ? WHERE permission_name = ?
            """, (1 if is_granted else 0, now, name))
            conn.commit()
            return cursor.rowcount > 0

    def is_permission_granted(self, name: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_granted FROM permissions WHERE permission_name = ?", (name,))
            row = cursor.fetchone()
            return bool(row["is_granted"]) if row else False

    # --- Voice Profile Operations ---
    def get_voice_profile(self) -> dict[str, Any] | None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM voice_profiles ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                res = dict(row)
                if res.get("acoustic_data"):
                    try:
                        res["acoustic_data"] = json.loads(res["acoustic_data"])
                    except (json.JSONDecodeError, TypeError, ValueError):
                        res["acoustic_data"] = None
                return res
            return None

    def save_voice_profile(self, user_name: str, sample_count: int, acoustic_data: Any, confidence_threshold: float = 0.65) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            acoustic_str = json.dumps(acoustic_data) if acoustic_data is not None else None
            cursor.execute("""
            INSERT OR REPLACE INTO voice_profiles (id, user_name, is_enrolled, sample_count, acoustic_data, confidence_threshold, created_at)
            VALUES (1, ?, 1, ?, ?, ?, ?)
            """, (user_name, sample_count, acoustic_str, confidence_threshold, now))
            conn.commit()
            return True

    # --- Command History Operations ---
    def add_command_history(self, speaker: str, raw_command: str, intent: str, status: str, vikram_response: str, details: str | None = None) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
            INSERT INTO command_history (timestamp, speaker, raw_command, intent, status, vikram_response, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (now, speaker, raw_command, intent, status, vikram_response, details))
            conn.commit()
            return cursor.lastrowid or 0

    def get_command_count(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM command_history")
            row = cursor.fetchone()
            return int(row["cnt"]) if row else 0

    def get_command_history(self, limit: int | None = None) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if limit is not None and limit > 0:
                cursor.execute("SELECT * FROM command_history ORDER BY id DESC LIMIT ?", (limit,))
            else:
                cursor.execute("SELECT * FROM command_history ORDER BY id DESC")
            return [dict(row) for row in cursor.fetchall()]

    def clear_command_history(self) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM command_history")
            conn.commit()
            return True

    # --- Settings Operations ---
    def get_setting(self, key: str, default: str | None = None) -> str | None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).isoformat()
            cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
            """, (key, value, now))
            conn.commit()
            return True

    def get_all_settings(self) -> dict[str, str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            return {row["key"]: row["value"] for row in cursor.fetchall()}


# Global singleton instance
db = Database()
