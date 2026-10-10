param(
    [Parameter(Mandatory=$true)]
    [string]$Target,
    [Parameter(Mandatory=$false)]
    [string]$Action = "status"
)

$Target = $Target.Trim()
$Action = $Action.ToLower().Trim()

# 1. Primary: Windows Runtime Radio Management API (Works without Admin for both Wi-Fi & Bluetooth)
try {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime -ErrorAction Stop
    $asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { 
        $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' 
    })[0]

    [Windows.Devices.Radios.Radio, Windows.System.Devices, ContentType = WindowsRuntime] | Out-Null
    $op = [Windows.Devices.Radios.Radio]::GetRadiosAsync()
    $task = $asTask.MakeGenericMethod([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]]).Invoke($null, @($op))
    $task.Wait(400) | Out-Null
    $radios = $task.Result

    $matchedRadio = $null
    foreach ($r in $radios) {
        if ($Target -eq "wifi" -or $Target -eq "wi-fi") {
            if ($r.Kind -eq [Windows.Devices.Radios.RadioKind]::WiFi -or $r.Name -like "*Wi-Fi*" -or $r.Name -like "*WiFi*") {
                $matchedRadio = $r
                break
            }
        } elseif ($Target -eq "bluetooth" -or $Target -eq "bt") {
            if ($r.Kind -eq [Windows.Devices.Radios.RadioKind]::Bluetooth -or $r.Name -like "*Bluetooth*") {
                $matchedRadio = $r
                break
            }
        }
    }

    if ($matchedRadio -ne $null) {
        if ($Action -eq "status") {
            Write-Output "SUCCESS: State is $($matchedRadio.State)"
            exit 0
        }

        $targetState = $null
        if ($Action -eq "on" -or $Action -eq "enable") {
            $targetState = [Windows.Devices.Radios.RadioState]::On
        } elseif ($Action -eq "off" -or $Action -eq "disable") {
            $targetState = [Windows.Devices.Radios.RadioState]::Off
        } elseif ($Action -eq "toggle") {
            if ($matchedRadio.State -eq [Windows.Devices.Radios.RadioState]::On) {
                $targetState = [Windows.Devices.Radios.RadioState]::Off
            } else {
                $targetState = [Windows.Devices.Radios.RadioState]::On
            }
        }

        if ($targetState -ne $null) {
            $setOp = $matchedRadio.SetStateAsync($targetState)
            $setTask = $asTask.MakeGenericMethod([Windows.Devices.Radios.RadioAccessStatus]).Invoke($null, @($setOp))
            $setTask.Wait(400) | Out-Null
            if ($setTask.Result -eq [Windows.Devices.Radios.RadioAccessStatus]::Allowed) {
                Write-Output "SUCCESS: Set to $($targetState.ToString())"
                exit 0
            } else {
                Write-Output "ERROR: Access status $($setTask.Result)"
            }
        }
    }
} catch {
    # WinRT exception fallback
}

# 2. Fallback for Wi-Fi if WinRT did not handle it
if ($Target -eq "wifi" -or $Target -eq "wi-fi") {
    try {
        if ($Action -eq "on" -or $Action -eq "enable") {
            netsh interface set interface name="Wi-Fi" admin=ENABLED | Out-Null
            Write-Output "SUCCESS: Set to On (netsh)"
            exit 0
        } elseif ($Action -eq "off" -or $Action -eq "disable") {
            netsh interface set interface name="Wi-Fi" admin=DISABLED | Out-Null
            Write-Output "SUCCESS: Set to Off (netsh)"
            exit 0
        }
    } catch {
        Write-Output "ERROR: $($_.Exception.Message)"
        exit 1
    }
}

Write-Output "ERROR: Radio device for $Target not found or could not be changed."
exit 1
