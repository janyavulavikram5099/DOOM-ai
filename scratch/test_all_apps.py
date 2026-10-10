import os
import sys

sys.path.insert(0, r"c:\Users\mones\OneDrive\Desktop\Vikram AI")

from backend.execution.application_executor import ApplicationExecutor, _INSTALLED_APPS_CACHE, APP_MAP, URI_MAP
from backend.ai.intent_parser import IntentParser

test_apps = [
    ("roblox", "roblox"),
    ("robolox", "roblox"),
    ("roblox player", "roblox player"),
    ("robolox player", "roblox player"),
    ("roblox studio", "roblox studio"),
    ("chrome", "chrome"),
    ("google chrome", "google chrome"),
    ("edge", "edge"),
    ("microsoft edge", "microsoft edge"),
    ("opera", "opera"),
    ("opera gx", "opera gx"),
    ("notepad", "notepad"),
    ("notepad++", "notepad++"),
    ("calculator", "calculator"),
    ("file explorer", "file explorer"),
    ("task manager", "task manager"),
    ("vs code", "vs code"),
    ("vscode", "vscode"),
    ("intellij", "intellij"),
    ("postman", "postman"),
    ("docker", "docker"),
    ("dev-c++", "dev-c++"),
    ("word", "word"),
    ("excel", "excel"),
    ("powerpoint", "powerpoint"),
    ("vantage", "vantage"),
    ("settings", "settings"),
    ("terminal", "terminal"),
]

print(f"Total apps in cache: {len(_INSTALLED_APPS_CACHE)}")
print("=" * 60)

passed = 0
for raw_name, clean in test_apps:
    # 1. Test intent parsing
    parsed_open = IntentParser.parse(f"open {raw_name}")
    parsed_close = IntentParser.parse(f"close {raw_name}")
    intent_ok = (
        parsed_open.get("intent") == "OPEN_APPLICATION"
        and parsed_close.get("intent") == "CLOSE_APPLICATION"
    )

    # 2. Check if known by ApplicationExecutor
    # Check in cache or APP_MAP or URI_MAP or special launcher
    in_cache = any(raw_name in k or k in raw_name for k in _INSTALLED_APPS_CACHE)
    in_map = (
        raw_name in APP_MAP
        or raw_name in URI_MAP
        or raw_name in ["roblox", "robolox", "roblox player", "robolox player", "roblox studio", "robolox studio", "opera", "opera gx", "file explorer"]
    )

    status = "OK" if (intent_ok and (in_cache or in_map)) else "FAIL"
    if status == "OK":
        passed += 1
    print(f"[{status}] {raw_name:20} | Intent: {intent_ok!s:5} | Catalog/Map: {in_cache or in_map}")

print("=" * 60)
print(f"Result: {passed}/{len(test_apps)} apps fully configured and recognized.")
