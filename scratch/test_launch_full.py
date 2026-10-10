import os, subprocess, json, re

def launch_app_test(app_name):
    clean_name = app_name.lower().strip()
    clean_name = re.sub(r"^(?:the|my|an|a)\s+", "", clean_name).strip()
    
    # Load catalog
    catalog = {}
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
        print("Catalog load error:", e)

    # 1. Exact match
    target = catalog.get(clean_name)
    
    # 2. Fuzzy match
    if not target:
        for k, v in catalog.items():
            if clean_name == k or f" {clean_name} " in f" {k} " or k.startswith(clean_name):
                target = v
                break

    if target:
        print(f"Target found for '{app_name}': {target}")
        try:
            if hasattr(os, "startfile"):
                os.startfile(target)
                return True, f"Opening {app_name}."
            subprocess.Popen(["explorer.exe", target])
            return True, f"Opening {app_name}."
        except Exception as e:
            try:
                subprocess.Popen(["explorer.exe", target])
                return True, f"Opening {app_name}."
            except Exception as e2:
                return False, f"Error: {e2}"
    return False, f"Could not find {app_name}"

success, msg = launch_app_test("whatsapp")
print("Launch result:", success, msg)
