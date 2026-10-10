import subprocess

# Query Bluetooth devices
ps_script = """
Get-PnpDevice -Class Bluetooth | Where-Object { $_.Status -eq 'OK' -and $_.Present -eq $true } | Select-Object FriendlyName, InstanceId, Status, Present | Format-Table -AutoSize
"""

res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True)
print("PnpDevice Bluetooth:")
print(res.stdout)

# Check connected Bluetooth devices using Windows.Devices.Bluetooth or Win32_PnPEntity
ps_script2 = """
Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPClass -eq 'Bluetooth' -or $_.Service -eq 'BthEnum' -or $_.Service -eq 'BthA2DP' -or $_.Service -eq 'BthHFP' } | Select-Object Name, Present, Status | Format-Table -AutoSize
"""
res2 = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script2], capture_output=True, text=True)
print("Win32_PnPEntity Bluetooth:")
print(res2.stdout)
