import subprocess

ps = """
$devs = Get-PnpDevice -Class Bluetooth | Where-Object { $_.InstanceId -like 'BTHENUM\\DEV_*' -or $_.InstanceId -like 'BTHLE\\DEV_*' }
foreach ($d in $devs) {
    $conn = $null
    try {
        $prop = Get-PnpDeviceProperty -InstanceId $d.InstanceId -KeyName '{83da6326-97a6-4088-9453-a1923f573b29} 15' -ErrorAction SilentlyContinue
        if ($prop) { $conn = $prop.Data }
    } catch {}
    
    # Also check DEVPKEY_Device_IsConnected
    $isConn = $null
    try {
        $p2 = Get-PnpDeviceProperty -InstanceId $d.InstanceId -KeyName 'DEVPKEY_Device_IsConnected' -ErrorAction SilentlyContinue
        if ($p2) { $isConn = $p2.Data }
    } catch {}

    Write-Host "Device:" $d.FriendlyName "| Connected1:" $conn "| IsConnected:" $isConn
}
"""

res = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
print(res.stdout)
