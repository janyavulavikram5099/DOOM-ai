import time
import subprocess

t0 = time.time()
ps = """
Get-PnpDevice -Class Bluetooth | Where-Object { $_.InstanceId -like 'BTHENUM\\DEV_*' -or $_.InstanceId -like 'BTHLE\\DEV_*' } | ForEach-Object {
    $p = Get-PnpDeviceProperty -InstanceId $_.InstanceId -KeyName '{83da6326-97a6-4088-9453-a1923f573b29} 15' -ErrorAction SilentlyContinue
    if ($p -and $p.Data -eq $true) {
        $_.FriendlyName
    }
}
"""

res = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
devices = [d.strip() for d in res.stdout.strip().splitlines() if d.strip()]
print("Connected Bluetooth Devices:", devices)
print(f"Elapsed: {time.time() - t0:.2f}s")
