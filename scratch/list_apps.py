import subprocess, json

res = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', 'Get-StartApps | ConvertTo-Json -Compress'], capture_output=True, text=True)
data = json.loads(res.stdout)
print(f"Total apps found: {len(data)}")
for item in sorted(data, key=lambda x: x.get('Name', '')):
    print(f"{item.get('Name')}: {item.get('AppID')}")
