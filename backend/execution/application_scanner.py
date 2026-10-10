"""
VIKRAM AI / DOOM AI - Full-Device Application Scanner & Controller Access
Discovers, indexes, and establishes control access for all installed applications across Windows:
1. Windows Store / UWP / MSIX applications (Get-StartApps & shell:AppsFolder)
2. Start Menu Shortcuts (%ProgramData% and %APPDATA%)
3. Windows Registry Uninstall keys (HKLM & HKCU 64-bit and 32-bit)
4. System Binaries & Executables in standard directories and PATH
"""

import json
import logging
import os
import re
import shutil
import subprocess
import threading
from typing import Any

logger = logging.getLogger("vikram.execution.scanner")

CACHE_FILE = os.path.join(os.path.dirname(__file__), "installed_apps.json")


class ApplicationScanner:
    _catalog: dict[str, dict[str, Any]] = {}
    _is_scanned: bool = False
    _scan_lock = threading.Lock()

    @classmethod
    def scan_all_applications(cls, force: bool = False) -> dict[str, dict[str, Any]]:
        """
        Scans the entire Windows device for all installed apps and establishes control access.
        Returns a dictionary mapping normalized app name to its launch/control metadata.
        """
        with cls._scan_lock:
            if cls._is_scanned and not force:
                return cls._catalog

            logger.info("Scanning whole device for installed applications and establishing control access...")
            apps: dict[str, dict[str, Any]] = {}

            # 1. Load existing cache if present
            if os.path.exists(CACHE_FILE):
                try:
                    with open(CACHE_FILE, "r", encoding="utf-8") as f:
                        cached = json.load(f)
                        if isinstance(cached, dict):
                            for k, v in cached.items():
                                if isinstance(v, str):
                                    apps[k] = {"target": v, "type": "cached", "name": k}
                                elif isinstance(v, dict):
                                    apps[k] = v
                except Exception as e:
                    logger.debug(f"Cache read error: {e}")

            # 2. Scan Start Menu shortcuts
            shortcut_dirs = [
                os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
                os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs")
            ]
            for sdir in shortcut_dirs:
                if os.path.exists(sdir):
                    for root, _, files in os.walk(sdir):
                        for f in files:
                            if f.lower().endswith(".lnk"):
                                raw_name = os.path.splitext(f)[0]
                                clean_name = raw_name.lower().strip()
                                clean_key = re.sub(r"[^\w\s]", "", clean_name).strip()
                                full_path = os.path.join(root, f)
                                
                                meta = {
                                    "target": full_path,
                                    "type": "shortcut",
                                    "name": raw_name,
                                    "clean_name": clean_name
                                }
                                if clean_name not in apps:
                                    apps[clean_name] = meta
                                if clean_key and clean_key not in apps:
                                    apps[clean_key] = meta

            # 3. Scan Windows Registry (HKLM and HKCU Uninstall keys)
            if os.name == "nt":
                try:
                    import winreg
                    reg_paths = [
                        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                    ]
                    for root_key, sub_path in reg_paths:
                        try:
                            with winreg.OpenKey(root_key, sub_path) as key:
                                num_subkeys = winreg.QueryInfoKey(key)[0]
                                for i in range(num_subkeys):
                                    try:
                                        sub_name = winreg.EnumKey(key, i)
                                        with winreg.OpenKey(key, sub_name) as app_key:
                                            try:
                                                disp_name, _ = winreg.QueryValueEx(app_key, "DisplayName")
                                                disp_name = str(disp_name).strip()
                                            except OSError:
                                                continue

                                            install_loc = ""
                                            try:
                                                install_loc, _ = winreg.QueryValueEx(app_key, "InstallLocation")
                                                install_loc = str(install_loc).strip()
                                            except OSError:
                                                pass

                                            clean = disp_name.lower()
                                            clean_k = re.sub(r"[^\w\s]", "", clean).strip()
                                            if clean and clean not in apps and install_loc:
                                                apps[clean] = {
                                                    "target": install_loc,
                                                    "type": "registry",
                                                    "name": disp_name,
                                                    "clean_name": clean
                                                }
                                            if clean_k and clean_k not in apps and install_loc:
                                                apps[clean_k] = {
                                                    "target": install_loc,
                                                    "type": "registry",
                                                    "name": disp_name,
                                                    "clean_name": clean_k
                                                }
                                    except Exception:
                                        continue
                        except Exception:
                            continue
                except Exception as e:
                    logger.debug(f"Registry scanning notice: {e}")

            # 4. Query Windows Store / UWP apps via Get-StartApps
            if os.name == "nt":
                try:
                    ps_cmd = "Get-StartApps | ConvertTo-Json -Compress"
                    res = subprocess.run(
                        ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        check=False
                    )
                    if res.returncode == 0 and res.stdout.strip():
                        data = json.loads(res.stdout)
                        items = data if isinstance(data, list) else [data]
                        for item in items:
                            name = item.get("Name", "").strip()
                            clean_name = name.lower()
                            clean_k = re.sub(r"[^\w\s]", "", clean_name).strip()
                            app_id = item.get("AppID", "").strip()
                            if name and app_id:
                                is_exe = os.path.exists(app_id) or ":\\" in app_id or app_id.lower().endswith((".exe", ".lnk", ".bat", ".cmd"))
                                target = app_id if is_exe else f"shell:AppsFolder\\{app_id}"
                                meta = {
                                    "target": target,
                                    "type": "uwp" if not is_exe else "win32",
                                    "name": name,
                                    "app_id": app_id,
                                    "clean_name": clean_name
                                }
                                apps[clean_name] = meta
                                if clean_k and clean_k not in apps:
                                    apps[clean_k] = meta
                except Exception as e:
                    logger.debug(f"Get-StartApps query notice: {e}")

            cls._catalog = apps
            cls._is_scanned = True
            logger.info(f"Device scan complete: DOOM AI has taken control access of {len(apps)} applications.")

            # Persist back to cache file
            try:
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    simplified = {k: v.get("target") if isinstance(v, dict) else v for k, v in apps.items()}
                    json.dump(simplified, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.debug(f"Failed to persist installed_apps.json: {e}")

            return cls._catalog

    @classmethod
    def get_catalog(cls) -> dict[str, dict[str, Any]]:
        """Returns the cached applications catalog, scanning on first call."""
        if not cls._is_scanned:
            return cls.scan_all_applications()
        return cls._catalog

    @classmethod
    def find_app(cls, query: str) -> dict[str, Any] | None:
        """Finds application metadata matching a name or alias."""
        clean = query.lower().strip()
        clean = re.sub(r"^(?:the|my|an|a)\s+", "", clean).strip()
        catalog = cls.get_catalog()

        # 1. Exact match
        if clean in catalog:
            meta = catalog[clean]
            return meta if isinstance(meta, dict) else {"target": meta, "name": clean}

        # 2. Key without punctuation
        clean_k = re.sub(r"[^\w\s]", "", clean).strip()
        if clean_k in catalog:
            meta = catalog[clean_k]
            return meta if isinstance(meta, dict) else {"target": meta, "name": clean}

        # 3. Substring / Boundary matching
        for k, v in catalog.items():
            if (
                clean == k
                or f" {clean} " in f" {k} "
                or k.startswith(f"{clean} ")
                or k.endswith(f" {clean}")
                or (len(clean) >= 4 and clean in k)
            ):
                return v if isinstance(v, dict) else {"target": v, "name": k}

        return None

    @classmethod
    def start_background_scanner(cls):
        """Asynchronously scans and establishes control access in the background without blocking server startup."""
        thread = threading.Thread(target=cls.scan_all_applications, daemon=True, name="DOOMAppScanner")
        thread.start()


# Export singleton alias for convenience
application_scanner = ApplicationScanner

