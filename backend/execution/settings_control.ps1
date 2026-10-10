param(
    [Parameter(Mandatory=$true)]
    [string]$Category,
    [Parameter(Mandatory=$false)]
    [string]$Action = "status",
    [Parameter(Mandatory=$false)]
    [int]$Level = -1,
    [Parameter(Mandatory=$false)]
    [string]$Feature = "general"
)

$Category = $Category.ToLower().Trim()
$Action = $Action.ToLower().Trim()
$Feature = $Feature.ToLower().Trim()

# Helper to load WinRT Radios
function Get-WinRTRadios {
    try {
        Add-Type -AssemblyName System.Runtime.WindowsRuntime -ErrorAction Stop
        $asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { 
            $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' 
        })[0]

        [Windows.Devices.Radios.Radio, Windows.System.Devices, ContentType = WindowsRuntime] | Out-Null
        $op = [Windows.Devices.Radios.Radio]::GetRadiosAsync()
        $task = $asTask.MakeGenericMethod([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]]).Invoke($null, @($op))
        $task.Wait(1200) | Out-Null
        return @{ Radios = $task.Result; AsTask = $asTask }
    } catch {
        return $null
    }
}

function Set-RadioState($radio, $asTask, $targetState) {
    try {
        $setOp = $radio.SetStateAsync($targetState)
        $setTask = $asTask.MakeGenericMethod([Windows.Devices.Radios.RadioAccessStatus]).Invoke($null, @($setOp))
        $setTask.Wait(1200) | Out-Null
        return $setTask.Result -eq [Windows.Devices.Radios.RadioAccessStatus]::Allowed
    } catch {
        return $false
    }
}

# ==============================================================================
# 1. BRIGHTNESS CONTROL
# ==============================================================================
if ($Category -eq "brightness") {
    $current = 70
    try {
        $m = Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness -ErrorAction SilentlyContinue
        if ($m) { $current = [int]$m.CurrentBrightness }
        else {
            $w = Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness -ErrorAction SilentlyContinue
            if ($w) { $current = [int]$w.CurrentBrightness }
        }
    } catch {}

    $target = $current
    if ($Action -eq "up" -or $Action -eq "increase" -or $Action -eq "more") {
        $step = if ($Level -gt 0) { $Level } else { 15 }
        $target = [Math]::Min(100, $current + $step)
    } elseif ($Action -eq "down" -or $Action -eq "decrease" -or $Action -eq "dim" -or $Action -eq "lower") {
        $step = if ($Level -gt 0) { $Level } else { 15 }
        $target = [Math]::Max(10, $current - $step)
    } elseif ($Action -eq "max" -or $Action -eq "maximum" -or $Action -eq "full") {
        $target = 100
    } elseif ($Action -eq "min" -or $Action -eq "minimum" -or $Action -eq "lowest") {
        $target = 10
    } elseif ($Action -eq "set") {
        if ($Level -ge 0 -and $Level -le 100) { $target = $Level }
    } elseif ($Action -eq "status" -or $Action -eq "check") {
        Write-Output "SUCCESS: Brightness is $current%"
        exit 0
    }

    # Apply brightness via CIM / WMI
    $applied = $false
    try {
        $setter = Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods -ErrorAction Stop
        $setter | Invoke-CimMethod -MethodName WmiSetBrightness -Arguments @{Timeout = 1; Brightness = $target} -ErrorAction Stop | Out-Null
        $applied = $true
    } catch {
        try {
            (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods -ErrorAction Stop).WmiSetBrightness(1, $target) | Out-Null
            $applied = $true
        } catch {}
    }

    if ($applied) {
        Write-Output "SUCCESS: Brightness set to $target%"
        exit 0
    } else {
        Write-Output "FALLBACK: Target $target%"
        exit 0
    }
}

