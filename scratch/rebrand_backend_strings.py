import re
import os

files_to_update = [
    r"c:\Users\mones\OneDrive\Desktop\Vikram AI\backend\security\permissions.py",
    r"c:\Users\mones\OneDrive\Desktop\Vikram AI\backend\security\policy_engine.py",
    r"c:\Users\mones\OneDrive\Desktop\Vikram AI\backend\service\background_service.py",
    r"c:\Users\mones\OneDrive\Desktop\Vikram AI\backend\monitoring\battery_monitor.py",
    r"c:\Users\mones\OneDrive\Desktop\Vikram AI\frontend\css\core.css"
]

for file_path in files_to_update:
    if not os.path.exists(file_path):
        continue
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    text = text.replace("Hey Vikram", "Hey Doom")
    text = text.replace("VIKRAM Background Service is ONLINE", "DOOM AI Background Service is ONLINE")
    text = text.replace("VIKRAM Background Service stopped", "DOOM AI Background Service stopped")
    text = text.replace("VIKRAM Battery Monitor", "DOOM AI Battery Monitor")
    text = text.replace("VIKRAM AI - 3D Holographic Sphere", "DOOM AI - 3D Holographic Sphere")
    text = text.replace("granted for VIKRAM", "granted for DOOM AI")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)

print("Backend string replacements completed successfully.")
