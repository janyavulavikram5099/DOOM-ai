import os, subprocess, json

# Test mapping for key apps
test_apps = {
    "whatsapp": "5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App",
    "calculator": "Microsoft.WindowsCalculator_8wekyb3d8bbwe!App",
    "notepad": "Microsoft.WindowsNotepad_8wekyb3d8bbwe!App",
    "settings": "windows.immersivecontrolpanel_cw5n1h2txyewy!microsoft.windows.immersivecontrolpanel"
}

for name, app_id in test_apps.items():
    target = f"shell:AppsFolder\\{app_id}"
    try:
        os.startfile(target)
        print(f"SUCCESS: Launched {name} via {target}")
    except Exception as e:
        print(f"FAILED: {name} via {target}: {e}")