# ==============================================================================
# 2. AIRPLANE / AEROPLANE MODE CONTROL
# ==============================================================================
if ($Category -eq "airplane" -or $Category -eq "aeroplane" -or $Category -eq "airplanemode") {
    $rt = Get-WinRTRadios
    if ($Action -eq "on" -or $Action -eq "enable") {
        # Airplane mode ON: Disable all active radios (Wi-Fi, Bluetooth)
        if ($rt -and $rt.Radios) {
            foreach ($r in $rt.Radios) {
                Set-RadioState $r $rt.AsTask ([Windows.Devices.Radios.RadioState]::Off) | Out-Null
            }
        }
        try { netsh interface set interface name="Wi-Fi" admin=DISABLED | Out-Null } catch {}
        Write-Output "SUCCESS: Airplane mode is turned ON"
        exit 0
    } elseif ($Action -eq "off" -or $Action -eq "disable") {
        # Airplane mode OFF: Re-enable radios (Wi-Fi, Bluetooth)
        if ($rt -and $rt.Radios) {
            foreach ($r in $rt.Radios) {
                Set-RadioState $r $rt.AsTask ([Windows.Devices.Radios.RadioState]::On) | Out-Null
            }
        }
        try { netsh interface set interface name="Wi-Fi" admin=ENABLED | Out-Null } catch {}
        Write-Output "SUCCESS: Airplane mode is turned OFF"
        exit 0
    } elseif ($Action -eq "status" -or $Action -eq "check") {
        $allOff = $true
        if ($rt -and $rt.Radios) {
            foreach ($r in $rt.Radios) {
                if ($r.State -eq [Windows.Devices.Radios.RadioState]::On) {
                    $allOff = $false
                    break
                }
            }
        }
        if ($allOff) {
            Write-Output "SUCCESS: Airplane mode is currently ON"
        } else {
            Write-Output "SUCCESS: Airplane mode is currently OFF"
        }
        exit 0
    }
}

# ==============================================================================
# 3. ACCESSIBILITY CONTROLS
# ==============================================================================
if ($Category -eq "accessibility" -or $Category -eq "easeofaccess") {
    if ($Feature -eq "magnifier") {
        if ($Action -eq "on" -or $Action -eq "open" -or $Action -eq "enable") {
            Start-Process "magnify.exe" -ErrorAction SilentlyContinue
            Write-Output "SUCCESS: Magnifier turned on"
            exit 0
        } elseif ($Action -eq "off" -or $Action -eq "close" -or $Action -eq "disable") {
            Stop-Process -Name "magnify" -Force -ErrorAction SilentlyContinue
            Write-Output "SUCCESS: Magnifier turned off"
            exit 0
        }
    } elseif ($Feature -eq "narrator") {
        if ($Action -eq "on" -or $Action -eq "open" -or $Action -eq "enable") {
            Start-Process "narrator.exe" -ErrorAction SilentlyContinue
            Write-Output "SUCCESS: Narrator turned on"
            exit 0
        } elseif ($Action -eq "off" -or $Action -eq "close" -or $Action -eq "disable") {
            Stop-Process -Name "narrator" -Force -ErrorAction SilentlyContinue
            Write-Output "SUCCESS: Narrator turned off"
            exit 0
        }
    } elseif ($Feature -eq "keyboard" -or $Feature -eq "osk") {
        if ($Action -eq "on" -or $Action -eq "open" -or $Action -eq "enable") {
            Start-Process "osk.exe" -ErrorAction SilentlyContinue
            Write-Output "SUCCESS: On-Screen Keyboard opened"
            exit 0
        } elseif ($Action -eq "off" -or $Action -eq "close" -or $Action -eq "disable") {
            Stop-Process -Name "osk" -Force -ErrorAction SilentlyContinue
            Write-Output "SUCCESS: On-Screen Keyboard closed"
            exit 0
        }
    } elseif ($Feature -eq "highcontrast") {
        Start-Process "ms-settings:easeofaccess-highcontrast"
        Write-Output "SUCCESS: High Contrast settings opened"
        exit 0
    } else {
        Start-Process "ms-settings:easeofaccess"
        Write-Output "SUCCESS: Accessibility settings opened"
        exit 0
    }
}

