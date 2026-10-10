import os, subprocess, json, re

def build_installed_catalog():
    catalog = {}
    
    # 1. Query Get-StartApps
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", "Get-StartApps | ConvertTo-Json -Compress"],
            capture_output=True, text=True, timeout=8, check=False
        )
        if res.returncode == 0 and res.stdout.strip():
            items = json.loads(res.stdout)
            if not isinstance(items, list):
                items = [items]
            for it in items:
                name = it.get("Name", "").strip()
                appid = it.get("AppID", "").strip()
                if name and appid:
                    k = name.lower()
                    clean_k = re.sub(r"[^\w\s]", "", k).strip()
                    target = appid if (os.path.exists(appid) or ":\\" in appid or appid.lower().endswith((".exe", ".lnk", ".bat", ".cmd"))) else f"shell:AppsFolder\\{appid}"
                    catalog[k] = target
                    if clean_k and clean_k not in catalog:
                        catalog[clean_k] = target
    except Exception as e:
        print("Error Get-StartApps:", e)
        
    return catalog

cat = build_installed_catalog()
print(f"Catalog entries: {len(cat)}")
for test in ["whatsapp", "roblox player", "word", "excel", "calculator", "notepad", "chrome", "settings"]:
    match = cat.get(test)
    if not match:
        for k, v in cat.items():
            if test == k or f" {test} " in f" {k} " or k.startswith(test):
                match = v
                break
    print(f"App '{test}' -> {match}")
