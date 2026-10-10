import subprocess
import time

t0 = time.time()
ps = """
Get-ChildItem 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\BTHPORT\\Parameters\\Devices' | ForEach-Object {
    $name = $_.GetValue('Name')
    if ($name) {
        $strName = [System.Text.Encoding]::ASCII.GetString($name).Trim([char]0)
        Write-Host "Reg Device:" $strName
    }
}
"""
res = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
print(res.stdout)
print(f"Elapsed: {time.time() - t0:.2f}s")