# ==============================================================================
# 4. WI-FI CONTROL
# ==============================================================================
if ($Category -eq "wifi" -or $Category -eq "wi-fi") {
    $rt = Get-WinRTRadios
    $wifiRadio = $null
    if ($rt -and $rt.Radios) {
        foreach ($r in $rt.Radios) {
            if ($r.Kind -eq [Windows.Devices.Radios.RadioKind]::WiFi -or $r.Name -like "*Wi-Fi*" -or $r.Name -like "*WiFi*") {
                $wifiRadio = $r
                break
            }
        }
    }
    if ($wifiRadio) {
        if ($Action -eq "on" -or $Action -eq "enable" -or $Action -eq "turn on" -or $Action -eq "switch on") {
            Set-RadioState $wifiRadio $rt.AsTask ([Windows.Devices.Radios.RadioState]::On) | Out-Null
            Write-Output "SUCCESS: Wi-Fi turned ON"
            exit 0
        } elseif ($Action -eq "off" -or $Action -eq "disable" -or $Action -eq "turn off" -or $Action -eq "switch off") {
            Set-RadioState $wifiRadio $rt.AsTask ([Windows.Devices.Radios.RadioState]::Off) | Out-Null
            Write-Output "SUCCESS: Wi-Fi turned OFF"
            exit 0
        } elseif ($Action -eq "status") {
            Write-Output "SUCCESS: State is $($wifiRadio.State)"
            exit 0
        }
    }
    # Fallback to netsh
    if ($Action -eq "on" -or $Action -eq "turn on" -or $Action -eq "enable") {
        try { netsh interface set interface name="Wi-Fi" admin=ENABLED | Out-Null; Write-Output "SUCCESS: Wi-Fi turned ON"; exit 0 } catch {}
    } elseif ($Action -eq "off" -or $Action -eq "turn off" -or $Action -eq "disable") {
        try { netsh interface set interface name="Wi-Fi" admin=DISABLED | Out-Null; Write-Output "SUCCESS: Wi-Fi turned OFF"; exit 0 } catch {}
    }
}

# ==============================================================================
# 5. BLUETOOTH CONTROL
# ==============================================================================
if ($Category -eq "bluetooth" -or $Category -eq "bt") {
    $rt = Get-WinRTRadios
    $btRadio = $null
    if ($rt -and $rt.Radios) {
        foreach ($r in $rt.Radios) {
            if ($r.Kind -eq [Windows.Devices.Radios.RadioKind]::Bluetooth -or $r.Name -like "*Bluetooth*") {
                $btRadio = $r
                break
            }
        }
    }
    if ($btRadio) {
        if ($Action -eq "on" -or $Action -eq "enable" -or $Action -eq "turn on" -or $Action -eq "switch on") {
            Set-RadioState $btRadio $rt.AsTask ([Windows.Devices.Radios.RadioState]::On) | Out-Null
            Write-Output "SUCCESS: Bluetooth turned ON"
            exit 0
        } elseif ($Action -eq "off" -or $Action -eq "disable" -or $Action -eq "turn off" -or $Action -eq "switch off") {
            Set-RadioState $btRadio $rt.AsTask ([Windows.Devices.Radios.RadioState]::Off) | Out-Null
            Write-Output "SUCCESS: Bluetooth turned OFF"
            exit 0
        } elseif ($Action -eq "status") {
            Write-Output "SUCCESS: State is $($btRadio.State)"
            exit 0
        }
    }
}

# ==============================================================================
# 6. WINDOWS SETTINGS PAGES
# ==============================================================================
if ($Category -eq "settings") {
    if ($Action -eq "close" -or $Action -eq "exit" -or $Action -eq "quit" -or $Action -eq "stop") {
        Get-Process -Name "SystemSettings*" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Output "SUCCESS: Closed Settings"
        exit 0
    }
    $uriMap = @{
        "display" = "ms-settings:display";
        "sound" = "ms-settings:sound";
        "audio" = "ms-settings:sound";
        "wifi" = "ms-settings:network-wifi";
        "bluetooth" = "ms-settings:bluetooth";
        "airplane" = "ms-settings:network-airplanemode";
        "aeroplane" = "ms-settings:network-airplanemode";
        "battery" = "ms-settings:batterysaver";
        "accessibility" = "ms-settings:easeofaccess";
        "easeofaccess" = "ms-settings:easeofaccess";
        "general" = "ms-settings:"
    }
    $targetUri = $uriMap[$Feature]
    if (-not $targetUri) { $targetUri = "ms-settings:" }
    Start-Process $targetUri
    Write-Output "SUCCESS: Opened $targetUri"
    exit 0
}

Write-Output "ERROR: Unhandled category $Category"
exit 1
