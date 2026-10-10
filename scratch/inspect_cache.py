from backend.execution.application_executor import _INSTALLED_APPS_CACHE, _refresh_installed_apps
_refresh_installed_apps()

print("Total apps in cache:", len(_INSTALLED_APPS_CACHE))
sample_keys = [
    "chrome", "google chrome", "edge", "microsoft edge", "file explorer", "explorer",
    "whatsapp", "store", "microsoft store", "settings", "outlook", "lenovo vantage",
    "notepad", "calculator", "calc", "word", "excel", "powerpoint", "copilot", "vs code", "vscode"
]

for k in sample_keys:
    val = _INSTALLED_APPS_CACHE.get(k)
    fuzzy = [item for item in _INSTALLED_APPS_CACHE.items() if k in item[0] or item[0] in k]
    print(f"Key: '{k}' -> Exact: '{val}' | Fuzzy: {fuzzy[:1]}")
